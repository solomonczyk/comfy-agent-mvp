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
            
            # 2. Evaluate status
            missing_assets = asset_gate.get("missing_assets", []) or asset_gate.get("missing", [])
            assets_resolved = not bool(missing_assets)
            
            # Preflight status (default to True if not found for stub purposes)
            preflight_ok = preflight_contract.get("preflight_passed", True)
            
            # 3. Determine decision and next action
            generation_authorized = False
            authorization_required = False
            next_allowed_action = "none"
            status = "stubbed"
            
            if not assets_resolved:
                next_allowed_action = "controlled_asset_resolution_review_required"
                blocked_by_assets = True
            else:
                blocked_by_assets = False
                if preflight_ok:
                    authorization_required = True
                    next_allowed_action = "operator_generation_authorization_required"
            
            # 4. Create artifacts
            auth_request = {
                "agent": self.role_name,
                "stage": stage,
                "assets_resolved": assets_resolved,
                "preflight_ok": preflight_ok,
                "authorization_required": authorization_required,
                "blocked_by_assets": blocked_by_assets,
                "missing_assets": missing_assets,
                "timestamp": timestamp
            }
            
            auth_decision = {
                "agent": self.role_name,
                "stage": stage,
                "generation_authorized": generation_authorized,
                "authorization_required": authorization_required,
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
                "dry_run": True
            }
            
            artifacts = [
                "combine_v2_generation_authorization_request.json",
                "combine_v2_generation_authorization_decision.json",
                "combine_v2_generation_payload_stub.json"
            ]
            
            metadata = {
                "action": "generation_authorization_request",
                "generation_authorized": generation_authorized,
                "authorization_required": authorization_required,
                "blocked_by_assets": blocked_by_assets,
                "next_recommended_stage": next_allowed_action,
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

        # DEFAULT: generate_assets or other stages
        return self.create_stub_result(context)

