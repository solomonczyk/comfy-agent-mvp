"""Tests for Planning State Transition — state machine, forbidden actions, production_accepted."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine
from app.planning.director import build_director_planning


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _create_minimal_brief(project_root: Path) -> None:
    brief_dir = project_root / "output" / "control" / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)
    _write_json(brief_dir / "brief_contract.json", {
        "project_id": "test_project",
        "normalized_task_summary": "Test educational video about AI pipeline QA",
        "content_type": "educational",
        "target_audience": "beginners",
        "goal": "Explain AI pipeline frame checking",
        "expected_output": "educational video",
        "readiness_for_director_planner": True,
        "production_accepted": False,
        "forbidden_actions": ["generation_without_authorization"],
        "assumptions": ["test assumption"],
        "missing_fields": [],
    })
    _write_json(brief_dir / "content_intent.json", {
        "content_type": "educational",
        "goal": "Explain AI pipeline frame checking",
        "target_audience": "beginners",
        "expected_output": "educational video",
        "primary_purpose": "educational",
    })
    _write_json(brief_dir / "project_constraints.json", {
        "style_tone": "clear_practical",
        "constraints": [],
        "format_hint": None,
        "aspect_ratio": None,
    })
    _write_json(brief_dir / "success_criteria.json", {"criteria": ["test"]})
    _write_json(brief_dir / "forbidden_actions.json", {"forbidden_actions": ["generation_without_authorization"]})
    _write_json(brief_dir / "brief_validation_report.json", {
        "brief_contract_created": True,
        "brief_validation_passed": True,
        "classification": "valid_for_director_planning",
        "brief_is_ready_for_director_planner": True,
        "production_accepted": False,
        "generation_performed": False,
        "downstream_executed": False,
    })


def _init_project_state(project_root: Path) -> None:
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    _write_json(control_dir / "artifact_index.json", {
        "artifacts": [],
        "current_state": "brief_operator_review_required",
        "next_allowed_action": "brief_operator_review_required",
    })
    _write_json(control_dir / "episode_ledger.json", {"events": []})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPlanningStateMachine:
    """Test state machine support for planning_operator_review_required."""

    def test_planning_state_is_valid(self):
        assert CombineStateMachine.is_valid_state("planning_operator_review_required") is True

    def test_planning_state_is_not_terminal(self):
        assert CombineStateMachine.is_terminal_state("planning_operator_review_required") is False

    def test_transition_from_brief_to_planning_allowed(self):
        assert CombineStateMachine.can_transition(
            "brief_operator_review_required",
            "planning_operator_review_required",
        ) is True

    def test_planning_self_loop_allowed(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "planning_operator_review_required",
        ) is True

    def test_planning_can_go_back_to_brief(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "brief_intake_required",
        ) is True

    def test_planning_cannot_skip_to_generation(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "generate_assets",
        ) is False

    def test_planning_cannot_skip_to_real_generation(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "real_generate_assets",
        ) is False

    def test_planning_cannot_skip_to_assembly(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "assembly_required",
        ) is False

    def test_planning_cannot_skip_to_visual_qa(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "visual_qa_required",
        ) is False

    def test_planning_cannot_skip_to_completed(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "completed",
        ) is False

    def test_planning_cannot_skip_to_production_accepted(self):
        # production_accepted is not a valid state
        assert CombineStateMachine.is_valid_state("production_accepted") is False

    def test_planning_cannot_skip_to_final_qc(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "final_qc_required",
        ) is False


class TestStateTransitionAfterBuild:
    """Test that state transitions to planning_operator_review_required after build."""

    def test_state_after_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = build_director_planning(str(project_root))
            assert result.get("current_state") == "planning_operator_review_required"
            assert result.get("next_allowed_action") == "planning_operator_review_required"

            # Verify artifact_index state
            index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(index_path) as f:
                index = json.load(f)
            assert index.get("current_state") == "planning_operator_review_required"
            assert index.get("next_allowed_action") == "planning_operator_review_required"

            # Verify episode_ledger state
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path) as f:
                ledger = json.load(f)
            if isinstance(ledger, dict):
                assert ledger.get("current_state") == "planning_operator_review_required"
                assert ledger.get("next_allowed_action") == "planning_operator_review_required"
                assert ledger.get("production_accepted") is False

    def test_production_accepted_remains_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = build_director_planning(str(project_root))
            assert result.get("production_accepted") is False

    def test_forbidden_actions_remain_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = build_director_planning(str(project_root))
            assert result.get("generation_performed") is False
            assert result.get("comfyui_submit_executed") is False
            assert result.get("assembly_executed") is False
            assert result.get("downstream_executed") is False

    def test_canonical_artifacts_updated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))

            # Verify artifact_index updated
            index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(index_path) as f:
                index = json.load(f)
            assert index.get("planning_layer_completed") is True
            assert any("planning/scenario_plan.json" in a for a in index.get("artifacts", []))

            # Verify ledger updated
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path) as f:
                ledger = json.load(f)
            events = ledger if isinstance(ledger, list) else ledger.get("events", [])
            planning_events = [e for e in events if e.get("event") == "director_planning_layer_completed"]
            assert len(planning_events) >= 1


import tempfile
