"""Standards Decision Adapter — adapts standards-based decisions for role-specific outputs.

RC-COMBINE-V2-QA-QC-TESTER-STANDARDS-INTEGRATION-001
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .standards_integration import StandardsIntegration


class StandardsDecisionAdapter:
    """Adapts raw policy evaluations into role-specific, traceable decisions."""

    ROLE_ALIAS = {
        "qa": "qa_agent",
        "qc": "qc_agent",
        "tester": "tester",
        "visual_qa": "visual_qa_agent",
        "script_supervisor": "script_supervisor",
        "state_audit": "state_audit_guard",
        "operator_review": "operator_review",
    }

    def __init__(self, project_root: str | Path) -> None:
        self.integration = StandardsIntegration(project_root)

    def adapt(
        self,
        role: str,
        conditions: Dict[str, Any],
        source_artifact: str = "",
    ) -> Dict[str, Any]:
        """Produce a fully traceable, role-specific decision result."""
        role_key = self.ROLE_ALIAS.get(role, role)
        load_result = self.integration.load_standards_pack()
        if not load_result.get("success"):
            return self._error_result(role, source_artifact, load_result.get("error", "unknown"))

        role_standard = self.integration._registry.get_role_standard(role_key) if self.integration._registry else {}
        if "error" in role_standard:
            return self._error_result(role, source_artifact, role_standard["error"])

        # Evaluate policies for role
        decision_result = self.integration.produce_role_specific_decision(role_key, conditions)
        overall = decision_result.get("overall_decision", "operator_review_required")

        # Determine severity based on decision
        severity = self._decision_to_severity(overall)

        # Find a representative rule reference
        rule_ref = self._find_representative_rule(role_key, overall)

        return {
            "standards_pack_version": self.integration._pack_version,
            "standard_id": f"{role_key}_standard",
            "policy_id": rule_ref.get("policy_id", f"{role_key}_decision_policy"),
            "rule_id": rule_ref.get("rule_id", "default"),
            "role": role,
            "severity": severity,
            "decision": overall,
            "source_artifact": source_artifact,
            "traceable": True,
            "policy_results": decision_result.get("policy_results", []),
        }

    def evaluate_defect(
        self,
        role: str,
        defect_id: str,
        source_artifact: str = "",
    ) -> Dict[str, Any]:
        """Evaluate a specific defect through the standards and return adapted decision."""
        defect_info = self.integration.map_defect_to_severity(defect_id)
        if not defect_info.get("found"):
            return self._error_result(role, source_artifact, f"defect '{defect_id}' not found")

        severity = defect_info["severity"]
        severity_map = self.integration.map_severity_to_decision(severity)
        decision = severity_map.get("decision", "operator_review_required")

        rule_ref = self._find_representative_rule(self.ROLE_ALIAS.get(role, role), decision)

        return {
            "standards_pack_version": self.integration._pack_version,
            "standard_id": f"{self.ROLE_ALIAS.get(role, role)}_standard",
            "policy_id": rule_ref.get("policy_id", "severity_model"),
            "rule_id": rule_ref.get("rule_id", f"severity_{severity}"),
            "role": role,
            "severity": severity,
            "decision": decision,
            "source_artifact": source_artifact,
            "traceable": True,
            "defect_info": defect_info,
        }

    def _find_representative_rule(self, role_key: str, decision: str) -> Dict[str, str]:
        """Find a rule that matches the role/decision."""
        if self.integration._loader is None:
            self.integration.load_standards_pack()
        artifacts = self.integration._loader.artifacts if self.integration._loader else {}
        for key, artifact in artifacts.items():
            if isinstance(artifact, dict):
                for rule in artifact.get("rules", []):
                    if rule.get("decision") == decision:
                        return {"policy_id": key, "rule_id": rule.get("rule_id", "unknown")}
        return {"policy_id": f"{role_key}_decision_policy", "rule_id": "default"}

    @staticmethod
    def _decision_to_severity(decision: str) -> str:
        mapping = {
            "blocked": "blocker",
            "rejected": "critical",
            "operator_review_required": "major",
            "warning": "warning",
            "pass_with_warning": "warning",
            "pass": "info",
        }
        return mapping.get(decision, "warning")

    @staticmethod
    def _error_result(role: str, source_artifact: str, error: str) -> Dict[str, Any]:
        return {
            "standards_pack_version": "unknown",
            "standard_id": f"{role}_standard",
            "policy_id": "unknown",
            "rule_id": "unknown",
            "role": role,
            "severity": "blocker",
            "decision": "blocked",
            "source_artifact": source_artifact,
            "traceable": True,
            "error": error,
        }
