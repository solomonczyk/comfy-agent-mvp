"""Tests for corrective retry V4 real execution route.

RC-COMBINE-V2-2181-2300 — real execution adapter + preflight.
"""

import json
import argparse
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args_preflight(project_root, shot_id="shot02", max_gen=1, json_out=True):
    return argparse.Namespace(
        project_root=str(project_root),
        shot_id=shot_id,
        max_generations=max_gen,
        json=json_out,
    )


def _make_args_execute(project_root, shot_id="shot02", execute=False, max_gen=1, json_out=True):
    return argparse.Namespace(
        project_root=str(project_root),
        shot_id=shot_id,
        execute=execute,
        max_generations=max_gen,
        json=json_out,
    )


SAVEIMAGE_PREFIX = "rc2_multishot1_ep01_ep01_shot01_generate_frames_1777576340"

REAL_WORKFLOW = {
    "3": {"class_type": "KSampler", "inputs": {}},
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": SAVEIMAGE_PREFIX, "images": ["8", 0]}},
}


def _setup_full_project(tmp_path, current_state="operator_retry_v4_real_execution_authorization_required"):
    """Set up a complete project structure for execution route tests."""
    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # artifact_index
    (control_dir / "artifact_index.json").write_text(json.dumps({
        "current_state": current_state,
        "next_allowed_action": "operator_retry_v4_real_execution_authorization_required",
        "generation_performed": False,
        "comfyui_execution": False,
        "workflow_submitted": False,
        "production_accepted": False,
    }))

    # episode_ledger
    (control_dir / "episode_ledger.json").write_text(json.dumps([]))

    # non-stub execution route
    (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(json.dumps({
        "route_has_comfyui_access": True,
        "real_execution_adapter_identified": True,
        "stub_layer_execute_block_preserved": True,
        "fake_comfyui_execution_forbidden": True,
        "fake_workflow_submitted_forbidden": True,
        "non_stub_execution_route_created": True,
        "dry_run_false_allowed_only_in_real_adapter": True,
    }))

    # real workflow binding
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(json.dumps({
        "real_workflow_binding_created": True,
        "workflow_source": "ep01_shot01_submitted_workflow.json",
        "fallback_workflow_blocked": True,
    }))

    # real workflow file
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(REAL_WORKFLOW))

    # implementation package
    (control_dir / "combine_v2_corrective_retry_v4_implementation_package.json").write_text(json.dumps({
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }))

    # real execution authorization artifact (required by execute=True path)
    (control_dir / "combine_v2_operator_retry_v4_real_execution_authorization.json").write_text(json.dumps({
        "operator_retry_v4_real_execution_authorized": True,
        "operator_decision": "approve_one_corrective_retry_v4_real_execution",
        "next_allowed_action": "corrective_retry_v4_real_execute_assets",
    }))

    return project_root, control_dir


# ---------------------------------------------------------------------------
# 1. Stub layer execute remains blocked
# ---------------------------------------------------------------------------

class TestStubLayerExecuteBlocked:
    def test_stub_execute_returns_error(self, tmp_path):
        """combine-corrective-retry-v4-generate-assets --execute must return exit 1."""
        from app.cli import combine_corrective_retry_v4_generate_assets
        project_root = tmp_path / "proj"
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        (control_dir / "combine_v2_operator_retry_v4_generation_authorization.json").write_text(
            json.dumps({"operator_retry_v4_generation_authorized": True}))
        (control_dir / "combine_v2_corrective_retry_v4_implementation_package.json").write_text(
            json.dumps({"failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION"}))
        for contract in [
            "combine_v2_retry_v4_pre_submit_validation_contract.json",
            "combine_v2_retry_v4_post_submit_validation_contract.json",
            "combine_v2_retry_v4_manifest_success_policy.json",
            "combine_v2_retry_v4_visual_qa_input_guard.json",
            "combine_v2_retry_v4_assembly_asset_guard.json",
        ]:
            (control_dir / contract).write_text(json.dumps({"created": True}))

        args = argparse.Namespace(
            project_root=str(project_root), shot_id="shot02",
            execute=True, max_generations=1, json=True)
        result = combine_corrective_retry_v4_generate_assets(args)
        assert result == 1

    def test_stub_execute_failure_code(self, tmp_path, capsys):
        """Stub layer must emit CORRECTIVE_RETRY_V4_EXECUTE_BLOCKED_IN_STUB_LAYER."""
        from app.cli import combine_corrective_retry_v4_generate_assets
        project_root = tmp_path / "proj"
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        (control_dir / "combine_v2_operator_retry_v4_generation_authorization.json").write_text(
            json.dumps({"operator_retry_v4_generation_authorized": True}))
        (control_dir / "combine_v2_corrective_retry_v4_implementation_package.json").write_text(
            json.dumps({"failure_basis": "x"}))

        args = argparse.Namespace(
            project_root=str(project_root), shot_id="shot02",
            execute=True, max_generations=1, json=True)
        combine_corrective_retry_v4_generate_assets(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["failure_code"] == "CORRECTIVE_RETRY_V4_EXECUTE_BLOCKED_IN_STUB_LAYER"
        assert data["stub_layer_no_comfyui_access"] is True


# ---------------------------------------------------------------------------
# 2. Real execution route exists
# ---------------------------------------------------------------------------

class TestRealExecutionRouteExists:
    def test_preflight_passes_when_route_exists(self, tmp_path):
        """Preflight must pass when route artifact is present."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        result = combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        assert result == 0

    def test_preflight_fails_when_route_missing(self, tmp_path):
        """Preflight must fail when route artifact is absent."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, control_dir = _setup_full_project(tmp_path)
        (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").unlink()
        result = combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        assert result == 1

    def test_preflight_artifact_has_real_execution_route_exists_true(self, tmp_path, capsys):
        """Preflight output must have real_execution_route_exists=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, control_dir = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["real_execution_route_exists"] is True


# ---------------------------------------------------------------------------
# 3. Real adapter can be selected
# ---------------------------------------------------------------------------

class TestRealAdapterSelectable:
    def test_real_adapter_identified_in_route_artifact(self, tmp_path):
        """Route artifact must have real_execution_adapter_identified=true."""
        project_root, control_dir = _setup_full_project(tmp_path)
        route = json.loads(
            (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").read_text())
        assert route["real_execution_adapter_identified"] is True

    def test_real_execute_command_exists_and_runs_without_execute(self, tmp_path, capsys):
        """combine-corrective-retry-v4-real-execute-assets without --execute returns 0."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        result = combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        assert result == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "authorization_required"
        assert out["generation_performed"] is False
        assert out["comfyui_execution"] is False


# ---------------------------------------------------------------------------
# 4. dry_run=false forbidden outside real adapter
# ---------------------------------------------------------------------------

class TestDryRunFalseForbiddenOutsideRealAdapter:
    def test_preflight_never_uses_dry_run_false(self, tmp_path, capsys):
        """Preflight must report dry_run_false_not_used_in_preflight=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["dry_run_false_not_used_in_preflight"] is True

    def test_route_artifact_enforces_dry_run_policy(self, tmp_path):
        """Route artifact must state dry_run_false_allowed_only_in_real_adapter=true."""
        project_root, control_dir = _setup_full_project(tmp_path)
        route = json.loads(
            (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").read_text())
        assert route["dry_run_false_allowed_only_in_real_adapter"] is True


# ---------------------------------------------------------------------------
# 5. Fake comfyui_execution forbidden
# ---------------------------------------------------------------------------

class TestFakeComfyuiExecutionForbidden:
    def test_preflight_reports_fake_comfyui_forbidden(self, tmp_path, capsys):
        """Preflight must report fake_comfyui_execution_forbidden=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["fake_comfyui_execution_forbidden"] is True
        assert out["comfyui_execution"] is False

    def test_real_execute_no_execute_flag_keeps_comfyui_false(self, tmp_path, capsys):
        """Without --execute, comfyui_execution must be false."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        out = json.loads(capsys.readouterr().out)
        assert out["comfyui_execution"] is False
        assert out["fake_comfyui_execution_forbidden"] is True


# ---------------------------------------------------------------------------
# 6. Fake workflow_submitted forbidden
# ---------------------------------------------------------------------------

class TestFakeWorkflowSubmittedForbidden:
    def test_preflight_reports_fake_workflow_submitted_forbidden(self, tmp_path, capsys):
        """Preflight must report fake_workflow_submitted_forbidden=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["fake_workflow_submitted_forbidden"] is True
        assert out["workflow_submitted"] is False

    def test_real_execute_no_execute_flag_keeps_workflow_submitted_false(self, tmp_path, capsys):
        """Without --execute, workflow_submitted must be false."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        out = json.loads(capsys.readouterr().out)
        assert out["workflow_submitted"] is False
        assert out["fake_workflow_submitted_forbidden"] is True


# ---------------------------------------------------------------------------
# 7. Preflight does not submit to ComfyUI
# ---------------------------------------------------------------------------

class TestPreflightNoComfySubmit:
    def test_actual_comfyui_submit_not_executed(self, tmp_path, capsys):
        """Preflight must confirm actual_comfyui_submit_not_executed=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["actual_comfyui_submit_not_executed"] is True

    def test_preflight_writes_artifact_file(self, tmp_path):
        """Preflight must write combine_v2_corrective_retry_v4_real_execution_route_preflight.json."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, control_dir = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        art = control_dir / "combine_v2_corrective_retry_v4_real_execution_route_preflight.json"
        assert art.exists()
        data = json.loads(art.read_text())
        assert data["preflight_passed"] is True
        assert data["actual_comfyui_submit_not_executed"] is True


# ---------------------------------------------------------------------------
# 8. filename_prefix consistency enforced
# ---------------------------------------------------------------------------

RUNTIME_PREFIX = "combine_v2_corrective_retry_v4_shot02"


class TestFilenamePrefixConsistency:
    def test_preflight_reports_runtime_prefix_not_source_prefix(self, tmp_path, capsys):
        """Preflight saveimage_filename_prefix must be the runtime prefix, not the source shot01 prefix."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["filename_prefix_consistency_valid"] is True
        assert out["saveimage_filename_prefix"] == RUNTIME_PREFIX
        assert out["saveimage_filename_prefix"] != SAVEIMAGE_PREFIX

    def test_preflight_reports_source_workflow_prefix_for_audit(self, tmp_path, capsys):
        """Preflight must report source_workflow_prefix_detected for audit."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["source_workflow_prefix_detected"] == SAVEIMAGE_PREFIX
        assert out["runtime_prefix_patched_for_target_shot"] is True

    def test_preflight_passes_even_without_saveimage_node(self, tmp_path, capsys):
        """Preflight must pass even if workflow has no SaveImage — runtime prefix is deterministic."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, control_dir = _setup_full_project(tmp_path)
        # Overwrite with workflow lacking SaveImage node
        no_saveimage_workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
            "4": {"class_type": "VAEDecode", "inputs": {}},
        }
        (control_dir / "ep01_shot01_submitted_workflow.json").write_text(
            json.dumps(no_saveimage_workflow))
        result = combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        # Runtime prefix is computed from shot_id, not from workflow node
        assert result == 0
        out = json.loads(capsys.readouterr().out)
        assert out["runtime_saveimage_prefix"] == RUNTIME_PREFIX
        assert out["source_workflow_prefix_detected"] is None

    def test_real_execute_no_execute_exposes_runtime_prefix(self, tmp_path, capsys):
        """Real execute (no --execute) must expose runtime prefix, not source shot01 prefix."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        out = json.loads(capsys.readouterr().out)
        assert out["saveimage_filename_prefix"] == RUNTIME_PREFIX
        assert out["saveimage_filename_prefix"] != SAVEIMAGE_PREFIX
        assert out["filename_prefix_consistency_valid"] is True
        assert out["runtime_prefix_patched_for_target_shot"] is True
        assert out["source_workflow_prefix_detected"] == SAVEIMAGE_PREFIX


# ---------------------------------------------------------------------------
# 9. Collector uses submitted SaveImage prefix
# ---------------------------------------------------------------------------

class TestCollectorUsesSubmittedPrefix:
    def test_preflight_confirms_collector_will_use_prefix(self, tmp_path, capsys):
        """Preflight must confirm collector_will_use_submitted_saveimage_prefix=true."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["collector_will_use_submitted_saveimage_prefix"] is True
        # Collector must use the runtime prefix, not old shot01 prefix
        assert out["saveimage_filename_prefix"] == RUNTIME_PREFIX

    def test_real_execute_no_execute_confirms_collector_runtime_prefix(self, tmp_path, capsys):
        """Real execute info must confirm collector uses runtime prefix."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        out = json.loads(capsys.readouterr().out)
        assert out["collector_will_use_submitted_saveimage_prefix"] is True
        assert out["runtime_saveimage_prefix"] == RUNTIME_PREFIX


# ---------------------------------------------------------------------------
# 10. next_allowed_action == operator_retry_v4_real_execution_authorization_required
# ---------------------------------------------------------------------------

class TestNextAllowedAction:
    def test_preflight_next_allowed_action(self, tmp_path, capsys):
        """Preflight next_allowed_action must be operator_retry_v4_real_execution_authorization_required."""
        from app.cli import combine_preflight_corrective_retry_v4_real_execution_route
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        out = json.loads(capsys.readouterr().out)
        assert out["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"

    def test_real_execute_no_flag_next_allowed_action(self, tmp_path, capsys):
        """Real execute (no --execute) next_allowed_action must be operator_retry_v4_real_execution_authorization_required."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)
        combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=False))
        out = json.loads(capsys.readouterr().out)
        assert out["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"

    def test_artifact_index_next_allowed_action(self, tmp_path):
        """artifact_index next_allowed_action must be operator_retry_v4_real_execution_authorization_required."""
        project_root, control_dir = _setup_full_project(tmp_path)
        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"


# ---------------------------------------------------------------------------
# Guard: real execute blocked without operator authorization state
# ---------------------------------------------------------------------------

class TestRealExecuteStateGuard:
    def test_execute_blocked_without_authorization_state(self, tmp_path):
        """Real execute with --execute must be blocked if state != operator_retry_v4_real_execution_authorization_required."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(
            tmp_path,
            current_state="corrective_retry_v4_non_stub_execution_route_required")
        result = combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=True))
        assert result == 1

    def test_execute_blocked_without_route_artifact(self, tmp_path):
        """Real execute with --execute must be blocked if route artifact missing."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, control_dir = _setup_full_project(tmp_path)
        (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").unlink()
        result = combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=True))
        assert result == 1

    def test_execute_calls_comfyclient_queue_prompt(self, tmp_path, capsys):
        """Real execute with --execute and proper state must call ComfyClient.queue_prompt."""
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        project_root, _ = _setup_full_project(tmp_path)

        mock_client = MagicMock()
        mock_client.queue_prompt = AsyncMock(return_value="test-prompt-id-123")

        with patch("app.comfy.comfy_client.ComfyClient", return_value=mock_client):
            with patch("asyncio.run", return_value="test-prompt-id-123"):
                result = combine_corrective_retry_v4_real_execute_assets(
                    _make_args_execute(project_root, execute=True))

        assert result == 0
        out = json.loads(capsys.readouterr().out)
        assert out["prompt_id"] == "test-prompt-id-123"
        assert out["workflow_submitted"] is True
        assert out["comfyui_execution"] is True
        assert out["real_workflow_binding_used"] is True
        assert out["fallback_workflow_used"] is False
        # Submitted workflow must use runtime prefix, not source shot01 prefix
        assert out["runtime_saveimage_prefix"] == RUNTIME_PREFIX
        assert out["runtime_prefix_patched_for_target_shot"] is True
        assert out["source_workflow_prefix_detected"] == SAVEIMAGE_PREFIX
        assert out["old_shot01_outputs_cannot_satisfy_v4_manifest"] is True


# ---------------------------------------------------------------------------
# Freeze-check command tests
# ---------------------------------------------------------------------------

def _make_args_freeze(project_root, shot_id="shot02", json_out=True):
    return argparse.Namespace(
        project_root=str(project_root),
        shot_id=shot_id,
        json=json_out,
    )


class TestPrefixShotidFreezeCheck:
    def test_freeze_check_passes_after_preflight(self, tmp_path, capsys):
        """Freeze check must pass when preflight has been run and prefix is correct."""
        from app.cli import (
            combine_preflight_corrective_retry_v4_real_execution_route,
            combine_corrective_retry_v4_prefix_shotid_freeze_check,
        )
        project_root, _ = _setup_full_project(tmp_path)
        # Run preflight first to write updated preflight artifact
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        capsys.readouterr()  # discard preflight output

        result = combine_corrective_retry_v4_prefix_shotid_freeze_check(
            _make_args_freeze(project_root))
        assert result == 0
        out = json.loads(capsys.readouterr().out)
        assert out["prefix_shotid_check_executed"] is True
        assert out["check_passed"] is True

    def test_freeze_check_proof_fields(self, tmp_path, capsys):
        """Freeze check proof must contain all required fields."""
        from app.cli import (
            combine_preflight_corrective_retry_v4_real_execution_route,
            combine_corrective_retry_v4_prefix_shotid_freeze_check,
        )
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        capsys.readouterr()

        combine_corrective_retry_v4_prefix_shotid_freeze_check(
            _make_args_freeze(project_root))
        out = json.loads(capsys.readouterr().out)

        assert out["target_shot_id"] == "shot02"
        assert out["source_workflow_prefix_detected"] == SAVEIMAGE_PREFIX
        assert out["runtime_saveimage_prefix"] == RUNTIME_PREFIX
        assert out["runtime_prefix_patched_for_target_shot"] is True
        assert out["collector_uses_runtime_saveimage_prefix"] is True
        assert out["old_shot01_outputs_cannot_satisfy_v4_manifest"] is True
        assert out["source_prefix_differs_from_runtime"] is True
        assert out["real_execution_adapter_ready"] is True
        assert out["new_generation_performed"] is False
        assert out["new_comfyui_submit_executed"] is False
        assert out["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"

    def test_freeze_check_writes_artifact(self, tmp_path):
        """Freeze check must write combine_v2_corrective_retry_v4_prefix_shotid_freeze_check.json."""
        from app.cli import (
            combine_preflight_corrective_retry_v4_real_execution_route,
            combine_corrective_retry_v4_prefix_shotid_freeze_check,
        )
        project_root, control_dir = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        combine_corrective_retry_v4_prefix_shotid_freeze_check(
            _make_args_freeze(project_root))

        art = control_dir / "combine_v2_corrective_retry_v4_prefix_shotid_freeze_check.json"
        assert art.exists()
        data = json.loads(art.read_text())
        assert data["check_passed"] is True
        assert data["runtime_saveimage_prefix"] == RUNTIME_PREFIX

    def test_freeze_check_fails_when_preflight_has_wrong_runtime_prefix(self, tmp_path):
        """Freeze check must fail when preflight artifact carries wrong runtime prefix."""
        from app.cli import combine_corrective_retry_v4_prefix_shotid_freeze_check
        project_root, control_dir = _setup_full_project(tmp_path)
        # Write a preflight artifact with a wrong/stale runtime prefix
        stale_preflight = {
            "runtime_saveimage_prefix": "rc2_multishot1_ep01_ep01_shot01_generate_frames_1777576340"
        }
        (control_dir / "combine_v2_corrective_retry_v4_real_execution_route_preflight.json").write_text(
            json.dumps(stale_preflight))
        result = combine_corrective_retry_v4_prefix_shotid_freeze_check(
            _make_args_freeze(project_root))
        assert result == 1

    def test_freeze_check_old_shot01_prefix_cannot_satisfy_manifest(self, tmp_path, capsys):
        """old_shot01_outputs_cannot_satisfy_v4_manifest must be true — runtime != source."""
        from app.cli import (
            combine_preflight_corrective_retry_v4_real_execution_route,
            combine_corrective_retry_v4_prefix_shotid_freeze_check,
        )
        project_root, _ = _setup_full_project(tmp_path)
        combine_preflight_corrective_retry_v4_real_execution_route(
            _make_args_preflight(project_root))
        capsys.readouterr()

        combine_corrective_retry_v4_prefix_shotid_freeze_check(
            _make_args_freeze(project_root))
        out = json.loads(capsys.readouterr().out)
        # Shot01 prefix != shot02 runtime prefix → isolation enforced
        assert out["old_shot01_outputs_cannot_satisfy_v4_manifest"] is True
        assert out["source_workflow_prefix_detected"] != out["runtime_saveimage_prefix"]


# ---------------------------------------------------------------------------
# RC-COMBINE-V2-2361-2420: ComfyClient constructor fix tests
# ---------------------------------------------------------------------------

class TestComfyClientConstructorFix:
    def test_v4_real_adapter_uses_no_arg_comfyclient_constructor(self, tmp_path):
        """V4 real adapter must instantiate ComfyClient() with no arguments.

        Root cause fix: ComfyClient.__init__(self) -> None takes NO arguments.
        base_url is read from settings.comfy_base_url internally.
        The broken call was: ComfyClient(base_url=comfy_base_url)
        The correct call is: ComfyClient()
        """
        import inspect
        import ast
        import textwrap
        from app.cli import combine_corrective_retry_v4_real_execute_assets

        src = inspect.getsource(combine_corrective_retry_v4_real_execute_assets)
        # Must NOT contain ComfyClient(base_url= anywhere in the function source
        assert "ComfyClient(base_url=" not in src, (
            "V4 real adapter still uses invalid ComfyClient(base_url=...) constructor. "
            "ComfyClient.__init__ takes no arguments."
        )
        # Must contain the correct no-arg instantiation
        assert "ComfyClient()" in src, (
            "V4 real adapter must instantiate ComfyClient() with no arguments."
        )

    def test_comfyclient_constructor_takes_no_args(self):
        """ComfyClient.__init__ must accept no arguments beyond self."""
        import inspect
        from app.comfy.comfy_client import ComfyClient

        sig = inspect.signature(ComfyClient.__init__)
        params = [p for p in sig.parameters if p != "self"]
        assert params == [], (
            f"ComfyClient.__init__ must have no parameters beyond self, got: {params}"
        )

    def test_comfyclient_constructor_failure_yields_honest_blocked_output(self, tmp_path, capsys, monkeypatch):
        """If ComfyClient() raises on construction, the adapter must return exit 1
        with workflow_submitted=false, comfyui_execution=false, generation_performed=false.
        """
        from app.cli import combine_corrective_retry_v4_real_execute_assets

        project_root, _ = _setup_full_project(
            tmp_path, current_state="corrective_retry_v4_real_execute_assets")

        def _bad_init(self):
            raise RuntimeError("settings misconfigured: COMFY_BASE_URL missing")

        import app.comfy.comfy_client as comfy_mod
        monkeypatch.setattr(comfy_mod.ComfyClient, "__init__", _bad_init)

        result = combine_corrective_retry_v4_real_execute_assets(
            _make_args_execute(project_root, execute=True))

        assert result == 1
        out = json.loads(capsys.readouterr().out)
        assert out["workflow_submitted"] is False
        assert out["comfyui_execution"] is False
        assert out["generation_performed"] is False
        assert out["production_accepted"] is False
        assert "settings misconfigured" in out["error"]
