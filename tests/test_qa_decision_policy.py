"""Tests for QA decision policy module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.decision_policy import DEFAULT_DECISION_POLICY, apply_decision_policy, load_decision_policy


class TestDecisionPolicyLoading:
    def test_default_policy_loaded(self):
        policy = load_decision_policy()
        assert policy["policy_id"] == "visual_qa_decision_policy_v1"
        assert "bad_teeth" in policy["auto_reject_if"]
        assert "borderline_skin_texture" in policy["operator_review_if"]
        assert policy["production_accepted_allowed"] is False

    def test_load_from_file(self, tmp_path):
        policy_data = {
            "policy_id": "test_policy",
            "auto_reject_if": ["test_defect"],
            "operator_review_if": [],
            "production_accepted_allowed": False,
        }
        policy_file = tmp_path / "visual_qa_decision_policy.json"
        with open(policy_file, "w") as f:
            json.dump(policy_data, f)
        policy = load_decision_policy(tmp_path)
        assert policy["policy_id"] == "test_policy"

    def test_fallback_on_missing_file(self):
        policy = load_decision_policy(Path("/nonexistent"))
        assert policy["policy_id"] == "visual_qa_decision_policy_v1"


class TestDecisionPolicyApplication:
    def test_auto_reject_single_defect(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(policy, critical_failures=["bad_teeth"], all_detected_defects=["bad_teeth"])
        assert result["decision"] == "reject"
        assert result["auto_rejected_by"] == ["bad_teeth"]
        assert result["recommended_next_action"] == "v13_correction_plan_required"

    def test_auto_reject_multiple_defects(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy,
            critical_failures=["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"],
            all_detected_defects=["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"],
        )
        assert result["decision"] == "reject"
        assert len(result["auto_rejected_by"]) >= 1

    def test_operator_review_triggered(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy,
            critical_failures=[],
            all_detected_defects=["borderline_skin_texture"],
        )
        assert result["decision"] == "operator_review_required"
        assert "borderline_skin_texture" in result["operator_review_by"]

    def test_candidate_ok(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(policy, critical_failures=[], all_detected_defects=[])
        assert result["decision"] == "candidate_ok_for_pipeline_review"

    def test_mixed_defects_auto_reject_wins(self):
        """When both auto-reject and operator-review defects are present, auto-reject wins."""
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy,
            critical_failures=["bad_teeth"],
            all_detected_defects=["bad_teeth", "borderline_skin_texture"],
        )
        assert result["decision"] == "reject"

    def test_production_accepted_always_false(self):
        policy = DEFAULT_DECISION_POLICY
        for defects in ([], ["bad_teeth"], ["borderline_skin_texture"]):
            result = apply_decision_policy(policy, critical_failures=defects, all_detected_defects=defects)
            assert result["production_accepted"] is False
            assert result["assembly_allowed"] is False
            assert result["downstream_allowed"] is False

    def test_auto_reject_if_in_critical_failures_only(self):
        """Even if a defect isn't in all_detected_defects, being in critical_failures triggers auto-reject."""
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy,
            critical_failures=["bad_teeth"],
            all_detected_defects=[],
        )
        assert result["decision"] == "reject"
        assert "bad_teeth" in result["auto_rejected_by"]

    def test_auto_reject_if_in_both_lists_no_duplicates(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy,
            critical_failures=["bad_teeth", "unnatural_mouth"],
            all_detected_defects=["bad_teeth", "unnatural_mouth"],
        )
        assert result["decision"] == "reject"
        # Each defect should appear only once in the list
        assert len(result["auto_rejected_by"]) == len(set(result["auto_rejected_by"]))
