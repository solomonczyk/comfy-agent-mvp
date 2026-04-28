"""Tests for MK-CTRL10 — Production handler contracts and adapters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from app.control.handler_contracts import HandlerPayload, HandlerResult
from app.control.handlers import HandlerRegistry
from app.control.ledger import ShotLedgerStorage
from app.control.production_handlers import (
    CANONICAL_ACTION_KEYS,
    ProductionHandlerAdapter,
    build_production_handler_registry,
)
from app.control.shot_controller import ShotController
from app.control.gate import ShotExecutionGate
from app.control.action_runner import ControlledActionRunner


# ── fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_payload() -> HandlerPayload:
    return HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={"current_state": "ready_for_generation"},
        action_plan={"next": "generate_frames"},
    )


@pytest.fixture
def real_callable() -> Callable:
    def _call(payload: HandlerPayload) -> dict:
        return {"frames": 24, "format": "png"}
    return _call


# ── 1. HandlerPayload serializes to dict ─────────────────────────────

def test_handler_payload_to_dict(sample_payload: HandlerPayload) -> None:
    d = sample_payload.to_dict()
    assert d["episode_id"] == "ep01"
    assert d["shot_id"] == "shot01"
    assert d["action"] == "generate_frames"
    assert d["state_report"] == {"current_state": "ready_for_generation"}
    assert d["action_plan"] == {"next": "generate_frames"}
    assert d["dry_validate"] is True
    assert d["allow_real_execution"] is False
    assert d["extra"] == {}


# ── 2. HandlerResult serializes to dict ────────────────────────────────

def test_handler_result_to_dict() -> None:
    r = HandlerResult(
        handler="generate_frames",
        status="validated",
        would_execute=True,
        executed=False,
        reason="dry run",
        artifacts={"frames": 10},
        metadata={"episode_id": "ep01"},
    )
    d = r.to_dict()
    assert d["handler"] == "generate_frames"
    assert d["status"] == "validated"
    assert d["would_execute"] is True
    assert d["executed"] is False
    assert d["reason"] == "dry run"
    assert d["artifacts"] == {"frames": 10}
    assert d["metadata"] == {"episode_id": "ep01"}


# ── 3. adapter dry_validate does not call real_callable ──────────────

def test_dry_validate_skips_real_callable(real_callable: Callable) -> None:
    called = {"count": 0}

    def counting(payload: HandlerPayload) -> dict:
        called["count"] += 1
        return {}

    adapter = ProductionHandlerAdapter("generate_frames", real_callable=counting)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={}, dry_validate=True,
    )
    result = adapter(payload)
    assert called["count"] == 0
    assert result["status"] == "validated"


# ── 4. adapter dry_validate returns status validated ─────────────────

def test_dry_validate_returns_validated() -> None:
    adapter = ProductionHandlerAdapter("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={}, dry_validate=True,
    )
    result = adapter(payload)
    assert result["status"] == "validated"
    assert result["executed"] is False
    assert result["would_execute"] is True


# ── 5. adapter blocks when allow_real_execution=False ──────────────────

def test_blocks_when_allow_real_execution_false(real_callable: Callable) -> None:
    adapter = ProductionHandlerAdapter("generate_frames", real_callable=real_callable)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=False,
    )
    result = adapter(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["would_execute"] is True
    assert "allow_real_execution=False" in result["reason"]


# ── 6. adapter blocks when real_callable is None ───────────────────────

def test_blocks_when_real_callable_none() -> None:
    adapter = ProductionHandlerAdapter("generate_frames", real_callable=None)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["would_execute"] is True
    assert "No real callable is configured" in result["reason"]


# ── 7. adapter executes real_callable only when explicitly allowed ─────

def test_executes_when_fully_enabled(real_callable: Callable) -> None:
    adapter = ProductionHandlerAdapter("generate_frames", real_callable=real_callable)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True
    assert result["would_execute"] is True


# ── 8. adapter returns artifacts from real_callable ────────────────────

def test_returns_artifacts_from_real_callable() -> None:
    def fake_callable(payload: HandlerPayload) -> dict:
        return {"frames": 42, "format": "png"}

    adapter = ProductionHandlerAdapter("generate_frames", real_callable=fake_callable)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "executed"
    assert result["artifacts"] == {"frames": 42, "format": "png"}


# ── 9. adapter handles dict payload input ──────────────────────────────

def test_adapter_accepts_dict_payload() -> None:
    adapter = ProductionHandlerAdapter("generate_frames")
    result = adapter({
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "generate_frames",
        "state_report": {},
        "action_plan": {},
        "dry_validate": True,
    })
    assert result["status"] == "validated"
    assert result["metadata"]["episode_id"] == "ep01"


# ── 10. adapter preserves episode_id and shot_id in metadata or result ───

def test_preserves_episode_and_shot_id() -> None:
    adapter = ProductionHandlerAdapter("generate_frames")
    for dry in (True, False):
        payload = HandlerPayload(
            episode_id="ep99", shot_id="shot99", action="generate_frames",
            state_report={}, action_plan={},
            dry_validate=dry, allow_real_execution=not dry,
        )
        result = adapter(payload)
        # In dry mode metadata contains ids; in blocked mode (allow=False when dry=False)
        # metadata also contains ids.
        assert result["metadata"]["episode_id"] == "ep99"
        assert result["metadata"]["shot_id"] == "shot99"


# ── 11. factory creates registry with all canonical action keys ────────

def test_factory_registry_has_all_canonical_keys() -> None:
    reg = build_production_handler_registry()
    for action in CANONICAL_ACTION_KEYS:
        assert action in reg.to_dict()
        assert reg.is_enabled(action) is True


# ── 12. factory with enable_real_handlers=False does not expose
#         executable real handlers ──────────────────────────────────────

def test_factory_disabled_no_real_handlers() -> None:
    def evil_callable(payload: HandlerPayload) -> dict:
        raise RuntimeError("should not run")

    reg = build_production_handler_registry(
        enable_real_handlers=False,
        real_callables={"generate_frames": evil_callable},
    )
    handler = reg.get("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = handler(payload)
    # Even with allow_real_execution=True, the adapter blocks because
    # enable_real_handlers=False caused real_callable=None.
    assert result["status"] == "blocked"
    assert "No real callable is configured" in result["reason"]


# ── 13. factory with enable_real_handlers=True still requires
#         allow_real_execution=True in payload ────────────────────────

def test_factory_enabled_payload_must_allow() -> None:
    def good_callable(payload: HandlerPayload) -> dict:
        return {"ok": True}

    reg = build_production_handler_registry(
        enable_real_handlers=True,
        real_callables={"generate_frames": good_callable},
    )
    handler = reg.get("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=False,
    )
    result = handler(payload)
    assert result["status"] == "blocked"
    assert "allow_real_execution=False" in result["reason"]


# ── 14. missing callable for one action does not break other actions ───

def test_missing_callable_does_not_break_others() -> None:
    def good_callable(payload: HandlerPayload) -> dict:
        return {"ok": True}

    reg = build_production_handler_registry(
        enable_real_handlers=True,
        real_callables={"assemble_scene_video": good_callable},
    )
    # generate_frames has no callable -> blocks
    blocked_payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    assert reg.get("generate_frames")(blocked_payload)["status"] == "blocked"

    # assemble_scene_video has callable -> executes
    exec_payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="assemble_scene_video",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    assert reg.get("assemble_scene_video")(exec_payload)["status"] == "executed"


# ── 15. service can execute production adapter in dry_validate mode
#         without real execution ──────────────────────────────────────

def test_service_executes_adapter_dry_validate(tmp_project: Path) -> None:
    """Wire a production adapter through ControlledActionRunner and verify
    dry_validate mode returns 'validated' without invoking a real callable."""
    called = {"count": 0}

    def counting_callable(payload: HandlerPayload) -> dict:
        called["count"] += 1
        return {"real": True}

    reg = build_production_handler_registry(
        enable_real_handlers=True,
        real_callables={"generate_frames": counting_callable},
    )
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger = ShotLedgerStorage(tmp_project)
    runner = ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers=reg.enabled_handlers(),
        ledger=ledger,
    )

    # Set up shot state so gate allows generate_frames
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    # The adapter is called via kwargs by the runner, which constructs a payload
    # with dry_validate=True by default -> validated, not executed.
    result = runner.run_one("ep01", "shot01", "generate_frames")
    assert result.allowed is True
    assert result.executed is True
    assert result.control_executed is True
    assert result.production_executed is False
    assert result.handler_status == "validated"
    assert result.handler_result is not None
    assert result.handler_result["status"] == "validated"
    assert result.handler_result["executed"] is False
    assert called["count"] == 0


# ── 16. ledger records validated/blocked result ────────────────────────

def test_ledger_records_adapter_result(tmp_project: Path) -> None:
    reg = build_production_handler_registry(enable_real_handlers=False)
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger = ShotLedgerStorage(tmp_project)
    runner = ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers=reg.enabled_handlers(),
        ledger=ledger,
    )

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    result = runner.run_one("ep01", "shot01", "generate_frames")
    assert result.allowed is True
    assert result.executed is True
    assert result.control_executed is True
    assert result.production_executed is False
    assert result.handler_status == "validated"

    ledger_data = ledger.load("ep01", "shot01")
    # Find the action_executed record
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    record = action_records[0]
    assert record.handler_result is not None
    assert record.handler_result["status"] == "validated"
    assert record.handler_result["executed"] is False
    assert record.handler_result["handler"] == "generate_frames"
    assert record.control_executed is True
    assert record.production_executed is False
    assert record.handler_status == "validated"


# ── 17. no ComfyUI / ffmpeg / TTS process is started by tests ──────────

def test_no_external_processes_started(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the adapter and factory never spawn subprocesses."""
    import subprocess

    spawned = []
    original_popen = subprocess.Popen

    def fake_popen(*args: Any, **kwargs: Any) -> Any:
        spawned.append((args, kwargs))
        raise RuntimeError("subprocess spawned during test")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    reg = build_production_handler_registry(enable_real_handlers=False)
    adapter = reg.get("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={}, dry_validate=True,
    )
    adapter(payload)
    assert len(spawned) == 0


# ── MK-CTRL10R: Execution Semantics Lock tests ─────────────────────────

# 1. dry_validate adapter result records control_executed=true

def test_dry_validate_records_control_executed_true(tmp_project: Path) -> None:
    reg = build_production_handler_registry(enable_real_handlers=False)
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger = ShotLedgerStorage(tmp_project)
    runner = ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers=reg.enabled_handlers(),
        ledger=ledger,
    )
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    result = runner.run_one("ep01", "shot01", "generate_frames")
    assert result.control_executed is True
    assert result.production_executed is False
    assert result.handler_status == "validated"


# 2. dry_validate adapter result records production_executed=false
# 3. dry_validate adapter result records handler_status="validated"
# (covered by test_dry_validate_records_control_executed_true above)

# 4. blocked adapter result records production_executed=false

def test_blocked_adapter_records_production_executed_false() -> None:
    adapter = ProductionHandlerAdapter("generate_frames", real_callable=None)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["would_execute"] is True


# 5. real executed adapter result records production_executed=true

def test_real_executed_records_production_executed_true() -> None:
    def fake_real(payload: HandlerPayload) -> dict:
        return {"output": "frame_001.png"}

    adapter = ProductionHandlerAdapter("generate_frames", real_callable=fake_real)
    payload = HandlerPayload(
        episode_id="ep01", shot_id="shot01", action="generate_frames",
        state_report={}, action_plan={},
        dry_validate=False, allow_real_execution=True,
    )
    result = adapter(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True
    assert result["would_execute"] is True


# 6. denied action records control_executed=false
# 7. denied action records production_executed=false

def test_denied_action_records_control_executed_false(tmp_project: Path) -> None:
    """When gate denies, no handler is invoked and ledger shows zero execution."""
    reg = build_production_handler_registry(enable_real_handlers=False)
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger = ShotLedgerStorage(tmp_project)
    runner = ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers=reg.enabled_handlers(),
        ledger=ledger,
    )
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    # assemble_scene_video is denied because next expected is generate_frames
    result = runner.run_one("ep01", "shot01", "assemble_scene_video")
    assert result.allowed is False
    assert result.control_executed is False
    assert result.production_executed is False
    assert result.handler_status is None

    ledger_data = ledger.load("ep01", "shot01")
    denied = [r for r in ledger_data.records if r.event_type == "action_denied"][0]
    assert denied.control_executed is False
    assert denied.production_executed is False
    assert denied.handler_status is None


# 8. failed handler records control_executed=true
# 9. failed handler records handler_status="failed"

def test_failed_handler_records_control_executed_true(tmp_project: Path) -> None:
    """When handler raises, control stack invoked it but production result is unknown."""
    def plain_boom(payload: dict) -> dict:
        raise RuntimeError("boom")

    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    ledger = ShotLedgerStorage(tmp_project)
    runner = ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers={"generate_frames": plain_boom},
        ledger=ledger,
    )
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="boom"):
        runner.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    failed = [r for r in ledger_data.records if r.event_type == "action_failed"][0]
    assert failed.control_executed is True
    assert failed.production_executed is None
    assert failed.handler_status == "failed"


# 10. old ledger JSON shape remains backward-compatible

def test_old_ledger_json_backward_compatible(tmp_project: Path) -> None:
    """JSON written before MK-CTRL10R loads cleanly; new fields default to None."""
    import json
    store = ShotLedgerStorage(tmp_project)
    # Manually write pre-MK-CTRL10R shaped ledger JSON
    old_shape = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "records": [
            {
                "timestamp": "2024-01-01T00:00:00",
                "episode_id": "ep01",
                "shot_id": "shot01",
                "event_type": "action_executed",
                "requested_action": "generate_frames",
                "allowed": True,
                "executed": True,
                "success": True,
                "current_state": "ready_for_generation",
                "expected_next_action": "generate_frames",
                "reason": "handler executed successfully",
                "handler_result": {"handler": "generate_frames", "frames": 10},
            }
        ]
    }
    path = store.ledger_path("ep01", "shot01")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(old_shape, indent=2), encoding="utf-8")

    ledger_data = store.load("ep01", "shot01")
    rec = ledger_data.records[0]
    assert rec.event_type == "action_executed"
    assert rec.executed is True
    assert rec.control_executed is None  # absent in old JSON
    assert rec.production_executed is None
    assert rec.handler_status is None


# 11. existing 45+17 tests still pass — verified by full suite run

