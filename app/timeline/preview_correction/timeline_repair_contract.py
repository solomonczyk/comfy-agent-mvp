"""
Timeline Repair Contract

Defines the repair scope and requirements for fixing timeline issues
that caused the preview to fail.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class TimelineRepairContract:
    """Builds timeline repair contracts for preview correction."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_path = self.project_root / "output" / "control"
    
    def build_timeline_repair_contract(self, root_causes: List[str]) -> Dict[str, Any]:
        """Build the timeline repair contract based on root causes."""
        
        repair_scope = [
            "asset_placement",
            "segment_progression",
            "motion/keyframe_planning",
            "contact_sheet_proof_sampling",
            "static/duplicate_guard"
        ]
        
        # If no frames exist, add frame generation to scope
        if "no_frames_in_preview" in root_causes:
            repair_scope.append("frame_generation")
        
        # If duplicate frames detected, add deduplication
        if "high_duplicate_frame_ratio" in root_causes:
            repair_scope.append("frame_deduplication")
        
        contract = {
            "report_id": "preview_timeline_repair_contract",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-STANDARDS-DRIVEN-PLAN-001",
            "role": "preview_correction_planner",
            "timestamp": datetime.utcnow().isoformat() + "+00:00",
            
            "timeline_repair_required": True,
            "repair_scope": repair_scope,
            "root_causes_addressed": root_causes,
            
            "dry_run_required_before_rerender": True,
            "rerender_requires_explicit_operator_authorization": True,
            
            "repair_requirements": {
                "asset_placement": {
                    "description": "Ensure assets are properly placed across timeline segments",
                    "minimum_unique_assets": 3,
                    "single_source_fallback_allowed": False
                },
                "segment_progression": {
                    "description": "Ensure visible progression across timeline segments",
                    "minimum_segments": 5,
                    "progression_must_be_visible": True
                },
                "motion/keyframe_planning": {
                    "description": "Plan motion transforms and keyframes",
                    "motion_required": True,
                    "keyframes_required": True,
                    "allowed_motion_types": [
                        "slow_push_in",
                        "slow_pull_out",
                        "pan_left",
                        "pan_right",
                        "pan_up",
                        "pan_down"
                    ]
                },
                "contact_sheet_proof_sampling": {
                    "description": "Ensure contact sheet samples prove progression",
                    "sample_points_required": [
                        "scene_start",
                        "early",
                        "middle",
                        "late",
                        "scene_end"
                    ],
                    "duplicate_samples_must_block": True
                },
                "static/duplicate_guard": {
                    "description": "Prevent static or duplicate frames from passing",
                    "duplicate_frame_ratio_max": 0.5,
                    "static_segment_without_motion_allowed": False
                }
            },
            
            "validation_criteria": {
                "dry_run_must_pass": True,
                "contact_sheet_must_show_progression": True,
                "no_duplicate_static_frames": True,
                "operator_review_required": True
            },
            
            "traceable": True
        }
        
        return contract
