"""
Root Cause Analyzer for Preview Correction

Analyzes Script Supervisor blocker and standards integration reports
to identify the root cause of preview failures.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class RootCauseAnalyzer:
    """Analyzes preview failures to determine root causes."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        # Check if project_root contains a data directory with episode structure
        data_path = self.project_root / "data"
        if data_path.exists():
            # Find the episode directory that has the blocker report
            episode_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("rc")]
            if episode_dirs:
                # Look for the episode with script_supervisor_blocker_report.json
                found_episode = None
                for episode_dir in episode_dirs:
                    blocker_path = episode_dir / "output" / "control" / "script_supervisor_blocker_report.json"
                    if blocker_path.exists():
                        found_episode = episode_dir
                        break
                    # Also check for script_supervisor subdirectory
                    blocker_path2 = episode_dir / "output" / "control" / "script_supervisor" / "script_supervisor_blocker_packet.json"
                    if blocker_path2.exists():
                        found_episode = episode_dir
                        break
                
                if found_episode:
                    self.control_path = found_episode / "output" / "control"
                else:
                    # Fallback to first episode
                    self.control_path = episode_dirs[0] / "output" / "control"
            else:
                self.control_path = self.project_root / "output" / "control"
        else:
            self.control_path = self.project_root / "output" / "control"
        self.script_supervisor_path = self.control_path / "script_supervisor"
        self.standards_integration_path = self.control_path / "standards_integration"
    
    def load_script_supervisor_blocker(self) -> Optional[Dict[str, Any]]:
        """Load the Script Supervisor blocker packet."""
        blocker_path = self.script_supervisor_path / "script_supervisor_blocker_packet.json"
        if not blocker_path.exists():
            # Try the control directory directly as fallback
            fallback_path = self.control_path / "script_supervisor_blocker_report.json"
            if fallback_path.exists():
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        
        with open(blocker_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_script_supervisor_preview_audit(self) -> Optional[Dict[str, Any]]:
        """Load the Script Supervisor preview audit report."""
        audit_path = self.script_supervisor_path / "script_supervisor_preview_audit_report.json"
        if not audit_path.exists():
            return None
        
        with open(audit_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_script_supervisor_fake_decision_audit(self) -> Optional[Dict[str, Any]]:
        """Load the Script Supervisor fake decision audit report."""
        audit_path = self.script_supervisor_path / "script_supervisor_fake_decision_audit.json"
        if not audit_path.exists():
            return None
        
        with open(audit_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_standards_integration(self) -> Optional[Dict[str, Any]]:
        """Load the standards integration proof."""
        proof_path = self.standards_integration_path / "standards_integration_proof.json"
        if not proof_path.exists():
            return None
        
        with open(proof_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def classify_preview_failure(self) -> str:
        """Classify the type of preview failure."""
        blocker = self.load_script_supervisor_blocker()
        if not blocker:
            return "unknown_failure"
        
        blocker_type = blocker.get("blocker_type", "unknown")
        return blocker_type
    
    def identify_root_causes(self) -> List[str]:
        """Identify root causes of the preview failure."""
        root_causes = []
        
        blocker = self.load_script_supervisor_blocker()
        if blocker:
            blocker_reasons = blocker.get("blocker_reasons", [])
            root_causes.extend(blocker_reasons)
        
        fake_audit = self.load_script_supervisor_fake_decision_audit()
        if fake_audit and fake_audit.get("fake_operator_decision_detected"):
            root_causes.append("fake_operator_decision_detected")
        
        preview_audit = self.load_script_supervisor_preview_audit()
        if preview_audit:
            total_frames = preview_audit.get("total_frame_count", 0)
            if total_frames == 0:
                root_causes.append("no_frames_in_preview")
            
            duplicate_ratio = preview_audit.get("duplicate_static_ratio", 0.0)
            if duplicate_ratio > 0.5:
                root_causes.append("high_duplicate_frame_ratio")
        
        return root_causes
    
    def build_root_cause_report(self) -> Dict[str, Any]:
        """Build the complete root cause report."""
        blocker = self.load_script_supervisor_blocker()
        preview_audit = self.load_script_supervisor_preview_audit()
        fake_audit = self.load_script_supervisor_fake_decision_audit()
        standards_integration = self.load_standards_integration()
        
        failure_type = self.classify_preview_failure()
        root_causes = self.identify_root_causes()
        
        # Collect standards references
        standards_references = []
        if blocker:
            traceable_finding = blocker.get("traceable_finding", {})
            rule_references = traceable_finding.get("rule_references", [])
            for ref in rule_references:
                standards_references.append({
                    "policy_id": ref.get("policy_id"),
                    "rule_id": ref.get("rule_id")
                })
        
        # Determine if technical preview exists
        technical_preview_exists = preview_audit is not None and preview_audit.get("preview_artifacts_registered", False)
        
        # Determine if fake operator decision was detected
        fake_operator_decision_detected = fake_audit is not None and fake_audit.get("fake_operator_decision_detected", False)
        
        report = {
            "report_id": "preview_root_cause_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-STANDARDS-DRIVEN-PLAN-001",
            "role": "preview_correction_planner",
            "timestamp": datetime.utcnow().isoformat() + "+00:00",
            
            "failure_type": failure_type,
            "fake_operator_decision_detected_or_preserved_as_blocker": fake_operator_decision_detected,
            "technical_preview_exists": technical_preview_exists,
            "technical_preview_not_acceptable": True,
            "operator_review_required": True,
            "production_accepted": False,
            "voice_assembly_downstream_blocked": True,
            
            "root_causes": root_causes,
            "standards_references": standards_references,
            
            "blocker_details": blocker if blocker else None,
            "preview_audit_details": preview_audit if preview_audit else None,
            "fake_decision_audit_details": fake_audit if fake_audit else None,
            
            "standards_integration_loaded": standards_integration is not None,
            "traceable": True
        }
        
        return report
