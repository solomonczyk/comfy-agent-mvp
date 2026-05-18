"""Actor / Character Control Agent Contract.

Defines the agent's responsibilities, permissions, and constraints.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ActorCharacterControlAgentContract:
    """Contract for Actor / Character Control Agent.
    
    This agent reviews visual candidates for actor/character quality:
    - face quality
    - eyes
    - mouth/teeth
    - skin realism
    - expression
    - anatomy/body consistency if visible
    - identity/style consistency
    
    Critical constraints:
    - No new generation allowed
    - No retry allowed
    - No second candidate allowed
    - No ComfyUI submit allowed
    - No image editing allowed
    - No Visual QA final acceptance allowed
    - No operator acceptance by agent allowed
    - No assembly allowed
    - No preview/final render allowed
    - No voice/audio allowed
    - No downstream allowed
    - production_accepted must remain false
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.actor_character_dir = self.control_dir / "actor_character_control_agent"
        
    def create_contract(self) -> Dict[str, Any]:
        """Create the agent contract artifact."""
        contract = {
            "agent_id": "actor_character_control_agent",
            "agent_role": "Actor / Character Control",
            "responsibility_zone": "Review visual candidates for actor/character quality including face, eyes, mouth/teeth, skin realism, expression, anatomy/body consistency if visible, and identity/style consistency.",
            "can_execute_generation": False,
            "can_retry": False,
            "can_accept_visual": False,
            "can_set_production_accepted": False,
            "can_run_assembly": False,
            "can_run_downstream": False,
            "can_edit_image": False,
            "can_submit_comfyui": False,
            "can_perform_visual_qa_final_acceptance": False,
            "can_perform_operator_acceptance": False,
            "can_run_preview_render": False,
            "can_run_final_render": False,
            "can_generate_voice": False,
            "can_generate_audio": False,
            "required_inputs": [
                "visual_candidate_path",
                "previous_dop_verdict",
                "actor_character_control_review_authorization"
            ],
            "required_outputs": [
                "actor_character_review_report",
                "actor_character_verdict",
                "actor_character_review_authorization"
            ],
            "stop_condition": "stop_after_review_and_wait_for_next_gate",
            "review_criteria": [
                "face_quality",
                "eye_artifacts",
                "mouth_teeth_artifacts",
                "skin_realism",
                "expression_mood_consistency",
                "anatomy_body_consistency_if_visible",
                "identity_style_consistency"
            ],
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        self.actor_character_dir.mkdir(parents=True, exist_ok=True)
        contract_path = self.actor_character_dir / "actor_character_agent_contract.json"
        
        with open(contract_path, 'w') as f:
            json.dump(contract, f, indent=2)
        
        return contract
    
    def create_review_authorization(self) -> Dict[str, Any]:
        """Create the review authorization artifact."""
        authorization = {
            "task_id": "RC-COMBINE-V2-ACTOR-CHARACTER-CONTROL-VERTICAL-SLICE-001",
            "source_state": "actor_character_control_review_required",
            "review_authorized": True,
            "generation_authorized": False,
            "retry_authorized": False,
            "downstream_authorized": False,
            "review_candidate_path": "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png",
            "candidate_sha256": "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b",
            "previous_dop_verdict": "ACCEPTED_FOR_NEXT_GATE",
            "previous_dop_commit": "f59f2a7",
            "max_reviews": 1,
            "new_generation_forbidden": True,
            "retry_forbidden": True,
            "second_generation_forbidden": True,
            "comfyui_submit_forbidden": True,
            "image_editing_forbidden": True,
            "visual_qa_final_acceptance_forbidden": True,
            "operator_acceptance_by_agent_forbidden": True,
            "assembly_forbidden": True,
            "preview_render_forbidden": True,
            "final_render_forbidden": True,
            "voice_audio_forbidden": True,
            "downstream_forbidden": True,
            "production_accepted_forbidden": True,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        auth_path = self.actor_character_dir / "actor_character_review_authorization.json"
        
        with open(auth_path, 'w') as f:
            json.dump(authorization, f, indent=2)
        
        return authorization
