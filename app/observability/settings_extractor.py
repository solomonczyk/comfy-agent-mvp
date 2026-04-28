"""MK-OBS2 — Workflow settings extractor.

Extracts final observed generation settings from a patched ComfyUI workflow
before submission. This provides the source of truth for later recipe validation.
"""
from __future__ import annotations

from typing import Any


class WorkflowSettingsExtractor:
    """Extracts generation settings from a ComfyUI workflow dict.

    Extraction rules:
    - checkpoint: CheckpointLoaderSimple.inputs.ckpt_name
    - sampler fields: first KSampler-like node (steps, cfg, sampler_name, scheduler, denoise)
    - resolution/batch: EmptyLatentImage.inputs (width, height, batch_size)
    - negative_prompt: CLIPTextEncode negative node or injected negative_prompt_node
    - raw_nodes: includes node IDs used for extraction
    """

    def extract(self, workflow: dict, generation_mode: str | None = None, reference_image_path: str | None = None, staged_reference_image_path: str | None = None, reference_cleanliness: dict[str, Any] | None = None, prompt_pack: dict | None = None) -> dict:
        """Extract generation settings from a ComfyUI workflow.

        Args:
            workflow: ComfyUI workflow dict (patched, ready for submit)
            generation_mode: Optional generation mode (e.g., "reference_locked")
            reference_image_path: Optional reference image path for reference_locked mode
            staged_reference_image_path: Optional staged reference image path (MK-REAL3R-6)
            reference_cleanliness: Optional reference cleanliness metadata (MK-PROFILE1)
            prompt_pack: Optional prompt_pack dict to extract negative_prompt from

        Returns:
            Dict with extracted settings and raw_nodes metadata.

        Raises:
            ValueError: If required nodes are missing from workflow.
        """
        if not workflow or not isinstance(workflow, dict):
            raise ValueError("Workflow must be a non-empty dict")

        # Extract checkpoint
        checkpoint, checkpoint_node = self._extract_checkpoint(workflow)
        if checkpoint is None:
            raise ValueError("No CheckpointLoaderSimple node found in workflow")

        # Extract KSampler settings
        ksampler_settings, ksampler_node = self._extract_ksampler(workflow)
        if ksampler_settings is None:
            raise ValueError("No KSampler node found in workflow")

        # MK-REAL3R-3A — For reference_locked mode, extract resolution from resize node (ImageScale or ImageResize)
        # but batch_size from EmptyLatentImage (may be disconnected)
        resize_node = None
        resize_node_type = None
        if generation_mode == "reference_locked":
            resize_settings, resize_node, resize_node_type = self._extract_resize_node(workflow)
            if resize_settings is None:
                raise ValueError("No ImageScale or ImageResize node found in reference_locked workflow")
            # Extract width/height from resize node
            width = resize_settings.get("width")
            height = resize_settings.get("height")
            # Extract batch_size from EmptyLatentImage (may be disconnected but still exists)
            _, empty_latent_node = self._extract_latent(workflow)
            if empty_latent_node:
                empty_latent_settings, _ = self._extract_latent(workflow)
                batch_size = empty_latent_settings.get("batch_size")
            else:
                batch_size = None
            latent_settings = {"width": width, "height": height, "batch_size": batch_size}
            latent_node = resize_node
        else:
            # Extract resolution/batch from EmptyLatentImage (standard txt2img)
            latent_settings, latent_node = self._extract_latent(workflow)
            if latent_settings is None:
                raise ValueError("No EmptyLatentImage node found in workflow")

        # Extract negative prompt
        negative_prompt, negative_node = self._extract_negative_prompt(workflow)
        
        # MK-REF1R-4 — If negative_prompt not found in workflow, try prompt_pack
        if negative_prompt is None and prompt_pack:
            negative_prompt = prompt_pack.get("negative_prompt")

        # MK-REF1 — Extract LoadImage and VAEEncode nodes for reference_locked mode
        load_image_node = None
        vae_encode_node = None
        if generation_mode == "reference_locked":
            load_image_node = self._extract_load_image(workflow)
            vae_encode_node = self._extract_vae_encode(workflow)

        result = {
            "checkpoint": checkpoint,
            "sampler_name": ksampler_settings.get("sampler_name"),
            "scheduler": ksampler_settings.get("scheduler"),
            "steps": ksampler_settings.get("steps"),
            "cfg": ksampler_settings.get("cfg"),
            "width": latent_settings.get("width"),
            "height": latent_settings.get("height"),
            "batch_size": latent_settings.get("batch_size"),
            "denoise": ksampler_settings.get("denoise"),
            "negative_prompt": negative_prompt,
            "raw_nodes": {
                "source": "patched_workflow_before_submit",
                "checkpoint_node": checkpoint_node,
                "ksampler_node": ksampler_node,
                "latent_node": latent_node,
                "negative_prompt_node": negative_node,
            },
        }

        # MK-REF1 — Add reference_locked mode fields if applicable
        if generation_mode == "reference_locked":
            result["generation_mode"] = generation_mode
            result["reference_image_path"] = reference_image_path
            # MK-REAL3R-6 — Add staged reference path if provided
            if staged_reference_image_path:
                result["staged_reference_image_path"] = staged_reference_image_path
            # MK-PROFILE1 — Add reference cleanliness metadata if provided
            if reference_cleanliness:
                result["reference_cleanliness"] = reference_cleanliness
                # Add clean_reference_path as alias for backward compatibility
                if staged_reference_image_path:
                    result["clean_reference_path"] = staged_reference_image_path
            result["raw_nodes"]["load_image_node"] = load_image_node
            # MK-REAL3R-3A — Add resize_node and type-specific node key for reference_locked mode
            if resize_node:
                result["raw_nodes"]["resize_node"] = resize_node
                if resize_node_type == "ImageScale":
                    result["raw_nodes"]["image_scale_node"] = resize_node
                elif resize_node_type == "ImageResize":
                    result["raw_nodes"]["image_resize_node"] = resize_node
            # MK-REF1R-4 — Add vae_encode_node and update latent_node if VAEEncode is used
            if vae_encode_node:
                result["raw_nodes"]["vae_encode_node"] = vae_encode_node
                # In reference_locked mode, VAEEncode is the true latent source
                result["raw_nodes"]["latent_node"] = vae_encode_node

        return result

    def _extract_checkpoint(self, workflow: dict) -> tuple[str | None, str | None]:
        """Extract checkpoint name from CheckpointLoaderSimple node."""
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                inputs = node.get("inputs", {})
                ckpt_name = inputs.get("ckpt_name")
                return ckpt_name, node_id
        return None, None

    def _extract_ksampler(self, workflow: dict) -> tuple[dict | None, str | None]:
        """Extract KSampler settings from first KSampler-like node."""
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "KSampler":
                inputs = node.get("inputs", {})
                settings = {
                    "steps": inputs.get("steps"),
                    "cfg": inputs.get("cfg"),
                    "sampler_name": inputs.get("sampler_name"),
                    "scheduler": inputs.get("scheduler"),
                    "denoise": inputs.get("denoise"),  # Optional, may be None
                }
                return settings, node_id
        return None, None

    def _extract_latent(self, workflow: dict) -> tuple[dict | None, str | None]:
        """Extract width/height/batch_size from EmptyLatentImage node."""
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                inputs = node.get("inputs", {})
                settings = {
                    "width": inputs.get("width"),
                    "height": inputs.get("height"),
                    "batch_size": inputs.get("batch_size"),
                }
                return settings, node_id
        return None, None

    def _extract_negative_prompt(self, workflow: dict) -> tuple[str | None, str | None]:
        """Extract negative prompt from CLIPTextEncode or injected node."""
        # First check for injected negative_prompt_node
        inject_map = workflow.get("__inject__", {})
        negative_node_id = inject_map.get("negative_prompt_node")

        if negative_node_id and negative_node_id in workflow:
            node = workflow[negative_node_id]
            if isinstance(node, dict):
                inputs = node.get("inputs", {})
                text = inputs.get("text")
                if text:
                    return text, negative_node_id

        # Fallback: look for CLIPTextEncode nodes (heuristic: look for negative in context)
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode":
                inputs = node.get("inputs", {})
                text = inputs.get("text")
                # Heuristic: if text contains common negative keywords, treat as negative
                if text and any(kw in text.lower() for kw in ["blurry", "low quality", "distorted", "ugly"]):
                    return text, node_id

        return None, None

    def _extract_resize_node(self, workflow: dict) -> tuple[dict | None, str | None, str | None]:
        """Extract width/height from resize node (ImageScale or ImageResize) for reference_locked mode.

        MK-REAL3R-3A — Extracts resolution from the active resize node which is the
        generation size in reference_locked mode, not the disconnected EmptyLatentImage.
        Supports both ImageScale (preferred, available in this ComfyUI) and ImageResize
        (backwards compatibility).
        """
        RESIZE_NODE_TYPES = ("ImageScale", "ImageResize")
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") in RESIZE_NODE_TYPES:
                inputs = node.get("inputs", {})
                settings = {
                    "width": inputs.get("width"),
                    "height": inputs.get("height"),
                }
                return settings, node_id, node.get("class_type")
        return None, None, None

    def _extract_load_image(self, workflow: dict) -> str | None:
        """Extract LoadImage node ID for reference_locked mode.

        MK-REF1 — Extracts the LoadImage node used for reference image input.
        """
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "LoadImage":
                return node_id
        return None

    def _extract_vae_encode(self, workflow: dict) -> str | None:
        """Extract VAEEncode node ID for reference_locked mode.

        MK-REF1R-4 — Extracts the VAEEncode node used for img2img latent encoding.
        """
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "VAEEncode":
                return node_id
        return None
