import pytest
import json
import os
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.state_machine import CombineStateMachine
from app.cli import main as cli_main

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Initialize with a state that can transition to operator_visual_review
    # visual_qa_required -> operator_visual_review
    artifact_index = {
        "current_state": "visual_qa_required",
        "route_family": "portrait_character_identity"
    }
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(artifact_index, f)
        
    return project_root

def test_operator_visual_decision_accept(temp_project, monkeypatch):
    """Test 'accept' decision via CLI."""
    project_root_str = str(temp_project)
    
    # 1. Run CLI command
    test_args = [
        "app/cli.py", "combine-operator-visual-decision",
        "--project-root", project_root_str,
        "--decision", "accept",
        "--json"
    ]
    
    # Mock sys.argv
    monkeypatch.setattr("sys.argv", test_args)
    
    # Execute
    with pytest.raises(SystemExit) as excinfo:
        cli_main()
    assert excinfo.value.code == 0
    
    # 2. Verify artifacts
    control_dir = temp_project / "output" / "control"
    decision_path = control_dir / "combine_v2_operator_visual_decision.json"
    gate_result_path = control_dir / "combine_v2_visual_acceptance_gate_result.json"
    
    assert decision_path.exists()
    assert gate_result_path.exists()
    
    with open(decision_path, 'r') as f:
        decision = json.load(f)
        assert decision["operator_visual_decision"] == "accepted"
        
    with open(gate_result_path, 'r') as f:
        gate = json.load(f)
        assert gate["operator_visual_decision"] == "accepted"
        assert gate["visuals_accepted"] is True
        assert gate["next_allowed_action"] == "assembly_required"
        assert gate["assembly_allowed"] is False
        assert gate["assembly_authorization_required"] is True
        assert gate["production_accepted"] is False
        assert gate["downstream_blocked"] is True
        
    # 3. Verify state transition
    orchestrator = CombineOrchestrator(project_root_str)
    status = orchestrator.get_status()
    assert status.current_state == "operator_visual_review"
    assert status.next_allowed_action == "assembly_required"

def test_operator_visual_decision_reject(temp_project, monkeypatch):
    """Test 'reject' decision via CLI."""
    project_root_str = str(temp_project)
    
    # 1. Run CLI command
    test_args = [
        "app/cli.py", "combine-operator-visual-decision",
        "--project-root", project_root_str,
        "--decision", "reject",
        "--reason", "visual_quality_failed",
        "--json"
    ]
    
    # Mock sys.argv
    monkeypatch.setattr("sys.argv", test_args)
    
    # Execute
    with pytest.raises(SystemExit) as excinfo:
        cli_main()
    assert excinfo.value.code == 0
    
    # 2. Verify artifacts
    control_dir = temp_project / "output" / "control"
    decision_path = control_dir / "combine_v2_operator_visual_decision.json"
    gate_result_path = control_dir / "combine_v2_visual_acceptance_gate_result.json"
    
    assert decision_path.exists()
    assert gate_result_path.exists()
    
    with open(decision_path, 'r') as f:
        decision = json.load(f)
        assert decision["operator_visual_decision"] == "rejected"
        assert decision["reason"] == "visual_quality_failed"
        
    with open(gate_result_path, 'r') as f:
        gate = json.load(f)
        assert gate["operator_visual_decision"] == "rejected"
        assert gate["visuals_accepted"] is False
        assert gate["next_allowed_action"] == "retry_correction_required"
        assert gate["retry_authorized"] is False
        assert gate["generation_performed"] is False
        assert gate["downstream_blocked"] is True
        
    # 3. Verify state transition
    orchestrator = CombineOrchestrator(project_root_str)
    status = orchestrator.get_status()
    assert status.current_state == "operator_visual_review"
    assert status.next_allowed_action == "retry_correction_required"

def test_operator_visual_decision_manual_review(temp_project, monkeypatch):
    """Test 'manual_review' decision via CLI."""
    project_root_str = str(temp_project)
    
    # 1. Run CLI command
    test_args = [
        "app/cli.py", "combine-operator-visual-decision",
        "--project-root", project_root_str,
        "--decision", "manual_review",
        "--reason", "operator_uncertain",
        "--json"
    ]
    
    # Mock sys.argv
    monkeypatch.setattr("sys.argv", test_args)
    
    # Execute
    with pytest.raises(SystemExit) as excinfo:
        cli_main()
    assert excinfo.value.code == 0
    
    # 2. Verify artifacts
    control_dir = temp_project / "output" / "control"
    decision_path = control_dir / "combine_v2_operator_visual_decision.json"
    gate_result_path = control_dir / "combine_v2_visual_acceptance_gate_result.json"
    
    assert decision_path.exists()
    assert gate_result_path.exists()
    
    with open(decision_path, 'r') as f:
        decision = json.load(f)
        assert decision["operator_visual_decision"] == "manual_review"
        
    with open(gate_result_path, 'r') as f:
        gate = json.load(f)
        assert gate["operator_visual_decision"] == "manual_review"
        assert gate["next_allowed_action"] == "blocked_manual_review"
        assert gate["production_accepted"] is False
        assert gate["downstream_blocked"] is True
        
    # 3. Verify state transition
    orchestrator = CombineOrchestrator(project_root_str)
    status = orchestrator.get_status()
    assert status.current_state == "operator_visual_review"
    assert status.next_allowed_action == "blocked_manual_review"

def test_no_side_effects(temp_project, monkeypatch):
    """Verify that no assembly or generation is triggered."""
    project_root_str = str(temp_project)
    
    # Run 'accept'
    test_args = [
        "app/cli.py", "combine-operator-visual-decision",
        "--project-root", project_root_str,
        "--decision", "accept",
        "--json"
    ]
    monkeypatch.setattr("sys.argv", test_args)
    with pytest.raises(SystemExit):
        cli_main()
        
    control_dir = temp_project / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
        for event in ledger:
            assert event.get("generation_performed") is False
            assert event.get("comfyui_execution") is False
            # Check for any assembly agent activity
            if event.get("agent") == "AssemblyAgent":
                pytest.fail("AssemblyAgent should not have been called")
