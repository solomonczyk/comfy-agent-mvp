"""RC-COMBINE-V2-741-800 — Test corrective retry plan functionality.

Tests for the corrective retry plan creation after operator visual rejection.
"""

import json
import tempfile
from pathlib import Path
from PIL import Image
import pytest

from app.cli import combine_create_corrective_retry_plan
import argparse


def test_corrective_retry_plan_creation():
    """Test corrective retry plan creation after operator visual rejection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test asset
        asset_path = project_root / "output" / "assets" / "test_asset.png"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', (1024, 1024), color='red')
        img.save(asset_path)
        
        # Create operator visual decision artifact
        op_decision = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "rebuilt_1024_asset_failed_visual_qa_semantic_and_production_quality",
            "source_asset": str(asset_path),
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": "2024-01-01T00:00:00"
        }
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(op_decision, f, indent=2)
        
        # Create QA stub report
        qa_report = {
            "qa_verdict": "qa_failed",
            "quality_metrics": {}
        }
        qa_path = control_dir / "combine_v2_visual_qa_stub_report.json"
        with open(qa_path, 'w') as f:
            json.dump(qa_report, f, indent=2)
        
        # Create args for the CLI command
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )
        
        # Run the command
        result_code = combine_create_corrective_retry_plan(args)
        
        # Should succeed
        assert result_code == 0
        
        # Check that all required artifacts were created
        required_artifacts = [
            "combine_v2_operator_visual_rejection.json",
            "combine_v2_rebuilt_asset_failure_classification.json",
            "combine_v2_corrective_retry_plan.json",
            "combine_v2_corrective_prompt_plan.json",
            "combine_v2_corrective_workflow_plan.json",
            "combine_v2_corrective_quality_pipeline_plan.json",
            "combine_v2_controlled_retry_authorization_request.json"
        ]
        
        for artifact_name in required_artifacts:
            artifact_path = control_dir / artifact_name
            assert artifact_path.exists(), f"Artifact {artifact_name} was not created"
        
        # Verify operator visual rejection artifact
        with open(control_dir / "combine_v2_operator_visual_rejection.json", 'r') as f:
            rejection = json.load(f)
        
        assert rejection["stage"] == "operator_visual_review"
        assert rejection["operator_visual_decision"] == "reject_visual_quality"
        assert rejection["source_asset"] == str(asset_path)
        assert rejection["asset_width"] == 1024
        assert rejection["asset_height"] == 1024
        assert rejection["previous_qa_verdict"] == "qa_failed"
        assert rejection["operator_rejection_confirmed"] is True
        assert rejection["generation_allowed"] is False
        assert rejection["retry_allowed"] is False
        assert rejection["blind_retry_allowed"] is False
        assert rejection["production_accepted"] is False
        assert rejection["next_allowed_action"] == "corrective_retry_plan_required"
        
        # Verify failure classification artifact
        with open(control_dir / "combine_v2_rebuilt_asset_failure_classification.json", 'r') as f:
            classification = json.load(f)
        
        assert classification["classification"] == "rebuilt_asset_visual_failure"
        assert classification["source_asset"] == str(asset_path)
        assert classification["blind_retry_allowed"] is False
        assert classification["production_accepted"] is False
        assert "semantic_content_failed" in classification["failure_basis"]
        assert "subject_not_recognizable" in classification["failure_basis"]
        
        # Verify corrective retry plan artifact
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'r') as f:
            retry_plan = json.load(f)
        
        assert retry_plan["stage"] == "corrective_retry_plan_required"
        assert retry_plan["plan_type"] == "controlled_corrective_retry_plan"
        assert retry_plan["blind_retry_allowed"] is False
        assert retry_plan["retry_requires_operator_authorization"] is True
        assert retry_plan["generation_allowed"] is False
        assert retry_plan["retry_attempted"] is False
        assert retry_plan["comfyui_execution"] is False
        assert retry_plan["workflow_submitted"] is False
        assert retry_plan["downstream_executed"] is False
        assert retry_plan["production_accepted"] is False
        assert retry_plan["next_allowed_action"] == "controlled_retry_authorization_required"
        assert retry_plan["required_corrections"]["prompt_correction_required"] is True
        assert retry_plan["required_corrections"]["workflow_correction_required"] is True
        assert retry_plan["required_corrections"]["quality_pipeline_correction_required"] is True
        
        # Verify prompt plan artifact
        with open(control_dir / "combine_v2_corrective_prompt_plan.json", 'r') as f:
            prompt_plan = json.load(f)
        
        assert prompt_plan["plan_type"] == "corrective_prompt_plan"
        assert prompt_plan["generation_allowed"] is False
        assert prompt_plan["required_corrections"]["semantic_clarity_improvement"] is True
        
        # Verify workflow plan artifact
        with open(control_dir / "combine_v2_corrective_workflow_plan.json", 'r') as f:
            workflow_plan = json.load(f)
        
        assert workflow_plan["plan_type"] == "corrective_workflow_plan"
        assert workflow_plan["generation_allowed"] is False
        assert workflow_plan["required_corrections"]["model_selection_review"] is True
        
        # Verify quality pipeline plan artifact
        with open(control_dir / "combine_v2_corrective_quality_pipeline_plan.json", 'r') as f:
            quality_plan = json.load(f)
        
        assert quality_plan["plan_type"] == "corrective_quality_pipeline_plan"
        assert quality_plan["generation_allowed"] is False
        assert quality_plan["required_corrections"]["resolution_validation"] is True
        
        # Verify authorization request artifact
        with open(control_dir / "combine_v2_controlled_retry_authorization_request.json", 'r') as f:
            auth_request = json.load(f)
        
        assert auth_request["stage"] == "controlled_retry_authorization_required"
        assert auth_request["operator_review_required"] is True
        assert auth_request["recommended_operator_decision"] == "approve_corrective_retry_implementation"
        assert auth_request["generation_allowed"] is False
        assert auth_request["retry_allowed"] is False
        assert auth_request["workflow_submitted"] is False
        assert auth_request["production_accepted"] is False
        assert auth_request["next_allowed_action"] == "controlled_retry_authorization_required"
        assert "approve_corrective_retry_implementation" in auth_request["operator_actions"]
        
        # Verify artifact index was updated
        artifact_index_path = control_dir / "artifact_index.json"
        assert artifact_index_path.exists()
        
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        assert artifact_index["current_state"] == "corrective_retry_plan_required"
        assert artifact_index["next_allowed_action"] == "controlled_retry_authorization_required"
        assert artifact_index["operator_visual_rejection_created"] is True
        assert artifact_index["failure_classification_created"] is True
        assert artifact_index["corrective_retry_plan_created"] is True
        assert artifact_index["blind_retry_allowed"] is False
        assert artifact_index["retry_requires_operator_authorization"] is True
        assert artifact_index["generation_allowed"] is False
        assert artifact_index["retry_allowed"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False
        
        # Verify episode ledger was updated
        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        
        with open(ledger_path, 'r') as f:
            ledger = json.load(f)
        
        assert isinstance(ledger, list)
        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "corrective_retry_plan_created"
        assert last_event["stage"] == "corrective_retry_plan_required"
        assert last_event["blind_retry_allowed"] is False
        assert last_event["retry_requires_operator_authorization"] is True
        assert last_event["generation_allowed"] is False


def test_corrective_retry_plan_missing_operator_decision():
    """Test corrective retry plan creation fails without operator decision."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create args without operator decision
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )
        
        # Run the command
        result_code = combine_create_corrective_retry_plan(args)
        
        # Should fail
        assert result_code == 1


def test_corrective_retry_plan_without_qa_report():
    """Test corrective retry plan creation without QA report (uses default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create operator visual decision artifact
        op_decision = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "visual_quality_failure",
            "source_asset": "output/assets/test.png",
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": "2024-01-01T00:00:00"
        }
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(op_decision, f, indent=2)
        
        # Create args for the CLI command
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )
        
        # Run the command
        result_code = combine_create_corrective_retry_plan(args)
        
        # Should succeed (uses default qa_failed)
        assert result_code == 0
        
        # Verify that default qa_failed was used
        with open(control_dir / "combine_v2_operator_visual_rejection.json", 'r') as f:
            rejection = json.load(f)
        
        assert rejection["previous_qa_verdict"] == "qa_failed"


def test_corrective_retry_plan_blind_retry_blocked():
    """Test that blind retry is properly blocked in corrective plan."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create operator visual decision artifact
        op_decision = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "visual_quality_failure",
            "source_asset": "output/assets/test.png",
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": "2024-01-01T00:00:00"
        }
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(op_decision, f, indent=2)
        
        # Create args for the CLI command
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )
        
        # Run the command
        result_code = combine_create_corrective_retry_plan(args)
        
        # Should succeed
        assert result_code == 0
        
        # Verify blind retry is blocked in all artifacts
        with open(control_dir / "combine_v2_operator_visual_rejection.json", 'r') as f:
            rejection = json.load(f)
        assert rejection["blind_retry_allowed"] is False
        
        with open(control_dir / "combine_v2_rebuilt_asset_failure_classification.json", 'r') as f:
            classification = json.load(f)
        assert classification["blind_retry_allowed"] is False
        
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'r') as f:
            retry_plan = json.load(f)
        assert retry_plan["blind_retry_allowed"] is False
        
        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)
        assert artifact_index["blind_retry_allowed"] is False


def test_corrective_retry_plan_generation_blocked():
    """Test that generation is properly blocked in corrective plan."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create operator visual decision artifact
        op_decision = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "visual_quality_failure",
            "source_asset": "output/assets/test.png",
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": "2024-01-01T00:00:00"
        }
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(op_decision, f, indent=2)
        
        # Create args for the CLI command
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )
        
        # Run the command
        result_code = combine_create_corrective_retry_plan(args)
        
        # Should succeed
        assert result_code == 0
        
        # Verify generation is blocked in all artifacts
        with open(control_dir / "combine_v2_operator_visual_rejection.json", 'r') as f:
            rejection = json.load(f)
        assert rejection["generation_allowed"] is False
        
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'r') as f:
            retry_plan = json.load(f)
        assert retry_plan["generation_allowed"] is False
        
        with open(control_dir / "combine_v2_corrective_prompt_plan.json", 'r') as f:
            prompt_plan = json.load(f)
        assert prompt_plan["generation_allowed"] is False
        
        with open(control_dir / "combine_v2_corrective_workflow_plan.json", 'r') as f:
            workflow_plan = json.load(f)
        assert workflow_plan["generation_allowed"] is False
        
        with open(control_dir / "combine_v2_corrective_quality_pipeline_plan.json", 'r') as f:
            quality_plan = json.load(f)
        assert quality_plan["generation_allowed"] is False
        
        with open(control_dir / "combine_v2_controlled_retry_authorization_request.json", 'r') as f:
            auth_request = json.load(f)
        assert auth_request["generation_allowed"] is False
        
        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)
        assert artifact_index["generation_allowed"] is False
