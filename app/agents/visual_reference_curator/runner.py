"""Visual Reference Curator Runner - CLI runner for the agent.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .artifacts import VisualReferenceCuratorArtifacts
from .classifier import ReferenceClassifier


class VisualReferenceCuratorRunner:
    """Runner for the Visual Reference Curator agent."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.classifier = ReferenceClassifier(self.project_root)
        self.artifacts = VisualReferenceCuratorArtifacts(self.project_root)

    def run(
        self,
        latest_generated_asset: str,
        operator_visual_verdict: str,
        rejection_reason: str,
    ) -> Dict[str, Any]:
        """Execute the full visual reference curator run."""
        # Step 1: Classify canonical references
        classification_results = self.classifier.classify_references()

        # Step 2: Register rejected asset as negative reference
        negative_reference = self.classifier.register_negative_reference(
            latest_generated_asset, rejection_reason
        )

        # Step 3: Diagnose reference misuse
        misuse_diagnosis = self.classifier.diagnose_reference_misuse(rejection_reason)

        # Step 4: Create corrective generation package
        corrective_package = self._create_corrective_package(
            classification_results, misuse_diagnosis
        )

        # Step 5: Determine next state
        next_state = "corrective_reference_bound_generation_authorization_required"
        next_action = "corrective_reference_bound_generation_authorization_required"

        # Step 6: Generate all artifacts
        self.artifacts.generate_all_artifacts(
            classification_results,
            negative_reference,
            misuse_diagnosis,
            corrective_package,
            next_state,
            next_action,
        )

        # Step 7: Update canonical files
        self.artifacts.update_artifact_index("CORRECTIVE_PACKAGE_READY", next_state, next_action)
        self.artifacts.update_episode_ledger("CORRECTIVE_PACKAGE_READY", next_state, next_action)
        self.artifacts.update_state(next_state, next_action)

        return {
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "role": "visual_reference_curator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": "CORRECTIVE_PACKAGE_READY",
            "next_state": next_state,
            "next_action": next_action,
            "generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "classification_results": classification_results,
            "negative_reference": negative_reference,
            "misuse_diagnosis": misuse_diagnosis,
            "corrective_package": corrective_package,
            "traceable": True,
        }

    def _create_corrective_package(
        self,
        classification_results: Dict[str, Any],
        misuse_diagnosis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create the corrective generation package."""
        package = {
            "package_id": "corrective_reference_bound_generation_package",
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "framing_constraints": {
                "normal_framing_required": True,
                "no_extreme_face_crop": True,
                "no_distorted_nose_perspective": True,
                "check_eyes_mouth": True,
            },
            "reference_role_constraints": {
                "quality_only_refs": classification_results.get("quality_only_refs", []),
                "forbidden_as_composition_target": classification_results.get(
                    "quality_only_refs", []
                ),
                "respect_reference_roles": True,
            },
            "misuse_fixes": misuse_diagnosis.get("recommended_fixes", []),
            "violated_constraints": misuse_diagnosis.get("violated_constraints", []),
        }

        return package

    def inspect(self) -> Dict[str, Any]:
        """Inspect current state without making changes."""
        classification_results = self.classifier.classify_references()

        return {
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "role": "visual_reference_curator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inspection_only": True,
            "classification_results": classification_results,
            "traceable": True,
        }
