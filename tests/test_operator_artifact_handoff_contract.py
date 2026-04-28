"""MK-CTRL37R — Artifact handoff contract tests.

Tests that each action receives the correct source artifact from the previous production stage.

Critical bug fixed:
- attach_audio must receive scene_mp4_path, NOT qa_report_path
- render_episode must receive audio_output_path, NOT audio_manifest.json
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.models import ShotArtifacts, ShotStateReport
from app.control.shot_state_storage import ShotState, ShotStateStorage


class TestArtifactHandoffContract:
    """Test that artifact handoff between actions uses correct typed paths."""

    def test_assemble_scene_uses_frame_manifest_path(self):
        """After frames_generated, assemble_scene action plan uses frame_manifest_path."""
        # Create a state report after frames_generated
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="frames_generated",
            next_action="assemble_scene",
            existing_artifacts=ShotArtifacts(),
            # MK-CTRL37R — Typed artifact paths from state
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path=None,
            qa_report_path=None,
            audio_output_path=None,
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "assemble_scene")

        # Verify assemble_scene uses frame_manifest_path
        assert plan.frame_manifest_path == "output/control/frames_manifest.json"
        assert plan.executable
        assert "frame_manifest_path" not in plan.missing_inputs

    def test_qa_review_uses_scene_mp4_path(self):
        """After scene_assembled, qa_review action plan uses scene_mp4_path."""
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="scene_assembled",
            next_action="qa_review",
            existing_artifacts=ShotArtifacts(),
            # MK-CTRL37R — Typed artifact paths from state
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
            qa_report_path=None,
            audio_output_path=None,
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "qa_review")

        # Verify qa_review uses scene_mp4_path
        assert plan.scene_mp4_path == "output/scenes/ep01_shot01_scene.mp4"
        assert plan.executable
        assert "scene_mp4_path" not in plan.missing_inputs

    def test_attach_audio_uses_scene_mp4_path_not_qa_report(self):
        """After qa_passed, attach_audio action plan uses scene_mp4_path, NOT qa_report_path."""
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="qa_passed",
            next_action="attach_audio",
            existing_artifacts=ShotArtifacts(),
            brief_path="data/briefs/ep01_shot01_brief.md",
            # MK-CTRL37R — Typed artifact paths from state
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
            qa_report_path="output/control/ep01_shot01_qa_report.json",  # This should NOT be used
            audio_output_path=None,
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "attach_audio")

        # Verify attach_audio uses scene_mp4_path, NOT qa_report_path
        assert plan.scene_mp4_path == "output/scenes/ep01_shot01_scene.mp4"
        assert plan.scene_mp4_path != "output/control/ep01_shot01_qa_report.json"
        # Note: attach_audio may not be executable due to gate rules - that's okay for this test
        # The critical fix is that scene_mp4_path is correct, not that the action is executable
        assert "scene_mp4_path" not in plan.missing_inputs

    def test_render_episode_uses_audio_output_path_not_manifest(self):
        """After audio_attached, render_episode action plan uses audio_output_path, NOT audio_manifest.json."""
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="audio_attached",
            next_action="render_episode",
            existing_artifacts=ShotArtifacts(),
            # MK-CTRL37R — Typed artifact paths from state
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
            qa_report_path="output/control/ep01_shot01_qa_report.json",
            audio_output_path="output/scenes/ep01_shot01_audio.mp4",  # This should be used
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "render_episode")

        # Verify render_episode uses audio_output_path, NOT audio_manifest
        assert plan.scene_mp4_path == "output/scenes/ep01_shot01_audio.mp4"
        assert plan.scene_mp4_path != "output/control/audio_manifest.json"
        assert plan.executable
        assert "scene_mp4_path" not in plan.missing_inputs

    def test_state_persists_typed_artifact_paths(self):
        """ShotState should persist typed artifact paths across transitions."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage = ShotStateStorage(root)

            # Simulate state after frames_generated
            state1 = ShotState(
                episode_id="ep01",
                shot_id="shot01",
                current_state="frames_generated",
                expected_next_action="assemble_scene",
                last_updated="2024-01-01T00:00:00",
                # MK-CTRL37R — Typed artifact paths
                frame_manifest_path="output/control/frames_manifest.json",
                scene_mp4_path=None,
                qa_report_path=None,
                audio_output_path=None,
                episode_output_path=None,
            )
            storage.save(state1)

            # Load and verify
            loaded = storage.load("ep01", "shot01")
            assert loaded is not None
            assert loaded.frame_manifest_path == "output/control/frames_manifest.json"
            assert loaded.scene_mp4_path is None

            # Simulate state transition to scene_assembled
            state2 = ShotState(
                episode_id="ep01",
                shot_id="shot01",
                current_state="scene_assembled",
                expected_next_action="qa_review",
                last_updated="2024-01-01T00:01:00",
                # MK-CTRL37R — Preserve frame_manifest_path, add scene_mp4_path
                frame_manifest_path="output/control/frames_manifest.json",
                scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
                qa_report_path=None,
                audio_output_path=None,
                episode_output_path=None,
            )
            storage.save(state2)

            # Load and verify both paths are preserved
            loaded2 = storage.load("ep01", "shot01")
            assert loaded2 is not None
            assert loaded2.frame_manifest_path == "output/control/frames_manifest.json"
            assert loaded2.scene_mp4_path == "output/scenes/ep01_shot01_scene.mp4"

            # Simulate state transition to qa_passed (scene_mp4_path must be preserved)
            state3 = ShotState(
                episode_id="ep01",
                shot_id="shot01",
                current_state="qa_passed",
                expected_next_action="attach_audio",
                last_updated="2024-01-01T00:02:00",
                # MK-CTRL37R — Preserve previous paths, add qa_report_path
                frame_manifest_path="output/control/frames_manifest.json",
                scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",  # Must be preserved
                qa_report_path="output/control/ep01_shot01_qa_report.json",
                audio_output_path=None,
                episode_output_path=None,
            )
            storage.save(state3)

            # Verify scene_mp4_path is still present (not overwritten by qa_report_path)
            loaded3 = storage.load("ep01", "shot01")
            assert loaded3 is not None
            assert loaded3.scene_mp4_path == "output/scenes/ep01_shot01_scene.mp4"
            assert loaded3.qa_report_path == "output/control/ep01_shot01_qa_report.json"

    def test_backward_compatibility_with_legacy_artifact_path(self):
        """Legacy artifact_path should still work as fallback."""
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="frames_generated",
            next_action="assemble_scene",
            existing_artifacts=ShotArtifacts(),
            artifact_path="output/control/frames_manifest.json",  # Legacy field
            # MK-CTRL37R — Typed artifact paths (None to test fallback)
            frame_manifest_path=None,
            scene_mp4_path=None,
            qa_report_path=None,
            audio_output_path=None,
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "assemble_scene")

        # Should fall back to legacy artifact_path
        assert plan.frame_manifest_path == "output/control/frames_manifest.json"
        assert plan.executable

    def test_no_legacy_artifact_paths_in_output(self):
        """Verify that action plans do not contain legacy wrong artifact paths."""
        # Test attach_audio does not receive qa_report.json as scene mp4
        report = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="qa_passed",
            next_action="attach_audio",
            existing_artifacts=ShotArtifacts(),
            brief_path="data/briefs/ep01_shot01_brief.md",
            # MK-CTRL37R — Typed artifact paths
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
            qa_report_path="output/control/ep01_shot01_qa_report.json",
            audio_output_path=None,
            episode_output_path=None,
        )

        planner = ActionPlanBuilder()
        plan = planner.build(report, "attach_audio")

        # Verify command preview does not contain qa_report.json
        assert plan.command_preview is not None
        assert "qa_report.json" not in plan.command_preview
        assert "ep01_shot01_scene.mp4" in plan.command_preview

        # Test render_episode does not receive audio_manifest.json as scene mp4
        report2 = ShotStateReport(
            episode_id="ep01",
            shot_id="shot01",
            current_state="audio_attached",
            next_action="render_episode",
            existing_artifacts=ShotArtifacts(),
            # MK-CTRL37R — Typed artifact paths
            frame_manifest_path="output/control/frames_manifest.json",
            scene_mp4_path="output/scenes/ep01_shot01_scene.mp4",
            qa_report_path="output/control/ep01_shot01_qa_report.json",
            audio_output_path="output/scenes/ep01_shot01_audio.mp4",
            episode_output_path=None,
        )

        plan2 = planner.build(report2, "render_episode")

        # Verify command preview does not contain audio_manifest.json
        assert plan2.command_preview is not None
        assert "audio_manifest.json" not in plan2.command_preview
        assert "ep01_shot01_audio.mp4" in plan2.command_preview
