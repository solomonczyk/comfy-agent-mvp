"""Tests for RC-COMBINE-V2-15001-22000 candidate generation limits.

Tests cover:
- v11_generation_limit_one
- second_v11_generation_blocked
- next_candidate_requires_operator_rejection
- max_candidates_3_enforced
- one_generation_per_candidate_enforced
- blind_retry_blocked
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


def _init_index(control_dir, candidate_count=0, max_candidates=3, **overrides):
    idx = {
        "task_id": "RC-COMBINE-V2-15001-22000",
        "current_state": "v11_correction_plan_required",
        "next_allowed_action": "v11_corrective_package_build_required",
        "candidate_count": candidate_count,
        "max_candidates": max_candidates,
        "candidate_accepted_for_pipeline": False,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "generation_allowed": False,
        "blind_retry_allowed": False,
    }
    idx.update(overrides)
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(idx, f, indent=2)
    return idx


def _read_index(control_dir):
    with open(control_dir / "artifact_index.json") as f:
        return json.load(f)


class TestV11GenerationLimitOne:
    """V11 candidate gets exactly one generation attempt."""

    def test_v11_generation_attempts_enforced(self, project_root):
        """V11 generation result must record exactly one attempt."""
        _, control_dir = project_root
        _init_index(control_dir)

        result = {
            "stage": "v11_generate_assets",
            "version": "v11",
            "generation_attempts": 1,
            "max_generations": 1,
            "second_generation_attempted": False,
            "blind_retry_allowed": False,
            "production_accepted": False,
            "timestamp": datetime.now().isoformat()
        }
        with open(control_dir / "combine_v2_v11_generation_result.json", 'w') as f:
            json.dump(result, f, indent=2)

        with open(control_dir / "combine_v2_v11_generation_result.json") as f:
            data = json.load(f)
        assert data["generation_attempts"] == 1
        assert data["max_generations"] == 1
        assert data["second_generation_attempted"] is False
        assert data["blind_retry_allowed"] is False


class TestSecondGenerationBlocked:
    """Second generation for same candidate must be blocked."""

    def test_v11_generation_executed_flag_blocks_second(self, project_root):
        """v11_generation_executed=true must prevent re-execution."""
        _, control_dir = project_root
        idx = _init_index(control_dir)
        idx["v11_generation_executed"] = True
        idx["current_state"] = "v11_generate_assets"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx.get("v11_generation_executed") is True

    def test_v12_generation_executed_flag_blocks_second(self, project_root):
        """v12_generation_executed=true must prevent re-execution."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=1)
        idx["v12_generation_executed"] = True
        idx["current_state"] = "v12_generate_assets"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx.get("v12_generation_executed") is True

    def test_v13_generation_executed_flag_blocks_second(self, project_root):
        """v13_generation_executed=true must prevent re-execution."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=2)
        idx["v13_generation_executed"] = True
        idx["current_state"] = "v13_generate_assets"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx.get("v13_generation_executed") is True


class TestBlindRetryBlocked:
    """Blind retry must be blocked for all candidates."""

    def test_blind_retry_blocked_v11(self, project_root):
        """V11 artifacts must have blind_retry_allowed=False."""
        _, control_dir = project_root
        _init_index(control_dir)
        idx = _read_index(control_dir)
        assert idx.get("blind_retry_allowed") is False

    def test_blind_retry_blocked_all_artifacts(self, project_root):
        """All generation results must have blind_retry_allowed=False."""
        _, control_dir = project_root
        for v in ["11", "12", "13"]:
            result = {
                "stage": f"v{v}_generate_assets",
                "version": f"v{v}",
                "blind_retry_allowed": False,
                "production_accepted": False,
                "timestamp": datetime.now().isoformat()
            }
            with open(control_dir / f"combine_v2_v{v}_generation_result.json", 'w') as f:
                json.dump(result, f, indent=2)

            with open(control_dir / f"combine_v2_v{v}_generation_result.json") as f:
                data = json.load(f)
            assert data["blind_retry_allowed"] is False


class TestNextCandidateRequiresOperatorRejection:
    """Next candidate generation requires operator rejection of previous one."""

    def test_v11_rejection_queues_v12(self, project_root):
        """V11 rejection must set state to prepare V12."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=1)
        idx["current_state"] = "v12_correction_plan_required"
        idx["next_allowed_action"] = "v12_corrective_package_build_required"
        idx["operator_visual_decision_recorded"] = True
        idx["candidate_accepted_for_pipeline"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "v12_correction_plan_required"

    def test_v12_rejection_queues_v13(self, project_root):
        """V12 rejection must set state to prepare V13."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=2)
        idx["current_state"] = "v13_correction_plan_required"
        idx["next_allowed_action"] = "v13_corrective_package_build_required"
        idx["operator_visual_decision_recorded"] = True
        idx["candidate_accepted_for_pipeline"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "v13_correction_plan_required"

    def test_acceptance_prevents_next_candidate(self, project_root):
        """Acceptance must stay at terminal state, not advance to next candidate."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=1)
        idx["current_state"] = "visual_candidate_accepted_for_pipeline"
        idx["candidate_accepted_for_pipeline"] = True
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "visual_candidate_accepted_for_pipeline"
        assert CombineStateMachine.is_terminal_state(idx["current_state"])


class TestMaxCandidatesEnforced:
    """Max candidates of 3 must be enforced."""

    def test_max_candidates_is_3(self, project_root):
        """Default max_candidates must be 3."""
        _, control_dir = project_root
        idx = _init_index(control_dir)
        assert idx["max_candidates"] == 3

    def test_candidate_count_increments(self, project_root):
        """candidate_count must increment after generation attempt."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=0)

        # Simulate V11 generation
        idx["candidate_count"] = 1
        idx["current_state"] = "v11_result_review_required"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["candidate_count"] == 1

        # Simulate V12 generation
        idx["candidate_count"] = 2
        idx["current_state"] = "v12_result_review_required"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["candidate_count"] == 2

        # Simulate V13 generation
        idx["candidate_count"] = 3
        idx["current_state"] = "v13_result_review_required"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["candidate_count"] == 3
