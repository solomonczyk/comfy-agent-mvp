"""Identity Context Pack - gathers context for identity-locked generation.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class IdentityContextPack:
    """Gathers and structures context for identity-locked generation."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def build_context_pack(
        self,
        canonical_inventory: list[Dict[str, Any]],
        previous_rejected_assets: list[str],
        operator_rejection_reason: list[str],
    ) -> Dict[str, Any]:
        """Build the identity context pack."""
        # Extract identity references from canonical inventory
        identity_refs = [
            ref for ref in canonical_inventory if "01_identity" in ref.get("relative_path", "")
        ]
        composition_refs = [
            ref for ref in canonical_inventory if "04_style_light" in ref.get("relative_path", "")
        ]
        quality_refs = [
            ref for ref in canonical_inventory if "06_quality_negative" in ref.get("relative_path", "")
        ]

        context_pack = {
            "context_pack_id": "identity_context_pack",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canonical_identity_sources": {
                "identity_references": identity_refs,
                "primary_identity_anchor": identity_refs[0] if identity_refs else None,
            },
            "previous_rejection_context": {
                "rejected_assets": previous_rejected_assets,
                "operator_rejection_reason": operator_rejection_reason,
                "idempotence_failed": True,
                "identity_lock_failed": True,
            },
            "framing_constraints": {
                "medium_or_upper_body_shot": True,
                "full_face_visible": True,
                "head_not_touching_edges": True,
                "environment_visible": True,
                "extreme_closeup_forbidden": True,
            },
            "reference_role_constraints": {
                "canonical_identity_source_only": True,
                "quality_refs_text_only": True,
                "composition_refs_text_only": True,
                "negative_refs_suppression_only": True,
                "no_second_person_reference": True,
            },
            "forbidden_reference_roles": [
                "quality_reference_as_identity_source",
                "composition_reference_as_identity_source",
                "second_person_reference",
            ],
        }

        return context_pack

    def save_context_pack(self, context_pack: Dict[str, Any]) -> None:
        """Save the identity context pack."""
        context_pack_path = self.identity_lock_dir / "identity_context_pack.json"
        with open(context_pack_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2, ensure_ascii=False)
