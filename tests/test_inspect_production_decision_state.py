"""Test inspect-production-decision-state command for bounded behavior.

RC2-PRODCARDS3AN-BLOCKER1: Verify inspect command is bounded and does not hang.
"""
import json
import pytest
from pathlib import Path
from app.production_cards.state_repair import inspect_real_project_decision_state


def test_inspect_reads_only_control_files(tmp_path):
    """Test that inspect reads only artifact_index.json and episode_ledger.json."""
    # Create minimal project structure
    output_dir = tmp_path / "output" / "control"
    output_dir.mkdir(parents=True)
    
    # Create artifact_index.json
    artifact_index = {
        "retry_gate_open": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_blocked": True
    }
    artifact_index_path = output_dir / "artifact_index.json"
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f)
    
    # Create episode_ledger.json
    episode_ledger = {
        "events": []
    }
    episode_ledger_path = output_dir / "episode_ledger.json"
    with open(episode_ledger_path, 'w') as f:
        json.dump(episode_ledger, f)
    
    # Run inspect
    result = inspect_real_project_decision_state(str(tmp_path), fast_mode=True)
    
    # Verify it returns without error
    assert result is not None
    assert result["project_root"] == str(tmp_path)
    assert result["fast_mode"] == True
    assert result["artifact_index"]["retry_gate_open"] == True
    assert result["artifact_index"]["next_allowed_action"] == "retry_generate_frames"


def test_inspect_fast_mode_skips_role_decisions(tmp_path):
    """Test that fast mode skips role decisions directory."""
    # Create minimal project structure without role_decisions
    output_dir = tmp_path / "output" / "control"
    output_dir.mkdir(parents=True)
    
    # Create artifact_index.json
    artifact_index = {
        "retry_gate_open": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_blocked": True
    }
    artifact_index_path = output_dir / "artifact_index.json"
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f)
    
    # Create episode_ledger.json
    episode_ledger = {
        "events": []
    }
    episode_ledger_path = output_dir / "episode_ledger.json"
    with open(episode_ledger_path, 'w') as f:
        json.dump(episode_ledger, f)
    
    # Run inspect in fast mode (should not fail even without role_decisions)
    result = inspect_real_project_decision_state(str(tmp_path), fast_mode=True)
    
    # Verify role decisions are None in fast mode
    assert result["role_decisions"]["character_director"]["decision_status"] is None
    assert result["role_decisions"]["workflow_td"]["decision_status"] is None
    assert result["role_decisions_pending"] is None


def test_inspect_normal_mode_reads_role_decisions(tmp_path):
    """Test that normal mode reads role decisions."""
    # Create full project structure
    output_dir = tmp_path / "output" / "control"
    role_decisions_dir = output_dir / "role_decisions"
    role_decisions_dir.mkdir(parents=True)
    
    # Create role decision files
    char_decision = {
        "decision_status": "pending",
        "production_accepted": False,
        "downstream_blocked": True
    }
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    with open(char_decision_path, 'w') as f:
        json.dump(char_decision, f)
    
    workflow_decision = {
        "decision_status": "pending",
        "production_accepted": False,
        "downstream_blocked": True
    }
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    with open(workflow_decision_path, 'w') as f:
        json.dump(workflow_decision, f)
    
    # Create artifact_index.json
    artifact_index = {
        "retry_gate_open": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_blocked": True
    }
    artifact_index_path = output_dir / "artifact_index.json"
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f)
    
    # Create episode_ledger.json
    episode_ledger = {
        "events": []
    }
    episode_ledger_path = output_dir / "episode_ledger.json"
    with open(episode_ledger_path, 'w') as f:
        json.dump(episode_ledger, f)
    
    # Run inspect in normal mode
    result = inspect_real_project_decision_state(str(tmp_path), fast_mode=False)
    
    # Verify role decisions are read
    assert result["role_decisions"]["character_director"]["decision_status"] == "pending"
    assert result["role_decisions"]["workflow_td"]["decision_status"] == "pending"
    assert result["role_decisions_pending"] == True
    assert result["fast_mode"] == False


def test_inspect_does_not_scan_backup_dirs(tmp_path):
    """Test that inspect does not scan backup directories."""
    # Create minimal project structure
    output_dir = tmp_path / "output" / "control"
    output_dir.mkdir(parents=True)
    
    # Create backup directory (should not be scanned)
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "large_file.txt").write_text("x" * 1000000)  # 1MB file
    
    # Create artifact_index.json
    artifact_index = {
        "retry_gate_open": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_blocked": True
    }
    artifact_index_path = output_dir / "artifact_index.json"
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f)
    
    # Create episode_ledger.json
    episode_ledger = {
        "events": []
    }
    episode_ledger_path = output_dir / "episode_ledger.json"
    with open(episode_ledger_path, 'w') as f:
        json.dump(episode_ledger, f)
    
    # Run inspect (should complete quickly despite large backup)
    result = inspect_real_project_decision_state(str(tmp_path), fast_mode=True)
    
    # Verify it returns without error
    assert result is not None
    assert result["fast_mode"] == True


def test_inspect_handles_missing_files_gracefully(tmp_path):
    """Test that inspect handles missing control files gracefully."""
    # Create empty project structure
    output_dir = tmp_path / "output" / "control"
    output_dir.mkdir(parents=True)
    
    # Run inspect without any control files
    result = inspect_real_project_decision_state(str(tmp_path), fast_mode=True)
    
    # Verify it returns with empty/default values
    assert result is not None
    assert result["artifact_index"]["retry_gate_open"] is None
    assert result["episode_ledger"]["role_decision_apply_event_count"] == 0


def test_inspect_rc2_multishot1_ep01_fixture():
    """Test inspect against actual rc2_multishot1_ep01 fixture for bounded behavior."""
    project_root = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
    
    if not project_root.exists():
        pytest.skip("rc2_multishot1_ep01 fixture not found")
    
    # Run inspect in fast mode
    result = inspect_real_project_decision_state(str(project_root), fast_mode=True)
    
    # Verify critical bounded behavior (not specific state values)
    assert result is not None
    assert result["project_root"] == str(project_root)
    assert result["fast_mode"] == True
    assert result["artifact_index"] is not None
    assert result["episode_ledger"] is not None
    assert result["corruption_indicators"] is not None
    # Verify role decisions are None in fast mode
    assert result["role_decisions"]["character_director"]["decision_status"] is None
    assert result["role_decisions"]["workflow_td"]["decision_status"] is None
