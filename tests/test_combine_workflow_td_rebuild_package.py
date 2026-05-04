"""Test RC-COMBINE-V2-331-420 Workflow TD Rebuild Package."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.agents.workflow_td_rebuild_agent import WorkflowTDRebuildAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineWorkflowTDRebuildPackage:
    """Test workflow TD rebuild package functionality."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_context(self, temp_project_root):
        """Create mock run context."""
        return CombineRunContext(
            project_root=str(temp_project_root),
            current_state="operator_strategy_review",
            stage="workflow_td_rebuild_required",
            dry_run=True
        )
    
    @pytest.fixture
    def agent(self):
        """Create workflow TD rebuild agent."""
        return WorkflowTDRebuildAgent()
    
    def _create_test_contracts(self, project_root):
        """Create test contract files."""
        control_dir = project_root / "output" / "control"
        
        # Operator strategy decision
        operator_decision = {
            "operator_strategy_decision": "approve_workflow_rebuild_plan",
            "workflow_rebuild_authorized": True,
            "generation_allowed": False,
            "retry_allowed": False,
            "next_allowed_action": "workflow_td_rebuild_required",
            "production_accepted": False
        }
        
        with open(control_dir / "combine_v2_operator_strategy_decision.json", 'w') as f:
            json.dump(operator_decision, f)
        
        # Recipe audit
        recipe_audit = {
            "actual_resolution": {"width": 512, "height": 512},
            "recipe_quality_status": "insufficient_for_production"
        }
        
        with open(control_dir / "combine_v2_generation_recipe_audit.json", 'w') as f:
            json.dump(recipe_audit, f)
        
        # Other required contracts
        contracts = [
            "combine_v2_workflow_rebuild_plan.json",
            "combine_v2_brain_corrective_strategy.json",
            "combine_v2_corrective_retry_delta_audit.json",
            "combine_v2_workflow_quality_diagnosis.json"
        ]
        
        for contract in contracts:
            with open(control_dir / contract, 'w') as f:
                json.dump({"test": "data"}, f)
    
    def test_workflow_td_rebuild_required(self, agent, mock_context, temp_project_root):
        """Test workflow_td_rebuild_required stage."""
        self._create_test_contracts(temp_project_root)
        
        result = agent.run(mock_context)
        
        assert result.status == "ok"
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.next_recommended_stage == "recipe_rebuild_contract_required"
        assert "combine_v2_workflow_td_rebuild_report.json" in result.artifacts
        
        # Check metadata
        metadata = result.metadata
        assert metadata["generation_allowed"] is False
        assert metadata["retry_allowed"] is False
        assert metadata["production_accepted"] is False
        
        # Check rebuild report
        rebuild_report = metadata["combine_v2_workflow_td_rebuild_report"]
        assert rebuild_report["workflow_rebuild_authorized"] is True
        assert rebuild_report["rebuild_package_created"] is True
        assert rebuild_report["next_allowed_action"] == "recipe_rebuild_contract_required"
    
    def test_recipe_rebuild_contract_required(self, agent, temp_project_root):
        """Test recipe_rebuild_contract_required stage."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_td_rebuild_required",
            stage="recipe_rebuild_contract_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "prompt_contract_rebuild_required"
        assert "combine_v2_recipe_rebuild_contract.json" in result.artifacts
        
        # Check recipe contract
        recipe_contract = result.metadata["combine_v2_recipe_rebuild_contract"]
        assert recipe_contract["old_resolution"] == "512x512"
        assert recipe_contract["new_resolution_policy"]["minimum_short_side"] == 1024
        assert recipe_contract["new_resolution_policy"]["512x512_forbidden_for_production"] is True
        assert recipe_contract["must_add_quality_stage"] is True
        assert "hires_fix_or_latent_upscale" in recipe_contract["required_quality_stages"]
        assert recipe_contract["generation_allowed"] is False
    
    def test_prompt_contract_rebuild_required(self, agent, temp_project_root):
        """Test prompt_contract_rebuild_required stage."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="recipe_rebuild_contract_required",
            stage="prompt_contract_rebuild_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "quality_pipeline_contract_required"
        assert "combine_v2_prompt_rebuild_contract.json" in result.artifacts
        
        # Check prompt contract
        prompt_contract = result.metadata["combine_v2_prompt_rebuild_contract"]
        assert prompt_contract["must_update_positive_prompt"] is True
        assert prompt_contract["must_update_negative_prompt"] is True
        assert prompt_contract["negative_prompt_required"] is True
        assert prompt_contract["must_include_quality_constraints"] is True
        assert prompt_contract["must_include_anatomy_and_hand_guards"] is True
        assert prompt_contract["must_include_face_identity_guards_if_character_route"] is True
        assert prompt_contract["generation_allowed"] is False
    
    def test_quality_pipeline_contract_required(self, agent, temp_project_root):
        """Test quality_pipeline_contract_required stage."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="prompt_contract_rebuild_required",
            stage="quality_pipeline_contract_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "workflow_rebuild_preflight_required"
        assert "combine_v2_quality_pipeline_contract.json" in result.artifacts
        
        # Check quality pipeline contract
        quality_contract = result.metadata["combine_v2_quality_pipeline_contract"]
        assert quality_contract["upscale_or_hires_fix_required"] is True
        assert quality_contract["refiner_recommended"] is True
        assert quality_contract["pose_or_composition_control_required_if_human_subject"] is True
        assert quality_contract["identity_lock_required_if_character_consistency_required"] is True
        assert "single_pass_512x512_production_generation" in quality_contract["forbidden"]
        assert "retry_without_recipe_change" in quality_contract["forbidden"]
        assert quality_contract["generation_allowed"] is False
    
    def test_workflow_rebuild_preflight_required(self, agent, temp_project_root):
        """Test workflow_rebuild_preflight_required stage."""
        self._create_test_contracts(temp_project_root)
        
        # Create the required contracts for preflight
        control_dir = temp_project_root / "output" / "control"
        
        recipe_contract = {"new_resolution_policy": {"512x512_forbidden_for_production": True}}
        with open(control_dir / "combine_v2_recipe_rebuild_contract.json", 'w') as f:
            json.dump(recipe_contract, f)
        
        with open(control_dir / "combine_v2_prompt_rebuild_contract.json", 'w') as f:
            json.dump({"test": "data"}, f)
        
        with open(control_dir / "combine_v2_quality_pipeline_contract.json", 'w') as f:
            json.dump({"test": "data"}, f)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="quality_pipeline_contract_required",
            stage="workflow_rebuild_preflight_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "operator_rebuild_approval_required"
        assert "combine_v2_workflow_rebuild_preflight_report.json" in result.artifacts
        
        # Check preflight report
        preflight_report = result.metadata["combine_v2_workflow_rebuild_preflight_report"]
        assert preflight_report["recipe_contract_exists"] is True
        assert preflight_report["prompt_contract_exists"] is True
        assert preflight_report["quality_pipeline_contract_exists"] is True
        assert preflight_report["old_failure_addressed"] is True
        assert preflight_report["resolution_512_blocked"] is True
        assert preflight_report["workflow_rebuild_ready_for_operator_review"] is True
        assert preflight_report["generation_allowed"] is False
    
    def test_operator_rebuild_approval_required(self, agent, temp_project_root):
        """Test operator_rebuild_approval_required stage."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_rebuild_preflight_required",
            stage="operator_rebuild_approval_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "operator_rebuild_approval_required"
        assert "combine_v2_operator_rebuild_approval_request.json" in result.artifacts
        
        # Check approval request
        approval_request = result.metadata["combine_v2_operator_rebuild_approval_request"]
        assert approval_request["operator_review_required"] is True
        assert approval_request["recommended_operator_decision"] == "approve_rebuild_implementation"
        assert "approve_rebuild_implementation" in approval_request["operator_actions"]
        assert "request_rebuild_changes" in approval_request["operator_actions"]
        assert "manual_review" in approval_request["operator_actions"]
        assert "abort_route" in approval_request["operator_actions"]
        assert approval_request["generation_allowed"] is False
        assert approval_request["retry_allowed"] is False
        assert approval_request["production_accepted"] is False
    
    def test_hard_boundaries_enforced(self, agent, mock_context, temp_project_root):
        """Test that hard boundaries are enforced across all stages."""
        self._create_test_contracts(temp_project_root)
        
        stages = [
            "workflow_td_rebuild_required",
            "recipe_rebuild_contract_required", 
            "prompt_contract_rebuild_required",
            "quality_pipeline_contract_required",
            "workflow_rebuild_preflight_required",
            "operator_rebuild_approval_required"
        ]
        
        for stage in stages:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            
            result = agent.run(context)
            
            # Verify hard boundaries
            assert result.generation_performed is False
            assert result.comfyui_execution is False
            assert result.downstream_executed is False
            
            metadata = result.metadata
            assert metadata["generation_allowed"] is False
            assert metadata["retry_allowed"] is False
            assert metadata["production_accepted"] is False
    
    def test_resolution_512_forbidden(self, agent, temp_project_root):
        """Test that 512x512 resolution is forbidden."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_td_rebuild_required",
            stage="recipe_rebuild_contract_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        recipe_contract = result.metadata["combine_v2_recipe_rebuild_contract"]
        assert recipe_contract["new_resolution_policy"]["512x512_forbidden_for_production"] is True
    
    def test_upscale_or_hires_fix_required(self, agent, temp_project_root):
        """Test that upscale or hires fix is required."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="prompt_contract_rebuild_required",
            stage="quality_pipeline_contract_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        quality_contract = result.metadata["combine_v2_quality_pipeline_contract"]
        assert quality_contract["upscale_or_hires_fix_required"] is True
        assert quality_contract["refiner_recommended"] is True
    
    def test_negative_prompt_required(self, agent, temp_project_root):
        """Test that negative prompt is required."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="recipe_rebuild_contract_required",
            stage="prompt_contract_rebuild_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        prompt_contract = result.metadata["combine_v2_prompt_rebuild_contract"]
        assert prompt_contract["negative_prompt_required"] is True
        assert prompt_contract["must_update_negative_prompt"] is True
    
    def test_retry_without_recipe_change_forbidden(self, agent, temp_project_root):
        """Test that retry without recipe change is forbidden."""
        self._create_test_contracts(temp_project_root)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="prompt_contract_rebuild_required",
            stage="quality_pipeline_contract_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        quality_contract = result.metadata["combine_v2_quality_pipeline_contract"]
        assert "retry_without_recipe_change" in quality_contract["forbidden"]
    
    def test_unsupported_stage(self, agent, mock_context):
        """Test handling of unsupported stage."""
        mock_context.stage = "unsupported_stage"
        
        result = agent.run(mock_context)
        
        assert result.status == "error"
        assert "Unsupported stage" in result.metadata["error"]
    
    def test_validation_failed(self, agent):
        """Test handling of validation failure."""
        context = CombineRunContext(
            project_root="",
            current_state="operator_strategy_review",
            stage="workflow_td_rebuild_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "error"
        assert result.metadata["error"] == "validation_failed"
