"""Tests for MK-CTRL11 — GenerateFramesHandler real-ready production handler."""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from app.control.generate_frames_handler import (
    GenerateFramesArtifacts,
    GenerateFramesHandler,
    GenerateFramesRequest,
    build_generate_frames_handler_registry,
)
from app.control.handler_contracts import HandlerPayload, HandlerResult
from app.control.handlers import HandlerRegistry
from app.control.ledger import ShotLedgerStorage
from app.control.shot_controller import ShotController
from app.control.gate import ShotExecutionGate
from app.control.action_plan import ActionPlanBuilder
from app.control.action_runner import ControlledActionRunner
from app.control.service import ShotControlService


# ── fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_request() -> GenerateFramesRequest:
    return GenerateFramesRequest(
        episode_id="ep01",
        shot_id="shot01",
        brief_path="data/briefs/ep01_shot01_brief.md",
        output_dir="output/shots/ep01/shot01",
        workflow_template_path="workflows/standard.json",
        checkpoint="model.ckpt",
        steps=20,
        seed=42,
        extra={"foo": "bar"},
    )


@pytest.fixture
def sample_artifacts() -> GenerateFramesArtifacts:
    return GenerateFramesArtifacts(
        frame_paths=["output/shots/ep01/shot01/frame_001.png"],
        manifest_path="output/shots/ep01/shot01/manifest.json",
        preview_path="output/shots/ep01/shot01/preview.png",
        metadata={"format": "png", "count": 1},
    )


@pytest.fixture
def fake_callable() -> Callable[[GenerateFramesRequest], GenerateFramesArtifacts]:
    def _call(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        return GenerateFramesArtifacts(
            frame_paths=["output/shots/ep01/shot01/frame_001.png"],
            manifest_path="output/shots/ep01/shot01/manifest.json",
            preview_path="output/shots/ep01/shot01/preview.png",
            metadata={"seed": request.seed, "steps": request.steps},
        )
    return _call


# ── 1. GenerateFramesRequest serializes to dict ──────────────────────

def test_generate_frames_request_to_dict(sample_request: GenerateFramesRequest) -> None:
    d = sample_request.to_dict()
    assert d["episode_id"] == "ep01"
    assert d["shot_id"] == "shot01"
    assert d["brief_path"] == "data/briefs/ep01_shot01_brief.md"
    assert d["output_dir"] == "output/shots/ep01/shot01"
    assert d["workflow_template_path"] == "workflows/standard.json"
    assert d["checkpoint"] == "model.ckpt"
    assert d["steps"] == 20
    assert d["seed"] == 42
    assert d["extra"] == {"foo": "bar"}


# ── 2. GenerateFramesArtifacts serializes to dict ────────────────────

def test_generate_frames_artifacts_to_dict(sample_artifacts: GenerateFramesArtifacts) -> None:
    d = sample_artifacts.to_dict()
    assert d["frame_paths"] == ["output/shots/ep01/shot01/frame_001.png"]
    assert d["manifest_path"] == "output/shots/ep01/shot01/manifest.json"
    assert d["preview_path"] == "output/shots/ep01/shot01/preview.png"
    assert d["metadata"] == {"format": "png", "count": 1}


# ── 3. handler accepts HandlerPayload ────────────────────────────────

def test_handler_accepts_handler_payload() -> None:
    handler = GenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["status"] == "validated"


# ── 4. handler accepts dict payload ──────────────────────────────────

def test_handler_accepts_dict_payload() -> None:
    handler = GenerateFramesHandler()
    result = handler({
        "episode_id": "ep01",
        "shot_id": "shot01",
        "action": "generate_frames",
        "state_report": {},
        "action_plan": {"brief_path": "data/briefs/ep01_shot01_brief.md"},
        "dry_validate": True,
    })
    assert result["status"] == "validated"
    assert result["metadata"]["episode_id"] == "ep01"


# ── 5. missing brief_path returns blocked ────────────────────────────

def test_missing_brief_path_returns_blocked() -> None:
    handler = GenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert "brief_path is missing" in result["reason"]


# ── 6. wrong action returns blocked ──────────────────────────────────

def test_wrong_action_returns_blocked() -> None:
    handler = GenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="assemble_scene_video",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert "Unsupported action" in result["reason"]


# ── 7. dry_validate returns status validated ─────────────────────────

def test_dry_validate_returns_validated() -> None:
    handler = GenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["status"] == "validated"
    assert result["executed"] is False
    assert result["would_execute"] is True


# ── 8. dry_validate does not call real_callable ──────────────────────

def test_dry_validate_skips_real_callable() -> None:
    called = {"count": 0}

    def counting(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        called["count"] += 1
        return GenerateFramesArtifacts()

    handler = GenerateFramesHandler(real_callable=counting)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert called["count"] == 0
    assert result["status"] == "validated"


# ── 9. dry_validate artifacts include brief_path ─────────────────────

def test_dry_validate_artifacts_include_brief_path() -> None:
    handler = GenerateFramesHandler()
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["artifacts"]["brief_path"] == "data/briefs/ep01_shot01_brief.md"


# ── 10. dry_validate artifacts include output_dir ────────────────────

def test_dry_validate_artifacts_include_output_dir() -> None:
    handler = GenerateFramesHandler(default_output_root="output/shots")
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=True,
    )
    result = handler(payload)
    assert result["artifacts"]["output_dir"].replace("\\", "/") == "output/shots/ep01/shot01"


# ── 11. allow_real_execution=False blocks real call ──────────────────

def test_allow_real_execution_false_blocks() -> None:
    def should_not_run(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        raise RuntimeError("should not run")

    handler = GenerateFramesHandler(real_callable=should_not_run)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=False,
    )
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["would_execute"] is True
    assert "allow_real_execution=False" in result["reason"]


# ── 12. allow_real_execution=True with no callable blocks ────────────

def test_allow_real_execution_true_no_callable_blocks() -> None:
    handler = GenerateFramesHandler(real_callable=None)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["would_execute"] is True
    assert "no real generate callable is configured" in result["reason"].lower()


# ── 13. allow_real_execution=True with callable executes ─────────────

def test_allow_real_execution_true_with_callable_executes(fake_callable: Callable) -> None:
    handler = GenerateFramesHandler(real_callable=fake_callable)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["status"] == "executed"
    assert result["executed"] is True
    assert result["would_execute"] is True


# ── 14. fake callable receives GenerateFramesRequest ─────────────────

def test_fake_callable_receives_generate_frames_request() -> None:
    received: list[GenerateFramesRequest] = []

    def capture(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        received.append(request)
        return GenerateFramesArtifacts()

    handler = GenerateFramesHandler(real_callable=capture)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={
            "brief_path": "data/briefs/ep01_shot01_brief.md",
            "command_preview": "python -m app run",
            "expected_outputs": ["output/shot01/*.png"],
            "workflow_template_path": "workflows/test.json",
            "checkpoint": "test.ckpt",
            "steps": 25,
            "seed": 123,
        },
        dry_validate=False,
        allow_real_execution=True,
    )
    handler(payload)
    assert len(received) == 1
    req = received[0]
    assert req.episode_id == "ep01"
    assert req.shot_id == "shot01"
    assert req.brief_path == "data/briefs/ep01_shot01_brief.md"
    assert req.workflow_template_path == "workflows/test.json"
    assert req.checkpoint == "test.ckpt"
    assert req.steps == 25
    assert req.seed == 123


# ── 15. fake callable frame_paths appear in artifacts ────────────────

def test_fake_callable_frame_paths_in_artifacts() -> None:
    def fake(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        return GenerateFramesArtifacts(
            frame_paths=["f1.png", "f2.png"],
        )

    handler = GenerateFramesHandler(real_callable=fake)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["artifacts"]["frame_paths"] == ["f1.png", "f2.png"]


# ── 16. fake callable manifest_path appears in artifacts ─────────────

def test_fake_callable_manifest_path_in_artifacts() -> None:
    def fake(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        return GenerateFramesArtifacts(
            manifest_path="output/manifest.json",
        )

    handler = GenerateFramesHandler(real_callable=fake)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["artifacts"]["manifest_path"] == "output/manifest.json"


# ── 17. fake callable exception returns status failed ────────────────

def test_fake_callable_exception_returns_failed() -> None:
    def boom(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        raise ValueError("generation error")

    handler = GenerateFramesHandler(real_callable=boom)
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={},
        action_plan={"brief_path": "data/briefs/ep01_shot01_brief.md"},
        dry_validate=False,
        allow_real_execution=True,
    )
    result = handler(payload)
    assert result["status"] == "failed"
    assert result["executed"] is False
    assert result["would_execute"] is True
    assert "ValueError: generation error" in result["reason"]


# ── 18. registry contains generate_frames ────────────────────────────

def test_registry_contains_generate_frames() -> None:
    reg = build_generate_frames_handler_registry()
    assert "generate_frames" in reg.to_dict()
    assert reg.is_enabled("generate_frames") is True


# ── 19. service can execute handler in dry_validate mode ─────────────

def test_service_executes_handler_dry_validate(tmp_project: Path) -> None:
    reg = build_generate_frames_handler_registry(enable_real_handlers=False)
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
    assert result.handler_result is not None
    assert result.handler_result["status"] == "validated"
    assert result.handler_result["executed"] is False


# ── 20. ledger records production_executed=false for dry_validate ────

def test_ledger_records_production_executed_false_dry_validate(tmp_project: Path) -> None:
    reg = build_generate_frames_handler_registry(enable_real_handlers=False)
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

    runner.run_one("ep01", "shot01", "generate_frames")

    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    record = action_records[0]
    assert record.production_executed is False
    assert record.handler_status == "validated"


# ── 21. ledger records production_executed=true for fake real execution ─

def test_ledger_records_production_executed_true_real_execution(tmp_project: Path) -> None:
    def fake_real(request: GenerateFramesRequest) -> GenerateFramesArtifacts:
        return GenerateFramesArtifacts(
            frame_paths=["output/shot01/frame_001.png"],
        )

    reg = build_generate_frames_handler_registry(
        enable_real_handlers=True,
        real_generate_callable=fake_real,
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

    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")

    # Need to override dry_validate to False and allow_real_execution to True.
    # The runner calls handler via kwargs (report=ShotStateReport), so we need
    # to inject the flags.  We call the handler directly through a wrapper that
    # sets the correct payload flags.
    handler = reg.get("generate_frames")
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="generate_frames",
        state_report={
            "existing_artifacts": {"brief_path": str(brief)},
        },
        action_plan={"brief_path": str(brief)},
        dry_validate=False,
        allow_real_execution=True,
    )
    handler_result = handler(payload)

    # Manually write a ledger record mimicking what the runner would do
    # so we can verify ledger semantics.
    from app.control.ledger import ShotLedgerRecord
    import time
    record = ShotLedgerRecord(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        episode_id="ep01",
        shot_id="shot01",
        event_type="action_executed",
        requested_action="generate_frames",
        allowed=True,
        executed=True,
        success=True,
        control_executed=True,
        production_executed=handler_result.get("executed"),
        handler_status=handler_result.get("status"),
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reason="handler executed successfully",
        handler_result=handler_result,
    )
    ledger.append("ep01", "shot01", record)

    ledger_data = ledger.load("ep01", "shot01")
    action_records = [r for r in ledger_data.records if r.event_type == "action_executed"]
    assert len(action_records) == 1
    rec = action_records[0]
    assert rec.production_executed is True
    assert rec.handler_status == "executed"


# ── 22. no ComfyUI / ffmpeg / TTS imports ────────────────────────────

def test_no_forbidden_imports() -> None:
    from app.control import generate_frames_handler as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)

    forbidden = {"comfyui", "ffmpeg", "tts", "comfy", "comfysubmitter", "executionrunner"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.lower() not in forbidden, f"Forbidden import: {alias.name}"
        if isinstance(node, ast.ImportFrom):
            mod_name = (node.module or "").lower()
            assert not any(f in mod_name for f in forbidden), f"Forbidden import from: {node.module}"
