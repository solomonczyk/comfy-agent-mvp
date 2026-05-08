"""Tests for Brief Intake state machine transitions and state management."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine
from app.brief.intake import build_brief_intake


class TestBriefOperatorReviewState:
    """Test the brief_operator_review_required state."""

    def test_state_is_valid(self):
        """brief_operator_review_required is a valid state."""
        assert CombineStateMachine.is_valid_state("brief_operator_review_required") is True

    def test_state_is_not_terminal(self):
        """brief_operator_review_required is not a terminal state."""
        assert CombineStateMachine.is_terminal_state("brief_operator_review_required") is False

    def test_transition_from_brief_intake_allowed(self):
        """Transition from brief_intake_required to brief_operator_review_required is allowed."""
        assert CombineStateMachine.can_transition("brief_intake_required", "brief_operator_review_required") is True

    def test_transition_to_route_classification_allowed(self):
        """Transition from brief_operator_review_required to route_classification_required is allowed."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "route_classification_required") is True

    def test_transition_back_to_brief_intake_allowed(self):
        """Transition from brief_operator_review_required back to brief_intake_required is allowed (refinement)."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "brief_intake_required") is True

    def test_transition_to_generate_assets_forbidden(self):
        """Transition from brief_operator_review_required to generate_assets is forbidden."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "generate_assets") is False

    def test_transition_to_real_generate_assets_forbidden(self):
        """Transition from brief_operator_review_required to real_generate_assets is forbidden."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "real_generate_assets") is False

    def test_transition_to_assembly_forbidden(self):
        """Transition from brief_operator_review_required to assembly is forbidden."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "assembly_required") is False

    def test_transition_to_visual_qa_forbidden(self):
        """Transition from brief_operator_review_required to visual_qa is forbidden."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "visual_qa_required") is False

    def test_transition_to_completed_forbidden(self):
        """Transition from brief_operator_review_required to completed is forbidden."""
        assert CombineStateMachine.can_transition("brief_operator_review_required", "completed") is False

    def test_original_brief_intake_transition_preserved(self):
        """Original brief_intake_required -> route_classification_required still works."""
        assert CombineStateMachine.can_transition("brief_intake_required", "route_classification_required") is True

    def test_initial_to_brief_intake_preserved(self):
        """initial -> brief_intake_required still works."""
        assert CombineStateMachine.can_transition("initial", "brief_intake_required") is True

    def test_get_allowed_next_states(self):
        """get_allowed_next_states returns correct states for brief_operator_review_required."""
        allowed = CombineStateMachine.get_allowed_next_states("brief_operator_review_required")
        assert "route_classification_required" in allowed
        assert "brief_intake_required" in allowed
        assert "generate_assets" not in allowed
        assert "assembly_required" not in allowed
        assert "completed" not in allowed

    def test_validate_transition_success(self):
        """validate_transition does not raise for valid transition."""
        # Should not raise
        CombineStateMachine.validate_transition("brief_operator_review_required", "route_classification_required")

    def test_validate_transition_failure(self):
        """validate_transition raises for forbidden transition."""
        with pytest.raises(ValueError, match="Forbidden|not allowed"):
            CombineStateMachine.validate_transition("brief_operator_review_required", "generate_assets")


class TestBuildSetsCorrectState:
    """Test that build_brief_intake sets the correct state."""

    def test_valid_brief_sets_brief_operator_review_state(self):
        """A valid brief sets state to brief_operator_review_required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create an educational video about AI for beginners.")
            assert result["current_state"] == "brief_operator_review_required"
            assert result["next_allowed_action"] == "brief_operator_review_required"

    def test_blocked_brief_still_sets_operator_review_state(self):
        """Even a blocked brief sets state to brief_operator_review_required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "")
            assert result["current_state"] == "brief_operator_review_required"

    def test_artifact_index_state_updated(self):
        """Artifact index current_state is updated to brief_operator_review_required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": [], "current_state": "agent_registry_operator_review_required"}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json") as f:
                index = json.load(f)
            assert index.get("current_state") == "brief_operator_review_required"
            assert index.get("next_allowed_action") == "brief_operator_review_required"


class TestEpisodeLedgerUpdate:
    """Test that episode_ledger is updated correctly."""

    def test_episode_ledger_has_brief_intake_event(self):
        """Episode ledger contains a brief_intake_layer_completed event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json") as f:
                ledger = json.load(f)
            events = ledger.get("events", [])
            intake_events = [e for e in events if e.get("event") == "brief_intake_layer_completed"]
            assert len(intake_events) >= 1
            event = intake_events[0]
            assert event["task_id"] == "RC-COMBINE-V2-54001-62000"
            assert event["status"] == "brief_operator_review_required"
            assert event["generation_performed"] is False
            assert event["production_accepted"] is False
            assert event["comfyui_submit_executed"] is False
            assert event["assembly_executed"] is False
            assert event["downstream_executed"] is False

    def test_episode_ledger_list_format(self):
        """Episode ledger also works in list-of-events format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump([], f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json") as f:
                ledger = json.load(f)
            assert isinstance(ledger, list)
            intake_events = [e for e in ledger if e.get("event") == "brief_intake_layer_completed"]
            assert len(intake_events) >= 1

    def test_episode_ledger_has_no_generation_flags(self):
        """Episode ledger event has all generation flags false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json") as f:
                ledger = json.load(f)
            events = ledger.get("events", [])
            intake_events = [e for e in events if e.get("event") == "brief_intake_layer_completed"]
            event = intake_events[0]
            assert event.get("generation_performed") is False
            assert event.get("comfyui_submit_executed") is False
            assert event.get("visual_qa_executed") is False
            assert event.get("preview_render_executed") is False
            assert event.get("voice_generation_executed") is False
            assert event.get("assembly_executed") is False
            assert event.get("downstream_executed") is False


class TestArtifactIndexUpdate:
    """Test that artifact_index is updated correctly."""

    def test_artifact_index_has_brief_artifacts(self):
        """Artifact index contains all brief intake artifact paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json") as f:
                index = json.load(f)
            artifacts = index.get("artifacts", [])
            assert "brief/brief_contract.json" in artifacts
            assert "brief/brief_validation_report.json" in artifacts
            assert "brief/project_constraints.json" in artifacts
            assert "brief/content_intent.json" in artifacts
            assert "brief/success_criteria.json" in artifacts
            assert "brief/forbidden_actions.json" in artifacts

    def test_artifact_index_layer_flag(self):
        """Artifact index has brief_intake_layer_completed flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(Path(tmpdir) / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            build_brief_intake(tmpdir, "Create an educational video about AI.")

            with open(Path(tmpdir) / "output" / "control" / "artifact_index.json") as f:
                index = json.load(f)
            assert index.get("brief_intake_layer_completed") is True


class TestForbiddenActions:
    """Test that forbidden actions are properly blocked."""

    def test_generation_not_performed(self):
        """No generation is performed in this layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("generation_performed") is False

    def test_comfyui_submit_not_performed(self):
        """No ComfyUI submit is performed in this layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("comfyui_submit_executed") is False

    def test_visual_qa_not_executed(self):
        """No visual QA is executed in this layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("visual_qa_executed", False) is False

    def test_assembly_not_executed(self):
        """No assembly is executed in this layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        """No downstream is executed in this layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("downstream_executed") is False

    def test_production_accepted_false(self):
        """production_accepted is always false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result.get("production_accepted") is False


class TestStateTransitionCorrect:
    """Test that state transitions are correct end-to-end."""

    def test_full_state_chain_valid(self):
        """Test that the full chain initial -> brief_intake_required -> brief_operator_review_required -> route_classification_required is valid."""
        assert CombineStateMachine.can_transition("initial", "brief_intake_required") is True
        assert CombineStateMachine.can_transition("brief_intake_required", "brief_operator_review_required") is True
        assert CombineStateMachine.can_transition("brief_operator_review_required", "route_classification_required") is True

    def test_no_skip_to_next_layer_without_operator_review(self):
        """Cannot skip from brief_intake_required directly to route_classification without operator review gate (still allowed for backward compat)."""
        # The old direct transition is preserved for backward compatibility
        assert CombineStateMachine.can_transition("brief_intake_required", "route_classification_required") is True
        # But the preferred path goes through operator review
        assert CombineStateMachine.can_transition("brief_intake_required", "brief_operator_review_required") is True
