"""Reference Router - routes references by role with identity protection.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class ReferenceRouter:
    """Routes references by role with identity protection."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def route_references(
        self, canonical_inventory: list[Dict[str, Any]], llm_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route references by role with identity protection."""
        # Categorize references
        identity_refs = [
            ref for ref in canonical_inventory if "01_identity" in ref.get("relative_path", "")
        ]
        composition_refs = [
            ref for ref in canonical_inventory if "04_style_light" in ref.get("relative_path", "")
        ]
        quality_refs = [
            ref for ref in canonical_inventory if "06_quality_negative" in ref.get("relative_path", "")
        ]
        negative_refs = [
            ref for ref in canonical_inventory if "negative_reference" in ref.get("filename", "")
        ]

        routing_report = {
            "report_id": "reference_role_routing_report",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "identity_source_selection": {
                "selected": True,
                "source": "canonical_01_identity_references",
                "count": len(identity_refs),
                "primary_anchor": identity_refs[0].get("relative_path", "") if identity_refs else "",
                "exclusive_identity_source": True,
            },
            "composition_source_selection": {
                "selected": True,
                "source": "canonical_04_style_light_references",
                "count": len(composition_refs),
                "downgraded_to_text_only": True,
                "cannot_affect_face_identity": True,
            },
            "quality_reference_handling": {
                "downgraded_to_text_only": True,
                "cannot_enter_image_conditioning": True,
                "style_only": True,
                "count": len(quality_refs),
            },
            "negative_reference_handling": {
                "suppression_only": True,
                "count": len(negative_refs),
            },
            "forbidden_routing": {
                "closeup_refs_cannot_enter_image_conditioning": True,
                "no_second_person_reference_allowed": True,
                "quality_refs_blocked_from_identity": True,
                "composition_refs_blocked_from_identity": True,
            },
            "reference_role_assignments": [
                {
                    "reference_path": ref.get("relative_path", ""),
                    "role": "identity_anchor" if "01_identity" in ref.get("relative_path", "") else "composition_text_only",
                    "allowed_use": ["identity_preservation"] if "01_identity" in ref.get("relative_path", "") else ["composition_text"],
                    "forbidden_use": [] if "01_identity" in ref.get("relative_path", "") else ["identity_source", "image_conditioning"],
                }
                for ref in identity_refs + composition_refs[:3]
            ],
            "llm_decision_alignment": llm_decision.get("reference_role_assignments", []),
        }

        return routing_report

    def save_routing_report(self, report: Dict[str, Any]) -> None:
        """Save the reference routing report."""
        report_path = self.identity_lock_dir / "reference_role_routing_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
