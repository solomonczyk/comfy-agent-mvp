from pathlib import Path
from typing import Any

from app.comfy.comfy_client import ComfyClient


class PreflightValidator:
    def __init__(self, workflow_id: str = "sdxl_txt2img_v1") -> None:
        """Initialize preflight validator with workflow-specific contracts.
        
        Args:
            workflow_id: Workflow ID to determine contract expectations
        """
        self.workflow_id = workflow_id
        self._set_workflow_contracts()
        self.client = ComfyClient()

    def _set_workflow_contracts(self) -> None:
        """Set contract expectations based on workflow type."""
        # SDXL txt2img contracts (default)
        if self.workflow_id in ["sdxl_txt2img_v1", "portrait_sdxl_v1", "cinematic_sdxl_v1", "product_sdxl_v1", "fashion_sdxl_v1"]:
            self.EXPECTED_CLASS_TYPES = {
                "3": "KSampler",
                "4": "CheckpointLoaderSimple",
                "5": "EmptyLatentImage",
                "6": "CLIPTextEncode",
                "7": "CLIPTextEncode",
                "8": "VAEDecode",
                "9": "SaveImage",
            }
            self.REQUIRED_INPUT_KEYS = {
                "3": {"seed", "steps", "cfg", "sampler_name", "scheduler", "model", "positive", "negative", "latent_image"},
                "4": {"ckpt_name"},
                "5": {"width", "height", "batch_size"},
                "6": {"text", "clip"},
                "7": {"text", "clip"},
                "8": {"samples", "vae"},
                "9": {"filename_prefix", "images"},
            }
        # img2img contracts (simple template without LatentNoise)
        elif self.workflow_id == "img2img_v1":
            self.EXPECTED_CLASS_TYPES = {
                "3": "KSampler",
                "4": "CheckpointLoaderSimple",
                "5": "LoadImage",
                "6": "CLIPTextEncode",
                "7": "CLIPTextEncode",
                "8": "VAEEncode",
                "9": "VAEDecode",
                "10": "SaveImage",
            }
            self.REQUIRED_INPUT_KEYS = {
                "3": {"seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "model", "positive", "negative", "latent_image"},
                "4": {"ckpt_name"},
                "5": {"image"},
                "6": {"text", "clip"},
                "7": {"text", "clip"},
                "8": {"pixels", "vae"},
                "9": {"samples", "vae"},
                "10": {"filename_prefix", "images"},
            }
        # upscale contracts
        elif self.workflow_id == "upscale_v1":
            self.EXPECTED_CLASS_TYPES = {
                "3": "KSampler",
                "4": "CheckpointLoaderSimple",
                "5": "LoadImage",
                "6": "CLIPTextEncode",
                "7": "CLIPTextEncode",
                "8": "VAEEncode",
                "9": "EmptyLatentImage",
                "10": "LatentUpscale",
                "11": "VAEDecode",
                "12": "SaveImage",
            }
            self.REQUIRED_INPUT_KEYS = {
                "3": {"seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "model", "positive", "negative", "latent_image"},
                "4": {"ckpt_name"},
                "5": {"image"},
                "6": {"text", "clip"},
                "7": {"text", "clip"},
                "8": {"pixels", "vae"},
                "9": {"width", "height", "batch_size"},
                "10": {"samples", "width", "height"},
                "11": {"samples", "vae"},
                "12": {"filename_prefix", "images"},
            }
        # inpaint_face contracts
        elif self.workflow_id == "inpaint_face_v1":
            self.EXPECTED_CLASS_TYPES = {
                "3": "KSampler",
                "4": "CheckpointLoaderSimple",
                "5": "LoadImage",
                "6": "CLIPTextEncode",
                "7": "CLIPTextEncode",
                "8": "VAEEncode",
                "9": "LoadImageMask",
                "10": "VAEDecode",
                "11": "EmptyLatentImage",
                "12": "SaveImage",
            }
            self.REQUIRED_INPUT_KEYS = {
                "3": {"seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "model", "positive", "negative", "latent_image"},
                "4": {"ckpt_name"},
                "5": {"image"},
                "6": {"text", "clip"},
                "7": {"text", "clip"},
                "8": {"pixels", "vae"},
                "9": {"mask"},
                "10": {"samples", "vae"},
                "11": {"width", "height", "batch_size"},
                "12": {"filename_prefix", "images"},
            }
        else:
            # Default to txt2img contracts
            self.EXPECTED_CLASS_TYPES = {
                "3": "KSampler",
                "4": "CheckpointLoaderSimple",
                "5": "EmptyLatentImage",
                "6": "CLIPTextEncode",
                "7": "CLIPTextEncode",
                "8": "VAEDecode",
                "9": "SaveImage",
            }
            self.REQUIRED_INPUT_KEYS = {
                "3": {"seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "model", "positive", "negative", "latent_image"},
                "4": {"ckpt_name"},
                "5": {"width", "height", "batch_size"},
                "6": {"text", "clip"},
                "7": {"text", "clip"},
                "8": {"samples", "vae"},
                "9": {"filename_prefix", "images"},
            }

    @staticmethod
    def _validate_preset(
        preset_name: str | None,
        presets: dict[str, dict[str, Any]],
    ) -> str | None:
        if not preset_name:
            return None

        if preset_name not in presets:
            available = ", ".join(sorted(presets.keys()))
            raise ValueError(
                f"Unknown preset: {preset_name}. Available presets: {available}"
            )

        return preset_name

    @staticmethod
    def _validate_required_node_ids(
        workflow: dict[str, Any],
        required_node_ids: set[str],
    ) -> list[str]:
        missing = sorted(node_id for node_id in required_node_ids if node_id not in workflow)
        if missing:
            raise ValueError(
                "Workflow template is missing required node ids: "
                + ", ".join(missing)
            )
        return missing

    def _validate_contract(self, workflow: dict[str, Any], required_node_ids: set[str]) -> dict[str, Any]:
        contract_issues: list[str] = []

        for node_id in sorted(required_node_ids):
            node_data = workflow.get(node_id)
            if not isinstance(node_data, dict):
                contract_issues.append(f"node {node_id}: not a dict")
                continue

            class_type = node_data.get("class_type")
            expected_class_type = self.EXPECTED_CLASS_TYPES.get(node_id)

            if class_type != expected_class_type:
                contract_issues.append(
                    f"node {node_id}: expected class_type={expected_class_type}, got class_type={class_type}"
                )

            inputs = node_data.get("inputs", {})
            if not isinstance(inputs, dict):
                contract_issues.append(f"node {node_id}: inputs is not a dict")
                continue

            required_keys = self.REQUIRED_INPUT_KEYS.get(node_id, set())
            missing_keys = sorted(required_keys - set(inputs.keys()))

            if missing_keys:
                contract_issues.append(
                    f"node {node_id}: missing input keys: {', '.join(missing_keys)}"
                )

        if contract_issues:
            raise ValueError(
                "Workflow template contract validation failed: "
                + "; ".join(contract_issues)
            )

        return {
            "contract_valid": True,
            "validated_node_ids": sorted(required_node_ids),
        }

    async def validate(
        self,
        *,
        workflow_path: str | Path,
        preset_name: str | None,
        presets: dict[str, dict[str, Any]],
        checkpoint_name: str,
        required_node_ids: set[str],
        workflow_id: str = "sdxl_txt2img_v1",
    ) -> dict[str, Any]:
        # Set contracts based on workflow_id
        self.workflow_id = workflow_id
        self._set_workflow_contracts()

        self._validate_preset(preset_name, presets)

        workflow = await self.client.load_workflow(workflow_path)
        self._validate_required_node_ids(workflow, required_node_ids)
        contract_result = self._validate_contract(workflow, required_node_ids)

        available_checkpoints = await self.client.get_models_in_folder("checkpoints")
        if checkpoint_name not in available_checkpoints:
            preview = ", ".join(sorted(available_checkpoints)[:20])
            raise ValueError(
                f"Checkpoint not found in ComfyUI models/checkpoints: {checkpoint_name}. "
                f"Available: {preview}"
            )

        return {
            "workflow_path": str(Path(workflow_path)),
            "preset_name": preset_name,
            "checkpoint_name": checkpoint_name,
            "required_node_ids": sorted(required_node_ids),
            "available_checkpoints_count": len(available_checkpoints),
            "contract": contract_result,
        }
