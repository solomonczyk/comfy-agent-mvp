"""Test RC-COMBINE-V2-421-520 Rebuilt Generation Readiness Gate."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from app.agents.workflow_recipe_implementation_agent import WorkflowRecipeImplementationAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineRebuiltGenerationReadinessGate:
    """Test rebuilt generation readiness gate functionality."""
    
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
    def setup_rebuild_artifacts(self, temp_project_root):
        """Setup rebuilt artifacts for testing."""
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
        
        # Create rebuilt workflow validation report
        validation_report = {
            "stage": "workflow_rebuild_validation_required",
            "old_512_resolution_blocked": True,
            "minimum_short_side_1024_enforced": True
        }
        with open(control_dir / "combine_v2_rebuilt_workflow_validation_report.json", 'w') as f:
            json.dump(validation_report, f, indent=2)
    
    def test_real_generation_readiness_required_stage(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test real_generation_readiness_required stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.next_recommended_stage == "operator_real_generation_authorization_required"
        
        # Check readiness report was created
        readiness_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_real_generation_readiness_report.json"
        assert readiness_path.exists()
        
        with open(readiness_path, 'r') as f:
            readiness_data = json.load(f)
        
        assert readiness_data["stage"] == "real_generation_readiness_required"
        assert readiness_data["readiness_type"] == "rebuilt_workflow_recipe"
        assert readiness_data["rebuilt_payload_ready"] is True
        assert readiness_data["rebuilt_workflow_contract_ready"] is True
        assert readiness_data["rebuilt_prompt_contract_ready"] is True
        assert readiness_data["rebuilt_quality_pipeline_ready"] is True
        assert readiness_data["operator_real_generation_authorization_required"] is True
        assert readiness_data["generation_allowed"] is False
        assert readiness_data["comfyui_execution"] is False
        assert readiness_data["workflow_submitted"] is False
        assert readiness_data["next_allowed_action"] == "operator_real_generation_authorization_required"
        
        # Check authorization request was created
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        assert auth_request_path.exists()
        
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        assert auth_request_data["stage"] == "operator_real_generation_authorization_required"
        assert auth_request_data["request_type"] == "rebuilt_workflow_recipe_real_generation_authorization"
        assert auth_request_data["operator_review_required"] is True
        assert auth_request_data["recommended_operator_decision"] == "approve_real_generation_with_rebuilt_recipe"
        assert "approve_real_generation_with_rebuilt_recipe" in auth_request_data["operator_actions"]
        assert auth_request_data["old_512_resolution_blocked"] is True
        assert auth_request_data["minimum_short_side_1024_enforced"] is True
        assert auth_request_data["generation_allowed"] is False
        assert auth_request_data["comfyui_execution"] is False
        assert auth_request_data["workflow_submitted"] is False
        assert auth_request_data["production_accepted"] is False
        assert auth_request_data["next_allowed_action"] == "operator_real_generation_authorization_required"
    
    def test_hard_boundaries_enforced(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test that hard boundaries are enforced in readiness stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        # Verify hard boundaries
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        
        # Check artifacts enforce hard boundaries
        readiness_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_real_generation_readiness_report.json"
        with open(readiness_path, 'r') as f:
            readiness_data = json.load(f)
        
        assert readiness_data["generation_allowed"] is False
        assert readiness_data["comfyui_execution"] is False
        assert readiness_data["workflow_submitted"] is False
        
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        assert auth_request_data["generation_allowed"] is False
        assert auth_request_data["comfyui_execution"] is False
        assert auth_request_data["workflow_submitted"] is False
        assert auth_request_data["production_accepted"] is False
    
    def test_old_512_resolution_blocked(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test that old 512 resolution is blocked."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        assert auth_request_data["old_512_resolution_blocked"] is True
    
    def test_minimum_short_side_1024_enforced(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test that minimum short side 1024 is enforced."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        assert auth_request_data["minimum_short_side_1024_enforced"] is True
    
    def test_operator_actions_available(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test that operator actions are available."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        expected_actions = [
            "approve_real_generation_with_rebuilt_recipe",
            "request_rebuild_changes",
            "manual_review",
            "abort_route"
        ]
        
        for action in expected_actions:
            assert action in auth_request_data["operator_actions"]
    
    def test_next_allowed_action_correct(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test that next allowed action is correct."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        assert result.next_recommended_stage == "operator_real_generation_authorization_required"
        
        readiness_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_real_generation_readiness_report.json"
        with open(readiness_path, 'r') as f:
            readiness_data = json.load(f)
        
        assert readiness_data["next_allowed_action"] == "operator_real_generation_authorization_required"
        
        auth_request_path = temp_project_root / "output" / "control" / "combine_v2_operator_real_generation_authorization_request.json"
        with open(auth_request_path, 'r') as f:
            auth_request_data = json.load(f)
        
        assert auth_request_data["next_allowed_action"] == "operator_real_generation_authorization_required"
    
    def test_comprehensive_coverage(self, agent, temp_project_root, setup_rebuild_artifacts):
        """Test comprehensive coverage of all required aspects."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context, dry_run=True)
        
        # Verify all required aspects from task spec
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.next_recommended_stage == "operator_real_generation_authorization_required"
        
        readiness_path = temp_project_root / "output" / "control" / "combine_v2_rebuilt_real_generation_readiness_report.json"
        with open(readiness_path, 'r') as f:
            readiness_data = json.load(f)
        
        assert readiness_data["rebuilt_payload_ready"] is True
        assert readiness_data["rebuilt_workflow_contract_ready"] is True
        assert readiness_data["rebuilt_prompt_contract_ready"] is True
        assert readiness_data["rebuilt_quality_pipeline_ready"] is True
        assert readiness_data["operator_real_generation_authorization_required"] is True
        assert readiness_data["generation_allowed"] is False
        assert readiness_data["comfyui_execution"] is False
        assert readiness_data["workflow_submitted"] is False
