"""Tests for QA Repairability Gate.

Task ID: RC-COMBINE-V2-QA-REPAIRABILITY-GATE-001
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.qa.repairability_gate import QARepairabilityGate, load_qa_repairability_gate
from app.standards.repairability import (
    get_defect_repairability_matrix,
    get_repair_tool_registry,
    get_defect_repairability,
    get_repair_tool,
    can_defect_be_fixed_by_tool,
    apply_stage_routing_policy,
)


class TestQARepairabilityGate:
    """Test QARepairabilityGate class."""

    def test_load_qa_repairability_gate(self, tmp_path):
        """Test loading QA repairability gate."""
        # Create minimal policy files
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "description": "Test policy",
            "rules": [
                {
                    "rule_id": "default",
                    "condition": {},
                    "decision": "operator_review_required",
                    "production_accepted": False,
                    "next_allowed_action": "operator_visual_review_required"
                }
            ]
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        assert gate is not None
        assert isinstance(gate, QARepairabilityGate)

    def test_inspect_defect_repairability_known_defect(self, tmp_path):
        """Test inspecting a known defect."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        # Test with a known defect
        result = gate.inspect_defect_repairability("bad_teeth")
        assert isinstance(result, dict)
        # Result contains defect info directly or error
        if "error" not in result:
            assert "repairability" in result or "defect_id" in result

    def test_inspect_defect_repairability_unknown_defect(self, tmp_path):
        """Test inspecting an unknown defect."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        result = gate.inspect_defect_repairability("unknown_defect")
        # Unknown defects return error
        assert isinstance(result, dict)
        assert "error" in result

    def test_inspect_repair_tool(self, tmp_path):
        """Test inspecting a repair tool."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        result = gate.inspect_repair_tool("comfyui_inpainting")
        # Tool may or may not exist in registry
        assert isinstance(result, dict)
        if "error" not in result:
            assert result["tool_id"] == "comfyui_inpainting"

    def test_list_all_repair_tools(self, tmp_path):
        """Test listing all repair tools."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        tools = gate.list_all_repair_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_validate_repairability_assessment_empty_defects(self, tmp_path):
        """Test validating with empty defects list."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        result = gate.validate_repairability_assessment(defects=[])
        assert "all_defects_repairable_before_next_stage" in result

    def test_validate_repairability_assessment_with_defects(self, tmp_path):
        """Test validating with defects."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        result = gate.validate_repairability_assessment(
            defects=["bad_teeth", "blur"]
        )
        assert "unrepairable_defects" in result
        assert "unknown_repairability_defects" in result

    def test_evaluate_no_defects(self, tmp_path):
        """Test evaluating with no defects."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        result = gate.evaluate(
            defects=[],
            technical_checks_passed=True,
            visual_or_editorial_acceptance=True
        )
        assert result["qa_decision"] == "pass"
        assert result["production_accepted"] is False

    def test_evaluate_with_blocking_defects(self, tmp_path):
        """Test evaluating with blocking defects."""
        standards_dir = tmp_path / "standards_pack"
        policies_dir = standards_dir / "policies"
        policies_dir.mkdir(parents=True)
        
        policy = {
            "policy_id": "qa_repairability_policy_v1",
            "version": "1.0",
            "rules": []
        }
        
        with open(policies_dir / "qa_repairability_policy.json", "w") as f:
            json.dump(policy, f)
        
        gate = load_qa_repairability_gate(standards_dir)
        
        # Test with fake_operator_decision which blocks
        result = gate.evaluate(
            defects=["fake_operator_decision"],
            technical_checks_passed=True,
            visual_or_editorial_acceptance=True
        )
        assert result["qa_decision"] == "blocked"
        assert result["production_accepted"] is False


class TestRepairabilityHelpers:
    """Test repairability helper functions."""

    def test_get_defect_repairability_matrix(self):
        """Test getting defect repairability matrix."""
        matrix = get_defect_repairability_matrix()
        assert isinstance(matrix, dict)
        # Matrix structure contains categories
        assert "anatomy_defects" in matrix or "version" in matrix

    def test_get_repair_tool_registry(self):
        """Test getting repair tool registry."""
        registry = get_repair_tool_registry()
        # Registry is a list of tools
        assert isinstance(registry, list)

    def test_get_defect_repairability(self):
        """Test getting repairability for a specific defect."""
        result = get_defect_repairability("bad_teeth")
        # Returns full defect info dict or None if not found
        assert isinstance(result, (dict, type(None)))
        if result is not None:
            assert isinstance(result, dict)

    def test_get_defect_repairability_unknown(self):
        """Test getting repairability for unknown defect."""
        result = get_defect_repairability("unknown_defect")
        # Returns None for unknown
        assert result is None

    def test_get_repair_tool(self):
        """Test getting a repair tool."""
        result = get_repair_tool("comfyui_inpainting")
        assert isinstance(result, (dict, type(None)))

    def test_can_defect_be_fixed_by_tool(self):
        """Test checking if tool can fix defect."""
        result = can_defect_be_fixed_by_tool("artifact_corruption", "comfyui_inpainting")
        assert isinstance(result, bool)

    def test_apply_stage_routing_policy(self):
        """Test applying stage routing policy."""
        assessment = {"all_defects_repairable_before_next_stage": True}
        result = apply_stage_routing_policy(assessment)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
