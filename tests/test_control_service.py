"""Tests for MK-CTRL8 — ShotControlService."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.gate import ShotExecutionGate
from app.control.ledger import ShotLedgerStorage
from app.control.service import ShotControlService
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
def handlers() -> dict[str, Any]:
    def generate_frames(payload: dict) -> dict:
        return {"handler": "generate_frames", "frames": 10, "executed": True, "status": "executed"}

    def assemble_episode(payload: dict) -> dict:
        return {"handler": "assemble_episode", "output": "episode.mp4", "executed": True, "status": "executed"}

    def bad_handler(payload: dict) -> dict:
        raise ValueError("handler failed")

    return {
        "generate_frames": generate_frames,
        "assemble_episode": assemble_episode,
        "bad_handler": bad_handler,
    }


def make_service(tmp_project: Path, handlers: dict[str, Any]) -> ShotControlService:
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    return ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handlers=handlers,
        ledger_root=tmp_project,
    )


# ── 1. dry_run returns ShotControlResponse ─────────────────────────────

def test_dry_run_returns_response(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)
    resp = svc.dry_run("ep01", "shot01", "generate_frames")
    assert resp.episode_id == "ep01"
    assert resp.shot_id == "shot01"
    assert resp.mode == "dry_run"


# ── 2. dry_run does not call handler ─────────────────────────────────

def test_dry_run_no_handler_call(tmp_project: Path, handlers: Any) -> None:
    call_count = 0

    def counting_handler(payload: dict) -> dict:
        nonlocal call_count
        call_count += 1
        return {"called": True}

    h = dict(handlers)
    h["generate_frames"] = counting_handler
    svc = make_service(tmp_project, h)

    svc.dry_run("ep01", "shot01", "generate_frames")
    assert call_count == 0


# ── 3. dry_run does not create ledger file ───────────────────────────

def test_dry_run_no_ledger_file(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)
    svc.dry_run("ep01", "shot01", "generate_frames")
    store = ShotLedgerStorage(tmp_project)
    assert not store.exists("ep01", "shot01")


# ── 4. execute allowed action calls exactly one handler ──────────────

def test_execute_allowed_calls_one_handler(tmp_project: Path, handlers: Any) -> None:
    call_count = 0

    def counting_handler(payload: dict) -> dict:
        nonlocal call_count
        call_count += 1
        return {"called": True}

    h = dict(handlers)
    h["generate_frames"] = counting_handler
    svc = make_service(tmp_project, h)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    resp = svc.execute("ep01", "shot01", "generate_frames")
    assert resp.success is True
    assert call_count == 1


# ── 5. execute allowed action creates ledger file ─────────────────────

def test_execute_allowed_creates_ledger(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    svc.execute("ep01", "shot01", "generate_frames")
    store = ShotLedgerStorage(tmp_project)
    assert store.exists("ep01", "shot01")


# ── 6. execute allowed appends inspect + gate + executed ───────────────

def test_execute_allowed_records_events(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    resp = svc.execute("ep01", "shot01", "generate_frames")
    assert resp.success is True

    store = ShotLedgerStorage(tmp_project)
    ledger = store.load("ep01", "shot01")
    types = [r.event_type for r in ledger.records]
    assert "inspect" in types
    assert "gate_decision" in types
    assert "action_executed" in types


# ── 7. execute denied action does not call handler ─────────────────────

def test_execute_denied_no_handler(tmp_project: Path, handlers: Any) -> None:
    call_count = 0

    def counting_handler(payload: dict) -> dict:
        nonlocal call_count
        call_count += 1
        return {"called": True}

    h = dict(handlers)
    h["assemble_episode"] = counting_handler
    svc = make_service(tmp_project, h)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    resp = svc.execute("ep01", "shot01", "assemble_episode")
    assert resp.success is False
    assert call_count == 0


# ── 8. execute denied records denial via ledger ────────────────────────

def test_execute_denied_records_denial(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    resp = svc.execute("ep01", "shot01", "assemble_episode")
    assert resp.success is False

    store = ShotLedgerStorage(tmp_project)
    ledger = store.load("ep01", "shot01")
    types = [r.event_type for r in ledger.records]
    assert "inspect" in types
    assert "action_denied" in types
    assert "action_executed" not in types


# ── 9. handler failure writes action_failed and re-raises ────────────

def test_execute_failure_writes_failed_and_raises(tmp_project: Path, handlers: Any) -> None:
    h = dict(handlers)
    h["generate_frames"] = handlers["bad_handler"]
    svc = make_service(tmp_project, h)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    with pytest.raises(ValueError, match="handler failed"):
        svc.execute("ep01", "shot01", "generate_frames")

    store = ShotLedgerStorage(tmp_project)
    ledger = store.load("ep01", "shot01")
    types = [r.event_type for r in ledger.records]
    assert "inspect" in types
    assert "gate_decision" in types
    assert "action_failed" in types
    failed = [r for r in ledger.records if r.event_type == "action_failed"][0]
    assert failed.success is False
    assert failed.reason == "handler raised an exception"


# ── 10. multiple execute calls append to same ledger ─────────────────

def test_multiple_executes_append(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    svc.execute("ep01", "shot01", "generate_frames")
    svc.execute("ep01", "shot01", "assemble_episode")

    store = ShotLedgerStorage(tmp_project)
    ledger = store.load("ep01", "shot01")
    types = [r.event_type for r in ledger.records]
    assert types.count("inspect") == 2


# ── 11. service uses output/control naming convention ──────────────────

def test_service_ledger_path_convention(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)
    store = ShotLedgerStorage(tmp_project)
    path = store.ledger_path("ep01", "shot01")
    assert path.name == "ep01_shot01_ledger.json"
    assert "output" in str(path)
    assert "control" in str(path)


# ── 12. service exposes ledger_enabled=true ──────────────────────────

def test_service_ledger_enabled_true(tmp_project: Path, handlers: Any) -> None:
    svc = make_service(tmp_project, handlers)
    resp = svc.dry_run("ep01", "shot01", "generate_frames")
    assert resp.ledger_enabled is True

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    resp2 = svc.execute("ep01", "shot01", "generate_frames")
    assert resp2.ledger_enabled is True


# ── 13. no direct ComfyUI / ffmpeg / TTS imports or calls ────────────

def test_service_layer_no_production_systems() -> None:
    import ast
    import inspect

    from app.control import service

    source = inspect.getsource(service)
    tree = ast.parse(source)

    forbidden = {"comfyui", "ffmpeg", "tts", "comfy"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.lower() not in forbidden
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            assert not any(f in mod for f in forbidden)
