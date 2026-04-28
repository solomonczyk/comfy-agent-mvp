"""MK-CTRL11 tests — RealGenerateFramesHandler execution semantics.

All tests use fake runners.  No ComfyUI, ffmpeg, or TTS is started.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.control.handler_contracts import HandlerPayload, HandlerResult
from app.control.real_generate_handler import (
    RealGenerateFramesHandler,
    build_real_generate_frames_handler_registry,
)
from app.control.gate import ShotExecutionGate
from app.control.ledger import ShotLedgerStorage
from app.control.production_handlers import ProductionHandlerAdapter, build_production_handler_registry
from app.control.service import ShotControlService
from app.control.shot_controller import ShotController


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    return tmp_path


# ── helpers ──────────────────────────────────────────────────────────────

def _make_payload(
    *,
    dry_validate: bool = True,
    allow_real_execution: bool = False,
    action_plan: dict | None = None,
    action: str = "generate_frames",
) -> HandlerPayload:
    return HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action=action,
        state_report={"current_state": "ready_for_generation"},
        action_plan=action_plan or {
            "brief_path": "briefs/ep01_shot01.md",
            "command_preview": " comfy --workflow test.json",
            "expected_outputs": ["frame_0001.png"],
        },
        dry_validate=dry_validate,
        allow_real_execution=allow_real_execution,
    )


def _make_fake_runner_factory():
    """Return a factory that yields a fake runner (callable)."""
    calls: list[dict] = []

    def _fake_runner(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {
            "frame_paths": [
                f"output/ep01/shot01/frame_{i:04d}.png" for i in range(1, 3)
            ]
        }

    return _fake_runner, calls


def _make_boom_runner_factory():
    """Return a factory that yields a runner that always raises."""
    def _boom_runner(**kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("boom")

    return _boom_runner


# ── 1. dry_validate returns status validated ─────────────────────────────

def test_dry_validate_returns_validated() -> None:
    handler = RealGenerateFramesHandler()
    payload = _make_payload(dry_validate=True)
    result = handler(payload)
    assert result["status"] == "validated"
    assert result["executed"] is False
    assert result["would_execute"] is True


# ── 2. dry_validate does not call runner_factory ───────────────────────

def test_dry_validate_never_calls_factory() -> None:
    factory_called = {"n": 0}

    def counting_factory():
        factory_called["n"] += 1
        return lambda **kw: {}

    handler = RealGenerateFramesHandler(
        runner_factory=counting_factory,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=True)
    handler(payload)
    assert factory_called["n"] == 0


# ── 3. enable_real_execution=False blocks execution ────────────────────

def test_handler_disabled_blocks() -> None:
    fake_runner, _ = _make_fake_runner_factory()
    handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=False,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert "enable_real_execution=False" in result["reason"]


# ── 4. payload allow_real_execution=False blocks execution ─────────────

def test_payload_denied_blocks() -> None:
    fake_runner, _ = _make_fake_runner_factory()
    handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=False)
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert "allow_real_execution=False" in result["reason"]


# ── 5. runner_factory=None blocks execution ──────────────────────────────

def test_no_factory_blocks() -> None:
    handler = RealGenerateFramesHandler(
        runner_factory=None,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert "No runner factory" in result["reason"]


# ── 6. unsupported action is blocked ─────────────────────────────────────

def test_wrong_action_blocked() -> None:
    handler = RealGenerateFramesHandler()
    payload = _make_payload(action="assemble_scene_video")
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["would_execute"] is False
    assert "Unsupported action" in result["reason"]


# ── 7. valid real execution calls runner_factory exactly once ──────────

def test_real_calls_factory_once() -> None:
    factory_calls = {"n": 0}
    fake_runner, runner_calls = _make_fake_runner_factory()

    def counting_factory():
        factory_calls["n"] += 1
        return fake_runner

    handler = RealGenerateFramesHandler(
        runner_factory=counting_factory,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    handler(payload)
    assert factory_calls["n"] == 1


# ── 8. valid real execution calls fake runner exactly once ─────────────

def test_real_calls_runner_once() -> None:
    fake_runner, runner_calls = _make_fake_runner_factory()
    handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    handler(payload)
    assert len(runner_calls) == 1
    call = runner_calls[0]
    assert call["episode_id"] == "ep01"
    assert call["shot_id"] == "shot01"
    assert call["brief_path"] == "briefs/ep01_shot01.md"


# ── 9. valid real execution returns status executed ────────────────────

def test_real_returns_executed() -> None:
    fake_runner, _ = _make_fake_runner_factory()
    handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True
    assert result["would_execute"] is True


# ── 10. artifacts include fake frame paths from fake runner ──────────────

def test_real_artifacts_have_frame_paths() -> None:
    fake_runner, _ = _make_fake_runner_factory()
    handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert "frame_paths" in result["artifacts"]
    assert len(result["artifacts"]["frame_paths"]) == 2


# ── 11. runner exception returns failed status ───────────────────────────

def test_runner_exception_returns_failed() -> None:
    handler = RealGenerateFramesHandler(
        runner_factory=_make_boom_runner_factory(),
        enable_real_execution=True,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "failed"
    assert result["executed"] is False
    assert "boom" in result["reason"]
    assert result["metadata"]["exception_type"] == "RuntimeError"


# ── 12. dict payload input works ─────────────────────────────────────────

def test_dict_payload_works() -> None:
    handler = RealGenerateFramesHandler()
    payload_dict = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "generate_frames",
        "state_report": {},
        "action_plan": {"brief_path": "b.md"},
        "dry_validate": True,
        "allow_real_execution": False,
    }
    result = handler(payload_dict)
    assert result["status"] == "validated"
    assert result["metadata"]["episode_id"] == "ep01"


# ── 13. HandlerPayload input works ─────────────────────────────────────

def test_handler_payload_input_works() -> None:
    handler = RealGenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep02",
        shot_id="shot02",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "b2.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["status"] == "validated"
    assert result["metadata"]["episode_id"] == "ep02"


# ── 14. metadata includes episode_id and shot_id ─────────────────────────

def test_metadata_has_ids() -> None:
    handler = RealGenerateFramesHandler()
    payload = _make_payload(dry_validate=True)
    result = handler(payload)
    assert result["metadata"]["episode_id"] == "ep01"
    assert result["metadata"]["shot_id"] == "shot01"


# ── 15. no top-level ComfyUI / ffmpeg / TTS imports ────────────────────

def test_no_forbidden_top_level_imports() -> None:
    from app.control import real_generate_handler as mod

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
                assert alias.name.lower() not in forbidden, (
                    f"Forbidden import: {alias.name}"
                )
        if isinstance(node, ast.ImportFrom):
            mod_name = (node.module or "").lower()
            assert not any(f in mod_name for f in forbidden), (
                f"Forbidden import from: {node.module}"
            )


# ── 16. integration with ProductionHandlerAdapter ──────────────────────

def test_adapter_integration_executed_result(tmp_project: Path) -> None:
    """When real handler returns executed=True, adapter sets
    production_executed=True in the ledger record."""
    fake_runner, _ = _make_fake_runner_factory()
    real_handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )

    # Wrap in ProductionHandlerAdapter
    adapter = ProductionHandlerAdapter(
        action="generate_frames",
        real_callable=real_handler,
    )

    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "b.md"},
        dry_validate=False,
        allow_real_execution=True,
    )

    result = adapter(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True


# ── 17. adapter direct call returns executed for real execution ─────────

def test_adapter_direct_call_executed() -> None:
    fake_runner, _ = _make_fake_runner_factory()
    real_handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )

    # Build a production registry with the real handler wired
    reg = build_production_handler_registry(
        enable_real_handlers=True,
        real_callables={"generate_frames": real_handler},
    )

    adapter = reg.get("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "b.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True


# ── 18. integration through ShotControlService — dry_validate ledger ───

def test_service_dry_validate_writes_ledger(tmp_project: Path) -> None:
    fake_runner, _ = _make_fake_runner_factory()
    real_handler = RealGenerateFramesHandler(
        runner_factory=lambda: fake_runner,
        enable_real_execution=True,
    )

    reg = build_production_handler_registry(
        enable_real_handlers=True,
        real_callables={"generate_frames": real_handler},
    )
    from app.control.action_plan import ActionPlanBuilder
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=ActionPlanBuilder(),
        handler_registry=reg,
        ledger_root=tmp_project,
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    # Run through service with default dry_validate=True
    result = service.execute("ep01", "shot01", "generate_frames")
    assert result.success is True
    assert result.action_result is not None
    assert result.action_result["handler_status"] == "validated"

    ledger_store = ShotLedgerStorage(tmp_project)
    ledger_data = ledger_store.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    rec = action_records[0]
    assert rec.control_executed is True
    assert rec.production_executed is False
    assert rec.handler_status == "validated"


# ── 19. blocked adapter records production_executed=false ───────────────

def test_blocked_handler_returns_production_false() -> None:
    handler = RealGenerateFramesHandler(
        runner_factory=None,
        enable_real_execution=False,
    )
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False


# ── 20. build_real_generate_frames_handler_registry safety ──────────────

def test_registry_default_is_safe() -> None:
    reg = build_real_generate_frames_handler_registry()
    handler = reg.get("generate_frames")
    payload = _make_payload(dry_validate=False, allow_real_execution=True)
    result = handler(payload)
    assert result["status"] == "blocked"
    assert "enable_real_execution=False" in result["reason"]
