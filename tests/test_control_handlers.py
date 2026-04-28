"""Tests for MK-CTRL9 — HandlerRegistry and safe mock handlers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.gate import ShotExecutionGate
from app.control.handlers import (
    HandlerRegistry,
    assemble_scene_handler,
    attach_audio_handler,
    build_default_handler_registry,
    final_render_handler,
    generate_frames_handler,
    qa_check_handler,
)
from app.control.ledger import ShotLedgerStorage
from app.control.service import ShotControlService
from app.control.shot_controller import ShotController


# ── registry basics ──────────────────────────────────────────────────

def test_registry_registers_handler() -> None:
    reg = HandlerRegistry()
    reg.register("test", lambda e, s, r: {}, enabled=True)
    assert "test" in reg.to_dict()


def test_registry_get_returns_callable() -> None:
    reg = HandlerRegistry()
    fn = lambda e, s, r: {}
    reg.register("test", fn, enabled=True)
    assert reg.get("test") is fn


def test_registry_unknown_raises() -> None:
    reg = HandlerRegistry()
    with pytest.raises(RuntimeError, match="No handler registered"):
        reg.get("missing")


def test_registry_disabled_by_default() -> None:
    reg = HandlerRegistry()
    reg.register("test", lambda e, s, r: {})
    assert reg.is_enabled("test") is False


def test_registry_enabled_handler_can_be_retrieved() -> None:
    reg = HandlerRegistry()
    fn = lambda e, s, r: {}
    reg.register("test", fn, enabled=True)
    assert reg.is_enabled("test") is True
    assert reg.get("test") is fn


def test_registry_enabled_handlers_dict() -> None:
    reg = HandlerRegistry()
    fn = lambda e, s, r: {}
    reg.register("on", fn, enabled=True)
    reg.register("off", fn, enabled=False)
    enabled = reg.enabled_handlers()
    assert "on" in enabled
    assert "off" not in enabled


# ── default registry contents ────────────────────────────────────────

def test_default_registry_has_generate_frames() -> None:
    reg = build_default_handler_registry()
    assert "generate_frames" in reg.to_dict()


def test_default_registry_has_assemble_scene() -> None:
    reg = build_default_handler_registry()
    assert "assemble_scene_video" in reg.to_dict()


def test_default_registry_has_attach_audio() -> None:
    reg = build_default_handler_registry()
    assert "synthesize_and_mux_audio" in reg.to_dict()


def test_default_registry_has_final_render() -> None:
    reg = build_default_handler_registry()
    assert "assemble_episode" in reg.to_dict()


def test_default_registry_has_qa_check() -> None:
    reg = build_default_handler_registry()
    assert "run_qa" in reg.to_dict()


# ── mock handler outputs ─────────────────────────────────────────────

def test_mock_generate_frames_result() -> None:
    result = generate_frames_handler("ep01", "shot01", None)
    assert result["handler"] == "generate_frames"
    assert result["status"] == "mocked"
    assert result["would_execute"] is True
    assert result["received"]["episode_id"] == "ep01"


def test_mock_assemble_scene_result() -> None:
    result = assemble_scene_handler("ep01", "shot01", None)
    assert result["handler"] == "assemble_scene_video"
    assert result["status"] == "mocked"


def test_mock_attach_audio_result() -> None:
    result = attach_audio_handler("ep01", "shot01", None)
    assert result["handler"] == "synthesize_and_mux_audio"
    assert result["status"] == "mocked"


def test_mock_final_render_result() -> None:
    result = final_render_handler("ep01", "shot01", None)
    assert result["handler"] == "assemble_episode"
    assert result["status"] == "mocked"


def test_mock_qa_result() -> None:
    result = qa_check_handler("ep01", "shot01", None)
    assert result["handler"] == "run_qa"
    assert result["status"] == "mocked"


# ── registry serialization ───────────────────────────────────────────

def test_registry_to_dict_is_json_serializable() -> None:
    reg = build_default_handler_registry(enable_mock_handlers=True)
    d = reg.to_dict()
    text = json.dumps(d)
    parsed = json.loads(text)
    assert parsed["generate_frames"]["enabled"] is True


# ── disabled handlers do not execute ─────────────────────────────────

def test_disabled_handler_not_in_enabled_dict() -> None:
    reg = build_default_handler_registry(enable_mock_handlers=False)
    assert reg.enabled_handlers() == {}


# ── integration with service ─────────────────────────────────────────

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    return tmp_path


def test_service_execute_with_enabled_mock_writes_ledger(tmp_project: Path) -> None:
    reg = build_default_handler_registry(enable_mock_handlers=True)
    svc = ShotControlService(
        controller=ShotController(tmp_project),
        gate=ShotExecutionGate(),
        planner=ActionPlanBuilder(),
        handler_registry=reg,
        ledger_root=tmp_project,
    )

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
    executed = [r for r in ledger.records if r.event_type == "action_executed"][0]
    assert executed.handler_result["handler"] == "generate_frames"
    assert executed.handler_result["status"] == "mocked"


def test_service_execute_with_disabled_mock_does_not_execute(tmp_project: Path) -> None:
    reg = build_default_handler_registry(enable_mock_handlers=False)
    svc = ShotControlService(
        controller=ShotController(tmp_project),
        gate=ShotExecutionGate(),
        planner=ActionPlanBuilder(),
        handler_registry=reg,
        ledger_root=tmp_project,
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    # Allowed by gate but no enabled handler -> runner raises RuntimeError
    with pytest.raises(RuntimeError, match="no handler is registered"):
        svc.execute("ep01", "shot01", "generate_frames")


# ── no forbidden imports ─────────────────────────────────────────────

def test_handlers_layer_no_production_systems() -> None:
    import ast
    import inspect

    from app.control import handlers as handlers_mod

    source = inspect.getsource(handlers_mod)
    tree = ast.parse(source)

    forbidden = {"comfyui", "ffmpeg", "tts", "comfy"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.lower() not in forbidden
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            assert not any(f in mod for f in forbidden)
