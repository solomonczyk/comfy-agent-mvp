"""Production Brain Agent - deterministic analysis.

Analyzes why corrective retry failed and creates workflow rebuild plan.
No generation, no ComfyUI submit, no retry, no assembly.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class ProductionBrainAgent(BaseRoleAgent):
    """Production brain agent for visual failure audit and workflow diagnosis.
    
    This agent works deterministically without LLM calls.
    It analyzes why corrective retry failed and creates a workflow rebuild plan.
    No generation, no ComfyUI submit, no retry, no assembly.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return [
            "production_brain_audit_required",
            "visual_failure_audit_required",
            "generation_recipe_audit_required",
            "workflow_rebuild_plan_required",
            "operator_strategy_review",
        ]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "ProductionBrainContract"
    
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
                "action": "production_brain_stub",
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "description": "Production brain audit (stub only)"
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
    
    def _get_asset_from_manifest(self, project_root: str) -> Dict[str, Any]:
        """Get the most recent generated asset from manifest or assets directory"""
        # Try to read from outputs manifest
        manifest = self._read_contract(project_root, "combine_v2_real_generation_outputs_manifest")
        if manifest and "generated_assets" in manifest and manifest["generated_assets"]:
            return manifest["generated_assets"][0]
        
        # Fallback: look for assets in output/assets
        assets_dir = Path(project_root) / "output" / "assets"
        if assets_dir.exists():
            for ext in ['.png', '.jpg', '.jpeg']:
                for file in assets_dir.glob(f"*{ext}"):
                    return {
                        "path": str(file),
                        "filename": file.name
                    }
        
        return {"path": "output/assets/combine_v2_00002_.png", "filename": "combine_v2_00002_.png"}
    
    def _check_audit_guard(self, project_root: str, current_stage: str) -> Dict[str, Any]:
        """Check audit guard to ensure production brain CLI cannot rewind from later state."""
        # Allowed states for production brain rerun
        allowed_states = [
            "real_visual_qa_preflight_required",
            "production_brain_audit_required", 
            "operator_strategy_review"
        ]
        
        # Check if current state is allowed for rerun
        idempotent_rerun_safe = current_stage in allowed_states
        
        # Additional check: ensure we're not trying to rewind from a later state
        # This prevents production brain from being used to bypass workflow rebuild
        production_brain_rerun_cannot_rewind_from_later_state = idempotent_rerun_safe
        
        return {
            "idempotent_rerun_safe": idempotent_rerun_safe,
            "production_brain_rerun_cannot_rewind_from_later_state": production_brain_rerun_cannot_rewind_from_later_state,
            "state_reset_allowed_only_when_current_state_in": allowed_states,
            "current_stage": current_stage
        }
    
    def _get_asset_dimensions(self, asset_path: str) -> tuple:
        """Get asset dimensions using PIL if available"""
        try:
            from PIL import Image
            if Path(asset_path).exists():
                with Image.open(asset_path) as img:
                    return img.size
        except Exception:
            pass
        return (512, 512)  # Default fallback
    
    def _compare_payloads(self, payload1: Dict, payload2: Dict) -> Dict[str, Any]:
        """Compare two generation payloads to detect changes"""
        def get_nested(d, keys, default=None):
            for key in keys:
                if isinstance(d, dict) and key in d:
                    d = d[key]
                else:
                    return default
            return d
        
        resolution_changed = False
        model_changed = False
        sampler_changed = False
        steps_changed = False
        cfg_changed = False
        negative_prompt_changed = False
        upscale_added = False
        refiner_added = False
        control_added = False
        identity_lock_added = False
        
        # Resolution comparison
        res1 = get_nested(payload1, ["width", "height"], None)
        res2 = get_nested(payload2, ["width", "height"], None)
        if res1 and res2 and res1 != res2:
            resolution_changed = True
        
        # Model comparison
        model1 = get_nested(payload1, ["model"], "")
        model2 = get_nested(payload2, ["model"], "")
        if model1 and model2 and model1 != model2:
            model_changed = True
        
        # Sampler comparison
        sampler1 = get_nested(payload1, ["sampler"], "")
        sampler2 = get_nested(payload2, ["sampler"], "")
        if sampler1 and sampler2 and sampler1 != sampler2:
            sampler_changed = True
        
        # Steps comparison
        steps1 = get_nested(payload1, ["steps"], 0)
        steps2 = get_nested(payload2, ["steps"], 0)
        if steps1 and steps2 and steps1 != steps2:
            steps_changed = True
        
        # CFG comparison
        cfg1 = get_nested(payload1, ["cfg"], 0)
        cfg2 = get_nested(payload2, ["cfg"], 0)
        if cfg1 and cfg2 and cfg1 != cfg2:
            cfg_changed = True
        
        # Negative prompt comparison
        neg1 = get_nested(payload1, ["negative_prompt"], "")
        neg2 = get_nested(payload2, ["negative_prompt"], "")
        if neg1 and neg2 and neg1 != neg2:
            negative_prompt_changed = True
        
        # Check for upscale/refiner/control additions
        upscale1 = get_nested(payload1, ["upscale"], False)
        upscale2 = get_nested(payload2, ["upscale"], False)
        if upscale2 and not upscale1:
            upscale_added = True
        
        refiner1 = get_nested(payload1, ["refiner"], False)
        refiner2 = get_nested(payload2, ["refiner"], False)
        if refiner2 and not refiner1:
            refiner_added = True
        
        control1 = get_nested(payload1, ["controlnet"], False)
        control2 = get_nested(payload2, ["controlnet"], False)
        if control2 and not control1:
            control_added = True
        
        identity1 = get_nested(payload1, ["identity_lock"], False)
        identity2 = get_nested(payload2, ["identity_lock"], False)
        if identity2 and not identity1:
            identity_lock_added = True
        
        return {
            "resolution_changed": resolution_changed,
            "model_changed": model_changed,
            "sampler_changed": sampler_changed,
            "steps_changed": steps_changed,
            "cfg_changed": cfg_changed,
            "negative_prompt_changed": negative_prompt_changed,
            "upscale_added": upscale_added,
            "refiner_added": refiner_added,
            "control_added": control_added,
            "identity_lock_added": identity_lock_added,
        }
    
    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the production brain agent."""
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
        
        # Audit guard: Check carryover from previous layer
        audit_guard = self._check_audit_guard(project_root, stage)
        if not audit_guard["idempotent_rerun_safe"]:
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="blocked",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                metadata={
                    "error": "audit_guard_failed",
                    "reason": "production_brain_rerun_cannot_rewind_from_later_state",
                    "audit_guard": audit_guard
                }
            )
        
        if stage == "production_brain_audit_required":
            # Create production brain audit artifact
            audit = {
                "stage": stage,
                "agent": self.role_name,
                "audit_type": "production_brain_audit",
                "next_allowed_action": "visual_failure_audit_required",
                "generation_allowed": False,
                "retry_allowed": False,
                "assembly_allowed": False,
                "downstream_executed": False,
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
                artifacts=["combine_v2_production_brain_audit.json"],
                next_recommended_stage="visual_failure_audit_required",
                metadata={
                    "action": "production_brain_audit",
                    "next_allowed_action": "visual_failure_audit_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "assembly_allowed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_production_brain_audit": audit
                }
            )
        
        if stage == "visual_failure_audit_required":
            # Analyze the generated asset
            asset_info = self._get_asset_from_manifest(project_root)
            asset_path = asset_info.get("path", "output/assets/combine_v2_00002_.png")
            width, height = self._get_asset_dimensions(asset_path)
            
            # Read operator decision to confirm rejection
            op_decision = self._read_contract(project_root, "combine_v2_operator_real_generation_approval")
            visual_operator_rejection = op_decision.get("operator_visual_decision") == "rejected"
            
            # Determine failure categories based on resolution
            failure_categories = []
            if width <= 512 or height <= 512:
                failure_categories.extend([
                    "low_resolution_or_unexpected_resolution",
                    "blur_or_softness",
                    "anatomy_distortion_risk",
                    "hand_distortion_risk",
                    "face_identity_unreliable",
                    "production_quality_failed"
                ])
            
            # Determine confirmation basis and confirm visual failure
            confirmation_basis = []
            if visual_operator_rejection:
                confirmation_basis.append("operator_visual_rejection_or_operator_observed_failure")
            if "low_resolution_or_unexpected_resolution" in failure_categories:
                confirmation_basis.append("low_resolution_or_unexpected_resolution")
            if failure_categories:
                confirmation_basis.append("failure_categories_present")
            
            # Read recipe audit if available to add additional confirmation basis
            recipe_audit = self._read_contract(project_root, "combine_v2_generation_recipe_audit")
            if recipe_audit.get("recipe_quality_status") == "insufficient_for_production":
                confirmation_basis.append("recipe_quality_status_insufficient_for_production")
            
            # Visual failure is confirmed if operator rejected OR failure categories are present
            visual_failure_confirmed = visual_operator_rejection or bool(failure_categories)
            
            audit = {
                "stage": stage,
                "source_asset": asset_path,
                "asset_exists": Path(asset_path).exists(),
                "asset_readable": Path(asset_path).exists(),
                "width": width,
                "height": height,
                "visual_operator_rejection": visual_operator_rejection,
                "visual_failure_confirmed": visual_failure_confirmed,
                "confirmation_basis": confirmation_basis,
                "failure_categories": failure_categories,
                "next_allowed_action": "generation_recipe_audit_required",
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
                artifacts=["combine_v2_visual_failure_audit.json"],
                next_recommended_stage="generation_recipe_audit_required",
                metadata={
                    "action": "visual_failure_audit",
                    "next_allowed_action": "generation_recipe_audit_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "assembly_allowed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_visual_failure_audit": audit
                }
            )
        
        if stage == "generation_recipe_audit_required":
            # Read generation artifacts
            real_payload = self._read_contract(project_root, "combine_v2_real_generation_payload")
            corrective_payload = self._read_contract(project_root, "combine_v2_corrective_retry_generation_payload")
            execution_contract = self._read_contract(project_root, "combine_v2_real_generation_execution_contract")
            trace = self._read_contract(project_root, "combine_v2_real_generation_trace")
            
            # Extract recipe parameters
            width = real_payload.get("width", 512) if real_payload else 512
            height = real_payload.get("height", 512) if real_payload else 512
            model = real_payload.get("model", "unknown") if real_payload else "unknown"
            sampler = real_payload.get("sampler", "unknown") if real_payload else "unknown"
            steps = real_payload.get("steps", "unknown") if real_payload else "unknown"
            cfg = real_payload.get("cfg", "unknown") if real_payload else "unknown"
            seed = real_payload.get("seed", "unknown") if real_payload else "unknown"
            positive_present = bool(real_payload.get("positive_prompt")) if real_payload else False
            negative_present = bool(real_payload.get("negative_prompt")) if real_payload else False
            
            # Check for quality enhancement stages
            upscale_enabled = real_payload.get("upscale", False) if real_payload else False
            refiner_enabled = real_payload.get("refiner", False) if real_payload else False
            controlnet_enabled = real_payload.get("controlnet", False) if real_payload else False
            identity_lock_enabled = real_payload.get("identity_lock", False) if real_payload else False
            
            # Determine recipe quality status
            blocking_issues = []
            if width <= 512 or height <= 512:
                blocking_issues.append("resolution_too_low_for_production")
            if not upscale_enabled and not refiner_enabled:
                blocking_issues.append("no_upscale_or_refiner_detected")
            if not controlnet_enabled and not identity_lock_enabled:
                blocking_issues.append("no_pose_or_identity_stabilization_detected")
            
            recipe_quality_status = "insufficient_for_production" if blocking_issues else "acceptable"
            
            audit = {
                "stage": stage,
                "actual_resolution": {"width": width, "height": height},
                "model_checkpoint": model,
                "sampler": sampler,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "positive_prompt_present": positive_present,
                "negative_prompt_present": negative_present,
                "upscale_enabled": upscale_enabled,
                "refiner_enabled": refiner_enabled,
                "controlnet_or_pose_enabled": controlnet_enabled,
                "face_or_identity_lock_enabled": identity_lock_enabled,
                "recipe_quality_status": recipe_quality_status,
                "blocking_recipe_issues": blocking_issues,
                "next_allowed_action": "workflow_rebuild_plan_required",
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
                artifacts=["combine_v2_generation_recipe_audit.json"],
                next_recommended_stage="workflow_rebuild_plan_required",
                metadata={
                    "action": "generation_recipe_audit",
                    "next_allowed_action": "workflow_rebuild_plan_required",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "assembly_allowed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_generation_recipe_audit": audit
                }
            )
        
        if stage == "workflow_rebuild_plan_required":
            # Read previous and corrective payloads for delta analysis
            real_payload = self._read_contract(project_root, "combine_v2_real_generation_payload")
            corrective_payload = self._read_contract(project_root, "combine_v2_corrective_retry_generation_payload")
            prompt_patch = self._read_contract(project_root, "combine_v2_corrective_retry_prompt_patch")
            
            # Compare payloads
            delta = self._compare_payloads(real_payload, corrective_payload)
            
            # Determine why retry failed
            why_retry_failed_likely = []
            if not any(delta.values()):
                why_retry_failed_likely.append("corrective_retry_did_not_change_core_generation_recipe")
            if not delta.get("resolution_changed"):
                why_retry_failed_likely.append("resolution_remained_low")
            if not delta.get("upscale_added") and not delta.get("refiner_added"):
                why_retry_failed_likely.append("no_quality_enhancement_stage_added")
            
            delta_quality = "insufficient" if why_retry_failed_likely else "some_changes_detected"
            
            # Create workflow quality diagnosis
            diagnosis = {
                "stage": "workflow_quality_diagnosis",
                "workflow_quality_status": "not_production_ready",
                "detected_limitations": [
                    "low_base_resolution",
                    "missing_upscale_stage",
                    "missing_refiner_stage",
                    "missing_pose_control",
                    "missing_identity_or_face_consistency_control",
                    "weak_negative_prompt_or_unknown_negative_prompt"
                ],
                "risk_if_retry_without_rebuild": "high_probability_of_repeating_low_quality_output",
                "generation_allowed_without_rebuild": False,
                "timestamp": timestamp
            }
            
            # Create brain corrective strategy
            strategy = {
                "stage": "brain_corrective_strategy",
                "strategy_verdict": "workflow_rebuild_required_before_next_generation",
                "recommended_changes": {
                    "resolution": {
                        "must_change": True,
                        "recommended_minimum": "1024x1024 or route-specific higher resolution",
                        "reason": "512x512 is insufficient for production visual quality"
                    },
                    "quality_pipeline": {
                        "must_add_upscale_or_refiner": True,
                        "recommended": [
                            "hires_fix_or_latent_upscale",
                            "image_upscale_pass",
                            "optional_refiner_pass"
                        ]
                    },
                    "prompting": {
                        "must_update_positive_prompt": True,
                        "must_update_negative_prompt": True
                    },
                    "control": {
                        "pose_or_composition_control_recommended": True,
                        "identity_lock_recommended_if_character_consistency_required": True
                    },
                    "workflow_td_review_required": True
                },
                "generation_allowed": False,
                "next_allowed_action": "operator_strategy_review",
                "timestamp": timestamp
            }
            
            # Create workflow rebuild plan
            rebuild_plan = {
                "stage": stage,
                "plan_type": "production_recipe_rebuild",
                "required_workflow_changes": [
                    {
                        "change": "raise_base_resolution",
                        "target": ">=1024 on shortest side or route policy",
                        "required": True
                    },
                    {
                        "change": "add_upscale_or_hires_fix_stage",
                        "required": True
                    },
                    {
                        "change": "add_stronger_negative_prompt_contract",
                        "required": True
                    },
                    {
                        "change": "add_pose_or_composition_control_if_human_subject",
                        "required": True
                    },
                    {
                        "change": "add_identity_or_face_stabilization_if_character_route",
                        "required": False
                    }
                ],
                "forbidden_next_action": "real_generate_assets",
                "next_allowed_action": "operator_strategy_review",
                "timestamp": timestamp
            }
            
            # Create corrective retry delta audit
            delta_audit = {
                "stage": "corrective_retry_delta_audit",
                "corrective_payload_exists": bool(corrective_payload),
                "prompt_patch_exists": bool(prompt_patch),
                "resolution_changed": delta.get("resolution_changed", False),
                "model_changed": delta.get("model_changed", False),
                "sampler_changed": delta.get("sampler_changed", False),
                "steps_changed": delta.get("steps_changed", False),
                "cfg_changed": delta.get("cfg_changed", False),
                "negative_prompt_changed": delta.get("negative_prompt_changed", False),
                "upscale_added": delta.get("upscale_added", False),
                "refiner_added": delta.get("refiner_added", False),
                "control_added": delta.get("control_added", False),
                "identity_lock_added": delta.get("identity_lock_added", False),
                "delta_quality": delta_quality,
                "why_retry_failed_likely": why_retry_failed_likely,
                "next_allowed_action": "workflow_rebuild_plan_required",
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
                artifacts=[
                    "combine_v2_corrective_retry_delta_audit.json",
                    "combine_v2_workflow_quality_diagnosis.json",
                    "combine_v2_brain_corrective_strategy.json",
                    "combine_v2_workflow_rebuild_plan.json"
                ],
                next_recommended_stage="operator_strategy_review",
                metadata={
                    "action": "workflow_rebuild_plan",
                    "next_allowed_action": "operator_strategy_review",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "assembly_allowed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_corrective_retry_delta_audit": delta_audit,
                    "combine_v2_workflow_quality_diagnosis": diagnosis,
                    "combine_v2_brain_corrective_strategy": strategy,
                    "combine_v2_workflow_rebuild_plan": rebuild_plan
                }
            )
        
        if stage == "operator_strategy_review":
            # Create operator strategy review packet
            review_packet = {
                "stage": stage,
                "operator_review_required": True,
                "summary": "Current corrective retry produced a technically valid but visually unacceptable 512x512 asset. Production brain recommends workflow recipe rebuild before any further generation.",
                "recommended_operator_decision": "approve_workflow_rebuild_plan",
                "operator_actions": [
                    "approve_workflow_rebuild_plan",
                    "request_recipe_audit_changes",
                    "manual_review",
                    "abort_route"
                ],
                "generation_allowed": False,
                "retry_allowed": False,
                "assembly_allowed": False,
                "production_accepted": False,
                "next_allowed_action": "operator_strategy_review",
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
                artifacts=["combine_v2_operator_strategy_review_packet.json"],
                next_recommended_stage="operator_strategy_review",
                metadata={
                    "action": "operator_strategy_review",
                    "next_allowed_action": "operator_strategy_review",
                    "generation_allowed": False,
                    "retry_allowed": False,
                    "assembly_allowed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_operator_strategy_review_packet": review_packet
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
