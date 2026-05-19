"""Tests for RC-COMBINE-V2-REFERENCE-BOUND-VISUAL-GENERATION-001

Execute exactly one reference-bound visual generation from accepted canonical references.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project structure for testing."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create control directory structure
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create operator reference review directory
    operator_review_dir = control_dir / "operator_reference_review"
    operator_review_dir.mkdir()
    
    # Create input/canonical_references directory
    ref_dir = project_root / "input" / "canonical_references"
    ref_dir.mkdir(parents=True)
    
    # Create state file with required pre-state
    state = {
        "current_state": "operator_reference_decision_captured",
        "next_allowed_action": "operator_reference_decision_captured",
        "canonical_reference_set_accepted": True,
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False
    }
    with open(control_dir / "state.json", 'w') as f:
        json.dump(state, f)
    
    # Create operator decision artifact
    operator_decision = {
        "accepted": True,
        "decision_source": "human_operator_manual_review",
        "timestamp": "2024-01-01T00:00:00",
        "canonical_reference_set": "input/canonical_references"
    }
    with open(operator_review_dir / "operator_reference_decision.json", 'w') as f:
        json.dump(operator_decision, f)
    
    # Create reference manifest
    reference_manifest = {
        "canonical_references": [],
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(ref_dir / "reference_manifest.json", 'w') as f:
        json.dump(reference_manifest, f)
    
    # Create artifact index
    artifact_index = {
        "current_state": "operator_reference_decision_captured",
        "next_allowed_action": "operator_reference_decision_captured"
    }
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(artifact_index, f)
    
    # Create episode ledger
    ledger = []
    with open(control_dir / "episode_ledger.json", 'w') as f:
        json.dump(ledger, f)
    
    return project_root


def test_reference_bound_generation_authorization_required(project_root):
    """Test that authorization is required before generation can execute."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    # Remove operator decision to test authorization requirement
    operator_decision_path = project_root / "output" / "control" / "operator_reference_review" / "operator_reference_decision.json"
    operator_decision_path.unlink()
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 1  # Should fail without authorization


def test_reference_bound_generation_canonical_references_accepted_required(project_root):
    """Test that canonical references must be accepted."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    # Modify operator decision to not accept references
    operator_decision_path = project_root / "output" / "control" / "operator_reference_review" / "operator_reference_decision.json"
    with open(operator_decision_path, 'r') as f:
        decision = json.load(f)
    decision["accepted"] = False
    with open(operator_decision_path, 'w') as f:
        json.dump(decision, f)
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 1  # Should fail without accepted references


def test_reference_bound_generation_decision_source_validation(project_root):
    """Test that decision source must be human_operator_manual_review."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    # Modify operator decision source
    operator_decision_path = project_root / "output" / "control" / "operator_reference_review" / "operator_reference_decision.json"
    with open(operator_decision_path, 'r') as f:
        decision = json.load(f)
    decision["decision_source"] = "automated"
    with open(operator_decision_path, 'w') as f:
        json.dump(decision, f)
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 1  # Should fail with invalid decision source


def test_reference_bound_generation_max_generations_one(project_root):
    """Test that max_generations is set to 1."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has max_generations=1
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["max_generations"] == 1


def test_reference_bound_generation_retry_forbidden(project_root):
    """Test that retry is forbidden."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has retry_allowed=False
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["retry_allowed"] == False


def test_reference_bound_generation_stop_after_generation(project_root):
    """Test that stop_after_generation is True."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has stop_after_generation=True
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["stop_after_generation"] == True


def test_reference_bound_generation_second_generation_forbidden(project_root):
    """Test that second generation is forbidden."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has second_generation_forbidden
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["generation_constraints"]["second_generation_forbidden"] == True


def test_reference_bound_generation_visual_qa_blocked(project_root):
    """Test that visual QA is blocked."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has visual_qa_blocked
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["generation_constraints"]["visual_qa_blocked"] == True
    
    # Check result review has visual_qa_blocked
    result_review_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_result_review.json"
    assert result_review_path.exists()
    with open(result_review_path, 'r') as f:
        result_review = json.load(f)
    assert result_review["visual_qa_blocked"] == True


def test_reference_bound_generation_assembly_blocked(project_root):
    """Test that assembly is blocked."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has assembly_blocked
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["generation_constraints"]["assembly_blocked"] == True


def test_reference_bound_generation_downstream_blocked(project_root):
    """Test that downstream is blocked."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check contract has downstream_blocked
    contract_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_contract.json"
    assert contract_path.exists()
    with open(contract_path, 'r') as f:
        contract = json.load(f)
    assert contract["generation_constraints"]["downstream_blocked"] == True


def test_reference_bound_generation_production_accepted_false(project_root):
    """Test that production_accepted remains False."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check state has production_accepted=False
    state_path = project_root / "output" / "control" / "state.json"
    assert state_path.exists()
    with open(state_path, 'r') as f:
        state = json.load(f)
    assert state["production_accepted"] == False
    
    # Check result review has production_accepted=False
    result_review_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_result_review.json"
    assert result_review_path.exists()
    with open(result_review_path, 'r') as f:
        result_review = json.load(f)
    assert result_review["production_accepted"] == False


def test_reference_bound_generation_state_transition(project_root):
    """Test that state transitions to operator_visual_review_required."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check state transition
    state_path = project_root / "output" / "control" / "state.json"
    assert state_path.exists()
    with open(state_path, 'r') as f:
        state = json.load(f)
    assert state["current_state"] == "operator_visual_review_required"
    assert state["next_allowed_action"] == "operator_visual_review_required"


def test_reference_bound_generation_artifacts_created(project_root):
    """Test that all required artifacts are created."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check all required artifacts exist
    ref_bound_dir = project_root / "output" / "control" / "reference_bound_generation"
    assert ref_bound_dir.exists()
    
    required_artifacts = [
        "reference_bound_generation_authorization.json",
        "reference_bound_generation_contract.json",
        "reference_bound_generation_preflight.json",
        "reference_bound_generation_manifest.json",
        "reference_bound_generation_result_review.json",
        "reference_bound_generation_proof.json",
        "submitted_workflow.json"
    ]
    
    for artifact in required_artifacts:
        artifact_path = ref_bound_dir / artifact
        assert artifact_path.exists(), f"Artifact {artifact} not found"


def test_reference_bound_generation_artifact_index_updated(project_root):
    """Test that artifact index is updated."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check artifact index updated
    index_path = project_root / "output" / "control" / "artifact_index.json"
    assert index_path.exists()
    with open(index_path, 'r') as f:
        index = json.load(f)
    assert index["reference_bound_generation_executed"] == True
    assert index["current_state"] == "operator_visual_review_required"


def test_reference_bound_generation_episode_ledger_updated(project_root):
    """Test that episode ledger is updated."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check ledger updated
    ledger_path = project_root / "output" / "control" / "episode_ledger.json"
    assert ledger_path.exists()
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    assert len(ledger) == 1
    assert ledger[0]["event_type"] == "reference_bound_generation_executed"
    assert ledger[0]["generation_count"] == 1


def test_reference_bound_generation_second_generation_blocked(project_root):
    """Test that second generation attempt is blocked."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    # First generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Second generation attempt should fail
    result = execute_reference_bound_generation(args)
    assert result == 1  # Should fail - generation already performed


def test_reference_bound_generation_dry_run_mode(project_root):
    """Test that dry-run mode does not execute real ComfyUI."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,  # Dry-run mode
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 0  # Should succeed
    
    # Check manifest indicates dry-run
    manifest_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    assert manifest["execute_mode"] == False
    
    # Check result review status
    result_review_path = project_root / "output" / "control" / "reference_bound_generation" / "reference_bound_generation_result_review.json"
    with open(result_review_path, 'r') as f:
        result_review = json.load(f)
    assert result_review["generation_status"] == "dry_run"


def test_reference_bound_generation_invalid_state_blocked(project_root):
    """Test that invalid state blocks generation."""
    from app.cli_commands.reference_bound_generation import execute_reference_bound_generation
    from argparse import Namespace
    
    # Modify state to invalid value
    state_path = project_root / "output" / "control" / "state.json"
    with open(state_path, 'r') as f:
        state = json.load(f)
    state["current_state"] = "invalid_state"
    with open(state_path, 'w') as f:
        json.dump(state, f)
    
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        json=True
    )
    
    result = execute_reference_bound_generation(args)
    assert result == 1  # Should fail with invalid state
