"""
Tests for Director-lite CLI integration.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_director_status_returns_terminal_rc1_status():
    """Test that director status returns terminal RC1 status."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["current_state"] == "episode_rendered"
    assert output["expected_next_action"] == "none"
    assert output["is_done"] is True


def test_director_validate_returns_validation_passed():
    """Test that director validate returns validation passed."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "validate",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["validation_status"] == "passed"
    assert output["passed_checks"] == 67
    assert output["errors"] == 0


def test_director_inspect_lists_required_artifacts():
    """Test that director inspect lists required artifacts."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "inspect",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["project_profile"] is not None
    assert output["prompt_pack"] is not None
    assert output["frames_manifest"] is not None
    assert output["generated_frame"] is not None
    assert output["ledger"] is not None
    assert output["artifact_index"] is not None


def test_director_history_parses_ledger_events():
    """Test that director history parses ledger events."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "history",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert "events" in output
    assert "summary" in output
    assert len(output["events"]) > 0
    assert output["summary"]["total_events"] > 0


def test_director_help_works():
    """Test that director help command works."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Director-lite" in result.stdout
    assert "status" in result.stdout
    assert "validate" in result.stdout
    assert "inspect" in result.stdout
    assert "history" in result.stdout


def test_missing_project_root_returns_structured_error():
    """Test that missing project-root returns structured error."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    # Should fail due to missing required argument
    assert result.returncode != 0


def test_json_returns_valid_json():
    """Test that --json returns valid JSON."""
    result = subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Should be valid JSON
    json.loads(result.stdout)


def test_director_commands_do_not_mutate_artifact_index():
    """Test that director commands do not mutate artifact_index.json."""
    # Read artifact_index before
    artifact_index_path = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01\\output\\control\\artifact_index.json")
    with open(artifact_index_path, 'r') as f:
        before = f.read()
    
    # Run director command
    subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    # Read artifact_index after
    with open(artifact_index_path, 'r') as f:
        after = f.read()
    
    # Should be unchanged
    assert before == after, "artifact_index.json was mutated"


def test_director_commands_do_not_mutate_ledger():
    """Test that director commands do not mutate ledger."""
    # Read ledger before
    ledger_path = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01\\output\\control\\ep01_shot01_ledger.json")
    with open(ledger_path, 'r') as f:
        before = f.read()
    
    # Run director command
    subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    # Read ledger after
    with open(ledger_path, 'r') as f:
        after = f.read()
    
    # Should be unchanged
    assert before == after, "ledger was mutated"


def test_director_commands_do_not_mutate_shot_state():
    """Test that director commands do not mutate shot state."""
    # Read shot state before
    state_path = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01\\output\\control\\ep01\\shot01_state.json")
    with open(state_path, 'r') as f:
        before = f.read()
    
    # Run director command
    subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    # Read shot state after
    with open(state_path, 'r') as f:
        after = f.read()
    
    # Should be unchanged
    assert before == after, "shot state was mutated"


def test_director_history_jsonl_is_written_as_read_only_audit():
    """Test that director_history.jsonl is written as read-only audit."""
    # Run a director command
    subprocess.run(
        [sys.executable, "-m", "app", "director", "status",
         "--project-root", "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01",
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True
    )
    
    # Check that director_history.jsonl exists
    history_path = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01\\output\\control\\director_history.jsonl")
    assert history_path.exists(), "director_history.jsonl was not created"
    
    # Check that it contains valid JSONL
    with open(history_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "director_history.jsonl is empty"
    
    # Check that each line is valid JSON
    for line in lines:
        record = json.loads(line)
        assert "timestamp" in record
        assert "command" in record
        assert "read_only" in record
        assert record["read_only"] is True
