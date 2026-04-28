"""Tests for MK-CTRL6 — ShotControlOrchestrator."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.action_runner import ControlledActionRunner
from app.control.gate import ShotExecutionGate
from app.control.models import ShotArtifacts, ShotStateReport
from app.control.orchestrator import ShotControlOrchestrator
from app.control.shot_controller import ShotController


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    (tmp_path / "output" / "scenes").mkdir(parents=True)
    return tmp_path


def _make_orchestrator(
    project_root: Path, handlers: dict[str, Any] | None = None
) -> ShotControlOrchestrator:
    controller = ShotController(project_root)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    runner = None
    if handlers is not None:
        runner = ControlledActionRunner(controller, gate, handlers)
    return ShotControlOrchestrator(controller, gate, planner, runner)


def _make_report(
    episode_id: str = "ep01",
    shot_id: str = "shot01",
    current_state: str = "ready_for_generation",
    next_action: str = "generate_frames",
    blocked_reason: str | None = None,
    brief_path: str | None = None,
    generated_frames: list[str] | None = None,
    scene_mp4_path: str | None = None,
    scene_audio_wav_path: str | None = None,
    scene_mp4_with_audio_path: str | None = None,
    final_episode_mp4_path: str | None = None,
    generation_required: bool = False,
    assembly_required: bool = False,
    audio_required: bool = False,
    qa_required: bool = False,
    is_done: bool = False,
) -> ShotStateReport:
    artifacts = ShotArtifacts(
        brief_path=brief_path,
        generated_frames=generated_frames or [],
        scene_mp4_path=scene_mp4_path,
        scene_audio_wav_path=scene_audio_wav_path,
        scene_mp4_with_audio_path=scene_mp4_with_audio_path,
        final_episode_mp4_path=final_episode_mp4_path,
    )
    return ShotStateReport(
        episode_id=episode_id,
        shot_id=shot_id,
        current_state=current_state,
        next_action=next_action,
        blocked_reason=blocked_reason,
        existing_artifacts=artifacts,
        missing_artifacts=[],
        generation_required=generation_required,
        assembly_required=assembly_required,
        audio_required=audio_required,
        qa_required=qa_required,
        is_done=is_done,
    )


# ── 1. dry_run returns report + decision + plan, no handler execution ──


def test_dry_run_returns_full_response_no_execution(tmp_project: Path) -> None:
    orch = _make_orchestrator(tmp_project)
    # Create a brief so the shot is ready for generation
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    resp = orch.dry_run("ep01", "shot01", "generate_frames")

    assert resp.mode == "dry_run"
    assert resp.state_report is not None
    assert resp.gate_decision is not None
    assert resp.action_plan is not None
    assert resp.action_result is None
    assert resp.success is True
    assert resp.gate_decision["allowed"] is True
    assert resp.action_plan["allowed"] is True


# ── 2. execute allowed action triggers exactly one handler ──


def test_execute_allowed_triggers_one_handler(tmp_project: Path) -> None:
    calls: list[dict] = []

    def mock_handler(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        calls.append({"episode_id": episode_id, "shot_id": shot_id})
        return {"ok": True}

    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project, handlers={"generate_frames": mock_handler})
    resp = orch.execute("ep01", "shot01", "generate_frames")

    assert resp.mode == "execute"
    assert resp.success is True
    assert resp.action_result is not None
    assert resp.action_result["executed"] is True
    assert len(calls) == 1
    assert calls[0]["shot_id"] == "shot01"


# ── 3. execute denied action triggers no handler ──


def test_execute_denied_triggers_no_handler(tmp_project: Path) -> None:
    calls: list[dict] = []

    def mock_handler(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        calls.append({"episode_id": episode_id, "shot_id": shot_id})
        return {"ok": True}

    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project, handlers={"generate_frames": mock_handler})
    # Request wrong action for this state (should be generate_frames, not assemble_scene_video)
    resp = orch.execute("ep01", "shot01", "assemble_scene_video")

    assert resp.success is False
    assert resp.action_result is None
    assert len(calls) == 0


# ── 4. blocked shot returns denied response in dry_run ──


def test_dry_run_blocked_returns_denied(tmp_project: Path) -> None:
    # Create a zero-byte mp4 to trigger blocked state
    bad = tmp_project / "output" / "scenes" / "shot01.mp4"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("")

    orch = _make_orchestrator(tmp_project)
    resp = orch.dry_run("ep01", "shot01", "generate_frames")

    assert resp.success is False
    assert resp.gate_decision["allowed"] is False
    assert "blocked" in resp.reason


# ── 5. execute without runner on allowed action -> RuntimeError ──


def test_execute_allowed_without_runner_raises(tmp_project: Path) -> None:
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project, handlers=None)
    with pytest.raises(RuntimeError, match="no runner is configured"):
        orch.execute("ep01", "shot01", "generate_frames")


# ── 6. response contains serialized state_report + gate_decision + action_plan ──


def test_response_contains_serialized_parts(tmp_project: Path) -> None:
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project)
    resp = orch.dry_run("ep01", "shot01", "generate_frames")

    assert isinstance(resp.state_report, dict)
    assert "episode_id" in resp.state_report
    assert isinstance(resp.gate_decision, dict)
    assert "allowed" in resp.gate_decision
    assert isinstance(resp.action_plan, dict)
    assert "required_inputs" in resp.action_plan


# ── 7. execute returns action_result when handler succeeds ──


def test_execute_returns_action_result_on_success(tmp_project: Path) -> None:
    def mock_handler(payload: dict) -> dict:
        return {"result": "frames_generated"}

    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project, handlers={"generate_frames": mock_handler})
    resp = orch.execute("ep01", "shot01", "generate_frames")

    assert resp.action_result is not None
    assert resp.action_result["handler_result"] == {"result": "frames_generated"}
    assert resp.action_result["executed"] is True
    assert resp.action_result["allowed"] is True


# ── 8. handler exception propagates clearly through execute() ──


def test_execute_handler_exception_propagates(tmp_project: Path) -> None:
    def bad_handler(payload: dict) -> dict:
        raise RuntimeError("handler exploded")

    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    orch = _make_orchestrator(tmp_project, handlers={"generate_frames": bad_handler})
    with pytest.raises(RuntimeError, match="handler exploded"):
        orch.execute("ep01", "shot01", "generate_frames")


# ── 9. dry_run does not mutate filesystem / create files ──


def test_dry_run_no_filesystem_mutation(tmp_project: Path) -> None:
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("# brief\n")

    # Snapshot all files under tmp_project before
    before = set(tmp_project.rglob("*"))

    orch = _make_orchestrator(tmp_project)
    orch.dry_run("ep01", "shot01", "generate_frames")

    after = set(tmp_project.rglob("*"))
    assert before == after


# ── 10. orchestrator does not mutate ShotStateReport contents ──


def test_orchestrator_does_not_mutate_report() -> None:
    report = _make_report(
        brief_path="data/briefs/ep01_shot01_brief.md",
        generation_required=True,
    )
    before = report.to_json()

    # Build an orchestrator around a mock controller that returns this report
    class MockController:
        def inspect(self, episode_id: str, shot_id: str) -> ShotStateReport:
            return report

    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    orch = ShotControlOrchestrator(MockController(), gate, planner)
    orch.dry_run("ep01", "shot01", "generate_frames")

    after = report.to_json()
    assert before == after
