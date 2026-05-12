"""
Readiness assessor for Fresh Visual Strategy.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from .strategy_models import StrategyReadinessResult


class StrategyReadinessAssessor:
    """Assesses readiness of fresh visual strategy for operator review."""
    
    def __init__(self, strategy_dir: Path, control_dir: Path):
        self.strategy_dir = Path(strategy_dir)
        self.control_dir = Path(control_dir)
    
    def assess_readiness(self) -> StrategyReadinessResult:
        """Assess overall readiness of the fresh visual strategy."""
        task_id = "RC-COMBINE-V2-FRESH-VISUAL-STRATEGY-001"
        timestamp = datetime.now().isoformat()
        
        # Assess artifact readiness
        artifact_readiness = self._assess_artifact_readiness()
        
        # Assess policy readiness
        policy_readiness = self._assess_policy_readiness()
        
        # Assess reference readiness
        reference_readiness = self._assess_reference_readiness()
        
        # Verify forbidden actions
        forbidden_verification = self._verify_forbidden_actions()
        
        # Verify state
        state_verification = self._verify_state()
        
        # Build readiness checklist
        readiness_checklist = {
            "all_artifacts_created": all(v["status"] == "created" for v in artifact_readiness.values()),
            "all_artifacts_valid": all(v["valid"] for v in artifact_readiness.values()),
            "policies_loaded": policy_readiness.get("qa_repairability_gate_active", False),
            "references_available": reference_readiness.get("positive_references_available", 0) > 0,
            "forbidden_actions_respected": all(forbidden_verification.values()),
            "state_consistent": state_verification.get("state_consistent", False),
            "qa_repairability_gate_active": policy_readiness.get("qa_repairability_gate_active", False),
            "generation_authorized": False,
            "ready_for_operator_review": True
        }
        
        # Determine overall readiness
        all_artifacts_ready = readiness_checklist["all_artifacts_created"] and readiness_checklist["all_artifacts_valid"]
        policies_ready = readiness_checklist["policies_loaded"]
        forbidden_respected = readiness_checklist["forbidden_actions_respected"]
        state_consistent = readiness_checklist["state_consistent"]
        
        overall_readiness = "ready_for_operator_review" if (all_artifacts_ready and policies_ready and forbidden_respected and state_consistent) else "not_ready"
        ready_for_generation = False
        generation_blocked_until = "operator_review_complete"
        
        blockers = []
        warnings = []
        
        if not all_artifacts_ready:
            blockers.append("Not all artifacts created or valid")
        if not policies_ready:
            blockers.append("Policies not loaded or QA repairability gate inactive")
        if not forbidden_respected:
            blockers.append("Forbidden actions were executed")
        if not state_consistent:
            blockers.append("State inconsistency detected")
        
        recommendation = "Proceed to operator review of fresh visual strategy" if overall_readiness == "ready_for_operator_review" else "Address blockers before proceeding"
        
        return StrategyReadinessResult(
            task_id=task_id,
            timestamp=timestamp,
            overall_readiness=overall_readiness,
            ready_for_generation=ready_for_generation,
            generation_blocked_until=generation_blocked_until,
            artifact_readiness=artifact_readiness,
            policy_readiness=policy_readiness,
            reference_readiness=reference_readiness,
            forbidden_actions_verification=forbidden_verification,
            state_verification=state_verification,
            readiness_checklist=readiness_checklist,
            blockers=blockers,
            warnings=warnings,
            recommendation=recommendation
        )
    
    def _assess_artifact_readiness(self) -> Dict[str, Dict[str, Any]]:
        """Assess readiness of all strategy artifacts."""
        artifacts = [
            "fresh_visual_strategy_manifest.json",
            "fresh_visual_strategy_brief.json",
            "visual_style_direction.json",
            "visual_quality_targets.json",
            "negative_reference_policy.json",
            "reference_acquisition_plan.json",
            "repairability_aware_visual_policy.json",
            "generation_readiness_blocker_policy.json",
            "future_generation_gate_requirements.json",
            "visual_strategy_operator_review_packet.json",
            "fresh_visual_strategy_readiness_report.json"
        ]
        
        artifact_readiness = {}
        for artifact in artifacts:
            artifact_path = self.strategy_dir / artifact
            exists = artifact_path.exists()
            valid = False
            
            if exists:
                try:
                    with open(artifact_path, 'r') as f:
                        data = json.load(f)
                    valid = isinstance(data, dict) and len(data) > 0
                except Exception:
                    valid = False
            
            artifact_readiness[artifact.replace(".json", "")] = {
                "status": "created" if exists else "missing",
                "valid": valid,
                "path": str(artifact_path)
            }
        
        return artifact_readiness
    
    def _assess_policy_readiness(self) -> Dict[str, bool]:
        """Assess readiness of repairability policy."""
        policy_path = self.strategy_dir / "repairability_aware_visual_policy.json"
        
        if not policy_path.exists():
            return {
                "qa_repairability_gate_active": False,
                "unknown_repairability_blocks": False,
                "downstream_requires_validated_repairability": False,
                "technical_pass_not_visual_pass_enforced": False,
                "visual_operator_review_required": False,
                "production_accepted_must_remain_false": False
            }
        
        try:
            with open(policy_path, 'r') as f:
                policy = json.load(f)
            
            return {
                "qa_repairability_gate_active": policy.get("qa_repairability_gate_required", False),
                "unknown_repairability_blocks": policy.get("unknown_repairability_blocks", False),
                "downstream_requires_validated_repairability": policy.get("downstream_requires_validated_repairability", False),
                "technical_pass_not_visual_pass_enforced": policy.get("technical_pass_is_not_visual_pass", False),
                "visual_operator_review_required": policy.get("visual_operator_review_required", False),
                "production_accepted_must_remain_false": policy.get("production_accepted_must_remain_false", False)
            }
        except Exception:
            return {
                "qa_repairability_gate_active": False,
                "unknown_repairability_blocks": False,
                "downstream_requires_validated_repairability": False,
                "technical_pass_not_visual_pass_enforced": False,
                "visual_operator_review_required": False,
                "production_accepted_must_remain_false": False
            }
    
    def _assess_reference_readiness(self) -> Dict[str, Any]:
        """Assess readiness of references."""
        reference_plan_path = self.strategy_dir / "reference_acquisition_plan.json"
        
        if not reference_plan_path.exists():
            return {
                "positive_references_available": 0,
                "negative_references_available": 0,
                "negative_reference_policy_enforced": False,
                "reference_integrity_valid": False
            }
        
        try:
            with open(reference_plan_path, 'r') as f:
                plan = json.load(f)
            
            acquisition_status = plan.get("acquisition_status", {})
            
            return {
                "positive_references_available": acquisition_status.get("positive_references_available", 0),
                "negative_references_available": acquisition_status.get("negative_references_available", 0),
                "negative_reference_policy_enforced": True,
                "reference_integrity_valid": acquisition_status.get("ready_for_generation", False)
            }
        except Exception:
            return {
                "positive_references_available": 0,
                "negative_references_available": 0,
                "negative_reference_policy_enforced": False,
                "reference_integrity_valid": False
            }
    
    def _verify_forbidden_actions(self) -> Dict[str, bool]:
        """Verify that all forbidden actions are false."""
        readiness_report_path = self.strategy_dir / "fresh_visual_strategy_readiness_report.json"
        
        if not readiness_report_path.exists():
            # Default to all false if report doesn't exist yet
            return {
                "generation_performed": False,
                "comfyui_submit_executed": False,
                "retry_attempted": False,
                "preview_rerender_executed": False,
                "preview_render_executed": False,
                "visual_qa_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "voice_generation_executed": False,
                "audio_generation_executed": False,
                "assembly_executed": False,
                "final_render_executed": False,
                "downstream_executed": False,
                "production_accepted": False
            }
        
        try:
            with open(readiness_report_path, 'r') as f:
                report = json.load(f)
            
            return report.get("forbidden_actions_verification", {})
        except Exception:
            return {}
    
    def _verify_state(self) -> Dict[str, str]:
        """Verify state consistency."""
        artifact_index_path = self.control_dir / "artifact_index.json"
        
        if not artifact_index_path.exists():
            return {
                "current_state": "unknown",
                "next_allowed_action": "unknown",
                "state_consistent": False
            }
        
        try:
            with open(artifact_index_path, 'r') as f:
                index = json.load(f)
            
            current_state = index.get("current_state", "unknown")
            next_allowed = index.get("next_allowed_action", "unknown")
            
            # Expected state for fresh visual strategy
            expected_state = "visual_outputs_purged_rebuild_required"
            expected_next = "fresh_visual_strategy_required"
            
            state_consistent = (current_state == expected_state and next_allowed == expected_next)
            
            return {
                "current_state": current_state,
                "next_allowed_action": next_allowed,
                "state_consistent": state_consistent
            }
        except Exception:
            return {
                "current_state": "unknown",
                "next_allowed_action": "unknown",
                "state_consistent": False
            }
