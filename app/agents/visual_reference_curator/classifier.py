"""Reference Classifier - classifies canonical references by role.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class ReferenceClassifier:
    """Classifies canonical references by their intended role."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"

    def classify_references(self) -> Dict[str, Any]:
        """Scan and classify all canonical references."""
        reference_role_map = {}
        quality_only_refs = []
        composition_refs = []

        # Scan for reference images
        reference_dir = self.project_root / "reference"
        if not reference_dir.exists():
            reference_dir = self.project_root / "input" / "reference"

        if reference_dir.exists():
            for ref_file in reference_dir.glob("*.png"):
                role = self._classify_single_reference(ref_file)
                reference_role_map[ref_file.name] = role

                if role == "quality_reference":
                    quality_only_refs.append(ref_file.name)
                elif role == "composition_reference":
                    composition_refs.append(ref_file.name)

        return {
            "reference_role_map": reference_role_map,
            "quality_only_refs": quality_only_refs,
            "composition_refs": composition_refs,
            "total_references": len(reference_role_map),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _classify_single_reference(self, ref_path: Path) -> str:
        """Classify a single reference based on filename patterns."""
        filename = ref_path.name.lower()

        # Close-up eye/skin patterns -> quality_reference only
        if any(pattern in filename for pattern in ["closeup", "close-up", "eye", "skin", "texture", "detail"]):
            return "quality_reference"

        # Environment patterns
        if any(pattern in filename for pattern in ["env", "environment", "background", "scene", "location"]):
            return "environment_reference"

        # Character in environment patterns
        if any(pattern in filename for pattern in ["character_env", "char_env", "in_scene", "on_location"]):
            return "character_in_environment_reference"

        # Identity patterns
        if any(pattern in filename for pattern in ["identity", "id", "face", "portrait", "headshot"]):
            return "identity_reference"

        # Default to composition reference
        return "composition_reference"

    def register_negative_reference(
        self, asset_path: str, rejection_reason: str
    ) -> Dict[str, Any]:
        """Register a rejected generated asset as negative reference."""
        negative_ref = {
            "asset_path": asset_path,
            "rejection_reason": rejection_reason,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "role": "negative_reference",
        }

        return negative_ref

    def diagnose_reference_misuse(
        self, rejection_reason: str
    ) -> Dict[str, Any]:
        """Diagnose reference misuse from rejection reason."""
        diagnosis = {
            "misuse_detected": False,
            "misuse_type": None,
            "violated_constraints": [],
            "recommended_fixes": [],
        }

        # Check for specific misuse patterns
        if "close-up" in rejection_reason.lower():
            diagnosis["misuse_detected"] = True
            diagnosis["misuse_type"] = "extreme_face_crop"
            diagnosis["violated_constraints"].append("no_extreme_face_crop")
            diagnosis["recommended_fixes"].append("use_normal_framing")

        if "distorted" in rejection_reason.lower():
            diagnosis["misuse_detected"] = True
            diagnosis["misuse_type"] = diagnosis["misuse_type"] or "distortion"
            diagnosis["violated_constraints"].append("no_distorted_perspective")
            diagnosis["recommended_fixes"].append("check_camera_angle")

        if "eye" in rejection_reason.lower() or "mouth" in rejection_reason.lower():
            diagnosis["misuse_detected"] = True
            diagnosis["misuse_type"] = diagnosis["misuse_type"] or "facial_artifact"
            diagnosis["violated_constraints"].append("check_eyes_mouth")
            diagnosis["recommended_fixes"].append("verify_facial_features")

        if "reference misuse" in rejection_reason.lower():
            diagnosis["misuse_detected"] = True
            diagnosis["misuse_type"] = diagnosis["misuse_type"] or "reference_misuse"
            diagnosis["violated_constraints"].append("respect_reference_roles")
            diagnosis["recommended_fixes"].append("enforce_reference_role_constraints")

        return diagnosis
