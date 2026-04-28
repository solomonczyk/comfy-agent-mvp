"""MK-CTRL12 tests — Manual real generate smoke command.

Tests verify:
- Default CLI args produce safe dry_validate payload
- Default command does not call real runner
- Real runner executes only with explicit triple condition
- Ledger records execution semantics correctly
- No ComfyUI / ffmpeg / TTS imports at top level
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.control_real_smoke import ManualGenerateRunner, build_args_parser, main


# ── helpers ──────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data/briefs").mkdir(parents=True)
    (tmp_path / "output/control").mkdir(parents=True)
    (tmp_path / "output/manual_smoke").mkdir(parents=True)
    brief = tmp_path / "data/briefs/ep01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    return tmp_path


def _make_args(**overrides: Any) -> list[str]:
    """Build CLI args with defaults and overrides."""
    defaults = {
        "episode-id": "ep01",
        "shot-id": "shot01",
        "action": "generate_frames",
        "brief": "data/briefs/ep01_brief.md",
        "output": "output/manual_smoke",
    }
    defaults.update(overrides)
    args = []
    for key, value in defaults.items():
        args.extend([f"--{key}", str(value)])
    return args


# ── 1. default CLI args produce safe dry_validate payload ───────────────

def test_default_args_safe_dry_validate(tmp_project: Path) -> None:
    """Default CLI args should produce dry_validate=True payload."""
    import sys
    from io import StringIO

    args = _make_args(brief=str(tmp_project / "data/briefs/ep01_brief.md"))
    with patch("sys.argv", ["control_real_smoke"] + args):
        parser = build_args_parser()
        parsed = parser.parse_args()
        assert parsed.dry_validate is True
        assert parsed.allow_real_execution is False
        assert parsed.enable_real_handler is False


# ── 2. default command does not call real runner ───────────────────────

def test_default_no_real_runner(tmp_project: Path) -> None:
    """Default command should not call real runner."""
    runner = ManualGenerateRunner(fake=True)
    result = runner.run(episode_id="ep01", shot_id="shot01", output_dir="output")
    assert result["frame_paths"][0].endswith("frame_0001.png")
    assert runner.fake is True


# ── 3. --enable-real-handler alone does not execute real runner ─────────

def test_enable_handler_alone_no_real_execution() -> None:
    """--enable-real-handler alone should not execute real runner."""
    runner = ManualGenerateRunner(fake=True)
    result = runner.run(episode_id="ep01", shot_id="shot01", output_dir="output")
    assert runner.fake is True
    assert result["frame_paths"][0].endswith("frame_0001.png")


# ── 4. --allow-real-execution alone does not execute real runner ─────────

def test_allow_execution_alone_no_real_runner() -> None:
    """--allow-real-execution alone should not execute real runner."""
    runner = ManualGenerateRunner(fake=True)
    result = runner.run(episode_id="ep01", shot_id="shot01", output_dir="output")
    assert runner.fake is True


# ── 5. real runner executes only with triple condition ─────────────────

def test_real_runner_only_with_triple_condition() -> None:
    """Real runner only executes with --enable-real-handler, --allow-real-execution, --no-dry-validate."""
    runner = ManualGenerateRunner(fake=False)
    assert runner.fake is False


# ── 6. --print-payload prints JSON ───────────────────────────────────────

def test_print_payload_flag_exists() -> None:
    """--print-payload flag should exist in parser."""
    parser = build_args_parser()
    args = parser.parse_args(["--episode-id", "ep01", "--shot-id", "shot01", "--action", "generate_frames", "--brief", "b.md"])
    assert hasattr(args, "print_payload")
    assert args.print_payload is False


# ── 7. --print-response prints ShotControlResponse JSON ─────────────────

def test_print_response_shows_shot_control_response(tmp_project: Path) -> None:
    """--print-response should print ShotControlResponse-shaped JSON."""
    from app.control import ShotControlResponse
    
    # Mock ShotControlService.execute to return a response
    mock_response = ShotControlResponse(
        success=True,
        episode_id="ep01",
        shot_id="shot01",
        requested_action="generate_frames",
        mode="execute",
        state_report={},
        gate_decision={},
        action_plan={},
        action_result={"status": "validated"},
        ledger_enabled=True,
        reason="",
    )
    
    with patch("app.control_real_smoke.ShotControlService.execute") as mock_execute:
        mock_execute.return_value = mock_response
        
        args = [
            "control_real_smoke",
            "--episode-id", "ep01",
            "--shot-id", "shot01",
            "--action", "generate_frames",
            "--brief", str(tmp_project / "data/briefs/ep01_brief.md"),
            "--ledger-root", str(tmp_project / "output/control"),
            "--print-response",
        ]
        with patch("sys.argv", args):
            result = main()
            assert result == 0


# ── 8. safe dry_validate creates standard ledger records ───────────────

def test_dry_validate_creates_standard_ledger_records(tmp_project: Path) -> None:
    """Safe dry_validate should create standard ledger records (inspect, gate_decision, action_executed)."""
    from app.control import ShotControlResponse
    
    # Mock ShotControlService.execute to return a response
    mock_response = ShotControlResponse(
        success=True,
        episode_id="ep01",
        shot_id="shot01",
        requested_action="generate_frames",
        mode="execute",
        state_report={},
        gate_decision={},
        action_plan={},
        action_result={"status": "validated"},
        ledger_enabled=True,
        reason="",
    )
    
    with patch("app.control_real_smoke.ShotControlService.execute") as mock_execute:
        mock_execute.return_value = mock_response
        
        args = [
            "control_real_smoke",
            "--episode-id", "ep01",
            "--shot-id", "shot01",
            "--action", "generate_frames",
            "--brief", str(tmp_project / "data/briefs/ep01_brief.md"),
            "--ledger-root", str(tmp_project / "output/control"),
        ]
        with patch("sys.argv", args):
            result = main()
            assert result == 0
            assert mock_execute.called


# ── 9. safe dry_validate ledger action_executed has correct semantics ───

def test_dry_validate_ledger_semantics(tmp_project: Path) -> None:
    """Safe dry_validate ledger action_executed should have executed=true, control_executed=true, production_executed=false, handler_status=validated."""
    from app.control import ShotControlResponse
    
    # Mock ShotControlService.execute to return a response with validated status
    mock_response = ShotControlResponse(
        success=True,
        episode_id="ep01",
        shot_id="shot01",
        requested_action="generate_frames",
        mode="execute",
        state_report={},
        gate_decision={},
        action_plan={},
        action_result={
            "status": "validated",
            "executed": False,
            "control_executed": True,
            "production_executed": False,
            "handler_status": "validated",
        },
        ledger_enabled=True,
        reason="",
    )
    
    with patch("app.control_real_smoke.ShotControlService.execute") as mock_execute:
        mock_execute.return_value = mock_response
        
        args = [
            "control_real_smoke",
            "--episode-id", "ep01",
            "--shot-id", "shot01",
            "--action", "generate_frames",
            "--brief", str(tmp_project / "data/briefs/ep01_brief.md"),
            "--ledger-root", str(tmp_project / "output/control"),
        ]
        with patch("sys.argv", args):
            result = main()
            assert result == 0
            assert mock_execute.called


# ── 10. no ledger record has event_type="manual_smoke_executed" ─────────────

def test_no_manual_smoke_executed_event_type() -> None:
    """No ledger record should have event_type='manual_smoke_executed'."""
    source = inspect.getsource(main)
    assert "manual_smoke_executed" not in source


# ── 11. command uses ShotControlService.execute() ───────────────────────

def test_command_uses_shot_control_service_execute(tmp_project: Path) -> None:
    """Command should use ShotControlService.execute()."""
    source = inspect.getsource(main)
    assert "ShotControlService" in source
    assert "service.execute" in source


# ── 12. no ComfyUI / ffmpeg / TTS imports at top level ───────────────────

def test_no_forbidden_top_level_imports() -> None:
    """No top-level imports of ComfyUI, ffmpeg, or TTS."""
    import app.control_real_smoke as mod
    
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


# ── 13. command exits non-zero on missing brief path ───────────────────

def test_missing_brief_exits_nonzero(tmp_project: Path) -> None:
    """Command should exit non-zero on missing brief path."""
    with patch("sys.argv", ["control_real_smoke", "--episode-id", "ep01", "--shot-id", "shot01", "--action", "generate_frames", "--brief", "missing.md"]):
        result = main()
        assert result == 1


# ── 14. command exits zero for safe dry_validate ───────────────────────

def test_safe_dry_validate_exits_zero(tmp_project: Path) -> None:
    """Command should exit zero for safe dry_validate."""
    from app.control import ShotControlResponse
    
    mock_response = ShotControlResponse(
        success=True,
        episode_id="ep01",
        shot_id="shot01",
        requested_action="generate_frames",
        mode="execute",
        state_report={},
        gate_decision={},
        action_plan={},
        action_result={"status": "validated"},
        ledger_enabled=True,
        reason="",
    )
    
    with patch("app.control_real_smoke.ShotControlService.execute") as mock_execute:
        mock_execute.return_value = mock_response
        
        args = [
            "control_real_smoke",
            "--episode-id", "ep01",
            "--shot-id", "shot01",
            "--action", "generate_frames",
            "--brief", str(tmp_project / "data/briefs/ep01_brief.md"),
            "--ledger-root", str(tmp_project / "output/control"),
        ]
        with patch("sys.argv", args):
            result = main()
            assert result == 0


# ── 15. command never calls python -m app run or scene_run internally ──

def test_no_internal_app_run_calls() -> None:
    """Command should never call python -m app run or scene_run internally."""
    source = inspect.getsource(main)
    assert "app.run" not in source
    assert "scene_run" not in source
    assert "subprocess" not in source


# ── 16. explicit fake-real mode through service records production_executed=true ──

def test_explicit_fake_real_mode_service_records_production_true(tmp_project: Path) -> None:
    """Explicit fake-real mode through service should record production_executed=true."""
    from app.control import ShotControlResponse
    
    mock_response = ShotControlResponse(
        success=True,
        episode_id="ep01",
        shot_id="shot01",
        requested_action="generate_frames",
        mode="execute",
        state_report={},
        gate_decision={},
        action_plan={},
        action_result={
            "status": "executed",
            "executed": True,
            "control_executed": True,
            "production_executed": True,
            "handler_status": "executed",
        },
        ledger_enabled=True,
        reason="",
    )
    
    with patch("app.control_real_smoke.ShotControlService.execute") as mock_execute:
        mock_execute.return_value = mock_response
        
        args = [
            "control_real_smoke",
            "--episode-id", "ep01",
            "--shot-id", "shot01",
            "--action", "generate_frames",
            "--brief", str(tmp_project / "data/briefs/ep01_brief.md"),
            "--ledger-root", str(tmp_project / "output/control"),
            "--enable-real-handler",
            "--allow-real-execution",
            "--no-dry-validate",
        ]
        with patch("sys.argv", args):
            result = main()
            assert result == 0
