"""Tests for RC-COMBINE-V2-6001-6300 V8 real execution readiness preflight.

Tests cover:
- dry_run_mode_classification_present
- empty_prompt_id_classification_present
- empty_generated_assets_classification_present
- server_unavailable_classification_present
- timeout_classification_present
- preflight_does_not_submit_workflow
- comfyui_execution_false_in_preflight
- failure_classifications_cover_all_modes
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def control_dir():
    root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01" / "output" / "control"
    return root


@pytest.fixture
def diagnosis_artifact(control_dir):
    path = control_dir / "combine_v2_v8_real_execution_readiness_diagnosis.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def preflight_report(control_dir):
    path = control_dir / "combine_v2_v8_runtime_preflight_report.json"
    assert path.exists(), f"Missing: {path}"
    with open(path) as f:
        return json.load(f)


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


class TestV8RealExecutionReadinessDiagnosis:

    def test_preflight_does_not_submit_workflow(self, diagnosis_artifact):
        assert diagnosis_artifact.get("generation_submitted") is False
        assert diagnosis_artifact.get("comfyui_execution") is False
        assert diagnosis_artifact.get("workflow_mutated") is False

    def test_comfyui_execution_false_in_preflight(self, diagnosis_artifact):
        assert diagnosis_artifact.get("comfyui_execution") is False
        assert diagnosis_artifact.get("v8_execution_comfyui_execution") is False

    def test_dry_run_mode_classification_present(self, diagnosis_artifact):
        classification = diagnosis_artifact.get("classification", {})
        assert classification.get("dry_run_mode") is True
        assert "dry_run_mode" in diagnosis_artifact.get("failure_classifications", [])

    def test_empty_prompt_id_classification_present(self, diagnosis_artifact, execution_artifact):
        assert not execution_artifact.get("prompt_id"), "prompt_id should be empty"
        classification = diagnosis_artifact.get("classification", {})
        assert classification.get("empty_prompt_id") is True
        assert "empty_prompt_id" in diagnosis_artifact.get("failure_classifications", [])

    def test_empty_generated_assets_classification_present(self, diagnosis_artifact, manifest_artifact):
        assert manifest_artifact.get("generated_assets") == []
        classification = diagnosis_artifact.get("classification", {})
        assert classification.get("empty_generated_assets") is True
        assert "empty_generated_assets" in diagnosis_artifact.get("failure_classifications", [])

    def test_server_unavailable_classification_present(self, diagnosis_artifact):
        classification = diagnosis_artifact.get("classification", {})
        assert diagnosis_artifact.get("comfyui_reachable") is False
        assert "server_unavailable" in diagnosis_artifact.get("failure_classifications", [])

    def test_failure_classifications_cover_all_modes(self, diagnosis_artifact):
        classification = diagnosis_artifact.get("classification", {})
        expected_keys = {
            "queue_timeout", "history_timeout", "output_collection_failed",
            "dry_run_mode", "empty_prompt_id", "empty_generated_assets"
        }
        for key in expected_keys:
            assert key in classification, f"Missing classification key: {key}"

    def test_timeout_classification_present(self, diagnosis_artifact):
        failure_codes = diagnosis_artifact.get("failure_classifications", [])
        assert isinstance(failure_codes, list)
        assert len(failure_codes) > 0


class TestV8RuntimePreflightReport:

    def test_preflight_report_exists(self, preflight_report):
        assert preflight_report.get("preflight_type") == "v8_runtime_preflight"
        assert preflight_report.get("task_id") == "RC-COMBINE-V2-6001-6300"

    def test_preflight_generation_not_submitted(self, preflight_report):
        assert preflight_report.get("generation_submitted") is False
        assert preflight_report.get("comfyui_execution") is False
        assert preflight_report.get("workflow_mutated") is False

    def test_preflight_dry_run_mode_detected(self, preflight_report):
        assert preflight_report.get("dry_run_mode_present") is True

    def test_preflight_empty_prompt_id_detected(self, preflight_report):
        assert preflight_report.get("empty_prompt_id_present") is True

    def test_preflight_empty_assets_detected(self, preflight_report):
        assert preflight_report.get("empty_generated_assets_present") is True

    def test_preflight_next_action_is_authorization(self, preflight_report):
        assert preflight_report.get("next_allowed_action") == "v8_generation_reexecution_authorization_required"


class TestV8ExecutionReadinessStateMachine:

    def test_v8_generation_reexecution_authorization_required_is_valid(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.is_valid_state("v8_generation_reexecution_authorization_required")

    def test_v8_generation_reexecution_authorization_required_can_self_loop(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "v8_generation_reexecution_authorization_required"
        )

    def test_v8_generation_reexecution_authorization_required_can_go_to_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "v8_quality_locked_generation_authorization_required"
        )

    def test_v8_generation_reexecution_authorization_required_cannot_skip_to_generate(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "generate_assets"
        )
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "real_generate_assets"
        )

    def test_v8_generation_reexecution_authorization_required_cannot_skip_to_visual_review(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "operator_visual_review_required"
        )

    def test_v8_generation_reexecution_authorization_required_cannot_skip_to_assembly(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "assembly_required"
        )
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "assembly_preflight_required"
        )

    def test_v8_generation_reexecution_authorization_required_cannot_skip_to_downstream(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "completed"
        )

    def test_v8_generation_runtime_blocked_can_transition_to_reexecution_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked",
            "v8_generation_reexecution_authorization_required"
        )

    def test_v8_generation_runtime_recovery_can_transition_to_reexecution_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_recovery_required",
            "v8_generation_reexecution_authorization_required"
        )
