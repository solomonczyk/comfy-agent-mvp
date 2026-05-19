"""
Workflow Patch

Patch workflow/prompt to explicitly target normal framing and prevent crop.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class WorkflowPatch:
    """
    Workflow and prompt patch to prevent crop failure.

    Patches previous workflow/prompt to explicitly target:
    - normal framing
    - full face visible
    - upper body / medium shot or character in environment
    - no extreme close-up
    - no cropped head/face
    - background/environment visible
    - camera distance controlled
    - quality references used only for detail, not framing
    """

    patch_request: Dict[str, Any] = field(default_factory=dict)
    patched_prompt_conditioning: Dict[str, Any] = field(default_factory=dict)
    patched_workflow_manifest: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: str = ""

    def create_patch(
        self,
        llm_decision: Dict[str, Any],
        previous_prompt: Dict[str, Any],
        previous_workflow: Dict[str, Any],
    ) -> None:
        """
        Create patch from LLM decision and previous manifests.

        Args:
            llm_decision: LLM decision with prompt_patch and workflow_patch_requirements
            previous_prompt: Previous prompt manifest
            previous_workflow: Previous workflow manifest
        """
        # Create patch request
        self.patch_request = {
            "source_prompt_id": previous_prompt.get("prompt_id") if previous_prompt else None,
            "source_workflow_id": previous_workflow.get("workflow_id") if previous_workflow else None,
            "llm_decision_id": llm_decision.get("decision_type"),
            "patch_reason": "prevent extreme face crop, enforce normal framing",
            "patch_timestamp": self.created_at,
            "llm_decision": llm_decision,
        }

        # Patch prompt conditioning
        self.patched_prompt_conditioning = self._patch_prompt_conditioning(
            previous_prompt, llm_decision
        )

        # Patch workflow manifest
        self.patched_workflow_manifest = self._patch_workflow_manifest(
            previous_workflow, llm_decision
        )

    def _patch_prompt_conditioning(
        self,
        previous_prompt: Dict[str, Any],
        llm_decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Patch prompt conditioning with LLM decision."""
        if not previous_prompt:
            previous_prompt = {}

        prompt_patch = llm_decision.get("prompt_patch", {})

        # Start with previous prompt
        patched = previous_prompt.copy()

        # Add positive prompt additions
        if "positive" in patched:
            patched["positive"] += " " + " ".join(prompt_patch.get("positive_prompt_additions", []))
        else:
            patched["positive"] = " ".join(prompt_patch.get("positive_prompt_additions", []))

        # Add negative prompt additions
        if "negative" in patched:
            patched["negative"] += " " + " ".join(prompt_patch.get("negative_prompt_additions", []))
        else:
            patched["negative"] = " ".join(prompt_patch.get("negative_prompt_additions", []))

        # Add camera language
        if "camera_language" not in patched:
            patched["camera_language"] = []
        patched["camera_language"].extend(prompt_patch.get("camera_language", []))

        # Add reference usage notes
        if "reference_usage_notes" not in patched:
            patched["reference_usage_notes"] = []
        patched["reference_usage_notes"].extend(prompt_patch.get("reference_usage_notes", []))

        # Apply composition policy
        composition_policy = llm_decision.get("composition_policy", {})
        patched["composition_policy"] = composition_policy

        # Add patch metadata
        patched["patched"] = True
        patched["patched_at"] = self.created_at
        patched["patch_reason"] = "prevent extreme face crop, enforce normal framing"

        return patched

    def _patch_workflow_manifest(
        self,
        previous_workflow: Dict[str, Any],
        llm_decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Patch workflow manifest with LLM decision."""
        if not previous_workflow:
            previous_workflow = {}

        workflow_patch_requirements = llm_decision.get("workflow_patch_requirements", [])

        # Start with previous workflow
        patched = previous_workflow.copy()

        # Apply workflow patch requirements
        if "patches" not in patched:
            patched["patches"] = []

        for requirement in workflow_patch_requirements:
            patched["patches"].append({
                "requirement": requirement,
                "applied_at": self.created_at,
            })

        # Apply composition policy
        composition_policy = llm_decision.get("composition_policy", {})
        patched["composition_policy"] = composition_policy

        # Add reference role assignments
        reference_role_assignments = llm_decision.get("reference_role_assignments", [])
        patched["reference_role_assignments"] = reference_role_assignments

        # Add patch metadata
        patched["patched"] = True
        patched["patched_at"] = self.created_at
        patched["patch_reason"] = "prevent extreme face crop, enforce normal framing"

        return patched

    def save_patch_request(self, path: str) -> None:
        """Save patch request to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.patch_request, f, indent=2, ensure_ascii=False)

    def save_patched_prompt(self, path: str) -> None:
        """Save patched prompt conditioning to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.patched_prompt_conditioning, f, indent=2, ensure_ascii=False)

    def save_patched_workflow(self, path: str) -> None:
        """Save patched workflow manifest to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.patched_workflow_manifest, f, indent=2, ensure_ascii=False)
