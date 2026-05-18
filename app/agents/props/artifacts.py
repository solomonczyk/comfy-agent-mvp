"""Props Agent Artifacts.

Manages creation and storage of agent artifacts.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class PropsArtifacts:
    """Manages props agent artifacts."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.props_dir = self.control_dir / "props_agent"
        self.props_dir.mkdir(parents=True, exist_ok=True)
    
    def create_review_report(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """Create the review report artifact."""
        report = {
            "task_id": "RC-COMBINE-V2-PROPS-VERTICAL-SLICE-001",
            "review_report": review,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        report_path = self.props_dir / "props_review_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def create_verdict(self, verdict: str, review: Dict[str, Any]) -> Dict[str, Any]:
        """Create the verdict artifact."""
        verdict_data = {
            "task_id": "RC-COMBINE-V2-PROPS-VERTICAL-SLICE-001",
            "props_verdict": verdict,
            "candidate_path": review["candidate_path"],
            "candidate_sha256": review["candidate_sha256"],
            "defects_found": review["defects_found"],
            "production_accepted": False,
            "next_state": self._get_next_state(verdict),
            "next_allowed_action": self._get_next_action(verdict),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        verdict_path = self.props_dir / "props_verdict.json"
        with open(verdict_path, 'w') as f:
            json.dump(verdict_data, f, indent=2)
        
        return verdict_data
    
    def create_corrective_plan(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """Create corrective plan if rejected."""
        plan = {
            "task_id": "RC-COMBINE-V2-PROPS-VERTICAL-SLICE-001",
            "corrective_plan_required": True,
            "defects_to_address": review["defects_found"],
            "corrective_actions": [
                f"Address {defect['component']}: {defect['issue']}" 
                for defect in review["defects_found"]
            ],
            "target_state": "visual_corrective_plan_required",
            "target_action": "visual_corrective_plan_required",
            "production_accepted": False,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        plan_path = self.props_dir / "props_corrective_plan.json"
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        return plan
    
    def _get_next_state(self, verdict: str) -> str:
        """Get next state based on verdict."""
        if verdict == "ACCEPTED":
            return "costume_review_required"
        elif verdict == "REJECTED":
            return "visual_corrective_plan_required"
        else:
            return "manual_visual_review_required"
    
    def _get_next_action(self, verdict: str) -> str:
        """Get next allowed action based on verdict."""
        if verdict == "ACCEPTED":
            return "costume_review_required"
        elif verdict == "REJECTED":
            return "visual_corrective_plan_required"
        else:
            return "manual_visual_review_required"
