import pytest
import json
import os
import shutil
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.state_machine import CombineStateMachine
from app.agents.visual_qa_agent import VisualQAAgent
from app.orchestrator.contracts import CombineRunContext

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Initialize with a state that can transition to visual_qa_required_stub_pending
    # Usually generate_assets -> visual_qa_required_stub_pending
    artifact_index = {
        "current_state": "generate_assets",
        "route_family": "portrait_character_identity"
    }
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(artifact_index, f)
        
    return project_root

def test_visual_qa_state_machine_validity():
    """Verify state machine transitions for Visual QA."""
    sm = CombineStateMachine()
    
    assert sm.is_valid_state("visual_qa_required_stub_pending")
    assert sm.is_valid_state("visual_qa_required")
    assert sm.is_valid_state("operator_visual_review")
    
    assert sm.can_transition("generate_assets", "visual_qa_required_stub_pending")
    assert sm.can_transition("visual_qa_required_stub_pending", "visual_qa_required")
    assert sm.can_transition("visual_qa_required", "operator_visual_review")
    
    # Verify transitions from operator_visual_review
    assert sm.can_transition("operator_visual_review", "assembly_required")
    assert sm.can_transition("operator_visual_review", "retry_correction_required")
    assert sm.can_transition("operator_visual_review", "blocked_manual_review")

def test_visual_qa_agent_stub_pending(temp_project):
    """Verify VisualQAAgent behavior in stub_pending stage."""
    orchestrator = CombineOrchestrator(str(temp_project))
    
    # Execute visual_qa_required_stub_pending
    result = orchestrator.run_stage("visual_qa_required_stub_pending", dry_run=True)
    
    assert result.success
    assert result.stage == "visual_qa_required_stub_pending"
    assert result.metadata["agent"] == "VisualQAAgent"
    assert result.metadata["next_recommended_stage"] == "visual_qa_required"
    assert result.metadata["visual_qa_stub"] is True
    assert result.metadata["real_image_analysis"] is False

def test_visual_qa_agent_required_logic(temp_project):
    """Verify VisualQAAgent creates required artifacts in visual_qa_required stage."""
    orchestrator = CombineOrchestrator(str(temp_project))
    
    # Set state to visual_qa_required_stub_pending first to allow transition
    orchestrator.run_stage("visual_qa_required_stub_pending", dry_run=True)
    
    # Execute visual_qa_required
    result = orchestrator.run_stage("visual_qa_required", dry_run=True)
    
    assert result.success
    assert "combine_v2_visual_qa_stub_report.json" in result.artifacts
    assert "combine_v2_operator_visual_review_packet.json" in result.artifacts
    
    # Check artifacts on disk
    control_dir = temp_project / "output" / "control"
    report_path = control_dir / "combine_v2_visual_qa_stub_report.json"
    packet_path = control_dir / "combine_v2_operator_visual_review_packet.json"
    
    assert report_path.exists()
    assert packet_path.exists()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
        assert report["stage"] == "visual_qa_required"
        assert report["status"] == "stubbed"
        assert report["real_image_analysis"] is False
        assert report["operator_review_required"] is True
        assert report["visual_qa_passed"] is False
        assert report["generation_performed"] is False
        assert report["comfyui_execution"] is False
        
    with open(packet_path, 'r') as f:
        packet = json.load(f)
        assert packet["stage"] == "operator_visual_review"
        assert packet["operator_review_required"] is True
        assert "block_manual_review" in packet["operator_actions"]
        assert packet["real_image_analysis"] is False
        assert packet["production_accepted"] is False
        assert packet["assembly_allowed"] is False
        assert packet["downstream_blocked"] is True

def test_visual_qa_safety_boundaries(temp_project):
    """Verify that VisualQAAgent enforces safety boundaries."""
    orchestrator = CombineOrchestrator(str(temp_project))
    
    # Transition to visual_qa_required
    orchestrator.run_stage("visual_qa_required_stub_pending", dry_run=True)
    result = orchestrator.run_stage("visual_qa_required", dry_run=True)
    
    assert result.metadata["generation_performed"] is False
    assert result.metadata["comfyui_execution"] is False
    assert result.metadata["downstream_executed"] is False
    assert result.metadata["visual_qa_stub"] is True
    assert result.metadata["real_image_analysis"] is False
