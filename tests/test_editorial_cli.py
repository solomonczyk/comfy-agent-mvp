"""Tests for editorial CLI commands."""
import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        control_dir = project_root / "output" / "control"
        editorial_dir = control_dir / "editorial"
        control_dir.mkdir(parents=True, exist_ok=True)
        editorial_dir.mkdir(parents=True, exist_ok=True)

        # Create initial artifact_index
        artifact_index = {
            "current_state": "v14_operator_visual_review_required",
            "next_allowed_action": "v14_operator_visual_review_required",
        }
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)

        # Create initial episode_ledger
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        yield project_root, control_dir, editorial_dir


class TestEditorialCliBuildPlan:
    def test_build_plan_creates_artifacts(self, temp_project):
        """Test that combine-build-editorial-plan creates all artifacts."""
        from app.cli import combine_build_editorial_plan
        import argparse

        project_root, control_dir, editorial_dir = temp_project

        args = argparse.Namespace(
            project_root=str(project_root),
            json=True,
        )
        result = combine_build_editorial_plan(args)
        assert result == 0

        # Verify all artifacts exist
        expected = [
            "timeline_model.json",
            "marker_registry.json",
            "edit_decision_list.json",
            "subtitle_plan.json",
            "transition_policy.json",
            "voice_casting_contract.json",
            "preview_proof_contract.json",
        ]
        for name in expected:
            assert (editorial_dir / name).exists(), f"Missing {name}"

        # Verify timeline model content
        with open(editorial_dir / "timeline_model.json") as f:
            tm = json.load(f)
            assert tm["project_id"] == "rc2_multishot1_ep01"
            assert tm["operator_review_required"] is True
            assert tm["final_render_allowed"] is False
            assert len(tm["scenes"]) > 0
            assert tm["scenes"][0]["scene_id"] == "scene_001"

        # Verify artifact index updated
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)
            assert idx["editorial_layer_implemented"] is True
            assert "timeline_model" in idx
            assert "marker_registry" in idx

        # Verify ledger updated
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)
            events = [e["event_type"] for e in ledger if "editorial" in e["event_type"] or "timeline" in e["event_type"]]
            assert "editorial_layer_started" in events
            assert "timeline_model_created" in events

    def test_build_plan_no_real_render(self, temp_project):
        """Test that build plan does not perform real rendering."""
        from app.cli import combine_build_editorial_plan
        import argparse

        project_root, control_dir, editorial_dir = temp_project
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True,
        )
        result = combine_build_editorial_plan(args)
        assert result == 0

        with open(editorial_dir / "timeline_model.json") as f:
            tm = json.load(f)
            assert tm["final_render_allowed"] is False


class TestEditorialCliDryRun:
    def test_dry_run_passes_with_valid_artifacts(self, temp_project):
        """Test that dry-run passes with valid artifacts."""
        from app.cli import combine_build_editorial_plan, combine_run_editorial_dry_run
        import argparse

        project_root, control_dir, editorial_dir = temp_project

        # First build the plan
        plan_args = argparse.Namespace(project_root=str(project_root), json=True)
        combine_build_editorial_plan(plan_args)

        # Then run dry-run
        dry_args = argparse.Namespace(project_root=str(project_root), json=True)
        result = combine_run_editorial_dry_run(dry_args)
        assert result == 0

        # Verify dry-run report
        with open(editorial_dir / "timeline_dry_run_report.json") as f:
            report = json.load(f)
            assert report["dry_run_status"] == "ready_for_operator_review"
            assert report["errors"] == []
            assert report["real_render_executed"] is False
            assert report["apply_performed"] is False

    def test_dry_run_fails_with_missing_timeline(self, temp_project):
        """Test that dry-run fails when timeline is missing."""
        from app.cli import combine_run_editorial_dry_run
        import argparse

        project_root, control_dir, editorial_dir = temp_project
        args = argparse.Namespace(project_root=str(project_root), json=True)
        result = combine_run_editorial_dry_run(args)
        assert result != 0


class TestEditorialCliOperatorReview:
    def test_operator_review_packet_created(self, temp_project):
        """Test operator review packet creation with null decision."""
        from app.cli import (
            combine_build_editorial_plan,
            combine_run_editorial_dry_run,
            combine_build_editorial_operator_review,
        )
        import argparse

        project_root, control_dir, editorial_dir = temp_project

        # Build plan and run dry-run first
        base_args = argparse.Namespace(project_root=str(project_root), json=True)
        combine_build_editorial_plan(base_args)
        combine_run_editorial_dry_run(base_args)

        # Build operator review
        result = combine_build_editorial_operator_review(base_args)
        assert result == 0

        # Verify review packet
        with open(editorial_dir / "editorial_operator_review_packet.json") as f:
            packet = json.load(f)
            assert packet["operator_decision"] is None
            assert packet["operator_review_required"] is True
            assert packet["preview_render_allowed"] is False
            assert packet["final_render_allowed"] is False
            assert packet["production_accepted"] is False
            assert packet["scenes_count"] > 0
            assert packet["operations_count"] > 0
            assert "timeline_summary" in packet
            assert "dry_run_result" in packet

    def test_allowed_operator_decisions(self, temp_project):
        """Test that the review packet has the correct allowed decisions."""
        from app.editorial.operator_review_gate import OperatorReviewPacket

        packet = OperatorReviewPacket()
        assert "approved_for_preview_render" in packet.allowed_operator_decisions
        assert "needs_changes" in packet.allowed_operator_decisions
        assert "rejected" in packet.allowed_operator_decisions
