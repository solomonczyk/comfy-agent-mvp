"""Tests for MK-CTRL4 — ShotLedgerStorage and ledger integration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.action_runner import ControlledActionRunner
from app.control.gate import ShotExecutionGate
from app.control.ledger import ShotLedgerRecord, ShotLedgerStorage
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

    def assemble_episode(payload: dict) -> dict:
        return {"handler": "assemble_episode", "output": "episode.mp4", "executed": True, "status": "executed"}

    def bad_handler(payload: dict) -> dict:
        raise ValueError("handler failed")

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()  # MK-CTRL21R
    handlers = {
        "generate_frames": generate_frames,
        "assemble_episode": assemble_episode,
        "bad_handler": bad_handler,
    }
    return controller, gate, handlers, planner


# ── 1. load on missing ledger returns empty ──────────────────────────

def test_load_missing_returns_empty(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    ledger = store.load("ep01", "shot01")
    assert ledger.episode_id == "ep01"
    assert ledger.shot_id == "shot01"
    assert ledger.records == []
    assert store.exists("ep01", "shot01") is False


# ── 2. append creates new ledger file ─────────────────────────────────

def test_append_creates_file(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    record = ShotLedgerRecord(
        timestamp="2024-01-01T00:00:00",
        episode_id="ep01", shot_id="shot01",
        event_type="inspect",
        current_state="ready_for_generation",
    )
    path = store.append("ep01", "shot01", record)
    assert path.exists()
    assert store.exists("ep01", "shot01") is True


# ── 3. append preserves previous records ──────────────────────────────

def test_append_preserves_records(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    r1 = ShotLedgerRecord(
        timestamp="2024-01-01T00:00:00",
        episode_id="ep01", shot_id="shot01",
        event_type="inspect",
        current_state="ready_for_generation",
    )
    r2 = ShotLedgerRecord(
        timestamp="2024-01-01T00:00:01",
        episode_id="ep01", shot_id="shot01",
        event_type="gate_decision",
        allowed=True,
        current_state="ready_for_generation",
    )
    store.append("ep01", "shot01", r1)
    store.append("ep01", "shot01", r2)
    ledger = store.load("ep01", "shot01")
    assert len(ledger.records) == 2
    assert ledger.records[0].event_type == "inspect"
    assert ledger.records[1].event_type == "gate_decision"


# ── 4. ledger JSON is human-readable ────────────────────────────────────

def test_ledger_json_readable(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    record = ShotLedgerRecord(
        timestamp="2024-01-01T00:00:00",
        episode_id="ep01", shot_id="shot01",
        event_type="inspect",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
    )
    store.append("ep01", "shot01", record)
    path = store.ledger_path("ep01", "shot01")
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["episode_id"] == "ep01"
    assert data["shot_id"] == "shot01"
    assert len(data["records"]) == 1
    assert data["records"][0]["event_type"] == "inspect"
    # Verify indent=2 (human readable)
    assert "\n" in text


# ── 5. runner with ledger writes inspect + gate + executed ──────────

def test_runner_writes_ledger_on_success(tmp_project: Path, runner: Any) -> None:
    controller, gate, handlers, planner = runner
    store = ShotLedgerStorage(tmp_project)
    runner_obj = ControlledActionRunner(controller, gate, handlers, ledger=store, planner=planner)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    r = runner_obj.run_one("ep01", "shot01", "generate_frames")
    assert r.allowed is True
    assert r.executed is True

    ledger = store.load("ep01", "shot01")
    assert len(ledger.records) >= 3  # inspect, gate_decision, action_executed
    types = [rec.event_type for rec in ledger.records]
    assert "inspect" in types
    assert "gate_decision" in types
    assert "action_executed" in types
    # Verify action_executed has handler_result
    executed = [r for r in ledger.records if r.event_type == "action_executed"][0]
    assert executed.handler_result == {"handler": "generate_frames", "frames": 10, "executed": True, "status": "executed"}


# ── 6. denied action writes inspect + denied, no handler ────────────

def test_denied_writes_ledger_no_handler(tmp_project: Path, runner: Any) -> None:
    controller, gate, handlers, planner = runner
    store = ShotLedgerStorage(tmp_project)
    runner_obj = ControlledActionRunner(controller, gate, handlers, ledger=store, planner=planner)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    r = runner_obj.run_one("ep01", "shot01", "assemble_scene_video")
    assert r.allowed is False
    assert r.executed is False

    ledger = store.load("ep01", "shot01")
    types = [rec.event_type for rec in ledger.records]
    assert "inspect" in types
    assert "action_denied" in types
    assert "action_executed" not in types


# ── 7. handler failure writes action_failed and re-raises ────────────

def test_failure_writes_failed_and_reraises(tmp_project: Path, runner: Any) -> None:
    def boom_handler(payload: dict) -> dict:
        raise ValueError("boom")

    controller, gate, handlers, planner = runner
    handlers["generate_frames"] = boom_handler  # replace with failing handler
    store = ShotLedgerStorage(tmp_project)
    runner_obj = ControlledActionRunner(controller, gate, handlers, ledger=store, planner=planner)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    with pytest.raises(ValueError, match="boom"):
        runner_obj.run_one("ep01", "shot01", "generate_frames")

    ledger = store.load("ep01", "shot01")
    types = [rec.event_type for rec in ledger.records]
    assert "inspect" in types
    assert "gate_decision" in types
    assert "action_failed" in types
    failed = [r for r in ledger.records if r.event_type == "action_failed"][0]
    assert failed.success is False
    assert failed.reason == "handler raised an exception"


# ── 8. ledger path matches expected naming ──────────────────────────

def test_ledger_path_naming(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    path = store.ledger_path("ep01", "shot01")
    assert path.name == "ep01_shot01_ledger.json"
    assert "output" in str(path)
    assert "control" in str(path)


# ── 9. multiple run_one calls append records ────────────────────────

def test_multiple_runs_append_records(tmp_project: Path, runner: Any) -> None:
    controller, gate, handlers, planner = runner
    store = ShotLedgerStorage(tmp_project)
    runner_obj = ControlledActionRunner(controller, gate, handlers, ledger=store, planner=planner)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    runner_obj.run_one("ep01", "shot01", "generate_frames")
    runner_obj.run_one("ep01", "shot01", "assemble_scene_video")

    ledger = store.load("ep01", "shot01")
    assert len(ledger.records) >= 4  # 2 inspects + 2 gate decisions (1 denied) + 1 executed
    types = [rec.event_type for rec in ledger.records]
    assert types.count("inspect") == 2


# ── 10. ledger serialization round-trip ───────────────────────────────

def test_serialization_round_trip(tmp_project: Path) -> None:
    store = ShotLedgerStorage(tmp_project)
    record = ShotLedgerRecord(
        timestamp="2024-01-01T00:00:00",
        episode_id="ep01", shot_id="shot01",
        event_type="action_executed",
        requested_action="generate_frames",
        allowed=True,
        executed=True,
        success=True,
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reason="handler executed successfully",
        handler_result={"frames": 10},
    )
    store.append("ep01", "shot01", record)
    ledger = store.load("ep01", "shot01")
    rec = ledger.records[0]
    assert rec.event_type == "action_executed"
    assert rec.handler_result == {"frames": 10}
    assert rec.allowed is True
    assert rec.executed is True
    assert rec.success is True


# ── 11. runner without ledger does not crash ─────────────────────────

def test_runner_without_ledger_no_crash(tmp_project: Path, runner: Any) -> None:
    controller, gate, handlers, planner = runner
    runner_obj = ControlledActionRunner(controller, gate, handlers, ledger=None, planner=planner)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    r = runner_obj.run_one("ep01", "shot01", "generate_frames")
    assert r.allowed is True
    assert r.executed is True
    # No ledger file should exist
    store = ShotLedgerStorage(tmp_project)
    assert not store.exists("ep01", "shot01")
