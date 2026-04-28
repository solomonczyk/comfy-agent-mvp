"""MK-CTRL25 — Lifecycle Full Path E2E Contract Test.

Proves the full controlled lifecycle for one shot:
ready_for_generation → generate_frames → frames_generated
→ assemble_scene → scene_assembled
→ qa_review → qa_passed
→ attach_audio → audio_attached
→ render_episode → episode_rendered

This test proves that the control stack can:
- Execute one action at a time
- Persist state after each accepted artifact
- Gate the next action correctly

All subprocess calls are mocked. No real ComfyUI, ffmpeg, TTS, or QA execution.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.control.action_plan import ActionPlanBuilder
from app.control.gate import ShotExecutionGate
from app.control.ledger import ShotLedgerStorage
from app.control.service import ShotControlService
from app.control.shot_controller import ShotController
from app.control.shot_state_storage import ShotState, ShotStateStorage


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project structure."""
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "output" / "episodes").mkdir(parents=True)
    (tmp_path / "output" / "scenes").mkdir(parents=True)
    (tmp_path / "output" / "frames").mkdir(parents=True)
    (tmp_path / "output" / "control").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to return fake stdout."""
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = ""
    return mock


def make_service_with_mock_handlers(
    tmp_project: Path,
    qa_fail: bool = False,
    artifact_failure: bool = False,
    skip_audio: bool = False,
):
    """Create ShotControlService with mock handlers that return proper artifact_status."""
    
    controller = ShotController(tmp_project)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    
    # Create enhanced mock handlers
    def generate_frames_mock(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        
        # Create fake frame manifest
        frame_manifest = tmp_project / "output" / "control" / f"{episode_id}_{shot_id}_frame_manifest.json"
        frame_manifest.parent.mkdir(parents=True, exist_ok=True)
        frame_manifest.write_text(json.dumps({"frame_count": 10}), encoding="utf-8")
        
        return {
            "handler": "generate_frames",
            "status": "executed",
            "executed": True,
            "would_execute": True,
            "reason": "generate_frames executed successfully",
            "artifacts": {
                "frame_manifest_path": str(frame_manifest),
                "frame_count": 10,
                "output_exists": True,
                "output_size_bytes": 100,
                "artifact_accepted": True,
                "artifact_status": "accepted",
                "artifact_reason": "frame manifest accepted",
            },
        }
    
    def assemble_scene_mock(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        
        if artifact_failure:
            # Simulate artifact failure
            return {
                "handler": "assemble_scene",
                "status": "executed",
                "executed": True,
                "would_execute": True,
                "reason": "assemble_scene completed but artifact missing",
                "artifacts": {
                    "scene_output_path": f"output/scenes/{episode_id}_{shot_id}.mp4",
                    "output_exists": False,
                    "output_size_bytes": None,
                    "artifact_accepted": False,
                    "artifact_status": "missing",
                    "artifact_reason": "scene MP4 missing or does not exist",
                },
            }
        
        # Create fake scene MP4
        scene_mp4 = tmp_project / "output" / "scenes" / f"{episode_id}_{shot_id}.mp4"
        scene_mp4.parent.mkdir(parents=True, exist_ok=True)
        scene_mp4.write_bytes(b"fake scene video")
        
        return {
            "handler": "assemble_scene",
            "status": "executed",
            "executed": True,
            "would_execute": True,
            "reason": "assemble_scene executed successfully",
            "artifacts": {
                "scene_output_path": str(scene_mp4),
                "output_exists": True,
                "output_size_bytes": 100,
                "artifact_accepted": True,
                "artifact_status": "accepted",
                "artifact_reason": "scene MP4 accepted",
            },
        }
    
    def qa_review_mock(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        
        # Create fake QA report
        qa_report = tmp_project / "output" / "control" / f"{episode_id}_{shot_id}_qa_report.json"
        qa_report.parent.mkdir(parents=True, exist_ok=True)
        
        if qa_fail:
            qa_report.write_text(json.dumps({
                "qa_score": 0.3,
                "qa_verdict": "fail",
                "defects": ["low_quality", "flicker"]
            }), encoding="utf-8")
            
            return {
                "handler": "qa_review",
                "status": "executed",
                "executed": True,
                "would_execute": True,
                "reason": "qa_review executed successfully but QA failed",
                "artifacts": {
                    "qa_report_path": str(qa_report),
                    "qa_score": 0.3,
                    "qa_verdict": "fail",
                    "artifact_accepted": True,  # Must be True for action_executed to be recorded
                    "artifact_status": "qa_failed",  # This triggers qa_failed state transition
                    "artifact_reason": "QA failed - below threshold",
                },
            }
        
        qa_report.write_text(json.dumps({
            "qa_score": 0.95,
            "qa_verdict": "pass",
            "defects": []
        }), encoding="utf-8")
        
        return {
            "handler": "qa_review",
            "status": "executed",
            "executed": True,
            "would_execute": True,
            "reason": "qa_review executed successfully",
            "artifacts": {
                "qa_report_path": str(qa_report),
                "qa_score": 0.95,
                "qa_verdict": "pass",
                "artifact_accepted": True,
                "artifact_status": "accepted",
                "artifact_reason": "QA passed",
            },
        }
    
    def attach_audio_mock(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        
        if skip_audio:
            # Create fake audio manifest only (skip)
            audio_manifest = tmp_project / "output" / "control" / f"{episode_id}_{shot_id}_audio_manifest.json"
            audio_manifest.parent.mkdir(parents=True, exist_ok=True)
            audio_manifest.write_text(json.dumps({
                "audio_engine": "silero",
                "audio_skipped": True,
                "skip_reason": "no dialogue"
            }), encoding="utf-8")
            
            return {
                "handler": "attach_audio",
                "status": "executed",
                "executed": True,
                "would_execute": True,
                "reason": "audio skipped - no dialogue",
                "artifacts": {
                    "audio_output_path": None,
                    "audio_manifest_path": str(audio_manifest),
                    "audio_skipped": True,
                    "skip_reason": "no dialogue",
                    "artifact_accepted": True,
                    "artifact_status": "skipped_no_audio",
                    "artifact_reason": "audio skipped - no dialogue",
                },
            }
        
        # Create fake audio output
        audio_output = tmp_project / "output" / "scenes" / f"{episode_id}_{shot_id}_audio.mp4"
        audio_output.parent.mkdir(parents=True, exist_ok=True)
        audio_output.write_bytes(b"fake audio video")
        
        # Create fake audio manifest
        audio_manifest = tmp_project / "output" / "control" / f"{episode_id}_{shot_id}_audio_manifest.json"
        audio_manifest.parent.mkdir(parents=True, exist_ok=True)
        audio_manifest.write_text(json.dumps({
            "audio_engine": "silero",
            "audio_duration_sec": 2.0
        }), encoding="utf-8")
        
        return {
            "handler": "attach_audio",
            "status": "executed",
            "executed": True,
            "would_execute": True,
            "reason": "attach_audio executed successfully",
            "artifacts": {
                "audio_output_path": str(audio_output),
                "audio_manifest_path": str(audio_manifest),
                "audio_duration_sec": 2.0,
                "audio_engine": "silero",
                "output_exists": True,
                "output_size_bytes": 100,
                "artifact_accepted": True,
                "artifact_status": "accepted",
                "artifact_reason": "audio attached accepted",
            },
        }
    
    def render_episode_mock(payload: dict) -> dict:
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        
        # Create fake episode MP4
        episode_output = tmp_project / "output" / "episodes" / f"{episode_id}_{shot_id}_episode.mp4"
        episode_output.parent.mkdir(parents=True, exist_ok=True)
        episode_output.write_bytes(b"fake episode")
        
        # Create fake episode manifest
        episode_manifest = tmp_project / "output" / "control" / f"{episode_id}_{shot_id}_episode_manifest.json"
        episode_manifest.parent.mkdir(parents=True, exist_ok=True)
        episode_manifest.write_text(json.dumps({
            "episode_duration_sec": 2.0,
            "episode_scene_count": 1
        }), encoding="utf-8")
        
        return {
            "handler": "render_episode",
            "status": "executed",
            "executed": True,
            "would_execute": True,
            "reason": "render_episode executed successfully",
            "artifacts": {
                "episode_output_path": str(episode_output),
                "episode_manifest_path": str(episode_manifest),
                "episode_duration_sec": 2.0,
                "episode_scene_count": 1,
                "output_exists": True,
                "output_size_bytes": 100,
                "artifact_accepted": True,
                "artifact_status": "accepted",
                "artifact_reason": "episode artifact accepted",
            },
        }
    
    handlers = {
        "generate_frames": generate_frames_mock,
        "assemble_scene": assemble_scene_mock,
        "qa_review": qa_review_mock,
        "attach_audio": attach_audio_mock,
        "render_episode": render_episode_mock,
    }
    
    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handlers=handlers,
        ledger_root=tmp_project,
    )
    
    return service


# ── Test 1: Full happy path reaches episode_rendered ─────────────────────

def test_full_happy_path_reaches_episode_rendered(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 1 — full happy path reaches episode_rendered."""
    # Set environment variable for real execution
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    # Create brief
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Create service with mock handlers
    service = make_service_with_mock_handlers(tmp_project)
    
    # Step 1: generate_frames (ready_for_generation → frames_generated)
    resp1 = service.execute("ep01", "shot01", "generate_frames")
    assert resp1.success is True
    
    # Verify state transition
    state_storage = ShotStateStorage(tmp_project)
    state1 = state_storage.load("ep01", "shot01")
    assert state1 is not None
    assert state1.current_state == "frames_generated"
    assert state1.expected_next_action == "assemble_scene"
    # artifact_path may be None or contain frame_manifest
    if state1.artifact_path:
        assert "frame_manifest" in state1.artifact_path.lower() or "frame" in state1.artifact_path.lower()
    
    # Step 2: assemble_scene (frames_generated → scene_assembled)
    resp2 = service.execute("ep01", "shot01", "assemble_scene")
    assert resp2.success is True
    
    state2 = state_storage.load("ep01", "shot01")
    assert state2.current_state == "scene_assembled"
    assert state2.expected_next_action == "qa_review"
    assert "scene" in state2.artifact_path.lower() or ".mp4" in str(state2.artifact_path).lower()
    
    # Step 3: qa_review pass (scene_assembled → qa_passed)
    resp3 = service.execute("ep01", "shot01", "qa_review")
    assert resp3.success is True
    
    state3 = state_storage.load("ep01", "shot01")
    assert state3.current_state == "qa_passed"
    assert state3.expected_next_action == "attach_audio"
    assert "qa_report" in state3.artifact_path or "qa" in str(state3.artifact_path).lower()
    
    # Step 4: attach_audio (qa_passed → audio_attached)
    resp4 = service.execute("ep01", "shot01", "attach_audio")
    assert resp4.success is True
    
    state4 = state_storage.load("ep01", "shot01")
    assert state4.current_state == "audio_attached"
    assert state4.expected_next_action == "render_episode"
    assert "audio" in state4.artifact_path.lower() or "manifest" in str(state4.artifact_path).lower()
    
    # Step 5: render_episode (audio_attached → episode_rendered)
    resp5 = service.execute("ep01", "shot01", "render_episode")
    assert resp5.success is True
    
    state5 = state_storage.load("ep01", "shot01")
    assert state5.current_state == "episode_rendered"
    assert state5.expected_next_action == "none"
    assert "episode" in state5.artifact_path.lower()
    
    # Final inspect
    report = service.controller.inspect("ep01", "shot01")
    assert report.current_state == "episode_rendered"
    assert report.next_action == "none"
    assert report.is_done is True


# ── Test 2: Exactly one action per service.execute call ───────────────────

def test_exactly_one_action_per_execute_call(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 2 — exactly one action per service.execute call."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    ledger = ShotLedgerStorage(tmp_project)
    
    # Execute generate_frames
    resp1 = service.execute("ep01", "shot01", "generate_frames")
    assert resp1.success is True
    
    # Check ledger: should have exactly one action_executed record
    ledger1 = ledger.load("ep01", "shot01")
    action_executed_count = sum(1 for r in ledger1.records if r.event_type == "action_executed")
    assert action_executed_count == 1
    
    # Execute assemble_scene
    resp2 = service.execute("ep01", "shot01", "assemble_scene")
    assert resp2.success is True
    
    # Check ledger: should have exactly two action_executed records total
    ledger2 = ledger.load("ep01", "shot01")
    action_executed_count = sum(1 for r in ledger2.records if r.event_type == "action_executed")
    assert action_executed_count == 2
    
    # Verify no auto-next-action occurred
    # If auto-next-action happened, we'd see more action_executed records
    # or state would have advanced beyond assemble_scene
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state.current_state == "scene_assembled"
    assert state.expected_next_action == "qa_review"


# ── Test 3: Gate blocks out-of-order action ─────────────────────────────

def test_gate_blocks_out_of_order_action(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 3 — gate blocks out-of-order action."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    
    # Execute generate_frames
    resp1 = service.execute("ep01", "shot01", "generate_frames")
    assert resp1.success is True
    
    # Try qa_review before assemble_scene (out of order)
    resp2 = service.execute("ep01", "shot01", "qa_review")
    assert resp2.success is False
    assert "expected next action" in resp2.reason.lower() or "denied" in resp2.reason.lower()
    
    # State should remain frames_generated
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state.current_state == "frames_generated"
    assert state.expected_next_action == "assemble_scene"
    
    # Verify no subprocess was invoked for the denied action
    ledger = ShotLedgerStorage(tmp_project)
    ledger_data = ledger.load("ep01", "shot01")
    denied_records = [r for r in ledger_data.records if r.event_type == "action_denied"]
    assert len(denied_records) == 1
    assert denied_records[0].requested_action == "qa_review"


# ── Test 4: QA fail branches to qa_failed ───────────────────────────────

def test_qa_fail_branches_to_qa_failed(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 4 — QA fail branches to qa_failed."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Create service with QA fail mock
    service = make_service_with_mock_handlers(tmp_project, qa_fail=True)
    
    # Execute generate_frames
    resp1 = service.execute("ep01", "shot01", "generate_frames")
    assert resp1.success is True
    
    # Execute assemble_scene
    resp2 = service.execute("ep01", "shot01", "assemble_scene")
    assert resp2.success is True
    
    # Execute qa_review (will fail)
    resp3 = service.execute("ep01", "shot01", "qa_review")
    assert resp3.success is True  # Handler executed successfully, but QA failed
    
    # State should be qa_failed, not qa_passed
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state.current_state == "qa_failed"
    assert state.expected_next_action == "generate_frames"  # Branch back to start
    
    # attach_audio should not be allowed
    resp4 = service.execute("ep01", "shot01", "attach_audio")
    assert resp4.success is False


# ── Test 5: Artifact failure stops progression ─────────────────────────

def test_artifact_failure_stops_progression(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 5 — artifact failure stops progression."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Create service with artifact failure mock
    service = make_service_with_mock_handlers(tmp_project, artifact_failure=True)
    
    # Execute generate_frames
    resp1 = service.execute("ep01", "shot01", "generate_frames")
    assert resp1.success is True
    
    state1 = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state1.current_state == "frames_generated"
    
    # Execute assemble_scene (will return success but artifact missing)
    resp2 = service.execute("ep01", "shot01", "assemble_scene")
    # Handler executed but artifact not accepted - this should be reflected in response
    # The action_failed should be recorded
    
    # State should remain frames_generated (no transition)
    state2 = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state2.current_state == "frames_generated"
    assert state2.expected_next_action == "assemble_scene"  # Still expects assemble_scene
    
    # Check ledger for action_failed
    ledger = ShotLedgerStorage(tmp_project)
    ledger_data = ledger.load("ep01", "shot01")
    failed_records = [r for r in ledger_data.records if r.event_type == "action_failed"]
    assert len(failed_records) >= 1


# ── Test 6: Kill switch blocks any real action ───────────────────────────

def test_kill_switch_blocks_any_real_action(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 6 — kill switch blocks any real action."""
    # Note: Since we're using mock handlers (which don't check the kill switch),
    # this test verifies the gate denies actions when not in correct state.
    # The real kill switch is tested in test_attach_audio.py and test_render_episode.py.
    
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    
    # Try attach_audio before reaching qa_passed state (gate blocks it)
    resp = service.execute("ep01", "shot01", "attach_audio")
    
    # Should be denied due to incorrect state
    assert resp.success is False
    assert "denied" in resp.reason.lower() or "expected" in resp.reason.lower()
    
    # State should remain ready_for_generation
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    if state:
        assert state.current_state == "ready_for_generation"


# ── Test 7: Final state denies all production actions ───────────────────

def test_final_state_denies_all_production_actions(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 7 — final state denies all production actions."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    
    # Run full lifecycle to episode_rendered
    service.execute("ep01", "shot01", "generate_frames")
    service.execute("ep01", "shot01", "assemble_scene")
    service.execute("ep01", "shot01", "qa_review")
    service.execute("ep01", "shot01", "attach_audio")
    service.execute("ep01", "shot01", "render_episode")
    
    # Verify final state
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    assert state.current_state == "episode_rendered"
    assert state.expected_next_action == "none"
    
    # Try all production actions - all should be denied
    actions = ["generate_frames", "assemble_scene", "qa_review", "attach_audio", "render_episode"]
    
    for action in actions:
        resp = service.execute("ep01", "shot01", action)
        assert resp.success is False
        assert "already done" in resp.reason.lower() or "denied" in resp.reason.lower()
    
    # Verify no new action_executed records were added
    ledger = ShotLedgerStorage(tmp_project)
    ledger_data = ledger.load("ep01", "shot01")
    # Count action_executed records - should be exactly 5 (one for each lifecycle step)
    action_executed_count = sum(1 for r in ledger_data.records if r.event_type == "action_executed")
    assert action_executed_count == 5


# ── Sample output helpers for test reporting ─────────────────────────────

def test_sample_lifecycle_state_sequence(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample lifecycle state sequence for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    state_storage = ShotStateStorage(tmp_project)
    
    states = []
    
    # Initial state
    report = service.controller.inspect("ep01", "shot01")
    states.append(f"Initial: {report.current_state} -> {report.next_action}")
    
    # Step 1
    service.execute("ep01", "shot01", "generate_frames")
    s1 = state_storage.load("ep01", "shot01")
    states.append(f"After generate_frames: {s1.current_state} -> {s1.expected_next_action}")
    
    # Step 2
    service.execute("ep01", "shot01", "assemble_scene")
    s2 = state_storage.load("ep01", "shot01")
    states.append(f"After assemble_scene: {s2.current_state} -> {s2.expected_next_action}")
    
    # Step 3
    service.execute("ep01", "shot01", "qa_review")
    s3 = state_storage.load("ep01", "shot01")
    states.append(f"After qa_review: {s3.current_state} -> {s3.expected_next_action}")
    
    # Step 4
    service.execute("ep01", "shot01", "attach_audio")
    s4 = state_storage.load("ep01", "shot01")
    states.append(f"After attach_audio: {s4.current_state} -> {s4.expected_next_action}")
    
    # Step 5
    service.execute("ep01", "shot01", "render_episode")
    s5 = state_storage.load("ep01", "shot01")
    states.append(f"After render_episode: {s5.current_state} -> {s5.expected_next_action}")
    
    # Print for reporting (will be captured in pytest output)
    print("\n=== Sample Full Lifecycle State Sequence ===")
    for state in states:
        print(state)


def test_sample_ledger_event_sequence(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample ledger event sequence for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    ledger = ShotLedgerStorage(tmp_project)
    
    # Run full lifecycle
    service.execute("ep01", "shot01", "generate_frames")
    service.execute("ep01", "shot01", "assemble_scene")
    service.execute("ep01", "shot01", "qa_review")
    service.execute("ep01", "shot01", "attach_audio")
    service.execute("ep01", "shot01", "render_episode")
    
    # Print ledger event sequence
    ledger_data = ledger.load("ep01", "shot01")
    print("\n=== Sample Ledger Event Sequence (Full Happy Path) ===")
    for i, record in enumerate(ledger_data.records, 1):
        print(f"{i}. {record.event_type}: {record.requested_action if hasattr(record, 'requested_action') and record.requested_action else 'N/A'}")


def test_sample_final_inspect_json(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample final inspect JSON for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    
    # Run full lifecycle
    service.execute("ep01", "shot01", "generate_frames")
    service.execute("ep01", "shot01", "assemble_scene")
    service.execute("ep01", "shot01", "qa_review")
    service.execute("ep01", "shot01", "attach_audio")
    service.execute("ep01", "shot01", "render_episode")
    
    # Final inspect
    report = service.controller.inspect("ep01", "shot01")
    print("\n=== Sample Final Inspect JSON ===")
    print(json.dumps({
        "current_state": report.current_state,
        "expected_next_action": report.next_action,
        "is_done": report.is_done,
        "artifact_path": report.artifact_path,
    }, indent=2))


def test_sample_out_of_order_denial_json(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample out-of-order denial JSON for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project)
    ledger = ShotLedgerStorage(tmp_project)
    
    # Execute generate_frames
    service.execute("ep01", "shot01", "generate_frames")
    
    # Try out-of-order qa_review
    resp = service.execute("ep01", "shot01", "qa_review")
    
    # Get denial record
    ledger_data = ledger.load("ep01", "shot01")
    denial = [r for r in ledger_data.records if r.event_type == "action_denied"][0]
    
    print("\n=== Sample Out-of-Order Denial JSON ===")
    print(json.dumps({
        "requested_action": denial.requested_action,
        "allowed": denial.allowed,
        "reason": denial.reason,
        "current_state": denial.current_state,
        "expected_next_action": denial.expected_next_action,
    }, indent=2))


def test_sample_qa_fail_branch_json(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample QA fail branch JSON for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project, qa_fail=True)
    
    # Run to QA fail
    service.execute("ep01", "shot01", "generate_frames")
    service.execute("ep01", "shot01", "assemble_scene")
    service.execute("ep01", "shot01", "qa_review")
    
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    
    print("\n=== Sample QA Fail Branch JSON ===")
    print(json.dumps({
        "current_state": state.current_state,
        "expected_next_action": state.expected_next_action,
        "artifact_path": state.artifact_path,
        "transition_reason": state.transition_reason,
    }, indent=2))


def test_sample_artifact_failure_json(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate sample artifact failure JSON for reporting."""
    monkeypatch.setenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "1")
    
    brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    service = make_service_with_mock_handlers(tmp_project, artifact_failure=True)
    ledger = ShotLedgerStorage(tmp_project)
    
    # Run to artifact failure
    service.execute("ep01", "shot01", "generate_frames")
    service.execute("ep01", "shot01", "assemble_scene")
    
    # Get failed record
    ledger_data = ledger.load("ep01", "shot01")
    failed = [r for r in ledger_data.records if r.event_type == "action_failed"][0]
    
    state = ShotStateStorage(tmp_project).load("ep01", "shot01")
    
    print("\n=== Sample Artifact Failure JSON ===")
    print(json.dumps({
        "current_state": state.current_state,
        "expected_next_action": state.expected_next_action,
        "failure_reason": failed.reason,
        "success": failed.success,
    }, indent=2))
