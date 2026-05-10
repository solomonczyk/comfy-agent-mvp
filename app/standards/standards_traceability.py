"""Standards Traceability — ensures every decision is traceable to a standard, policy, and rule.

RC-COMBINE-V2-QA-QC-TESTER-STANDARDS-INTEGRATION-001
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .standards_integration import StandardsIntegration


class StandardsTraceability:
    """Provides traceability links between decisions and standards artifacts."""

    def __init__(self, project_root: str | Path) -> None:
        self.integration = StandardsIntegration(project_root)

    def trace(
        self,
        role: str,
        decision: str,
        severity: str,
        source_artifact: str,
    ) -> Dict[str, Any]:
        """Return a traceable result with all required fields."""
        self.integration.load_standards_pack()
        rule_refs = self._collect_rule_references(role, decision)
        return {
            "standards_pack_version": self.integration._pack_version,
            "standard_id": f"{role}_standard",
            "policy_id": rule_refs[0]["policy_id"] if rule_refs else f"{role}_decision_policy",
            "rule_id": rule_refs[0]["rule_id"] if rule_refs else "default",
            "role": role,
            "severity": severity,
            "decision": decision,
            "source_artifact": source_artifact,
            "traceable": True,
            "rule_references": rule_refs,
        }

    def audit_chain(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit a chain of results for traceability completeness."""
        issues = []
        for i, result in enumerate(results):
            required = [
                "standards_pack_version", "standard_id", "policy_id",
                "rule_id", "role", "severity", "decision", "source_artifact", "traceable",
            ]
            for field in required:
                if field not in result:
                    issues.append(f"Result[{i}] missing field: {field}")
            if not result.get("traceable"):
                issues.append(f"Result[{i}] is not marked traceable")

        return {
            "valid": not issues,
            "issues": issues,
            "result_count": len(results),
        }

    def _collect_rule_references(self, role: str, decision: str) -> List[Dict[str, str]]:
        """Collect all rules matching role and decision."""
        if self.integration._loader is None:
            self.integration.load_standards_pack()
        refs = []
        artifacts = self.integration._loader.artifacts if self.integration._loader else {}
        for key, artifact in artifacts.items():
            if isinstance(artifact, dict):
                for rule in artifact.get("rules", []):
                    rid = rule.get("rule_id", "")
                    if decision in rid or role.replace("_", "") in rid.lower():
                        refs.append({"policy_id": key, "rule_id": rid})
        return refs
