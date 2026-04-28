"""Tests for MK-CTRL12 — GenerateFramesRunner."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.control.generate_frames_runner import GenerateFramesRunner
from app.control.handler_contracts import HandlerPayload


# ── 1. validate_payload accepts valid HandlerPayload ────────────────────

def test_validate_payload_accepts_valid_payload(tmp_path: Path) -> None:
    """validate_payload should accept valid HandlerPayload."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner.validate_payload(payload)
    assert result["valid"] is True
    assert result["reason"] == "Payload is valid"


# ── 2. validate_payload rejects missing episode_id ───────────────────────

def test_validate_payload_rejects_missing_episode_id() -> None:
    """validate_payload should reject missing episode_id."""
    runner = GenerateFramesRunner()
    payload = {
        "shot_id": "shot01",
        "action": "generate_frames",
        "state_report": {},
        "action_plan": {"brief_path": "brief.md"},
    }
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "episode_id" in result["reason"]


# ── 3. validate_payload rejects missing shot_id ─────────────────────────

def test_validate_payload_rejects_missing_shot_id() -> None:
    """validate_payload should reject missing shot_id."""
    runner = GenerateFramesRunner()
    payload = {
        "episode_id": "ep01",
        "action": "generate_frames",
        "state_report": {},
        "action_plan": {"brief_path": "brief.md"},
    }
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "shot_id" in result["reason"]


# ── 4. validate_payload rejects wrong action ───────────────────────────

def test_validate_payload_rejects_wrong_action() -> None:
    """validate_payload should reject wrong action."""
    runner = GenerateFramesRunner()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="assemble_scene",
        state_report={},
        action_plan={"brief_path": "brief.md"},
    )
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "Wrong action" in result["reason"]


# ── 5. validate_payload rejects missing action_plan ─────────────────────

def test_validate_payload_rejects_missing_action_plan() -> None:
    """validate_payload should reject missing action_plan."""
    runner = GenerateFramesRunner()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan=None,
    )
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "action_plan" in result["reason"]


# ── 6. validate_payload rejects missing brief_path and command_preview ──

def test_validate_payload_rejects_missing_brief_and_command() -> None:
    """validate_payload should reject missing brief_path and command_preview."""
    runner = GenerateFramesRunner()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={},  # Empty dict, no brief_path or command_preview
    )
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "brief_path or command_preview" in result["reason"]


# ── 7. validate_payload rejects nonexistent brief_path ───────────────────

def test_validate_payload_rejects_nonexistent_brief() -> None:
    """validate_payload should reject nonexistent brief_path."""
    runner = GenerateFramesRunner()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "nonexistent/brief.md"},
    )
    result = runner.validate_payload(payload)
    assert result["valid"] is False
    assert "does not exist" in result["reason"]


# ── 8. build_command returns list[str] ─────────────────────────────────

def test_build_command_returns_list(tmp_path: Path) -> None:
    """build_command should return list[str]."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    assert isinstance(command, list)
    assert all(isinstance(arg, str) for arg in command)


# ── 9. build_command includes python executable ───────────────────────

def test_build_command_includes_python_executable(tmp_path: Path) -> None:
    """build_command should include python executable."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(python_executable="python3", project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    assert command[0] == "python3"


# ── 10. build_command includes "-m app run" ───────────────────────────

def test_build_command_includes_module_run(tmp_path: Path) -> None:
    """build_command should include '-m app run'."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    assert "-m" in command
    assert "app" in command
    # MK-CTRL20 — Now uses "generate-frames" subcommand instead of "run"
    assert "generate-frames" in command


# ── 11. build_command includes --brief path ───────────────────────────

def test_build_command_includes_brief_path(tmp_path: Path) -> None:
    """build_command should include --brief path."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    assert "--brief" in command
    brief_index = command.index("--brief")
    assert "brief.md" in command[brief_index + 1]


# ── 12. build_command includes --output dir ───────────────────────────

def test_build_command_includes_output_dir(tmp_path: Path) -> None:
    """build_command should include --output dir."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path), "output_dir": "output/custom"},
    )
    command = runner.build_command(payload)
    assert "--output" in command
    output_index = command.index("--output")
    # After MK-CTRL30 fix, output_dir is resolved to absolute path relative to project_root
    expected_output = str(tmp_path / "output" / "custom")
    assert expected_output in command[output_index + 1]


# ── 13. __call__ default does not execute subprocess ─────────────────

def test_call_default_no_subprocess(tmp_path: Path) -> None:
    """__call__ default should not execute subprocess."""
    # Create a brief file
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner(payload)
    assert result["status"] == "command_ready"
    assert result["executed"] is False


# ── 14. __call__ returns status command_ready ─────────────────────────

def test_call_returns_command_ready(tmp_path: Path) -> None:
    """__call__ should return status command_ready."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner(payload)
    assert result["status"] == "command_ready"


# ── 15. __call__ returns executed=false by default ────────────────────

def test_call_returns_executed_false_default(tmp_path: Path) -> None:
    """__call__ should return executed=false by default."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner(payload)
    assert result["executed"] is False


# ── 16. subprocess only when allowed ───────────────────────────────────

def test_subprocess_only_when_allowed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Subprocess should only run when allow_subprocess_execution=True."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    run_called = {"count": 0}

    def fake_run(*args, **kwargs):
        run_called["count"] += 1
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("subprocess.run", fake_run)

    # Enable global guard for test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    # Test with allow_subprocess_execution=False
    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=False,
    )
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner(payload)
    assert run_called["count"] == 0
    assert result["executed"] is False

    # Test with allow_subprocess_execution=True
    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    result = runner(payload)
    assert run_called["count"] == 1
    assert result["executed"] is True


# ── 17. subprocess result includes returncode/stdout/stderr ────────────

def test_subprocess_result_includes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Subprocess result should include returncode, stdout, stderr."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return type("Result", (), {
            "returncode": 0,
            "stdout": "output text",
            "stderr": "error text",
        })()

    monkeypatch.setattr("subprocess.run", fake_run)

    # Enable global guard for test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = runner(payload)
    assert result["returncode"] == 0
    assert result["stdout"] == "output text"
    assert result["stderr"] == "error text"


# ── 18. no shell=True anywhere ─────────────────────────────────────────

def test_no_shell_true() -> None:
    """No shell=True should be used anywhere in the code."""
    import inspect
    import app.control.generate_frames_runner as mod

    source = inspect.getsource(mod)
    # Check actual code, not docstrings
    lines = source.split('\n')
    code_lines = []
    in_docstring = False
    for line in lines:
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            in_docstring = not in_docstring
            continue
        if not in_docstring and not stripped.startswith('#'):
            code_lines.append(line)
    code = '\n'.join(code_lines)
    assert "shell=True" not in code


# ── 19. runner can be injected into RealGenerateFramesHandler and dry_validate still does not run it ─

def test_runner_injected_dry_validate_no_run(tmp_path: Path) -> None:
    """Runner injected into RealGenerateFramesHandler should not run in dry_validate mode."""
    from app.control.real_handlers import RealGenerateFramesHandler

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    runner = GenerateFramesRunner(project_root=tmp_path)
    call_count = {"count": 0}

    # Wrap runner to count calls
    def counting_runner(payload):
        call_count["count"] += 1
        return runner(payload)

    handler = RealGenerateFramesHandler(runner_callable=counting_runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    assert result.status == "validated"
    assert result.executed is False
    assert call_count["count"] == 0


# ── 20. runner can be injected into RealGenerateFramesHandler with allow_real_execution=True and fake subprocess monkeypatch records executed=true ─

def test_runner_injected_real_execution_fake_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Runner injected with allow_real_execution=True and fake subprocess should record executed=true."""
    from app.control.real_handlers import RealGenerateFramesHandler

    # Create fake file for artifact acceptance
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return type("Result", (), {
            "returncode": 0,
            "stdout": "Episode saved: output\\episodes\\test.mp4",
            "stderr": "",
        })()

    monkeypatch.setattr("subprocess.run", fake_run)

    # Enable global guard for test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    handler = RealGenerateFramesHandler(runner_callable=runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    assert result.status == "executed"
    assert result.executed is True


# ── MK-CTRL17 Tests ───────────────────────────────────────────────────────


# ── Test 4 — successful subprocess stores artifact paths ──────────────────

def test_subprocess_stores_artifact_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful subprocess should store artifact paths in result."""
    from app.control.real_handlers import RealGenerateFramesHandler

    # Create fake files for artifact acceptance
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    manifest_dir = tmp_path / "output"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    fake_manifest = manifest_dir / "manifest.json"
    fake_manifest.write_text('{"test": "data"}', encoding="utf-8")

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return type("Result", (), {
            "returncode": 0,
            "stdout": "Manifest saved: output\\manifest.json\nEpisode saved: output\\episodes\\test.mp4",
            "stderr": "",
        })()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    handler = RealGenerateFramesHandler(runner_callable=runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    
    assert result.status == "executed"
    assert result.executed is True
    assert result.artifacts["returncode"] == 0
    assert result.artifacts["subprocess_invoked"] is True
    assert result.artifacts["production_executed"] is True
    assert result.artifacts["episode_output_path"] is not None
    assert "test.mp4" in result.artifacts["episode_output_path"]
    assert result.artifacts["manifest_path"] is not None
    assert "manifest.json" in result.artifacts["manifest_path"]
    # MK-CTRL18 — artifact acceptance
    assert result.artifacts["artifact_status"] == "accepted"
    assert result.artifacts["artifact_accepted"] is True


# ── Test 5 — file existence and size ───────────────────────────────────────

def test_file_existence_and_size_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """File existence and size should be captured when output file exists."""
    from app.control.real_handlers import RealGenerateFramesHandler

    # Create a fake mp4 file
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return type("Result", (), {
            "returncode": 0,
            "stdout": "Episode saved: output\\episodes\\test.mp4",
            "stderr": "",
        })()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    handler = RealGenerateFramesHandler(runner_callable=runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    
    assert result.artifacts["output_exists"] is True
    assert result.artifacts["output_size_bytes"] == 1800


# ── Test 6 — missing output file is not fatal ─────────────────────────────

def test_missing_output_file_not_fatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing output file should not be fatal, returncode still captured."""
    from app.control.real_handlers import RealGenerateFramesHandler

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return type("Result", (), {
            "returncode": 0,
            "stdout": "Episode saved: output\\episodes\\nonexistent.mp4",
            "stderr": "",
        })()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    handler = RealGenerateFramesHandler(runner_callable=runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    
    assert result.artifacts["output_exists"] is False
    assert result.artifacts["output_size_bytes"] is None
    assert result.artifacts["returncode"] == 0


# ── Test 7 — dry flow unaffected ──────────────────────────────────────────

def test_dry_flow_unaffected(tmp_path: Path) -> None:
    """Dry flow should still work without requiring episode_output_path."""
    from app.control.real_handlers import RealGenerateFramesHandler

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    runner = GenerateFramesRunner(project_root=tmp_path)
    handler = RealGenerateFramesHandler(runner_callable=runner)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=True,
        allow_real_execution=False,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    
    assert result.status == "validated"
    assert result.executed is False
    assert result.artifacts.get("production_executed") is False or result.artifacts.get("production_executed") is None


# ── Test 8 — blocked kill switch unaffected ───────────────────────────────

def test_blocked_kill_switch_unaffected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Blocked kill switch should still prevent subprocess execution."""
    from app.control.real_handlers import RealGenerateFramesHandler

    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")

    # Disable global execution guard
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "0")

    runner = GenerateFramesRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        dry_validate=False,
        allow_real_execution=True,
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    result = handler(payload)
    
    assert result.status == "blocked"
    assert result.artifacts.get("subprocess_invoked") is False
    assert result.artifacts.get("production_executed") is False


# ── MK-OBS3 Tests ───────────────────────────────────────────────────────────

def test_generate_frames_runner_passes_snapshot_metadata(tmp_path: Path) -> None:
    """Test that runner passes episode_id, shot_id, project_root in command."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    
    # Verify episode_id and shot_id are in command
    assert "--episode-id" in command
    episode_idx = command.index("--episode-id")
    assert command[episode_idx + 1] == "ep01"
    assert "--shot-id" in command
    shot_idx = command.index("--shot-id")
    assert command[shot_idx + 1] == "shot01"


# ── MK-REAL3R-4 Tests ───────────────────────────────────────────────────────

def test_build_command_includes_prompt_pack_for_reference_locked_mode(tmp_path: Path) -> None:
    """build_command should include --prompt-pack when generation_mode is reference_locked."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={
            "brief_path": str(brief_path),
            "generation_mode": "reference_locked",
            "prompt_pack_path": str(tmp_path / "output" / "control" / "prompt_pack.json"),
        },
    )
    command = runner.build_command(payload)
    assert "--prompt-pack" in command


def test_build_command_includes_prompt_pack_when_prompt_pack_path_set(tmp_path: Path) -> None:
    """build_command should include --prompt-pack when prompt_pack_path is present."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={
            "brief_path": str(brief_path),
            "prompt_pack_path": str(tmp_path / "output" / "control" / "prompt_pack.json"),
        },
    )
    command = runner.build_command(payload)
    assert "--prompt-pack" in command


def test_build_command_does_not_include_prompt_pack_for_brief_mode(tmp_path: Path) -> None:
    """build_command should NOT include --prompt-pack for brief-only mode."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path)},
    )
    command = runner.build_command(payload)
    assert "--prompt-pack" not in command
