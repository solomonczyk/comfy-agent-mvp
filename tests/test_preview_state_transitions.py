"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — State transition tests.

Tests that the state machine correctly transitions between states for
the three branches: preview_render_executed, authorization_required,
and runtime_blocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from app.timeline.controlled_preview_render import (
    run_controlled_preview_render,
)
from app.orchestrator.state_machine import CombineStateMachine


def _make_control_dir(tmp_path: Path) -> Path:
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return control_dir


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestStateMachineStates:
    """Verify new states are registered in the state machine."""

    def test_new_states_are_valid(self):
        """preview_operator_review_required must be a valid state."""
        assert CombineStateMachine.is_valid_state("preview_operator_review_required")
        assert CombineStateMachine.is_valid_state("preview_render_blocked")
        assert CombineStateMachine.is_valid_state("preview_render_blocker_review_required")

    def test_preview_operator_review_required_transitions(self):
        """Verify allowed transitions from preview_operator_review_required."""
        allowed = CombineStateMachine.ALLOWED_TRANSITIONS.get(
            "preview_operator_review_required", set()
        )
        assert "blocked_manual_review" in allowed

    def test_preview_render_blocked_transitions(self):
        """Verify allowed transitions from preview_render_blocked."""
        allowed = CombineStateMachine.ALLOWED_TRANSITIONS.get(
            "preview_render_blocked", set()
        )
        assert "preview_render_blocker_review_required" in allowed
        assert "blocked_manual_review" in allowed

    def test_preview_render_blocker_review_required_transitions(self):
        """Verify allowed transitions from preview_render_blocker_review_required."""
        allowed = CombineStateMachine.ALLOWED_TRANSITIONS.get(
            "preview_render_blocker_review_required", set()
        )
        assert "blocked_manual_review" in allowed

    def test_authorization_required_transitions_to_new_states(self):
        """preview_render_authorization_required can go to new states."""
        allowed = CombineStateMachine.ALLOWED_TRANSITIONS.get(
            "preview_render_authorization_required", set()
        )
        assert "preview_operator_review_required" in allowed
        assert "preview_render_blocked" in allowed

    def test_terminal_states_unaffected(self):
        """Existing terminal states should not include new states."""
        assert "preview_operator_review_required" not in CombineStateMachine.TERMINAL_STATES
        assert "preview_render_blocked" not in CombineStateMachine.TERMINAL_STATES


class TestStateTransitionBranches:
    """Test the three state transition branches."""

    def test_preview_render_executed_branch(self, tmp_path: Path):
        """Successful preview render transitions to preview_operator_review_required."""
        control_dir = _make_control_dir(tmp_path)

        auth = {
            "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
            "operator_authorized": True,
            "preview_render_authorized": True,
            "max_preview_renders": 1,
            "source_timeline": "timeline_model.json",
            "preview_proof_contract": "preview_proof_contract.json",
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_acceptance_allowed": False,
            "final_render_allowed": False,
            "stop_after_preview_result_review": True,
        }
        _write_json(control_dir / "preview_render_authorization.json", auth)

        artifacts = {
            "marker_registry.json": [],
            "edit_decision_list.json": [],
            "subtitle_plan.json": [],
            "transition_policy.json": {"default": "hard_cut"},
            "voice_casting_contract.json": {"full_voiceover_generation_allowed": False},
            "preview_proof_contract.json": {"preview_lowres_required": True},
            "timeline_preview_dry_run_report.json": {"dry_run_status": "ready", "errors": [], "warnings": []},
            "preview_render_authorization_packet.json": {"authorization_required": True},
        }
        for name, data in artifacts.items():
            _write_json(control_dir / name, data)

        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (200, 150), color=(100, 100, 200))
        asset_path = assets_dir / "test_asset.png"
        img.save(asset_path)

        _write_json(
            control_dir / "timeline_model.json",
            {
                "scenes": [],
                "operations": [{"operation_id": "place_test", "asset_ref": str(asset_path), "track": "video_main"}],
            },
        )

        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["selected_branch"] == "preview_render_executed"
        assert result["current_state"] == "preview_operator_review_required"
        assert result["next_allowed_action"] == "preview_operator_review_required"
        assert result["preview_render_executed"] is True
        assert result["preview_render_count"] == 1

    def test_authorization_required_branch(self, tmp_path: Path):
        """Missing authorization stays at preview_render_authorization_required."""
        control_dir = _make_control_dir(tmp_path)

        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["selected_branch"] == "authorization_required"
        assert result["current_state"] == "preview_render_authorization_required"
        assert result["next_allowed_action"] == "preview_render_authorization_required"
        assert result["preview_render_executed"] is False

    def test_runtime_blocked_branch(self, tmp_path: Path):
        """Render with no asset transitions to preview_render_blocked."""
        control_dir = _make_control_dir(tmp_path)

        auth = {
            "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
            "operator_authorized": True,
            "preview_render_authorized": True,
            "max_preview_renders": 1,
            "source_timeline": "timeline_model.json",
            "preview_proof_contract": "preview_proof_contract.json",
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_acceptance_allowed": False,
            "final_render_allowed": False,
            "stop_after_preview_result_review": True,
        }
        _write_json(control_dir / "preview_render_authorization.json", auth)

        artifacts = {
            "marker_registry.json": [],
            "edit_decision_list.json": [],
            "subtitle_plan.json": [],
            "transition_policy.json": {"default": "hard_cut"},
            "voice_casting_contract.json": {"full_voiceover_generation_allowed": False},
            "preview_proof_contract.json": {"preview_lowres_required": True},
            "timeline_preview_dry_run_report.json": {"dry_run_status": "ready", "errors": [], "warnings": []},
            "preview_render_authorization_packet.json": {"authorization_required": True},
            "timeline_model.json": {"scenes": [], "operations": []},
        }
        for name, data in artifacts.items():
            _write_json(control_dir / name, data)

        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["selected_branch"] == "runtime_blocked"
        assert result["current_state"] == "preview_render_blocked"
        assert result["next_allowed_action"] == "preview_render_blocker_review_required"

    def test_artifact_index_updated_on_success(self, tmp_path: Path):
        """Artifact index is updated on successful preview render."""
        control_dir = _make_control_dir(tmp_path)

        auth = {
            "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
            "operator_authorized": True,
            "preview_render_authorized": True,
            "max_preview_renders": 1,
            "source_timeline": "timeline_model.json",
            "preview_proof_contract": "preview_proof_contract.json",
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_acceptance_allowed": False,
            "final_render_allowed": False,
            "stop_after_preview_result_review": True,
        }
        _write_json(control_dir / "preview_render_authorization.json", auth)

        artifacts = {
            "marker_registry.json": [],
            "edit_decision_list.json": [],
            "subtitle_plan.json": [],
            "transition_policy.json": {"default": "hard_cut"},
            "voice_casting_contract.json": {"full_voiceover_generation_allowed": False},
            "preview_proof_contract.json": {"preview_lowres_required": True},
            "timeline_preview_dry_run_report.json": {"dry_run_status": "ready", "errors": [], "warnings": []},
            "preview_render_authorization_packet.json": {"authorization_required": True},
        }
        for name, data in artifacts.items():
            _write_json(control_dir / name, data)

        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (200, 150), color=(100, 100, 200))
        asset_path = assets_dir / "test_asset.png"
        img.save(asset_path)

        _write_json(
            control_dir / "timeline_model.json",
            {
                "scenes": [],
                "operations": [{"operation_id": "place_test", "asset_ref": str(asset_path), "track": "video_main"}],
            },
        )

        run_controlled_preview_render(project_root=str(tmp_path))

        index_path = control_dir / "artifact_index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert index.get("current_state") == "preview_operator_review_required"
        assert index.get("preview_render_executed") is True

    def test_episode_ledger_updated_on_success(self, tmp_path: Path):
        """Episode ledger is updated on successful preview render."""
        control_dir = _make_control_dir(tmp_path)

        auth = {
            "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
            "operator_authorized": True,
            "preview_render_authorized": True,
            "max_preview_renders": 1,
            "source_timeline": "timeline_model.json",
            "preview_proof_contract": "preview_proof_contract.json",
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_acceptance_allowed": False,
            "final_render_allowed": False,
            "stop_after_preview_result_review": True,
        }
        _write_json(control_dir / "preview_render_authorization.json", auth)

        artifacts = {
            "marker_registry.json": [],
            "edit_decision_list.json": [],
            "subtitle_plan.json": [],
            "transition_policy.json": {"default": "hard_cut"},
            "voice_casting_contract.json": {"full_voiceover_generation_allowed": False},
            "preview_proof_contract.json": {"preview_lowres_required": True},
            "timeline_preview_dry_run_report.json": {"dry_run_status": "ready", "errors": [], "warnings": []},
            "preview_render_authorization_packet.json": {"authorization_required": True},
        }
        for name, data in artifacts.items():
            _write_json(control_dir / name, data)

        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (200, 150), color=(100, 100, 200))
        asset_path = assets_dir / "test_asset.png"
        img.save(asset_path)

        _write_json(
            control_dir / "timeline_model.json",
            {
                "scenes": [],
                "operations": [{"operation_id": "place_test", "asset_ref": str(asset_path), "track": "video_main"}],
            },
        )

        run_controlled_preview_render(project_root=str(tmp_path))

        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        events = [e for e in ledger if e.get("task_id") == "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001"]
        assert len(events) > 0
        # Check for the preview render completed event
        render_completed = [
            e for e in events if e.get("event_type") == "preview_render_completed"
        ]
        assert len(render_completed) > 0
        assert render_completed[0]["current_state"] == "preview_operator_review_required"
