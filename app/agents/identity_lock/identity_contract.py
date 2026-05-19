"""Identity Contract - enforces canonical reference as identity source.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class IdentityContract:
    """Enforces identity preservation contract."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def create_identity_contract(
        self, llm_decision: Dict[str, Any], context_pack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create identity anchor contract."""
        identity_refs = context_pack.get("canonical_identity_sources", {}).get(
            "identity_references", []
        )
        primary_identity = identity_refs[0] if identity_refs else {}

        contract = {
            "contract_id": "identity_anchor_contract",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canonical_identity_source": {
                "reference_path": primary_identity.get("relative_path", ""),
                "reference_id": primary_identity.get("reference_id", ""),
                "sha256": primary_identity.get("sha256", ""),
                "role": "identity_anchor",
                "exclusive_identity_source": True,
            },
            "identity_preservation_rules": {
                "canonical_reference_is_only_identity_source": True,
                "quality_references_cannot_affect_face_identity": True,
                "composition_references_cannot_affect_face_identity": True,
                "no_multi_person_scene_unless_authorized": True,
                "identity_gate_required_before_operator_packet": True,
                "low_identity_confidence_blocks_operator_packet": True,
            },
            "forbidden_actions": {
                "use_quality_reference_as_identity_source": True,
                "use_composition_reference_as_identity_source": True,
                "allow_second_person_reference": True,
                "allow_extra_foreground_person": True,
                "allow_background_people": True,
                "skip_identity_gate": True,
            },
            "llm_decision_reference": llm_decision.get("canonical_identity_source", {}),
            "contract_enforcement": {
                "identity_source_locked": True,
                "quality_refs_downgraded_to_text_only": True,
                "composition_refs_downgraded_to_text_only": True,
                "single_subject_policy_enforced": True,
            },
        }

        return contract

    def save_contract(self, contract: Dict[str, Any]) -> None:
        """Save the identity contract."""
        contract_path = self.identity_lock_dir / "identity_anchor_contract.json"
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2, ensure_ascii=False)
