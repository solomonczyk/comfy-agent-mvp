"""Tests for MK-CTRL2 — ShotExecutionGate."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.control.gate import ActionGateDecision, ShotExecutionGate
from app.control.models import ShotArtifacts, ShotStateReport
from app.control.shot_controller import ShotController


@pytest.fixture
def gate() -> ShotExecutionGate:
    return ShotExecutionGate()


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    return tmp_path


def _report(
    current_state: str,
    next_action: str,
    blocked_reason: str | None = None,
    is_done: bool = False,
) -> ShotStateReport:
    return ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state=current_state,
        next_action=next_action,
        blocked_reason=blocked_reason,
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        is_done=is_done,
    )


# ── 1. ready_for_generation + generate_frames ───────────────────────

def test_ready_generate_allowed(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    d = gate.decide(r, "generate_frames")
    assert d.allowed is True
    assert d.reason == "action matches next expected step"


# ── 2. ready_for_generation + assemble_scene_video ────────────────────

def test_ready_assemble_denied(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    d = gate.decide(r, "assemble_scene_video")
    assert d.allowed is False
    assert "expected next action is 'generate_frames'" in d.reason


# ── 3. partial_generation + continue_generation ───────────────────────

def test_partial_continue_allowed(gate: ShotExecutionGate) -> None:
    r = _report("partial_generation", "continue_generation")
    d = gate.decide(r, "continue_generation")
    assert d.allowed is True


# ── 4. ready_for_audio + synthesize_and_mux_audio ────────────────────

def test_ready_audio_allowed(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_audio", "synthesize_and_mux_audio")
    d = gate.decide(r, "synthesize_and_mux_audio")
    assert d.allowed is True


# ── 5. blocked + any execution action ─────────────────────────────────

def test_blocked_denied(gate: ShotExecutionGate) -> None:
    r = _report("blocked", "none", blocked_reason="zero-byte file: scene.mp4")
    d = gate.decide(r, "generate_frames")
    assert d.allowed is False
    assert "blocked: zero-byte file" in d.reason


# ── 6. done + none ──────────────────────────────────────────────────

def test_done_none_allowed(gate: ShotExecutionGate) -> None:
    r = _report("done", "none", is_done=True)
    d = gate.decide(r, "none")
    assert d.allowed is True
    assert "done state" in d.reason


# ── 7. done + generate_frames ───────────────────────────────────────

def test_done_generate_denied(gate: ShotExecutionGate) -> None:
    r = _report("done", "none", is_done=True)
    d = gate.decide(r, "generate_frames")
    assert d.allowed is False
    assert "already done" in d.reason


# ── 8. unknown action ───────────────────────────────────────────────

def test_unknown_action_denied(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    d = gate.decide(r, "delete_everything")
    assert d.allowed is False
    assert "unknown action" in d.reason


# ── 9. gate does not mutate report ──────────────────────────────────

def test_gate_does_not_mutate_report(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    original = r.current_state
    gate.decide(r, "generate_frames")
    assert r.current_state == original


# ── 10. gate does not create files / run subprocesses ───────────────────

def test_gate_does_not_create_files(tmp_project: Path, gate: ShotExecutionGate) -> None:
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    gate.decide(r, "generate_frames")
    assert not (tmp_project / "output" / "ep01" / "shot01").exists()


# ── 11. assert_allowed raises on deny ─────────────────────────────────

def test_assert_allowed_raises_on_deny(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    with pytest.raises(RuntimeError) as exc_info:
        gate.assert_allowed(r, "assemble_scene_video")
    assert "denied" in str(exc_info.value).lower() or "expected next action" in str(exc_info.value)


# ── 12. none denied in non-done non-blocked state ─────────────────────

def test_none_denied_in_ready_state(gate: ShotExecutionGate) -> None:
    r = _report("ready_for_generation", "generate_frames")
    d = gate.decide(r, "none")
    assert d.allowed is False
    assert "'none' is not a valid execution action" in d.reason


# ── 13. blocked state + none allowed ──────────────────────────────────

def test_blocked_none_allowed(gate: ShotExecutionGate) -> None:
    r = _report("blocked", "none", blocked_reason="corrupt data")
    d = gate.decide(r, "none")
    assert d.allowed is True
    assert "blocked state" in d.reason
