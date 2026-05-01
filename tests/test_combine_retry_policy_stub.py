import pytest
import json
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.contracts import CombineRunContext
from app.agents.retry_policy_agent import RetryPolicyAgent


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Initialize with a state that can transition to operator_visual_review
    artifact_index = {
        "current_state": "retry_correction_required",
        "route_family": "portrait_character_identity"
    }
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(artifact_index, f)

    # Inputs consumed by RetryPolicyAgent at retry_correction_required stage
    with open(control_dir / "combine_v2_operator_visual_decision.json", "w") as f:
        json.dump({"operator_visual_decision": "rejected", "reason": "visual_quality_failed"}, f)
    with open(control_dir / "combine_v2_visual_acceptance_gate_result.json", "w") as f:
        json.dump({"operator_visual_decision": "rejected", "next_allowed_action": "retry_correction_required"}, f)
    with open(control_dir / "combine_v2_visual_qa_stub_report.json", "w") as f:
        json.dump({"verdict": "fail", "issues": ["blurry_subject"]}, f)
    with open(control_dir / "combine_v2_operator_visual_review_packet.json", "w") as f:
        json.dump({"review_packet_id": "VP-001", "review_status": "rejected"}, f)
        
    return project_root

def test_retry_policy_stub_artifacts(temp_project):
    """Verify RetryPolicyAgent creates correct artifacts and respects boundaries."""
    project_root_str = str(temp_project)
    
    # Run the agent
    context = CombineRunContext(
        project_root=project_root_str,
        current_state="retry_correction_required",
        stage="retry_correction_required",
        dry_run=True,
        metadata={}
    )
    
    agent = RetryPolicyAgent()
    result = agent.run(context, dry_run=True)
    
    control_dir = temp_project / "output" / "control"
    
    # Verify artifacts created
    failure_class_path = control_dir / "combine_v2_retry_failure_classification.json"
    corrective_plan_path = control_dir / "combine_v2_retry_corrective_plan.json"
    auth_request_path = control_dir / "combine_v2_retry_authorization_request.json"
    
    assert failure_class_path.exists(), "RetryPolicyAgent creates failure classification"
    assert corrective_plan_path.exists(), "RetryPolicyAgent creates corrective plan"
    assert auth_request_path.exists(), "RetryPolicyAgent creates retry authorization request"
    
    # Verify metadata fields
    assert result.metadata.get("failure_classification_created") is True
    assert result.metadata.get("corrective_plan_created") is True
    assert result.metadata.get("retry_authorization_request_created") is True
    assert result.metadata.get("retry_authorized") is False, "retry_authorized=false"
    assert result.generation_performed is False, "generation_performed=false"
    assert result.comfyui_execution is False, "comfyui_execution=false"
    assert result.downstream_executed is False, "downstream_executed=false"
    assert result.metadata.get("next_allowed_action") == "operator_retry_authorization_required", "next_allowed_action=operator_retry_authorization_required"
    
    # Verify no downstream execution is requested
    assert result.next_recommended_stage == "operator_retry_authorization_required"

def test_retry_policy_orchestrator_integration(temp_project):
    """Verify orchestrator runs RetryPolicyAgent correctly without launching retries."""
    project_root_str = str(temp_project)
    orchestrator = CombineOrchestrator(project_root_str)
    
    result = orchestrator.run_stage("retry_correction_required", dry_run=True)
    
    assert result is not None
    assert result.success is True
    
    # Check updated state
    status = orchestrator.get_status()
    assert status.current_state == "retry_correction_required"
    assert status.next_allowed_action == "operator_retry_authorization_required"
    
    # Check ledger for boundary preservation
    control_dir = temp_project / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    assert ledger_path.exists()
    
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
        last_event = ledger[-1]
        
        # Verify boundary constraints
        assert last_event.get("generation_performed") is False
        assert last_event.get("comfyui_execution") is False
        assert last_event.get("agent") == "RetryPolicyAgent"

        # Verify retry and downstream stacks did not start.
        disallowed_agents = {"GenerationAgent", "AssemblyAgent", "AudioAgent", "RenderAgent"}
        for event in ledger:
            assert event.get("agent") not in disallowed_agents
            assert event.get("stage") != "retry_generate_frames"
