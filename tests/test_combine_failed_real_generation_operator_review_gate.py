import json
import subprocess
import sys
from pathlib import Path


def _run_cli(args):
    cmd = [sys.executable, "-m", "app.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    payload = {}
    if result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _seed_failed_real_generation_result(project_root):
    """Seed a failed real generation result with zero assets."""
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    (control_dir / "combine_v2_real_generation_result.json").write_text(
        json.dumps(
            {
                "stage": "real_generate_assets",
                "status": "failed",
                "generated_assets_count": 0,
                "failure_code": "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS",
                "next_allowed_action": "real_generation_result_review_required",
                "visual_qa_executed": False,
                "retry_attempted": False,
                "downstream_executed": False,
                "production_accepted": False,
            }
        ),
        encoding="utf-8",
    )
    return control_dir


def test_failed_real_generation_operator_review_request_new_generation_attempt(tmp_path):
    """Test request_new_generation_attempt decision."""
    control_dir = _seed_failed_real_generation_result(tmp_path)
    
    # Run the CLI command
    result, payload = _run_cli([
        "combine-review-failed-real-generation",
        "--project-root", str(tmp_path),
        "--decision", "request_new_generation_attempt",
        "--reason", "zero_assets_after_real_submit",
        "--json"
    ])
    
    assert result.returncode == 0
    assert payload["status"] == "ok"
    assert payload["operator_decision"] == "request_new_generation_attempt"
    assert payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    assert payload["next_allowed_action"] == "operator_real_generation_authorization_required"
    assert payload["new_generation_authorized"] == False
    assert payload["requires_new_operator_real_generation_approval"] == True
    assert payload["generation_attempted"] == False
    assert payload["comfyui_execution"] == False
    assert payload["visual_qa_executed"] == False
    assert payload["retry_attempted"] == False
    assert payload["downstream_executed"] == False
    assert payload["production_accepted"] == False
    
    # Verify artifacts created
    assert (control_dir / "combine_v2_failed_real_generation_operator_review.json").exists()
    assert (control_dir / "combine_v2_real_generation_failure_classification.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_plan.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").exists()
    
    # Verify artifact content
    operator_review = json.loads(
        (control_dir / "combine_v2_failed_real_generation_operator_review.json").read_text(encoding="utf-8")
    )
    assert operator_review["operator_decision"] == "request_new_generation_attempt"
    assert operator_review["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    
    gate_decision = json.loads(
        (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").read_text(encoding="utf-8")
    )
    assert gate_decision["operator_decision"] == "request_new_generation_attempt"
    assert gate_decision["new_generation_authorized"] == False
    assert gate_decision["next_allowed_action"] == "operator_real_generation_authorization_required"
    assert gate_decision["requires_new_operator_real_generation_approval"] == True


def test_failed_real_generation_operator_review_manual_review(tmp_path):
    """Test manual_review decision."""
    control_dir = _seed_failed_real_generation_result(tmp_path)
    
    # Run the CLI command
    result, payload = _run_cli([
        "combine-review-failed-real-generation",
        "--project-root", str(tmp_path),
        "--decision", "manual_review",
        "--reason", "manual_intervention_required",
        "--json"
    ])
    
    assert result.returncode == 0
    assert payload["status"] == "ok"
    assert payload["operator_decision"] == "manual_review"
    assert payload["next_allowed_action"] == "blocked_manual_review"
    assert payload["new_generation_authorized"] == False
    assert payload["requires_new_operator_real_generation_approval"] == False
    assert payload["generation_attempted"] == False
    assert payload["comfyui_execution"] == False
    assert payload["visual_qa_executed"] == False
    assert payload["retry_attempted"] == False
    assert payload["downstream_executed"] == False
    assert payload["production_accepted"] == False
    
    # Verify artifacts created
    assert (control_dir / "combine_v2_failed_real_generation_operator_review.json").exists()
    assert (control_dir / "combine_v2_real_generation_failure_classification.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_plan.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").exists()
    
    # Verify gate decision content
    gate_decision = json.loads(
        (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").read_text(encoding="utf-8")
    )
    assert gate_decision["operator_decision"] == "manual_review"
    assert gate_decision["next_allowed_action"] == "blocked_manual_review"


def test_failed_real_generation_operator_review_abort_generation_route(tmp_path):
    """Test abort_generation_route decision."""
    control_dir = _seed_failed_real_generation_result(tmp_path)
    
    # Run the CLI command
    result, payload = _run_cli([
        "combine-review-failed-real-generation",
        "--project-root", str(tmp_path),
        "--decision", "abort_generation_route",
        "--reason", "generation_route_aborted",
        "--json"
    ])
    
    assert result.returncode == 0
    assert payload["status"] == "ok"
    assert payload["operator_decision"] == "abort_generation_route"
    assert payload["next_allowed_action"] == "blocked_generation_route_aborted"
    assert payload["new_generation_authorized"] == False
    assert payload["requires_new_operator_real_generation_approval"] == False
    assert payload["generation_attempted"] == False
    assert payload["comfyui_execution"] == False
    assert payload["visual_qa_executed"] == False
    assert payload["retry_attempted"] == False
    assert payload["downstream_executed"] == False
    assert payload["production_accepted"] == False
    
    # Verify artifacts created
    assert (control_dir / "combine_v2_failed_real_generation_operator_review.json").exists()
    assert (control_dir / "combine_v2_real_generation_failure_classification.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_plan.json").exists()
    assert (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").exists()
    
    # Verify gate decision content
    gate_decision = json.loads(
        (control_dir / "combine_v2_real_generation_remediation_gate_decision.json").read_text(encoding="utf-8")
    )
    assert gate_decision["operator_decision"] == "abort_generation_route"
    assert gate_decision["next_allowed_action"] == "blocked_generation_route_aborted"


def test_failed_real_generation_operator_review_invalid_decision(tmp_path):
    """Test invalid decision returns error."""
    control_dir = _seed_failed_real_generation_result(tmp_path)
    
    # Run the CLI command with invalid decision
    result, payload = _run_cli([
        "combine-review-failed-real-generation",
        "--project-root", str(tmp_path),
        "--decision", "invalid_decision",
        "--reason", "test",
        "--json"
    ])
    
    assert result.returncode == 2  # argparse returns 2 for invalid arguments
    assert "invalid choice" in result.stderr or "Invalid decision" in result.stdout


def test_state_machine_blocked_generation_route_aborted_is_terminal():
    """Test that blocked_generation_route_aborted is a terminal state."""
    from app.orchestrator.state_machine import CombineStateMachine
    
    assert CombineStateMachine.is_terminal_state("blocked_generation_route_aborted")
    assert "blocked_generation_route_aborted" in CombineStateMachine.get_terminal_states()


def test_state_machine_blocked_generation_route_aborted_transitions():
    """Test transitions from blocked_generation_route_aborted."""
    from app.orchestrator.state_machine import CombineStateMachine
    
    allowed = CombineStateMachine.get_allowed_next_states("blocked_generation_route_aborted")
    assert "brief_intake_required" in allowed
    assert "route_classification_required" in allowed
    assert "production_plan_required" in allowed
