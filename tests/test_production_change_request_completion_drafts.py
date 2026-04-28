"""
Test production change request completion draft creation.

Tests the create_change_request_completion_drafts function to ensure:
- Submitted completion drafts are created from execution plans and templates
- Drafts include required evidence outputs
- Drafts validate through existing validator
- ready_for_resubmission=true only for the submitted draft folder
- retry gate remains closed
- role_decisions remain pending
- production_accepted=false
- downstream_blocked=true
- No apply/generation/downstream action executes
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from app.production_cards.change_request_completion import (
    create_change_request_completion_drafts,
    load_execution_plans,
    load_completion_templates
)
from app.production_cards.change_request_completion_validator import (
    validate_submitted_change_request_completions
)


@pytest.fixture
def sample_project_root():
    """Create a temporary project root with execution plans and completion templates."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create directory structure
        execution_plans_dir = project_root / "output" / "control" / "change_request_execution_plan"
        completions_dir = project_root / "output" / "control" / "change_request_completions"
        artifact_index_dir = project_root / "output" / "control"
        
        execution_plans_dir.mkdir(parents=True, exist_ok=True)
        completions_dir.mkdir(parents=True, exist_ok=True)
        artifact_index_dir.mkdir(parents=True, exist_ok=True)
        
        # Create workflow TD execution plan
        workflow_execution_plan = {
            "plan_type": "workflow_td_change_request_execution_plan",
            "role": "Workflow TD / ComfyUI Technical Director",
            "source_work_order": "workflow_td_identity_workflow_change_order.json",
            "source_completion_template": "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "execution_status": "planned",
            "execution_performed": False,
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "planned_steps": [
                "audit_current_identity_workflow_strategy",
                "verify_required_nodes",
                "verify_required_models",
                "define_updated_workflow_strategy",
                "define_preflight_requirements",
                "define_output_collection_contract"
            ],
            "required_outputs_before_completion": [
                "updated_workflow_strategy",
                "workflow_audit",
                "required_nodes",
                "required_models",
                "preflight_result",
                "output_collection_contract"
            ],
            "completion_submission_allowed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "created_at": "2026-04-28T14:51:04.278415Z"
        }
        
        with open(execution_plans_dir / "workflow_td_identity_workflow_execution_plan.json", 'w') as f:
            json.dump(workflow_execution_plan, f, indent=2)
        
        # Create character director execution plan
        character_execution_plan = {
            "plan_type": "character_director_reference_rebuild_execution_plan",
            "role": "Character Director",
            "source_work_order": "character_director_reference_rebuild_order.json",
            "source_completion_template": "character_director_reference_rebuild.COMPLETION_TEMPLATE.json",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "execution_status": "planned",
            "execution_performed": False,
            "planned_steps": [
                "review_identity_failure_evidence",
                "review_current_character_identity_rules",
                "define_updated_reference_strategy",
                "define_identity_acceptance_criteria",
                "write_reference_rebuild_notes"
            ],
            "required_outputs_before_completion": [
                "updated_character_identity_rules",
                "updated_reference_strategy",
                "identity_acceptance_criteria",
                "reference_rebuild_notes"
            ],
            "completion_submission_allowed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "created_at": "2026-04-28T14:51:04.278415Z"
        }
        
        with open(execution_plans_dir / "character_director_reference_rebuild_execution_plan.json", 'w') as f:
            json.dump(character_execution_plan, f, indent=2)
        
        # Create workflow TD completion template
        workflow_completion_template = {
            "completion_type": "workflow_change_completion",
            "role": "Workflow TD / ComfyUI Technical Director",
            "source_work_order": "workflow_td_identity_workflow_change_order.json",
            "blocked_shot": "shot01",
            "completion_status": "template",
            "execution_performed": False,
            "selected_resolution": None,
            "allowed_resolutions": [
                "workflow_strategy_updated",
                "missing_nodes_reported",
                "missing_models_reported",
                "reference_rebuild_required",
                "blocked"
            ],
            "required_outputs": [
                "updated_workflow_strategy",
                "workflow_audit",
                "required_nodes",
                "required_models",
                "preflight_result",
                "output_collection_contract"
            ],
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "ready_for_resubmission": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "created_at": "2026-04-28T14:26:07.680233Z"
        }
        
        with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
            json.dump(workflow_completion_template, f, indent=2)
        
        # Create character director completion template
        character_completion_template = {
            "completion_type": "reference_rebuild_completion",
            "role": "Character Director",
            "source_work_order": "character_director_reference_rebuild_order.json",
            "blocked_shot": "shot01",
            "completion_status": "template",
            "execution_performed": False,
            "selected_resolution": None,
            "allowed_resolutions": [
                "reference_strategy_updated",
                "identity_rules_updated",
                "new_reference_required",
                "workflow_change_required",
                "blocked"
            ],
            "required_outputs": [
                "updated_character_identity_rules",
                "updated_reference_strategy",
                "identity_acceptance_criteria",
                "reference_rebuild_notes"
            ],
            "ready_for_resubmission": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "created_at": "2026-04-28T14:26:07.688977Z"
        }
        
        with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
            json.dump(character_completion_template, f, indent=2)
        
        # Create artifact index
        artifact_index = {
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(artifact_index_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f, indent=2)
        
        yield str(project_root)


def test_load_execution_plans(sample_project_root):
    """Test loading execution plans from project."""
    execution_plans = load_execution_plans(sample_project_root)
    
    assert "workflow_td" in execution_plans
    assert "character_director" in execution_plans
    assert execution_plans["workflow_td"]["plan_type"] == "workflow_td_change_request_execution_plan"
    assert execution_plans["character_director"]["plan_type"] == "character_director_reference_rebuild_execution_plan"


def test_load_completion_templates(sample_project_root):
    """Test loading completion templates from project."""
    completion_templates = load_completion_templates(sample_project_root)
    
    assert "workflow_td" in completion_templates
    assert "character_director" in completion_templates
    assert completion_templates["workflow_td"]["completion_type"] == "workflow_change_completion"
    assert completion_templates["character_director"]["completion_type"] == "reference_rebuild_completion"


def test_create_change_request_completion_drafts(sample_project_root):
    """Test creating submitted completion drafts from execution plans and templates."""
    result = create_change_request_completion_drafts(sample_project_root)
    
    # Check result structure
    assert result["status"] == "completed"
    assert result["submitted_completions_created"] == 2
    assert result["execution_performed"] == True
    assert result["ready_for_resubmission"] == True
    assert result["retry_gate_open"] == False
    assert result["production_accepted"] == False
    assert result["downstream_blocked"] == True
    assert "submitted_path" in result
    
    # Check submitted directory exists
    submitted_dir = Path(result["submitted_path"])
    assert submitted_dir.exists()
    
    # Check both submitted files exist
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    
    assert workflow_submitted.exists()
    assert character_submitted.exists()


def test_workflow_td_submitted_completion_structure(sample_project_root):
    """Test workflow TD submitted completion has required structure."""
    create_change_request_completion_drafts(sample_project_root)
    
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    
    with open(workflow_submitted, 'r') as f:
        completion = json.load(f)
    
    # Check required fields
    assert completion["completion_status"] == "submitted"
    assert completion["selected_resolution"] == "workflow_strategy_updated"
    assert completion["execution_performed"] == True
    assert completion["ready_for_resubmission"] == True
    assert completion["retry_gate_open"] == False
    assert completion["production_accepted"] == False
    assert completion["downstream_blocked"] == True
    assert completion["apply_performed"] == False
    assert completion["current_required_generation_mode"] == "gorynych_identity"
    assert completion["legacy_reference_locked_allowed_for_production"] == False
    
    # Check evidence outputs are provided
    assert "outputs_provided" in completion
    assert "updated_workflow_strategy" in completion["outputs_provided"]
    assert "workflow_audit" in completion["outputs_provided"]
    assert "required_nodes" in completion["outputs_provided"]
    assert "required_models" in completion["outputs_provided"]
    assert "preflight_result" in completion["outputs_provided"]
    assert "output_collection_contract" in completion["outputs_provided"]
    
    # Check top-level evidence fields
    assert completion["updated_workflow_strategy"] is not None
    assert completion["workflow_audit"] is not None
    assert completion["required_nodes"] is not None
    assert completion["required_models"] is not None
    assert completion["preflight_result"] is not None
    assert completion["output_collection_contract"] is not None


def test_character_director_submitted_completion_structure(sample_project_root):
    """Test character director submitted completion has required structure."""
    create_change_request_completion_drafts(sample_project_root)
    
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    
    with open(character_submitted, 'r') as f:
        completion = json.load(f)
    
    # Check required fields
    assert completion["completion_status"] == "submitted"
    assert completion["selected_resolution"] == "reference_strategy_updated"
    assert completion["execution_performed"] == True
    assert completion["ready_for_resubmission"] == True
    assert completion["retry_gate_open"] == False
    assert completion["production_accepted"] == False
    assert completion["downstream_blocked"] == True
    assert completion["apply_performed"] == False
    
    # Check evidence outputs are provided
    assert "outputs_provided" in completion
    assert "updated_character_identity_rules" in completion["outputs_provided"]
    assert "updated_reference_strategy" in completion["outputs_provided"]
    assert "identity_acceptance_criteria" in completion["outputs_provided"]
    assert "reference_rebuild_notes" in completion["outputs_provided"]
    
    # Check top-level evidence fields
    assert completion["updated_character_identity_rules"] is not None
    assert completion["updated_reference_strategy"] is not None
    assert completion["identity_acceptance_criteria"] is not None
    assert completion["reference_rebuild_notes"] is not None


def test_submitted_completions_validate(sample_project_root):
    """Test submitted completions validate through existing validator."""
    create_change_request_completion_drafts(sample_project_root)
    
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    result = validate_submitted_change_request_completions(sample_project_root, str(submitted_dir))
    
    # Check validation result
    assert result["status"] == "valid"
    assert result["submitted_completions_ready"] == True
    assert result["valid_completions"] == 2
    assert result["ready_for_resubmission"] == True
    assert result["execution_performed"] == True
    assert result["retry_gate_open"] == False
    assert result["production_accepted"] == False
    assert result["downstream_blocked"] == True
    assert result["real_project_mutated"] == False


def test_no_real_project_mutations(sample_project_root):
    """Test that creating drafts does not mutate real project artifacts."""
    # Create a role_decisions directory to ensure it's not touched
    role_decisions_dir = Path(sample_project_root) / "role_decisions"
    role_decisions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a marker file to detect mutations
    marker_file = role_decisions_dir / "do_not_touch.txt"
    marker_file.write_text("unchanged")
    
    # Create completion drafts
    create_change_request_completion_drafts(sample_project_root)
    
    # Verify marker file is unchanged
    assert marker_file.exists()
    assert marker_file.read_text() == "unchanged"
    
    # Verify artifact index is unchanged
    artifact_index_path = Path(sample_project_root) / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["retry_gate_open"] == False
    assert artifact_index["production_accepted"] == False
    assert artifact_index["downstream_blocked"] == True


def test_ready_for_resubmission_only_in_submitted_folder(sample_project_root):
    """Test that ready_for_resubmission=true only in submitted folder, not in templates."""
    create_change_request_completion_drafts(sample_project_root)
    
    # Check submitted completions have ready_for_resubmission=true
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    with open(workflow_submitted, 'r') as f:
        workflow_completion = json.load(f)
    assert workflow_completion["ready_for_resubmission"] == True
    
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    with open(character_submitted, 'r') as f:
        character_completion = json.load(f)
    assert character_completion["ready_for_resubmission"] == True
    
    # Check original templates still have ready_for_resubmission=false
    completions_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions"
    
    workflow_template = completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
    with open(workflow_template, 'r') as f:
        workflow_template_data = json.load(f)
    assert workflow_template_data["ready_for_resubmission"] == False
    
    character_template = completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
    with open(character_template, 'r') as f:
        character_template_data = json.load(f)
    assert character_template_data["ready_for_resubmission"] == False


def test_retry_gate_remains_closed(sample_project_root):
    """Test that retry gate remains closed after creating drafts."""
    create_change_request_completion_drafts(sample_project_root)
    
    # Check artifact index
    artifact_index_path = Path(sample_project_root) / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["retry_gate_open"] == False
    
    # Check submitted completions
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    with open(workflow_submitted, 'r') as f:
        workflow_completion = json.load(f)
    assert workflow_completion["retry_gate_open"] == False
    
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    with open(character_submitted, 'r') as f:
        character_completion = json.load(f)
    assert character_completion["retry_gate_open"] == False


def test_production_accepted_remains_false(sample_project_root):
    """Test that production_accepted remains false after creating drafts."""
    create_change_request_completion_drafts(sample_project_root)
    
    # Check artifact index
    artifact_index_path = Path(sample_project_root) / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["production_accepted"] == False
    
    # Check submitted completions
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    with open(workflow_submitted, 'r') as f:
        workflow_completion = json.load(f)
    assert workflow_completion["production_accepted"] == False
    
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    with open(character_submitted, 'r') as f:
        character_completion = json.load(f)
    assert character_completion["production_accepted"] == False


def test_downstream_remains_blocked(sample_project_root):
    """Test that downstream remains blocked after creating drafts."""
    create_change_request_completion_drafts(sample_project_root)
    
    # Check artifact index
    artifact_index_path = Path(sample_project_root) / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["downstream_blocked"] == True
    
    # Check submitted completions
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    with open(workflow_submitted, 'r') as f:
        workflow_completion = json.load(f)
    assert workflow_completion["downstream_blocked"] == True
    
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    with open(character_submitted, 'r') as f:
        character_completion = json.load(f)
    assert character_completion["downstream_blocked"] == True


def test_apply_performed_remains_false(sample_project_root):
    """Test that apply_performed remains false in submitted completions."""
    create_change_request_completion_drafts(sample_project_root)
    
    submitted_dir = Path(sample_project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    workflow_submitted = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    with open(workflow_submitted, 'r') as f:
        workflow_completion = json.load(f)
    assert workflow_completion["apply_performed"] == False
    
    character_submitted = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    with open(character_submitted, 'r') as f:
        character_completion = json.load(f)
    assert character_completion["apply_performed"] == False
