"""
Tests for Generated Asset Visual QA Package — RC-COMBINE-V2-102001-106000.

Covers:
- valid_asset_routes_to_operator_review
- missing_asset_routes_to_blocker
- sha256_mismatch_rejected
- stub_asset_rejected
- manifest_filesystem_mismatch_rejected
- technical_pass_not_visual_acceptance
- production_accepted_never_set_true
- artifact_index_updated
- episode_ledger_updated
- state_transition_correct
"""

import hashlib
import json
import os
import pytest
from pathlib import Path
from datetime import datetime, timezone

from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_asset(path: Path, width: int = 1024, height: int = 1024,
                     noise: bool = True) -> str:
    """Create a test PNG image with a gradient pattern (not solid color) and return SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height))
    # Fill with a gradient to avoid solid-color detection
    for x in range(width):
        for y in range(height):
            r = (x + y) % 256
            g = (x * 2 + y) % 256
            b = (x + y * 3) % 256
            img.putpixel((x, y), (r, g, b))
    img.save(path, "PNG")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_stub_asset(path: Path) -> str:
    """Create a stub (too-small) asset file and return its SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"stub")  # 4 bytes < 1024
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_input_artifacts(
    control_dir: Path,
    asset_rel_path: str,
    sha256: str,
    width: int = 1024,
    height: int = 1024,
    size_bytes: int = 100000,
) -> None:
    """Create the three input artifacts for testing."""
    control_dir.mkdir(parents=True, exist_ok=True)

    asset_entry = {
        "path": asset_rel_path,
        "exists": True,
        "readable": True,
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
        "sha256": sha256,
    }

    # generation_result_review.json
    with open(control_dir / "generation_result_review.json", "w") as f:
        json.dump({
            "task_id": "RC-COMBINE-V2-99001-102000",
            "stage": "generation_result_review",
            "status": "generation_result_review_required",
            "generated_assets": [asset_entry],
            "production_accepted": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, f)

    # visual_qa_input_packet.json
    with open(control_dir / "visual_qa_input_packet.json", "w") as f:
        json.dump({
            "task_id": "RC-COMBINE-V2-99001-102000",
            "stage": "generation_result_review_required",
            "generated_assets": [asset_entry],
            "production_accepted": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, f)

    # canonical_outputs_manifest.json
    with open(control_dir / "canonical_outputs_manifest.json", "w") as f:
        json.dump({
            "task_id": "RC-COMBINE-V2-99001-102000",
            "generated_assets": [asset_entry],
            "production_accepted": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, f)


def _make_artifact_index(control_dir: Path, state: str = "generation_result_review_required") -> None:
    """Create a minimal artifact_index.json."""
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": state,
            "next_allowed_action": state,
            "production_accepted": False,
            "stage_results": [],
        }, f)


def _make_episode_ledger(control_dir: Path) -> None:
    """Create a minimal episode_ledger.json."""
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "episode_ledger.json", "w") as f:
        json.dump([], f)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    control_dir = tmp_path / "output" / "control"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


# ===================================================================
# Tests
# ===================================================================

class TestGeneratedAssetVisualQAPackage:
    """Tests for the Visual QA package main function."""

    def test_valid_asset_routes_to_operator_review(self, project_dir: Path):
        """A valid asset with correct inputs routes to operator_visual_review_required."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_valid.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_valid.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert result["current_state"] == "operator_visual_review_required"
        assert result["next_allowed_action"] == "operator_visual_review_required"
        assert result["feature_completed"] is True
        assert result["asset_exists"] is True
        assert result["sha256_verified"] is True
        assert result["dimensions_verified"] is True
        assert result["stub_asset_detected"] is False
        assert result["technical_visual_qa_executed"] is True
        assert result["visual_qa_report_created"] is True
        assert result["operator_visual_review_packet_created"] is True
        assert result["artifact_index_updated"] is True
        assert result["episode_ledger_updated"] is True
        assert result["state_updated"] is True
        assert result["new_generation_performed"] is False
        assert result["visual_acceptance_executed"] is False
        assert result["production_accepted"] is False
        assert result["blockers"] == []

        # Verify verification fields
        assert result["input_generation_result_review_validated"] is True
        assert result["input_visual_qa_packet_validated"] is True
        assert result["canonical_manifest_validated"] is True
        assert result["blur_metric_recorded"] is True
        assert result["brightness_metric_recorded"] is True
        assert result["contrast_metric_recorded"] is True
        assert result["manifest_matches_filesystem"] is True
        assert result["operator_visual_decision_made_by_agent"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["retry_attempted"] is False
        assert result["comfyui_submit_executed"] is False

    def test_missing_asset_routes_to_blocker(self, project_dir: Path):
        """A missing asset creates a blocker instead of passing silently."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        control_dir = project_dir / "output" / "control"
        # Create input artifacts pointing to a non-existent asset
        _make_input_artifacts(
            control_dir,
            "output/assets/nonexistent.png",
            "0" * 64,
        )
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert len(result["blockers"]) > 0
        assert result["asset_exists"] is False

    def test_sha256_mismatch_rejected(self, project_dir: Path):
        """A SHA-256 mismatch is detected and blocked."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_mismatch.png"
        _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        # Report wrong SHA-256
        _make_input_artifacts(
            control_dir,
            "output/assets/test_mismatch.png",
            "a" * 64,  # wrong sha256
        )
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert len(result["blockers"]) > 0
        assert result["sha256_verified"] is False

    def test_stub_asset_rejected(self, project_dir: Path):
        """A stub asset (too small) is detected and blocked."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "stub.png"
        sha256 = _make_stub_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/stub.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert len(result["blockers"]) > 0
        assert result["stub_asset_detected"] is True

    def test_manifest_filesystem_mismatch_rejected(self, project_dir: Path):
        """A manifest that lists a different SHA-256 than the actual file is detected."""
        from app.qa.visual_qa_package import validate_manifest_matches_filesystem

        asset_path = project_dir / "output" / "assets" / "test_manifest.png"
        _make_test_asset(asset_path)

        # Manifest says file has different SHA-256
        manifest_assets = [
            {
                "path": "output/assets/test_manifest.png",
                "sha256": "a" * 64,  # wrong
            }
        ]

        result = validate_manifest_matches_filesystem(project_dir, manifest_assets)

        assert result["filesystem_matches"] is False
        assert len(result["mismatches"]) > 0

    def test_technical_pass_not_visual_acceptance(self, project_dir: Path):
        """Technical pass does NOT set visual acceptance, production_accepted, or assembly."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_tech_pass.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_tech_pass.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert result["visual_acceptance_executed"] is False
        assert result["production_accepted"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False

    def test_production_accepted_never_set_true(self, project_dir: Path):
        """production_accepted is never True in any output artifact."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_prod.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_prod.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert result["production_accepted"] is False

        # Check output artifacts
        with open(control_dir / "visual_qa_report.json") as f:
            report = json.load(f)
            assert report["production_accepted"] is False

        with open(control_dir / "operator_visual_review_packet.json") as f:
            packet = json.load(f)
            assert packet["production_accepted"] is False

        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)
            assert idx["production_accepted"] is False

    def test_artifact_index_updated(self, project_dir: Path):
        """artifact_index.json is updated with new state and stage result."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_idx.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_idx.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        run_generated_asset_visual_qa_package(str(project_dir))

        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx["current_state"] == "operator_visual_review_required"
        assert idx["visual_qa_executed"] is True
        assert idx["new_generation_performed"] is False
        assert "stage_results" in idx
        last_stage = idx["stage_results"][-1]
        assert last_stage["stage"] == "generated_asset_visual_qa_package"

    def test_episode_ledger_updated(self, project_dir: Path):
        """episode_ledger.json has a new event after QA package execution."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_ledger.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_ledger.png", sha256)
        _make_artifact_index(control_dir)
        _make_episode_ledger(control_dir)

        run_generated_asset_visual_qa_package(str(project_dir))

        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        if isinstance(ledger, list):
            assert any(
                e.get("event_type") == "generated_asset_visual_qa_package_executed"
                for e in ledger
            )
        elif isinstance(ledger, dict):
            events = ledger.get("events", [])
            assert any(
                e.get("event_type") == "generated_asset_visual_qa_package_executed"
                for e in events
            )

    def test_state_transition_correct(self, project_dir: Path):
        """State transitions from generation_result_review_required to operator_visual_review_required."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package

        asset_path = project_dir / "output" / "assets" / "test_state.png"
        sha256 = _make_test_asset(asset_path)
        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test_state.png", sha256)
        _make_artifact_index(control_dir, "generation_result_review_required")
        _make_episode_ledger(control_dir)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert result["current_state"] == "operator_visual_review_required"
        assert result["next_allowed_action"] == "operator_visual_review_required"


class TestInputArtifactValidation:
    """Tests for input artifact validation logic."""

    def test_all_artifacts_valid(self, project_dir: Path):
        """When all three input artifacts exist and match, validation passes."""
        from app.qa.visual_qa_package import validate_input_artifacts

        control_dir = project_dir / "output" / "control"
        _make_input_artifacts(control_dir, "output/assets/test.png", "a" * 64)

        result = validate_input_artifacts(control_dir)

        assert result["generation_result_review_valid"] is True
        assert result["visual_qa_input_packet_valid"] is True
        assert result["canonical_manifest_valid"] is True
        assert result["assets_match_across_artifacts"] is True
        assert result["blocker"] is None

    def test_missing_artifact_blocked(self, project_dir: Path):
        """When an input artifact is missing, validation fails."""
        from app.qa.visual_qa_package import validate_input_artifacts

        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        # Only create one of three
        with open(control_dir / "generation_result_review.json", "w") as f:
            json.dump({"generated_assets": []}, f)

        result = validate_input_artifacts(control_dir)

        assert result["blocker"] is not None
        assert "Missing" in result["blocker"]

    def test_sha256_mismatch_across_artifacts(self, project_dir: Path):
        """When artifacts reference different SHA-256, validation fails."""
        from app.qa.visual_qa_package import validate_input_artifacts

        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        entry1 = {"path": "a.png", "sha256": "a" * 64, "width": 1024, "height": 1024, "size_bytes": 100000}
        entry2 = {"path": "a.png", "sha256": "b" * 64, "width": 1024, "height": 1024, "size_bytes": 100000}

        with open(control_dir / "generation_result_review.json", "w") as f:
            json.dump({"generated_assets": [entry1]}, f)
        with open(control_dir / "visual_qa_input_packet.json", "w") as f:
            json.dump({"generated_assets": [entry2]}, f)
        with open(control_dir / "canonical_outputs_manifest.json", "w") as f:
            json.dump({"generated_assets": [entry1]}, f)

        result = validate_input_artifacts(control_dir)

        assert result["assets_match_across_artifacts"] is False
        assert result["blocker"] is not None


class TestAssetTechnicalValidation:
    """Tests for asset technical validation."""

    def test_valid_asset_passes(self, project_dir: Path):
        """A valid 1024x1024 PNG with correct SHA-256 passes validation."""
        from app.qa.visual_qa_package import validate_asset_technical

        asset_path = project_dir / "output" / "assets" / "valid.png"
        sha256 = _make_test_asset(asset_path)

        result = validate_asset_technical(
            project_dir,
            "output/assets/valid.png",
            sha256,
        )

        assert result["exists"] is True
        assert result["readable"] is True
        assert result["sha256_matches"] is True
        assert result["dimensions_match"] is True
        assert result["size_valid"] is True
        assert result["stub_asset"] is False
        assert result["technical_validation_pass"] is True
        assert result.get("solid_color_detected") is False

    def test_nonexistent_asset_fails(self, project_dir: Path):
        """A non-existent asset fails validation."""
        from app.qa.visual_qa_package import validate_asset_technical

        result = validate_asset_technical(
            project_dir,
            "output/assets/nope.png",
            "0" * 64,
        )

        assert result["exists"] is False
        assert result["technical_validation_pass"] is False

    def test_wrong_dimensions_detected(self, project_dir: Path):
        """An asset with wrong dimensions (not 1024x1024) is flagged."""
        from app.qa.visual_qa_package import validate_asset_technical

        asset_path = project_dir / "output" / "assets" / "wrong_dims.png"
        sha256 = _make_test_asset(asset_path, width=512, height=512)

        result = validate_asset_technical(
            project_dir,
            "output/assets/wrong_dims.png",
            sha256,
            expected_width=1024,
            expected_height=1024,
        )

        assert result["dimensions_match"] is False
        assert result["technical_validation_pass"] is False

    def test_stub_detected(self, project_dir: Path):
        """A stub file (< 1024 bytes) is detected."""
        from app.qa.visual_qa_package import validate_asset_technical

        asset_path = project_dir / "output" / "assets" / "stub.png"
        sha256 = _make_stub_asset(asset_path)

        result = validate_asset_technical(
            project_dir,
            "output/assets/stub.png",
            sha256,
        )

        assert result["stub_asset"] is True
        assert result["size_valid"] is False
        assert result["technical_validation_pass"] is False


class TestTechnicalMetrics:
    """Tests for technical Visual QA metrics computation."""

    def test_metrics_computed(self, project_dir: Path):
        """Technical metrics are computed for a valid asset."""
        from app.qa.visual_qa_package import compute_technical_visual_qa_metrics

        asset_path = project_dir / "output" / "assets" / "metrics.png"
        _make_test_asset(asset_path)

        result = compute_technical_visual_qa_metrics(project_dir, "output/assets/metrics.png")

        assert result["metrics_computed"] is True
        # blur_score, brightness, contrast should be populated (or baseline)
        assert "blur_score" in result
        assert "brightness" in result
        assert "contrast" in result
        assert result["automatic_visual_pass"] is False

    def test_automatic_visual_pass_never_true(self, project_dir: Path):
        """automatic_visual_pass is always False after metric computation."""
        from app.qa.visual_qa_package import compute_technical_visual_qa_metrics

        asset_path = project_dir / "output" / "assets" / "never_pass.png"
        _make_test_asset(asset_path)

        result = compute_technical_visual_qa_metrics(project_dir, "output/assets/never_pass.png")

        assert result["automatic_visual_pass"] is False


class TestManifestFilesystemMatch:
    """Tests for manifest vs filesystem validation."""

    def test_matching_manifest(self, project_dir: Path):
        """When manifest SHA-256 matches file, validation passes."""
        from app.qa.visual_qa_package import validate_manifest_matches_filesystem

        asset_path = project_dir / "output" / "assets" / "match.png"
        sha256 = _make_test_asset(asset_path)

        result = validate_manifest_matches_filesystem(project_dir, [
            {"path": "output/assets/match.png", "sha256": sha256},
        ])

        assert result["filesystem_matches"] is True
        assert len(result["mismatches"]) == 0

    def test_mismatched_manifest(self, project_dir: Path):
        """When manifest SHA-256 differs from file, validation fails."""
        from app.qa.visual_qa_package import validate_manifest_matches_filesystem

        asset_path = project_dir / "output" / "assets" / "mismatch.png"
        _make_test_asset(asset_path)

        result = validate_manifest_matches_filesystem(project_dir, [
            {"path": "output/assets/mismatch.png", "sha256": "a" * 64},
        ])

        assert result["filesystem_matches"] is False
        assert len(result["mismatches"]) > 0
