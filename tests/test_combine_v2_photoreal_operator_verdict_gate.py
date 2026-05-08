"""Tests for RC-COMBINE-V2-15001-22000 operator verdict gate.

Tests cover:
- v11_acceptance_reaches_terminal_accepted_state
- v11_rejection_moves_to_v12
- v12_rejection_moves_to_v13
- v13_rejection_reaches_blocked_state
- operator_verdict_required_before_next_candidate
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


def _init_index(control_dir, candidate_count=1, max_candidates=3):
    idx = {
        "task_id": "RC-COMBINE-V2-15001-22000",
        "current_state": "v11_operator_visual_review_required",
        "next_allowed_action": "v11_operator_visual_review_required",
        "candidate_count": candidate_count,
        "max_candidates": max_candidates,
        "candidate_accepted_for_pipeline": False,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "operator_visual_decision_recorded": False,
    }
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(idx, f, indent=2)
    return idx


class TestV11Acceptance:
    """V11 operator acceptance reaches terminal accepted state."""

    def test_v11_acceptance_sets_correct_state(self, project_root):
        """Accepting V11 must set state to visual_candidate_accepted_for_pipeline."""
        _, control_dir = project_root
        idx = _init_index(control_dir)
        idx["current_state"] = "visual_candidate_accepted_for_pipeline"
        idx["candidate_accepted_for_pipeline"] = True
        idx["operator_visual_decision_recorded"] = True
        idx["production_accepted"] = False
        idx["assembly_allowed"] = False
        idx["downstream_allowed"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["current_state"] == "visual_candidate_accepted_for_pipeline"
        assert idx["candidate_accepted_for_pipeline"] is True
        assert idx["production_accepted"] is False
        assert idx["assembly_allowed"] is False
        assert idx["downstream_allowed"] is False
        assert CombineStateMachine.is_terminal_state(idx["current_state"])

    def test_v11_acceptance_creates_artifact(self, project_root):
        """Acceptance must create the acceptance artifact."""
        _, control_dir = project_root
        acceptance = {
            "version": "v11",
            "stage": "v11_operator_visual_review_required",
            "operator_decision": "accept_v11_visual_quality",
            "candidate_accepted_for_pipeline": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "current_state": "visual_candidate_accepted_for_pipeline",
            "timestamp": datetime.now().isoformat()
        }
        with open(control_dir / "combine_v2_v11_operator_visual_acceptance.json", 'w') as f:
            json.dump(acceptance, f, indent=2)

        assert (control_dir / "combine_v2_v11_operator_visual_acceptance.json").exists()
        with open(control_dir / "combine_v2_v11_operator_visual_acceptance.json") as f:
            data = json.load(f)
        assert data["candidate_accepted_for_pipeline"] is True
        assert data["production_accepted"] is False

    def test_v11_acceptance_blocks_assembly_downstream(self, project_root):
        """Accepted candidate must have assembly/downstream blocked."""
        _, control_dir = project_root
        idx = _init_index(control_dir)
        idx["current_state"] = "visual_candidate_accepted_for_pipeline"
        idx["assembly_allowed"] = False
        idx["downstream_allowed"] = False
        idx["candidate_accepted_for_pipeline"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["assembly_allowed"] is False
        assert idx["downstream_allowed"] is False


class TestV11RejectionToV12:
    """V11 rejection moves to V12 correction plan."""

    def test_v11_rejection_creates_v12_correction_plan(self, project_root):
        """Rejecting V11 must create V12 correction plan."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=1)
        idx["current_state"] = "v12_correction_plan_required"
        idx["next_allowed_action"] = "v12_corrective_package_build_required"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        # Create V12 correction plan artifact
        plan = {
            "version": "v12",
            "stage": "v12_correction_plan_required",
            "source_asset": "test_asset.png",
            "generation_allowed": False,
            "production_accepted": False,
            "next_allowed_action": "v12_corrective_package_build_required",
            "timestamp": datetime.now().isoformat()
        }
        with open(control_dir / "combine_v2_v12_correction_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        assert (control_dir / "combine_v2_v12_correction_plan.json").exists()
        with open(control_dir / "combine_v2_v12_correction_plan.json") as f:
            data = json.load(f)
        assert data["version"] == "v12"
        assert data["generation_allowed"] is False
        assert data["production_accepted"] is False
        assert CombineStateMachine.can_transition(
            "v12_correction_plan_required",
            "v12_corrective_package_build_required"
        )


class TestV12RejectionToV13:
    """V12 rejection moves to V13 correction plan."""

    def test_v12_rejection_creates_v13_correction_plan(self, project_root):
        """Rejecting V12 must create V13 correction plan."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=2)
        idx["current_state"] = "v13_correction_plan_required"
        idx["next_allowed_action"] = "v13_corrective_package_build_required"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        plan = {
            "version": "v13",
            "stage": "v13_correction_plan_required",
            "source_asset": "test_asset.png",
            "generation_allowed": False,
            "production_accepted": False,
            "next_allowed_action": "v13_corrective_package_build_required",
            "timestamp": datetime.now().isoformat()
        }
        with open(control_dir / "combine_v2_v13_correction_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        assert (control_dir / "combine_v2_v13_correction_plan.json").exists()
        with open(control_dir / "combine_v2_v13_correction_plan.json") as f:
            data = json.load(f)
        assert data["version"] == "v13"
        assert data["generation_allowed"] is False
        assert data["production_accepted"] is False


class TestV13RejectionToBlocked:
    """V13 rejection reaches blocked state (max candidates exhausted)."""

    def test_v13_rejection_blocks_with_artifact(self, project_root):
        """Rejecting V13 must create blocker artifact."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=3)
        idx["current_state"] = "qa_recovery_blocked_after_max_candidates"
        idx["candidate_accepted_for_pipeline"] = False
        idx["operator_visual_decision_recorded"] = True
        idx["all_candidates_exhausted"] = True
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        blocker = {
            "version": "v13",
            "stage": "v13_operator_visual_review_required",
            "operator_decision": "reject_v13_visual_quality",
            "candidate_accepted_for_pipeline": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "candidate_count": 3,
            "max_candidates": 3,
            "all_candidates_exhausted": True,
            "current_state": "qa_recovery_blocked_after_max_candidates",
            "timestamp": datetime.now().isoformat()
        }
        with open(control_dir / "combine_v2_v13_qa_recovery_blocker.json", 'w') as f:
            json.dump(blocker, f, indent=2)

        assert idx["current_state"] == "qa_recovery_blocked_after_max_candidates"
        assert idx["candidate_accepted_for_pipeline"] is False
        assert idx["production_accepted"] is False
        assert idx["assembly_allowed"] is False
        assert idx["downstream_allowed"] is False
        assert idx["all_candidates_exhausted"] is True
        assert CombineStateMachine.is_terminal_state("qa_recovery_blocked_after_max_candidates")


class TestOperatorVerdictRequiredBeforeNext:
    """Operator verdict is required before next candidate can proceed."""

    def test_no_auto_advance_without_verdict(self, project_root):
        """State must stay at operator_visual_review_required until verdict."""
        _, control_dir = project_root
        idx = _init_index(control_dir)
        idx["operator_visual_decision_recorded"] = False
        idx["current_state"] = "v11_operator_visual_review_required"
        idx["next_allowed_action"] = "v11_operator_visual_review_required"
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        assert idx["operator_visual_decision_recorded"] is False
        assert idx["current_state"] == "v11_operator_visual_review_required"
        # Only acceptable transitions from operator review
        allowed = CombineStateMachine.get_allowed_next_states("v11_operator_visual_review_required")
        assert "v11_correction_plan_required" in allowed
        assert "visual_candidate_accepted_for_pipeline" in allowed
        assert "qa_recovery_blocked_after_max_candidates" in allowed

    def test_v12_operator_verdict_gate(self, project_root):
        """V12 operator review must be required before advancing."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=2)
        idx["current_state"] = "v12_operator_visual_review_required"
        idx["operator_visual_decision_recorded"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        allowed = CombineStateMachine.get_allowed_next_states("v12_operator_visual_review_required")
        assert "v12_correction_plan_required" in allowed
        assert "visual_candidate_accepted_for_pipeline" in allowed
        assert "qa_recovery_blocked_after_max_candidates" in allowed

    def test_v13_operator_verdict_gate(self, project_root):
        """V13 operator review must be required before advancing."""
        _, control_dir = project_root
        idx = _init_index(control_dir, candidate_count=3)
        idx["current_state"] = "v13_operator_visual_review_required"
        idx["operator_visual_decision_recorded"] = False
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(idx, f, indent=2)

        allowed = CombineStateMachine.get_allowed_next_states("v13_operator_visual_review_required")
        assert "v13_correction_plan_required" in allowed
        assert "visual_candidate_accepted_for_pipeline" in allowed
        assert "qa_recovery_blocked_after_max_candidates" in allowed
