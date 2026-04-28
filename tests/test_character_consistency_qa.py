"""Tests for CharacterConsistencyQA module (RC2-MULTISHOT1C-QA1)."""
import json
import tempfile
from pathlib import Path

import pytest

from app.judges.character_consistency_qa import CharacterConsistencyQA, run_identity_qa


class TestCharacterConsistencyQA:
    """Test CharacterConsistencyQA functionality."""

    def test_evaluate_batch_with_missing_frames(self):
        """Test that missing frames are detected."""
        qa = CharacterConsistencyQA()
        report = qa.evaluate_batch(
            frame_paths=["/nonexistent/frame1.png", "/nonexistent/frame2.png"],
            reference_image_path=None,
            shot_id="test_shot",
        )
        assert report["verdict"] == "rejected"
        assert "Missing frame files" in report["reason"]

    def test_evaluate_batch_without_face_detector(self):
        """Test that manual review is required when face detector unavailable."""
        qa = CharacterConsistencyQA()
        qa.face_cascade = None  # Simulate no face detector
        report = qa.evaluate_batch(
            frame_paths=[],
            reference_image_path=None,
            shot_id="test_shot",
        )
        assert report["verdict"] == "manual_review_required"
        assert "identity consistency could not be verified" in report["reason"]

    def test_evaluate_batch_with_valid_frames(self):
        """Test evaluation with valid frame paths."""
        qa = CharacterConsistencyQA()
        # Test with empty list (no frames to check)
        report = qa.evaluate_batch(
            frame_paths=[],
            reference_image_path=None,
            shot_id="test_shot",
        )
        assert "checks_performed" in report
        assert report["checks_performed"][0]["check"] == "frame_count"


class TestRunIdentityQA:
    """Test run_identity_qa function."""

    def test_run_identity_qa_missing_manifest(self, tmp_path):
        """Test that missing frame manifest is detected."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / "output" / "control").mkdir(parents=True)

        report = run_identity_qa(
            project_root=project_root,
            episode_id="ep01",
            shot_id="shot01",
        )
        assert report["verdict"] == "rejected"
        assert "frame_manifest_missing" in report["reason"]

    def test_run_identity_qa_shot_id_mismatch(self, tmp_path):
        """Test that shot_id mismatch is detected."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create manifest with wrong shot_id
        manifest = {
            "shot_id": "shot02",
            "frame_paths": [],
        }
        (control_dir / "frames_manifest.json").write_text(json.dumps(manifest))

        report = run_identity_qa(
            project_root=project_root,
            episode_id="ep01",
            shot_id="shot01",
        )
        assert report["verdict"] == "rejected"
        assert "manifest_shot_id_mismatch" in report["reason"]

    def test_run_identity_qa_no_frames(self, tmp_path):
        """Test that empty frame list is detected."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create manifest with no frames
        manifest = {
            "shot_id": "shot01",
            "frame_paths": [],
        }
        (control_dir / "frames_manifest.json").write_text(json.dumps(manifest))

        report = run_identity_qa(
            project_root=project_root,
            episode_id="ep01",
            shot_id="shot01",
        )
        assert report["verdict"] == "rejected"
        assert "no_frames_in_manifest" in report["reason"]


class TestIdentityQAIntegration:
    """Integration tests for identity QA in multi-shot context."""

    def test_identity_qa_report_required_after_generation(self, tmp_path):
        """Test that identity QA report is required after multi-frame generation."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True)
        frames_dir = project_root / "output" / "frames" / "shot01"
        frames_dir.mkdir(parents=True)

        # Create a dummy frame
        (frames_dir / "frame1.png").write_bytes(b"fake_png_data")

        # Create frames manifest without identity_qa_passed
        manifest = {
            "shot_id": "shot01",
            "frame_paths": [str(frames_dir / "frame1.png")],
            "frame_qc_passed": True,
        }
        (control_dir / "frames_manifest.json").write_text(json.dumps(manifest))

        # This should fail validation
        from app.cli import validate_multishot_generation
        from argparse import Namespace

        args = Namespace(
            project_root=str(project_root),
            episode="ep01",
            json=True,
        )
        result = validate_multishot_generation(args)
        assert result == 1  # Validation should fail

    def test_frames_manifest_qa_compliant_with_identity_drift(self, tmp_path):
        """Test that frames manifest with identity drift is not accepted."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create frames manifest with identity_qa_passed=false
        manifest = {
            "shot_id": "shot01",
            "frame_qc_passed": True,
            "identity_qa_passed": False,
            "artifact_status": "accepted",  # This should fail validation
        }
        (control_dir / "frames_manifest.json").write_text(json.dumps(manifest))

        from app.cli import validate_multishot_generation
        from argparse import Namespace

        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True,
        )
        result = validate_multishot_generation(args)
        assert result == 1  # Validation should fail

    def test_artifact_index_records_retry_candidate_after_identity_drift(self, tmp_path):
        """Test that artifact_index records retry_candidate after identity drift."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create artifact_index with identity_qa_passed=false but wrong status
        artifact_index = {
            "shots": [
                {
                    "shot_id": "shot01",
                    "frame_qc_passed": True,
                    "identity_qa_passed": False,
                    "status": "preflight_complete",  # Should be identity_qa_failed or retry_candidate
                }
            ]
        }
        (control_dir / "artifact_index.json").write_text(json.dumps(artifact_index))

        from app.cli import validate_multishot_generation
        from argparse import Namespace

        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True,
        )
        result = validate_multishot_generation(args)
        assert result == 1  # Validation should fail

    def test_identity_qa_failed_blocks_downstream(self, tmp_path):
        """Test that identity_qa_failed blocks downstream actions."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create episode ledger with identity_qa_failed followed by assemble_scene
        episode_ledger = {
            "records": [
                {"event_type": "identity_qa_failed"},
                {"event_type": "assemble_scene", "executed": True},
            ]
        }
        (control_dir / "episode_ledger.json").write_text(json.dumps(episode_ledger))

        from app.cli import validate_multishot_generation
        from argparse import Namespace

        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True,
        )
        result = validate_multishot_generation(args)
        assert result == 1  # Validation should fail
