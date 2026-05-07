"""Tests for RC-COMBINE-V2-5701-6000-RECOVERY V8 generation timeout reconciliation.

Tests cover:
- operator_visual_review_blocked_without_generated_asset
- dry_run_not_accepted_as_real_generation
- prompt_id_empty_blocks_history_success_claim
- manifest_zero_assets_blocks_visual_review
- runtime_timeout_recorded
- no_new_generation_performed
- no_second_generation_attempted
- state_repaired_when_no_asset
- state_allows_visual_review_only_if_asset_exists
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
    return root


@pytest.fixture
def control_dir(project_root):
    return project_root / "output" / "control"


@pytest.fixture
def execution_artifact(control_dir):
    path = control_dir / "combine_v2_v8_quality_locked_generation_execution.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def manifest_artifact(control_dir):
    path = control_dir / "combine_v2_v8_quality_locked_outputs_manifest.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def result_review_artifact(control_dir):
    path = control_dir / "combine_v2_v8_quality_locked_generation_result_review.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def visual_review_packet_artifact(control_dir):
    path = control_dir / "combine_v2_v8_operator_visual_review_packet.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def reconciliation_artifact(control_dir):
    path = control_dir / "combine_v2_v8_generation_timeout_reconciliation.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def artifact_index(control_dir):
    path = control_dir / "artifact_index.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def episode_ledger(control_dir):
    path = control_dir / "episode_ledger.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


class TestV8GenerationTimeoutReconciliation:

    def test_operator_visual_review_blocked_without_generated_asset(
        self, result_review_artifact, visual_review_packet_artifact
    ):
        assert result_review_artifact.get("operator_visual_review_blocked_without_generated_asset") is True
        assert visual_review_packet_artifact.get("visual_review_blocked_no_image") is True
        assert visual_review_packet_artifact.get("operator_visual_review_required") is False

    def test_dry_run_not_accepted_as_real_generation(
        self, result_review_artifact
    ):
        assert result_review_artifact.get("dry_run_not_accepted_as_real_generation") is True

    def test_prompt_id_empty_blocks_history_success_claim(
        self, execution_artifact, result_review_artifact
    ):
        assert execution_artifact.get("prompt_id_available") is False
        assert execution_artifact.get("comfyui_history_check_possible") is False
        assert result_review_artifact.get("prompt_id_empty_blocks_history_success_claim") is True

    def test_manifest_zero_assets_blocks_visual_review(
        self, manifest_artifact
    ):
        assert manifest_artifact.get("zero_assets_block_visual_review") is True
        assert manifest_artifact.get("generated_assets") == []
        assert manifest_artifact.get("canonical_outputs_registered") is False

    def test_runtime_timeout_recorded(
        self, execution_artifact, result_review_artifact
    ):
        assert execution_artifact.get("generation_timeout") is True
        assert result_review_artifact.get("runtime_timeout_recorded") is True

    def test_no_new_generation_performed(
        self, execution_artifact, reconciliation_artifact
    ):
        assert execution_artifact.get("new_generation_performed") is False
        assert execution_artifact.get("generation_performed") is False
        assert reconciliation_artifact.get("new_generation_performed") is False

    def test_no_second_generation_attempted(
        self, execution_artifact, reconciliation_artifact, artifact_index
    ):
        assert execution_artifact.get("second_generation_attempted") is False
        assert reconciliation_artifact.get("second_generation_attempted") is False
        assert artifact_index.get("no_second_generation_attempted") is True

    def test_state_repaired_when_no_asset(
        self, artifact_index, reconciliation_artifact
    ):
        assert artifact_index.get("current_state") == "v8_generation_runtime_blocked"
        assert artifact_index.get("next_allowed_action") == "v8_generation_runtime_recovery_required"
        assert reconciliation_artifact.get("reconciled_from_state") == "v8_operator_visual_review_required"
        assert reconciliation_artifact.get("reconciled_to_state") == "v8_generation_runtime_blocked"

    def test_state_allows_visual_review_only_if_asset_exists(
        self, artifact_index, execution_artifact
    ):
        assert artifact_index.get("generated_assets") == []
        assert execution_artifact.get("generated_asset_found") is None or execution_artifact.get("comfyui_execution") is False
        assert artifact_index.get("operator_visual_review_packet_created") is False
        assert artifact_index.get("v8_operator_visual_review_packet_created") is False


class TestReconciliationArtifact:

    def test_reconciliation_artifact_exists(self, reconciliation_artifact):
        assert reconciliation_artifact.get("task_id") == "RC-COMBINE-V2-5701-6000-RECOVERY"
        assert reconciliation_artifact.get("timeout_reconciliation_executed") is True

    def test_no_new_generation_in_reconciliation(self, reconciliation_artifact):
        assert reconciliation_artifact.get("new_generation_performed") is False
        assert reconciliation_artifact.get("new_comfyui_submit_executed") is False
        assert reconciliation_artifact.get("second_generation_attempted") is False
        assert reconciliation_artifact.get("retry_attempted") is False

    def test_reconciliation_prompt_id_findings(self, reconciliation_artifact):
        assert reconciliation_artifact.get("prompt_id_found") is False

    def test_reconciliation_native_output_check(self, reconciliation_artifact):
        assert reconciliation_artifact.get("native_output_checked") is True
        assert reconciliation_artifact.get("canonical_assets_checked") is True
        assert reconciliation_artifact.get("existing_v8_asset_found") is False

    def test_reconciliation_blocks_downstream(self, reconciliation_artifact):
        assert reconciliation_artifact.get("operator_visual_review_allowed") is False
        assert reconciliation_artifact.get("visual_acceptance_executed") is False
        assert reconciliation_artifact.get("assembly_executed") is False
        assert reconciliation_artifact.get("downstream_executed") is False
        assert reconciliation_artifact.get("production_accepted") is False

    def test_reconciliation_correct_state(self, reconciliation_artifact):
        assert reconciliation_artifact.get("current_state") == "v8_generation_runtime_blocked"
        assert reconciliation_artifact.get("next_allowed_action") == "v8_generation_runtime_recovery_required"

    def test_reconciliation_contradictions_documented(self, reconciliation_artifact):
        contradictions = reconciliation_artifact.get("blocking_contradictions_found", [])
        assert len(contradictions) >= 6
        assert any("new_generation_performed=false but generation_count=1" in c for c in contradictions)
        assert any("comfyui_execution=false" in c for c in contradictions)
        assert any("prompt_id is empty" in c for c in contradictions)
        assert any("state incorrectly moved" in c for c in contradictions)


class TestEpisodeLedger:

    def test_ledger_contains_reconciliation_event(self, episode_ledger):
        events = [e for e in episode_ledger if e.get("event_type") == "v8_generation_timeout_reconciliation"]
        assert len(events) >= 1
        event = events[0]
        assert event.get("task_id") == "RC-COMBINE-V2-5701-6000-RECOVERY"

    def test_ledger_reconciliation_blocks(self, episode_ledger):
        events = [e for e in episode_ledger if e.get("event_type") == "v8_generation_timeout_reconciliation"]
        assert len(events) >= 1
        event = events[0]
        assert event.get("new_generation_performed") is False
        assert event.get("operator_visual_review_allowed") is False
        assert event.get("production_accepted") is False

    def test_ledger_state_correct_after_reconciliation(self, episode_ledger):
        events = [e for e in episode_ledger if e.get("event_type") == "v8_generation_timeout_reconciliation"]
        assert len(events) >= 1
        event = events[0]
        assert event.get("current_state") == "v8_generation_runtime_blocked"
        assert event.get("next_allowed_action") == "v8_generation_runtime_recovery_required"

    def test_ledger_previous_generation_event_reconciled(self, episode_ledger):
        gen_events = [e for e in episode_ledger if e.get("event_type") == "v8_quality_locked_generation_executed"]
        assert len(gen_events) >= 1
        event = gen_events[0]
        assert event.get("reconciliation_applied") == "RC-COMBINE-V2-5701-6000-RECOVERY"
        assert event.get("current_state") == "v8_generation_runtime_blocked"


class TestStateMachine:

    def test_v8_generation_runtime_blocked_is_valid(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.is_valid_state("v8_generation_runtime_blocked")

    def test_v8_generation_runtime_recovery_required_is_valid(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.is_valid_state("v8_generation_runtime_recovery_required")

    def test_v8_generation_runtime_blocked_can_self_loop(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked", "v8_generation_runtime_blocked"
        )

    def test_v8_generation_runtime_blocked_can_transition_to_recovery(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked", "v8_generation_runtime_recovery_required"
        )

    def test_v8_generation_runtime_blocked_can_restart_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked", "v8_quality_locked_generation_authorization_required"
        )

    def test_v8_generation_runtime_recovery_can_self_loop(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_recovery_required", "v8_generation_runtime_recovery_required"
        )

    def test_v8_generation_runtime_recovery_can_go_to_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_recovery_required", "v8_quality_locked_generation_authorization_required"
        )

    def test_v8_generation_runtime_recovery_can_go_to_blocked_manual_review(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_recovery_required", "blocked_manual_review"
        )

    def test_operator_visual_review_allowed_only_via_authorization_not_from_runtime_blocked(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked", "operator_visual_review_required"
        )
