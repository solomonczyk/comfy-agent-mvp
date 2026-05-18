"""Costume Agent Contract.

Defines the agent's responsibilities, permissions, and constraints.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class CostumeAgentContract:
    """Contract for Costume Agent.
    
    This agent reviews visual candidates for costume quality:
    - visible costume/clothing
    - outfit consistency with character
    - costume style coherence
    - genre/era/style consistency
    - clothing artifacts
    - costume continuity risk
    
    Critical constraints:
    - No new generation allowed
    - No retry allowed
    - No second candidate allowed
    - No ComfyUI submit allowed
    - No image editing allowed
    - No costume modification allowed
    - No actor/body modification allowed
    - No preview/final render allowed
    - No Visual QA final acceptance allowed
    - No operator acceptance by agent allowed
    - No assembly allowed
    - No voice/audio allowed
    - No downstream allowed
    - production_accepted must remain false
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.costume_dir = self.control_dir / "costume_agent"
        
    def create_contract(self) -> Dict[str, Any]:
        """Create the agent contract artifact."""
        contract = {
            "agent_id": "costume_agent",
            "agent_role": "Costume",
            "responsibility_zone": "Review visual candidates for costume quality including visible costume/clothing, outfit consistency with character, costume style coherence, genre/era/style consistency, clothing artifacts, and costume continuity risk.",
            "can_execute_generation": False,
            "can_retry": False,
            "can_accept_visual": False,
            "can_set_production_accepted": False,
            "can_run_assembly": False,
            "can_run_downstream": False,
            "can_edit_image": False,
            "can_submit_comfyui": False,
            "can_modify_costume": False,
            "can_modify_actor_body": False,
            "can_perform_visual_qa_final_acceptance": False,
            "can_perform_operator_acceptance": False,
            "can_run_preview_render": False,
            "can_run_final_render": False,
            "can_generate_voice": False,
            "can_generate_audio": False,
            "required_inputs": [
                "visual_candidate_path",
                "previous_props_verdict",
                "costume_review_authorization"
            ],
            "required_outputs": [
                "costume_review_report",
                "costume_verdict",
                "costume_review_authorization"
            ],
            "stop_condition": "stop_after_review_and_wait_for_next_gate",
            "review_criteria": [
                "visible_costume_clothing",
                "outfit_consistency_with_character",
                "costume_style_coherence",
                "genre_era_style_consistency",
                "clothing_artifacts",
                "costume_continuity_risk"
            ],
            "blocking_conditions": [
                "candidate_missing",
                "candidate_sha256_mismatch",
                "previous_agent_not_completed"
            ],
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        self.costume_dir.mkdir(parents=True, exist_ok=True)
        contract_path = self.costume_dir / "costume_agent_contract.json"
        
        with open(contract_path, 'w') as f:
            json.dump(contract, f, indent=2)
        
        return contract
    
    def create_review_authorization(self) -> Dict[str, Any]:
        """Create the review authorization artifact."""
        authorization = {
            "task_id": "RC-COMBINE-V2-COSTUME-VERTICAL-SLICE-001",
            "source_state": "costume_review_required",
            "review_authorized": True,
            "generation_authorized": False,
            "retry_authorized": False,
            "render_authorized": False,
            "downstream_authorized": False,
            "review_candidate_path": "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png",
            "candidate_sha256": "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b",
            "previous_props_verdict": "ACCEPTED",
            "previous_props_commit": "f248d8e",
            "max_reviews": 1,
            "new_generation_forbidden": True,
            "retry_forbidden": True,
            "second_generation_forbidden": True,
            "comfyui_submit_forbidden": True,
            "image_editing_forbidden": True,
            "costume_modification_forbidden": True,
            "actor_body_modification_forbidden": True,
            "render_forbidden": True,
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
        
        auth_path = self.costume_dir / "costume_review_authorization.json"
        
        with open(auth_path, 'w') as f:
            json.dump(authorization, f, indent=2)
        
        return authorization
