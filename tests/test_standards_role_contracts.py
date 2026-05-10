"""Tests for role standard validator and QA/QC/Tester separation."""

import json
from pathlib import Path

import pytest

from app.standards.role_standard_validator import RoleStandardValidator


@pytest.fixture
def role_pack(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test_manifest",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"roles": "roles"},
        "artifacts": {
            "qa_agent_standard": "roles/qa_agent_standard.json",
            "qc_agent_standard": "roles/qc_agent_standard.json",
            "tester_standard": "roles/tester_standard.json",
            "operator_review_standard": "roles/operator_review_standard.json",
        },
    }
    (pack_dir / "standards_pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (pack_dir / "roles").mkdir()

    def make_role(role_id, responsibilities, forbidden):
        return {
            "role_id": role_id,
            "role_name": role_id.replace("_", " ").title(),
            "responsibilities": responsibilities,
            "inputs_required": [],
            "outputs_required": [],
            "allowed_tools": [],
            "forbidden_actions": forbidden,
            "decision_rights": [],
            "cannot_decide": [],
            "blocker_rules": [],
            "required_artifacts": [],
            "proof_requirements": [],
        }

    qa = make_role(
        "qa_agent",
        ["Evaluate outputs against quality rules", "Record technical metrics"],
        ["fake_operator_decision", "set_production_accepted_true", "claim_visual_acceptance"],
    )
    (pack_dir / "roles" / "qa_agent_standard.json").write_text(json.dumps(qa), encoding="utf-8")

    qc = make_role(
        "qc_agent",
        ["Verify process compliance", "Audit state transitions"],
        ["fake_operator_decision", "set_production_accepted_true"],
    )
    (pack_dir / "roles" / "qc_agent_standard.json").write_text(json.dumps(qc), encoding="utf-8")

    tester = make_role(
        "tester",
        ["Validate schemas", "Test CLI behavior", "Check reproducibility"],
        ["fake_operator_decision"],
    )
    (pack_dir / "roles" / "tester_standard.json").write_text(json.dumps(tester), encoding="utf-8")

    operator = make_role(
        "operator_review",
        ["Make final decisions"],
        ["delegate_decision_to_agent", "fake_operator_decision"],
    )
    (pack_dir / "roles" / "operator_review_standard.json").write_text(json.dumps(operator), encoding="utf-8")

    return pack_dir


def test_role_validation_passes(role_pack):
    validator = RoleStandardValidator(role_pack)
    result = validator.validate()
    assert result["valid"] is True
    assert not result["errors"]


def test_missing_operator_review_role(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"roles": "roles"},
        "artifacts": {},
    }
    (pack_dir / "standards_pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pack_dir / "roles").mkdir()
    validator = RoleStandardValidator(pack_dir)
    result = validator.validate()
    assert result["valid"] is False
    assert any("operator_review_standard missing" in err for err in result["errors"])


def test_qa_missing_forbidden_action(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"roles": "roles"},
        "artifacts": {"qa_agent_standard": "roles/qa_agent_standard.json"},
    }
    (pack_dir / "standards_pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pack_dir / "roles").mkdir()
    qa = {
        "role_id": "qa_agent",
        "role_name": "QA Agent",
        "responsibilities": [],
        "inputs_required": [],
        "outputs_required": [],
        "allowed_tools": [],
        "forbidden_actions": [],
        "decision_rights": [],
        "cannot_decide": [],
        "blocker_rules": [],
        "required_artifacts": [],
        "proof_requirements": [],
    }
    (pack_dir / "roles" / "qa_agent_standard.json").write_text(json.dumps(qa), encoding="utf-8")
    validator = RoleStandardValidator(pack_dir)
    result = validator.validate()
    assert result["valid"] is False
    assert any("fake_operator_decision" in err for err in result["errors"])
