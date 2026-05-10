"""Standards Integration Layer — orchestrates standards-driven QA/QC/Tester workflows.

RC-COMBINE-V2-QA-QC-TESTER-STANDARDS-INTEGRATION-001
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .standards_pack_loader import StandardsPackLoader
from .standards_pack_validator import StandardsPackValidator
from .standards_registry import StandardsRegistry
from .decision_policy_engine import DecisionPolicyEngine
from .role_standard_validator import RoleStandardValidator


class StandardsIntegration:
    """Main integration layer for standards-driven controls."""

    REQUIRED_CATEGORIES = [
        "roles", "policies", "internal", "references", "schemas", "reports"
    ]

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.standards_pack_dir = self.control_dir / "standards_pack"
        self.integration_dir = self.control_dir / "standards_integration"
        self._loader: Optional[StandardsPackLoader] = None
        self._validator: Optional[StandardsPackValidator] = None
        self._registry: Optional[StandardsRegistry] = None
        self._policy_engine: Optional[DecisionPolicyEngine] = None
        self._role_validator: Optional[RoleStandardValidator] = None
        self._pack_version: str = "unknown"

    def load_standards_pack(self) -> Dict[str, Any]:
        """Load the standards pack and cache references."""
        if not self.standards_pack_dir.exists():
            return {
                "success": False,
                "error": "standards_pack directory does not exist",
                "path": str(self.standards_pack_dir),
            }
        self._loader = StandardsPackLoader(self.standards_pack_dir)
        self._validator = StandardsPackValidator(self.standards_pack_dir)
        self._registry = StandardsRegistry(self.standards_pack_dir)
        self._policy_engine = DecisionPolicyEngine(self.standards_pack_dir)
        self._role_validator = RoleStandardValidator(self.standards_pack_dir)

        data = self._loader.load_all()
        manifest = data.get("manifest", {})
        self._pack_version = manifest.get("version", "unknown")
        return {
            "success": True,
            "version": self._pack_version,
            "artifact_count": len(data.get("artifacts", {})),
        }

    def validate_required_categories(self) -> Dict[str, Any]:
        """Ensure all required categories exist in the standards pack."""
        if self._loader is None:
            self.load_standards_pack()
        missing = []
        manifest = self._loader.manifest if self._loader else {}
        directories = manifest.get("directories", {})
        for cat in self.REQUIRED_CATEGORIES:
            if cat not in directories:
                missing.append(cat)
        return {
            "valid": not missing,
            "missing": missing,
            "required": self.REQUIRED_CATEGORIES,
        }

    def resolve_rule_by_id(self, rule_id: str) -> Dict[str, Any]:
        """Find a rule by ID across all policy artifacts."""
        if self._loader is None:
            self.load_standards_pack()
        artifacts = self._loader.artifacts if self._loader else {}
        for key, artifact in artifacts.items():
            if isinstance(artifact, dict):
                rules = artifact.get("rules", [])
                for rule in rules:
                    if isinstance(rule, dict) and rule.get("rule_id") == rule_id:
                        return {
                            "found": True,
                            "policy_key": key,
                            "rule": rule,
                        }
        return {"found": False, "rule_id": rule_id}

    def resolve_policy_by_id(self, policy_id: str) -> Dict[str, Any]:
        """Find a policy artifact by policy_id."""
        if self._registry is None:
            self.load_standards_pack()
        policy = self._registry.get_policy(policy_id) if self._registry else {}
        if "error" in policy:
            return {"found": False, "policy_id": policy_id, "error": policy["error"]}
        return {"found": True, "policy_id": policy_id, "policy": policy}

    def map_defect_to_severity(self, defect_id: str) -> Dict[str, Any]:
        """Look up a defect in the defect taxonomy and return its severity."""
        if self._loader is None:
            self.load_standards_pack()
        taxonomy = self._loader.artifacts.get("defect_taxonomy", {}) if self._loader else {}
        defects = taxonomy.get("defects", []) if isinstance(taxonomy, dict) else []
        for defect in defects:
            if defect.get("defect_id") == defect_id:
                return {
                    "found": True,
                    "defect_id": defect_id,
                    "severity": defect.get("severity_default", "unknown"),
                    "category": defect.get("category", "unknown"),
                    "blocks": defect.get("blocks", []),
                }
        return {"found": False, "defect_id": defect_id}

    def map_severity_to_decision(self, severity: str) -> Dict[str, Any]:
        """Map a severity level to a decision outcome using the severity model."""
        if self._loader is None:
            self.load_standards_pack()
        severity_model = self._loader.artifacts.get("severity_model", {}) if self._loader else {}
        levels = severity_model.get("levels", []) if isinstance(severity_model, dict) else []
        for level in levels:
            if level.get("level") == severity:
                return {
                    "severity": severity,
                    "decision": level.get("default_decision", "operator_review_required"),
                    "blocks": level.get("blocks", []),
                }
        # Fallback mapping
        fallback = {
            "blocker": "blocked",
            "critical": "operator_review_required",
            "major": "warning",
            "warning": "pass_with_warning",
            "info": "pass",
        }
        return {
            "severity": severity,
            "decision": fallback.get(severity, "operator_review_required"),
            "blocks": ["production_acceptance"] if severity in ("blocker", "critical") else [],
        }

    def produce_role_specific_decision(
        self, role: str, conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate all policies applicable to a role and return a unified decision."""
        if self._policy_engine is None:
            self.load_standards_pack()
        role_standard = self._registry.get_role_standard(role) if self._registry else {}
        policies_to_check = []
        if isinstance(role_standard, dict):
            # Check role-specific policies by convention
            policy_map = {
                "qa_agent": "qa_decision_policy",
                "qc_agent": "qc_acceptance_matrix",
                "tester": "tester_validation_matrix",
                "visual_qa_agent": "visual_rejection_policy",
                "script_supervisor": "preview_acceptance_policy",
                "state_audit_guard": "fake_success_policy",
                "operator_review": "production_acceptance_policy",
            }
            primary_policy = policy_map.get(role)
            if primary_policy:
                policies_to_check.append(primary_policy)

        results = []
        for policy_id in policies_to_check:
            result = self._policy_engine.evaluate(policy_id, conditions) if self._policy_engine else {}
            results.append({"policy_id": policy_id, "result": result})

        # Determine overall decision
        decisions = [r["result"].get("decision", "no_match") for r in results]
        overall = self._aggregate_decisions(decisions)

        return {
            "role": role,
            "overall_decision": overall,
            "policy_results": results,
            "standards_pack_version": self._pack_version,
            "traceable": True,
        }

    def return_traceable_rule_references(
        self, role: str, source_artifact: str, decision: str, severity: str
    ) -> Dict[str, Any]:
        """Return a traceable result with explicit standard references."""
        # Find applicable rules for this role
        rule_refs = []
        if self._loader is None:
            self.load_standards_pack()
        artifacts = self._loader.artifacts if self._loader else {}
        for key, artifact in artifacts.items():
            if isinstance(artifact, dict):
                rules = artifact.get("rules", [])
                for rule in rules:
                    # Simple heuristic: role appears in rule or policy applies
                    if isinstance(rule, dict):
                        rule_id = rule.get("rule_id", "")
                        if role.replace("_", "") in rule_id.lower() or role in rule_id.lower():
                            rule_refs.append({
                                "rule_id": rule_id,
                                "policy_key": key,
                            })

        return {
            "standards_pack_version": self._pack_version,
            "standard_id": f"{role}_standard",
            "policy_id": f"{role}_decision_policy",
            "rule_id": rule_refs[0]["rule_id"] if rule_refs else "default",
            "role": role,
            "severity": severity,
            "decision": decision,
            "source_artifact": source_artifact,
            "traceable": True,
            "rule_references": rule_refs,
        }

    def build_validation_report(self) -> Dict[str, Any]:
        """Validation report for the integration layer itself."""
        load_result = self.load_standards_pack()
        valid = load_result.get("success", False)
        categories = self.validate_required_categories()
        return {
            "report_id": "standards_integration_validation_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-QA-QC-TESTER-STANDARDS-INTEGRATION-001",
            "valid": valid and categories.get("valid", False),
            "standards_pack_loaded": valid,
            "required_categories_present": categories.get("valid", False),
            "missing_categories": categories.get("missing", []),
            "traceable": True,
        }

    @staticmethod
    def _aggregate_decisions(decisions: List[str]) -> str:
        priority = ["blocked", "rejected", "operator_review_required", "warning", "pass"]
        for p in priority:
            if p in decisions:
                return p
        return "operator_review_required"

    def ensure_integration_dir(self) -> Path:
        self.integration_dir.mkdir(parents=True, exist_ok=True)
        return self.integration_dir

    def write_artifact(self, name: str, data: Dict[str, Any]) -> Path:
        path = self.ensure_integration_dir() / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
