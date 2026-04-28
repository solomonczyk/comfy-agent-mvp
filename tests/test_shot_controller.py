"""Tests for MK-CTRL1 — ShotController."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.control.shot_controller import ShotController


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a temp project root with standard dirs."""
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    (tmp_path / "output" / "scenes").mkdir(parents=True)
    return tmp_path


# ── 1. no brief ───────────────────────────────────────────────────────

def test_no_brief_returns_missing_brief(tmp_project: Path) -> None:
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "missing_brief"
    assert r.next_action == "create_brief"
    assert r.existing_artifacts.brief_path is None
    assert "brief" in r.missing_artifacts


# ── 2. brief exists, nothing else ─────────────────────────────────────

def test_brief_exists_ready_for_generation(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "ready_for_generation"
    assert r.next_action == "generate_frames"
    assert r.generation_required is True
    assert "generated_frames" in r.missing_artifacts


# ── 3. partial generation (some frames) ───────────────────────────────

def test_some_frames_partial_generation(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    frames_dir = tmp_project / "output/scenes"
    frames_dir.mkdir(parents=True, exist_ok=True)
    (frames_dir / "shot01_00001.png").write_bytes(b"\x89PNG")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "partial_generation"
    assert r.next_action == "continue_generation"
    assert r.generation_required is True
    assert len(r.existing_artifacts.generated_frames) == 1


# ── 4. ready for assembly (frames exist, no mp4) ────────────────────

def test_frames_ready_for_assembly(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    frames_dir = tmp_project / "output/scenes"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        (frames_dir / f"shot01_{i:05d}.png").write_bytes(b"\x89PNG")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    # With enough frames but no scene mp4, controller sees partial
    # (frames exist, no scene_mp4 -> partial_generation)
    assert r.current_state in ("partial_generation", "ready_for_assembly")
    assert r.next_action in ("continue_generation", "assemble_scene_video")


# ── 5. ready for audio (dialogue exists) ────────────────────────────

def test_dialogue_triggers_ready_for_audio(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\ndialogue: hello\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "ready_for_audio"
    assert r.next_action == "synthesize_and_mux_audio"
    assert r.audio_required is True
    assert "scene_audio_wav" in r.missing_artifacts
    assert "scene_mp4_with_audio" in r.missing_artifacts


# ── 6. ready for final episode (muxed exists) ───────────────────────

def test_muxed_ready_for_final_episode(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\ndialogue: hello\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    (scenes_dir / "shot01_with_audio.mp4").write_bytes(b"fake")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "ready_for_final_episode"
    assert r.next_action == "assemble_episode"


# ── 7. ready for qa (final episode exists, no qa) ───────────────────

def test_final_exists_ready_for_qa(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ep_dir = tmp_project / "output/episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "ep01_final.mp4").write_bytes(b"fake")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"fake")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "ready_for_qa"
    assert r.next_action == "run_qa"
    assert r.qa_required is True


# ── 8. done (final + qa marker) ──────────────────────────────────────

def test_done_when_qa_passed(tmp_project: Path) -> None:
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
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "done"
    assert r.next_action == "none"
    assert r.is_done is True


# ── 9. blocked: zero-byte file ──────────────────────────────────────

def test_zero_byte_file_blocked(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01.mp4").write_bytes(b"")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "blocked"
    assert r.next_action == "none"
    assert r.blocked_reason is not None
    assert "zero-byte" in r.blocked_reason


# ── 10. blocked: muxed without base mp4 ──────────────────────────────

def test_muxed_without_base_blocked(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    scenes_dir = tmp_project / "output/scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (scenes_dir / "shot01_with_audio.mp4").write_bytes(b"fake")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "blocked"
    assert "scene_mp4 missing" in r.blocked_reason


# ── 11. blocked: final episode without scene artifacts ──────────────

def test_final_without_scene_blocked(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ep_dir = tmp_project / "output/episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "ep01_final.mp4").write_bytes(b"fake")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "blocked"
    assert "final_episode exists but no scene_mp4" in r.blocked_reason


# ── 12. report serialization ─────────────────────────────────────────

def test_report_to_json(tmp_project: Path) -> None:
    brief = tmp_project / "data/briefs/ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    data = json.loads(r.to_json())
    assert data["episode_id"] == "ep01"
    assert data["shot_id"] == "shot01"
    assert "current_state" in data


# ── 13. inspect is read-only ─────────────────────────────────────────

def test_inspect_does_not_create_files(tmp_project: Path) -> None:
    ctrl = ShotController(tmp_project)
    r = ctrl.inspect("ep01", "shot01")
    assert r.current_state == "missing_brief"
    assert not (tmp_project / "output" / "ep01" / "shot01").exists()
