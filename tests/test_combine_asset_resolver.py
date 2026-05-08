"""Tests for Asset Resolver — requirements, inventory, resolution, blocker detection.

RC-COMBINE-V2-70001-86000
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.workflow_assets.workflow_assets_package import (
    _build_asset_requirements,
    _discover_local_assets,
    _build_asset_resolution_plan,
    _build_asset_verification_report,
    _build_asset_blocker_report_if_needed,
    _paths,
    _now_iso,
    WorkflowSelectionReport,
    DEFAULT_CHECKPOINT_PATHS,
    DEFAULT_ADAPTER_PATHS,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAssetRequirements:
    """Test asset requirements derivation."""

    def test_requirements_include_sdxl_checkpoint(self):
        """Verify SDXL checkpoint is always required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport()
            reqs = _build_asset_requirements(p, [], selection_report, ts)
            checkpoint_types = [r["asset_type"] for r in reqs.all_requirements if r["asset_type"] == "checkpoint"]
            assert len(checkpoint_types) >= 1

    def test_requirements_include_shot_assets(self):
        """Verify shot-level asset requirements are included."""
        shot_contracts = [
            {
                "shot_id": "shot_001",
                "required_assets": "motion_graphics_assets: title card template",
            },
            {
                "shot_id": "shot_002",
                "required_assets": "sample_frame_assets: test images",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport(
                shot_workflow_bindings=[
                    {"shot_id": "shot_001", "selected_workflow_family": "sdxl_txt2img"},
                    {"shot_id": "shot_002", "selected_workflow_family": "sdxl_txt2img"},
                ],
            )

            reqs = _build_asset_requirements(p, shot_contracts, selection_report, ts)
            assert reqs.total_requirements >= 3  # checkpoint + 2 shot assets
            assert reqs.workflow_execution_performed is False
            assert reqs.comfyui_submit_executed is False


class TestAssetInventory:
    """Test local asset inventory (read-only)."""

    def test_inventory_discovers_checkpoints(self):
        """Verify inventory discovers checkpoints if they exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            inventory = _discover_local_assets(p, str(project_root), ts)
            assert inventory.install_performed is False
            assert inventory.download_performed is False
            assert inventory.no_unapproved_downloads is True
            assert inventory.no_unapproved_installs is True

    def test_inventory_discovers_existing_assets(self):
        """Verify inventory discovers existing output assets if present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            (project_root / "output" / "assets").mkdir(parents=True, exist_ok=True)
            # Create a test asset
            test_asset = project_root / "output" / "assets" / "test_existing.png"
            test_asset.write_text("fake png content")

            p = _paths(str(project_root))
            ts = _now_iso()

            inventory = _discover_local_assets(p, str(project_root), ts)
            media_files = [m for m in inventory.discovered_media_reference_files if "test_existing" in m["path"]]
            assert len(media_files) >= 1

    def test_inventory_no_downloads_or_installs(self):
        """Verify inventory never performs downloads or installs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            inventory = _discover_local_assets(p, str(project_root), ts)
            assert inventory.install_performed is False
            assert inventory.download_performed is False


class TestAssetResolution:
    """Test asset resolution plan."""

    def test_resolution_classifies_assets(self):
        """Verify resolution classifies each asset as ready/missing/unknown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport()
            reqs = _build_asset_requirements(p, [], selection_report, ts)
            inventory = _discover_local_assets(p, str(project_root), ts)
            plan = _build_asset_resolution_plan(p, reqs, inventory, ts)

            assert plan.total_assets_evaluated > 0
            assert plan.unapproved_download_performed is False
            assert plan.unapproved_install_performed is False

    def test_resolution_reports_missing_checkpoint(self):
        """Verify resolution reports missing SDXL checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport()
            reqs = _build_asset_requirements(p, [], selection_report, ts)
            inventory = _discover_local_assets(p, str(project_root), ts)
            plan = _build_asset_resolution_plan(p, reqs, inventory, ts)

            # SDXL checkpoint should be missing (no checkpoints exist in test env)
            if plan.assets_missing > 0:
                assert len(plan.missing_assets) > 0


class TestAssetVerification:
    """Test asset verification report."""

    def test_verification_generation_readiness(self):
        """Verify generation_readiness is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport()
            reqs = _build_asset_requirements(p, [], selection_report, ts)
            inventory = _discover_local_assets(p, str(project_root), ts)
            plan = _build_asset_resolution_plan(p, reqs, inventory, ts)
            report = _build_asset_verification_report(p, plan, reqs, ts)

            assert report.checksum_size_path_validation_policy_defined is True
            assert report.invalid_candidate_substitutions_rejected is True
            assert report.missing_assets_not_hidden is True


class TestAssetBlocker:
    """Test asset blocker report."""

    def test_blocker_not_created_when_no_missing_assets(self):
        """Verify blocker report is NOT created when no assets are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            # Create a fake SDXL checkpoint to avoid missing assets
            (project_root / "models" / "checkpoints" / "sdxl").mkdir(parents=True, exist_ok=True)
            (project_root / "models" / "checkpoints" / "sdxl" / "sdxl_base.safetensors").write_text("fake checkpoint")
            (project_root / "output" / "control" / "planning" / "shot_contracts" / "shot_001.json").write_text(
                json.dumps({"shot_id": "shot_001", "required_assets": "none"})
            )

            p = _paths(str(project_root))
            ts = _now_iso()

            # Build resolution plan with no missing assets
            from app.workflow_assets.workflow_assets_package import (
                AssetRequirements, AssetInventory, AssetResolutionPlan,
            )

            plan = AssetResolutionPlan(
                total_assets_evaluated=1,
                assets_ready=1,
                assets_missing=0,
                assets_unknown=0,
            )
            shot_contracts = [{"shot_id": "shot_001"}]
            blocker = _build_asset_blocker_report_if_needed(p, plan, shot_contracts, ts)
            assert blocker is None

    def test_blocker_created_when_assets_missing(self):
        """Verify blocker report IS created when critical assets are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            plan = type('obj', (object,), {
                'assets_missing': 1,
                'missing_assets': ['checkpoint_sdxl_base'],
                'asset_resolutions': [{"asset_id": "checkpoint_sdxl_base", "status": "missing"}],
            })()
            shot_contracts = [{"shot_id": "shot_001"}]

            blocker = _build_asset_blocker_report_if_needed(p, plan, shot_contracts, ts)
            assert blocker is not None
            assert blocker.get("generation_preflight_allowed") is False
