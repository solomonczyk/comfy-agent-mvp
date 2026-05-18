"""
Director of Photography Agent Contract
Defines the role, responsibilities, and constraints for the DoP agent.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class DirectorOfPhotographyAgentContract:
    """Director of Photography Agent contract and policy definition."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.agent_id = "director_of_photography_agent"
        self.task_id = "RC-COMBINE-V2-DOP-VISUAL-REVIEW-VERTICAL-SLICE-001"

    def create_agent_contract(self) -> Dict[str, Any]:
        """Create the DoP agent contract."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_role": "Director of Photography",
            "responsibility_zone": "Cinematography and visual quality review",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "role_definition": {
                "primary_focus": "Visual composition, framing, lighting, and cinematic quality",
                "review_scope": [
                    "composition_balance",
                    "framing_composition",
                    "camera_angle",
                    "lighting_direction",
                    "subject_readability",
                    "shot_mood",
                    "visual_focus",
                    "cinematic_suitability"
                ],
                "decision_authority": "Recommendatory only - cannot accept to production"
            },
            "allowed_inputs": {
                "candidate_image_path": "Path to existing visual candidate",
                "candidate_prompt_id": "Generation prompt identifier",
                "previous_agent_verdict": "Camera operator visual verdict"
            },
            "required_artifacts": [
                "dop_agent_contract.json",
                "dop_visual_review_authorization.json",
                "dop_visual_review_report.json",
                "dop_visual_verdict.json"
            ],
            "forbidden_actions": {
                "new_generation": False,
                "retry_generation": False,
                "second_candidate": False,
                "comfyui_submit": False,
                "image_editing": False,
                "visual_qa_final_acceptance": False,
                "operator_acceptance_by_agent": False,
                "assembly": False,
                "preview_render": False,
                "voice_generation": False,
                "audio_generation": False,
                "downstream_processing": False,
                "production_acceptance": False
            },
            "decision_outputs": {
                "verdict_types": [
                    "ACCEPTED_FOR_NEXT_GATE",
                    "REJECTED_NEEDS_CORRECTIVE_PLAN",
                    "MANUAL_REVIEW_REQUIRED"
                ],
                "verdict_authority": "Recommendation to next gate or corrective planning",
                "production_acceptance_forbidden": True
            }
        }

    def create_review_authorization(self, candidate_path: str, prompt_id: str) -> Dict[str, Any]:
        """Create the DoP visual review authorization artifact."""
        return {
            "task_id": self.task_id,
            "authorization_type": "dop_visual_review_authorization",
            "source_state": "next_visual_gate_authorization_required",
            "authorized_action": "visual_review_only",
            "candidate_image_path": candidate_path,
            "candidate_prompt_id": prompt_id,
            "generation_authorized": False,
            "retry_authorized": False,
            "second_generation_authorized": False,
            "downstream_authorized": False,
            "production_acceptance_authorized": False,
            "review_scope": {
                "composition": True,
                "framing": True,
                "lighting": True,
                "cinematic_quality": True,
                "subject_readability": True
            },
            "constraints": {
                "no_modification_of_candidate": True,
                "no_new_generation": True,
                "no_retry": True,
                "no_downstream": True
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0"
        }

    def save_contract(self, output_dir: str) -> Path:
        """Save the agent contract to disk."""
        output_path = Path(output_dir) / "dop_agent_contract.json"
        contract = self.create_agent_contract()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(contract, f, indent=2, ensure_ascii=False)
        return output_path

    def save_authorization(self, output_dir: str, candidate_path: str, prompt_id: str) -> Path:
        """Save the review authorization to disk."""
        output_path = Path(output_dir) / "dop_visual_review_authorization.json"
        auth = self.create_review_authorization(candidate_path, prompt_id)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(auth, f, indent=2, ensure_ascii=False)
        return output_path
