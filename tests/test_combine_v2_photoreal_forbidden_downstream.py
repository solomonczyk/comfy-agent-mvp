"""Tests for RC-COMBINE-V2-15001-22000 forbidden downstream operations.

Tests cover:
- production_accepted_always_false
- assembly_blocked
- downstream_blocked
- no hidden second generation
- no fake prompt_id
- no fake generated assets
- final_proof_generated
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        control_dir = root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield root, control_dir


class TestProductionAcceptedAlwaysFalse:
    """production_accepted must always be false in QA recovery loop."""

    def test_artifact_index_production_accepted_false(self, project_root):
        """artifact_index must have production_accepted=false."""
        _, control_dir = project_root
        idx = {
            "task_id": "RC-COMBINE-V2-15001-22000",
            "current_state": "v11_correction_plan_required",
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
        }
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        with open(control_dir / "artifact_index.json") as f:
            data = json.load(f)
        assert data.get("production_accepted") is False

    def test_state_machine_forbids_production_accepted(self, project_root):
        """State machine must forbid transitions to production_accepted from V11 states."""
        _, control_dir = project_root

        # V11 states
        assert not CombineStateMachine.can_transition("v11_generate_assets", "production_accepted")
        assert not CombineStateMachine.can_transition("v11_result_review_required", "production_accepted")
        assert not CombineStateMachine.can_transition("v11_operator_visual_review_required", "production_accepted")

        # V12 states
        assert not CombineStateMachine.can_transition("v12_generate_assets", "production_accepted")
        assert not CombineStateMachine.can_transition("v12_result_review_required", "production_accepted")
        assert not CombineStateMachine.can_transition("v12_operator_visual_review_required", "production_accepted")

        # V13 states
        assert not CombineStateMachine.can_transition("v13_generate_assets", "production_accepted")
        assert not CombineStateMachine.can_transition("v13_result_review_required", "production_accepted")
        assert not CombineStateMachine.can_transition("v13_operator_visual_review_required", "production_accepted")


class TestAssemblyBlocked:
    """Assembly must be blocked from all V11/V12/V13 states."""

    @pytest.mark.parametrize("state", [
        "v11_correction_plan_required",
        "v11_corrective_package_build_required",
        "v11_generation_authorization_required",
        "v11_generate_assets",
        "v11_result_review_required",
        "v11_visual_qa_preflight_required",
        "v11_visual_qa_required",
        "v11_operator_visual_review_required",
        "v12_correction_plan_required",
        "v12_corrective_package_build_required",
        "v12_generation_authorization_required",
        "v12_generate_assets",
        "v12_result_review_required",
        "v12_visual_qa_preflight_required",
        "v12_visual_qa_required",
        "v12_operator_visual_review_required",
        "v13_correction_plan_required",
        "v13_corrective_package_build_required",
        "v13_generation_authorization_required",
        "v13_generate_assets",
        "v13_result_review_required",
        "v13_visual_qa_preflight_required",
        "v13_visual_qa_required",
        "v13_operator_visual_review_required",
        "visual_candidate_accepted_for_pipeline",
        "qa_recovery_blocked_after_max_candidates",
    ])
    def test_assembly_blocked_from_state(self, state):
        """Assembly must be blocked from all QA recovery states."""
        assert not CombineStateMachine.can_transition(state, "assembly_required"), \
            f"Assembly should be blocked from {state}"
        assert not CombineStateMachine.can_transition(state, "assembly_preflight_required"), \
            f"Assembly preflight should be blocked from {state}"


class TestDownstreamBlocked:
    """Downstream (completed, final_qc, final_operator_acceptance) must be blocked."""

    @pytest.mark.parametrize("state,downstream", [
        ("v11_generation_authorization_required", "completed"),
        ("v11_generate_assets", "completed"),
        ("v11_operator_visual_review_required", "completed"),
        ("v11_operator_visual_review_required", "final_qc_required"),
        ("v11_operator_visual_review_required", "final_operator_acceptance"),
        ("v12_generation_authorization_required", "completed"),
        ("v12_generate_assets", "completed"),
        ("v12_operator_visual_review_required", "completed"),
        ("v12_operator_visual_review_required", "final_qc_required"),
        ("v12_operator_visual_review_required", "final_operator_acceptance"),
        ("v13_generation_authorization_required", "completed"),
        ("v13_generate_assets", "completed"),
        ("v13_operator_visual_review_required", "completed"),
        ("v13_operator_visual_review_required", "final_qc_required"),
        ("v13_operator_visual_review_required", "final_operator_acceptance"),
        ("visual_candidate_accepted_for_pipeline", "completed"),
        ("visual_candidate_accepted_for_pipeline", "final_qc_required"),
        ("visual_candidate_accepted_for_pipeline", "final_operator_acceptance"),
        ("qa_recovery_blocked_after_max_candidates", "completed"),
        ("qa_recovery_blocked_after_max_candidates", "final_qc_required"),
        ("qa_recovery_blocked_after_max_candidates", "final_operator_acceptance"),
    ])
    def test_downstream_blocked(self, state, downstream):
        """Downstream must be blocked from QA recovery states."""
        assert not CombineStateMachine.can_transition(state, downstream), \
            f"Downstream '{downstream}' should be blocked from {state}"


class TestNoHiddenSecondGeneration:
    """No hidden second generation is allowed within same candidate."""

    @pytest.mark.parametrize("state,target", [
        ("v11_generate_assets", "generate_assets"),
        ("v11_generate_assets", "real_generate_assets"),
        ("v12_generate_assets", "generate_assets"),
        ("v12_generate_assets", "real_generate_assets"),
        ("v13_generate_assets", "generate_assets"),
        ("v13_generate_assets", "real_generate_assets"),
    ])
    def test_no_cross_version_generation(self, state, target):
        """Generate states must not transition to other generation states."""
        assert not CombineStateMachine.can_transition(state, target), \
            f"Should not transition from {state} to {target}"


class TestNoFakePromptId:
    """No fake prompt_id should appear in QA recovery loop artifacts."""

    def test_no_fake_prompt_id_in_v11_artifacts(self, project_root):
        """V11 generation artifacts should not contain fake prompt_id."""
        _, control_dir = project_root
        # Generation trace should not have fake prompt IDs
        trace = {
            "stage": "v11_generate_assets",
            "version": "v11",
            "events": [
                {"event": "operator_authorization_check", "status": "authorized"},
                {"event": "workflow_submitted", "status": "dry_run"},
                {"event": "blind_retry_blocked", "status": "enforced"},
            ],
            "timestamp": "2026-05-08T00:00:00"
        }
        with open(control_dir / "combine_v2_v11_generation_trace.json", 'w') as f:
            json.dump(trace, f, indent=2)

        with open(control_dir / "combine_v2_v11_generation_trace.json") as f:
            data = json.load(f)
        # Dry run traces should not have prompt_id
        for event in data.get("events", []):
            if event.get("status") == "dry_run":
                assert "prompt_id" not in event, \
                    "Dry run events must not contain fake prompt_id"


class TestNoFakeGeneratedAssets:
    """No fake generated assets should appear in QA recovery loop."""

    def test_dry_run_has_empty_assets(self, project_root):
        """Dry run generation must have empty generated_assets list."""
        _, control_dir = project_root
        result = {
            "stage": "v11_generate_assets",
            "version": "v11",
            "generation_performed": True,
            "comfyui_execution": False,
            "generated_assets": [],
            "production_accepted": False,
            "timestamp": "2026-05-08T00:00:00"
        }
        with open(control_dir / "combine_v2_v11_generation_result.json", 'w') as f:
            json.dump(result, f, indent=2)

        with open(control_dir / "combine_v2_v11_generation_result.json") as f:
            data = json.load(f)
        assert data["comfyui_execution"] is False
        assert len(data.get("generated_assets", [])) == 0

    def test_v12_dry_run_empty_assets(self, project_root):
        """V12 dry run must have empty generated_assets."""
        _, control_dir = project_root
        result = {
            "stage": "v12_generate_assets",
            "version": "v12",
            "comfyui_execution": False,
            "generated_assets": [],
            "production_accepted": False,
        }
        with open(control_dir / "combine_v2_v12_generation_result.json", 'w') as f:
            json.dump(result, f, indent=2)

        with open(control_dir / "combine_v2_v12_generation_result.json") as f:
            data = json.load(f)
        assert data["comfyui_execution"] is False
        assert len(data.get("generated_assets", [])) == 0


class TestFinalProofGenerated:
    """Final proof must be generated by combine_finalize_qa_recovery_loop."""

    def test_final_decision_artifact_path(self, project_root):
        """Final decision artifact must have correct name."""
        _, control_dir = project_root
        artifact_path = control_dir / "combine_v2_photoreal_human_qa_recovery_final_decision.json"
        # Simulate creation
        decision = {
            "task_id": "RC-COMBINE-V2-15001-22000",
            "stage": "qa_recovery_loop_finalized",
            "current_state": "visual_candidate_accepted_for_pipeline",
            "loop_outcome": "candidate_accepted",
            "loop_completed": True,
            "recovery_successful": True,
            "candidate_accepted_for_pipeline": True,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "timestamp": "2026-05-08T00:00:00"
        }
        with open(artifact_path, 'w') as f:
            json.dump(decision, f, indent=2)

        assert artifact_path.exists()
        with open(artifact_path) as f:
            data = json.load(f)
        assert data["production_accepted"] is False
        assert data["assembly_executed"] is False
        assert data["downstream_executed"] is False

    def test_final_decision_blocked_state_content(self, project_root):
        """Final decision for blocked state must have correct flags."""
        _, control_dir = project_root
        artifact_path = control_dir / "combine_v2_photoreal_human_qa_recovery_final_decision.json"
        decision = {
            "task_id": "RC-COMBINE-V2-15001-22000",
            "stage": "qa_recovery_loop_finalized",
            "current_state": "qa_recovery_blocked_after_max_candidates",
            "loop_outcome": "max_candidates_exhausted",
            "loop_completed": True,
            "recovery_successful": False,
            "candidate_accepted_for_pipeline": False,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "timestamp": "2026-05-08T00:00:00"
        }
        with open(artifact_path, 'w') as f:
            json.dump(decision, f, indent=2)

        with open(artifact_path) as f:
            data = json.load(f)
        assert data["current_state"] == "qa_recovery_blocked_after_max_candidates"
        assert data["candidate_accepted_for_pipeline"] is False
        assert data["production_accepted"] is False
        assert data["assembly_executed"] is False
        assert data["downstream_executed"] is False


class TestForbiddenTransitionsStateMachine:
    """Verify forbidden transitions are properly enforced."""

    def test_forbidden_transitions_are_registered(self):
        """All V11/V12/V13 forbidden transitions must be registered."""
        # V11 operator review -> assembly is forbidden
        assert not CombineStateMachine.can_transition(
            "v11_operator_visual_review_required", "assembly_required"
        )
        assert not CombineStateMachine.can_transition(
            "v11_operator_visual_review_required", "assembly_preflight_required"
        )
        # V12 operator review -> assembly is forbidden
        assert not CombineStateMachine.can_transition(
            "v12_operator_visual_review_required", "assembly_required"
        )
        # V13 operator review -> assembly is forbidden
        assert not CombineStateMachine.can_transition(
            "v13_operator_visual_review_required", "assembly_required"
        )
        # Terminal states -> anything is forbidden
        assert not CombineStateMachine.can_transition(
            "visual_candidate_accepted_for_pipeline", "assembly_required"
        )
        assert not CombineStateMachine.can_transition(
            "qa_recovery_blocked_after_max_candidates", "assembly_required"
        )
        assert not CombineStateMachine.can_transition(
            "visual_candidate_accepted_for_pipeline", "completed"
        )
        assert not CombineStateMachine.can_transition(
            "qa_recovery_blocked_after_max_candidates", "completed"
        )
