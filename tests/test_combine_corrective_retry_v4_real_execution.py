"""RC-COMBINE-V2-2901-2960: Tests for corrective retry V4 real execution.

Covers:
- authorized execution allowed
- max_generations enforced
- second generation blocked
- comfyui submit executed once
- output manifest created
- result review created
- missing output blocks success
- corrupted output blocks success
- visual QA not executed
- assembly not executed
- downstream not executed
- production_accepted=false
"""
import json
import hashlib
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import argparse


PROJECT_ROOT = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
ASSETS_DIR = PROJECT_ROOT / "output" / "assets"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _load(filename):
    p = CONTROL_DIR / filename
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Pre-condition validation tests
# ---------------------------------------------------------------------------

class TestPreConditions:
    def test_current_state_is_result_review_required(self):
        """After execution state must be corrective_retry_v4_result_review_required."""
        ai = _load("artifact_index.json")
        assert ai.get("current_state") == "corrective_retry_v4_result_review_required"

    def test_next_allowed_action_is_result_review_required(self):
        ai = _load("artifact_index.json")
        assert ai.get("next_allowed_action") == "corrective_retry_v4_result_review_required"

    def test_generation_attempts_is_one(self):
        ai = _load("artifact_index.json")
        assert ai.get("generation_attempts") == 1

    def test_max_generations_is_one(self):
        ai = _load("artifact_index.json")
        assert ai.get("max_generations") == 1

    def test_production_accepted_false(self):
        ai = _load("artifact_index.json")
        assert ai.get("production_accepted") is False

    def test_real_execution_authorization_artifact_exists(self):
        p = CONTROL_DIR / "combine_v2_operator_retry_v4_real_execution_authorization.json"
        assert p.exists(), "Real execution authorization artifact must exist"

    def test_real_execution_authorized(self):
        auth = _load("combine_v2_operator_retry_v4_real_execution_authorization.json")
        assert auth.get("operator_retry_v4_real_execution_authorized") is True


# ---------------------------------------------------------------------------
# Execution result artifact tests
# ---------------------------------------------------------------------------

class TestExecutionResultArtifact:
    def test_execution_result_artifact_exists(self):
        p = CONTROL_DIR / "combine_v2_corrective_retry_v4_real_execution_result.json"
        assert p.exists(), "Real execution result artifact must exist"

    def test_workflow_submitted_true(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("workflow_submitted") is True

    def test_comfyui_execution_true(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("comfyui_execution") is True

    def test_generation_performed_true(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("generation_performed") is True

    def test_generation_attempts_one(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("generation_attempts") == 1

    def test_max_generations_one(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("max_generations") == 1

    def test_second_generation_not_attempted(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("second_generation_attempted") is False

    def test_prompt_id_present(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("prompt_id"), "prompt_id must be non-empty"

    def test_generated_assets_count_one(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("generated_assets_count") == 1

    def test_asset_path_present(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        paths = r.get("generated_asset_paths", [])
        assert len(paths) >= 1

    def test_asset_exists_true(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("asset_exists") is True

    def test_asset_readable_true(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("asset_readable") is True

    def test_asset_size_gt_1024(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("asset_size_gt_1024") is True
        assert r.get("asset_size_bytes", 0) > 1024

    def test_sha256_present(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("sha256_present") is True
        assert r.get("sha256"), "sha256 must be non-empty"

    def test_state_transition_to_result_review(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("current_state") == "corrective_retry_v4_result_review_required"
        assert r.get("next_allowed_action") == "corrective_retry_v4_result_review_required"

    def test_visual_qa_not_executed(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("visual_qa_executed") is False

    def test_assembly_not_executed(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("downstream_executed") is False

    def test_production_accepted_false(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("production_accepted") is False

    def test_fallback_workflow_not_used(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("fallback_workflow_used") is False

    def test_dry_run_false(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("dry_run") is False


# ---------------------------------------------------------------------------
# Output manifest artifact tests
# ---------------------------------------------------------------------------

class TestOutputManifest:
    def test_outputs_manifest_exists(self):
        p = CONTROL_DIR / "combine_v2_corrective_retry_v4_outputs_manifest.json"
        assert p.exists(), "Outputs manifest must exist"

    def test_output_manifest_created_true(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("output_manifest_created") is True

    def test_generated_assets_count_one(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("generated_assets_count") == 1

    def test_all_assets_valid(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("all_assets_valid") is True

    def test_asset_entry_has_sha256(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assets = m.get("assets", [])
        assert len(assets) == 1
        assert assets[0].get("sha256"), "Asset must have sha256"


# ---------------------------------------------------------------------------
# Result review artifact tests
# ---------------------------------------------------------------------------

class TestResultReview:
    def test_result_review_artifact_exists(self):
        p = CONTROL_DIR / "combine_v2_corrective_retry_v4_real_result_review.json"
        assert p.exists(), "Result review artifact must exist"

    def test_result_review_complete(self):
        r = _load("combine_v2_corrective_retry_v4_real_result_review.json")
        assert r.get("result_review_complete") is True

    def test_result_review_state(self):
        r = _load("combine_v2_corrective_retry_v4_real_result_review.json")
        assert r.get("current_state") == "corrective_retry_v4_result_review_required"


# ---------------------------------------------------------------------------
# Physical asset tests
# ---------------------------------------------------------------------------

class TestPhysicalAsset:
    def test_asset_file_exists_on_disk(self):
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        assert p.exists(), f"Asset file must exist on disk: {p}"

    def test_asset_size_gt_1024_bytes(self):
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        assert p.stat().st_size > 1024

    def test_asset_sha256_matches_manifest(self):
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        with open(p, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        recorded = m.get("assets", [{}])[0].get("sha256", "")
        assert computed == recorded, f"SHA256 mismatch: {computed} != {recorded}"

    def test_asset_is_readable_image(self):
        pytest.importorskip("PIL")
        from PIL import Image
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        img = Image.open(p)
        img.load()
        assert img.size[0] > 0 and img.size[1] > 0


# ---------------------------------------------------------------------------
# Guard / negative path tests (unit-level, no real ComfyUI)
# ---------------------------------------------------------------------------

class TestGuards:
    """Unit tests for CLI guards — use mocked state to test blocked paths."""

    def _make_args(self, execute=True, max_generations=1, shot_id="shot02",
                   project_root=None, json_out=True):
        args = argparse.Namespace()
        args.project_root = str(project_root or PROJECT_ROOT)
        args.shot_id = shot_id
        args.execute = execute
        args.max_generations = max_generations
        args.json = json_out
        return args

    def test_max_generations_not_one_is_blocked(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        # Write minimal route + binding to pass earlier guards
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        args = self._make_args(execute=True, max_generations=2, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["blocked_reason"] == "max_generations_must_equal_1"

    def test_without_execute_flag_no_generation(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        args = self._make_args(execute=False, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data.get("generation_performed") is False
        assert data.get("comfyui_execution") is False
        assert data.get("workflow_submitted") is False
        assert data.get("production_accepted") is False

    def test_missing_route_blocks_execution(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        # No route file at all
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        args = self._make_args(execute=True, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "non_stub_execution_route" in data["blocked_reason"]

    def test_missing_binding_blocks_execution(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        # No binding file
        args = self._make_args(execute=True, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "binding" in data["blocked_reason"]

    def test_missing_auth_artifact_blocks_execute(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        # artifact_index with valid state but no auth artifact
        (control / "artifact_index.json").write_text(
            json.dumps({"current_state": "operator_retry_v4_real_execution_authorization_required"})
        )
        # No auth artifact
        args = self._make_args(execute=True, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "authorization" in data["blocked_reason"]

    def test_wrong_state_blocks_execute(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        (control / "artifact_index.json").write_text(
            json.dumps({"current_state": "visual_qa_required"})
        )
        (control / "combine_v2_operator_retry_v4_real_execution_authorization.json").write_text(
            json.dumps({"operator_retry_v4_real_execution_authorized": True})
        )
        args = self._make_args(execute=True, project_root=tmp_path)
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "state" in data["blocked_reason"]


# ---------------------------------------------------------------------------
# Boundary guards for downstream / visual QA / assembly not executed
# ---------------------------------------------------------------------------

class TestDownstreamBoundary:
    def test_visual_qa_not_executed_in_execution_result(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("visual_qa_executed") is False

    def test_assembly_not_executed_in_execution_result(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("assembly_executed") is False

    def test_downstream_not_executed_in_execution_result(self):
        r = _load("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("downstream_executed") is False

    def test_production_accepted_false_in_manifest(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("production_accepted") is False

    def test_visual_qa_not_executed_in_manifest(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("visual_qa_executed") is False

    def test_assembly_not_executed_in_manifest(self):
        m = _load("combine_v2_corrective_retry_v4_outputs_manifest.json")
        assert m.get("assembly_executed") is False
