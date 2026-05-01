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
        return ["generation_authorization_required", "operator_generation_authorization_required", "generate_assets"]
    
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

        # DEFAULT: other stages
        return self.create_stub_result(context)

