"""QA Repairability Gate — enforces downstream repairability checks before pipeline progression.

This module implements the gate that ensures QA checks not just whether output
technically exists, but whether defects can be repaired by downstream stages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.standards.repairability import (
    assess_repairability,
    apply_stage_routing_policy,
    get_defect_repairability_matrix,
    get_repair_tool_registry,
)


class QARepairabilityGate:
    """Enforces repairability checks before allowing pipeline progression."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        """Initialize the repairability gate with standards pack directory."""
        self.standards_pack_dir = Path(standards_pack_dir)
        self._policy: Dict[str, Any] = {}
        self._routing_policy: Dict[str, Any] = {}

    def load_policies(self) -> None:
        """Load QA repairability policy and downstream routing policy."""
        # Load QA repairability policy
        qa_policy_path = (
            self.standards_pack_dir / "policies" / "qa_repairability_policy.json"
        )
        if qa_policy_path.exists():
            with open(qa_policy_path, "r", encoding="utf-8") as f:
                self._policy = json.load(f)

        # Load downstream routing policy
        routing_policy_path = (
            self.standards_pack_dir / "policies" / "downstream_repairability_gate_policy.json"
        )
        if routing_policy_path.exists():
            with open(routing_policy_path, "r", encoding="utf-8") as f:
                self._routing_policy = json.load(f)

    def evaluate(
        self,
        defects: List[str],
        technical_checks_passed: bool,
        visual_or_editorial_acceptance: bool,
        generation_gate_open: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate QA decision with repairability assessment.

        Args:
            defects: List of detected defect IDs
            technical_checks_passed: Whether technical checks passed
            visual_or_editorial_acceptance: Whether visual/editorial acceptance achieved
            generation_gate_open: Whether generation gate is open

        Returns:
            QA decision with repairability assessment
        """
        # Assess repairability of defects
        repairability_assessment = assess_repairability(defects)

        # Apply hard blocking rules
        qa_decision = self._apply_hard_blocking_rules(
            repairability_assessment,
            technical_checks_passed,
            visual_or_editorial_acceptance,
            generation_gate_open,
            defects,
        )

        # Apply stage routing policy
        next_action = apply_stage_routing_policy(repairability_assessment)

        # Construct full decision output
        return {
            "qa_decision": qa_decision,
            "technical_checks_passed": technical_checks_passed,
            "visual_or_editorial_acceptance": visual_or_editorial_acceptance,
            "defects": defects,
            "repairability_assessment": repairability_assessment,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "voice_generation_allowed": False,
            "next_allowed_action": next_action,
        }

    def _apply_hard_blocking_rules(
        self,
        repairability_assessment: Dict[str, Any],
        technical_checks_passed: bool,
        visual_or_editorial_acceptance: bool,
        generation_gate_open: bool,
        defects: List[str],
    ) -> str:
        """Apply hard blocking rules to determine QA decision."""
        # Rule: Block if not repairable downstream
        if not repairability_assessment.get("all_defects_repairable_before_next_stage", True):
            return "blocked"

        # Rule: Block if unknown repairability
        unknown_defects = repairability_assessment.get("unknown_repairability_defects", [])
        if unknown_defects:
            return "blocked"

        # Rule: Block if technical-only pass treated as visual pass
        if technical_checks_passed and not visual_or_editorial_acceptance:
            return "blocked"

        # Rule: Block if fake operator decision detected
        if "fake_operator_decision" in defects:
            return "blocked"

        # Rule: Block if repair requires generation but gate not open
        required_fix_stage = repairability_assessment.get("required_fix_stage", "")
        if "generation" in required_fix_stage.lower() and not generation_gate_open:
            return "blocked"

        # Rule: Needs operator review if required
        if "operator_review" in required_fix_stage.lower():
            return "needs_operator_review"

        # Rule: Requires corrective plan if fix stage is specified
        if required_fix_stage:
            return "requires_corrective_plan"

        # Default: Pass
        return "pass"

    def inspect_defect_repairability(self, defect_id: str) -> Dict[str, Any]:
        """Inspect repairability information for a specific defect."""
        matrix = get_defect_repairability_matrix()
        return matrix.get(defect_id, {"error": f"Defect '{defect_id}' not found in matrix"})

    def inspect_repair_tool(self, tool_id: str) -> Dict[str, Any]:
        """Inspect a specific repair tool from the registry."""
        registry = get_repair_tool_registry()
        for tool in registry:
            if tool["tool_id"] == tool_id:
                return dict(tool)
        return {"error": f"Tool '{tool_id}' not found in registry"}

    def list_all_repair_tools(self) -> List[Dict[str, Any]]:
        """List all repair tools in the registry."""
        return get_repair_tool_registry()

    def validate_repairability_assessment(
        self, defects: List[str], available_tools: List[str] | None = None
    ) -> Dict[str, Any]:
        """Validate repairability assessment without applying blocking rules.

        Returns detailed assessment including which defects are repairable
        and which tools would be needed.
        """
        assessment = assess_repairability(defects, available_tools)

        # Add detailed tool information
        tool_details = []
        for defect_id in defects:
            defect_info = self.inspect_defect_repairability(defect_id)
            if "error" not in defect_info:
                fix_paths = defect_info.get("allowed_fix_paths", [])
                for path in fix_paths:
                    # Check if path corresponds to a tool
                    tool_info = self.inspect_repair_tool(path)
                    if "error" not in tool_info:
                        tool_details.append({
                            "defect_id": defect_id,
                            "tool_id": tool_info["tool_id"],
                            "available": tool_info.get("available", False),
                            "validated": tool_info.get("validated", False),
                        })

        assessment["tool_details"] = tool_details
        return assessment


def load_qa_repairability_gate(standards_pack_dir: str | Path) -> QARepairabilityGate:
    """Load and initialize QA repairability gate."""
    gate = QARepairabilityGate(standards_pack_dir)
    gate.load_policies()
    return gate
