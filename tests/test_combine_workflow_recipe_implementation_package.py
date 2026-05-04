"""Test RC-COMBINE-V2-421-520 Workflow Recipe Implementation Package."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from app.agents.workflow_recipe_implementation_agent import WorkflowRecipeImplementationAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineWorkflowRecipeImplementationPackage:
    """Test workflow recipe implementation package functionality."""
    
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
    def agent(self):
        """Create agent instance."""
        return WorkflowRecipeImplementationAgent()
    
    @pytest.fixture
    def setup_input_contracts(self, temp_project_root):
        """Setup input contracts for testing."""
        control_dir = temp_project_root / "output" / "control"
        
        # Create operator rebuild decision
        operator_decision = {
            "stage": "operator_rebuild_decision",
            "operator_rebuild_decision": "approve_rebuild_implementation",
            "workflow_rebuild_implementation_authorized": True,
            "generation_allowed": False,
            "next_allowed_action": "workflow_recipe_implementation_required",
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(control_dir / "combine_v2_operator_rebuild_decision.json", 'w') as f:
            json.dump(operator_decision, f, indent=2)
        
        # Create recipe rebuild contract
        recipe_contract = {
            "stage": "recipe_rebuild_contract_required",
            "old_resolution": "512x512",
            "new_resolution_policy": {
                "minimum_short_side": 1024,
                "512x512_forbidden_for_production": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(control_dir / "combine_v2_recipe_rebuild_contract.json", 'w') as f:
            json.dump(recipe_contract, f, indent=2)
        
        # Create prompt rebuild contract
        prompt_contract = {
            "stage": "prompt_contract_rebuild_required",
            "must_update_positive_prompt": True,
            "must_update_negative_prompt": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(control_dir / "combine_v2_prompt_rebuild_contract.json", 'w') as f:
            json.dump(prompt_contract, f, indent=2)
        
        # Create quality pipeline contract
        quality_contract = {
            "stage": "quality_pipeline_contract_required",
            "upscale_or_hires_fix_required": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(control_dir / "combine_v2_quality_pipeline_contract.json", 'w') as f:
            json.dump(quality_contract, f, indent=2)
        
        # Create workflow rebuild preflight report
        preflight_report = {
            "stage": "workflow_rebuild_preflight_required",
            "recipe_contract_exists": True,
            "prompt_contract_exists": True,
            "quality_pipeline_contract_exists": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(control_dir / "combine_v2_workflow_rebuild_preflight_report.json", 'w') as f:
            json.dump(preflight_report, f, indent=2)
    
    def test_operator_rebuild_approved_stage(self, agent, temp_project_root, setup_input_contracts):
        """Test operator_rebuild_approved stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="operator_rebuild_approved",
            stage="operator_rebuild_approved",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.next_recommended_stage == "workflow_recipe_implementation_required"
        
        # Check implementation report was created
        report_path = temp_project_root / "output" / "control" / "combine_v2_workflow_recipe_implementation_report.json"
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert report_data["stage"] == "operator_rebuild_approved"
        assert report_data["workflow_rebuild_implementation_authorized"] is True
        assert report_data["implementation_package_created"] is True
        assert report_data["generation_allowed"] is False
    
    def test_workflow_recipe_implementation_required_stage(self, agent, temp_project_root, setup_input_contracts):
        """Test workflow_recipe_implementation_required stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_recipe_implementation_required",
            stage="workflow_recipe_implementation_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "generation_payload_rebuild_required"
        
        # Check rebuilt generation payload was created
        payload_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_generation_payload.json"
        assert payload_path.exists()
        
        with open(payload_path, 'r') as f:
            payload_data = json.load(f)
        
        assert payload_data["stage"] == "generation_payload_rebuild_required"
        assert payload_data["old_resolution"] == "512x512"
        assert payload_data["uses_old_512_recipe"] is False
        assert payload_data["old_512_resolution_blocked"] is True
        assert payload_data["minimum_short_side_1024_enforced"] is True
        assert payload_data["generation_allowed"] is False
        assert payload_data["workflow_submitted"] is False
    
    def test_generation_payload_rebuild_required_stage(self, agent, temp_project_root, setup_input_contracts):
        """Test generation_payload_rebuild_required stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="generation_payload_rebuild_required",
            stage="generation_payload_rebuild_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "workflow_graph_rebuild_required"
        
        # Check rebuilt prompt contract was created
        prompt_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_prompt_contract.json"
        assert prompt_path.exists()
        
        with open(prompt_path, 'r') as f:
            prompt_data = json.load(f)
        
        assert prompt_data["stage"] == "prompt_contract_rebuild_required"
        assert prompt_data["positive_prompt_rebuilt"] is True
        assert prompt_data["negative_prompt_rebuilt"] is True
        assert prompt_data["negative_prompt_required"] is True
        assert prompt_data["quality_constraints_included"] is True
        assert prompt_data["anatomy_and_hand_guards_included"] is True
    
    def test_workflow_graph_rebuild_required_stage(self, agent, temp_project_root, setup_input_contracts):
        """Test workflow_graph_rebuild_required stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_graph_rebuild_required",
            stage="workflow_graph_rebuild_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "workflow_rebuild_validation_required"
        
        # Check rebuilt workflow graph contract was created
        graph_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_workflow_graph_contract.json"
        assert graph_path.exists()
        
        with open(graph_path, 'r') as f:
            graph_data = json.load(f)
        
        assert graph_data["stage"] == "workflow_graph_rebuild_required"
        assert graph_data["graph_rebuild_required"] is True
        assert graph_data["graph_rebuild_planned"] is True
        assert graph_data["base_resolution_512_removed"] is True
        assert graph_data["minimum_short_side_1024_enforced"] is True
        assert graph_data["upscale_or_hires_fix_stage_planned"] is True
        assert graph_data["no_single_pass_512_production_path"] is True
        assert graph_data["generation_allowed"] is False
        assert graph_data["workflow_submitted"] is False
        
        # Check rebuilt quality pipeline plan was created
        quality_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_quality_pipeline_plan.json"
        assert quality_path.exists()
        
        with open(quality_path, 'r') as f:
            quality_data = json.load(f)
        
        assert quality_data["stage"] == "quality_pipeline_plan_required"
        assert quality_data["quality_pipeline_plan_created"] is True
        assert "hires_fix_or_latent_upscale" in quality_data["required_quality_stages"]
        assert "single_pass_512x512_production_generation" in quality_data["forbidden"]
    
    def test_workflow_rebuild_validation_required_stage(self, agent, temp_project_root, setup_input_contracts):
        """Test workflow_rebuild_validation_required stage."""
        # First create the required artifacts
        control_dir = temp_project_root / "output" / "control"
        
        # Create rebuilt generation payload
        rebuilt_payload = {
            "stage": "generation_payload_rebuild_required",
            "old_512_resolution_blocked": True,
            "minimum_short_side_1024_enforced": True
        }
        with open(control_dir / "combine_v2_rebuilt_generation_payload.json", 'w') as f:
            json.dump(rebuilt_payload, f, indent=2)
        
        # Create rebuilt prompt contract
        rebuilt_prompt = {
            "stage": "prompt_contract_rebuild_required"
        }
        with open(control_dir / "combine_v2_rebuilt_prompt_contract.json", 'w') as f:
            json.dump(rebuilt_prompt, f, indent=2)
        
        # Create rebuilt workflow graph contract
        rebuilt_graph = {
            "stage": "workflow_graph_rebuild_required"
        }
        with open(control_dir / "combine_v2_rebuilt_workflow_graph_contract.json", 'w') as f:
            json.dump(rebuilt_graph, f, indent=2)
        
        # Create rebuilt quality pipeline plan
        quality_pipeline = {
            "stage": "quality_pipeline_plan_required",
            "forbidden": ["retry_without_recipe_change"]
        }
        with open(control_dir / "combine_v2_rebuilt_quality_pipeline_plan.json", 'w') as f:
            json.dump(quality_pipeline, f, indent=2)
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_rebuild_validation_required",
            stage="workflow_rebuild_validation_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.next_recommended_stage == "real_generation_readiness_required"
        
        # Check validation report was created
        validation_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_workflow_validation_report.json"
        assert validation_path.exists()
        
        with open(validation_path, 'r') as f:
            validation_data = json.load(f)
        
        assert validation_data["stage"] == "workflow_rebuild_validation_required"
        assert validation_data["rebuilt_payload_exists"] is True
        assert validation_data["rebuilt_prompt_contract_exists"] is True
        assert validation_data["rebuilt_graph_contract_exists"] is True
        assert validation_data["quality_pipeline_plan_exists"] is True
        assert validation_data["old_512_resolution_blocked"] is True
        assert validation_data["minimum_short_side_1024_enforced"] is True
        assert validation_data["retry_without_recipe_change_blocked"] is True
        assert validation_data["workflow_rebuild_valid_for_operator_generation_review"] is True
    
    def test_hard_boundaries_enforced(self, agent, temp_project_root, setup_input_contracts):
        """Test that hard boundaries are enforced across all stages."""
        stages = [
            "operator_rebuild_approved",
            "workflow_recipe_implementation_required",
            "generation_payload_rebuild_required",
            "workflow_graph_rebuild_required"
        ]
        
        for stage in stages:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                route_family="custom",
                dry_run=True
            )
            
            result = agent.run(context, dry_run=True)
            
            assert result.generation_performed is False
            assert result.comfyui_execution is False
            assert result.downstream_executed is False
    
    def test_agent_supported_stages(self, agent):
        """Test that agent supports the correct stages."""
        expected_stages = [
            "operator_rebuild_approved",
            "workflow_recipe_implementation_required",
            "generation_payload_rebuild_required",
            "workflow_graph_rebuild_required",
            "workflow_rebuild_validation_required",
            "real_generation_readiness_required"
        ]
        
        assert agent.supported_stages == expected_stages
