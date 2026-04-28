"""MK-CTRL28 — Operator CLI Full Lifecycle E2E tests.

Proves the full shot lifecycle through operator CLI commands only:
- control-status for read-only inspection
- control-shot for controlled action execution

No direct service.execute calls. Uses mocked subprocess and fake artifacts.
"""
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from argparse import Namespace


@pytest.fixture
def patched_shot_control_service(tmp_project: Path):
    """Fixture that provides a patched build_shot_control_service function with mocked handlers."""
    from app.control import factory
    original_build = factory.build_shot_control_service
    
    def patched_build(project_root, enable_mock_handlers=True):
        service = original_build(project_root, enable_mock_handlers=enable_mock_handlers)
        
        # Patch the handlers in the service's handler registry
        def patched_generate_frames(payload):
            if payload is None:
                payload = {}
            # Handle both dict and HandlerPayload
            if hasattr(payload, 'to_dict'):
                payload = payload.to_dict()
            
            from app.control import handlers
            result = handlers.generate_frames_handler(payload)
            create_fake_frame_manifest(tmp_project)
            result["artifacts"] = {
                "frame_manifest_path": str(tmp_project / "output" / "control" / "frame_manifest.json"),
                "episode_output_path": str(tmp_project / "output" / payload.get("shot_id", "shot01")),
                "artifact_status": "accepted",
                "artifact_accepted": True,
            }
            return result
        
        def patched_assemble_scene(payload):
            if payload is None:
                payload = {}
            # Handle both dict and HandlerPayload
            if hasattr(payload, 'to_dict'):
                payload = payload.to_dict()
            
            from app.control import handlers
            result = handlers.assemble_scene_handler(payload)
            create_fake_scene_mp4(tmp_project)
            result["artifacts"] = {
                "scene_output_path": str(tmp_project / "output" / "scenes" / f"{payload.get('episode_id', 'ep01')}_{payload.get('shot_id', 'shot01')}.mp4"),
                "artifact_status": "accepted",
                "artifact_accepted": True,
            }
            return result
        
        def patched_qa_review(payload):
            if payload is None:
                payload = {}
            # Handle both dict and HandlerPayload
            if hasattr(payload, 'to_dict'):
                payload = payload.to_dict()
            
            from app.control import handlers
            result = handlers.qa_review_handler(payload)
            create_fake_qa_report(tmp_project, verdict="pass")
            result["artifacts"] = {
                "qa_report_path": str(tmp_project / "output" / "control" / "qa_report.json"),
                "artifact_status": "accepted",
                "artifact_accepted": True,
            }
            return result
        
        def patched_attach_audio(payload):
            try:
                if payload is None:
                    payload = {}
                # Handle both dict and HandlerPayload
                if hasattr(payload, 'to_dict'):
                    payload = payload.to_dict()
                
                # Extract scene_mp4_path and brief_path from action_plan
                action_plan = payload.get("action_plan", {})
                scene_mp4_path = action_plan.get("scene_mp4_path") or payload.get("scene_mp4_path")
                brief_path = action_plan.get("brief_path") or payload.get("brief_path")
                
                # Call the original handler with the correct fields
                from app.control import handlers
                result = handlers.attach_audio_handler({
                    "scene_mp4_path": scene_mp4_path,
                    "brief_path": brief_path,
                })
                create_fake_audio_mp4(tmp_project, skip=False)
                # Add artifacts with the correct structure
                result["artifacts"] = {
                    "scene_mp4_with_audio_path": str(tmp_project / "output" / "scenes" / f"{payload.get('episode_id', 'ep01')}_{payload.get('shot_id', 'shot01')}_audio.mp4"),
                    "artifact_status": "accepted",
                    "artifact_accepted": True,
                }
                return result
            except Exception as e:
                print(f"Error in patched_attach_audio: {e}")
                print(f"Payload: {payload}")
                raise
        
        def patched_render_episode(payload):
            if payload is None:
                payload = {}
            # Handle both dict and HandlerPayload
            if hasattr(payload, 'to_dict'):
                payload = payload.to_dict()
            
            from app.control import handlers
            result = handlers.final_render_handler(payload)
            create_fake_episode_mp4(tmp_project)
            result["artifacts"] = {
                "final_episode_mp4_path": str(tmp_project / "output" / "episodes" / f"{payload.get('episode_id', 'ep01')}_{payload.get('shot_id', 'shot01')}_episode.mp4"),
                "artifact_status": "accepted",
                "artifact_accepted": True,
            }
            return result
        
        # Replace handlers in the service's handler registry
        if service.handler_registry:
            service.handler_registry._handlers["generate_frames"] = patched_generate_frames
            service.handler_registry._handlers["assemble_scene"] = patched_assemble_scene
            service.handler_registry._handlers["assemble_scene_video"] = patched_assemble_scene
            service.handler_registry._handlers["qa_review"] = patched_qa_review
            service.handler_registry._handlers["attach_audio"] = patched_attach_audio
            service.handler_registry._handlers["synthesize_and_mux_audio"] = patched_attach_audio
            service.handler_registry._handlers["render_episode"] = patched_render_episode
            service.handler_registry._handlers["assemble_episode"] = patched_render_episode
            
            # Update the service's handlers dict
            service.handlers = service.handler_registry.enabled_handlers()
            
            # Also update the runner's handlers dict directly
            if hasattr(service._runner, 'handlers'):
                service._runner.handlers = service.handlers
        else:
            # Fallback: patch handlers dict directly
            service.handlers["generate_frames"] = patched_generate_frames
            service.handlers["assemble_scene"] = patched_assemble_scene
            service.handlers["qa_review"] = patched_qa_review
            service.handlers["attach_audio"] = patched_attach_audio
            service.handlers["synthesize_and_mux_audio"] = patched_attach_audio
            service.handlers["render_episode"] = patched_render_episode
            
            # Also update the runner's handlers dict directly
            if hasattr(service._runner, 'handlers'):
                service._runner.handlers = service.handlers
        
        return service
    
    return patched_build


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project structure with isolated state for each test."""
    test_id = os.urandom(4).hex()
    project_root = tmp_path / f"project_{test_id}"
    
    (project_root / "data" / "briefs").mkdir(parents=True)
    (project_root / "output" / "control").mkdir(parents=True)
    (project_root / "output" / "episodes").mkdir(parents=True)
    (project_root / "output" / "scenes").mkdir(parents=True)
    (project_root / "output" / "frames").mkdir(parents=True)
    
    # Create a brief file
    brief = project_root / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    return project_root


def run_control_status_direct(args: Namespace, project_root: Path) -> tuple[int, dict]:
    """Helper to run control-status function directly."""
    from app.cli import control_status
    
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        exit_code = control_status(args)
    
    output_json = json.loads(output_buffer.getvalue())
    return exit_code, output_json


def run_control_shot_direct(args: Namespace, project_root: Path) -> tuple[int, dict]:
    """Helper to run control-shot function directly."""
    from app.cli import control_shot
    
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
        exit_code = control_shot(args)
    
    output_str = output_buffer.getvalue()
    error_str = error_buffer.getvalue()
    
    # If stdout is empty, try to parse stderr
    if output_str.strip():
        try:
            output_json = json.loads(output_str)
        except json.JSONDecodeError as e:
            print(f"DEBUG: Failed to parse JSON: {e}")
            print(f"DEBUG: First 500 chars of output_str: {output_str[:500]}")
            print(f"DEBUG: Last 500 chars of output_str: {output_str[-500:]}")
            raise
    elif error_str.strip():
        # Error was printed to stderr
        print(f"Error from control_shot: {error_str}")
        output_json = {
            "success": False,
            "reason": error_str.strip(),
            "state_report": None,
            "gate_decision": None,
            "action_plan": None,
            "action_result": None,
        }
    else:
        raise ValueError("No output from control_shot")
    
    return exit_code, output_json


def create_fake_frame_manifest(project_root: Path) -> Path:
    """Create fake frame manifest artifact."""
    manifest_path = project_root / "output" / "control" / "frames_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "brief_path": str(project_root / "data" / "briefs" / "ep01_shot01_brief.md"),
        "generated_frames_dir": str(project_root / "output" / "frames" / "ep01_shot01"),
        "frame_count": 1,
        "frame_paths": [str(project_root / "output" / "frames" / "ep01_shot01" / "frame_0001.png")],
        "created_at": "2024-01-01T00:00:00",
    }
    
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Create fake frame file
    frame_dir = project_root / "output" / "frames" / "ep01_shot01"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_file = frame_dir / "frame_0001.png"
    frame_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # Minimal PNG
    
    return manifest_path


def create_fake_scene_mp4(project_root: Path) -> Path:
    """Create fake scene MP4 artifact."""
    scene_path = project_root / "output" / "scenes" / "ep01_shot01.mp4"
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_bytes(b"FAKE_MP4" + b"\x00" * 100)
    
    # Create scene manifest
    manifest_path = project_root / "output" / "control" / "scene_manifest.json"
    manifest = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "scene_output_path": str(scene_path),
        "scene_frame_count": 1,
        "scene_duration_sec": 2.0,
        "fps": 24,
        "created_at": "2024-01-01T00:00:00",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return scene_path


def create_fake_qa_report(project_root: Path, verdict: str = "pass") -> Path:
    """Create fake QA report artifact."""
    qa_report_path = project_root / "output" / "control" / "qa_report.json"
    qa_report_path.parent.mkdir(parents=True, exist_ok=True)
    
    qa_score = 0.85 if verdict == "pass" else 0.5
    qa_verdict = verdict
    
    qa_report = {
        "scene_path": str(project_root / "output" / "scenes" / "ep01_shot01.mp4"),
        "scene_size_bytes": 104,
        "qa_score": qa_score,
        "qa_verdict": qa_verdict,
        "qa_reasons": [] if verdict == "pass" else ["blurry"],
        "created_at": "2024-01-01T00:00:00",
    }
    
    qa_report_path.write_text(json.dumps(qa_report, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return qa_report_path


def create_fake_audio_mp4(project_root: Path, skip: bool = False) -> Path:
    """Create fake audio MP4 artifact or audio manifest for skip."""
    if skip:
        audio_manifest_path = project_root / "output" / "control" / "audio_manifest.json"
        audio_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        audio_manifest = {
            "scene_path": str(project_root / "output" / "scenes" / "ep01_shot01.mp4"),
            "audio_output_path": str(project_root / "output" / "scenes" / "ep01_shot01.mp4"),  # Same file for skip
            "brief_path": str(project_root / "data" / "briefs" / "ep01_shot01_brief.md"),
            "audio_duration_sec": 0.0,
            "audio_engine": "silero",
            "dialogue_lines": 0,
            "artifact_status": "skipped_no_audio",
            "artifact_reason": "no dialogue in brief",
            "created_at": "2024-01-01T00:00:00",
        }
        
        audio_manifest_path.write_text(json.dumps(audio_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return audio_manifest_path
    else:
        audio_path = project_root / "output" / "scenes" / "ep01_shot01_audio.mp4"
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"FAKE_AUDIO_MP4" + b"\x00" * 100)
        
        audio_manifest_path = project_root / "output" / "control" / "audio_manifest.json"
        audio_manifest = {
            "scene_path": str(project_root / "output" / "scenes" / "ep01_shot01.mp4"),
            "audio_output_path": str(audio_path),
            "brief_path": str(project_root / "data" / "briefs" / "ep01_shot01_brief.md"),
            "audio_duration_sec": 2.0,
            "audio_engine": "silero",
            "dialogue_lines": 5,
            "artifact_status": "accepted",
            "artifact_reason": "audio attached successfully",
            "created_at": "2024-01-01T00:00:00",
        }
        audio_manifest_path.write_text(json.dumps(audio_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        
        return audio_path


def create_fake_episode_mp4(project_root: Path) -> Path:
    """Create fake final episode MP4 artifact."""
    episode_path = project_root / "output" / "episodes" / "ep01_shot01_episode.mp4"
    episode_path.parent.mkdir(parents=True, exist_ok=True)
    episode_path.write_bytes(b"FAKE_EPISODE_MP4" + b"\x00" * 100)
    
    # Create episode manifest
    manifest_path = project_root / "output" / "control" / "episode_manifest.json"
    manifest = {
        "scene_path": str(project_root / "output" / "scenes" / "ep01_shot01_audio.mp4"),
        "episode_output_path": str(episode_path),
        "episode_duration_sec": 2.0,
        "episode_scene_count": 1,
        "artifact_status": "accepted",
        "artifact_reason": "episode rendered successfully",
        "created_at": "2024-01-01T00:00:00",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return episode_path


# ── Test 1: Full CLI lifecycle reaches episode_rendered ───────────────

def test_full_cli_lifecycle_reaches_episode_rendered(tmp_project: Path, patched_shot_control_service) -> None:
    """Test 1 — Full CLI lifecycle reaches episode_rendered.
    
    Using CLI only with execute mode and patched mock handlers:
    1. status new shot
    2. control-shot generate_frames --execute
    3. status
    4. control-shot assemble_scene --execute
    5. status
    6. control-shot qa_review --execute
    7. status
    8. control-shot attach_audio --execute
    9. status
    10. control-shot render_episode --execute
    11. final status
    
    Expected final state: episode_rendered
    """
    # Import factory for patching
    from app.control import factory
    
    # Apply the patch using the fixture
    with patch.object(factory, "build_shot_control_service", side_effect=patched_shot_control_service):
        # Step 1: status new shot
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["current_state"] == "ready_for_generation"
        assert output["expected_next_action"] == "generate_frames"
        
        # Step 2: control-shot generate_frames execute
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="generate_frames",
            execute=True,
            allow_real=False,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        if exit_code != 0:
            print(f"generate_frames failed with exit code {exit_code}")
            print(f"Output: {json.dumps(output, indent=2)}")
        assert exit_code == 0
        assert output["success"] is True
        
        # Step 3: status
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["current_state"] == "frames_generated"
        assert output["expected_next_action"] == "assemble_scene"
        
        # Step 4: control-shot assemble_scene execute
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="assemble_scene",
            execute=True,
            allow_real=False,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        assert exit_code == 0
        assert output["success"] is True
        
        # Step 5: status
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["expected_next_action"] == "qa_review"
        
        # Step 6: control-shot qa_review execute
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="qa_review",
            execute=True,
            allow_real=False,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        if exit_code != 0:
            print(f"qa_review failed with exit code {exit_code}")
            print(f"Output: {json.dumps(output, indent=2)}")
        assert exit_code == 0
        assert output["success"] is True
        
        # Step 7: status
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["expected_next_action"] == "attach_audio"
        
        # Step 8: control-shot attach_audio execute
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="attach_audio",
            execute=True,
            allow_real=False,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        if exit_code != 0:
            print(f"attach_audio failed with exit code {exit_code}")
            print(f"Output: {json.dumps(output, indent=2)}")
        assert exit_code == 0
        assert output["success"] is True
        
        # Step 9: status
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["expected_next_action"] == "render_episode"
        
        # Step 10: control-shot render_episode execute
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="render_episode",
            execute=True,
            allow_real=False,
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        assert exit_code == 0
        assert output["success"] is True
        
        # Step 11: final status
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        assert exit_code == 0
        assert output["current_state"] == "episode_rendered"
        assert output["is_done"] is True
        assert output["available_actions"] == []


# ── Test 2: Every control-shot call executes exactly one action ─────────

def test_every_control_shot_executes_exactly_one_action(tmp_project: Path, monkeypatch: pytest.MonkeyPatch, patched_shot_control_service) -> None:
    """Test 2 — Every control-shot call executes exactly one action.
    
    Check ledger after full flow:
    action_executed count == 5
    executed actions list exactly:
    [generate_frames, assemble_scene, qa_review, attach_audio, render_episode]
    
    No duplicate action. No auto-next-action.
    """
    # Import factory for patching
    from app.control import factory
    
    # Apply the patch using the fixture
    with patch.object(factory, "build_shot_control_service", side_effect=patched_shot_control_service):
        # Execute each action in sequence with state transitions
        actions = [
            "generate_frames",
            "assemble_scene",
            "qa_review",
            "attach_audio",
            "render_episode",
        ]
        
        for action in actions:
            args = Namespace(
                episode="ep01",
                shot="shot01",
                action=action,
                execute=True,
                allow_real=False,  # Use mock handlers for safety
                ledger_root="output/control",
                project_root=str(tmp_project),
                json=True,
            )
            exit_code, output = run_control_shot_direct(args, tmp_project)
            assert exit_code == 0, f"Action {action} failed with exit code {exit_code}: {output}"
            
            # Check status after each action (like the main lifecycle test)
            args = Namespace(
                episode="ep01",
                shot="shot01",
                project_root=str(tmp_project),
                ledger_root="output/control",
                json=True,
                last=10,
            )
            exit_code, status_output = run_control_status_direct(args, tmp_project)
            assert exit_code == 0
    
    # Check ledger
    from app.control.ledger import ShotLedgerStorage
    ledger_storage = ShotLedgerStorage(tmp_project)
    ledger = ledger_storage.load("ep01", "shot01")
    
    # Count action_executed events
    action_executed_events = [r for r in ledger.records if r.event_type == "action_executed"]
    assert len(action_executed_events) == 5
    
    # Verify exact action sequence
    executed_actions = [r.requested_action for r in action_executed_events]
    assert executed_actions == ["generate_frames", "assemble_scene", "qa_review", "attach_audio", "render_episode"]
    
    # Verify no duplicates
    assert len(executed_actions) == len(set(executed_actions))


# ── Test 3: Status is read-only during full lifecycle ───────────────────

def test_status_is_read_only_during_lifecycle(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 3 — Status is read-only during full lifecycle.
    
    For every control-status call:
    - ledger count does not increase
    - state does not mutate
    """
    def mock_subprocess_run(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        
        if "generate-frames" in cmd_str or "run" in cmd_str:
            create_fake_frame_manifest(tmp_project)
        elif "assemble-scene" in cmd_str:
            create_fake_scene_mp4(tmp_project)
        elif "qa-review" in cmd_str:
            create_fake_qa_report(tmp_project, verdict="pass")
        elif "attach-audio" in cmd_str:
            create_fake_audio_mp4(tmp_project, skip=True)
        elif "render-episode" in cmd_str:
            create_fake_episode_mp4(tmp_project)
        
        return MagicMock(returncode=0, stdout=b"", stderr=b"")
    
    with patch("subprocess.run", side_effect=mock_subprocess_run):
        from app.control.ledger import ShotLedgerStorage
        from app.control.shot_state_storage import ShotStateStorage
        
        ledger_storage = ShotLedgerStorage(tmp_project)
        state_storage = ShotStateStorage(tmp_project)
        
        # Create fake frames manifest, then execute generate_frames
        create_fake_frame_manifest(tmp_project)
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="generate_frames",
            execute=True,
            allow_real=False,  # Use mock handlers for safety
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        
        # Check status before and after
        ledger_before = ledger_storage.load("ep01", "shot01")
        count_before = len(ledger_before.records)
        state_before = state_storage.load("ep01", "shot01")
        
        args = Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        ledger_after = ledger_storage.load("ep01", "shot01")
        count_after = len(ledger_after.records)
        state_after = state_storage.load("ep01", "shot01")
        
        # Status should not mutate ledger or state
        assert count_before == count_after
        assert state_before.current_state == state_after.current_state


# ── Test 4: Out-of-order CLI action denied ────────────────────────────

def test_out_of_order_cli_action_denied(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 4 — Out-of-order CLI action denied.
    
    After generate_frames, call:
    control-shot --action qa_review --execute
    
    Expected:
    - exit code 2
    - state remains frames_generated
    - no subprocess
    """
    def mock_subprocess_run(cmd, *args, **kwargs):
        create_fake_frame_manifest(tmp_project)
        return MagicMock(returncode=0, stdout=b"", stderr=b"")
    
    with patch("subprocess.run", side_effect=mock_subprocess_run):
        # Create fake frames manifest, then execute generate_frames
        create_fake_frame_manifest(tmp_project)
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="generate_frames",
            execute=True,
            allow_real=False,  # Use mock handlers for safety
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        assert exit_code == 0
        
        # Try out-of-order qa_review
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action="qa_review",
            execute=True,
            allow_real=False,  # Use mock handlers for safety
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        
        assert exit_code == 2
        assert output["gate_decision"]["allowed"] is False
        assert output["action_result"]["production_executed"] is False
        assert output["action_result"]["subprocess_invoked"] is False
        
        # Verify state remains frames_generated
        from app.control.shot_state_storage import ShotStateStorage
        state_storage = ShotStateStorage(tmp_project)
        state = state_storage.load("ep01", "shot01")
        assert state.current_state == "frames_generated"


# ── Test 5: Kill switch blocks via CLI ────────────────────────────────

def test_kill_switch_blocks_via_cli(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 5 — Kill switch blocks via CLI.
    
    Env disabled. Call next valid action with --execute --allow-real.
    
    Expected:
    - exit code 3
    - action_blocked
    - state unchanged
    - subprocess_invoked=false
    """
    # Ensure env is disabled
    monkeypatch.delenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", raising=False)
    
    # Do NOT patch the factory - let the real kill switch check happen
    # Execute generate_frames (should be blocked by kill switch)
    args = Namespace(
        episode="ep01",
        shot="shot01",
        action="generate_frames",
        execute=True,
        allow_real=True,
        ledger_root="output/control",
        project_root=str(tmp_project),
        json=True,
    )
    exit_code, output = run_control_shot_direct(args, tmp_project)
    
    assert exit_code == 3
    assert output["action_result"]["handler_status"] == "blocked"
    assert output["action_result"]["production_executed"] is False
    assert output["action_result"]["subprocess_invoked"] is False
    
    # Verify state unchanged (should still be ready_for_generation or None if never persisted)
    from app.control.shot_state_storage import ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    state = state_storage.load("ep01", "shot01")
    # State should be None (never persisted) or ready_for_generation (initial state)
    assert state is None or state.current_state == "ready_for_generation"


# ── Test 6: Final state denies all actions via CLI ───────────────────

def test_final_state_denies_all_actions_via_cli(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 6 — Final state denies all actions via CLI.
    
    After episode_rendered, try all actions:
    - generate_frames
    - assemble_scene
    - qa_review
    - attach_audio
    - render_episode
    
    Expected:
    - exit code 2
    - reason "shot is already done"
    - no subprocess
    - state remains episode_rendered
    """
    # Set state to episode_rendered
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="episode_rendered",
        expected_next_action="none",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"),
    )
    state_storage.save(state)
    
    # Try all actions - all should be denied
    actions = ["generate_frames", "assemble_scene", "qa_review", "attach_audio", "render_episode"]
    
    for action in actions:
        args = Namespace(
            episode="ep01",
            shot="shot01",
            action=action,
            execute=True,
            allow_real=False,  # Use mock handlers for safety
            ledger_root="output/control",
            project_root=str(tmp_project),
            json=True,
        )
        exit_code, output = run_control_shot_direct(args, tmp_project)
        
        assert exit_code == 2
        assert output["gate_decision"]["allowed"] is False
        assert "shot is already done" in output["gate_decision"]["reason"].lower() or "done" in output["gate_decision"]["reason"].lower()
        assert output["action_result"]["production_executed"] is False
        assert output["action_result"]["subprocess_invoked"] is False
    
    # Verify state remains episode_rendered
    state = state_storage.load("ep01", "shot01")
    assert state.current_state == "episode_rendered"
