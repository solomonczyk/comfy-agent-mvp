"""Tests for standards pack policies.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_standards_pack_dir() -> Path:
    """Return the standards pack directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control/standards_pack")


def load_policy(policy_name: str) -> dict:
    """Load a policy by name."""
    path = get_standards_pack_dir() / "policies" / f"{policy_name}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestFakeSuccessPolicy:
    """Test fake success policy."""

    def test_fake_success_policy_exists(self):
        """fake_success_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "fake_success_policy.json"
        assert path.exists()

    def test_fake_success_policy_blocks_acceptance(self):
        """Fake success policy must block production acceptance."""
        policy = load_policy("fake_success_policy")
        rules = policy.get("rules", [])

        # Find rule that blocks on fake success
        blocking_rules = [r for r in rules if r.get("decision") == "blocked"]
        assert len(blocking_rules) > 0, "No blocking rules found in fake_success_policy"

    def test_fake_success_indicators_defined(self):
        """Policy must define fake success indicators."""
        policy = load_policy("fake_success_policy")
        indicators = policy.get("fake_success_indicators", [])
        assert len(indicators) > 0
        # Should include dry_run_reported_as_real
        assert any("dry_run" in i.lower() for i in indicators)


class TestNoBlindRetryPolicy:
    """Test no blind retry policy."""

    def test_no_blind_retry_policy_exists(self):
        """no_blind_retry_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "no_blind_retry_policy.json"
        assert path.exists()

    def test_blind_retry_forbidden(self):
        """Policy must forbid blind retry."""
        policy = load_policy("no_blind_retry_policy")
        # Should have rules about retry conditions
        rules = policy.get("rules", [])
        assert len(rules) > 0


class TestForbiddenActionsPolicy:
    """Test forbidden actions policy."""

    def test_forbidden_actions_policy_exists(self):
        """forbidden_actions_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "forbidden_actions_policy.json"
        assert path.exists()

    def test_generation_forbidden_without_authorization(self):
        """Generation should be forbidden without proper authorization."""
        policy = load_policy("forbidden_actions_policy")
        forbidden = policy.get("forbidden_actions", [])
        forbidden_str = json.dumps(forbidden).lower()
        # Check for hidden_generation or other generation-related forbidden actions
        assert "generation" in forbidden_str or "submit" in forbidden_str or "hidden" in forbidden_str


class TestProductionAcceptancePolicy:
    """Test production acceptance policy."""

    def test_production_acceptance_policy_exists(self):
        """production_acceptance_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "production_acceptance_policy.json"
        assert path.exists()

    def test_production_acceptance_requires_operator_gate(self):
        """Production acceptance must require operator gate."""
        policy = load_policy("production_acceptance_policy")
        rules = policy.get("rules", [])

        # Find rule about production acceptance
        prod_rules = [r for r in rules if "production" in str(r).lower()]
        assert len(prod_rules) > 0, "No production acceptance rules found"

        # Should require operator approval
        policy_str = json.dumps(policy).lower()
        assert "operator" in policy_str, "Policy should reference operator"


class TestBlockerPolicy:
    """Test blocker policy."""

    def test_blocker_policy_exists(self):
        """blocker_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "blocker_policy.json"
        assert path.exists()


class TestQADecisionPolicy:
    """Test QA decision policy."""

    def test_qa_decision_policy_exists(self):
        """qa_decision_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "qa_decision_policy.json"
        assert path.exists()


class TestQCAcceptanceMatrix:
    """Test QC acceptance matrix."""

    def test_qc_acceptance_matrix_exists(self):
        """qc_acceptance_matrix.json must exist."""
        path = get_standards_pack_dir() / "policies" / "qc_acceptance_matrix.json"
        assert path.exists()


class TestTesterValidationMatrix:
    """Test tester validation matrix."""

    def test_tester_validation_matrix_exists(self):
        """tester_validation_matrix.json must exist."""
        path = get_standards_pack_dir() / "policies" / "tester_validation_matrix.json"
        assert path.exists()


class TestVisualRejectionPolicy:
    """Test visual rejection policy."""

    def test_visual_rejection_policy_exists(self):
        """visual_rejection_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "visual_rejection_policy.json"
        assert path.exists()


class TestPreviewAcceptancePolicy:
    """Test preview acceptance policy."""

    def test_preview_acceptance_policy_exists(self):
        """preview_acceptance_policy.json must exist."""
        path = get_standards_pack_dir() / "policies" / "preview_acceptance_policy.json"
        assert path.exists()


class TestHardRules:
    """Test hard rules across policies."""

    def test_technical_pass_is_not_visual_pass(self):
        """Technical pass must not automatically mean visual pass."""
        # Check across all role standards
        roles_dir = get_standards_pack_dir() / "roles"
        for role_file in roles_dir.glob("*_standard.json"):
            with open(role_file, "r", encoding="utf-8") as f:
                role = json.load(f)

            # QA Agent should have blocker rule about this
            if role.get("role_id") == "qa_agent":
                blocker_rules = role.get("blocker_rules", [])
                rule_str = json.dumps(blocker_rules).lower()
                assert "technical" in rule_str and "visual" in rule_str, \
                    "QA Agent must have blocker rule about technical pass != visual pass"

    def test_agent_cannot_decide_production_acceptance(self):
        """No agent role can decide production acceptance."""
        roles_dir = get_standards_pack_dir() / "roles"

        agent_roles = ["qa_agent", "qc_agent", "tester", "visual_qa_agent"]

        for role_name in agent_roles:
            role_file = roles_dir / f"{role_name}_standard.json"
            if role_file.exists():
                with open(role_file, "r", encoding="utf-8") as f:
                    role = json.load(f)

                cannot_decide = role.get("cannot_decide", [])
                assert "production_acceptance" in cannot_decide, \
                    f"{role_name} must not be able to decide production_acceptance"

                forbidden = role.get("forbidden_actions", [])
                assert "set_production_accepted_true" in forbidden, \
                    f"{role_name} must forbid set_production_accepted_true"

    def test_production_accepted_requires_final_operator_gate(self):
        """Production acceptance requires operator final gate."""
        policy = load_policy("production_acceptance_policy")
        policy_str = json.dumps(policy).lower()

        assert "operator" in policy_str, "Policy must reference operator"
        assert "final" in policy_str or "human" in policy_str or "review" in policy_str, \
            "Policy must indicate operator final gate"

    def test_blind_retry_is_forbidden(self):
        """Blind retry must be forbidden."""
        policy = load_policy("no_blind_retry_policy")
        policy_str = json.dumps(policy).lower()

        assert "blind" in policy_str or "retry" in policy_str

    def test_fake_success_is_forbidden(self):
        """Fake success must be forbidden."""
        policy = load_policy("fake_success_policy")
        rules = policy.get("rules", [])

        # Should have at least one blocking rule
        blocking_rules = [r for r in rules if r.get("decision") == "blocked"]
        assert len(blocking_rules) > 0
