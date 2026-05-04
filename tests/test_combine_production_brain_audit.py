"""
Tests for Combine V2 Production Brain Audit

Tests the production brain layer for visual failure audit and workflow rebuild plan.
"""

import pytest
import json
from pathlib import Path
from app.orchestrator.state_machine import CombineStateMachine
from app.orchestrator.orchestrator import CombineOrchestrator
from app.agents.production_brain_agent import ProductionBrainAgent


class TestProductionBrainStateMachine:
    """Test the production brain states in the state machine"""
    
    def test_production_brain_states_are_valid(self):
        """Test that all production brain states are valid"""
        new_states = [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
        
        for state in new_states:
            assert CombineStateMachine.is_valid_state(state), f"State {state} should be valid"
    
    def test_production_brain_transitions_are_allowed(self):
        """Test that production brain transitions are allowed"""
        assert CombineStateMachine.can_transition("real_visual_qa_preflight_required", "production_brain_audit_required")
        assert CombineStateMachine.can_transition("production_brain_audit_required", "visual_failure_audit_required")
        assert CombineStateMachine.can_transition("visual_failure_audit_required", "generation_recipe_audit_required")
        assert CombineStateMachine.can_transition("generation_recipe_audit_required", "workflow_rebuild_plan_required")
        assert CombineStateMachine.can_transition("workflow_rebuild_plan_required", "operator_strategy_review")
    
    def test_production_brain_forbids_generation_transitions(self):
        """Test that production brain states cannot skip to generation"""
        assert not CombineStateMachine.can_transition("production_brain_audit_required", "real_generate_assets")
        assert not CombineStateMachine.can_transition("workflow_rebuild_plan_required", "real_generate_assets")
        assert not CombineStateMachine.can_transition("operator_strategy_review", "real_generate_assets")
        assert not CombineStateMachine.can_transition("operator_strategy_review", "assembly_required")


class TestProductionBrainAgent:
    """Test the production brain agent"""
    
    def test_production_brain_agent_supported_stages(self):
        """Test that production brain agent supports correct stages"""
        agent = ProductionBrainAgent()
        expected_stages = [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
        
        for stage in expected_stages:
            assert stage in agent.supported_stages, f"Stage {stage} should be supported"
    
    def test_production_brain_agent_requires_project_root(self):
        """Test that production brain agent requires project_root"""
        agent = ProductionBrainAgent()
        assert "project_root" in agent.required_inputs
    
    def test_production_brain_agent_creates_all_artifacts(self, tmp_path):
        """Test that production brain agent creates all required artifacts"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock required artifacts
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(json.dumps({
            "generated_assets": [{"path": "output/assets/combine_v2_00002_.png", "width": 512, "height": 512}]
        }))
        (control_dir / "combine_v2_operator_real_generation_approval.json").write_text(json.dumps({
            "operator_visual_decision": "rejected"
        }))
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps({
            "width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0
        }))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps({
            "width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0
        }))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        # Create mock asset
        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "combine_v2_00002_.png").write_bytes(b"fake_png_data")
        
        agent = ProductionBrainAgent()
        
        # Test production_brain_audit_required stage
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="real_visual_qa_preflight_required",
            stage="production_brain_audit_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed == False
        assert result.comfyui_execution == False
        assert result.downstream_executed == False
        assert "combine_v2_production_brain_audit.json" in result.artifacts
        
        # Test visual_failure_audit_required stage
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="production_brain_audit_required",
            stage="visual_failure_audit_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed == False
        assert "combine_v2_visual_failure_audit.json" in result.artifacts
        
        # Test generation_recipe_audit_required stage
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="visual_failure_audit_required",
            stage="generation_recipe_audit_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed == False
        assert "combine_v2_generation_recipe_audit.json" in result.artifacts
        
        # Test workflow_rebuild_plan_required stage
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_recipe_audit_required",
            stage="workflow_rebuild_plan_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed == False
        assert "combine_v2_corrective_retry_delta_audit.json" in result.artifacts
        assert "combine_v2_workflow_quality_diagnosis.json" in result.artifacts
        assert "combine_v2_brain_corrective_strategy.json" in result.artifacts
        assert "combine_v2_workflow_rebuild_plan.json" in result.artifacts
        
        # Test operator_strategy_review stage
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="workflow_rebuild_plan_required",
            stage="operator_strategy_review",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        assert result.status == "ok"
        assert result.generation_performed == False
        assert "combine_v2_operator_strategy_review_packet.json" in result.artifacts
    
    def test_production_brain_detects_low_resolution(self, tmp_path):
        """Test that production brain detects low resolution"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock required artifacts
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(json.dumps({
            "generated_assets": [{"path": "output/assets/combine_v2_00002_.png", "width": 512, "height": 512}]
        }))
        (control_dir / "combine_v2_operator_real_generation_approval.json").write_text(json.dumps({
            "operator_visual_decision": "rejected"
        }))
        
        # Create mock asset
        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "combine_v2_00002_.png").write_bytes(b"fake_png_data")
        
        agent = ProductionBrainAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="production_brain_audit_required",
            stage="visual_failure_audit_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        # Check that low resolution is flagged and visual failure is confirmed
        audit = result.metadata.get("combine_v2_visual_failure_audit", {})
        assert audit.get("width") == 512
        assert audit.get("height") == 512
        assert "low_resolution_or_unexpected_resolution" in audit.get("failure_categories", [])
        assert audit.get("visual_failure_confirmed") == True
        assert "low_resolution_or_unexpected_resolution" in audit.get("confirmation_basis", [])
        assert "failure_categories_present" in audit.get("confirmation_basis", [])
    
    def test_production_brain_analyzes_corrective_retry_delta(self, tmp_path):
        """Test that production brain analyzes corrective retry delta"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock payloads with no changes
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        agent = ProductionBrainAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_recipe_audit_required",
            stage="workflow_rebuild_plan_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        # Check that delta analysis is performed
        delta_audit = result.metadata.get("combine_v2_corrective_retry_delta_audit", {})
        assert delta_audit.get("resolution_changed") == False
        assert delta_audit.get("model_changed") == False
        assert delta_audit.get("delta_quality") == "insufficient"
        assert len(delta_audit.get("why_retry_failed_likely", [])) > 0
    
    def test_production_brain_workflow_rebuild_required(self, tmp_path):
        """Test that production brain recommends workflow rebuild"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock payloads
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        agent = ProductionBrainAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_recipe_audit_required",
            stage="workflow_rebuild_plan_required",
            dry_run=True
        )
        result = agent.run(context, dry_run=True)
        
        # Check that workflow rebuild is recommended
        strategy = result.metadata.get("combine_v2_brain_corrective_strategy", {})
        assert strategy.get("strategy_verdict") == "workflow_rebuild_required_before_next_generation"
        assert strategy.get("generation_allowed") == False
        
        rebuild_plan = result.metadata.get("combine_v2_workflow_rebuild_plan", {})
        assert rebuild_plan.get("plan_type") == "production_recipe_rebuild"
        assert rebuild_plan.get("forbidden_next_action") == "real_generate_assets"
    
    def test_production_brain_generation_not_allowed(self, tmp_path):
        """Test that production brain does not allow generation"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock payloads
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        agent = ProductionBrainAgent()
        
        # Test all stages to ensure generation is not allowed
        stages = [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
        
        for stage in stages:
            context = CombineRunContext(
                project_root=str(tmp_path),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            result = agent.run(context, dry_run=True)
            
            assert result.generation_performed == False
            assert result.comfyui_execution == False
            assert result.downstream_executed == False
            
            metadata = result.metadata
            assert metadata.get("generation_allowed", False) == False
            assert metadata.get("retry_allowed", False) == False
            assert metadata.get("assembly_allowed", False) == False
            assert metadata.get("production_accepted", False) == False
    
    def test_production_brain_no_comfyui_submit(self, tmp_path):
        """Test that production brain does not submit to ComfyUI"""
        from app.orchestrator.contracts import CombineRunContext
        
        # Create a mock project structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock payloads
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        agent = ProductionBrainAgent()
        
        # Test all stages to ensure no ComfyUI submission
        stages = [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
        
        for stage in stages:
            context = CombineRunContext(
                project_root=str(tmp_path),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            result = agent.run(context, dry_run=True)
            
            assert result.comfyui_execution == False


class TestProductionBrainOrchestratorIntegration:
    """Test production brain integration with orchestrator"""
    
    def test_orchestrator_runs_production_brain_stages(self, tmp_path):
        """Test that orchestrator can run production brain stages"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Create required artifacts
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(json.dumps({
            "generated_assets": [{"path": "output/assets/combine_v2_00002_.png", "width": 512, "height": 512}]
        }))
        (control_dir / "combine_v2_operator_real_generation_approval.json").write_text(json.dumps({
            "operator_visual_decision": "rejected"
        }))
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "combine_v2_00002_.png").write_bytes(b"fake_png_data")
        
        # Set current state to allow production brain stages
        artifact_index = tmp_path / "output" / "control" / "artifact_index.json"
        artifact_index.write_text(json.dumps({"current_state": "real_visual_qa_preflight_required"}))
        
        # Run production brain stages
        stages = [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
        
        for stage in stages:
            result = orchestrator.run_stage(stage, dry_run=True)
            assert result.success == True
            assert result.no_generation_performed == True
    
    def test_production_brain_ends_at_operator_strategy_review(self, tmp_path):
        """Test that production brain chain ends at operator_strategy_review"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Create required artifacts
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        base_payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(json.dumps({
            "generated_assets": [{"path": "output/assets/combine_v2_00002_.png", "width": 512, "height": 512}]
        }))
        (control_dir / "combine_v2_operator_real_generation_approval.json").write_text(json.dumps({
            "operator_visual_decision": "rejected"
        }))
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(base_payload))
        (control_dir / "combine_v2_corrective_retry_prompt_patch.json").write_text(json.dumps({
            "patch_created": True
        }))
        
        assets_dir = tmp_path / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "combine_v2_00002_.png").write_bytes(b"fake_png_data")
        
        # Set current state to allow production brain stages
        artifact_index = tmp_path / "output" / "control" / "artifact_index.json"
        artifact_index.write_text(json.dumps({"current_state": "workflow_rebuild_plan_required"}))
        
        # Run final stage
        result = orchestrator.run_stage("operator_strategy_review", dry_run=True)
        
        assert result.success == True
        assert result.metadata.get("next_allowed_action") == "operator_strategy_review"
        assert result.metadata.get("generation_allowed") == False
