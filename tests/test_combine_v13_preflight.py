"""Tests for V13 controlled generation preflight.

Verifies that the V13 correction package is verified, mouth/teeth defects
are detected, and preflight report is generated correctly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REQUIRED_DEFECTS = ["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"]
V13_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"


class TestV13PreflightReports:
    """Verify preflight report fields and constraints."""

    def test_preflight_report_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_preflight_report.json"
        assert path.exists(), "Preflight report must exist"

    def test_preflight_report_fields(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_preflight_report.json"
        with open(path) as f:
            report = json.load(f)

        assert report.get("v13_preflight_completed") is True
        assert report.get("v13_correction_package_verified") is True
        assert report.get("full_mouth_teeth_defect_set_used") is True
        assert report.get("generation_allowed_after_preflight") is True
        assert report.get("patch_applied_if_needed") is True

    def test_preflight_no_missing_defects(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_preflight_report.json"
        with open(path) as f:
            report = json.load(f)

        missing = report.get("missing_defects_before_patch", [])
        assert isinstance(missing, list)
        assert len(missing) == 0, f"Expected no missing defects, got: {missing}"

    def test_correction_package_has_required_defects(self):
        plan_path = Path(V13_CONTROL_DIR) / "combine_v2_v13_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        critical_failures = plan.get("qa_evidence", {}).get("critical_failures", [])
        for defect in REQUIRED_DEFECTS:
            assert defect in critical_failures, f"Missing required defect: {defect}"

    def test_prompt_patch_includes_teeth_negative_prompts(self):
        prompt_path = Path(V13_CONTROL_DIR) / "combine_v2_v13_prompt_patch.json"
        with open(prompt_path) as f:
            patch = json.load(f)

        strengthened = patch.get("negative_prompt_strengthened", [])
        assert "bad teeth" in strengthened
        assert "malformed teeth" in strengthened
        assert "unnatural mouth" in strengthened

    def test_quality_pipeline_patch_includes_mouth_checks(self):
        qp_path = Path(V13_CONTROL_DIR) / "combine_v2_v13_quality_pipeline_patch.json"
        with open(qp_path) as f:
            patch = json.load(f)

        checklist = patch.get("qa_checklist_additions", [])
        assert any("teeth" in item.lower() for item in checklist)
        assert any("mouth" in item.lower() for item in checklist)

    def test_all_four_correction_artifacts_exist(self):
        for name in [
            "combine_v2_v13_correction_plan.json",
            "combine_v2_v13_prompt_patch.json",
            "combine_v2_v13_workflow_patch.json",
            "combine_v2_v13_quality_pipeline_patch.json",
        ]:
            assert (Path(V13_CONTROL_DIR) / name).exists(), f"Missing: {name}"

    def test_generation_not_allowed_before_authorization(self):
        plan_path = Path(V13_CONTROL_DIR) / "combine_v2_v13_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        assert plan.get("generation_allowed") is False
        assert plan.get("retry_allowed") is False
        assert plan.get("blind_retry_allowed") is False


class TestV13PreflightEdgeCases:
    """Verify edge cases in preflight defect detection."""

    def test_preflight_reports_patch_not_needed_when_all_defects_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_preflight_report.json"
        with open(path) as f:
            report = json.load(f)
        assert report.get("patch_applied_if_needed") is True
        assert len(report.get("missing_defects_before_patch", [])) == 0

    def test_correction_plan_has_production_guards(self):
        plan_path = Path(V13_CONTROL_DIR) / "combine_v2_v13_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        assert plan.get("production_accepted") is False
        assert plan.get("assembly_allowed") is False
        assert plan.get("downstream_allowed") is False
