"""Planned settings resolver for recipe validation before ComfyUI execution."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.recipes.models import ObservedGenerationSettings


class PlannedSettingsResolver:
    """Resolve planned generation settings from config, workflow, and prompt pack.
    
    Resolution order (priority):
    1. Check if observed settings file exists - if so, return None (ObservedSettingsResolver is source of truth)
    2. Derive planned settings from:
       - prompt_pack_path if provided
       - data/config.json
       - data/workflow_template.json
       - known defaults
    3. Return ObservedGenerationSettings-compatible object
    4. If not enough information exists, return None
    
    This resolver is read-only and does NOT run ComfyUI, submit prompts, or mutate workflows.
    """

    # Hardware-safe resolution map for aspect ratios
    ASPECT_RATIO_MAP: dict[str, tuple[int, int]] = {
        "9:16": (480, 640),
        "4:3": (640, 480),
        "1:1": (512, 512),
        "16:9": (640, 360),
    }

    # Default fallback values when config/workflow missing
    DEFAULT_STEPS = 20
    DEFAULT_CFG = 7.0
    DEFAULT_SAMPLER = "dpmpp_2m"
    DEFAULT_SCHEDULER = "karras"
    DEFAULT_BATCH_SIZE = 2
    DEFAULT_ASPECT_RATIO = "9:16"

    def __init__(self, project_root: Path | str):
        """Initialize resolver with project root.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def resolve_for_shot(
        self,
        episode_id: str,
        shot_id: str,
        prompt_pack_path: Path | str | None = None,
    ) -> ObservedGenerationSettings | None:
        """Resolve planned settings for a specific shot.
        
        Args:
            episode_id: Episode ID (e.g., "ep01")
            shot_id: Shot ID (e.g., "shot01")
            prompt_pack_path: Optional path to prompt pack JSON
            
        Returns:
            ObservedGenerationSettings if enough information exists, None otherwise
            
        Raises:
            ValueError: If file exists but contains invalid JSON
        """
        # Check if observed settings file exists - if so, return None
        # ObservedSettingsResolver remains the source of truth
        observed_paths = [
            self.project_root / "output" / "control" / f"{episode_id}_{shot_id}_observed_settings.json",
            self.project_root / "output" / "observability" / f"{episode_id}_{shot_id}_observed_settings.json",
            self.project_root / "data" / "observed_settings" / f"{episode_id}_{shot_id}.json",
        ]
        
        for observed_path in observed_paths:
            if observed_path.exists():
                # Observed settings exist - let ObservedSettingsResolver handle it
                return None

        # Load config.json
        config_path = self.project_root / "data" / "config.json"
        config_data: dict[str, Any] = {}
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file {config_path}: {e}") from e

        # Load workflow_template.json
        workflow_path = self.project_root / "data" / "workflow_template.json"
        workflow_data: dict[str, Any] = {}
        if workflow_path.exists():
            try:
                with open(workflow_path, encoding="utf-8") as f:
                    workflow_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in workflow file {workflow_path}: {e}") from e

        # Load prompt pack if provided
        prompt_pack_data: dict[str, Any] = {}
        if prompt_pack_path:
            prompt_pack_path = Path(prompt_pack_path)
            if prompt_pack_path.exists():
                try:
                    with open(prompt_pack_path, encoding="utf-8") as f:
                        prompt_pack_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in prompt pack {prompt_pack_path}: {e}") from e

        # Derive settings
        checkpoint = self._resolve_checkpoint(config_data, workflow_data)
        steps = self._resolve_steps(config_data, workflow_data)
        cfg = self._resolve_cfg(config_data, workflow_data)
        sampler_name = self._resolve_sampler_name(config_data, workflow_data)
        scheduler = self._resolve_scheduler(config_data, workflow_data)
        width, height = self._resolve_resolution(config_data, prompt_pack_data)
        batch_size = self._resolve_batch_size(config_data, prompt_pack_data)
        negative_prompt = self._resolve_negative_prompt(config_data, prompt_pack_data)
        denoise = self._resolve_denoise(config_data, workflow_data)
        generation_mode = self._resolve_generation_mode(prompt_pack_data)
        reference_image_path = self._resolve_reference_image_path(prompt_pack_data)

        # Build source summary for raw_nodes
        raw_nodes = {
            "source": "planned_settings",
            "config_path": str(config_path) if config_path.exists() else None,
            "workflow_template_path": str(workflow_path) if workflow_path.exists() else None,
            "prompt_pack_path": str(prompt_pack_path) if prompt_pack_path and Path(prompt_pack_path).exists() else None,
        }

        # Check if we have enough information
        # At minimum, we need checkpoint
        if checkpoint is None:
            return None

        # Create ObservedGenerationSettings
        return ObservedGenerationSettings(
            checkpoint=checkpoint,
            sampler_name=sampler_name,
            scheduler=scheduler,
            steps=steps,
            cfg=cfg,
            width=width,
            height=height,
            batch_size=batch_size,
            denoise=denoise,
            negative_prompt=negative_prompt,
            raw_nodes=raw_nodes,
            generation_mode=generation_mode,
            reference_image_path=reference_image_path,
        )

    def _resolve_checkpoint(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> str | None:
        """Resolve checkpoint from config or workflow."""
        # Try config.json first
        checkpoint = config_data.get("checkpoint")
        if checkpoint:
            return checkpoint

        # Fallback to workflow CheckpointLoaderSimple
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "CheckpointLoaderSimple":
                inputs = node_data.get("inputs", {})
                ckpt_name = inputs.get("ckpt_name")
                if ckpt_name:
                    return ckpt_name

        return None

    def _resolve_steps(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> int | None:
        """Resolve steps from config or workflow."""
        # Try config.json first
        steps = config_data.get("steps")
        if steps is not None:
            return int(steps)

        # Fallback to workflow KSampler
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                steps = inputs.get("steps")
                if steps is not None:
                    return int(steps)

        # Fallback to default
        return self.DEFAULT_STEPS

    def _resolve_cfg(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> float | None:
        """Resolve cfg from config or workflow."""
        # Try config.json first
        cfg = config_data.get("cfg")
        if cfg is not None:
            return float(cfg)

        # Fallback to workflow KSampler
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                cfg = inputs.get("cfg")
                if cfg is not None:
                    return float(cfg)

        # Fallback to default
        return self.DEFAULT_CFG

    def _resolve_sampler_name(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> str | None:
        """Resolve sampler_name from config or workflow."""
        # Try config.json first
        sampler_name = config_data.get("sampler_name")
        if sampler_name:
            return sampler_name

        # Fallback to workflow KSampler
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                sampler_name = inputs.get("sampler_name")
                if sampler_name:
                    return sampler_name

        # Fallback to default
        return self.DEFAULT_SAMPLER

    def _resolve_scheduler(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> str | None:
        """Resolve scheduler from config or workflow."""
        # Try config.json first
        scheduler = config_data.get("scheduler")
        if scheduler:
            return scheduler

        # Fallback to workflow KSampler
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                scheduler = inputs.get("scheduler")
                if scheduler:
                    return scheduler

        # Fallback to default
        return self.DEFAULT_SCHEDULER

    def _resolve_resolution(
        self, config_data: dict[str, Any], prompt_pack_data: dict[str, Any]
    ) -> tuple[int | None, int | None]:
        """Resolve width/height from aspect ratio."""
        # Determine aspect ratio
        aspect_ratio = None

        # Try prompt_pack aspect_ratio
        if prompt_pack_data:
            aspect_ratio = prompt_pack_data.get("aspect_ratio")

        # Try config.json aspect_ratio
        if not aspect_ratio:
            aspect_ratio = config_data.get("aspect_ratio")

        # Fallback to default
        if not aspect_ratio:
            aspect_ratio = self.DEFAULT_ASPECT_RATIO

        # Use safe resolution map
        resolution = self.ASPECT_RATIO_MAP.get(aspect_ratio)
        if resolution:
            return resolution

        return None, None

    def _resolve_batch_size(
        self, config_data: dict[str, Any], prompt_pack_data: dict[str, Any]
    ) -> int | None:
        """Resolve batch_size from config or prompt pack."""
        # Try config.json max_frames_per_batch
        batch_size = config_data.get("max_frames_per_batch")
        if batch_size is not None:
            batch_size = int(batch_size)

        # If prompt pack has frame_count and it's lower, use that
        if prompt_pack_data:
            frame_count = prompt_pack_data.get("frame_count")
            if frame_count is not None:
                frame_count = int(frame_count)
                if batch_size is None or frame_count < batch_size:
                    batch_size = frame_count

        # Fallback to default
        if batch_size is None:
            batch_size = self.DEFAULT_BATCH_SIZE

        return batch_size

    def _resolve_negative_prompt(
        self, config_data: dict[str, Any], prompt_pack_data: dict[str, Any]
    ) -> str | None:
        """Resolve negative_prompt from config and prompt pack (merged/deduplicated)."""
        negative_terms = []

        # Start with config.json default_negative
        default_negative = config_data.get("default_negative")
        if default_negative:
            negative_terms.extend([term.strip() for term in default_negative.split(",")])

        # Append/merge prompt_pack negative_prompt if present
        if prompt_pack_data:
            # Check beat_prompts for negative_prompt
            beat_prompts = prompt_pack_data.get("beat_prompts", [])
            if beat_prompts and len(beat_prompts) > 0:
                # Use first beat's negative_prompt as representative
                first_beat = beat_prompts[0]
                pack_negative = first_beat.get("negative_prompt")
                if pack_negative:
                    pack_terms = [term.strip() for term in pack_negative.split(",")]
                    negative_terms.extend(pack_terms)

        # Deduplicate while preserving order
        seen = set()
        deduplicated = []
        for term in negative_terms:
            if term and term not in seen:
                seen.add(term)
                deduplicated.append(term)

        return ", ".join(deduplicated) if deduplicated else None

    def _resolve_denoise(self, config_data: dict[str, Any], workflow_data: dict[str, Any]) -> float | None:
        """Resolve denoise from config or workflow."""
        # Try config.json first
        denoise = config_data.get("denoise")
        if denoise is not None:
            return float(denoise)

        # Fallback to workflow KSampler
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                denoise = inputs.get("denoise")
                if denoise is not None:
                    return float(denoise)

        # Return None for txt2img/storyboard recipe
        return None

    def _resolve_generation_mode(self, prompt_pack_data: dict[str, Any]) -> str | None:
        """Resolve generation_mode from prompt pack."""
        if not prompt_pack_data:
            return None
        
        return prompt_pack_data.get("generation_mode")

    def _resolve_reference_image_path(self, prompt_pack_data: dict[str, Any]) -> str | None:
        """Resolve reference_image_path from prompt pack."""
        if not prompt_pack_data:
            return None
        
        return prompt_pack_data.get("reference_image_path")
