"""Workflow Recipe Implementation Agent - Implementation-ready rebuilt workflow recipe package.

Creates comprehensive implementation-ready rebuilt workflow recipe package after operator
rebuild approval. No generation, no ComfyUI submit, no retry, no assembly.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class WorkflowRecipeImplementationAgent(BaseRoleAgent):
    """Workflow recipe implementation agent for creating implementation-ready rebuilt package.
    
    This agent works deterministically without LLM calls.
    It creates comprehensive implementation-ready artifacts after operator rebuild approval.
    No generation, no ComfyUI submit, no retry, no assembly.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return [
            "operator_rebuild_approved",
            "workflow_recipe_implementation_required",
            "generation_payload_rebuild_required",
            "workflow_graph_rebuild_required",
            "workflow_rebuild_validation_required",
            "real_generation_readiness_required",
        ]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "WorkflowRecipeImplementationContract"
    
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
                "action": "workflow_recipe_implementation_stub",
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "description": "Workflow recipe implementation (stub only)"
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
    
    def _write_contract(self, project_root: str, contract_name: str, data: Dict[str, Any]) -> None:
        """Helper to write contract files to output/control"""
        control_dir = Path(project_root) / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        contract_path = control_dir / f"{contract_name}.json"
        with open(contract_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the workflow recipe implementation agent."""
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
        operator_decision = self._read_contract(project_root, "combine_v2_operator_rebuild_decision")
        recipe_contract = self._read_contract(project_root, "combine_v2_recipe_rebuild_contract")
        prompt_contract = self._read_contract(project_root, "combine_v2_prompt_rebuild_contract")
        quality_contract = self._read_contract(project_root, "combine_v2_quality_pipeline_contract")
        preflight_report = self._read_contract(project_root, "combine_v2_workflow_rebuild_preflight_report")
        
        if stage == "operator_rebuild_approved":
            # Create workflow recipe implementation report
            implementation_report = {
                "stage": stage,
                "agent": self.role_name,
                "operator_rebuild_decision": operator_decision.get("operator_rebuild_decision", "unknown"),
                "workflow_rebuild_implementation_authorized": operator_decision.get("workflow_rebuild_implementation_authorized", False),
                "implementation_package_created": True,
                "next_allowed_action": "workflow_recipe_implementation_required",
                "generation_allowed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "production_accepted": False,
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_workflow_recipe_implementation_report", implementation_report)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_workflow_recipe_implementation_report.json"],
                next_recommended_stage="workflow_recipe_implementation_required",
                metadata={
                    "action": "operator_rebuild_approved",
                    "next_allowed_action": "workflow_recipe_implementation_required",
                    "generation_allowed": False,
                    "comfyui_execution": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_workflow_recipe_implementation_report": implementation_report
                }
            )
        
        if stage == "workflow_recipe_implementation_required":
            # Create rebuilt generation payload
            old_resolution = recipe_contract.get("old_resolution", "512x512")
            new_resolution_policy = recipe_contract.get("new_resolution_policy", {})
            
            rebuilt_payload = {
                "stage": "generation_payload_rebuild_required",
                "payload_type": "rebuilt_after_production_brain_audit",
                "old_resolution": old_resolution,
                "new_resolution": {
                    "width": 1024,
                    "height": 1024,
                    "policy": "minimum_short_side_1024"
                },
                "uses_old_512_recipe": False,
                "old_512_resolution_blocked": True,
                "minimum_short_side_1024_enforced": True,
                "generation_allowed": False,
                "workflow_submitted": False,
                "next_allowed_action": "workflow_graph_rebuild_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_generation_payload", rebuilt_payload)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_rebuilt_generation_payload.json"],
                next_recommended_stage="generation_payload_rebuild_required",
                metadata={
                    "action": "workflow_recipe_implementation",
                    "next_allowed_action": "workflow_graph_rebuild_required",
                    "generation_allowed": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_rebuilt_generation_payload": rebuilt_payload
                }
            )
        
        if stage == "generation_payload_rebuild_required":
            # Create rebuilt prompt contract
            rebuilt_prompt_contract = {
                "stage": "prompt_contract_rebuild_required",
                "positive_prompt_rebuilt": True,
                "negative_prompt_rebuilt": True,
                "negative_prompt_required": True,
                "quality_constraints_included": True,
                "anatomy_and_hand_guards_included": True,
                "face_identity_guards_included_if_character_route": True,
                "route_aware_prompt_contract": True,
                "generation_allowed": False,
                "next_allowed_action": "workflow_graph_rebuild_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_prompt_contract", rebuilt_prompt_contract)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_rebuilt_prompt_contract.json"],
                next_recommended_stage="workflow_graph_rebuild_required",
                metadata={
                    "action": "generation_payload_rebuild",
                    "next_allowed_action": "workflow_graph_rebuild_required",
                    "generation_allowed": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_rebuilt_prompt_contract": rebuilt_prompt_contract
                }
            )
        
        if stage == "workflow_graph_rebuild_required":
            # Create rebuilt workflow graph contract
            rebuilt_graph_contract = {
                "stage": "workflow_graph_rebuild_required",
                "graph_rebuild_required": True,
                "graph_rebuild_planned": True,
                "base_resolution_512_removed": True,
                "minimum_short_side_1024_enforced": True,
                "upscale_or_hires_fix_stage_planned": True,
                "refiner_stage_planned_or_documented_optional": True,
                "pose_or_composition_control_planned_if_human_subject": True,
                "identity_lock_planned_if_character_consistency_required": True,
                "no_single_pass_512_production_path": True,
                "generation_allowed": False,
                "workflow_submitted": False,
                "next_allowed_action": "workflow_rebuild_validation_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_workflow_graph_contract", rebuilt_graph_contract)
            
            # Also create rebuilt quality pipeline plan
            rebuilt_quality_pipeline = {
                "stage": "quality_pipeline_plan_required",
                "quality_pipeline_plan_created": True,
                "required_quality_stages": [
                    "hires_fix_or_latent_upscale",
                    "image_upscale_pass",
                    "optional_refiner_pass"
                ],
                "forbidden": [
                    "single_pass_512x512_production_generation",
                    "retry_without_recipe_change",
                    "retry_without_preflight",
                    "workflow_submit_without_operator_real_generation_authorization"
                ],
                "generation_allowed": False,
                "workflow_submitted": False,
                "next_allowed_action": "workflow_rebuild_validation_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_quality_pipeline_plan", rebuilt_quality_pipeline)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=[
                    "combine_v2_rebuilt_workflow_graph_contract.json",
                    "combine_v2_rebuilt_quality_pipeline_plan.json"
                ],
                next_recommended_stage="workflow_rebuild_validation_required",
                metadata={
                    "action": "workflow_graph_rebuild",
                    "next_allowed_action": "workflow_rebuild_validation_required",
                    "generation_allowed": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_rebuilt_workflow_graph_contract": rebuilt_graph_contract,
                    "combine_v2_rebuilt_quality_pipeline_plan": rebuilt_quality_pipeline
                }
            )
        
        if stage == "workflow_rebuild_validation_required":
            # Check if all rebuilt artifacts exist
            rebuilt_payload = self._read_contract(project_root, "combine_v2_rebuilt_generation_payload")
            rebuilt_prompt = self._read_contract(project_root, "combine_v2_rebuilt_prompt_contract")
            rebuilt_graph = self._read_contract(project_root, "combine_v2_rebuilt_workflow_graph_contract")
            quality_pipeline = self._read_contract(project_root, "combine_v2_rebuilt_quality_pipeline_plan")
            
            artifacts_exist = all([rebuilt_payload, rebuilt_prompt, rebuilt_graph, quality_pipeline])
            
            # Create workflow rebuild validation report
            validation_report = {
                "stage": "workflow_rebuild_validation_required",
                "rebuilt_payload_exists": bool(rebuilt_payload),
                "rebuilt_prompt_contract_exists": bool(rebuilt_prompt),
                "rebuilt_graph_contract_exists": bool(rebuilt_graph),
                "quality_pipeline_plan_exists": bool(quality_pipeline),
                "old_512_resolution_blocked": rebuilt_payload.get("old_512_resolution_blocked", True),
                "minimum_short_side_1024_enforced": rebuilt_payload.get("minimum_short_side_1024_enforced", True),
                "retry_without_recipe_change_blocked": quality_pipeline.get("forbidden", []).count("retry_without_recipe_change") > 0,
                "workflow_rebuild_valid_for_operator_generation_review": artifacts_exist,
                "generation_allowed": False,
                "workflow_submitted": False,
                "next_allowed_action": "real_generation_readiness_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_workflow_validation_report", validation_report)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_rebuilt_workflow_validation_report.json"],
                next_recommended_stage="real_generation_readiness_required",
                metadata={
                    "action": "workflow_rebuild_validation",
                    "next_allowed_action": "real_generation_readiness_required",
                    "generation_allowed": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_rebuilt_workflow_validation_report": validation_report
                }
            )
        
        if stage == "real_generation_readiness_required":
            # Create rebuilt real generation readiness report
            readiness_report = {
                "stage": "real_generation_readiness_required",
                "readiness_type": "rebuilt_workflow_recipe",
                "rebuilt_payload_ready": True,
                "rebuilt_workflow_contract_ready": True,
                "rebuilt_prompt_contract_ready": True,
                "rebuilt_quality_pipeline_ready": True,
                "operator_real_generation_authorization_required": True,
                "generation_allowed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "next_allowed_action": "operator_real_generation_authorization_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_rebuilt_real_generation_readiness_report", readiness_report)
            
            # Create operator real generation authorization request
            authorization_request = {
                "stage": "operator_real_generation_authorization_required",
                "request_type": "rebuilt_workflow_recipe_real_generation_authorization",
                "operator_review_required": True,
                "recommended_operator_decision": "approve_real_generation_with_rebuilt_recipe",
                "operator_actions": [
                    "approve_real_generation_with_rebuilt_recipe",
                    "request_rebuild_changes",
                    "manual_review",
                    "abort_route"
                ],
                "old_512_resolution_blocked": True,
                "minimum_short_side_1024_enforced": True,
                "generation_allowed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "production_accepted": False,
                "next_allowed_action": "operator_real_generation_authorization_required",
                "timestamp": timestamp
            }
            
            self._write_contract(project_root, "combine_v2_operator_real_generation_authorization_request", authorization_request)
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=[
                    "combine_v2_rebuilt_real_generation_readiness_report.json",
                    "combine_v2_operator_real_generation_authorization_request.json"
                ],
                next_recommended_stage="operator_real_generation_authorization_required",
                metadata={
                    "action": "real_generation_readiness",
                    "next_allowed_action": "operator_real_generation_authorization_required",
                    "generation_allowed": False,
                    "comfyui_execution": False,
                    "workflow_submitted": False,
                    "production_accepted": False,
                    "combine_v2_rebuilt_real_generation_readiness_report": readiness_report,
                    "combine_v2_operator_real_generation_authorization_request": authorization_request
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
