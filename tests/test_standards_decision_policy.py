"""Tests for decision policy engine."""

import json
from pathlib import Path

import pytest

from app.standards.decision_policy_engine import DecisionPolicyEngine


@pytest.fixture
def policy_pack(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test_manifest",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"policies": "policies"},
        "artifacts": {
            "qa_decision_policy": "policies/qa_decision_policy.json",
            "blocker_policy": "policies/blocker_policy.json",
        },
    }
    (pack_dir / "standards_pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (pack_dir / "policies").mkdir()
    qa_policy = {
        "policy_id": "qa_decision_policy",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "technical_pass_not_visual_pass",
                "condition": {"technical_checks_passed": True, "operator_visual_review_executed": False},
                "decision": "operator_review_required",
                "production_accepted": False,
            },
            {
                "rule_id": "technical_fail_blocks",
                "condition": {"technical_checks_passed": False, "critical_defects_found": True},
                "decision": "blocked",
                "production_accepted": False,
            },
        ],
    }
    (pack_dir / "policies" / "qa_decision_policy.json").write_text(
        json.dumps(qa_policy), encoding="utf-8"
    )
    blocker_policy = {
        "policy_id": "blocker_policy",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "any_blocker_blocks",
                "condition": {"any_blocker_present": True},
                "decision": "blocked",
                "production_accepted": False,
            }
        ],
    }
    (pack_dir / "policies" / "blocker_policy.json").write_text(
        json.dumps(blocker_policy), encoding="utf-8"
    )
    return pack_dir


def test_evaluate_operator_review_required(policy_pack):
    engine = DecisionPolicyEngine(policy_pack)
    result = engine.evaluate(
        "qa_decision_policy",
        {"technical_checks_passed": True, "operator_visual_review_executed": False},
    )
    assert result["decision"] == "operator_review_required"
    assert result["production_accepted"] is False


def test_evaluate_blocked(policy_pack):
    engine = DecisionPolicyEngine(policy_pack)
    result = engine.evaluate(
        "qa_decision_policy",
        {"technical_checks_passed": False, "critical_defects_found": True},
    )
    assert result["decision"] == "blocked"
    assert result["production_accepted"] is False


def test_evaluate_no_match(policy_pack):
    engine = DecisionPolicyEngine(policy_pack)
    result = engine.evaluate(
        "qa_decision_policy",
        {"technical_checks_passed": True, "operator_visual_review_executed": True},
    )
    assert result["decision"] == "no_match"


def test_evaluate_all_policies(policy_pack):
    engine = DecisionPolicyEngine(policy_pack)
    results = engine.evaluate_all({"any_blocker_present": True})
    assert len(results) == 1
    assert results[0]["decision"] == "blocked"
