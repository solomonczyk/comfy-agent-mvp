"""
Tests for Combine V2 Workflow Recipe Diagnosis

Tests the workflow recipe diagnosis capabilities of the production brain layer.
"""

import pytest
import json
from pathlib import Path
from app.agents.production_brain_agent import ProductionBrainAgent
from app.orchestrator.contracts import CombineRunContext


class TestWorkflowRecipeDiagnosis:
    """Test workflow recipe diagnosis"""
    
    def test_diagnosis_detects_low_resolution(self, tmp_path):
        """Test that diagnosis detects low base resolution"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create payload with low resolution
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "low_base_resolution" in diagnosis.get("detected_limitations", [])
    
    def test_diagnosis_detects_missing_upscale_stage(self, tmp_path):
        """Test that diagnosis detects missing upscale stage"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create payload without upscale
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0, "upscale": False}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "missing_upscale_stage" in diagnosis.get("detected_limitations", [])
    
    def test_diagnosis_detects_missing_refiner_stage(self, tmp_path):
        """Test that diagnosis detects missing refiner stage"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create payload without refiner
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0, "refiner": False}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "missing_refiner_stage" in diagnosis.get("detected_limitations", [])
    
    def test_diagnosis_detects_missing_pose_control(self, tmp_path):
        """Test that diagnosis detects missing pose control"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create payload without pose control
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0, "controlnet": False}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "missing_pose_control" in diagnosis.get("detected_limitations", [])
    
    def test_diagnosis_detects_missing_identity_control(self, tmp_path):
        """Test that diagnosis detects missing identity control"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create payload without identity lock
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0, "identity_lock": False}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "missing_identity_or_face_consistency_control" in diagnosis.get("detected_limitations", [])
    
    def test_diagnosis_workflow_quality_status_not_production_ready(self, tmp_path):
        """Test that diagnosis marks workflow as not production ready"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert diagnosis.get("workflow_quality_status") == "not_production_ready"
    
    def test_diagnosis_generation_not_allowed_without_rebuild(self, tmp_path):
        """Test that diagnosis does not allow generation without rebuild"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert diagnosis.get("generation_allowed_without_rebuild") == False
    
    def test_diagnosis_risk_assessment_high(self, tmp_path):
        """Test that diagnosis assesses high risk of repeating low quality"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        diagnosis = result.metadata.get("combine_v2_workflow_quality_diagnosis", {})
        assert "high" in diagnosis.get("risk_if_retry_without_rebuild", "").lower()


class TestWorkflowRebuildPlan:
    """Test workflow rebuild plan"""
    
    def test_rebuild_plan_requires_resolution_increase(self, tmp_path):
        """Test that rebuild plan requires resolution increase"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        rebuild_plan = result.metadata.get("combine_v2_workflow_rebuild_plan", {})
        changes = rebuild_plan.get("required_workflow_changes", [])
        
        resolution_change = next((c for c in changes if c.get("change") == "raise_base_resolution"), None)
        assert resolution_change is not None
        assert resolution_change.get("required") == True
    
    def test_rebuild_plan_requires_upscale_or_hires_fix(self, tmp_path):
        """Test that rebuild plan requires upscale or hires fix"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        rebuild_plan = result.metadata.get("combine_v2_workflow_rebuild_plan", {})
        changes = rebuild_plan.get("required_workflow_changes", [])
        
        upscale_change = next((c for c in changes if c.get("change") == "add_upscale_or_hires_fix_stage"), None)
        assert upscale_change is not None
        assert upscale_change.get("required") == True
    
    def test_rebuild_plan_forbids_generation_without_rebuild(self, tmp_path):
        """Test that rebuild plan forbids generation without rebuild"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        rebuild_plan = result.metadata.get("combine_v2_workflow_rebuild_plan", {})
        assert rebuild_plan.get("forbidden_next_action") == "real_generate_assets"
    
    def test_rebuild_plan_next_action_operator_strategy_review(self, tmp_path):
        """Test that rebuild plan next action is operator_strategy_review"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        payload = {"width": 512, "height": 512, "model": "test", "sampler": "euler", "steps": 20, "cfg": 7.0}
        (control_dir / "combine_v2_real_generation_payload.json").write_text(json.dumps(payload))
        (control_dir / "combine_v2_corrective_retry_generation_payload.json").write_text(json.dumps(payload))
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
        
        rebuild_plan = result.metadata.get("combine_v2_workflow_rebuild_plan", {})
        assert rebuild_plan.get("next_allowed_action") == "operator_strategy_review"
