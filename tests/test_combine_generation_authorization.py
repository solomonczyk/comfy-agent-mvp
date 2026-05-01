import pytest
import json
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.agents.generation_agent import GenerationAgent
from app.orchestrator.contracts import CombineRunContext

class TestGenerationAuthorizationLayer:
    """Tests for the safe generation authorization layer"""

    def test_missing_assets_block_generation_authorization(self, tmp_path):
        """Verify that missing assets block authorization and point to asset review"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create asset gate with missing assets
        asset_gate_file = control_dir / "combine_v2_asset_gate_decision.json"
        with open(asset_gate_file, 'w') as f:
            json.dump({
                "missing_assets": ["hero_v2"],
                "generation_authorized": False
            }, f)
            
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_authorization_required",
            stage="generation_authorization_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.metadata["generation_authorized"] is False
        assert result.metadata["blocked_by_assets"] is True
        assert result.next_recommended_stage == "controlled_asset_resolution_review_required"
        
        # Verify artifacts were listed
        assert "combine_v2_generation_authorization_request.json" in result.artifacts
        assert "combine_v2_generation_authorization_decision.json" in result.artifacts
        
    def test_resolved_assets_create_operator_authorization_request(self, tmp_path):
        """Verify that resolved assets lead to operator authorization request"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create asset gate with NO missing assets
        with open(control_dir / "combine_v2_asset_gate_decision.json", 'w') as f:
            json.dump({"missing_assets": [], "generation_authorized": False}, f)
            
        # Create other required contracts
        with open(control_dir / "combine_v2_workflow_contract.json", 'w') as f:
            json.dump({"workflow_id": "test_wf"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", 'w') as f:
            json.dump({"prompts": ["hello world"]}, f)
        with open(control_dir / "combine_v2_preflight_contract.json", 'w') as f:
            json.dump({"preflight_passed": True}, f)
            
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_authorization_required",
            stage="generation_authorization_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.metadata["generation_authorized"] is False
        assert result.metadata["authorization_required"] is True
        assert result.next_recommended_stage == "operator_generation_authorization_required"
        
        # Verify payload stub
        payload = result.metadata["combine_v2_generation_payload_stub"]
        assert payload["workflow"] == "test_wf"
        assert payload["prompts"] == ["hello world"]
        assert payload["is_stub"] is True

    def test_no_side_effects_safety(self, tmp_path):
        """Verify that GenerationAgent does not call ComfyUI or generate non-JSON files"""
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_authorization_required",
            stage="generation_authorization_required",
            route_family="custom",
            dry_run=True
        )
        
        # Mock empty control dir
        (tmp_path / "output" / "control").mkdir(parents=True)
        
        result = agent.run(context)
        
        # Safety flags
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        
        # Verify only JSON artifacts are listed
        for art in result.artifacts:
            assert art.endswith(".json")
            
    def test_orchestrator_state_transition_safety(self, tmp_path):
        """Test orchestrator enforces new state transitions"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Setup pre-generation state
        orchestrator._write_stage_result(type('obj', (object,), {
            "stage": "workflow_preflight_required", "success": True, "message": "", "artifacts": [], "metadata": {}, "timestamp": "", "no_generation_performed": True
        }))
        
        # 1. Can go to generation_authorization_required
        result = orchestrator.run_stage("generation_authorization_required")
        assert result.success
        
        # 2. Cannot skip to generate_assets directly (by state machine rules)
        # We need to mock current state for this check if we don't use run_stage's internal state
        # Actually run_stage handles state internally.
        
        # If we are at generation_authorization_required, we should go to operator_authorization
        assert result.metadata["next_recommended_stage"] == "operator_generation_authorization_required"
        
        # Try to skip to generate_assets (should fail if state machine blocks it)
        # Note: run_stage checks against current state. After step 1, current state is generation_authorization_required.
        # ALLOWED: generation_authorization_required -> operator_generation_authorization_required
        # ALLOWED: generation_authorization_required -> controlled_asset_resolution_review_required
        # NOT ALLOWED: generation_authorization_required -> generate_assets
        
        skip_result = orchestrator.run_stage("generate_assets")
        assert skip_result.success is False
        assert "cannot be executed from current state" in skip_result.message
