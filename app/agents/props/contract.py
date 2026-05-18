"""Props Agent Contract.

Defines the agent's responsibilities, permissions, and constraints.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class PropsAgentContract:
    """Contract for Props Agent.
    
    This agent reviews visual candidates for props quality:
    - visible props
    - object placement
    - object continuity risk
    - object shape/color consistency
    - character-object interaction if visible
    - props consistency with scene/genre/production design
    - missing/extra/contradictory props
    
    Critical constraints:
    - No new generation allowed
    - No retry allowed
    - No second candidate allowed
    - No ComfyUI submit allowed
    - No image editing allowed
    - No object modification allowed
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
        self.props_dir = self.control_dir / "props_agent"
        
    def create_contract(self) -> Dict[str, Any]:
        """Create the agent contract artifact."""
        contract = {
            "agent_id": "props_agent",
            "agent_role": "Props",
            "responsibility_zone": "Review visual candidates for props quality including visible props, object placement, object continuity risk, object shape/color consistency, character-object interaction if visible, props consistency with scene/genre/production design, and missing/extra/contradictory props.",
            "can_execute_generation": False,
            "can_retry": False,
            "can_accept_visual": False,
            "can_set_production_accepted": False,
            "can_run_assembly": False,
            "can_run_downstream": False,
            "can_edit_image": False,
            "can_submit_comfyui": False,
            "can_modify_objects": False,
            "can_perform_visual_qa_final_acceptance": False,
            "can_perform_operator_acceptance": False,
            "can_run_preview_render": False,
            "can_run_final_render": False,
            "can_generate_voice": False,
            "can_generate_audio": False,
            "required_inputs": [
                "visual_candidate_path",
                "previous_set_decorator_verdict",
                "props_review_authorization"
            ],
            "required_outputs": [
                "props_review_report",
                "props_verdict",
                "props_review_authorization"
            ],
            "stop_condition": "stop_after_review_and_wait_for_next_gate",
            "review_criteria": [
                "visible_props",
                "object_placement",
                "object_continuity_risk",
                "object_shape_color_consistency",
                "character_object_interaction",
                "scene_genre_production_design_consistency",
                "missing_extra_contradictory_props"
            ],
            "blocking_conditions": [
                "candidate_missing",
                "candidate_sha256_mismatch",
                "previous_agent_not_completed"
            ],
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        self.props_dir.mkdir(parents=True, exist_ok=True)
        contract_path = self.props_dir / "props_agent_contract.json"
        
        with open(contract_path, 'w') as f:
            json.dump(contract, f, indent=2)
        
        return contract
    
    def create_review_authorization(self) -> Dict[str, Any]:
        """Create the review authorization artifact."""
        authorization = {
            "task_id": "RC-COMBINE-V2-PROPS-VERTICAL-SLICE-001",
            "source_state": "props_review_required",
            "review_authorized": True,
            "generation_authorized": False,
            "retry_authorized": False,
            "render_authorized": False,
            "downstream_authorized": False,
            "review_candidate_path": "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png",
            "candidate_sha256": "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b",
            "previous_set_decorator_verdict": "ACCEPTED",
            "previous_set_decorator_commit": "7773ae9",
            "max_reviews": 1,
            "new_generation_forbidden": True,
            "retry_forbidden": True,
            "second_generation_forbidden": True,
            "comfyui_submit_forbidden": True,
            "image_editing_forbidden": True,
            "object_modification_forbidden": True,
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
        
        auth_path = self.props_dir / "props_review_authorization.json"
        
        with open(auth_path, 'w') as f:
            json.dump(authorization, f, indent=2)
        
        return authorization
