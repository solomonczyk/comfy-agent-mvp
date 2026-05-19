"""Workflow Patch - patches workflow for identity-locked generation.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class WorkflowPatch:
    """Patches workflow for identity-locked generation."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def create_workflow_patch(
        self, llm_decision: Dict[str, Any], canonical_identity_path: str
    ) -> Dict[str, Any]:
        """Create workflow patch for identity-locked generation."""
        positive_additions = llm_decision.get("positive_prompt_additions", [])
        negative_additions = llm_decision.get("negative_prompt_additions", [])

        patch = {
            "patch_id": "identity_locked_workflow_patch",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "identity_locking": {
                "canonical_identity_source": canonical_identity_path,
                "exclusive_identity_source": True,
                "preserve_facial_identity": True,
            },
            "prompt_modifications": {
                "positive_prompt_additions": positive_additions + [
                    "one woman only",
                    "single subject",
                    "same person as canonical reference",
                    "preserve facial identity",
                    "no man in foreground",
                    "no second person",
                    "no crowd",
                    "no over-the-shoulder dialogue shot",
                ],
                "negative_prompt_additions": negative_additions + [
                    "second person",
                    "man in foreground",
                    "duplicate person",
                    "different woman",
                    "identity drift",
                    "face swap",
                    "close-up",
                    "cropped face",
                    "extra person",
                    "crowd",
                    "multiple people",
                ],
            },
            "framing_constraints": {
                "medium_shot_or_upper_body": True,
                "full_face_visible": True,
                "head_not_touching_edges": True,
                "environment_visible": True,
                "extreme_closeup_forbidden": True,
                "target_resolution": "1344x768",
                "alternative_wide_formats": ["1536x864", "1728x972"],
            },
            "reference_conditioning": {
                "identity_reference_mode": "image_conditioning",
                "composition_reference_mode": "text_only",
                "quality_reference_mode": "text_only",
                "negative_reference_mode": "suppression_only",
            },
            "workflow_patch_requirements": [
                "enforce_single_subject",
                "lock_identity_to_canonical",
                "downgrade_non_identity_refs_to_text",
                "prevent_square_closeup_output",
            ],
        }

        return patch

    def save_patch(self, patch: Dict[str, Any]) -> None:
        """Save the workflow patch."""
        patch_path = self.identity_lock_dir / "identity_locked_workflow_patch.json"
        with open(patch_path, "w", encoding="utf-8") as f:
            json.dump(patch, f, indent=2, ensure_ascii=False)

    def apply_patch_to_workflow(
        self, base_workflow: Dict[str, Any], patch: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply patch to base workflow (ComfyUI format)."""
        submitted_workflow = base_workflow.copy()

        # Add identity lock metadata
        submitted_workflow["identity_lock_metadata"] = {
            "patch_id": patch["patch_id"],
            "task_id": patch["task_id"],
            "canonical_identity_source": patch["identity_locking"]["canonical_identity_source"],
            "timestamp": patch["timestamp"],
        }

        # Modify positive prompt in ComfyUI workflow format
        # Find CLIPTextEncode node for positive prompt (typically node 6 in sdxl template)
        positive_additions = " ".join(patch["prompt_modifications"]["positive_prompt_additions"])
        
        # Look for CLIPTextEncode nodes and update the one that's connected to KSampler positive
        for node_id, node_data in submitted_workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                inputs = node_data.get("inputs", {})
                current_text = inputs.get("text", "")
                # Check if this is the positive prompt (not negative)
                if "negative" not in current_text.lower():
                    node_data["inputs"]["text"] = f"{current_text}, {positive_additions}"

        # Modify negative prompt in ComfyUI workflow format
        negative_additions = " ".join(patch["prompt_modifications"]["negative_prompt_additions"])
        
        for node_id, node_data in submitted_workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                inputs = node_data.get("inputs", {})
                current_text = inputs.get("text", "")
                # Check if this is the negative prompt
                if "negative" in current_text.lower() or "blurry" in current_text.lower():
                    node_data["inputs"]["text"] = f"{current_text}, {negative_additions}"

        # Set resolution in EmptyLatentImage node
        target_resolution = patch["framing_constraints"]["target_resolution"]
        width, height = map(int, target_resolution.split("x"))
        
        for node_id, node_data in submitted_workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "EmptyLatentImage":
                node_data["inputs"]["width"] = width
                node_data["inputs"]["height"] = height

        return submitted_workflow

    def save_submitted_workflow(self, workflow: Dict[str, Any]) -> None:
        """Save the submitted workflow."""
        workflow_path = self.identity_lock_dir / "submitted_identity_locked_workflow.json"
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
