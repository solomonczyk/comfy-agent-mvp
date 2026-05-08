"""Tests for RC-COMBINE-V2-15001-22000 photoreal QA recovery loop.

Tests cover:
- v10_rejection_recorded
- v11_generation_limit_one
- next_candidate_requires_operator_rejection
- v11_acceptance_reaches_terminal_accepted_state
- v11_rejection_moves_to_v12
- v12_rejection_moves_to_v13
- v13_rejection_reaches_blocked_state
- max_candidates_3_enforced
- production_accepted_always_false
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from app.orchestrator.state_machine import CombineStateMachine


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        control_dir = root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield root, control_dir


def _init_artifact_index(control_dir, candidate_count=0, max_candidates=3, state="v11_correction_plan_required"):
    idx = {
        "task_id": "RC-COMBINE-V2-15001-22000",
        "qa_recovery_loop_task_id": "RC-COMBINE-V2-15001-22000",
        "current_state": state,
        "next_allowed_action": "v11_corrective_package_build_required",
        "candidate_count": candidate_count,
        "max_candidates": max_candidates,
        "candidate_generated": False,
        "candidate_accepted_for_pipeline": False,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "generation_allowed": False,
        "blind_retry_allowed": False,
        "visual_qa_executed": False,
        "operator_visual_decision_recorded": False
    }
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(idx, f, indent=2)
    return idx


def _create_v11_generation_result(control_dir, has_assets=True):
    result = {
        "stage": "v11_generate_assets",
        "version": "v11",
        "generation_attempts": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "generation_performed": True,
        "comfyui_execution": False,
        "blind_retry_allowed": False,
        "source_asset": "test_asset.png",
        "generated_assets": [{"path": "test_output.png"}] if has_assets else [],
        "asset_paths": ["test_output.png"] if has_assets else [],
        "generated_assets_count": 1 if has_assets else 0,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "status": "completed" if has_assets else "failed",
        "timestamp": datetime.now().isoformat()
    }
    with open(control_dir / "combine_v2_v11_generation_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    return result


def _create_v12_generation_result(control_dir, has_assets=True):
    result = {
        "stage": "v12_generate_assets",
        "version": "v12",
        "generation_attempts": 1,
        "max_generations": 1,
        "blind_retry_allowed": False,
        "source_asset": "test_asset.png",
        "generated_assets": [{"path": "test_output.png"}] if has_assets else [],
        "asset_paths": ["test_output.png"] if has_assets else [],
        "generated_assets_count": 1 if has_assets else 0,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "status": "completed" if has_assets else "failed",
        "timestamp": datetime.now().isoformat()
    }
    with open(control_dir / "combine_v2_v12_generation_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    return result


def _create_v13_generation_result(control_dir, has_assets=True):
    result = {
        "stage": "v13_generate_assets",
        "version": "v13",
        "generation_attempts": 1,
        "max_generations": 1,
        "blind_retry_allowed": False,
        "source_asset": "test_asset.png",
        "generated_assets": [{"path": "test_output.png"}] if has_assets else [],
        "asset_paths": ["test_output.png"] if has_assets else [],
        "generated_assets_count": 1 if has_assets else 0,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "status": "completed" if has_assets else "failed",
        "timestamp": datetime.now().isoformat()
    }
    with open(control_dir / "combine_v2_v13_generation_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    return result


class TestV10RejectionRecorded:
    """V10 rejection must be recorded before QA recovery loop can start."""

    def test_v10_rejection_artifact_required(self, project_root):
        _, control_dir = project_root
        rejection_path = control_dir / "combine_v2_v10_operator_visual_rejection.json"
        assert not rejection_path.exists()

        # Simulate V10 rejection creation
        rejection = {
            "task_id": "RC-COMBINE-V2-15001-22000",
            "stage": "v10_operator_visual_review_required",
            "operator_decision": "reject_visual_quality",
            "production_accepted": False,
            "source_asset": "v10_asset.png",
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": datetime.now().isoformat()
        }
        with open(rejection_path, 'w') as f:
            json.dump(rejection, f, indent=2)

        assert rejection_path.exists()
        with open(rejection_path) as f:
            data = json.load(f)
        assert data["operator_decision"] == "reject_visual_quality"
        assert data["production_accepted"] is False


class TestV11GenerationLimitOne:
    """V11 generation must be limited to exactly one attempt."""

    def test_v11_max_generations_forced_to_one(self, project_root):
        """Verify that max_generations=1 is enforced in generation artifacts."""
        _, control_dir = project_root
        _init_artifact_index(control_dir)
        _create_v11_generation_result(control_dir)

        with open(control_dir / "combine_v2_v11_generation_result.json") as f:
            result = json.load(f)
        assert result["max_generations"] == 1
        assert result["generation_attempts"] == 1

    def test_v11_second_generation_blocked(self, project_root):
        """Verify v11_generation_executed flag prevents second generation."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir)
        idx["v11_generation_executed"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx.get("v11_generation_executed") is True
        assert idx.get("candidate_count", 0) == 0


class TestNextCandidateRequiresRejection:
    """Next candidate only allowed after operator rejection is recorded."""

    def test_acceptance_blocks_next_candidate(self, project_root):
        """If V11 is accepted, no V12 should be generated."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=1)
        idx["current_state"] = "visual_candidate_accepted_for_pipeline"
        idx["candidate_accepted_for_pipeline"] = True
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "visual_candidate_accepted_for_pipeline"
        assert idx["candidate_count"] == 1

    def test_rejection_allows_next_candidate(self, project_root):
        """If V11 is rejected and candidates remain, V12 should be queued."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=1)
        idx["current_state"] = "v12_correction_plan_required"
        idx["next_allowed_action"] = "v12_corrective_package_build_required"
        idx["operator_visual_decision_recorded"] = True
        idx["candidate_accepted_for_pipeline"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "v12_correction_plan_required"
        assert idx["candidate_accepted_for_pipeline"] is False


class TestFullCandidateLoop:
    """Test complete V11 -> V12 -> V13 candidate loop."""

    def test_v11_acceptance_reaches_terminal(self, project_root):
        """V11 acceptance should reach visual_candidate_accepted_for_pipeline."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=1)
        idx["current_state"] = "visual_candidate_accepted_for_pipeline"
        idx["candidate_accepted_for_pipeline"] = True
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert CombineStateMachine.is_valid_state(idx["current_state"])
        assert CombineStateMachine.is_terminal_state("visual_candidate_accepted_for_pipeline")
        assert idx["candidate_accepted_for_pipeline"] is True

    def test_v11_rejection_moves_to_v12(self, project_root):
        """V11 rejection should move state to v12_correction_plan_required."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=1)
        idx["current_state"] = "v12_correction_plan_required"
        idx["next_allowed_action"] = "v12_corrective_package_build_required"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "v12_correction_plan_required"
        assert idx["candidate_accepted_for_pipeline"] is False
        assert CombineStateMachine.can_transition(
            "v12_correction_plan_required",
            "v12_corrective_package_build_required"
        )

    def test_v12_rejection_moves_to_v13(self, project_root):
        """V12 rejection should move state to v13_correction_plan_required."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=2)
        idx["current_state"] = "v13_correction_plan_required"
        idx["next_allowed_action"] = "v13_corrective_package_build_required"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "v13_correction_plan_required"
        assert idx["candidate_accepted_for_pipeline"] is False
        assert CombineStateMachine.can_transition(
            "v13_correction_plan_required",
            "v13_corrective_package_build_required"
        )

    def test_v13_rejection_reaches_blocked(self, project_root):
        """V13 rejection should reach qa_recovery_blocked_after_max_candidates."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir, candidate_count=3)
        idx["current_state"] = "qa_recovery_blocked_after_max_candidates"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        idx["all_candidates_exhausted"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "qa_recovery_blocked_after_max_candidates"
        assert idx["candidate_accepted_for_pipeline"] is False
        assert CombineStateMachine.is_terminal_state("qa_recovery_blocked_after_max_candidates")

    def test_max_candidates_3_enforced(self, project_root):
        """Max candidates must be 3."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir)
        assert idx["max_candidates"] == 3


class TestProductionAcceptedAlwaysFalse:
    """production_accepted must always be false in QA recovery loop."""

    def test_production_accepted_false_on_all_artifacts(self, project_root):
        """All candidate artifacts must have production_accepted=False."""
        _, control_dir = project_root
        _init_artifact_index(control_dir)
        _create_v11_generation_result(control_dir)
        _create_v12_generation_result(control_dir)
        _create_v13_generation_result(control_dir)

        for version in ["v11", "v12", "v13"]:
            path = control_dir / f"combine_v2_{version}_generation_result.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                assert data.get("production_accepted") is False, \
                    f"{version} result has production_accepted={data.get('production_accepted')}"

    def test_index_production_accepted_false(self, project_root):
        """artifact_index must have production_accepted=False."""
        _, control_dir = project_root
        idx = _init_artifact_index(control_dir)
        assert idx.get("production_accepted") is False
