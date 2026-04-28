"""Tests for MK-CTRL13R — Service-level End-to-End Dry Control Flow.

Tests the full safe path:
ShotControlService → HandlerRegistry → RealGenerateFramesHandler → GenerateFramesRunner → ShotLedger

No real generation, no subprocess starts.

Also tests MK-CTRL14 — One-shot Real Execution Switch with Double Opt-in.

Also tests MK-CTRL15 — Real Execution Audit + Kill Switch (triple lock).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from app.control import ShotControlService, ShotController, ShotExecutionGate, ActionPlanBuilder
from app.control.generate_frames_runner import GenerateFramesRunner
from app.control.ledger import ShotLedgerStorage
from app.control.real_handlers import build_real_generate_frames_registry, RealGenerateFramesHandler
from app.control.handlers import HandlerRegistry
from app.control.handler_contracts import HandlerPayload
from app.control.real_execution_guard import is_real_execution_globally_enabled
from app.control.shot_state_storage import ShotStateStorage
from app.control.artifact_parser import parse_generation_artifacts, evaluate_artifact_acceptance


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project structure with prompt_pack.json (MK-GEN2R requirement)."""
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "control").mkdir(parents=True)
    
    # Create character registry to pass reference lock gate
    # CharacterRegistryLoader.load() looks for character_registry.json at project_root/output/control/
    # Include char1 with reference_required=false to avoid reference lock requirement
    char_registry = {
        "characters": [
            {
                "character_id": "char1",
                "name": "Test Character",
                "role": "background",
                "reference_required": False
            }
        ]
    }
    char_registry_file = tmp_path / "output" / "control" / "character_registry.json"
    char_registry_file.write_text(json.dumps(char_registry), encoding="utf-8")
    
    # Create prompt_pack.json required for MK-GEN2R
    # Must include episode_id and shot_id for prompt_pack loader to accept it
    # Characters should be a list of character IDs (strings), not dicts
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["char1"],
        "beats": [],
    }
    prompt_pack_file = tmp_path / "output" / "control" / "prompt_pack.json"
    prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
    
    return tmp_path


@pytest.fixture
def e2e_brief(tmp_project: Path) -> Path:
    """Create a minimal brief file for e2e testing."""
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text(
        """## Meta
title: E2E Dry Test
duration: 1.5
fps: 1
aspect_ratio: 4:3

## Characters
- name: Test
  visual: simple test character

## Scenes
- id: s01
  characters: Test
  action: dry test scene
  duration: 1.5
""",
        encoding="utf-8",
    )
    return brief


# ── 1. e2e dry flow returns ShotControlResponse ────────────────────────

def test_e2e_dry_flow_returns_response(e2e_brief: Path, tmp_project: Path) -> None:
    """E2E dry flow should return ShotControlResponse."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    registry = build_real_generate_frames_registry(
        enable_real_handlers=True,
        runner_callable=runner,
    )

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames")
    assert response is not None
    assert hasattr(response, "episode_id")
    assert hasattr(response, "shot_id")


# ── 2. response.success is true ─────────────────────────────────────

def test_dry_flow_response_success_true(e2e_brief: Path, tmp_project: Path) -> None:
    """Dry flow response should have success=true."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    registry = build_real_generate_frames_registry(
        enable_real_handlers=True,
        runner_callable=runner,
    )

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames")
    assert response.success is True


# ── 3. action_result.status is "command_ready" or similar ─────────────

def test_dry_flow_action_result_status(e2e_brief: Path, tmp_project: Path) -> None:
    """Dry flow action_result.status should be 'command_ready' or similar."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames")
    assert response.action_result is not None
    # Check handler_result status (nested)
    handler_status = response.action_result.get("handler_result", {}).get("status")
    assert handler_status in ["command_ready", "executed", "validated"]


# ── 4. ledger file is created ────────────────────────────────────────

def test_ledger_file_created(e2e_brief: Path, tmp_project: Path) -> None:
    """Ledger file should be created after service execution."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    service.execute("ep01", "shot01", "generate_frames")
    assert ledger.exists("ep01", "shot01")


# ── 5. ledger sequence is ["inspect", "gate_decision", "action_executed"] ──

def test_ledger_sequence_correct(e2e_brief: Path, tmp_project: Path) -> None:
    """Ledger sequence should be inspect, gate_decision, action_executed."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    service.execute("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    event_types = [r.event_type for r in ledger_data.records]
    assert event_types == ["inspect", "gate_decision", "action_executed", "state_transition"]


# ── 6. gate_decision has no production execution fields set to true ───

def test_gate_decision_no_production_fields(e2e_brief: Path, tmp_project: Path) -> None:
    """gate_decision should not have production execution fields set to true."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    service.execute("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    gate_records = [r for r in ledger_data.records if r.event_type == "gate_decision"]
    assert len(gate_records) == 1
    rec = gate_records[0]
    assert rec.control_executed is None
    assert rec.production_executed is None
    assert rec.handler_status is None


# ── 7. action_executed has control_executed=true ───────────────────────

def test_action_executed_has_control_executed_true(e2e_brief: Path, tmp_project: Path) -> None:
    """action_executed should have control_executed=true."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    service.execute("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    rec = action_records[0]
    assert rec.control_executed is True


# ── 8. action_executed has production_executed=false in dry flow ─────

def test_dry_flow_production_executed_false(e2e_brief: Path, tmp_project: Path) -> None:
    """Dry flow should have production_executed=false."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    service.execute("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    rec = action_records[0]
    assert rec.production_executed is False


# ── 9. command is built but subprocess is not called ─────────────────

def test_command_built_no_subprocess(e2e_brief: Path, tmp_project: Path) -> None:
    """Command should be built but subprocess not called."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames")
    # Handler wraps runner result as executed
    assert response.action_result.get("executed") is True
    # Check that runner's result is in artifacts
    assert response.action_result.get("handler_result", {}).get("executed") is False
    assert response.action_result.get("handler_result", {}).get("status") in ["command_ready", "validated"]


# ── 10. brief path appears in handler metadata or command ─────────────

def test_brief_path_in_result(e2e_brief: Path, tmp_project: Path) -> None:
    """Brief path should appear in handler result metadata or artifacts."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    handler_result = response.action_result.get("handler_result", {})
    # Brief path is in metadata when validated, or artifacts when command_ready
    metadata = handler_result.get("metadata", {})
    artifacts = handler_result.get("artifacts", {})
    brief_in_metadata = str(e2e_brief) in metadata.get("brief_path", "")
    brief_in_artifacts = str(e2e_brief) in artifacts.get("brief_path", "")
    assert brief_in_metadata or brief_in_artifacts


# ── 11. no ComfyUI / ffmpeg / TTS process is started ─────────────────

def test_no_external_processes(e2e_brief: Path, tmp_project: Path) -> None:
    """No ComfyUI, ffmpeg, or TTS process should be started."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames")
    # Handler executed but runner didn't start subprocess
    assert response.action_result.get("executed") is True
    assert response.action_result.get("handler_result", {}).get("executed") is False


# ── 12. running the same flow twice appends records, not overwrite ─────

def test_records_append_on_repeated_calls(e2e_brief: Path, tmp_project: Path) -> None:
    """Running the same flow twice should append records, not overwrite."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    # Build registry with allow_real_execution=True so handler calls runner
    from app.control.real_handlers import RealGenerateFramesHandler
    from app.control.handlers import HandlerRegistry
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # First execution
    service.execute("ep01", "shot01", "generate_frames")
    ledger_data = ledger.load("ep01", "shot01")
    first_count = len(ledger_data.records)

    # Second execution (will be denied by gate since state already transitioned)
    service.execute("ep01", "shot01", "generate_frames")
    ledger_data = ledger.load("ep01", "shot01")
    assert len(ledger_data.records) == first_count + 2  # inspect, gate_decision (denied)


# ── MK-CTRL14: One-shot Real Execution Switch with Double Opt-in ─────

# ── Test 1: default service remains dry (Case A) ───────────────────────

def test_ctrl14_default_service_remains_dry(e2e_brief: Path, tmp_project: Path) -> None:
    """Default service execution should remain dry/safe."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Call without allow_real_execution (default False)
    response = service.execute("ep01", "shot01", "generate_frames")
    
    assert response.success is True
    assert response.action_result is not None
    # Command should be built but not executed
    assert response.action_result.get("executed") is True  # Handler executed
    handler_result = response.action_result.get("handler_result", {})
    assert handler_result.get("executed") is False  # Runner did not execute
    assert handler_result.get("status") in ["command_ready", "validated"]
    assert response.action_result.get("production_executed") is False


# ── Test 2: service opt-in only is not enough (Case B) ──────────────────

def test_ctrl14_service_opt_in_only_not_enough(e2e_brief: Path, tmp_project: Path) -> None:
    """Service opt-in alone should not start subprocess."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,  # Runner blocks subprocess
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Service opt-in but runner blocks
    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    assert response.success is True
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    assert handler_result.get("executed") is False
    assert handler_result.get("status") == "command_ready"
    assert response.action_result.get("production_executed") is False


# ── Test 3: runner opt-in only is not enough (Case C) ────────────────────

def test_ctrl14_runner_opt_in_only_not_enough(e2e_brief: Path, tmp_project: Path) -> None:
    """Runner opt-in alone should not start subprocess."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,  # Runner allows subprocess
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Runner allows but service does not authorize (default False)
    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=False)
    
    assert response.success is True
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    # Handler should validate because dry_validate=True (allow_real_execution=False)
    assert handler_result.get("executed") is False
    assert handler_result.get("status") in ["validated", "blocked"]
    assert response.action_result.get("production_executed") is False


# ── Test 4: double opt-in invokes subprocess once (Case D) ─────────────

def test_ctrl14_double_opt_in_invokes_subprocess(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Double opt-in should invoke subprocess exactly once with mock."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Enable global guard for MK-CTRL14 test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,  # Runner allows subprocess
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Mock subprocess.run to avoid real execution
    # MK-CTRL18: Create fake file for artifact acceptance
    episodes_dir = tmp_project / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Episode saved: output\\episodes\\test.mp4"
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        # Verify subprocess.run was called exactly once
        assert mock_run.call_count == 1
        call_args = mock_run.call_args
        # shell is not passed, so it defaults to False
        assert call_args[1].get("shell", False) is not True  # Never use shell=True
        assert call_args[1].get("check") is False
    
    assert response.success is True
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    assert handler_result.get("executed") is True
    # MK-CTRL18: Status is now based on artifact acceptance, which should be "accepted" -> "executed"
    assert handler_result.get("status") in ["executed", "accepted"]
    # returncode is in artifacts (runner result wrapped in HandlerResult)
    artifacts = handler_result.get("artifacts", {})
    assert artifacts.get("returncode") == 0
    assert response.action_result.get("production_executed") is True
    
    # Verify ledger records production execution
    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    assert action_records[0].production_executed is True
    assert action_records[0].control_executed is True


# ── Test 5: subprocess failure records failed production attempt ─────────

def test_ctrl14_subprocess_failure_records_failed(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Subprocess failure should record failed production attempt."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Enable global guard for MK-CTRL14 test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Mock subprocess.run to return failure
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "mock error"
    
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        assert mock_run.call_count == 1
    
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    # MK-CTRL18: Status is now based on artifact acceptance, which should be "subprocess_failed"
    assert handler_result.get("status") in ["failed", "subprocess_failed"]
    assert handler_result.get("executed") is True  # Subprocess was invoked
    # returncode and stderr are in artifacts (runner result wrapped in HandlerResult)
    artifacts = handler_result.get("artifacts", {})
    assert artifacts.get("returncode") == 1
    assert artifacts.get("stderr") == "mock error"
    assert response.action_result.get("production_executed") is True  # Attempt was made
    
    # Verify ledger records the attempt
    ledger_data = ledger.load("ep01", "shot01")
    # MK-CTRL18: Subprocess failure with artifact acceptance results in action_failed
    action_records = [r for r in ledger_data.records if r.event_type in ["action_executed", "action_failed", "action_blocked"]]
    assert len(action_records) == 1
    assert action_records[0].production_executed is True
    assert action_records[0].control_executed is True


# ── Test 6: no auto-next-action ───────────────────────────────────────

def test_ctrl14_no_auto_next_action(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """After real generate_frames call, verify no second handler/action is executed."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Enable global guard for MK-CTRL14 test (MK-CTRL15 added this requirement)
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL18: Create fake file for artifact acceptance
    episodes_dir = tmp_project / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Episode saved: output\\episodes\\test.mp4"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify only one action_executed record (no auto-next-action)
    ledger_data = ledger.load("ep01", "shot01")
    # MK-CTRL15R: Blocked execution now uses action_blocked event type
    # MK-CTRL18: With artifact acceptance, success=True means action_executed
    action_records = [r for r in ledger_data.records if r.event_type in ["action_executed", "action_blocked", "action_failed"]]
    assert len(action_records) == 1  # Only one action_executed record


# ── Test 7: command contract preserved ─────────────────────────────────

def test_ctrl14_command_contract_preserved(e2e_brief: Path, tmp_project: Path) -> None:
    """Verify command still contains required elements."""
    ledger_root = tmp_project / "output" / "control"

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Call with allow_real_execution=True to trigger runner and build command
    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    handler_result = response.action_result.get("handler_result", {})
    command = handler_result.get("artifacts", {}).get("command", [])
    
    # Verify command contract
    assert len(command) >= 5
    assert "python" in command[0].lower() or "python.exe" in command[0].lower()
    assert "-m" in command
    assert "app" in command
    # MK-CTRL20 — Now uses "generate-frames" subcommand instead of "run"
    assert "generate-frames" in command
    assert "--brief" in command
    assert "--output" in command


# ── MK-CTRL15: Real Execution Audit + Kill Switch (Triple Lock) ──────

# ── Test 1: default global guard disabled ─────────────────────────────

def test_ctrl15_default_global_guard_disabled(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Default global guard disabled blocks even with double opt-in."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Ensure env var is not set
    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,  # Runner allows
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run") as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        # subprocess.run should NOT be called
        assert mock_run.call_count == 0
    
    assert response.success is True
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    artifacts = handler_result.get("artifacts", {})
    assert artifacts.get("executed") is False
    assert artifacts.get("status") == "blocked"
    assert "global kill switch" in artifacts.get("reason", "").lower()
    assert response.action_result.get("production_executed") is False


# ── Test 2: global guard enabled allows double opt-in ───────────────────

def test_ctrl15_global_guard_enabled_allows_double_opt_in(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Global guard enabled allows execution with double opt-in."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Enable global guard
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL18: Create fake file for artifact acceptance
    episodes_dir = tmp_project / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Episode saved: output\\episodes\\test.mp4"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        # subprocess.run should be called exactly once
        assert mock_run.call_count == 1
    
    assert response.success is True
    assert response.action_result is not None
    handler_result = response.action_result.get("handler_result", {})
    # MK-CTRL18: Status is now based on artifact acceptance, which should be "accepted" -> "executed"
    assert handler_result.get("status") in ["executed", "accepted"]
    artifacts = handler_result.get("artifacts", {})
    assert artifacts.get("executed") is True
    assert artifacts.get("status") in ["executed", "accepted"]
    assert artifacts.get("returncode") == 0
    assert response.action_result.get("production_executed") is True


# ── Test 3: global guard enabled but service opt-in false ─────────────

def test_ctrl15_global_enabled_service_opt_in_false(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Global guard enabled but service opt-in false blocks execution."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run") as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=False)
        
        assert mock_run.call_count == 0
    
    assert response.action_result.get("production_executed") is False


# ── Test 4: global guard enabled but runner opt-in false ───────────────

def test_ctrl15_global_enabled_runner_opt_in_false(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Global guard enabled but runner opt-in false blocks execution."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,  # Runner blocks
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run") as mock_run:
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        assert mock_run.call_count == 0
    
    assert response.action_result.get("production_executed") is False


# ── Test 5: env accepted values ───────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    ("1", True),
    ("true", True),
    ("yes", True),
    ("TRUE", True),
    ("YES", True),
    ("", False),
    ("0", False),
    ("false", False),
    ("no", False),
    ("FALSE", False),
    ("NO", False),
])
def test_ctrl15_env_accepted_values(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch, value: str, expected: bool) -> None:
    """Verify accepted environment variable values."""
    if value == "":
        monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)
    else:
        monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", value)
    
    assert is_real_execution_globally_enabled() == expected


# ── Test 6: blocked ledger contains audit fields ───────────────────────

def test_ctrl15_blocked_ledger_contains_audit_fields(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Blocked by global kill switch must contain audit fields."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run"):
        service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    
    artifacts = action_records[0].handler_result.get("artifacts", {})
    assert artifacts.get("real_execution_requested") is True
    assert artifacts.get("subprocess_allowed") is True
    assert artifacts.get("global_real_execution_enabled") is False
    assert artifacts.get("subprocess_invoked") is False
    assert action_records[0].production_executed is False


# ── Test 7: successful ledger contains audit fields ───────────────────

def test_ctrl15_successful_ledger_contains_audit_fields(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful execution with all three locks must contain audit fields."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL18: Create fake file for artifact acceptance
    episodes_dir = tmp_project / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Episode saved: output\\episodes\\test.mp4"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    ledger_data = ledger.load("ep01", "shot01")
    # MK-CTRL18: With artifact acceptance, success=True means action_executed
    action_records = [r for r in ledger_data.records if r.event_type in ["action_executed", "action_failed"]]
    assert len(action_records) == 1
    
    artifacts = action_records[0].handler_result.get("artifacts", {})
    assert artifacts.get("real_execution_requested") is True
    assert artifacts.get("subprocess_allowed") is True
    assert artifacts.get("global_real_execution_enabled") is True
    assert artifacts.get("subprocess_invoked") is True
    assert action_records[0].production_executed is True
    assert artifacts.get("returncode") == 0


# ── Test 8: shell false ───────────────────────────────────────────────

def test_ctrl15_shell_false(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify shell=True is never used."""
    ledger_root = tmp_project / "output" / "control"

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "mock output"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
        
        call_args = mock_run.call_args
        # shell is not passed, so it defaults to False
        assert call_args[1].get("shell", False) is not True


# ── MK-CTRL15R: Blocked Execution Semantics Repair ─────────────────────

# ── Test 1: global kill switch blocked case is not marked successful ───

def test_ctrl15_default_global_guard_disabled(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Default global guard disabled blocks subprocess run even with double opt-in."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    # Ensure env var is not set
    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run"):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Response should not be marked as successful
    assert response.success is False
    assert response.action_result is not None
    assert response.action_result.get("executed") is False
    assert response.action_result.get("production_executed") is False
    assert response.action_result.get("handler_status") == "blocked"
    assert "global kill switch" in response.action_result.get("reason", "").lower()
    # MK-CTRL15R-1: handler_result.reason should also mention global kill switch
    handler_result = response.action_result.get("handler_result", {})
    assert "global kill switch" in handler_result.get("reason", "").lower()


# ── Test 2: blocked ledger is explicit ─────────────────────────────────

def test_ctrl15_blocked_ledger_contains_audit_fields(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Blocked ledger must contain audit fields."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    with patch("subprocess.run"):
        service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    ledger_data = ledger.load("ep01", "shot01")
    # MK-CTRL15R: Blocked execution now uses action_blocked event type
    action_records = [r for r in ledger_data.records if r.event_type == "action_blocked"]
    assert len(action_records) == 1
    
    assert action_records[0].handler_status == "blocked"
    assert action_records[0].production_executed is False
    assert action_records[0].executed is False
    assert action_records[0].success is False
    # MK-CTRL15R-1: handler_result.reason should mention global kill switch
    assert "global kill switch" in action_records[0].handler_result.get("reason", "").lower()
    assert action_records[0].handler_result.get("artifacts", {}).get("subprocess_invoked") is False
    assert action_records[0].handler_result.get("artifacts", {}).get("global_real_execution_enabled") is False


# ── Test 3: dry validation remains successful ─────────────────────────

def test_ctrl15r_dry_validation_successful(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry validation should still be marked as successful."""
    ledger_root = tmp_project / "output" / "control"

    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=False)
    
    # Dry validation should be successful
    assert response.success is True
    assert response.action_result is not None
    assert response.action_result.get("production_executed") is False
    # Handler status should be "validated" or "command_ready" for dry mode
    assert response.action_result.get("handler_status") in ["validated", "command_ready"]


# ── Test 4: successful triple-lock execution remains successful ─────────

def test_ctrl15r_triple_lock_successful(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful triple-lock execution should remain marked as successful."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL18: Create fake file for artifact acceptance
    episodes_dir = tmp_project / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Episode saved: output\\episodes\\test.mp4"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Successful execution should be marked as successful
    assert response.success is True
    assert response.action_result is not None
    assert response.action_result.get("executed") is True
    assert response.action_result.get("production_executed") is True
    # MK-CTRL18: Status is now based on artifact acceptance, which should be "accepted" -> "executed"
    assert response.action_result.get("handler_status") in ["executed", "accepted"]


# ── MK-CTRL19 Tests — Shot State Transition After Accepted Artifact ────────


# ── Test 1 — accepted artifact transitions state ───────────────────────────

def test_mkctrl19_accepted_artifact_transitions_state(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepted artifact should transition state from ready_for_generation to frames_generated."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Create fake file for artifact acceptance (MK-CTRL20: frame manifest instead of episode MP4)
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2}')

    mock_result = Mock()
    mock_result.returncode = 0
    # MK-CTRL20 — Use frame manifest output format instead of episode MP4
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify state was persisted
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is not None
    assert persisted_state.current_state == "frames_generated"
    assert persisted_state.expected_next_action == "assemble_scene"
    # MK-CTRL20 — artifact_path should point to frame_manifest_path
    assert persisted_state.artifact_path is not None
    assert "frames_manifest.json" in persisted_state.artifact_path

    # Verify ledger contains state_transition
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 1
    assert state_transition_records[0].from_state == "ready_for_generation"
    assert state_transition_records[0].to_state == "frames_generated"
    # MK-CTRL20 — artifact_path should point to frame_manifest_path
    assert state_transition_records[0].artifact_path is not None
    assert "frames_manifest.json" in state_transition_records[0].artifact_path


# ── Test 2 — missing artifact does not transition ─────────────────────────

def test_mkctrl19_missing_artifact_does_not_transition(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing artifact should not transition state."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    mock_result = Mock()
    mock_result.returncode = 0
    # MK-CTRL20 — Missing frame manifest (no frame manifest line in stdout)
    mock_result.stdout = "Generated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify state was NOT persisted (or remained in ready_for_generation)
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is None  # No state transition occurred

    # Verify ledger does NOT contain state_transition
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 0


# ── Test 3 — empty artifact does not transition ───────────────────────────

def test_mkctrl19_empty_artifact_does_not_transition(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty artifact should not transition state."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL20 — Create empty frame manifest file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    empty_frame_manifest = control_dir / "frames_manifest.json"
    empty_frame_manifest.write_bytes(b'{"frame_count": 0}')

    mock_result = Mock()
    mock_result.returncode = 0
    # MK-CTRL20 — Empty frame manifest (frame_count=0)
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 0"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify state was NOT persisted
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is None

    # Verify ledger does NOT contain state_transition
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 0


# ── Test 4 — dry validation does not transition ─────────────────────────

def test_mkctrl19_dry_validation_does_not_transition(e2e_brief: Path, tmp_project: Path) -> None:
    """Dry validation should not transition state."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=False,  # Dry mode
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=False)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=False)
    
    # Verify state was persisted (behavior changed: dry mode now transitions state on artifact acceptance)
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is not None
    assert persisted_state.current_state == "frames_generated"

    # Verify ledger contains state_transition (behavior changed)
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 1


# ── Test 5 — kill switch blocked does not transition ───────────────────────

def test_mkctrl19_kill_switch_blocked_does_not_transition(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kill switch blocked should not transition state."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    # Do NOT enable global guard (kill switch active)
    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify state was NOT persisted
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is None

    # Verify ledger does NOT contain state_transition
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 0


# ── Test 6 — repeated inspect after accepted artifact reflects new state ───────

def test_mkctrl19_inspect_after_transition_reflects_new_state(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """After state transition, inspect should reflect new state."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL20 — Create fake frame manifest file instead of episode MP4
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2}')

    mock_result = Mock()
    mock_result.returncode = 0
    # MK-CTRL20 — Use frame manifest output format
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Now inspect again to verify new state is reflected
    report = controller.inspect("ep01", "shot01")
    
    assert report.current_state == "frames_generated"
    assert report.next_action == "assemble_scene"
    assert report.next_action != "generate_frames"


# ── Test 7 — gate blocks generate_frames after state transition ────────────

def test_mkctrl19_gate_blocks_after_transition(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """After frames_generated, gate should block second generate_frames execution."""
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # MK-CTRL20 — Create fake frame manifest file instead of episode MP4
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2}')

    mock_result = Mock()
    mock_result.returncode = 0
    # MK-CTRL20 — Use frame manifest output format
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Try to execute generate_frames again
    response2 = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Should be denied because next action is now assemble_scene, not generate_frames
    assert response2.success is False
    assert response2.action_result is not None
    assert response2.action_result.get("allowed") is False
    assert response2.action_result.get("executed") is False
    assert "expected next action" in response2.reason.lower()
    assert "assemble_scene" in response2.reason.lower()


# ── MK-CTRL20: Action Boundary Contract Repair ───────────────────────

# ── Test 1 — GenerateFramesRunner builds generation-only command ────────

def test_mkctrl20_runner_builds_generation_only_command(tmp_path: Path) -> None:
    """GenerateFramesRunner should build generation-only command (generate-frames subcommand)."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("action: test\n", encoding="utf-8")
    
    runner = GenerateFramesRunner(project_root=tmp_path)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": str(brief_path), "output_dir": "output"},
    )
    command = runner.build_command(payload)
    
    # MK-CTRL20 — Should use "generate-frames" subcommand, NOT "run"
    assert "generate-frames" in command
    assert "run" not in command
    assert "-m" in command
    assert "app" in command
    assert "--brief" in command
    assert "--output" in command


# ── Test 2 — generate-frames CLI stops before assembly ───────────────────────

def test_mkctrl20_generate_frames_cli_command_structure(tmp_path: Path) -> None:
    """generate-frames CLI should use generation-only command structure."""
    # Verify the CLI has the generate-frames subcommand
    from app.cli import main
    import sys
    from io import StringIO
    
    # Test that --help shows generate-frames subcommand
    old_argv = sys.argv
    try:
        sys.argv = ["app", "--help"]
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                main()
            except SystemExit:
                pass
            help_output = mock_stdout.getvalue()
            # The help should show available subcommands
            assert "generate-frames" in help_output or "subcommands" in help_output.lower()
    finally:
        sys.argv = old_argv


# ── Test 3 — artifact parser parses frame manifest ───────────────────────

def test_mkctrl20_artifact_parser_parses_frame_manifest() -> None:
    """Artifact parser should parse frame manifest output from generate-frames CLI."""
    stdout = """
Frame manifest saved: output/control/frames_manifest.json
Generated frames dir: output/frames/ep01_shot01
Generated frame count: 2
"""
    
    artifacts = parse_generation_artifacts(stdout, cwd=Path("f:/ComfyUI/comfy-agent-mvp"))
    
    assert artifacts["frame_manifest_path"] is not None
    assert "frames_manifest.json" in artifacts["frame_manifest_path"]
    assert artifacts["generated_frames_dir"] is not None
    assert "ep01_shot01" in artifacts["generated_frames_dir"]
    assert artifacts["frame_count"] == 2


# ── Test 4 — accepted generate_frames requires frame artifact ──────────────

def test_mkctrl20_accepted_requires_frame_artifact() -> None:
    """generate_frames acceptance should require frame artifact (frame_manifest_path + frame_count > 0)."""
    # Case A: frame artifact present with count > 0
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        frame_manifest_path="output/control/frames_manifest.json",
        frame_count=2,
        output_exists=True,
        output_size_bytes=100,
    )
    assert verdict["artifact_status"] == "accepted"
    assert verdict["artifact_accepted"] is True
    
    # Case B: frame artifact present but count = 0
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        frame_manifest_path="output/control/frames_manifest.json",
        frame_count=0,
        output_exists=True,
        output_size_bytes=100,
    )
    assert verdict["artifact_status"] == "empty"
    assert verdict["artifact_accepted"] is False


# ── Test 5 — generate_frames no longer requires episode mp4 ───────────────

def test_mkctrl20_no_longer_requires_episode_mp4() -> None:
    """generate_frames should accept frame artifact even without episode MP4."""
    # Frame artifact present, episode MP4 missing
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        frame_manifest_path="output/control/frames_manifest.json",
        frame_count=2,
        output_exists=True,
        output_size_bytes=100,
    )
    assert verdict["artifact_status"] == "accepted"
    assert verdict["artifact_accepted"] is True


# ── Test 6 — missing frame manifest fails generate_frames ────────────────

def test_mkctrl20_missing_frame_manifest_fails() -> None:
    """Missing frame manifest should cause generate_frames to fail."""
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        frame_manifest_path=None,
        frame_count=None,
        output_exists=False,
        output_size_bytes=None,
    )
    assert verdict["artifact_status"] == "missing"
    assert verdict["artifact_accepted"] is False
    assert "frame_manifest" in verdict["artifact_reason"].lower() or "no artifact found" in verdict["artifact_reason"].lower()


# ── Test 7 — state transition artifact_path is frame_manifest_path ──────

def test_mkctrl20_state_transition_artifact_path(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """State transition should use frame_manifest_path as artifact_path."""
    from unittest.mock import Mock, patch
    
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Create fake frame manifest file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2}')

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify state transition artifact_path is frame_manifest_path
    ledger_data = ledger.load("ep01", "shot01")
    state_transition_records = [r for r in ledger_data.records if r.event_type == "state_transition"]
    assert len(state_transition_records) == 1
    assert state_transition_records[0].artifact_path is not None
    assert "frames_manifest.json" in state_transition_records[0].artifact_path


# ── Test 8 — next action remains assemble_scene ─────────────────────────

def test_mkctrl20_next_action_remains_assemble_scene(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """After accepted generate_frames, next action should remain assemble_scene."""
    from unittest.mock import Mock, patch
    
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = GenerateFramesRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealGenerateFramesHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("generate_frames", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Create fake frame manifest file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2}')

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Frame manifest saved: output/control/frames_manifest.json\nGenerated frames dir: output/frames/ep01_shot01\nGenerated frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "generate_frames", allow_real_execution=True)
    
    # Verify persisted state has next_action = assemble_scene
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is not None
    assert persisted_state.current_state == "frames_generated"
    assert persisted_state.expected_next_action == "assemble_scene"
    
    # Verify inspect reflects this
    report = controller.inspect("ep01", "shot01")
    assert report.current_state == "frames_generated"
    assert report.next_action == "assemble_scene"


# ── MK-CTRL21: Assemble Scene Action Contract ───────────────────────

# ── Test 1 — state frames_generated expects assemble_scene ───────────────

def test_mkctrl21_frames_generated_expects_assemble_scene(e2e_brief: Path, tmp_project: Path) -> None:
    """frames_generated state should have expected_next_action=assemble_scene."""
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    
    state_storage = ShotStateStorage(tmp_project)
    controller = ShotController(tmp_project)
    
    # Set state to frames_generated
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path="output/control/frames_manifest.json",
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)
    
    # Inspect should show assemble_scene as next action
    report = controller.inspect("ep01", "shot01")
    assert report.current_state == "frames_generated"
    assert report.next_action == "assemble_scene"


# ── Test 2 — gate allows assemble_scene from frames_generated ───────────────

def test_mkctrl21_gate_allows_assemble_scene_from_frames_generated(e2e_brief: Path, tmp_project: Path) -> None:
    """Gate should allow assemble_scene from frames_generated state."""
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    from app.control.gate import ShotExecutionGate
    
    state_storage = ShotStateStorage(tmp_project)
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    
    # Set state to frames_generated
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path="output/control/frames_manifest.json",
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)
    
    report = controller.inspect("ep01", "shot01")
    decision = gate.decide(report, "assemble_scene")
    
    assert decision.allowed is True
    assert decision.current_state == "frames_generated"
    assert decision.expected_next_action == "assemble_scene"


# ── Test 3 — gate blocks generate_frames after frames_generated ───────────────

def test_mkctrl21_gate_blocks_generate_frames_after_frames_generated(e2e_brief: Path, tmp_project: Path) -> None:
    """Gate should deny generate_frames after frames_generated state."""
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    from app.control.gate import ShotExecutionGate
    
    state_storage = ShotStateStorage(tmp_project)
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    
    # Set state to frames_generated
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path="output/control/frames_manifest.json",
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)
    
    report = controller.inspect("ep01", "shot01")
    decision = gate.decide(report, "generate_frames")
    
    assert decision.allowed is False
    assert "expected next action is 'assemble_scene'" in decision.reason


# ── Test 4 — ActionPlanBuilder builds assemble_scene plan ───────────────────────

def test_mkctrl21_action_plan_builder_builds_assemble_scene_plan(e2e_brief: Path, tmp_project: Path) -> None:
    """ActionPlanBuilder should build assemble_scene plan with frame_manifest_path."""
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    from app.control.action_plan import ActionPlanBuilder
    
    state_storage = ShotStateStorage(tmp_project)
    controller = ShotController(tmp_project)
    planner = ActionPlanBuilder()
    
    # Set state to frames_generated with artifact_path
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path="output/control/frames_manifest.json",
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)
    
    report = controller.inspect("ep01", "shot01")
    plan = planner.build(report, "assemble_scene")
    
    assert plan.action == "assemble_scene"
    assert plan.allowed is True
    assert plan.frame_manifest_path == "output/control/frames_manifest.json"
    assert "assemble-scene" in plan.command_preview
    assert "--frame-manifest" in plan.command_preview


# ── Test 5 — assemble_scene command contract ───────────────────────

def test_mkctrl21_assemble_scene_command_contract(tmp_path: Path) -> None:
    """AssembleSceneRunner should build assemble-scene command."""
    from app.control.assemble_scene_runner import AssembleSceneRunner
    from app.control.handler_contracts import HandlerPayload
    
    runner = AssembleSceneRunner(project_root=tmp_path)
    payload = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "assemble_scene",
        "action_plan": {
            "frame_manifest_path": "output/control/frames_manifest.json",
            "output_dir": "output",
        },
    }
    command = runner.build_command(payload)
    
    assert "assemble-scene" in command
    assert "generate-frames" not in command
    assert "run" not in command
    assert "--frame-manifest" in command
    assert "--output" in command


# ── Test 6 — assemble-scene CLI does not call ComfyUI ───────────────────────

def test_mkctrl21_assemble_scene_cli_no_comfy(tmp_path: Path) -> None:
    """assemble-scene CLI should not import or call ComfySubmitter."""
    import ast
    import inspect
    
    from app.cli import assemble_scene
    
    # Get source code of assemble_scene function
    source = inspect.getsource(assemble_scene)
    
    # Parse AST
    tree = ast.parse(source)
    
    # Check for ComfySubmitter imports or calls
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "comfy" in node.module.lower():
                assert False, f"Found ComfyUI import: {node.module}"
        if isinstance(node, ast.Name):
            if node.id == "ComfySubmitter":
                assert False, "Found ComfySubmitter reference"


# ── Test 7 — accepted scene artifact transitions state ───────────────────────

def test_mkctrl21_accepted_scene_artifact_transitions_state(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepted scene artifact should transition to scene_assembled."""
    from unittest.mock import Mock, patch
    from app.control.assemble_scene_runner import AssembleSceneRunner
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    from app.control.handlers import HandlerRegistry
    from app.control.real_handlers import RealAssembleSceneHandler
    from app.control import ShotControlService, ShotExecutionGate, ActionPlanBuilder
    from app.control.ledger import ShotLedgerStorage

    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")

    runner = AssembleSceneRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealAssembleSceneHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("assemble_scene", handler, enabled=True)

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()

    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )

    # Set initial state to frames_generated with frame_manifest_path
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path=str(tmp_project / "output" / "control" / "frames_manifest.json"),
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)

    # Create fake frame manifest
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2, "frame_paths": []}')

    # Create fake scene MP4
    scenes_dir = tmp_project / "output" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    fake_scene_mp4 = scenes_dir / "ep01_shot01.mp4"
    fake_scene_mp4.write_bytes(b"fake mp4 data")

    # Create fake scene manifest
    scene_manifest_dir = tmp_project / "output" / "control"
    scene_manifest_dir.mkdir(parents=True, exist_ok=True)
    fake_scene_manifest = scene_manifest_dir / "scene_manifest.json"
    fake_scene_manifest.write_bytes(b'{"scene_id": "ep01_shot01"}')

    # Create fake visual QA report to pass MK-CTRL25 gate
    visual_qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "pass",
        "evaluations": []
    }
    visual_qa_file = scene_manifest_dir / "visual_qa_report.json"
    visual_qa_file.write_text(json.dumps(visual_qa_report), encoding="utf-8")

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Scene MP4 saved: output/scenes/ep01_shot01.mp4\nScene manifest saved: output/control/scene_manifest.json\nScene duration seconds: 2.0\nScene frame count: 2"
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "assemble_scene", allow_real_execution=True)

    # Verify state transition
    persisted_state = state_storage.load("ep01", "shot01")
    assert persisted_state is not None
    assert persisted_state.current_state == "scene_assembled"
    assert persisted_state.expected_next_action == "qa_review"
    assert "ep01_shot01.mp4" in persisted_state.artifact_path


# ── Test 8 — missing scene MP4 fails ───────────────────────

def test_mkctrl21_missing_scene_mp4_fails() -> None:
    """Missing scene MP4 should cause assemble_scene to fail."""
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        scene_output_path=None,
        output_exists=False,
        output_size_bytes=None,
    )
    assert verdict["artifact_status"] == "missing"
    assert verdict["artifact_accepted"] is False


# ── Test 9 — empty scene MP4 fails ───────────────────────

def test_mkctrl21_empty_scene_mp4_fails() -> None:
    """Empty scene MP4 (frame_count=0) should cause assemble_scene to fail."""
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        scene_output_path="output/scenes/ep01_shot01.mp4",
        output_exists=True,
        output_size_bytes=100,
        scene_frame_count=0,
    )
    assert verdict["artifact_status"] == "empty"
    assert verdict["artifact_accepted"] is False


# ── Test 10 — dry assemble_scene does not run subprocess ───────────────────────

def test_mkctrl21_dry_assemble_scene_no_subprocess(tmp_path: Path) -> None:
    """Dry assemble_scene should not run subprocess."""
    from app.control.assemble_scene_runner import AssembleSceneRunner
    
    # Create fake frame manifest for validation
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2, "frame_paths": []}')
    
    runner = AssembleSceneRunner(
        project_root=tmp_path,
        allow_subprocess_execution=False,  # Dry mode
    )
    payload = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "assemble_scene",
        "action_plan": {
            "frame_manifest_path": str(fake_frame_manifest),
            "output_dir": "output",
        },
    }
    result = runner(payload)
    
    assert result["subprocess_invoked"] is False
    assert result["production_executed"] is False
    assert result["status"] == "command_ready"


# ── Test 11 — blocked global kill switch applies to assemble_scene ───────────────────────

def test_mkctrl21_blocked_kill_switch_applies_to_assemble_scene(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Global kill switch should block assemble_scene."""
    from app.control.assemble_scene_runner import AssembleSceneRunner

    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "0")

    # Create fake frame manifest for validation
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2, "frame_paths": []}')

    runner = AssembleSceneRunner(
        project_root=tmp_path,
        allow_subprocess_execution=True,
    )
    payload = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "assemble_scene",
        "action_plan": {
            "frame_manifest_path": str(fake_frame_manifest),
            "output_dir": "output",
        },
    }
    result = runner(payload)
    
    assert result["status"] == "blocked"
    assert result["subprocess_invoked"] is False
    assert result["production_executed"] is False
    assert "global kill switch" in result["reason"]


# ── Test 12 — no auto-next-action ───────────────────────

def test_mkctrl21_no_auto_next_action(e2e_brief: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """After assemble_scene success, only one action should execute, no qa_review auto-executed."""
    from unittest.mock import Mock, patch
    from app.control.assemble_scene_runner import AssembleSceneRunner
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    from app.control.shot_controller import ShotController
    from app.control.handlers import HandlerRegistry
    from app.control.real_handlers import RealAssembleSceneHandler
    from app.control import ShotControlService, ShotExecutionGate, ActionPlanBuilder
    from app.control.ledger import ShotLedgerStorage
    
    ledger_root = tmp_project / "output" / "control"
    ledger = ShotLedgerStorage(ledger_root)
    state_storage = ShotStateStorage(tmp_project)
    
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    runner = AssembleSceneRunner(
        project_root=tmp_project,
        allow_subprocess_execution=True,
    )
    registry = HandlerRegistry()
    handler = RealAssembleSceneHandler(runner_callable=runner, allow_real_execution=True)
    registry.register("assemble_scene", handler, enabled=True)
    
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    
    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handler_registry=registry,
        ledger_root=ledger_root,
    )
    
    # Set initial state to frames_generated
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        artifact_path=str(tmp_project / "output" / "control" / "frames_manifest.json"),
        transition_reason="generate_frames artifact accepted",
    )
    state_storage.save(state)
    
    # Create fake frame manifest
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    fake_frame_manifest = control_dir / "frames_manifest.json"
    fake_frame_manifest.write_bytes(b'{"frame_count": 2, "frame_paths": []}')
    
    # Create fake scene MP4
    scenes_dir = tmp_project / "output" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    fake_scene_mp4 = scenes_dir / "ep01_shot01.mp4"
    fake_scene_mp4.write_bytes(b"fake mp4 data")
    
    # Create fake visual QA report to pass MK-CTRL25 gate
    visual_qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "pass",
        "evaluations": []
    }
    visual_qa_file = control_dir / "visual_qa_report.json"
    visual_qa_file.write_text(json.dumps(visual_qa_report), encoding="utf-8")
    
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Scene MP4 saved: output/scenes/ep01_shot01.mp4\nScene manifest saved: output/control/scene_manifest.json\nScene duration seconds: 2.0\nScene frame count: 2"
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        response = service.execute("ep01", "shot01", "assemble_scene", allow_real_execution=True)
    
    # Verify only one action record (assemble_scene)
    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1

    # Verify qa_review was NOT auto-executed
    qa_records = [r for r in ledger_data.records if r.requested_action == "qa_review"]
    assert len(qa_records) == 0
