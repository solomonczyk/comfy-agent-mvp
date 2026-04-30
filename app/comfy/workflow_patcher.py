"""Workflow patcher for fixing common ComfyUI workflow defects."""
from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

from app.reference.reference_staging import stage_reference_to_ascii

log = logging.getLogger(__name__)


class WorkflowPatcher:
    """Patches ComfyUI workflows to fix common defects."""

    SAFE_DEFAULTS = {
        "denoise": 0.75,
        "cfg": 7.0,
        "steps": 6,
        "sampler_name": "dpmpp_sde",
        "scheduler": "karras",
    }

    ASPECT_RATIO_MAP = {
        "4:3":  (640, 480),
        "16:9": (768, 432),
        "1:1":  (512, 512),
        "9:16": (480, 640),  # MK-REAL2R-3: Fixed from 480x848 to 480x640 (307200 pixels)
        "7:4":  (1344, 768),  # RC2-PRODCARDS3AO: Support 1344x768 landscape resolution
    }

    @classmethod
    def patch_ksampler_nodes(cls, workflow: dict, node_ids: list[str]) -> dict:
        """
        Patch KSampler nodes with safe defaults when defect conditions are met.

        Args:
            workflow: ComfyUI workflow dict
            node_ids: List of KSampler node IDs to patch

        Returns:
            Patched workflow copy (does not mutate input)
        """
        workflow_copy = copy.deepcopy(workflow)

        for node_id in node_ids:
            if node_id not in workflow_copy:
                log.warning(f"[PATCH] node {node_id}: not found in workflow, skipping")
                continue

            node = workflow_copy[node_id]
            if node.get("class_type") != "KSampler":
                log.warning(f"[PATCH] node {node_id}: not a KSampler node, skipping")
                continue

            inputs = node.get("inputs", {})
            cls._patch_ksampler_inputs(node_id, inputs)

        return workflow_copy

    @classmethod
    def patch_resolution(cls, workflow: dict, aspect_ratio: str) -> dict:
        """Patch EmptyLatentImage width/height based on aspect ratio.

        Args:
            workflow: ComfyUI workflow dict (mutated in place)
            aspect_ratio: Aspect ratio string (e.g., "4:3", "16:9")

        Returns:
            The mutated workflow dict.
        """
        width, height = cls.ASPECT_RATIO_MAP.get(aspect_ratio, cls.ASPECT_RATIO_MAP["4:3"])
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
                log.info(f"[PATCH] Node {node_id}: resolution = {width}x{height} ({aspect_ratio})")
        return workflow

    @classmethod
    def patch_reference_image(
        cls,
        workflow: dict,
        reference_image_path: str,
        project_root: str | Path | None = None,
        character_name: str = "character",
        denoise: float = 0.5,  # MK-REAL3R-2: Changed from 0.42 to 0.5 to be within valid range 0.45-0.75
    ) -> tuple[dict, str, str, dict[str, Any] | None]:
        """Patch LoadImage node with reference image path and set denoise.

        MK-REAL3R-6 — Stages non-ASCII reference paths to ASCII-safe local paths.
        MK-PROFILE1 — Returns reference cleanliness metadata from project profile.

        Args:
            workflow: ComfyUI workflow dict (mutated in place)
            reference_image_path: Absolute path to reference image
            project_root: Project root for staging (optional)
            character_name: Character name for staging filename
            denoise: Denoise strength for img2img (default 0.42)

        Returns:
            Tuple of (workflow, original_path, staged_path, cleanliness_metadata).
            If original is already ASCII, staged_path equals original_path.
            cleanliness_metadata contains strategy info if clean reference was used.

        MK-REF1 — Patches LoadImage.inputs.image with reference path and
        KSampler.inputs.denoise with specified value for reference_locked mode.
        MK-REF1R-4 — Rewires KSampler.latent_image to VAEEncode output for img2img.
        MK-REAL3R-6 — Stages non-ASCII paths to ASCII-safe local paths.
        """
        # MK-REAL3R-6 — Stage reference to ASCII path if needed
        original_path = reference_image_path
        staged_path = reference_image_path
        cleanliness_metadata = None

        if project_root is not None:
            original_path, staged_path, cleanliness_metadata = stage_reference_to_ascii(
                reference_image_path,
                project_root,
                character_name,
            )
            if original_path != staged_path:
                log.info(f"[MK-REAL3R-6] Staged reference: {original_path} → {staged_path}")
                if cleanliness_metadata:
                    log.info(f"[MK-PROFILE1] Clean reference strategy: {cleanliness_metadata}")

        # Convert staged path to forward slashes for ComfyUI compatibility
        ref_path_str = str(Path(staged_path).resolve()).replace("\\", "/")

        # Find LoadImage and VAEEncode nodes
        load_image_node_id = None
        vae_encode_node_id = None

        for node_id, node in workflow.items():
            if isinstance(node, dict):
                if node.get("class_type") == "LoadImage":
                    load_image_node_id = node_id
                elif node.get("class_type") == "VAEEncode":
                    vae_encode_node_id = node_id

        # Patch LoadImage node
        if load_image_node_id:
            node = workflow[load_image_node_id]
            old_path = node["inputs"].get("image", "")
            node["inputs"]["image"] = ref_path_str
            log.info(f"[PATCH] Node {load_image_node_id}: LoadImage.image {old_path!r} → {ref_path_str!r}")

        # Rewire KSampler.latent_image to VAEEncode output for img2img
        if vae_encode_node_id:
            for node_id, node in workflow.items():
                if isinstance(node, dict) and node.get("class_type") == "KSampler":
                    old_latent = node["inputs"].get("latent_image")
                    node["inputs"]["latent_image"] = [vae_encode_node_id, 0]
                    log.info(f"[PATCH] Node {node_id}: KSampler.latent_image {old_latent} → [{vae_encode_node_id}, 0] (VAEEncode output)")
        else:
            log.warning("[PATCH] No VAEEncode node found - cannot rewire KSampler.latent_image for img2img")

        # Patch KSampler denoise
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "KSampler":
                old_denoise = node["inputs"].get("denoise", 0.0)
                node["inputs"]["denoise"] = denoise
                log.info(f"[PATCH] Node {node_id}: KSampler.denoise {old_denoise} → {denoise}")

        return workflow, original_path, staged_path, cleanliness_metadata

    @classmethod
    def patch_checkpoint(cls, workflow: dict, checkpoint_name: str) -> dict:
        """Patch CheckpointLoaderSimple ckpt_name.

        Args:
            workflow: ComfyUI workflow dict (mutated in place)
            checkpoint_name: Checkpoint filename to set

        Returns:
            The mutated workflow dict.
        """
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                old = node["inputs"].get("ckpt_name", "")
                node["inputs"]["ckpt_name"] = checkpoint_name
                log.info(f"[PATCH] Node {node_id}: ckpt_name {old!r} → {checkpoint_name!r}")
        return workflow

    @classmethod
    def _patch_ksampler_inputs(cls, node_id: str, inputs: dict) -> None:
        """Patch individual KSampler inputs based on defect conditions."""
        # Check denoise
        denoise = inputs.get("denoise", 0.0)
        if denoise > 0.95:
            inputs["denoise"] = cls.SAFE_DEFAULTS["denoise"]
            log.info(f"[PATCH] node {node_id}: denoise {denoise} → {cls.SAFE_DEFAULTS['denoise']}")

        # Check cfg
        cfg = inputs.get("cfg", 0.0)
        if cfg < 3.0:
            inputs["cfg"] = cls.SAFE_DEFAULTS["cfg"]
            log.info(f"[PATCH] node {node_id}: cfg {cfg} → {cls.SAFE_DEFAULTS['cfg']}")

        # Check steps
        steps = inputs.get("steps", 0)
        if steps > 25:
            inputs["steps"] = cls.SAFE_DEFAULTS["steps"]
            log.info(f"[PATCH] node {node_id}: steps {steps} → {cls.SAFE_DEFAULTS['steps']}")

        # Always apply fast sampler
        inputs["sampler_name"] = cls.SAFE_DEFAULTS["sampler_name"]
        inputs["scheduler"] = cls.SAFE_DEFAULTS["scheduler"]
        log.info(f"[PATCH] node {node_id}: sampler={cls.SAFE_DEFAULTS['sampler_name']}, scheduler={cls.SAFE_DEFAULTS['scheduler']}")

        # Check latent_image source
        latent_image = inputs.get("latent_image")
        if latent_image:
            source_id = latent_image[0] if isinstance(latent_image, list) else None
            # This check would require looking up the source node type
            # For now, we log the source ID for debugging
            if source_id:
                log.debug(f"[PATCH] node {node_id}: latent_image source is node {source_id}")

        # Check positive conditioning
        positive = inputs.get("positive")
        if not positive:
            log.warning(f"[PATCH] node {node_id}: positive conditioning is missing or empty")

        # Check negative conditioning
        negative = inputs.get("negative")
        if not negative:
            log.warning(f"[PATCH] node {node_id}: negative conditioning is missing or empty")

    _IPADAPTER_STRIP_CLASSES = frozenset(
        ("IPAdapterAdvanced", "IPAdapter", "IPAdapterFaceID",
         "IPAdapterUnifiedLoader", "LoadImage")
    )

    @classmethod
    def strip_ipadapter(cls, workflow: dict) -> dict:
        """Remove IPAdapter-related nodes and reconnect KSampler model to checkpoint.

        Removes IPAdapterAdvanced, IPAdapter, IPAdapterFaceID, IPAdapterUnifiedLoader,
        and LoadImage nodes, then reconnects any KSampler model input that pointed to
        an IPAdapter node back to CheckpointLoaderSimple (node output index 0).

        Args:
            workflow: ComfyUI workflow dict (mutated in place).

        Returns:
            The mutated workflow dict.
        """
        # Find checkpoint loader node id
        ckpt_node_id: str | None = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                ckpt_node_id = node_id
                break

        # Collect node IDs that belong to IPAdapter chain
        to_remove = [
            nid for nid, node in workflow.items()
            if isinstance(node, dict) and node.get("class_type", "") in cls._IPADAPTER_STRIP_CLASSES
        ]
        removed = set(to_remove)
        for nid in to_remove:
            del workflow[nid]
            log.info(f"[PATCH] strip_ipadapter: removed node {nid}")

        # Reconnect KSampler model input if it points to a removed node
        if ckpt_node_id:
            for node in workflow.values():
                if not isinstance(node, dict) or node.get("class_type") != "KSampler":
                    continue
                model_ref = node["inputs"].get("model")
                if isinstance(model_ref, list) and str(model_ref[0]) in removed:
                    node["inputs"]["model"] = [ckpt_node_id, 0]
                    log.info(f"[PATCH] strip_ipadapter: KSampler model → [{ckpt_node_id}, 0]")

        return workflow

    @classmethod
    def patch_ipadapter(
        cls,
        workflow: dict,
        reference_image_path: Path,
        weight: float = 0.6,
    ) -> dict:
        """Patch IPAdapter nodes with a reference image path and weight.

        Finds LoadImage nodes connected to an IPAdapterAdvanced or IPAdapter node
        and sets their image field to the reference_image_path. Also updates the
        weight on IPAdapter nodes.

        Args:
            workflow: ComfyUI workflow dict (mutated in place).
            reference_image_path: Absolute path to reference grid PNG.
            weight: IP-Adapter conditioning weight (default 0.6).

        Returns:
            The mutated workflow dict.
        """
        _IPADAPTER_CLASSES = ("IPAdapterAdvanced", "IPAdapter", "IPAdapterFaceID")
        _LOAD_IMAGE_CLASSES = ("LoadImage",)

        ipadapter_node_ids: list[str] = []
        load_image_node_ids: list[str] = []

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            ct = node.get("class_type", "")
            if ct in _IPADAPTER_CLASSES:
                ipadapter_node_ids.append(node_id)
            elif ct in _LOAD_IMAGE_CLASSES:
                load_image_node_ids.append(node_id)

        if not ipadapter_node_ids:
            log.warning("[PATCH] patch_ipadapter: no IPAdapter node found in workflow — skipping")
            return workflow

        # Find LoadImage nodes that feed into any IPAdapter node
        referenced_load_nodes: set[str] = set()
        for node_id in ipadapter_node_ids:
            inputs = workflow[node_id].get("inputs", {})
            image_ref = inputs.get("image")
            if isinstance(image_ref, list) and image_ref:
                referenced_load_nodes.add(str(image_ref[0]))
            # Update weight
            inputs["weight"] = weight
            log.info(f"[PATCH] Node {node_id}: IPAdapter weight → {weight}")

        # Patch referenced LoadImage nodes; fall back to all LoadImage nodes
        targets = referenced_load_nodes & set(load_image_node_ids) or set(load_image_node_ids)
        img_str = str(reference_image_path.resolve()).replace("\\", "/")
        for node_id in targets:
            workflow[node_id]["inputs"]["image"] = img_str
            log.info(f"[PATCH] Node {node_id}: LoadImage.image → {img_str}")

        return workflow
