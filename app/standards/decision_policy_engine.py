"""Decision Policy Engine — evaluates simple decision policies from input conditions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .standards_pack_loader import StandardsPackLoader


class DecisionPolicyEngine:
    """Evaluates decision policy rules against a set of input conditions."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        self.loader = StandardsPackLoader(standards_pack_dir)
        self._policies: Dict[str, Any] = {}

    def load_policies(self) -> None:
        self.loader.load_artifacts()
        self._policies = {
            key: val
            for key, val in self.loader.artifacts.items()
            if isinstance(val, dict) and "rules" in val
        }

    def evaluate(self, policy_id: str, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate conditions against a policy's rules and return the matched decision."""
        if not self._policies:
            self.load_policies()
        policy = self._policies.get(policy_id)
        if policy is None:
            return {"error": f"Policy '{policy_id}' not found"}

        matched_rules: List[Dict[str, Any]] = []
        for rule in policy.get("rules", []):
            if self._match(rule.get("condition", {}), conditions):
                matched_rules.append(rule)

        if not matched_rules:
            return {
                "policy_id": policy_id,
                "decision": "no_match",
                "matched_rules": [],
                "production_accepted": False,
            }

        # Return the first matched rule (policies are ordered by specificity)
        first = matched_rules[0]
        return {
            "policy_id": policy_id,
            "matched_rule_id": first.get("rule_id"),
            "decision": first.get("decision"),
            "production_accepted": first.get("production_accepted", False),
            "blocks": first.get("blocks", []),
            "next_allowed_action": first.get("next_allowed_action"),
            "all_matched_rules": [r.get("rule_id") for r in matched_rules],
        }

    def evaluate_all(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate conditions against all loaded policies."""
        if not self._policies:
            self.load_policies()
        results = []
        for policy_id in sorted(self._policies):
            result = self.evaluate(policy_id, conditions)
            if result.get("matched_rule_id"):
                results.append(result)
        return results

    @staticmethod
    def _match(rule_condition: Dict[str, Any], input_conditions: Dict[str, Any]) -> bool:
        """Check whether input conditions satisfy the rule condition."""
        for key, expected in rule_condition.items():
            actual = input_conditions.get(key)
            if actual is None:
                return False
            if isinstance(expected, dict):
                # Support simple operators like ">", "<", etc.
                op = list(expected.keys())[0]
                val = expected[op]
                if op == ">" and not (actual > val):
                    return False
                if op == ">=" and not (actual >= val):
                    return False
                if op == "<" and not (actual < val):
                    return False
                if op == "<=" and not (actual <= val):
                    return False
                if op == "!=" and not (actual != val):
                    return False
            elif actual != expected:
                return False
        return True
