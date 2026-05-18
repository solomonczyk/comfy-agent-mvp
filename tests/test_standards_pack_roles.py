"""Tests for standards pack role standards.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_standards_pack_dir() -> Path:
    """Return the standards pack directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control/standards_pack")


def load_role(role_name: str) -> dict:
    """Load a role standard by name."""
    path = get_standards_pack_dir() / "roles" / f"{role_name}_standard.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestQAAgentStandard:
    """Test QA Agent role standard."""

    def test_qa_agent_standard_exists(self):
        """qa_agent_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "qa_agent_standard.json"
        assert path.exists()

    def test_qa_agent_has_role_id(self):
        """QA Agent must have role_id."""
        role = load_role("qa_agent")
        assert role.get("role_id") == "qa_agent"

    def test_qa_agent_cannot_claim_visual_acceptance(self):
        """QA Agent must not be able to claim visual acceptance."""
        role = load_role("qa_agent")
        forbidden = role.get("forbidden_actions", [])
        assert "claim_visual_acceptance" in forbidden

    def test_qa_agent_cannot_set_production_accepted(self):
        """QA Agent must not be able to set production_accepted=true."""
        role = load_role("qa_agent")
        forbidden = role.get("forbidden_actions", [])
        assert "set_production_accepted_true" in forbidden

    def test_qa_agent_cannot_fake_operator_decision(self):
        """QA Agent must forbid fake operator decision."""
        role = load_role("qa_agent")
        forbidden = role.get("forbidden_actions", [])
        assert "fake_operator_decision" in forbidden

    def test_qa_agent_has_quality_focused_responsibilities(self):
        """QA Agent must have quality-focused responsibilities."""
        role = load_role("qa_agent")
        resp = role.get("responsibilities", [])
        resp_str = " ".join(resp).lower()
        assert "quality" in resp_str or "defect" in resp_str or "metric" in resp_str


class TestQCAgentStandard:
    """Test QC Agent role standard."""

    def test_qc_agent_standard_exists(self):
        """qc_agent_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "qc_agent_standard.json"
        assert path.exists()

    def test_qc_agent_has_role_id(self):
        """QC Agent must have role_id."""
        role = load_role("qc_agent")
        assert role.get("role_id") == "qc_agent"

    def test_qc_agent_cannot_claim_visual_acceptance(self):
        """QC Agent must not be able to claim visual acceptance."""
        role = load_role("qc_agent")
        forbidden = role.get("forbidden_actions", [])
        assert "claim_visual_acceptance" in forbidden

    def test_qc_agent_cannot_set_production_accepted(self):
        """QC Agent must not be able to set production_accepted=true."""
        role = load_role("qc_agent")
        forbidden = role.get("forbidden_actions", [])
        assert "set_production_accepted_true" in forbidden

    def test_qc_agent_has_process_compliance_focus(self):
        """QC Agent must have process compliance responsibilities."""
        role = load_role("qc_agent")
        resp = role.get("responsibilities", [])
        resp_str = " ".join(resp).lower()
        assert "process" in resp_str or "compliance" in resp_str or "audit" in resp_str


class TestTesterStandard:
    """Test Tester role standard."""

    def test_tester_standard_exists(self):
        """tester_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "tester_standard.json"
        assert path.exists()

    def test_tester_has_role_id(self):
        """Tester must have role_id."""
        role = load_role("tester")
        assert role.get("role_id") == "tester"

    def test_tester_cannot_claim_visual_acceptance(self):
        """Tester must not be able to claim visual acceptance."""
        role = load_role("tester")
        forbidden = role.get("forbidden_actions", [])
        assert "claim_visual_acceptance" in forbidden

    def test_tester_cannot_set_production_accepted(self):
        """Tester must not be able to set production_accepted=true."""
        role = load_role("tester")
        forbidden = role.get("forbidden_actions", [])
        assert "set_production_accepted_true" in forbidden

    def test_tester_has_reproducibility_focus(self):
        """Tester must have reproducibility/schema/CLI responsibilities."""
        role = load_role("tester")
        resp = role.get("responsibilities", [])
        resp_str = " ".join(resp).lower()
        assert any(x in resp_str for x in ["reproducibility", "schema", "cli", "test"])


class TestVisualQAAgentStandard:
    """Test Visual QA Agent role standard."""

    def test_visual_qa_agent_standard_exists(self):
        """visual_qa_agent_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "visual_qa_agent_standard.json"
        assert path.exists()

    def test_visual_qa_agent_cannot_approve_production(self):
        """Visual QA Agent cannot approve production."""
        role = load_role("visual_qa_agent")
        cannot_decide = role.get("cannot_decide", [])
        assert "production_acceptance" in cannot_decide or "visual_acceptance" in cannot_decide


class TestScriptSupervisorStandard:
    """Test Script Supervisor role standard."""

    def test_script_supervisor_standard_exists(self):
        """script_supervisor_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "script_supervisor_standard.json"
        assert path.exists()


class TestStateAuditGuardStandard:
    """Test State Audit Guard role standard."""

    def test_state_audit_guard_standard_exists(self):
        """state_audit_guard_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "state_audit_guard_standard.json"
        assert path.exists()


class TestOperatorReviewStandard:
    """Test Operator Review role standard."""

    def test_operator_review_standard_exists(self):
        """operator_review_standard.json must exist."""
        path = get_standards_pack_dir() / "roles" / "operator_review_standard.json"
        assert path.exists()

    def test_operator_review_is_human_only(self):
        """Operator Review must be marked as human-only authority."""
        role = load_role("operator_review")
        # Should forbid delegating to agent
        forbidden = role.get("forbidden_actions", [])
        assert "delegate_decision_to_agent" in forbidden

    def test_operator_can_decide_visual_acceptance(self):
        """Operator must have visual_acceptance in decision_rights."""
        role = load_role("operator_review")
        rights = role.get("decision_rights", [])
        assert "visual_acceptance" in rights

    def test_operator_can_decide_production_acceptance(self):
        """Operator must have production_acceptance in decision_rights."""
        role = load_role("operator_review")
        rights = role.get("decision_rights", [])
        assert "production_acceptance" in rights


class TestRoleSeparation:
    """Test that QA/QC/Tester roles are properly separated."""

    def test_qa_qc_tester_are_distinct_roles(self):
        """QA, QC, and Tester must have different role_ids."""
        qa = load_role("qa_agent")
        qc = load_role("qc_agent")
        tester = load_role("tester")

        assert qa.get("role_id") != qc.get("role_id")
        assert qa.get("role_id") != tester.get("role_id")
        assert qc.get("role_id") != tester.get("role_id")

    def test_qa_focuses_on_quality_not_process(self):
        """QA focuses on output quality, not process compliance."""
        qa = load_role("qa_agent")
        resp = " ".join(qa.get("responsibilities", [])).lower()
        # QA should focus on quality, defects, metrics
        assert any(x in resp for x in ["quality", "defect", "metric"])

    def test_qc_focuses_on_process_not_output_quality(self):
        """QC focuses on process compliance, not output quality."""
        qc = load_role("qc_agent")
        resp = " ".join(qc.get("responsibilities", [])).lower()
        # QC should focus on process, compliance, state
        assert any(x in resp for x in ["process", "compliance", "state", "audit"])

    def test_tester_focuses_on_reproducibility(self):
        """Tester focuses on reproducibility, schemas, CLI."""
        tester = load_role("tester")
        resp = " ".join(tester.get("responsibilities", [])).lower()
        assert any(x in resp for x in ["reproducibility", "schema", "cli", "test", "regression"])
