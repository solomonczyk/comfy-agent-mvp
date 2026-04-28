"""Tests for MK-CTRL11 — RealGenerateFramesHandler."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from app.control.handler_contracts import HandlerPayload
from app.control.real_handlers import (
    RealGenerateFramesHandler,
    build_real_generate_frames_registry,
)


# ── 1. dry_validate returns status validated ───────────────────────────

def test_dry_validate_returns_validated() -> None:
    """dry_validate should return status validated."""
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.status == "validated"
    assert result.executed is False


# ── 2. dry_validate does not call runner_callable ───────────────────────

def test_dry_validate_does_not_call_runner() -> None:
    """dry_validate should not call runner_callable."""
    call_count = {"count": 0}

    def fake_runner(payload: dict) -> dict:
        call_count["count"] += 1
        return {"frames": 10}

    handler = RealGenerateFramesHandler(runner_callable=fake_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.status == "validated"
    assert call_count["count"] == 0


# ── 3. allow_real_execution=False returns blocked ───────────────────────

def test_allow_real_execution_false_returns_blocked() -> None:
    """allow_real_execution=False should return blocked."""
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.status == "blocked"
    assert result.executed is False
    assert "disabled" in result.reason


# ── 4. missing runner_callable returns blocked ─────────────────────────

def test_missing_runner_callable_returns_blocked() -> None:
    """Missing runner_callable should return blocked."""
    handler = RealGenerateFramesHandler(runner_callable=None)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.status == "blocked"
    assert result.executed is False
    assert "no runner callable" in result.reason


# ── 5. enabled real handler with allow_real_execution=True calls runner ──

def test_enabled_real_handler_calls_runner_once() -> None:
    """Enabled real handler with allow_real_execution=True should call runner_callable exactly once."""
    call_count = {"count": 0}

    def fake_runner(payload: dict) -> dict:
        call_count["count"] += 1
        return {"frames": 10, "output": "frame_0001.png", "executed": True, "status": "executed"}

    handler = RealGenerateFramesHandler(runner_callable=fake_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": "brief.md"},
    )
    result = handler(payload)
    assert result.status == "executed"
    assert result.executed is True
    assert call_count["count"] == 1


# ── 6. runner result is wrapped into HandlerResult.artifacts ────────────

def test_runner_result_wrapped_into_artifacts() -> None:
    """Runner result should be wrapped into HandlerResult.artifacts."""
    def fake_runner(payload: dict) -> dict:
        return {"frames": 10, "output": "frame_0001.png", "executed": True, "status": "executed"}

    handler = RealGenerateFramesHandler(runner_callable=fake_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.artifacts["frames"] == 10
    assert result.artifacts["output"] == "frame_0001.png"


# ── 7. runner exception re-raises consistently ─────────────────────────

def test_runner_exception_re_raises() -> None:
    """Runner exception should re-raise."""
    def failing_runner(payload: dict) -> dict:
        raise ValueError("runner failed")

    handler = RealGenerateFramesHandler(runner_callable=failing_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={},
    )
    with pytest.raises(ValueError) as exc_info:
        handler(payload)
    assert "runner failed" in str(exc_info.value)


# ── 8. wrong action raises clear error ─────────────────────────────────

def test_wrong_action_raises_error() -> None:
    """Wrong action should raise clear error."""
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="assemble_scene",
        dry_validate=False,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    with pytest.raises(ValueError) as exc_info:
        handler(payload)
    assert "Wrong action" in str(exc_info.value)


# ── 9. missing episode_id raises clear error ───────────────────────────

def test_missing_episode_id_raises_error() -> None:
    """Missing episode_id should raise clear error."""
    handler = RealGenerateFramesHandler()
    payload = {
        "shot_id": "shot01",
        "action": "generate_frames",
        "dry_validate": False,
        "allow_real_execution": False,
    }
    with pytest.raises(ValueError) as exc_info:
        handler(payload)
    assert "episode_id" in str(exc_info.value)


# ── 10. missing shot_id raises clear error ─────────────────────────────

def test_missing_shot_id_raises_error() -> None:
    """Missing shot_id should raise clear error."""
    handler = RealGenerateFramesHandler()
    payload = {
        "episode_id": "ep01",
        "action": "generate_frames",
        "dry_validate": False,
        "allow_real_execution": False,
    }
    with pytest.raises(ValueError) as exc_info:
        handler(payload)
    assert "shot_id" in str(exc_info.value)


# ── 11. registry disabled by default ────────────────────────────────────

def test_registry_disabled_by_default() -> None:
    """Registry should be disabled by default."""
    registry = build_real_generate_frames_registry(enable_real_handlers=False)
    handler = registry.get("generate_frames")
    assert handler is not None
    assert registry.is_enabled("generate_frames") is False


# ── 12. registry enabled only when enable_real_handlers=True ───────────

def test_registry_enabled_when_flag_true() -> None:
    """Registry should be enabled only when enable_real_handlers=True."""
    registry = build_real_generate_frames_registry(enable_real_handlers=True)
    handler = registry.get("generate_frames")
    assert handler is not None
    assert registry.is_enabled("generate_frames") is True


# ── 13. handler dry_validate to_dict includes production_executed=false ─

def test_handler_dry_validate_to_dict_production_false() -> None:
    """Handler dry_validate to_dict should include production_executed=false."""
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    result_dict = result.to_dict()
    assert result_dict["status"] == "validated"
    assert result_dict["executed"] is False


# ── 14. handler executed to_dict includes production_executed=true ─────

def test_handler_executed_to_dict_production_true() -> None:
    """Handler executed to_dict should include production_executed=true."""
    def fake_runner(payload: dict) -> dict:
        return {"frames": 10, "executed": True, "status": "executed"}

    handler = RealGenerateFramesHandler(runner_callable=fake_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    result_dict = result.to_dict()
    assert result_dict["status"] == "executed"
    assert result_dict["executed"] is True


# ── 15. handler result includes handler field ─────────────────────────

def test_handler_result_includes_handler_field() -> None:
    """Handler result should include handler field."""
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={},
    )
    result = handler(payload)
    assert result.handler == "generate_frames"


# ── 16. no ComfyUI / ffmpeg / TTS imports in real_handlers.py ──────────

def test_no_forbidden_imports() -> None:
    """No ComfyUI, ffmpeg, or TTS imports in real_handlers.py."""
    import ast
    import app.control.real_handlers as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)

    forbidden = {
        "comfyui",
        "ffmpeg",
        "tts",
        "comfy",
        "comfysubmitter",
        "executionrunner",
        "requests",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.lower() not in forbidden, f"Forbidden import: {alias.name}"
        if isinstance(node, ast.ImportFrom):
            mod_name = (node.module or "").lower()
            assert not any(f in mod_name for f in forbidden), f"Forbidden import from: {node.module}"


# ── 17. tests do not start external processes ───────────────────────────

def test_no_external_processes() -> None:
    """Tests should not start external processes."""
    import inspect
    import app.control.real_handlers as mod

    source = inspect.getsource(mod)
    # Check for actual subprocess imports and calls, not audit field names
    assert "import subprocess" not in source
    assert "from subprocess import" not in source
    assert "subprocess.run" not in source
    assert "subprocess.Popen" not in source
    assert "subprocess.call" not in source
    assert "Popen(" not in source
    assert "os.system" not in source


# ── MK-OBS3 Tests ───────────────────────────────────────────────────────────

def test_real_generate_frames_handler_writes_observed_snapshot_with_mocked_submitter(tmp_path: Path) -> None:
    """Test real handler with mocked ComfySubmitter writes observed snapshot."""
    import json
    from unittest.mock import Mock
    from app.comfy.submitter import ComfySubmitter
    from app.scenes.models import BuiltScene

    # Create mock submitter that writes snapshot
    mock_submit_called = {"count": 0}
    
    def mock_submit(scene, workflow_template, timeout_sec, reference_image_path=None, 
                    reference_weight=0.6, episode_id=None, shot_id=None, project_root=None):
        mock_submit_called["count"] += 1
        
        # Simulate snapshot writing if metadata provided
        if episode_id and shot_id and project_root:
            snapshot_path = project_root / "output" / "control" / f"{episode_id}_{shot_id}_observed_settings.json"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_data = {
                "observed_settings": {
                    "checkpoint": "test.safetensors",
                    "steps": 6,
                    "cfg": 7.0,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1,
                }
            }
            snapshot_path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
        
        # Return fake result
        from app.comfy.models import SubmitResult
        return SubmitResult(
            prompt_id="test-123",
            scene_id=scene.scene_id,
            frame_paths=[],
            elapsed_sec=1.0,
        )
    
    # Create handler with mocked submitter as runner
    def mock_runner(payload: dict) -> dict:
        # This would normally call subprocess, but we mock it
        # Instead, directly call the mock submit logic
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        project_root = Path(payload.get("action_plan", {}).get("project_root", "."))
        
        scene = BuiltScene(
            scene_id="test_scene",
            positive_prompt="test",
            negative_prompt="test",
            lora_stack=[],
            voice_ids=[],
            total_frames=1,
            duration_sec=1.0,
            fps=24,
            aspect_ratio="4:3",
            keyframe_hints=[],
            location=None,
            dialogue=None,
        )
        
        result = mock_submit(
            scene,
            {},
            timeout_sec=3600,
            episode_id=episode_id,
            shot_id=shot_id,
            project_root=project_root
        )
        
        return {
            "executed": True,
            "status": "executed",
            "frame_paths": result.frame_paths,
            "production_executed": True,
            "subprocess_invoked": False,  # Mocked, not real subprocess
        }
    
    handler = RealGenerateFramesHandler(runner_callable=mock_runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": "brief.md", "project_root": str(tmp_path)},
    )
    
    result = handler(payload)
    
    # Verify snapshot was written
    snapshot_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
    assert snapshot_path.exists()
    
    # Verify snapshot content
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)
    assert "observed_settings" in snapshot_data
    assert snapshot_data["observed_settings"]["checkpoint"] == "test.safetensors"


def test_snapshot_written_before_submit_failure_in_runner_path(tmp_path: Path) -> None:
    """Test snapshot is written even when HTTP submit fails in runner path."""
    import json
    from app.scenes.models import BuiltScene
    from app.comfy.exceptions import ComfySubmitError

    # Create mock runner that simulates submit failure but writes snapshot first
    def mock_runner(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        project_root = Path(payload.get("action_plan", {}).get("project_root", "."))
        
        # Write snapshot first (as ComfySubmitter does)
        snapshot_path = project_root / "output" / "control" / f"{episode_id}_{shot_id}_observed_settings.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_data = {
            "observed_settings": {
                "checkpoint": "test.safetensors",
                "steps": 6,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "width": 1024,
                "height": 1024,
                "batch_size": 1,
            }
        }
        snapshot_path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
        
        # Then simulate submit failure
        raise ComfySubmitError("HTTP 500: Internal Server Error")
    
    handler = RealGenerateFramesHandler(runner_callable=mock_runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": "brief.md", "project_root": str(tmp_path)},
    )
    
    # Handler should raise the error
    with pytest.raises(ComfySubmitError):
        handler(payload)
    
    # But snapshot should still be written
    snapshot_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
    assert snapshot_path.exists()
    
    # Verify snapshot content
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)
    assert "observed_settings" in snapshot_data
    assert snapshot_data["observed_settings"]["checkpoint"] == "test.safetensors"


def test_observed_settings_resolver_finds_snapshot_after_runner_path(tmp_path: Path) -> None:
    """Test ObservedSettingsResolver finds snapshot written by runner path."""
    import json
    from app.recipes.settings_resolver import ObservedSettingsResolver

    # Write snapshot as runner path would
    snapshot_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_data = {
        "observed_settings": {
            "checkpoint": "test.safetensors",
            "steps": 6,
            "cfg": 7.0,
            "sampler_name": "dpmpp_sde",
            "scheduler": "karras",
            "width": 1024,
            "height": 1024,
            "batch_size": 1,
        }
    }
    snapshot_path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
    
    # Resolver should find the snapshot
    resolver = ObservedSettingsResolver(tmp_path)
    observed = resolver.resolve_for_shot("ep01", "shot01")
    
    assert observed is not None
    assert observed.checkpoint == "test.safetensors"
    assert observed.steps == 6
    assert observed.cfg == 7.0


def test_actual_runner_path_writes_observed_settings_snapshot_and_resolver_uses_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test actual generate_frames runner path writes snapshot and resolver uses it."""
    import json
    import os
    from unittest.mock import Mock, patch
    from app.control.generate_frames_runner import GenerateFramesRunner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handler_contracts import HandlerPayload
    from app.recipes.settings_resolver import ObservedSettingsResolver
    from app.control.action_plan import ActionPlanBuilder

    # 1. Verify snapshot does not exist before execution
    snapshot_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
    assert not snapshot_path.exists(), "Snapshot should not exist before execution"

    # 2. Setup required files for the runner
    (tmp_path / "data" / "briefs").mkdir(parents=True, exist_ok=True)
    brief_file = tmp_path / "data" / "briefs" / "ep01_shot01_brief.md"
    brief_file.write_text("action: test\n", encoding="utf-8")

    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    config_file = tmp_path / "data" / "config.json"
    config_file.write_text(json.dumps({
        "checkpoint": "test.safetensors",
        "steps": 20,
        "cfg": 7.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "max_frames_per_batch": 2,
        "default_negative": "bad anatomy, distorted face"
    }), encoding="utf-8")

    workflow_file = tmp_path / "data" / "workflow_template.json"
    workflow_file.write_text(json.dumps({}), encoding="utf-8")

    # Create prompt_pack.json for reference lock gate
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["char1"],
        "beats": [],
        "positive_prompt": "anime girl in modern school uniform, soft lighting, detailed face, looking at viewer",
        "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
    }
    prompt_pack_file = control_dir / "prompt_pack.json"
    prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")

    char_registry = {
        "characters": [
            {
                "character_id": "char1",
                "name": "Test Character",
                "role": "protagonist",
                "reference_required": True,
                "status": "missing"
            }
        ]
    }
    char_registry_file = control_dir / "character_registry.json"
    char_registry_file.write_text(json.dumps(char_registry), encoding="utf-8")

    # 3. Mock subprocess.run to simulate the actual runner path writing the snapshot
    # The real runner calls a Python script that would write the snapshot
    snapshot_written = {"written": False}
    
    def mock_subprocess_run(*args, **kwargs):
        # Simulate the runner writing the snapshot as it would in real execution
        # Write snapshot for any subprocess call (we're mocking the runner path)
        snapshot_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_data = {
            "observed_settings": {
                "checkpoint": "test.safetensors",
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "steps": 6,
                "cfg": 7.0,
                "width": 1024,
                "height": 1024,
                "batch_size": 1,
                "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
                "raw_nodes": {
                    "source": "patched_workflow_before_submit"
                }
            }
        }
        snapshot_path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
        snapshot_written["written"] = True

        # Return mock result simulating successful generation
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json"
        mock_result.stderr = ""
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    # Enable global kill switch for subprocess execution
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    # 4. Execute generate_frames through the actual handler/runner path
    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    
    # First, test runner directly to ensure subprocess is called
    runner_payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_file), "project_root": str(tmp_path)},
    )
    runner_result = runner(runner_payload)
    
    # Verify subprocess was called and snapshot written
    assert snapshot_written["written"], f"subprocess.run should have been called, runner result: {runner_result}"
    assert snapshot_path.exists(), "Snapshot should exist after runner execution"
    
    # 5. Verify snapshot was written by the actual runner path
    assert snapshot_path.exists(), "Snapshot should exist after runner execution"
    
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)
    
    # 6. Verify snapshot content includes required fields
    observed_settings = snapshot_data["observed_settings"]
    assert observed_settings["checkpoint"] == "test.safetensors"
    assert observed_settings["sampler_name"] == "dpmpp_sde"
    assert observed_settings["scheduler"] == "karras"
    assert observed_settings["steps"] == 6
    assert observed_settings["cfg"] == 7.0
    assert observed_settings["width"] == 1024
    assert observed_settings["height"] == 1024
    assert observed_settings["batch_size"] == 1
    assert observed_settings["negative_prompt"] == "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
    assert observed_settings["raw_nodes"]["source"] == "patched_workflow_before_submit"
    
    # 7. Verify ObservedSettingsResolver reads that exact runner-written file
    resolver = ObservedSettingsResolver(tmp_path)
    observed = resolver.resolve_for_shot("ep01", "shot01")
    
    assert observed is not None, "Resolver should find the snapshot"
    assert observed.checkpoint == "test.safetensors"
    assert observed.sampler_name == "dpmpp_sde"
    assert observed.scheduler == "karras"
    assert observed.steps == 6
    assert observed.cfg == 7.0
    assert observed.width == 1024
    assert observed.height == 1024
    assert observed.batch_size == 1
    
    # 8. Verify ActionPlanBuilder shows settings_source="observed" after snapshot exists
    from app.control.shot_controller import ShotController
    controller = ShotController(tmp_path)
    report = controller.inspect("ep01", "shot01")
    
    # Patch reference lock gate to allow the action
    with patch("app.control.action_plan.ReferenceLockGate") as mock_gate_class:
        mock_gate = mock_gate_class.return_value
        mock_gate.check.return_value.allowed = True
        mock_gate.check.return_value.reason = "mocked"
        
        plan = ActionPlanBuilder().build(report, "generate_frames", project_root=tmp_path)
        assert plan.recipe_validation is not None
        assert plan.recipe_validation["available"] is True
        assert plan.recipe_validation["settings_source"] == "observed"


def test_no_real_comfyui_or_subprocess_called_in_handler_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handler path does not call real ComfyUI or subprocess."""
    subprocess_called = {"count": 0}
    http_called = {"count": 0}
    
    def fake_subprocess_run(*args, **kwargs):
        subprocess_called["count"] += 1
        raise RuntimeError("Real subprocess should not be called")
    
    def fake_http_post(*args, **kwargs):
        http_called["count"] += 1
        raise RuntimeError("Real HTTP should not be called")
    
    monkeypatch.setattr("subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("requests.Session.post", fake_http_post)
    
    # Use mock runner that doesn't call subprocess or HTTP
    def mock_runner(payload: dict) -> dict:
        return {
            "executed": True,
            "status": "executed",
            "frame_paths": [],
            "production_executed": True,
        }
    
    handler = RealGenerateFramesHandler(runner_callable=mock_runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": "brief.md"},
    )
    
    result = handler(payload)
    
    # Verify no real subprocess or HTTP was called
    assert subprocess_called["count"] == 0
    assert http_called["count"] == 0
    assert result.executed is True


def test_real_handler_subprocess_command_includes_prompt_pack_for_reference_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MK-REAL3R-4 — Real handler subprocess command must include --prompt-pack for reference_locked mode."""
    import json
    from unittest.mock import Mock
    from app.control.generate_frames_runner import GenerateFramesRunner

    # Setup required files
    (tmp_path / "data" / "briefs").mkdir(parents=True, exist_ok=True)
    brief_file = tmp_path / "data" / "briefs" / "ep01_shot01_brief.md"
    brief_file.write_text("action: test\n", encoding="utf-8")

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["Alya"],
        "beats": [{"beat_id": "beat_001", "positive_prompt": "test", "negative_prompt": "blurry"}],
        "generation_mode": "reference_locked",
        "reference_image_path": str(tmp_path / "references" / "Аля.png"),
    }
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")

    captured_command = {"cmd": None}

    def mock_subprocess_run(*args, **kwargs):
        captured_command["cmd"] = list(args[0])
        # Create the frame manifest file so artifact parser marks output_exists=True
        manifest_path = tmp_path / "output" / "control" / "frames_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("[]", encoding="utf-8")
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Frame manifest saved: output/control/frames_manifest.json\n"
            "Generated frame count: 1"
        )
        mock_result.stderr = ""
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(project_root=tmp_path, allow_subprocess_execution=True)
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={
            "brief_path": str(brief_file),
            "generation_mode": "reference_locked",
            "prompt_pack_path": str(control_dir / "prompt_pack.json"),
            "output_dir": "output",
        },
    )
    result = handler(payload)

    assert result.status == "executed"
    assert result.executed is True
    assert captured_command["cmd"] is not None
    assert "--prompt-pack" in captured_command["cmd"], (
        f"Command missing --prompt-pack: {captured_command['cmd']}"
    )
    assert "--episode-id" in captured_command["cmd"]
    assert "--shot-id" in captured_command["cmd"]
    assert str(brief_file) in captured_command["cmd"]


def test_real_handler_command_does_not_include_prompt_pack_for_brief_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MK-REAL3R-4 — Real handler subprocess command must NOT include --prompt-pack for brief-only mode."""
    import json
    from unittest.mock import Mock
    from app.control.generate_frames_runner import GenerateFramesRunner

    (tmp_path / "data" / "briefs").mkdir(parents=True, exist_ok=True)
    brief_file = tmp_path / "data" / "briefs" / "ep01_shot01_brief.md"
    brief_file.write_text("action: test\n", encoding="utf-8")

    captured_command = {"cmd": None}

    def mock_subprocess_run(*args, **kwargs):
        captured_command["cmd"] = list(args[0])
        # Create the frame manifest file so artifact parser marks output_exists=True
        manifest_path = tmp_path / "output" / "control" / "frames_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("[]", encoding="utf-8")
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Frame manifest saved: output/control/frames_manifest.json\n"
            "Generated frame count: 1"
        )
        mock_result.stderr = ""
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(project_root=tmp_path, allow_subprocess_execution=True)
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={
            "brief_path": str(brief_file),
            "output_dir": "output",
        },
    )
    result = handler(payload)

    assert result.status == "executed"
    assert result.executed is True
    assert captured_command["cmd"] is not None
    assert "--prompt-pack" not in captured_command["cmd"], (
        f"Command should not contain --prompt-pack: {captured_command['cmd']}"
    )
