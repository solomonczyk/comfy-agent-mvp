"""Tests for RC-COMBINE-V2-6001-6300 V8 dry-run guard enforcement.

Tests cover:
- dry_run_cannot_claim_real_generation
- empty_prompt_id_blocks_success
- empty_generated_assets_blocks_operator_visual_review
- missing_execute_flag_stays_safe
- real_execute_path_requires_explicit_execute
- guard_contradiction_detection
- state_transition_correct
"""

import json
import tempfile
from pathlib import Path

import pytest


def _create_dry_run_artifact_set(control_dir):
    """Create a dry-run artifact set (no execute flag)."""
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_generation_runtime_blocked",
            "next_allowed_action": "v8_generation_runtime_recovery_required",
            "generated_assets": [],
            "new_generation_performed": False,
            "comfyui_execution": False,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_execution.json", "w") as f:
        json.dump({
            "workflow_submitted": True,
            "generation_count": 1,
            "comfyui_execution": False,
            "execute_mode": False,
            "generation_performed": False,
            "prompt_id": "",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": [],
            "collection_status": "dry_run",
            "canonical_outputs_registered": False,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_result_review.json", "w") as f:
        json.dump({
            "generated_assets_count": 0,
            "next_allowed_action": "v8_operator_visual_review_required",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_operator_visual_review_packet.json", "w") as f:
        json.dump({
            "generated_assets": [],
            "generation_count": 0,
        }, f, indent=2)


def _create_real_artifact_set(control_dir):
    """Create a real execution artifact set (with execute flag)."""
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required",
            "generated_assets": ["output/assets/test.png"],
            "new_generation_performed": True,
            "comfyui_execution": True,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_execution.json", "w") as f:
        json.dump({
            "workflow_submitted": True,
            "generation_count": 1,
            "comfyui_execution": True,
            "execute_mode": True,
            "generation_performed": True,
            "prompt_id": "test-prompt-123",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": [{"path": "output/assets/test.png", "exists": True}],
            "collection_status": "success",
            "canonical_outputs_registered": True,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_result_review.json", "w") as f:
        json.dump({
            "generated_assets_count": 1,
            "next_allowed_action": "v8_operator_visual_review_required",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_operator_visual_review_packet.json", "w") as f:
        json.dump({
            "generated_assets": [{"path": "output/assets/test.png"}],
            "generation_count": 1,
        }, f, indent=2)


class TestDryRunGuardDryRunScenario:
    """Test guard behavior when real artifacts simulate dry-run scenario."""

    @pytest.fixture
    def project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_dry_run_artifact_set(root / "output" / "control")
            yield root

    def _run_guard_check(self, project_root):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
        from app.cli import combine_v8_dry_run_guard_check
        import argparse
        args = argparse.Namespace(
            project_root=str(project_root),
            json=False,
            silent=True,
        )
        return combine_v8_dry_run_guard_check(args)

    def _read_report(self, project_root):
        path = project_root / "output" / "control" / "combine_v2_v8_dry_run_guard_report.json"
        with open(path) as f:
            return json.load(f)

    def test_dry_run_cannot_claim_real_generation(self, project_root):
        exit_code = self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("dry_run_cannot_claim_real_generation") is True

    def test_empty_prompt_id_blocks_success(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        guards = report.get("guards_triggered", [])
        assert "empty_prompt_id_blocks_success" in guards
        assert report.get("guards_enforced", {}).get("dry_run_claimed_prompt_id_success") is False

    def test_empty_generated_assets_blocks_operator_visual_review(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        guards = report.get("guards_triggered", [])
        assert "empty_generated_assets_blocks_operator_visual_review" in guards
        assert report.get("guards_enforced", {}).get("operator_visual_review_blocked") is True

    def test_missing_execute_flag_stays_safe(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        guards = report.get("guards_triggered", [])
        assert "missing_execute_flag_stays_safe" in guards
        assert report.get("generation_allowed_now") is False
        assert report.get("new_generation_performed") is False

    def test_real_execute_path_requires_explicit_execute(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("guards_enforced", {}).get("dry_run_claimed_real_generation") is False
        assert report.get("guards_enforced", {}).get("dry_run_claimed_comfyui_execution") is False

    def test_dry_run_routes_to_authorization_not_visual_review(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("next_allowed_action") == "v8_generation_reexecution_authorization_required"
        assert report.get("guards_enforced", {}).get("dry_run_routes_to_authorization_not_visual_review") is True

    def test_state_transition_correct(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("dry_run_not_accepted_as_real_generation_new") is True
        assert report.get("production_accepted") is False

    def test_assembly_downstream_blocked(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("assembly_executed") is False
        assert report.get("downstream_executed") is False


class TestDryRunGuardRealScenario:
    """Test guard behavior with real execution artifacts."""

    @pytest.fixture
    def project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_real_artifact_set(root / "output" / "control")
            yield root

    def _run_guard_check(self, project_root):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
        from app.cli import combine_v8_dry_run_guard_check
        import argparse
        args = argparse.Namespace(
            project_root=str(project_root),
            json=False,
            silent=True,
        )
        return combine_v8_dry_run_guard_check(args)

    def _read_report(self, project_root):
        path = project_root / "output" / "control" / "combine_v2_v8_dry_run_guard_report.json"
        with open(path) as f:
            return json.load(f)

    def test_real_execution_no_contradictions(self, project_root):
        exit_code = self._run_guard_check(project_root)
        report = self._read_report(project_root)
        contradictions = report.get("contradictions", [])
        assert len(contradictions) == 0

    def test_real_execution_prompt_id_present(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("v8_artifact_findings", {}).get("prompt_id") == "test-prompt-123"
        assert report.get("guards_enforced", {}).get("dry_run_claimed_prompt_id_success") is True

    def test_real_execution_execute_mode_true(self, project_root):
        self._run_guard_check(project_root)
        report = self._read_report(project_root)
        assert report.get("v8_artifact_findings", {}).get("execute_mode") is True
        assert report.get("v8_artifact_findings", {}).get("comfyui_execution") is True
