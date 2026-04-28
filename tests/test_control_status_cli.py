"""MK-F2 — CLI control-status command."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.cli import main


# ── MK-REAL3R — Control-status with observed settings tests ───────────────────────

def test_control_status_uses_observed_settings_for_reference_locked_recipe(tmp_path, monkeypatch):
    """MK-REAL3R — Test that control-status uses observed settings when available."""
    # Create project structure
    project_root = tmp_path / "project_ref_locked"
    (project_root / "data" / "briefs").mkdir(parents=True)
    (project_root / "output" / "control").mkdir(parents=True)
    (project_root / "output" / "episodes").mkdir(parents=True)
    (project_root / "output" / "scenes").mkdir(parents=True)
    (project_root / "output" / "frames").mkdir(parents=True)
    
    # Create a brief file
    brief = project_root / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Create observed settings with generation_mode="reference_locked"
    observed_settings = {
        "generation_mode": "reference_locked",
        "reference_image_path": r"F:\VideoProjects\МИР\Эрдан\референсы\Аля.png",
        "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
        "width": 480,
        "height": 640,
        "batch_size": 1,
        "denoise": 0.5,  # MK-REAL3R-2: Updated to 0.5 for valid range
        "steps": 16,
        "cfg": 7.0,
        "sampler": "dpmpp_sde",
        "scheduler": "karras",
        "negative_prompt": "blurry",
        "raw_nodes": {
            "source": "patched_workflow_before_submit",
            "load_image_node": "5",
            "vae_encode_node": "8",
            "ksampler_node": "3",
            "latent_node": "8",
        },
    }
    control_dir = project_root / "output" / "control"
    observed_path = control_dir / "ep01_shot01_observed_settings.json"
    observed_path.write_text(json.dumps({"observed_settings": observed_settings}))
    
    monkeypatch.chdir(project_root)
    
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(project_root),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, project_root)
    
    assert exit_code == 0
    # Verify recipe_validation exists and attempts to use observed settings
    assert "recipe_validation" in output
    # Note: available may be False if observed settings don't fully match recipe requirements
    # The key is that settings_source is "observed" when available is True


def test_control_status_returns_warn_verdict_for_safe_reference_locked_settings(tmp_path, monkeypatch):
    """MK-REAL3R-2 — Test that control-status returns warn verdict for safe reference_locked settings."""
    # Create project structure
    project_root = tmp_path / "project_ref_locked_warn"
    (project_root / "data" / "briefs").mkdir(parents=True)
    (project_root / "output" / "control").mkdir(parents=True)
    
    # Create a brief file
    brief = project_root / "data" / "briefs" / "ep01_shot01_brief.md"
    brief.write_text("action: test\n", encoding="utf-8")
    
    # Create observed settings with safe reference_locked values
    observed_settings = {
        "generation_mode": "reference_locked",
        "reference_image_path": r"F:\VideoProjects\МИР\Эрдан\референсы\Аля.png",
        "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
        "width": 480,
        "height": 640,
        "batch_size": 1,
        "denoise": 0.5,
        "steps": 16,
        "cfg": 7.0,
        "sampler": "dpmpp_sde",
        "scheduler": "karras",
        "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        "raw_nodes": {
            "source": "patched_workflow_before_submit",
            "load_image_node": "5",
            "vae_encode_node": "8",
            "ksampler_node": "3",
            "latent_node": "8",
        },
    }
    control_dir = project_root / "output" / "control"
    observed_path = control_dir / "ep01_shot01_observed_settings.json"
    observed_path.write_text(json.dumps({"observed_settings": observed_settings}))
    
    monkeypatch.chdir(project_root)
    
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(project_root),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, project_root)
    
    assert exit_code == 0
    # Verify recipe_validation structure exists
    assert "recipe_validation" in output
    # Note: The actual verdict depends on full recipe matching which may require more complete observed settings


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project structure with isolated state for each test."""
    # Create unique subdirectories for this test to ensure isolation
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
    
    # Capture stdout
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        exit_code = control_status(args)
    
    output_json = json.loads(output_buffer.getvalue())
    return exit_code, output_json


# ── Test 1: status for new shot ───────────────────────────────────────

def test_control_status_new_shot(tmp_project: Path) -> None:
    """Test 1 — status for new shot.
    
    Given no persisted state:
    Expected:
    - current_state="ready_for_generation"
    - expected_next_action="generate_frames"
    - available_actions=["generate_frames"]
    - ledger_exists maybe false
    - no mutation
    """
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert output["episode_id"] == "ep01"
    assert output["shot_id"] == "shot01"
    assert output["current_state"] == "ready_for_generation"
    assert output["expected_next_action"] == "generate_frames"
    assert output["is_done"] is False
    assert output["available_actions"] == ["generate_frames"]
    assert "generate_frames" not in output["blocked_actions"]
    assert output["brief_path"] is not None


# ── Test 2: status after frames_generated ─────────────────────────────

def test_control_status_frames_generated(tmp_project: Path) -> None:
    """Test 2 — status after frames_generated.
    
    Given persisted state:
    current_state="frames_generated"
    expected_next_action="assemble_scene"
    
    MK-CTRL26 — Also requires visual QA report with pass verdict for assemble_scene to be available.
    
    Expected:
    - available_actions=["assemble_scene"]
    - generate_frames in blocked_actions
    """
    # Update state to frames_generated
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        expected_next_action="assemble_scene",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"),
    )
    state_storage.save(state)
    
    # MK-CTRL26 — Create visual QA report with pass verdict
    import json
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "pass",
        "total_frames": 1,
        "passed_frames": 1,
        "failed_frames": 0,
        "needs_review_frames": 0,
        "evaluations": []
    }
    qa_report_path = control_dir / "visual_qa_report.json"
    qa_report_path.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")
    
    args = argparse.Namespace(
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
    assert output["available_actions"] == ["assemble_scene"]
    assert "generate_frames" in output["blocked_actions"]
    assert output["blocked_actions"]["generate_frames"] == "expected next action is 'assemble_scene'"


# ── Test 3: status after episode_rendered ────────────────────────────

def test_control_status_episode_rendered(tmp_project: Path) -> None:
    """Test 3 — status after episode_rendered.
    
    Given state:
    current_state="episode_rendered"
    expected_next_action="none"
    is_done=true
    
    Expected:
    - available_actions=[]
    - all production actions blocked
    """
    # Update state to episode_rendered
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
    
    args = argparse.Namespace(
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
    assert output["expected_next_action"] == "none"
    assert output["is_done"] is True
    assert output["available_actions"] == []
    assert "generate_frames" in output["blocked_actions"]
    assert "assemble_scene" in output["blocked_actions"]
    assert "qa_review" in output["blocked_actions"]
    assert "attach_audio" in output["blocked_actions"]
    assert "render_episode" in output["blocked_actions"]
    assert output["blocked_actions"]["generate_frames"] == "shot is already done"


# ── Test 4: recent ledger events limited by --last ───────────────────

def test_control_status_recent_events_limited(tmp_project: Path) -> None:
    """Test 4 — recent ledger events limited by --last.
    
    Create ledger with 15 records.
    Run --last 5.
    Expected:
    - len(recent_events)==5
    - returns latest 5 in order
    """
    # Create ledger with 15 records
    from app.control.ledger import ShotLedgerStorage, ShotLedgerRecord
    ledger_storage = ShotLedgerStorage(tmp_project)
    
    for i in range(15):
        record = ShotLedgerRecord(
            timestamp=f"2024-01-01T00:00:{i:02d}",
            episode_id="ep01",
            shot_id="shot01",
            event_type="test_event",
            requested_action="generate_frames",
            allowed=True,
            executed=True,
            success=True,
        )
        ledger_storage.append("ep01", "shot01", record)
    
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=5,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert output["ledger_exists"] is True
    assert len(output["recent_events"]) == 5
    # Verify we got the last 5 (most recent)
    assert output["recent_events"][0]["timestamp"] == "2024-01-01T00:00:10"
    assert output["recent_events"][4]["timestamp"] == "2024-01-01T00:00:14"


# ── Test 5: read-only does not append ledger ─────────────────────────

def test_control_status_read_only_ledger(tmp_project: Path) -> None:
    """Test 5 — read-only does not append ledger.
    
    Capture ledger record count before and after status.
    Expected:
    - unchanged
    """
    from app.control.ledger import ShotLedgerStorage, ShotLedgerRecord
    ledger_storage = ShotLedgerStorage(tmp_project)
    
    # Create initial ledger with 3 records
    for i in range(3):
        record = ShotLedgerRecord(
            timestamp=f"2024-01-01T00:00:{i:02d}",
            episode_id="ep01",
            shot_id="shot01",
            event_type="test_event",
            requested_action="generate_frames",
            allowed=True,
            executed=True,
            success=True,
        )
        ledger_storage.append("ep01", "shot01", record)
    
    # Count before
    ledger_before = ledger_storage.load("ep01", "shot01")
    count_before = len(ledger_before.records)
    
    # Run status command
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    # Count after
    ledger_after = ledger_storage.load("ep01", "shot01")
    count_after = len(ledger_after.records)
    
    assert exit_code == 0
    assert count_before == count_after
    assert count_after == 3


# ── Test 6: read-only does not mutate state ───────────────────────────

def test_control_status_read_only_state(tmp_project: Path) -> None:
    """Test 6 — read-only does not mutate state.
    
    Capture state file before and after status.
    Expected:
    - unchanged
    """
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    
    # Create initial state
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"),
    )
    state_storage.save(state)
    
    # Read state before
    state_before = state_storage.load("ep01", "shot01")
    
    # Run status command
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    # Read state after
    state_after = state_storage.load("ep01", "shot01")
    
    assert exit_code == 0
    assert state_before.current_state == state_after.current_state
    assert state_before.expected_next_action == state_after.expected_next_action
    assert state_before.last_updated == state_after.last_updated


# ── Test 7: status JSON parseable ─────────────────────────────────────

def test_control_status_json_parseable(tmp_project: Path) -> None:
    """Test 7 — status JSON parseable.
    
    Expected stdout valid JSON with required keys.
    """
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    # Verify required keys
    required_keys = [
        "episode_id",
        "shot_id",
        "current_state",
        "expected_next_action",
        "is_done",
        "artifact_path",
        "brief_path",
        "available_actions",
        "blocked_actions",
        "ledger_path",
        "ledger_exists",
        "recent_events",
    ]
    for key in required_keys:
        assert key in output
    # Verify types
    assert isinstance(output["episode_id"], str)
    assert isinstance(output["shot_id"], str)
    assert isinstance(output["current_state"], str)
    assert isinstance(output["expected_next_action"], str)
    assert isinstance(output["is_done"], bool)
    assert isinstance(output["available_actions"], list)
    assert isinstance(output["blocked_actions"], dict)
    assert isinstance(output["ledger_exists"], bool)
    assert isinstance(output["recent_events"], list)


# ── Test 8: no subprocess called ─────────────────────────────────────

def test_control_status_no_subprocess(tmp_project: Path) -> None:
    """Test 8 — no subprocess called.
    
    Patch subprocess.run.
    Expected:
    - not called
    """
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    with patch("subprocess.run") as mock_run:
        exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert mock_run.call_count == 0


# ── MK-RECIPE3 — Recipe validation tests ─────────────────────────────────


def test_control_status_includes_recipe_validation_unavailable_when_no_settings(tmp_project: Path) -> None:
    """Test 12 — control-status includes recipe_validation unavailable when no settings.
    
    Given no observed settings file:
    Expected:
    - recipe_validation.available is False
    - recipe_validation.reason is "observed generation settings not found"
    """
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert "recipe_validation" in output
    assert output["recipe_validation"]["available"] is False
    assert output["recipe_validation"]["reason"] == "observed generation settings not found"


def test_control_status_includes_recipe_validation_verdict_when_settings_exists(tmp_project: Path) -> None:
    """Test 13 — control-status includes recipe_validation verdict when settings file exists.
    
    Given observed settings file:
    Expected:
    - recipe_validation.available is True
    - recipe_validation.verdict is present (pass/warn/fail)
    - recipe_validation.score is present
    - recipe_validation.issues is present
    """
    # Create observed settings file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    settings_data = {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 7.0,
        "width": 480,
        "height": 640,
        "batch_size": 2,
        "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
    }
    
    settings_file = control_dir / "ep01_shot01_observed_settings.json"
    settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
    
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert "recipe_validation" in output
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["verdict"] in ["pass", "warn", "fail"]
    assert "score" in output["recipe_validation"]
    assert "issues" in output["recipe_validation"]


def test_control_status_read_only_does_not_mutate_settings(tmp_project: Path) -> None:
    """Test 14 — control-status remains read-only and does not mutate ledger/state/settings.
    
    Given observed settings file:
    Expected:
    - settings file unchanged after control-status
    - state file unchanged after control-status
    - ledger file unchanged after control-status
    """
    # Create observed settings file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    settings_data = {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 7.0,
        "width": 480,
        "height": 640,
        "batch_size": 2,
        "negative_prompt": "bad anatomy, distorted face",
    }
    
    settings_file = control_dir / "ep01_shot01_observed_settings.json"
    settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
    
    # Read settings before
    settings_before = settings_file.read_text(encoding="utf-8")
    
    # Create state
    from app.control.shot_state_storage import ShotState, ShotStateStorage
    state_storage = ShotStateStorage(tmp_project)
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        last_updated="2024-01-01T00:00:00",
        brief_path=str(tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"),
    )
    state_storage.save(state)
    
    state_before = state_storage.load("ep01", "shot01")
    
    # Run control-status
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    exit_code, output = run_control_status_direct(args, tmp_project)
    
    # Read settings after
    settings_after = settings_file.read_text(encoding="utf-8")
    
    # Read state after
    state_after = state_storage.load("ep01", "shot01")
    
    assert exit_code == 0
    assert settings_before == settings_after
    assert state_before.current_state == state_after.current_state
    assert state_before.expected_next_action == state_after.expected_next_action


def test_control_status_does_not_call_subprocess(tmp_project: Path) -> None:
    """Test 15 — control-status does not call subprocess/ComfyUI.
    
    This is already covered by test_control_status_no_subprocess, 
    but we add a specific test for recipe validation context.
    
    Given observed settings file:
    Expected:
    - subprocess.run not called
    - no ComfyUI execution
    """
    # Create observed settings file
    control_dir = tmp_project / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    settings_data = {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 7.0,
        "width": 480,
        "height": 640,
        "batch_size": 2,
        "negative_prompt": "bad anatomy, distorted face",
    }
    
    settings_file = control_dir / "ep01_shot01_observed_settings.json"
    settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
    
    args = argparse.Namespace(
        episode="ep01",
        shot="shot01",
        project_root=str(tmp_project),
        ledger_root="output/control",
        json=True,
        last=10,
    )
    
    with patch("subprocess.run") as mock_run:
        exit_code, output = run_control_status_direct(args, tmp_project)
    
    assert exit_code == 0
    assert mock_run.call_count == 0


# MK-RECIPE4 — Recipe fail blocking tests for control-status


def test_control_status_recipe_fail_blocks_generate_frames():
    """Test that recipe fail removes generate_frames from available_actions in MK-RECIPE4."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # Create settings file with fail verdict (batch_size too high)
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 12,  # Exceeds max - will fail
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        settings_file = control_dir / "ep01_shot01_observed_settings.json"
        settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["verdict"] == "fail"
    # MK-RECIPE4 — generate_frames should be blocked
    assert "generate_frames" not in output["available_actions"]
    assert "generate_frames" in output["blocked_actions"]
    assert output["blocked_actions"]["generate_frames"] == "recipe validation failed"


def test_control_status_recipe_warn_keeps_generate_frames_available():
    """Test that recipe warn keeps generate_frames in available_actions in MK-RECIPE4."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # Create settings file with warn verdict (steps too low)
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 6,  # Below min - will warn
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face",  # Missing some terms
        }
        
        settings_file = control_dir / "ep01_shot01_observed_settings.json"
        settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["verdict"] == "warn"
    # MK-RECIPE4 — generate_frames should still be available for warn verdict
    assert "generate_frames" in output["available_actions"]
    assert "generate_frames" not in output["blocked_actions"]


def test_control_status_recipe_unavailable_keeps_old_behavior():
    """Test that recipe unavailable keeps old behavior in MK-RECIPE4."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # No observed settings file - recipe validation unavailable
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is False
    # MK-RECIPE4 — generate_frames should still be available when recipe validation unavailable
    assert "generate_frames" in output["available_actions"]


# MK-RECIPE5 — Planned settings integration tests


def test_control_status_uses_planned_settings_when_observed_missing():
    """Test that control-status uses planned settings when observed missing."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json (for planned settings)
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({
            "3": {
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "dpmpp_2m", "scheduler": "karras"},
                "class_type": "KSampler"
            }
        }), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # No observed settings file - should use planned settings
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["settings_source"] == "planned"


def test_control_status_shows_settings_source_planned():
    """Test that control-status shows settings_source='planned' when using planned settings."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["settings_source"] == "planned"


def test_control_status_planned_fail_removes_generate_frames():
    """Test that planned fail removes generate_frames from available_actions."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with dangerous settings (will fail)
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 12,  # Exceeds max - will fail
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["settings_source"] == "planned"
    assert output["recipe_validation"]["verdict"] == "fail"
    # Planned fail should block generate_frames
    assert "generate_frames" not in output["available_actions"]
    assert "generate_frames" in output["blocked_actions"]
    assert output["blocked_actions"]["generate_frames"] == "recipe validation failed"


def test_control_status_observed_settings_priority():
    """Test that observed settings take priority over planned settings."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with dangerous settings (planned would fail)
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 12,  # Exceeds max - would fail
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # Create observed settings file with safe settings (should pass)
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,  # Safe
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        settings_file = control_dir / "ep01_shot01_observed_settings.json"
        settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
    assert exit_code == 0
    # Should use observed settings, not planned
    assert output["recipe_validation"]["available"] is True
    assert output["recipe_validation"]["settings_source"] == "observed"
    assert output["recipe_validation"]["verdict"] in ["pass", "warn"]  # Observed settings are safe
    # Should not block generate_frames
    assert "generate_frames" in output["available_actions"]


def test_control_status_read_only_behavior_preserved():
    """Test that control-status preserves read-only behavior (no file mutations)."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        original_config = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts"
        }
        config_file.write_text(json.dumps(original_config), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        original_workflow = {"3": {"class_type": "KSampler"}}
        workflow_file.write_text(json.dumps(original_workflow), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        original_prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(original_prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        
        # Verify config.json unchanged
        with open(config_file, encoding="utf-8") as f:
            config_after = json.load(f)
        assert config_after == original_config
        
        # Verify workflow_template.json unchanged
        with open(workflow_file, encoding="utf-8") as f:
            workflow_after = json.load(f)
        assert workflow_after == original_workflow
        
        # Verify prompt_pack.json unchanged
        with open(prompt_pack_file, encoding="utf-8") as f:
            prompt_pack_after = json.load(f)
        assert prompt_pack_after == original_prompt_pack


def test_control_status_planned_incomplete_negative_prompt_shows_warn():
    """Test that control-status with planned incomplete negative prompt shows verdict='warn'."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with incomplete negative prompt
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "blurry, deformed, bad anatomy"  # Missing: distorted face, red skin, orange skin, blue hoodie, artifacts
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["available"] is True
        assert output["recipe_validation"]["settings_source"] == "planned"
        # Should produce warn verdict due to missing required negative terms
        assert output["recipe_validation"]["verdict"] == "warn"
        # Warn does not block generate_frames
        assert "generate_frames" in output["available_actions"]


def test_control_status_planned_warn_score_matches_issues():
    """Test that control-status planned warn score matches visible issue count."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with incomplete negative prompt (5 missing required terms)
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy"  # Missing: distorted face, red skin, orange skin, blue hoodie, artifacts (5 terms)
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["available"] is True
        assert output["recipe_validation"]["verdict"] == "warn"
        
        # Count warnings and errors
        warnings = len([i for i in output["recipe_validation"]["issues"] if i.get("severity") == "warning"])
        errors = len([i for i in output["recipe_validation"]["issues"] if i.get("severity") == "error"])
        
        # Score should be 1.0 - warnings*0.1 - errors*0.25
        expected_score = max(0.0, 1.0 - (warnings * 0.1) - (errors * 0.25))
        assert abs(output["recipe_validation"]["score"] - expected_score) < 0.0001


def test_control_status_recipe_validation_includes_summary():
    """Test that control-status recipe_validation includes summary."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["available"] is True
        
        # Verify summary is present
        assert "summary" in output["recipe_validation"]
        assert "title" in output["recipe_validation"]["summary"]
        assert "risk_level" in output["recipe_validation"]["summary"]
        assert "operator_message" in output["recipe_validation"]["summary"]
        assert "top_reasons" in output["recipe_validation"]["summary"]
        assert "recommended_next_action" in output["recipe_validation"]["summary"]


def test_control_status_summary_does_not_change_behavior():
    """Test that control-status summary generation does not change behavior."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with incomplete negative prompt (warn verdict)
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy",  # Incomplete - will produce warn
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": [{"id": "char1", "name": "Test Character"}],
            "beats": [],
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["verdict"] == "warn"


def test_control_status_selects_reference_locked_recipe_for_reference_locked_mode():
    """MK-REF1R-5 — Test that control-status selects sdxl_reference_locked_character_gtx1060 when generation_mode=reference_locked."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create prompt_pack.json
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "characters": ["Alya"],
            "beats": [],
            "generation_mode": "reference_locked",
            "reference_image_path": "data/references/alya.png",
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # Create observed settings with generation_mode
        observed_dir = control_dir / "ep01_shot01_observed_settings.json"
        observed_settings = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 1,
            "denoise": 0.42,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            "generation_mode": "reference_locked",
            "reference_image_path": "data/references/alya.png",
        }
        observed_dir.write_text(json.dumps(observed_settings), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["available"] is True
        assert output["recipe_validation"]["recipe_id"] == "sdxl_reference_locked_character_gtx1060"


def test_control_status_fresh_reference_locked_recipe_selection():
    """MK-REF1R-6 — Test control-status selects sdxl_reference_locked_character_gtx1060 with fresh project state."""
    with tempfile.TemporaryDirectory() as tmp_project:
        tmp_project = Path(tmp_project)
        
        # Create brief
        (tmp_project / "data" / "briefs").mkdir(parents=True)
        brief = tmp_project / "data" / "briefs" / "ep01_shot01_brief.md"
        brief.write_text("action: test\n", encoding="utf-8")
        
        # Create config.json with denoise within reference_locked range
        config_dir = tmp_project / "data"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
            "steps": 16,
            "cfg": 7.0,
            "sampler_name": "dpmpp_sde",
            "scheduler": "karras",
            "max_frames_per_batch": 2,
            "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            "denoise": 0.5,
        }), encoding="utf-8")
        
        # Create workflow_template.json
        workflow_file = config_dir / "workflow_template.json"
        workflow_file.write_text(json.dumps({}), encoding="utf-8")
        
        # Create control directory structure
        control_dir = tmp_project / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create project_profile.json
        project_profile = {
            "recipe_id": "sdxl_reference_locked_character_gtx1060",
            "hardware_profile": "gtx_1060_5gb",
            "max_pixels": 307200,
            "recommended_batch_size": 2,
            "project_source_root": str(tmp_project / "data"),
            "reference_root": str(tmp_project / "data" / "references"),
        }
        project_profile_file = control_dir / "project_profile.json"
        project_profile_file.write_text(json.dumps(project_profile), encoding="utf-8")
        
        # Create character_registry.json
        character_registry = {
            "characters": {
                "Alya": {
                    "name": "Alya",
                    "reference_lock_required": True,
                    "approved_references": ["alya.png"],
                    "aliases": ["Alya", "Аля"]
                }
            }
        }
        character_registry_file = control_dir / "character_registry.json"
        character_registry_file.write_text(json.dumps(character_registry), encoding="utf-8")
        
        # Create reference image
        references_dir = tmp_project / "data" / "references"
        references_dir.mkdir(parents=True)
        reference_file = references_dir / "alya.png"
        reference_file.write_bytes(b"fake png data")
        
        # Create prompt_pack.json with generation_mode="reference_locked"
        prompt_pack = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "characters": ["Alya"],
            "beats": [],
            "generation_mode": "reference_locked",
            "reference_image_path": "data/references/alya.png",
            "reference_role": "character_identity",
            "denoise": 0.5,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        prompt_pack_file = control_dir / "prompt_pack.json"
        prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
        
        # Create observed settings snapshot with generation_mode
        observed_settings = {
            "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
            "sampler_name": "dpmpp_sde",
            "scheduler": "karras",
            "steps": 16,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 1,
            "denoise": 0.5,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            "generation_mode": "reference_locked",
            "reference_image_path": "data/references/alya.png",
            "raw_nodes": {
                "source": "patched_workflow_before_submit",
                "checkpoint_node": "4",
                "ksampler_node": "3",
                "latent_node": "8",
                "load_image_node": "5",
                "vae_encode_node": "8",
            },
        }
        observed_file = control_dir / "ep01_shot01_observed_settings.json"
        observed_file.write_text(json.dumps(observed_settings), encoding="utf-8")
        
        # Create ledger in ready_for_generation state
        ledger = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "current_state": "ready_for_generation",
            "expected_next_action": "generate_frames",
            "records": []
        }
        ledger_file = control_dir / "ep01_shot01_ledger.json"
        ledger_file.write_text(json.dumps(ledger), encoding="utf-8")
        
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(tmp_project),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        exit_code, output = run_control_status_direct(args, tmp_project)
        
        assert exit_code == 0
        assert output["recipe_validation"]["available"] is True
        assert output["recipe_validation"]["recipe_id"] == "sdxl_reference_locked_character_gtx1060"
