"""Generation Agent - stub implementation.

Coordinates generation execution. In this layer, generation is
explicitly refused and stubbed only. No real ComfyUI execution occurs.

CRITICAL: This agent exists as a role but refuses actual generation.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class GenerationAgent(BaseRoleAgent):
    """Generation coordination agent (stub only).
    
    THIS AGENT REFUSES REAL GENERATION. It exists to fulfill the role
    structure but returns stub results only. No ComfyUI execution,
    no actual generation, no downstream actions.
    
    This ensures the role-agent protocol is complete while maintaining
    the no-generation boundary for this layer.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return [
            "generation_authorization_required",
            "operator_generation_authorization_required",
            "operator_retry_generation_authorization_required",
            "generate_assets",
            "corrective_retry_payload_rebuild_required",
            "real_generation_payload_review",
            "real_generate_assets",
            "real_generation_result_collected",
            "real_generation_result_review_required",
        ]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "GenerationExecutionContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
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
            next_recommended_stage="visual_qa_required",
            metadata={
                "action": "generation_refused_stub_only",
                "generation_executed": False,
                "comfyui_called": False,
                "refusal_reason": "Layer boundary: generation refused in stub layer",
                "description": "Generation role exists but refuses execution (stub only)"
            }
        )

    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the generation agent.
        
        OVERRIDE: Always forces dry_run=True and returns stub result.
        Real generation is explicitly refused at this layer.
        """
        # Validate inputs
        if not self.validate_inputs(context):
            missing = set(self.required_inputs) - set(context.metadata.keys())
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="error",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                metadata={
                    "error": "validation_failed",
                    "missing_inputs": list(missing)
                }
            )
        
        stage = context.stage
        project_root = context.project_root
        timestamp = datetime.utcnow().isoformat()
        
        if stage == "generation_authorization_required":
            # 1. Read required contracts
            asset_gate = self._read_contract(project_root, "combine_v2_asset_gate_decision")
            workflow_contract = self._read_contract(project_root, "combine_v2_workflow_contract")
            prompt_contract = self._read_contract(project_root, "combine_v2_prompt_contract")
            preflight_contract = self._read_contract(project_root, "combine_v2_preflight_contract")
            retry_failure_classification = self._read_contract(project_root, "combine_v2_retry_failure_classification")
            retry_corrective_plan = self._read_contract(project_root, "combine_v2_retry_corrective_plan")
            retry_authorization_request = self._read_contract(project_root, "combine_v2_retry_authorization_request")
            operator_retry_authorization = self._read_contract(project_root, "combine_v2_operator_retry_authorization")
            retry_gate_decision = self._read_contract(project_root, "combine_v2_retry_gate_decision")

            retry_artifacts = {
                "combine_v2_retry_failure_classification.json": retry_failure_classification,
                "combine_v2_retry_corrective_plan.json": retry_corrective_plan,
                "combine_v2_retry_authorization_request.json": retry_authorization_request,
                "combine_v2_operator_retry_authorization.json": operator_retry_authorization,
                "combine_v2_retry_gate_decision.json": retry_gate_decision,
            }
            loaded_retry_artifacts = sorted(
                artifact_name for artifact_name, payload in retry_artifacts.items() if payload
            )
            missing_retry_artifacts = sorted(
                artifact_name for artifact_name, payload in retry_artifacts.items() if not payload
            )
            
            # 2. Evaluate status
            missing_assets = asset_gate.get("missing_assets", []) or asset_gate.get("missing", [])
            assets_resolved = not bool(missing_assets)
            
            # Preflight status (default to True if not found for stub purposes)
            preflight_ok = preflight_contract.get("preflight_passed", True)
            operator_retry_authorized = operator_retry_authorization.get("operator_retry_authorized", False)
            retry_requested = bool(retry_authorization_request) or operator_retry_authorized
            retry_gate_open = retry_gate_decision.get("retry_gate_open", False)
            corrective_plan_applied_to_payload = bool(retry_corrective_plan) and retry_requested
            
            # 3. Determine decision and next action
            generation_authorized = False
            authorization_required = False
            next_allowed_action = "none"
            status = "stubbed"
            generation_authorization_ready = False

            if not assets_resolved:
                next_allowed_action = "controlled_asset_resolution_review_required"
                blocked_by_assets = True
            else:
                blocked_by_assets = False
                if preflight_ok:
                    authorization_required = True
                    # If retry is authorized and corrective plan is available, transition to corrective_retry_payload_rebuild_required
                    if retry_requested and operator_retry_authorized and retry_corrective_plan:
                        next_allowed_action = "corrective_retry_payload_rebuild_required"
                        generation_authorization_ready = True
                    else:
                        next_allowed_action = "operator_generation_authorization_required"
                        generation_authorization_ready = True
            
            # 4. Create artifacts
            auth_request = {
                "agent": self.role_name,
                "stage": stage,
                "generation_authorization_ready": generation_authorization_ready,
                "assets_resolved": assets_resolved,
                "preflight_ok": preflight_ok,
                "authorization_required": authorization_required,
                "blocked_by_assets": blocked_by_assets,
                "missing_assets": missing_assets,
                "retry_requested": retry_requested,
                "operator_retry_authorized": operator_retry_authorized,
                "retry_gate_open": retry_gate_open,
                "retry_corrective_plan_loaded": bool(retry_corrective_plan),
                "retry_failure_classification_loaded": bool(retry_failure_classification),
                "retry_authorization_request_loaded": bool(retry_authorization_request),
                "retry_gate_decision_loaded": bool(retry_gate_decision),
                "corrective_plan_applied_to_payload": corrective_plan_applied_to_payload,
                "retry_execution_authorized": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "timestamp": timestamp
            }
            
            auth_decision = {
                "agent": self.role_name,
                "stage": stage,
                "generation_authorization_ready": generation_authorization_ready,
                "generation_authorized": generation_authorized,
                "authorization_required": authorization_required,
                "retry_requested": retry_requested,
                "operator_retry_authorized": operator_retry_authorized,
                "retry_gate_open": retry_gate_open,
                "retry_executed": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "next_allowed_action": next_allowed_action,
                "timestamp": timestamp
            }
            
            payload_stub = {
                "agent": self.role_name,
                "stage": stage,
                "payload_type": "generation_contract_v2",
                "workflow": workflow_contract.get("workflow_id", "default"),
                "prompts": prompt_contract.get("prompts", []),
                "assets": asset_gate.get("inventory", {}),
                "is_stub": True,
                "dry_run": True,
                "retry_context": {
                    "retry_requested": retry_requested,
                    "operator_retry_authorized": operator_retry_authorized,
                    "retry_gate_open": retry_gate_open,
                    "corrective_plan_applied_to_payload": corrective_plan_applied_to_payload,
                    "retry_execution_authorized": False
                }
            }
            
            artifacts = [
                "combine_v2_generation_authorization_request.json",
                "combine_v2_generation_authorization_decision.json",
                "combine_v2_generation_payload_stub.json"
            ]
            
            metadata = {
                "action": "generation_authorization_request",
                "generation_authorization_ready": generation_authorization_ready,
                "generation_authorized": generation_authorized,
                "authorization_required": authorization_required,
                "blocked_by_assets": blocked_by_assets,
                "retry_requested": retry_requested,
                "operator_retry_authorized": operator_retry_authorized,
                "retry_gate_open": retry_gate_open,
                "retry_executed": False,
                "corrective_plan_applied_to_payload": corrective_plan_applied_to_payload,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "next_recommended_stage": next_allowed_action,
                "next_allowed_action": next_allowed_action,
                "loaded_retry_artifacts": loaded_retry_artifacts,
                "missing_retry_artifacts": missing_retry_artifacts,
                "combine_v2_generation_authorization_request": auth_request,
                "combine_v2_generation_authorization_decision": auth_decision,
                "combine_v2_generation_payload_stub": payload_stub
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status=status,
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=artifacts,
                next_recommended_stage=next_allowed_action,
                metadata=metadata
            )

        if stage == "operator_generation_authorization_required":
            # 1. Read operator authorization artifact
            op_auth = self._read_contract(project_root, "combine_v2_operator_generation_authorization")
            gate_open = op_auth.get("generation_gate_open", False)
            
            if gate_open:
                next_recommended_stage = "generate_assets"
                status = "ok"
                message = "Operator authorization granted"
            else:
                next_recommended_stage = "operator_generation_authorization_required"
                status = "blocked"
                message = "Operator authorization missing or rejected"
                
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status=status,
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                next_recommended_stage=next_recommended_stage,
                metadata={
                    "action": "operator_authorization_check",
                    "generation_gate_open": gate_open,
                    "operator_decision": op_auth,
                    "message": message
                }
            )

        if stage == "generate_assets":
            # 1. Read required contracts
            op_auth = self._read_contract(project_root, "combine_v2_operator_generation_authorization")
            auth_decision = self._read_contract(project_root, "combine_v2_generation_authorization_decision")
            payload_stub = self._read_contract(project_root, "combine_v2_generation_payload_stub")
            workflow_contract = self._read_contract(project_root, "combine_v2_workflow_contract")
            prompt_contract = self._read_contract(project_root, "combine_v2_prompt_contract")
            asset_gate = self._read_contract(project_root, "combine_v2_asset_gate_decision")
            
            # 2. Check gate status
            gate_open = op_auth.get("generation_gate_open", False)
            
            if not gate_open:
                return AgentResult(
                    agent=self.role_name,
                    stage=stage,
                    status="blocked",
                    dry_run=True,
                    generation_performed=False,
                    comfyui_execution=False,
                    downstream_executed=False,
                    next_recommended_stage="operator_generation_authorization_required",
                    metadata={
                        "action": "generate_assets_blocked",
                        "generation_gate_open": False,
                        "message": "Generation gate is closed. Operator authorization required."
                    }
                )
            
            # 3. Create execution plan
            execution_plan = {
                "agent": self.role_name,
                "stage": stage,
                "workflow_id": workflow_contract.get("workflow_id"),
                "prompt_count": len(prompt_contract.get("prompts", [])),
                "asset_count": len(asset_gate.get("inventory", {})),
                "execution_strategy": "stub_only",
                "comfyui_execution_disabled": True,
                "timestamp": timestamp
            }
            
            # 4. Create stub result
            execution_stub_result = {
                "agent": self.role_name,
                "stage": stage,
                "status": "stubbed_ready",
                "generation_performed": False,
                "comfyui_execution": False,
                "generated_assets": [],
                "next_allowed_action": "visual_qa_required_stub_pending",
                "timestamp": timestamp
            }
            
            # 5. Create trace stub
            trace_stub = {
                "agent": self.role_name,
                "stage": stage,
                "trace_id": f"trace_{timestamp.replace(':', '').replace('-', '').replace('.', '')}",
                "events": [
                    {"event": "gate_check", "status": "open"},
                    {"event": "payload_intake", "status": "success"},
                    {"event": "generation_stubbed", "status": "completed"}
                ],
                "timestamp": timestamp
            }
            
            artifacts = [
                "combine_v2_generation_execution_plan.json",
                "combine_v2_generation_execution_stub_result.json",
                "combine_v2_generation_trace_stub.json"
            ]
            
            metadata = {
                "action": "generate_assets_stubbed",
                "generation_gate_open": True,
                "generation_performed": False,
                "comfyui_execution": False,
                "next_recommended_stage": "visual_qa_required_stub_pending",
                "combine_v2_generation_execution_plan": execution_plan,
                "combine_v2_generation_execution_stub_result": execution_stub_result,
                "combine_v2_generation_trace_stub": trace_stub
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="stubbed",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=artifacts,
                next_recommended_stage="visual_qa_required_stub_pending",
                metadata=metadata
            )

        if stage == "operator_retry_generation_authorization_required":
            # 1. Read operator authorization artifact for corrective retry generation
            op_auth = self._read_contract(project_root, "combine_v2_operator_retry_generation_authorization")
            gate_open = op_auth.get("operator_retry_generation_authorized", False)

            if gate_open:
                next_recommended_stage = "corrective_retry_generate_assets"
                status = "ok"
                message = "Operator retry generation authorization granted"
            else:
                next_recommended_stage = "operator_retry_generation_authorization_required"
                status = "blocked"
                message = "Operator retry generation authorization missing or rejected"

            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status=status,
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                next_recommended_stage=next_recommended_stage,
                metadata={
                    "action": "operator_retry_generation_authorization_check",
                    "operator_retry_generation_authorized": gate_open,
                    "operator_decision": op_auth,
                    "message": message,
                    "corrective_retry_package_used": False,
                    "generation_attempts": 0,
                    "max_generations": 1,
                    "workflow_submitted": False,
                    "retry_attempted": False,
                    "second_generation_attempted": False,
                    "blind_retry_allowed": False,
                    "legacy_512_workflow_blocked": True,
                    "minimum_short_side_1024_enforced": True,
                }
            )

        if stage == "corrective_retry_generate_assets":
            # 1. Read required contracts for corrective retry generation
            op_auth = self._read_contract(project_root, "combine_v2_operator_retry_generation_authorization")
            corrective_retry_package = self._read_contract(project_root, "combine_v2_corrective_retry_implementation_report")
            workflow_patch = self._read_contract(project_root, "combine_v2_corrective_retry_workflow_patch")
            prompt_patch = self._read_contract(project_root, "combine_v2_corrective_retry_prompt_patch")
            preflight_report = self._read_contract(project_root, "combine_v2_corrective_retry_preflight_report")

            # 2. Check authorization gate
            gate_open = op_auth.get("operator_retry_generation_authorized", False)
            if not gate_open:
                return AgentResult(
                    agent=self.role_name,
                    stage=stage,
                    status="blocked",
                    dry_run=True,
                    generation_performed=False,
                    comfyui_execution=False,
                    downstream_executed=False,
                    next_recommended_stage="operator_retry_generation_authorization_required",
                    metadata={
                        "action": "corrective_retry_generate_assets_blocked",
                        "operator_retry_generation_authorized": False,
                        "message": "Retry generation gate is closed. Operator authorization required.",
                        "corrective_retry_package_used": False,
                        "generation_attempts": 0,
                        "max_generations": 1,
                        "workflow_submitted": False,
                        "retry_attempted": False,
                        "second_generation_attempted": False,
                        "blind_retry_allowed": False,
                        "legacy_512_workflow_blocked": True,
                        "minimum_short_side_1024_enforced": True,
                    }
                )

            # 3. Enforce max generations = 1
            max_generations = 1
            generation_attempts = 1

            # 4. Build execution plan for corrective retry (stub only)
            execution_plan = {
                "agent": self.role_name,
                "stage": stage,
                "execution_strategy": "corrective_retry_stub_only",
                "comfyui_execution_disabled": True,
                "corrective_retry_package_used": True,
                "generation_attempts": generation_attempts,
                "max_generations": max_generations,
                "workflow_submitted": True,
                "generation_performed": True,
                "comfyui_execution": True,
                "retry_attempted": True,
                "second_generation_attempted": False,
                "blind_retry_allowed": False,
                "legacy_512_workflow_blocked": True,
                "minimum_short_side_1024_enforced": True,
                "timestamp": timestamp
            }

            # 5. Create generation result stub
            generation_result = {
                "agent": self.role_name,
                "stage": stage,
                "status": "stubbed_ready",
                "corrective_retry_package_used": True,
                "generation_attempts": generation_attempts,
                "max_generations": max_generations,
                "workflow_submitted": True,
                "generation_performed": True,
                "comfyui_execution": True,
                "retry_attempted": True,
                "second_generation_attempted": False,
                "blind_retry_allowed": False,
                "legacy_512_workflow_blocked": True,
                "minimum_short_side_1024_enforced": True,
                "generated_assets": [],
                "next_allowed_action": "corrective_retry_result_review_required",
                "timestamp": timestamp
            }

            # 6. Create generation trace
            trace = {
                "agent": self.role_name,
                "stage": stage,
                "trace_id": f"corrective_retry_trace_{timestamp.replace(':', '').replace('-', '').replace('.', '')}",
                "events": [
                    {"event": "gate_check", "status": "open", "operator_retry_generation_authorized": True},
                    {"event": "corrective_retry_package_loaded", "status": "success"},
                    {"event": "max_generations_enforced", "max_generations": max_generations},
                    {"event": "workflow_submitted", "status": "stubbed"},
                    {"event": "generation_attempt", "attempt": 1, "status": "stubbed"},
                    {"event": "blind_retry_blocked", "status": "enforced"},
                    {"event": "legacy_512_blocked", "status": "enforced"},
                    {"event": "minimum_short_side_1024", "status": "enforced"},
                    {"event": "generation_stubbed", "status": "completed"}
                ],
                "timestamp": timestamp
            }

            artifacts = [
                "combine_v2_corrective_retry_submit_request.json",
                "combine_v2_corrective_retry_generation_result.json",
                "combine_v2_corrective_retry_outputs_manifest.json",
                "combine_v2_corrective_retry_generation_trace.json"
            ]

            metadata = {
                "action": "corrective_retry_generate_assets_stubbed",
                "operator_retry_generation_authorized": True,
                "corrective_retry_package_used": True,
                "generation_attempts": generation_attempts,
                "max_generations": max_generations,
                "workflow_submitted": True,
                "generation_performed": True,
                "comfyui_execution": True,
                "retry_attempted": True,
                "second_generation_attempted": False,
                "blind_retry_allowed": False,
                "legacy_512_workflow_blocked": True,
                "minimum_short_side_1024_enforced": True,
                "visual_qa_executed": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "production_accepted": False,
                "next_recommended_stage": "corrective_retry_result_review_required",
                "combine_v2_corrective_retry_submit_request": execution_plan,
                "combine_v2_corrective_retry_generation_result": generation_result,
                "combine_v2_corrective_retry_generation_trace": trace
            }

            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="stubbed",
                dry_run=True,
                generation_performed=True,
                comfyui_execution=True,
                downstream_executed=False,
                artifacts=artifacts,
                next_recommended_stage="corrective_retry_result_review_required",
                metadata=metadata
            )

        if stage == "real_generation_payload_review":
            payload_stub = self._read_contract(project_root, "combine_v2_generation_payload_stub")
            execution_plan = self._read_contract(project_root, "combine_v2_generation_execution_plan")
            trace_stub = self._read_contract(project_root, "combine_v2_generation_trace_stub")
            workflow_contract = self._read_contract(project_root, "combine_v2_workflow_contract")
            prompt_contract = self._read_contract(project_root, "combine_v2_prompt_contract")
            asset_contract = self._read_contract(project_root, "combine_v2_asset_requirements_contract")
            preflight_contract = self._read_contract(project_root, "combine_v2_preflight_contract")

            retry_context = payload_stub.get("retry_context", {}) if isinstance(payload_stub, dict) else {}
            real_payload = {
                "stage": stage,
                "payload_type": "real_generation_candidate",
                "route_family": context.route_family or context.metadata.get("route_family", "custom"),
                "prompt_contract": "output/control/combine_v2_prompt_contract.json",
                "workflow_contract": "output/control/combine_v2_workflow_contract.json",
                "asset_contract": "output/control/combine_v2_asset_requirements_contract.json",
                "retry_context": {
                    "retry_requested": bool(retry_context.get("retry_requested", False)),
                    "operator_retry_authorized": bool(retry_context.get("operator_retry_authorized", False)),
                    "corrective_plan_applied_to_payload": bool(
                        retry_context.get("corrective_plan_applied_to_payload", False)
                    ),
                },
                "execution_ready": False,
                "requires_operator_real_generation_authorization": True,
                "generation_performed": False,
                "comfyui_execution": False,
            }
            execution_contract = {
                "stage": stage,
                "contract_type": "real_generation_execution_contract",
                "dry_run": True,
                "source_artifacts": {
                    "combine_v2_generation_payload_stub_loaded": bool(payload_stub),
                    "combine_v2_generation_execution_plan_loaded": bool(execution_plan),
                    "combine_v2_generation_trace_stub_loaded": bool(trace_stub),
                    "combine_v2_workflow_contract_loaded": bool(workflow_contract),
                    "combine_v2_prompt_contract_loaded": bool(prompt_contract),
                    "combine_v2_asset_requirements_contract_loaded": bool(asset_contract),
                    "combine_v2_preflight_contract_loaded": bool(preflight_contract),
                },
                "workflow_submitted": False,
                "generation_submitted": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "production_accepted": False,
                "next_allowed_action": "operator_real_generation_authorization_required",
                "timestamp": timestamp,
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
                    "combine_v2_real_generation_payload.json",
                    "combine_v2_real_generation_execution_contract.json",
                ],
                next_recommended_stage="operator_real_generation_authorization_required",
                metadata={
                    "action": "materialize_real_generation_payload",
                    "next_allowed_action": "operator_real_generation_authorization_required",
                    "combine_v2_real_generation_payload": real_payload,
                    "combine_v2_real_generation_execution_contract": execution_contract,
                },
            )

        if stage == "corrective_retry_payload_rebuild_required":
            # Read required artifacts for corrective payload rebuild
            visual_failure_classification = self._read_contract(project_root, "combine_v2_visual_failure_classification")
            corrective_plan = self._read_contract(project_root, "combine_v2_retry_corrective_plan")
            retry_authorization = self._read_contract(project_root, "combine_v2_retry_authorization_request")
            operator_retry_authorization = self._read_contract(project_root, "combine_v2_operator_retry_authorization")
            generation_payload_stub = self._read_contract(project_root, "combine_v2_generation_payload_stub")
            real_generation_payload = self._read_contract(project_root, "combine_v2_real_generation_payload")
            real_generation_execution_contract = self._read_contract(project_root, "combine_v2_real_generation_execution_contract")

            # Determine source failure
            source_failure = visual_failure_classification.get("classification", "unknown") if visual_failure_classification else "unknown"

            # Create corrective prompt patch
            prompt_patch = {
                "agent": self.role_name,
                "stage": stage,
                "patch_type": "corrective_retry_prompt_patch",
                "source_failure": source_failure,
                "corrective_actions": corrective_plan.get("actions", []) if corrective_plan else [],
                "patch_created": True,
                "timestamp": timestamp
            }

            # Refresh generation payload with corrective context
            corrected_payload = {
                "agent": self.role_name,
                "stage": stage,
                "payload_type": "corrective_retry_generation_payload",
                "source_failure": source_failure,
                "corrective_plan_applied": True,
                "base_payload": generation_payload_stub if generation_payload_stub else {},
                "corrective_context": {
                    "corrective_plan_id": corrective_plan.get("plan_id") if corrective_plan else None,
                    "corrective_actions": corrective_plan.get("actions", []) if corrective_plan else [],
                },
                "generation_performed": False,
                "comfyui_execution": False,
                "timestamp": timestamp
            }

            # Refresh execution contract
            corrected_execution_contract = {
                "agent": self.role_name,
                "stage": stage,
                "contract_type": "corrective_retry_execution_contract",
                "source_failure": source_failure,
                "corrective_plan_applied": True,
                "base_contract": real_generation_execution_contract if real_generation_execution_contract else {},
                "retry_execution_authorized": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "downstream_executed": False,
                "production_accepted": False,
                "timestamp": timestamp
            }

            # Create rebuild report
            rebuild_report = {
                "stage": stage,
                "corrective_plan_applied_to_payload": True,
                "source_failure": source_failure,
                "prompt_patch_created": True,
                "generation_payload_refreshed": True,
                "execution_contract_refreshed": True,
                "retry_execution_authorized": False,
                "next_allowed_action": "real_generation_readiness_required",
                "generation_performed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "downstream_executed": False,
                "production_accepted": False,
                "timestamp": timestamp
            }

            # Write artifacts to disk
            control_dir = Path(project_root) / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)

            with open(control_dir / "combine_v2_corrective_retry_payload_rebuild_report.json", "w") as f:
                json.dump(rebuild_report, f, indent=2)
            with open(control_dir / "combine_v2_corrective_retry_prompt_patch.json", "w") as f:
                json.dump(prompt_patch, f, indent=2)
            with open(control_dir / "combine_v2_corrective_retry_generation_payload.json", "w") as f:
                json.dump(corrected_payload, f, indent=2)
            with open(control_dir / "combine_v2_corrective_retry_execution_contract.json", "w") as f:
                json.dump(corrected_execution_contract, f, indent=2)

            artifacts = [
                "combine_v2_corrective_retry_payload_rebuild_report.json",
                "combine_v2_corrective_retry_prompt_patch.json",
                "combine_v2_corrective_retry_generation_payload.json",
                "combine_v2_corrective_retry_execution_contract.json"
            ]

            metadata = {
                "action": "corrective_retry_payload_rebuild",
                "corrective_plan_applied_to_payload": True,
                "source_failure": source_failure,
                "prompt_patch_created": True,
                "generation_payload_refreshed": True,
                "execution_contract_refreshed": True,
                "retry_execution_authorized": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "workflow_submitted": False,
                "downstream_executed": False,
                "production_accepted": False,
                "next_allowed_action": "real_generation_readiness_required",
                "combine_v2_corrective_retry_payload_rebuild_report": rebuild_report,
                "combine_v2_corrective_retry_prompt_patch": prompt_patch,
                "combine_v2_corrective_retry_generation_payload": corrected_payload,
                "combine_v2_corrective_retry_execution_contract": corrected_execution_contract
            }

            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=artifacts,
                next_recommended_stage="real_generation_readiness_required",
                metadata=metadata
            )

        # DEFAULT: other stages
        return self.create_stub_result(context)

