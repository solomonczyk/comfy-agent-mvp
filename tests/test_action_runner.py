"""Tests for MK-CTRL3 — ControlledActionRunner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.action_runner import ActionRunResult, ControlledActionRunner
from app.control.gate import ShotExecutionGate
from app.control.models import ShotArtifacts, ShotStateReport
from app.control.shot_controller import ShotController


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    (tmp_path / "output" / "control").mkdir(parents=True)
    
    # Create character registry to pass reference lock gate
    char_registry_file = tmp_path / "output" / "control" / "character_registry.json"
    char_registry_file.write_text(json.dumps({"characters": []}), encoding="utf-8")
    
    # Create prompt_pack.json to pass prompt-pack mode gate
    prompt_pack = {
        "characters": [],
        "beats": [],
        "positive_prompt": "a cinematic shot of a character walking through a futuristic city at sunset with dramatic lighting and detailed architecture",
        "negative_prompt": "blurry, low quality, distorted, watermark, text, bad anatomy"
    }
    prompt_pack_file = tmp_path / "output" / "control" / "prompt_pack.json"
    prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
    
    return tmp_path


@pytest.fixture
def runner(tmp_project: Path) -> ControlledActionRunner:
    def generate_frames(payload: dict) -> dict:
        return {"handler": "generate_frames", "frames": 10, "executed": True, "status": "executed"}

    def continue_generation(payload: dict) -> dict:
        return {"handler": "continue_generation", "frames": 5, "executed": True, "status": "executed"}

    def assemble_scene_video(payload: dict) -> dict:
        return {"handler": "assemble_scene_video", "output": "scene.mp4", "executed": True, "status": "executed"}

    def synthesize_and_mux_audio(payload: dict) -> dict:
        return {"handler": "synthesize_and_mux_audio", "wav": "scene.wav", "executed": True, "status": "executed"}

    def assemble_episode(payload: dict) -> dict:
        return {"handler": "assemble_episode", "output": "episode.mp4", "executed": True, "status": "executed"}

    def run_qa(payload: dict) -> dict:
        return {"handler": "run_qa", "passed": True, "executed": True, "status": "executed"}

    def create_brief(payload: dict) -> dict:
        return {"handler": "create_brief", "path": "brief.md", "executed": True, "status": "executed"}

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()  # MK-CTRL21R
    handlers = {
        "create_brief": create_brief,
        "generate_frames": generate_frames,
        "continue_generation": continue_generation,
        "assemble_scene_video": assemble_scene_video,
        "synthesize_and_mux_audio": synthesize_and_mux_audio,
        "assemble_episode": assemble_episode,
        "run_qa": run_qa,
    }
    return ControlledActionRunner(controller, gate, handlers, planner=planner)


# ── 1. allowed action executes exactly one matching handler ─────────

def test_allowed_action_executes_handler(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.allowed is True
    assert r.executed is True
    assert r.executed_action == "generate_frames"
    assert r.handler_result == {"handler": "generate_frames", "frames": 10, "executed": True, "status": "executed"}


# ── 2. denied action executes no handler ───────────────────────────

def test_denied_action_does_not_execute(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "assemble_scene_video")
    assert r.allowed is False
    assert r.executed is False
    assert r.executed_action is None
    assert r.handler_result is None


# ── 3. blocked report executes no handler ────────────────────────────

def test_blocked_report_no_execution(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    # Create zero-byte scene MP4 to trigger blocked state
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.allowed is False
    assert r.executed is False
    assert "blocked" in r.reason.lower()


# ── 4. done report + none ───────────────────────────────────────────

def test_done_none_allowed_no_execution(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ep_dir = tmp_project / "output/episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "ep01_final.mp4").write_bytes(b"fake")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    qa = tmp_project / "output/qa_passed"
    qa.write_text("ok", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "none")
    assert r.allowed is True
    assert r.executed is False
    assert "not an executable action" in r.reason


# ── 5. allowed action with missing handler ──────────────────────────

def test_allowed_missing_handler_raises(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\ndialogue: hello\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    # Remove synthesize_and_mux_audio handler
    runner.handlers.pop("synthesize_and_mux_audio", None)
    with pytest.raises(RuntimeError) as exc_info:
        runner.run_one("ep01", "shot01", "synthesize_and_mux_audio")
    assert "no handler is registered" in str(exc_info.value)


# ── 6. handler exception propagates clearly ─────────────────────────

def test_handler_exception_propagates(tmp_project: Path) -> None:
    def bad_handler(payload: dict) -> dict:
        raise ValueError("boom")

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    runner = ControlledActionRunner(controller, gate, {
        "generate_frames": bad_handler,
    })
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc_info:
        runner.run_one("ep01", "shot01", "generate_frames")
    assert "boom" in str(exc_info.value)


# ── 7. runner returns structured ActionRunResult ─────────────────

def test_returns_structured_result(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert isinstance(r, ActionRunResult)
    assert r.episode_id == "ep01"
    assert r.shot_id == "shot01"
    assert r.requested_action == "generate_frames"
    assert r.current_state == "ready_for_generation"
    assert r.expected_next_action == "generate_frames"


# ── 8. runner does not mutate report ────────────────────────────────

def test_runner_does_not_mutate_report(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    report_before = runner.controller.inspect("ep01", "shot01")
    original_state = report_before.current_state
    runner.run_one("ep01", "shot01", "generate_frames")
    report_after = runner.controller.inspect("ep01", "shot01")
    assert report_after.current_state == original_state


# ── 9. run_next executes next action ────────────────────────────────

def test_run_next_executes_next_action(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_next("ep01", "shot01")
    assert r.allowed is True
    assert r.executed is True
    assert r.executed_action == "generate_frames"


# ── 10. run_next with done state does nothing ──────────────────────

def test_run_next_done_no_execution(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ep_dir = tmp_project / "output/episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "ep01_final.mp4").write_bytes(b"fake")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    qa = tmp_project / "output/qa_passed"
    qa.write_text("ok", encoding="utf-8")
    r = runner.run_next("ep01", "shot01")
    assert r.executed is False
    assert r.reason == "next action is 'none' — nothing to execute"


# ── 11. run_next blocked state ──────────────────────────────────────

def test_run_next_blocked_denied(runner: ControlledActionRunner, tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"")
    r = runner.run_next("ep01", "shot01")
    assert r.allowed is False
    assert r.executed is False
    assert "blocked" in r.reason.lower()


# ── 12. one request -> one execution only ────────────────────────────

def test_single_execution_only(runner: ControlledActionRunner, tmp_project: Path) -> None:
    call_count = {"count": 0}

    def counting_handler(payload: dict) -> dict:
        call_count["count"] += 1
        return {"count": call_count["count"]}

    runner.handlers["generate_frames"] = counting_handler
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.handler_result == {"count": 1}
    assert call_count["count"] == 1


# ── 13. MK-CTRL10R: handler execution records control_executed=true ───────

def test_handler_execution_records_control_executed_true(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """Handler execution should record control_executed=true."""
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.control_executed is True


# ── 14. MK-CTRL10R: dry_validate result records production_executed=false ──

def test_dry_validate_records_production_executed_false(tmp_project: Path) -> None:
    """Handler returning executed=false should record production_executed=false."""
    def dry_validate_handler(payload: dict) -> dict:
        return {"status": "validated", "executed": False}

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    runner = ControlledActionRunner(controller, gate, {
        "generate_frames": dry_validate_handler,
    })
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.control_executed is True
    assert r.production_executed is False
    assert r.handler_status == "validated"


# ── 15. MK-CTRL10R: real executed result records production_executed=true ──

def test_real_executed_records_production_executed_true(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """Handler returning executed=true should record production_executed=true."""
    def real_executed_handler(payload: dict) -> dict:
        return {"status": "executed", "executed": True}
    
    runner.handlers["generate_frames"] = real_executed_handler
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "generate_frames")
    assert r.control_executed is True
    assert r.production_executed is True
    assert r.handler_status == "executed"


# ── 16. MK-CTRL10R: denied action records control_executed=false ────────

def test_denied_action_records_control_executed_false(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """Denied action should record control_executed=false."""
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    r = runner.run_one("ep01", "shot01", "assemble_scene_video")
    assert r.control_executed is False
    assert r.production_executed is False
    assert r.handler_status is None


# ── 17. MK-CTRL10R: failed handler records control_executed=true ─────────

def test_failed_handler_records_control_executed_true(tmp_project: Path) -> None:
    """Failed handler should record control_executed=true and handler_status=failed."""
    from app.control.ledger import ShotLedgerStorage
    
    def failing_handler(payload: dict) -> dict:
        raise ValueError("handler failed")

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger_root = tmp_project / "output/control"
    ledger = ShotLedgerStorage(ledger_root)
    runner = ControlledActionRunner(controller, gate, {
        "generate_frames": failing_handler,
    }, ledger=ledger)
    
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    with pytest.raises(ValueError):
        runner.run_one("ep01", "shot01", "generate_frames")
    
    # Check ledger record for action_failed
    ledger_data = ledger.load("ep01", "shot01")
    failed_records = [r for r in ledger_data.records if r.event_type == "action_failed"]
    assert len(failed_records) == 1
    rec = failed_records[0]
    assert rec.control_executed is True
    assert rec.production_executed is None
    assert rec.handler_status == "failed"


# ── 18. MK-CTRL10R: backward-compatible ledger shape ──────────────────

def test_ledger_backward_compatible(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """Ledger records should maintain backward-compatible shape."""
    from app.control.ledger import ShotLedgerStorage

    ledger_root = tmp_project / "output/control"
    ledger = ShotLedgerStorage(ledger_root)
    runner_with_ledger = ControlledActionRunner(
        runner.controller, runner.gate, runner.handlers, ledger=ledger
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    runner_with_ledger.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    assert ledger_data.episode_id == "ep01"
    assert ledger_data.shot_id == "shot01"
    assert len(ledger_data.records) > 0

    # Check that old fields still exist
    for rec in ledger_data.records:
        assert rec.timestamp is not None
        assert rec.event_type is not None
        assert rec.episode_id == "ep01"
        assert rec.shot_id == "shot01"


# ── 19. MK-CTRL11R: gate_decision does not contain handler execution metadata ──

def test_gate_decision_no_handler_metadata(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """gate_decision record should not contain handler execution metadata."""
    from app.control.ledger import ShotLedgerStorage

    ledger_root = tmp_project / "output/control"
    ledger = ShotLedgerStorage(ledger_root)
    runner_with_ledger = ControlledActionRunner(
        runner.controller, runner.gate, runner.handlers, ledger=ledger
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    runner_with_ledger.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    gate_records = [r for r in ledger_data.records if r.event_type == "gate_decision"]
    assert len(gate_records) == 1
    rec = gate_records[0]
    assert rec.control_executed is None
    assert rec.production_executed is None
    assert rec.handler_status is None


# ── 20. MK-CTRL11R: action_executed contains handler execution metadata ─────

def test_action_executed_has_handler_metadata(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """action_executed record should contain handler execution metadata."""
    from app.control.ledger import ShotLedgerStorage

    # Update handler to return executed field
    def generate_frames_with_executed(payload: dict) -> dict:
        return {"handler": "generate_frames", "frames": 10, "executed": True, "status": "executed"}

    ledger_root = tmp_project / "output/control"
    ledger = ShotLedgerStorage(ledger_root)
    runner_with_ledger = ControlledActionRunner(
        runner.controller, runner.gate, {"generate_frames": generate_frames_with_executed}, ledger=ledger
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    runner_with_ledger.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    rec = action_records[0]
    assert rec.control_executed is True
    assert rec.production_executed is True
    assert rec.handler_status == "executed"


# ── 21. MK-CTRL11R: ledger event sequence is correct ───────────────────────

def test_ledger_event_sequence_correct(runner: ControlledActionRunner, tmp_project: Path) -> None:
    """Ledger should have correct event sequence: inspect, gate_decision, action_executed."""
    from app.control.ledger import ShotLedgerStorage

    ledger_root = tmp_project / "output/control"
    ledger = ShotLedgerStorage(ledger_root)
    runner_with_ledger = ControlledActionRunner(
        runner.controller, runner.gate, runner.handlers, ledger=ledger
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    runner_with_ledger.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    event_types = [r.event_type for r in ledger_data.records]
    assert event_types == ["inspect", "gate_decision", "action_executed", "state_transition"]
