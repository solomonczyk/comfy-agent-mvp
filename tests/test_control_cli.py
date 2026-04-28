"""MK-CTRL26R-2 — Control CLI safety tests with isolated project roots.

Tests for the control-shot CLI command that exposes the controlled shot lifecycle.
Updated to verify safety requirements: execute-safe mode, kill switch, gate denial.
Each test uses an isolated tmp_path to prevent state leakage between tests.
"""
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from argparse import Namespace


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project structure with isolated state for each test."""
    # Create unique subdirectories for this test to ensure isolation
    test_id = os.urandom(4).hex()
    project_root = tmp_path / f"project_{test_id}"
    
    (project_root / "data" / "briefs").mkdir(parents=True)
    (project_root / "output" / "control").mkdir(parents=True)
    (project_root / "output" / "episodes").mkdir(parents=True)
    (project_root / "output" / "scenes").mkdir(parents=True)
    (project_root / "output" / "frames").mkdir(parents=True)
    
    # Create character registry to pass reference lock gate
    char_registry_file = project_root / "output" / "control" / "character_registry.json"
    char_registry_file.write_text(json.dumps({"characters": []}), encoding="utf-8")
    
    # Create prompt_pack.json to pass prompt-pack mode gate
    prompt_pack = {"characters": [], "beats": []}
    prompt_pack_file = project_root / "output" / "control" / "prompt_pack.json"
    prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
    
    # Create a brief file
    brief = project_root / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Initialize shot state to ready_for_generation
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(project_root)
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(brief),
    )
    state_storage.save(state)
    
    return project_root


def run_control_shot_direct(args: Namespace, project_root: Path) -> tuple[int, dict]:
    """Helper to run control-shot function directly."""
    from app.cli import control_shot
    
    # Capture stdout
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        exit_code = control_shot(args)
    
    output_json = json.loads(output_buffer.getvalue())
    return exit_code, output_json


# ── Test 1: blocked kill switch exits 3 ───────────────────────────────

def test_control_shot_blocked_kill_switch_exits_3(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 1 — blocked kill switch exits 3.
    
    Setup:
    - --execute --allow-real
    - env missing
    
    Expected:
    - exit_code == 3
    - handler_status="blocked"
    - subprocess_invoked=false
    - production_executed=false
    """
    # Ensure env is not set
    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)
    
    args = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=True,
        ledger_root="output/control",
        project_root=str(tmp_project),
        json=True,
    )
    
    exit_code, output = run_control_shot_direct(args, tmp_project)
    
    assert exit_code == 3
    assert output["mode"] == "execute"
    assert output["state_report"] is not None
    assert output["gate_decision"] is not None
    assert output["action_plan"] is not None
    assert output["action_result"] is not None
    assert output["action_result"].get("handler_status") == "blocked"
    assert output["action_result"].get("production_executed") is False
    assert output["action_result"].get("subprocess_invoked") is False
    assert output["success"] is False


# ── Test 2: gate denied exits 2 ───────────────────────────────────────

def test_control_shot_gate_denied_exits_2(tmp_project: Path) -> None:
    """Test 2 — gate denied exits 2.
    
    Setup:
    - state frames_generated
    - requested generate_frames
    
    Expected:
    - exit_code == 2
    - gate_decision.allowed=false
    - no subprocess
    """
    # Update state to frames_generated
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"),
    )
    state_storage.save(state)
    
    args = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=False,
        ledger_root="output/control",
        project_root=str(tmp_project),
        json=True,
    )
    
    exit_code, output = run_control_shot_direct(args, tmp_project)
    
    assert exit_code == 2
    assert output["mode"] == "execute"
    assert output["gate_decision"] is not None
    assert output["gate_decision"].get("allowed") is False
    assert output["action_result"] is not None
    assert output["action_result"].get("production_executed") is False
    assert output["action_result"].get("subprocess_invoked") is False
    assert output["success"] is False


# ── Test 3: execute-safe exits 0 and stays dry ─────────────────────────

def test_control_shot_execute_safe_exits_0(tmp_project: Path) -> None:
    """Test 3 — execute without allow-real is safe.
    
    Setup:
    - --execute without --allow-real
    
    Expected:
    - exit_code == 0
    - production_executed=false
    - subprocess_invoked=false
    """
    args = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=False,
        ledger_root="output/control",
        project_root=str(tmp_project),
        json=True,
    )
    
    exit_code, output = run_control_shot_direct(args, tmp_project)
    
    assert exit_code == 0
    assert output["mode"] == "execute"
    assert output["action_result"] is not None
    assert output["action_result"].get("production_executed") is False
    assert output["action_result"].get("subprocess_invoked") is False
    assert output["success"] is True


# ── Test 4: successful mocked real execution exits 0 ───────────────────

def test_control_shot_successful_mocked_real_execution_exits_0(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 4 — successful mocked real execution exits 0.
    
    Setup:
    - --execute --allow-real
    - env enabled
    
    Expected:
    - exit_code == 0
    - production_executed=true
    - subprocess_invoked=true
    """
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    # Patch the factory to always use mock handlers (safe) but simulate real execution
    from app.control import factory
    original_build = factory.build_shot_control_service
    
    def mock_build_with_real_flag(project_root, enable_mock_handlers=False):
        # Force use of mock handlers (safe) regardless of allow_real flag
        service = original_build(project_root, enable_mock_handlers=True)
        return service
    
    # Patch the generate_frames_handler to return real execution fields when allow_real_execution=True
    from app.control import handlers
    original_generate_handler = handlers.generate_frames_handler
    
    def real_mock_handler(payload: dict) -> dict:
        # Simulate real execution when allow_real_execution=True
        if payload.get("allow_real_execution"):
            return {
                "handler": "generate_frames",
                "status": "executed",
                "executed": True,
                "control_executed": True,
                "production_executed": True,
                "subprocess_invoked": True,
                "received": {
                    "episode_id": payload.get("episode_id"),
                    "shot_id": payload.get("shot_id"),
                }
            }
        return original_generate_handler(payload)
    
    # Patch at the module level before CLI builds the service
    with patch.object(factory, 'build_shot_control_service', side_effect=mock_build_with_real_flag), \
         patch.object(handlers, 'generate_frames_handler', side_effect=real_mock_handler):
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="generate_frames",
            execute=True,
            allow_real=True,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        
        exit_code, output = run_control_shot_direct(args, tmp_project)
    
    assert exit_code == 0
    assert output["mode"] == "execute"
    assert output["action_result"] is not None
    assert output["action_result"].get("production_executed") is True
    assert output["action_result"].get("subprocess_invoked") is True
    assert output["success"] is True


# ── Test 5: test isolation ─────────────────────────────────────────────

def test_control_shot_isolation(tmp_path: Path) -> None:
    """Test 5 — CLI tests use isolated temp roots.
    
    Run two CLI calls in separate tmp project roots.
    Expected:
    - states do not leak between calls.
    """
    # Create two isolated project roots
    project1 = tmp_path / "project_isolation_1"
    project2 = tmp_path / "project_isolation_2"
    
    for project in [project1, project2]:
        (project / "data" / "briefs").mkdir(parents=True)
        (project / "output" / "control").mkdir(parents=True)
        (project / "output" / "episodes").mkdir(parents=True)
        brief = project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create character registry to pass reference lock gate
        char_registry_file = project / "output" / "control" / "character_registry.json"
        char_registry_file.write_text(json.dumps({"characters": []}), encoding="utf-8")
        
        # Create prompt_pack.json to pass prompt-pack mode gate
        prompt_pack = {"characters": [], "beats": []}
        prompt_pack_file = project / "output" / "control" / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        from app.control.shot_state_storage import ShotState, ShotStateStorage
        state_storage = ShotStateStorage(project)
        state = ShotState(
            episode_id="ep01",
            shot_id="shot01",
            current_state="ready_for_generation",
            expected_next_action="generate_frames",
            last_updated="2024-01-01T00:00:00",
            brief_path=str(brief),
        )
        state_storage.save(state)
    
    # Run CLI on project1
    args1 = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=False,
        ledger_root="output/control",
        project_root=str(project1),
        json=True,
    )
    exit_code1, output1 = run_control_shot_direct(args1, project1)
    
    # Run CLI on project2
    args2 = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=False,
        ledger_root="output/control",
        project_root=str(project2),
        json=True,
    )
    exit_code2, output2 = run_control_shot_direct(args2, project2)
    
    # Both should succeed independently
    assert exit_code1 == 0
    assert exit_code2 == 0
    assert output1["action_result"]["production_executed"] is False
    assert output2["action_result"]["production_executed"] is False

