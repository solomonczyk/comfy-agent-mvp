"""Tests for State Audit Guard Agent.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

import json
from pathlib import Path
import pytest

from app.agents.state_audit_guard import StateAuditGuardRunner, StateAuditGuardValidator, StateAuditGuardContract, StateAuditGuardArtifacts


class TestStateAuditGuardAgent:
    """Test the state audit guard agent."""

    @pytest.fixture
    def project_root(self):
        return Path("F:/ComfyUI/comfy-agent-mvp")

    @pytest.fixture
    def validator(self, project_root):
        return StateAuditGuardValidator(project_root)

    @pytest.fixture
    def runner(self, project_root):
        return StateAuditGuardRunner(project_root)

    def test_agent_contract_exists(self):
        """Test that the agent contract exists and defines forbidden actions."""
        contract = StateAuditGuardContract.get_contract()

        assert contract["role"] == "state_audit_guard"
        assert contract["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert "claim_visual_acceptance" in contract["forbidden_actions"]
        assert "set_production_accepted_true" in contract["forbidden_actions"]
        assert "fake_operator_decision" in contract["forbidden_actions"]
        assert "approve_for_downstream" in contract["forbidden_actions"]
        assert "trigger_voice_generation" in contract["forbidden_actions"]
        assert "trigger_assembly" in contract["forbidden_actions"]
        assert "perform_generation" in contract["forbidden_actions"]
        assert contract["may_set_production_accepted"] == False
        assert contract["may_authorize_generation"] == False
        assert contract["may_authorize_retry"] == False
        assert contract["may_authorize_render"] == False
        assert contract["may_authorize_downstream"] == False

    def test_tool_policy_exists(self):
        """Test that the tool policy exists and defines forbidden tools."""
        policy = StateAuditGuardContract.get_tool_policy()

        assert policy["policy_id"] == "state_audit_guard_tool_policy"
        assert policy["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert policy["role"] == "state_audit_guard"
        assert "comfyui_submit" in policy["forbidden_tools"]
        assert "image_generation" in policy["forbidden_tools"]
        assert "render_engine" in policy["forbidden_tools"]
        assert policy["no_generation_authorized"] == True
        assert policy["no_retry_authorized"] == True
        assert policy["no_render_authorized"] == True
        assert policy["no_downstream_authorized"] == True

    def test_state_consistency_validation(self, validator):
        """Test state consistency validation."""
        result = validator.validate_state_consistency()

        assert result["report_id"] == "state_consistency_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "findings" in result

    def test_artifact_index_consistency_validation(self, validator):
        """Test artifact index consistency validation."""
        result = validator.validate_artifact_index_consistency()

        assert result["report_id"] == "artifact_index_consistency_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "findings" in result

    def test_episode_ledger_consistency_validation(self, validator):
        """Test episode ledger consistency validation."""
        result = validator.validate_episode_ledger_consistency()

        assert result["report_id"] == "episode_ledger_consistency_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "findings" in result

    def test_proof_consistency_validation(self, validator):
        """Test proof consistency validation."""
        result = validator.validate_proof_consistency()

        assert result["report_id"] == "proof_consistency_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "findings" in result

    def test_forbidden_actions_validation(self, validator):
        """Test forbidden actions validation."""
        result = validator.validate_forbidden_actions()

        assert result["report_id"] == "forbidden_actions_audit_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "violations" in result
        assert "findings" in result

    def test_operator_decisions_validation(self, validator):
        """Test operator decisions validation."""
        result = validator.validate_operator_decisions()

        assert result["report_id"] == "operator_decision_audit_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "fake_decision_detected" in result
        assert "findings" in result

    def test_git_proof_validation(self, validator):
        """Test git proof validation."""
        result = validator.validate_git_proof()

        assert result["report_id"] == "git_proof_audit_report"
        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "valid" in result
        assert "git_dirty" in result
        assert "findings" in result

    def test_run_all_validations(self, validator):
        """Test running all validations."""
        result = validator.run_all_validations()

        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "verdict" in result
        assert result["verdict"] in ("ACCEPTED", "BLOCKED")
        assert "next_state" in result
        assert "next_action" in result
        assert "has_blocker" in result
        assert "blocker_count" in result
        assert "state_consistency" in result
        assert "artifact_index_consistency" in result
        assert "episode_ledger_consistency" in result
        assert "proof_consistency" in result
        assert "forbidden_actions_audit" in result
        assert "operator_decision_audit" in result
        assert "git_proof_audit" in result
        assert "all_findings" in result

    def test_runner_run(self, runner):
        """Test runner run method."""
        result = runner.run()

        assert result["task_id"] == "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        assert result["role"] == "state_audit_guard"
        assert "verdict" in result
        assert result["verdict"] in ("ACCEPTED", "BLOCKED")
        assert "next_state" in result
        assert "next_action" in result
        assert "has_blocker" in result
        assert "validation_results" in result

    def test_artifacts_generate_all(self, runner):
        """Test artifacts generation."""
        validation_results = runner.validator.run_all_validations()
        verdict = "ACCEPTED"
        next_state = "production_gate_review_required"
        next_action = "production_gate_review_required"

        artifacts = StateAuditGuardArtifacts(runner.project_root)
        written = artifacts.generate_all_artifacts(validation_results, verdict, next_state, next_action)

        assert "agent_contract" in written
        assert "tool_policy" in written
        assert "state_consistency_report" in written
        assert "artifact_index_consistency_report" in written
        assert "episode_ledger_consistency_report" in written
        assert "proof_consistency_report" in written
        assert "forbidden_actions_audit_report" in written
        assert "operator_decision_audit_report" in written
        assert "git_proof_audit_report" in written
        assert "final_report" in written

        # Verify files exist
        for artifact_path in written.values():
            assert Path(artifact_path).exists()

    def test_accepted_verdict_transitions_to_production_gate_review_required(self, runner):
        """Test that accepted verdict transitions to production_gate_review_required."""
        result = runner.run()

        if result["verdict"] == "ACCEPTED":
            assert result["next_state"] == "production_gate_review_required"
            assert result["next_action"] == "production_gate_review_required"
        elif result["verdict"] == "BLOCKED":
            assert result["next_state"] == "state_audit_blocker_resolution_required"
            assert result["next_action"] == "state_audit_blocker_resolution_required"
