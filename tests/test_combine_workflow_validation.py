"""Tests for Workflow Validation — shot contract binding verification, forbidden workflows.

RC-COMBINE-V2-70001-86000
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.workflow_assets.workflow_assets_package import (
    _build_workflow_validation_report,
    _build_workflow_selection_report,
    _build_workflow_patch_plan,
    _build_workflow_inventory,
    _build_submitted_workflow_contract,
    _paths,
    _now_iso,
    WorkflowSelectionReport,
    WorkflowValidationReport,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWorkflowValidation:
    """Test workflow validation logic."""

    def test_validation_passes_with_valid_bindings(self):
        """Verify validation passes when all shots have valid workflow bindings."""
        selection_report = WorkflowSelectionReport(
            total_shots_mapped=2,
            shot_workflow_bindings=[
                {"shot_id": "shot_001", "selected_workflow_family": "sdxl_txt2img",
                 "scene_id": "scene_001", "selection_reason": "default",
                 "unsupported_requirements": [], "fallback_policy": "no_fallback_needed",
                 "forbidden_fallback_detected": False, "workflow_readiness_status": "ready"},
                {"shot_id": "shot_002", "selected_workflow_family": "sdxl_txt2img",
                 "scene_id": "scene_001", "selection_reason": "default",
                 "unsupported_requirements": [], "fallback_policy": "no_fallback_needed",
                 "forbidden_fallback_detected": False, "workflow_readiness_status": "ready"},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            report = _build_workflow_validation_report(p, selection_report, ts)
            assert report.validation_passed is True
            assert report.shot_contract_binding_verified is True
            assert report.ksampler_required is True
            assert report.saveimage_required is True
            assert report.filename_prefix_policy_defined is True
            assert report.resolution_policy_enforced is True
            assert report.legacy_512_workflow_blocked is True
            assert report.stub_workflow_blocked is True
            assert report.workflow_execution_performed is False
            assert report.comfyui_submit_executed is False
            assert report.production_accepted is False

    def test_validation_fails_with_forbidden_fallback(self):
        """Verify validation fails when a forbidden fallback is detected."""
        selection_report = WorkflowSelectionReport(
            total_shots_mapped=1,
            shot_workflow_bindings=[
                {"shot_id": "shot_001", "selected_workflow_family": "legacy_512_txt2img",
                 "scene_id": "scene_001", "selection_reason": "fallback",
                 "unsupported_requirements": [], "fallback_policy": "512x512_fallback",
                 "forbidden_fallback_detected": True, "workflow_readiness_status": "blocked"},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            report = _build_workflow_validation_report(p, selection_report, ts)
            assert report.validation_passed is False
            assert report.shot_contract_binding_verified is False
            assert len(report.errors) > 0

    def test_validation_fails_with_no_bindings(self):
        """Verify validation fails when no shot-workflow bindings exist."""
        selection_report = WorkflowSelectionReport(
            total_shots_mapped=0,
            shot_workflow_bindings=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            report = _build_workflow_validation_report(p, selection_report, ts)
            assert report.validation_passed is False
            assert len(report.errors) > 0

    def test_legacy_512_is_blocked(self):
        """Verify legacy 512x512 workflow is always blocked in validation report."""
        selection_report = WorkflowSelectionReport(
            total_shots_mapped=1,
            shot_workflow_bindings=[
                {"shot_id": "shot_001", "selected_workflow_family": "sdxl_txt2img",
                 "scene_id": "scene_001", "selection_reason": "default",
                 "unsupported_requirements": [], "fallback_policy": "no_fallback_needed",
                 "forbidden_fallback_detected": False, "workflow_readiness_status": "ready"},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            report = _build_workflow_validation_report(p, selection_report, ts)
            assert report.legacy_512_workflow_blocked is True

    def test_stub_workflow_is_blocked(self):
        """Verify stub workflow is always blocked in validation report."""
        selection_report = WorkflowSelectionReport(
            total_shots_mapped=1,
            shot_workflow_bindings=[
                {"shot_id": "shot_001", "selected_workflow_family": "sdxl_txt2img",
                 "scene_id": "scene_001", "selection_reason": "default",
                 "unsupported_requirements": [], "fallback_policy": "no_fallback_needed",
                 "forbidden_fallback_detected": False, "workflow_readiness_status": "ready"},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            report = _build_workflow_validation_report(p, selection_report, ts)
            assert report.stub_workflow_blocked is True

    def test_patch_plan_blocks_legacy_and_stub(self):
        """Verify patch plan explicitly blocks legacy and stub workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            plan = _build_workflow_patch_plan(p, [], ts)
            assert plan.legacy_512_workflow_blocked is True
            assert plan.stub_workflow_blocked is True
            assert plan.stub_minimal_workflow_blocked is True
            assert plan.workflow_execution_performed is False
            assert plan.comfyui_submit_executed is False

    def test_submitted_workflow_contract_forbids_fakes(self):
        """Verify submitted workflow contract forbids fake prompt IDs and assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            selection_report = WorkflowSelectionReport(
                total_shots_mapped=1,
                shot_workflow_bindings=[
                    {"shot_id": "shot_001", "selected_workflow_family": "sdxl_txt2img",
                     "scene_id": "scene_001", "selection_reason": "default",
                     "unsupported_requirements": [], "fallback_policy": "no_fallback_needed",
                     "forbidden_fallback_detected": False, "workflow_readiness_status": "ready"},
                ],
            )

            contract = _build_submitted_workflow_contract(p, [], selection_report, ts)
            assert contract.forbidden_fake_prompt_id is True
            assert contract.forbidden_fake_asset is True
            assert contract.comfyui_submit_executed is False
            assert contract.workflow_execution_performed is False
            assert contract.max_generations_per_gate == 1
            assert contract.expected_runtime_executor == "comfyui"
