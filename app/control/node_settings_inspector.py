"""MK-OBS1.1 — Node Settings Inspector for ComfyUI workflow payloads.

Extracts critical settings from effective ComfyUI workflow payloads
to provide operator visibility into what will be submitted to ComfyUI.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class NodeSettingsInspector:
    """Inspects ComfyUI workflow payloads and extracts node settings."""

    def __init__(self, workflow: dict[str, Any]) -> None:
        """
        Initialize inspector with workflow payload.

        Args:
            workflow: ComfyUI workflow dictionary
        """
        self.workflow = workflow
        self.inject_config = workflow.get("__inject__", {})

    def inspect(self) -> dict[str, Any]:
        """
        Extract all node settings from workflow.

        Returns:
            Dictionary with extracted node settings
        """
        result: dict[str, Any] = {
            "checkpoint_loader": self._extract_checkpoint_loader(),
            "ksampler": self._extract_ksampler(),
            "empty_latent": self._extract_empty_latent(),
            "positive_prompt": self._extract_positive_prompt(),
            "negative_prompt": self._extract_negative_prompt(),
            "save_image": self._extract_save_image(),
        }
        return result

    def _extract_checkpoint_loader(self) -> dict[str, Any] | None:
        """Extract CheckpointLoaderSimple node settings."""
        for node_id, node_data in self.workflow.items():
            if node_id == "__inject__":
                continue
            if node_data.get("class_type") == "CheckpointLoaderSimple":
                inputs = node_data.get("inputs", {})
                return {
                    "node_id": node_id,
                    "ckpt_name": inputs.get("ckpt_name"),
                }
        return None

    def _extract_ksampler(self) -> dict[str, Any] | None:
        """Extract KSampler node settings."""
        for node_id, node_data in self.workflow.items():
            if node_id == "__inject__":
                continue
            if node_data.get("class_type") == "KSampler":
                inputs = node_data.get("inputs", {})
                return {
                    "node_id": node_id,
                    "seed": inputs.get("seed"),
                    "steps": inputs.get("steps"),
                    "cfg": inputs.get("cfg"),
                    "sampler_name": inputs.get("sampler_name"),
                    "scheduler": inputs.get("scheduler"),
                    "denoise": inputs.get("denoise"),
                }
        return None

    def _extract_empty_latent(self) -> dict[str, Any] | None:
        """Extract EmptyLatentImage node settings."""
        for node_id, node_data in self.workflow.items():
            if node_id == "__inject__":
                continue
            if node_data.get("class_type") == "EmptyLatentImage":
                inputs = node_data.get("inputs", {})
                return {
                    "node_id": node_id,
                    "width": inputs.get("width"),
                    "height": inputs.get("height"),
                    "batch_size": inputs.get("batch_size"),
                }
        return None

    def _extract_positive_prompt(self) -> dict[str, Any] | None:
        """Extract CLIPTextEncode positive prompt node settings."""
        positive_node_id = self.inject_config.get("positive_prompt_node")
        if not positive_node_id:
            # Try to find by convention if not specified
            for node_id, node_data in self.workflow.items():
                if node_id == "__inject__":
                    continue
                if node_data.get("class_type") == "CLIPTextEncode":
                    inputs = node_data.get("inputs", {})
                    text = inputs.get("text", "")
                    if text and not self._is_negative_prompt(text):
                        return self._make_prompt_entry(node_id, inputs, "inferred_positive")
            return None

        node_data = self.workflow.get(positive_node_id)
        if node_data and node_data.get("class_type") == "CLIPTextEncode":
            inputs = node_data.get("inputs", {})
            return self._make_prompt_entry(positive_node_id, inputs, "prompt_pack.json")

        return None

    def _extract_negative_prompt(self) -> dict[str, Any] | None:
        """Extract CLIPTextEncode negative prompt node settings."""
        negative_node_id = self.inject_config.get("negative_prompt_node")
        if not negative_node_id:
            # Try to find by convention if not specified
            for node_id, node_data in self.workflow.items():
                if node_id == "__inject__":
                    continue
                if node_data.get("class_type") == "CLIPTextEncode":
                    inputs = node_data.get("inputs", {})
                    text = inputs.get("text", "")
                    if text and self._is_negative_prompt(text):
                        return self._make_prompt_entry(node_id, inputs, "inferred_negative")
            return None

        node_data = self.workflow.get(negative_node_id)
        if node_data and node_data.get("class_type") == "CLIPTextEncode":
            inputs = node_data.get("inputs", {})
            return self._make_prompt_entry(negative_node_id, inputs, "prompt_pack.json")

        return None

    def _make_prompt_entry(self, node_id: str, inputs: dict[str, Any], source: str) -> dict[str, Any]:
        """Create a prompt entry with text hash."""
        text = inputs.get("text", "")
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""
        return {
            "node_id": node_id,
            "text_sha256": text_hash,
            "source": source,
        }

    def _is_negative_prompt(self, text: str) -> bool:
        """Heuristic to identify negative prompts."""
        negative_indicators = ["blurry", "deformed", "bad anatomy", "extra limbs", "watermark"]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in negative_indicators)

    def _extract_save_image(self) -> dict[str, Any] | None:
        """Extract SaveImage node settings."""
        for node_id, node_data in self.workflow.items():
            if node_id == "__inject__":
                continue
            if node_data.get("class_type") == "SaveImage":
                inputs = node_data.get("inputs", {})
                return {
                    "node_id": node_id,
                    "filename_prefix": inputs.get("filename_prefix"),
                }
        return None


def inspect_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to inspect a workflow.

    Args:
        workflow: ComfyUI workflow dictionary

    Returns:
        Extracted node settings
    """
    inspector = NodeSettingsInspector(workflow)
    return inspector.inspect()


def inspect_workflow_file(workflow_path: str | Path) -> dict[str, Any]:
    """
    Inspect a workflow from a JSON file.

    Args:
        workflow_path: Path to workflow JSON file

    Returns:
        Extracted node settings
    """
    workflow_path = Path(workflow_path)
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)
    return inspect_workflow(workflow)


if __name__ == "__main__":
    # CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.control.node_settings_inspector <workflow.json>")
        sys.exit(1)

    workflow_path = sys.argv[1]
    settings = inspect_workflow_file(workflow_path)
    print(json.dumps(settings, indent=2))
