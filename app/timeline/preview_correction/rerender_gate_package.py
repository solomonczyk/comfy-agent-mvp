"""
Rerender Gate Package

Prepares the controlled preview rerender authorization gate package.
This does NOT authorize or execute the rerender - only prepares the package.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class RerenderGatePackage:
    """Builds rerender gate packages for preview correction."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_path = self.project_root / "output" / "control"
    
    def build_controlled_preview_rerender_gate_package(self) -> Dict[str, Any]:
        """Build the controlled preview rerender gate package."""
        
        package = {
            "report_id": "controlled_preview_rerender_gate_package",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-STANDARDS-DRIVEN-PLAN-001",
            "role": "preview_correction_planner",
            "timestamp": datetime.utcnow().isoformat() + "+00:00",
            
            "preview_rerender_authorization_required": True,
            "preview_rerender_authorized_now": False,
            "max_preview_renders": 1,
            
            "generation_allowed": False,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted_allowed": False,
            
            "stop_after_preview_rerender": True,
            "next_expected_task": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-STANDARDS-DRIVEN-001",
            
            "authorization_requirements": {
                "description": "Requirements for authorizing the preview rerender",
                "operator_review_required": True,
                "correction_plan_review_required": True,
                "timeline_repair_contract_review_required": True,
                "asset_diversity_plan_review_required": True,
                "motion_progression_contract_review_required": True,
                "contact_sheet_strategy_review_required": True
            },
            
            "pre_rerender_checklist": {
                "description": "Checks that must pass before rerender authorization",
                "correction_plan_exists": True,
                "timeline_repair_contract_exists": True,
                "asset_diversity_plan_exists": True,
                "motion_progression_contract_exists": True,
                "contact_sheet_strategy_exists": True,
                "static_duplicate_prevention_policy_exists": True,
                "operator_review_packet_exists": True
            },
            
            "post_rerender_expectations": {
                "description": "What is expected after the rerender",
                "contact_sheet_must_show_progression": True,
                "duplicate_frame_ratio_below_threshold": True,
                "motion_visible_in_contact_sheet": True,
                "minimum_unique_visual_sources_met": True,
                "operator_review_required": True
            },
            
            "blocking_conditions": {
                "description": "Conditions that will block the rerender",
                "correction_plan_not_reviewed": "block_rerender",
                "timeline_repair_not_approved": "block_rerender",
                "operator_authorization_missing": "block_rerender",
                "pre_rerender_checklist_failed": "block_rerender"
            },
            
            "forbidden_actions": {
                "preview_render_executed_in_this_task": False,
                "voice_generation_allowed": False,
                "assembly_allowed": False,
                "production_accepted": False,
                "generation_performed": False,
                "comfyui_submit_executed": False,
                "retry_attempted": False,
                "final_render_executed": False,
                "visual_qa_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "voice_generation_executed": False,
                "audio_generation_executed": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "hidden_external_llm_api_call": False,
                "hidden_network_or_api_calls_performed": False,
                "hidden_downloads_or_installs_performed": False,
                "fake_operator_decision_created": False,
                "fake_success_created": False
            },
            
            "traceable": True
        }
        
        return package
