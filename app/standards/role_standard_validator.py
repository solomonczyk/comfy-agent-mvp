"""Role Standard Validator — validates role separation and forbidden actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set

from .standards_pack_loader import StandardsPackLoader


class RoleStandardValidator:
    """Validates role standards for correct separation of concerns."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        self.loader = StandardsPackLoader(standards_pack_dir)
        self._roles: Dict[str, Any] = {}

    def load_roles(self) -> None:
        self.loader.load_artifacts()
        self._roles = {
            key: val
            for key, val in self.loader.artifacts.items()
            if isinstance(val, dict) and "role_id" in val
        }

    def validate(self) -> Dict[str, Any]:
        """Run all role validation checks."""
        if not self._roles:
            self.load_roles()

        errors: List[str] = []
        warnings: List[str] = []

        # Check each role has required fields
        required_fields = [
            "role_id", "role_name", "responsibilities", "inputs_required",
            "outputs_required", "allowed_tools", "forbidden_actions",
            "decision_rights", "cannot_decide", "blocker_rules",
            "required_artifacts", "proof_requirements",
        ]
        for key, role in self._roles.items():
            for field in required_fields:
                if field not in role:
                    errors.append(f"Role '{key}' missing required field: {field}")

        # Check QA/QC/Tester separation
        separation_errors = self._check_role_separation()
        errors.extend(separation_errors)

        # Check operator_review is human-only
        operator = self._roles.get("operator_review_standard")
        if operator:
            forbidden = operator.get("forbidden_actions", [])
            if "delegate_decision_to_agent" not in forbidden:
                errors.append("Operator Review standard must forbid 'delegate_decision_to_agent'")
        else:
            errors.append("operator_review_standard missing")

        # Check no role allows fake operator decision
        for key, role in self._roles.items():
            forbidden = role.get("forbidden_actions", [])
            if "fake_operator_decision" not in forbidden:
                errors.append(f"Role '{key}' must forbid 'fake_operator_decision'")

        # Check QA cannot set production_accepted
        qa = self._roles.get("qa_agent_standard")
        if qa:
            forbidden = qa.get("forbidden_actions", [])
            if "set_production_accepted_true" not in forbidden:
                errors.append("QA Agent standard must forbid 'set_production_accepted_true'")
            if "claim_visual_acceptance" not in forbidden:
                errors.append("QA Agent standard must forbid 'claim_visual_acceptance'")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _check_role_separation(self) -> List[str]:
        """Ensure QA, QC, and Tester have distinct responsibilities."""
        errors: List[str] = []
        qa = self._roles.get("qa_agent_standard")
        qc = self._roles.get("qc_agent_standard")
        tester = self._roles.get("tester_standard")

        if not qa or not qc or not tester:
            errors.append("QA, QC, and Tester role standards must all exist")
            return errors

        qa_resp = set(qa.get("responsibilities", []))
        qc_resp = set(qc.get("responsibilities", []))
        tester_resp = set(tester.get("responsibilities", []))

        # Overlap is allowed for shared concerns (e.g., "report defects"),
        # but core responsibilities must differ.
        qa_core = {r for r in qa_resp if "quality rules" in r or "technical metrics" in r}
        qc_core = {r for r in qc_resp if "process compliance" in r or "state transitions" in r}
        tester_core = {r for r in tester_resp if "reproducibility" in r or "CLI behavior" in r or "schemas" in r}

        if not qa_core:
            errors.append("QA Agent must have quality-rules-focused responsibilities")
        if not qc_core:
            errors.append("QC Agent must have process-compliance-focused responsibilities")
        if not tester_core:
            errors.append("Tester must have reproducibility/schemas/CLI-focused responsibilities")

        return errors
