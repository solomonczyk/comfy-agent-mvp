"""Tests for Brief Intake CLI commands."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLIHelp:
    """Test that CLI commands are registered and show help."""

    def test_build_brief_intake_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-build-brief-intake", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-build-brief-intake" in result.stdout
        assert "--input-text" in result.stdout

    def test_validate_brief_intake_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-validate-brief-intake", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-validate-brief-intake" in result.stdout

    def test_build_brief_operator_review_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-build-brief-operator-review", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-build-brief-operator-review" in result.stdout


class TestCLIBuildBriefIntake:
    """Test combine-build-brief-intake command."""

    def test_build_with_valid_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control").mkdir(parents=True, exist_ok=True)
            # Create a minimal artifact_index.json so the build succeeds
            with open(project_root / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            # Create a minimal episode_ledger.json
            with open(project_root / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-intake",
                    "--project-root", str(project_root),
                    "--input-text", "Create an educational video about AI pipeline for beginners",
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)
            assert output.get("brief_contract_created") is True
            assert output.get("generation_performed") is False
            assert output.get("production_accepted") is False

    def test_build_with_empty_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(project_root / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(project_root / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-intake",
                    "--project-root", str(project_root),
                    "--input-text", "",
                    "--json",
                ],
                capture_output=True, text=True,
            )
            output = json.loads(result.stdout)
            assert output.get("blocked_path_reached") is True

    def test_build_creates_artifact_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(project_root / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(project_root / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-intake",
                    "--project-root", str(project_root),
                    "--input-text", "Create an educational video about AI pipeline for beginners",
                ],
                capture_output=True, text=True,
            )

            brief_dir = project_root / "output" / "control" / "brief"
            assert (brief_dir / "brief_contract.json").exists()
            assert (brief_dir / "brief_validation_report.json").exists()
            assert (brief_dir / "project_constraints.json").exists()
            assert (brief_dir / "content_intent.json").exists()
            assert (brief_dir / "success_criteria.json").exists()
            assert (brief_dir / "forbidden_actions.json").exists()


class TestCLIValidateBriefIntake:
    """Test combine-validate-brief-intake command."""

    def test_validate_existing_brief(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(project_root / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(project_root / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            # Build first
            subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-intake",
                    "--project-root", str(project_root),
                    "--input-text", "Create an educational video",
                ],
                capture_output=True, text=True,
            )

            # Validate
            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-validate-brief-intake",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)
            assert output.get("brief_contract_created") is True


class TestCLIBuildBriefOperatorReview:
    """Test combine-build-brief-operator-review command."""

    def test_build_operator_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control").mkdir(parents=True, exist_ok=True)
            with open(project_root / "output" / "control" / "artifact_index.json", "w") as f:
                json.dump({"artifacts": []}, f)
            with open(project_root / "output" / "control" / "episode_ledger.json", "w") as f:
                json.dump({"events": []}, f)

            # Build first
            subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-intake",
                    "--project-root", str(project_root),
                    "--input-text", "Create an educational video about AI for beginners",
                ],
                capture_output=True, text=True,
            )

            # Build operator review
            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-brief-operator-review",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)
            assert output.get("status") == "ok"
            packet = output.get("packet", {})
            assert packet.get("operator_review_required") is True
            assert packet.get("generation_performed") is False
            assert packet.get("production_accepted") is False
            assert "62001-70000" in packet.get("next_recommended_layer", "")

            # Verify operator review file exists
            packet_path = project_root / "output" / "control" / "brief" / "brief_operator_review_packet.json"
            assert packet_path.exists()
