"""Camera Operator Agent Contract.

Defines the agent's responsibilities, permissions, and constraints.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class CameraOperatorAgentContract:
    """Contract for Camera Operator Agent.
    
    This agent executes authorized full-frame corrective generation
    with strict limits: exactly one generation, no retry, no automatic
    visual acceptance, stops for operator visual review.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.camera_operator_dir = self.control_dir / "camera_operator_agent"
        
    def create_contract(self) -> Dict[str, Any]:
        """Create the agent contract artifact."""
        contract = {
            "agent_id": "camera_operator_agent",
            "agent_role": "Camera Operator / Generation Operator",
            "responsibility_zone": "Execute authorized visual generation according to approved shot/camera/generation contract.",
            "can_execute_generation": True,
            "generation_requires_operator_authorization": True,
            "can_retry": False,
            "can_accept_visual": False,
            "can_set_production_accepted": False,
            "can_run_assembly": False,
            "can_run_downstream": False,
            "required_inputs": [
                "full_frame_corrective_generation_contract",
                "reference_usage_scope_policy",
                "full_frame_corrective_prompt_recipe",
                "operator_authorization"
            ],
            "required_outputs": [
                "generation_manifest",
                "generation_result_review",
                "operator_visual_review_packet"
            ],
            "stop_condition": "stop_after_one_generation_and_wait_for_operator_visual_review",
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        self.camera_operator_dir.mkdir(parents=True, exist_ok=True)
        contract_path = self.camera_operator_dir / "camera_operator_agent_contract.json"
        
        with open(contract_path, 'w') as f:
            json.dump(contract, f, indent=2)
        
        return contract
    
    def create_tool_policy(self) -> Dict[str, Any]:
        """Create the tool/permission policy artifact."""
        policy = {
            "agent_id": "camera_operator_agent",
            "allowed_tools": [
                "filesystem.read_contracts",
                "filesystem.write_artifacts",
                "comfyui.submit_once_when_authorized",
                "image.read_metadata",
                "image.sha256",
                "json.validate",
                "state.update_after_execution"
            ],
            "forbidden_tools": [
                "comfyui.submit_without_authorization",
                "comfyui.submit_second_generation",
                "generation.retry",
                "visual_qa.accept",
                "operator.accept",
                "preview.render",
                "assembly.run",
                "voice.generate",
                "downstream.run",
                "production.accept"
            ],
            "max_comfyui_submits": 1,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        policy_path = self.camera_operator_dir / "camera_operator_tool_policy.json"
        
        with open(policy_path, 'w') as f:
            json.dump(policy, f, indent=2)
        
        return policy
    
    def create_operator_authorization(self) -> Dict[str, Any]:
        """Create the operator authorization artifact for one generation."""
        authorization = {
            "task_id": "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001",
            "operator_authorized": True,
            "authorized_action": "execute_one_full_frame_corrective_generation",
            "authorization_source": "current_operator_directive",
            "max_generations": 1,
            "generation_gate_open": True,
            "target_output_type": "full_frame_production_visual_candidate",
            "body_part_crop_forbidden": True,
            "quality_references_are_not_composition_targets": True,
            "stop_after_generation": True,
            "operator_visual_review_required_after_generation": True,
            "retry_authorized": False,
            "blind_retry_allowed": False,
            "second_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        auth_path = self.camera_operator_dir / "operator_authorization_one_full_frame_generation.json"
        
        with open(auth_path, 'w') as f:
            json.dump(authorization, f, indent=2)
        
        return authorization
