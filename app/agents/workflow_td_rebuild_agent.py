"""Workflow TD Rebuild Agent - Production-ready recipe rebuild package.

Creates comprehensive rebuild package after operator strategy approval.
No generation, no ComfyUI submit, no retry, no assembly.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class WorkflowTDRebuildAgent(BaseRoleAgent):
    """Workflow TD rebuild agent for creating production-ready rebuild package.
    
    This agent works deterministically without LLM calls.
    It creates comprehensive rebuild contracts after operator strategy approval.
    No generation, no ComfyUI submit, no retry, no assembly.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return [
            "workflow_td_rebuild_required",
            "recipe_rebuild_contract_required", 
            "prompt_contract_rebuild_required",
            "quality_pipeline_contract_required",
            "workflow_rebuild_preflight_required",
            "operator_rebuild_approval_required",
        ]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "WorkflowTDRebuildContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        """Create a stub result for dry-run execution."""
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=True,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage=context.stage,
            metadata={
                "action": "workflow_td_rebuild_stub",
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "description": "Workflow TD rebuild (stub only)"
            }
        )
    
    def _read_contract(self, project_root: str, contract_name: str) -> Dict[str, Any]:
        """Helper to read contract files from output/control"""
        contract_path = Path(project_root) / "output" / "control" / f"{contract_name}.json"
        if contract_path.exists():
            try:
                with open(contract_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the workflow TD rebuild agent."""
        if not self.validate_inputs(context):
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="error",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                metadata={"error": "validation_failed", "missing": ["project_root"]}
            )
        
        project_root = context.project_root
        stage = context.stage
        timestamp = datetime.utcnow().isoformat()
        
        # Read required input contracts
        operator_decision = self._read_contract(project_root, "combine_v2_operator_strategy_decision")
        rebuild_plan = self._read_contract(project_root, "combine_v2_workflow_rebuild_plan")
        brain_strategy = self._read_contract(project_root, "combine_v2_brain_corrective_strategy")
        recipe_audit = self._read_contract(project_root, "combine_v2_generation_recipe_audit")
        delta_audit = self._read_contract(project_root, "combine_v2_corrective_retry_delta_audit")
        quality_diagnosis = self._read_contract(project_root, "combine_v2_workflow_quality_diagnosis")
        
        if stage == "workflow_td_rebuild_required":
            # Create workflow TD rebuild report
            rebuild_report = {
                "stage": stage,
                "agent": self.role_name,
                "operator_decision": operator_decision.get("operator_strategy_decision", "unknown"),
                "workflow_rebuild_authorized": operator_decision.get("workflow_rebuild_authorized", False),
                "rebuild_package_created": True,
                "next_allowed_action": "recipe_rebuild_contract_required",
                "generation_allowed": False,
                "retry_allowed": False,
                "production_accepted": False,
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_workflow_td_rebuild_report.json"],
                next_recommended_stage="recipe_rebuild_contract_required",
                metadata={
                    "action": "workflow_td_rebuild",
                    "next_allowed_action": "recipe_rebuild_contract_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_workflow_td_rebuild_report": rebuild_report
                }
            )
        
        if stage == "recipe_rebuild_contract_required":
            # Read current recipe audit for resolution info
            current_resolution = {"width": 512, "height": 512}  # Default fallback
            if recipe_audit and "actual_resolution" in recipe_audit:
                current_resolution = recipe_audit["actual_resolution"]
            
            # Create recipe rebuild contract
            recipe_contract = {
                "stage": stage,
                "old_resolution": f"{current_resolution.get('width', 512)}x{current_resolution.get('height', 512)}",
                "new_resolution_policy": {
                    "minimum_short_side": 1024,
                    "recommended": "1024x1024 or route-specific higher",
                    "512x512_forbidden_for_production": True
                },
                "must_add_quality_stage": True,
                "required_quality_stages": [
                    "hires_fix_or_latent_upscale",
                    "image_upscale_pass", 
                    "optional_refiner_pass"
                ],
                "generation_allowed": False,
                "next_allowed_action": "prompt_contract_rebuild_required",
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_recipe_rebuild_contract.json"],
                next_recommended_stage="prompt_contract_rebuild_required",
                metadata={
                    "action": "recipe_rebuild_contract",
                    "next_allowed_action": "prompt_contract_rebuild_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_recipe_rebuild_contract": recipe_contract
                }
            )
        
        if stage == "prompt_contract_rebuild_required":
            # Create prompt rebuild contract
            prompt_contract = {
                "stage": stage,
                "must_update_positive_prompt": True,
                "must_update_negative_prompt": True,
                "negative_prompt_required": True,
                "must_include_quality_constraints": True,
                "must_include_anatomy_and_hand_guards": True,
                "must_include_face_identity_guards_if_character_route": True,
                "generation_allowed": False,
                "next_allowed_action": "quality_pipeline_contract_required",
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_prompt_rebuild_contract.json"],
                next_recommended_stage="quality_pipeline_contract_required",
                metadata={
                    "action": "prompt_rebuild_contract",
                    "next_allowed_action": "quality_pipeline_contract_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_prompt_rebuild_contract": prompt_contract
                }
            )
        
        if stage == "quality_pipeline_contract_required":
            # Create quality pipeline contract
            quality_contract = {
                "stage": stage,
                "upscale_or_hires_fix_required": True,
                "refiner_recommended": True,
                "pose_or_composition_control_required_if_human_subject": True,
                "identity_lock_required_if_character_consistency_required": True,
                "forbidden": [
                    "single_pass_512x512_production_generation",
                    "retry_without_recipe_change",
                    "retry_without_preflight"
                ],
                "generation_allowed": False,
                "next_allowed_action": "workflow_rebuild_preflight_required",
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_quality_pipeline_contract.json"],
                next_recommended_stage="workflow_rebuild_preflight_required",
                metadata={
                    "action": "quality_pipeline_contract",
                    "next_allowed_action": "workflow_rebuild_preflight_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_quality_pipeline_contract": quality_contract
                }
            )
        
        if stage == "workflow_rebuild_preflight_required":
            # Check if all contracts exist
            recipe_contract = self._read_contract(project_root, "combine_v2_recipe_rebuild_contract")
            prompt_contract = self._read_contract(project_root, "combine_v2_prompt_rebuild_contract")
            quality_contract = self._read_contract(project_root, "combine_v2_quality_pipeline_contract")
            
            contracts_exist = all([recipe_contract, prompt_contract, quality_contract])
            
            # Create workflow rebuild preflight report
            preflight_report = {
                "stage": stage,
                "recipe_contract_exists": bool(recipe_contract),
                "prompt_contract_exists": bool(prompt_contract),
                "quality_pipeline_contract_exists": bool(quality_contract),
                "old_failure_addressed": True,
                "resolution_512_blocked": recipe_contract.get("new_resolution_policy", {}).get("512x512_forbidden_for_production", False),
                "workflow_rebuild_ready_for_operator_review": contracts_exist,
                "generation_allowed": False,
                "next_allowed_action": "operator_rebuild_approval_required",
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_workflow_rebuild_preflight_report.json"],
                next_recommended_stage="operator_rebuild_approval_required",
                metadata={
                    "action": "workflow_rebuild_preflight",
                    "next_allowed_action": "operator_rebuild_approval_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_workflow_rebuild_preflight_report": preflight_report
                }
            )
        
        if stage == "operator_rebuild_approval_required":
            # Create operator rebuild approval request
            approval_request = {
                "stage": stage,
                "operator_review_required": True,
                "recommended_operator_decision": "approve_rebuild_implementation",
                "operator_actions": [
                    "approve_rebuild_implementation",
                    "request_rebuild_changes", 
                    "manual_review",
                    "abort_route"
                ],
                "generation_allowed": False,
                "retry_allowed": False,
                "production_accepted": False,
                "next_allowed_action": "operator_rebuild_approval_required",
                "timestamp": timestamp
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_operator_rebuild_approval_request.json"],
                next_recommended_stage="operator_rebuild_approval_required",
                metadata={
                    "action": "operator_rebuild_approval_request",
                    "next_allowed_action": "operator_rebuild_approval_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "production_accepted": False,
                    "combine_v2_operator_rebuild_approval_request": approval_request
                }
            )
        
        # Default: unsupported stage
        return AgentResult(
            agent=self.role_name,
            stage=stage,
            status="error",
            dry_run=True,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            metadata={"error": f"Unsupported stage: {stage}"}
        )
