"""
Motion Progression Contract

Defines deterministic rules for motion progression in the next preview render.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class MotionProgressionContract:
    """Builds motion progression contracts for preview correction."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_path = self.project_root / "output" / "control"
    
    def build_motion_progression_contract(self) -> Dict[str, Any]:
        """Build the motion progression contract."""
        
        contract = {
            "report_id": "preview_motion_progression_contract",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-STANDARDS-DRIVEN-PLAN-001",
            "role": "preview_correction_planner",
            "timestamp": datetime.utcnow().isoformat() + "+00:00",
            
            "motion_progression_required": True,
            "allowed_motion_types": [
                "slow_push_in",
                "slow_pull_out",
                "pan_left",
                "pan_right",
                "pan_up",
                "pan_down"
            ],
            "static_segment_without_motion_allowed": False,
            "keyframes_required": True,
            "motion_must_be_visible_in_contact_sheet": True,
            
            "motion_requirements": {
                "keyframe_planning": {
                    "description": "Keyframes must be planned for each segment",
                    "minimum_keyframes_per_segment": 2,
                    "keyframe_positions": [
                        "segment_start",
                        "segment_end"
                    ]
                },
                "motion_types": {
                    "slow_push_in": {
                        "description": "Slow camera push in towards subject",
                        "duration_range": [2.0, 5.0],
                        "intensity_range": [0.1, 0.3]
                    },
                    "slow_pull_out": {
                        "description": "Slow camera pull out from subject",
                        "duration_range": [2.0, 5.0],
                        "intensity_range": [0.1, 0.3]
                    },
                    "pan_left": {
                        "description": "Slow pan to the left",
                        "duration_range": [3.0, 6.0],
                        "intensity_range": [0.05, 0.15]
                    },
                    "pan_right": {
                        "description": "Slow pan to the right",
                        "duration_range": [3.0, 6.0],
                        "intensity_range": [0.05, 0.15]
                    },
                    "pan_up": {
                        "description": "Slow pan upward",
                        "duration_range": [3.0, 6.0],
                        "intensity_range": [0.05, 0.15]
                    },
                    "pan_down": {
                        "description": "Slow pan downward",
                        "duration_range": [3.0, 6.0],
                        "intensity_range": [0.05, 0.15]
                    }
                },
                "progression_rules": {
                    "description": "Rules for ensuring visible progression",
                    "motion_must_change_between_segments": True,
                    "cumulative_motion_allowed": True,
                    "motion_reset_at_scene_boundary": True
                }
            },
            
            "validation_criteria": {
                "keyframe_count_check": True,
                "motion_type_check": True,
                "progression_visibility_check": True,
                "contact_sheet_motion_check": True
            },
            
            "traceable": True
        }
        
        return contract
