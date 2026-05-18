"""Production Designer Agent Runner.

Orchestrates the production design review process.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.agents.production_designer.contract import ProductionDesignerAgentContract
from app.agents.production_designer.validator import ProductionDesignerValidator
from app.agents.production_designer.reviewer import ProductionDesignerReviewer
from app.agents.production_designer.artifacts import ProductionDesignerArtifacts


class ProductionDesignerRunner:
    """Runs the production design review process."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.contract = ProductionDesignerAgentContract(project_root)
        self.validator = ProductionDesignerValidator(project_root)
        self.reviewer = ProductionDesignerReviewer(project_root)
        self.artifacts = ProductionDesignerArtifacts(project_root)
        
    def run_vertical_slice(self, candidate_path: str) -> Dict[str, Any]:
        """Run the full production designer vertical slice."""
        results = {
            "task_id": "RC-COMBINE-V2-PRODUCTION-DESIGNER-VERTICAL-SLICE-001",
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Create contract
        results["steps"].append({"step": "create_contract", "status": "in_progress"})
        contract = self.contract.create_contract()
        results["steps"].append({"step": "create_contract", "status": "completed"})
        
        # Step 2: Create review authorization
        results["steps"].append({"step": "create_review_authorization", "status": "in_progress"})
        authorization = self.contract.create_review_authorization()
        results["steps"].append({"step": "create_review_authorization", "status": "completed"})
        
        # Step 3: Validate inputs
        results["steps"].append({"step": "validate_inputs", "status": "in_progress"})
        validations = self._run_validations(candidate_path)
        results["steps"].append({
            "step": "validate_inputs", 
            "status": "completed",
            "validations": validations
        })
        
        # Check if all validations passed
        all_valid_passed = all(v["passed"] for v in validations.values())
        if not all_valid_passed:
            results["status"] = "failed_validation"
            results["message"] = "Validation failed - cannot proceed with review"
            return results
        
        # Step 4: Review candidate
        results["steps"].append({"step": "review_candidate", "status": "in_progress"})
        review = self.reviewer.review_candidate(candidate_path)
        results["steps"].append({
            "step": "review_candidate",
            "status": "completed",
            "review_summary": {
                "verdict": review["overall_verdict"],
                "defects_count": len(review["defects_found"])
            }
        })
        
        # Step 5: Create review report
        results["steps"].append({"step": "create_review_report", "status": "in_progress"})
        report = self.artifacts.create_review_report(review)
        results["steps"].append({"step": "create_review_report", "status": "completed"})
        
        # Step 6: Create verdict
        results["steps"].append({"step": "create_verdict", "status": "in_progress"})
        verdict_data = self.artifacts.create_verdict(review["overall_verdict"], review)
        results["steps"].append({
            "step": "create_verdict",
            "status": "completed",
            "verdict": review["overall_verdict"]
        })
        
        # Step 7: Create corrective plan if rejected
        if review["overall_verdict"] == "REJECTED":
            results["steps"].append({"step": "create_corrective_plan", "status": "in_progress"})
            corrective_plan = self.artifacts.create_corrective_plan(review)
            results["steps"].append({
                "step": "create_corrective_plan",
                "status": "completed"
            })
        
        # Step 8: Update state
        results["steps"].append({"step": "update_state", "status": "in_progress"})
        state_update = self._update_state(review["overall_verdict"])
        results["steps"].append({
            "step": "update_state",
            "status": "completed",
            "new_state": state_update
        })
        
        # Step 9: Update artifact index
        results["steps"].append({"step": "update_artifact_index", "status": "in_progress"})
        artifact_index_update = self._update_artifact_index(review["overall_verdict"])
        results["steps"].append({
            "step": "update_artifact_index",
            "status": "completed"
        })
        
        # Step 10: Update episode ledger
        results["steps"].append({"step": "update_episode_ledger", "status": "in_progress"})
        episode_ledger_update = self._update_episode_ledger(review["overall_verdict"])
        results["steps"].append({
            "step": "update_episode_ledger",
            "status": "completed"
        })
        
        results["status"] = "completed"
        results["final_verdict"] = review["overall_verdict"]
        results["next_state"] = verdict_data["next_state"]
        results["next_allowed_action"] = verdict_data["next_allowed_action"]
        
        return results
    
    def _run_validations(self, candidate_path: str) -> Dict[str, Any]:
        """Run all validations."""
        validations = {}
        
        validations["candidate_exists"] = self.validator.validate_candidate_exists(candidate_path)
        validations["candidate_sha256"] = self.validator.validate_candidate_sha256(
            candidate_path, 
            "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b"
        )
        validations["previous_state"] = self.validator.validate_previous_state("production_design_review_required")
        validations["previous_colorist_proof"] = self.validator.validate_previous_colorist_proof("79c429f")
        validations["forbidden_actions"] = self.validator.validate_forbidden_actions_not_executed()
        
        return validations
    
    def _update_state(self, verdict: str) -> Dict[str, Any]:
        """Update the state file."""
        state_path = self.project_root / "output" / "control" / "state.json"
        
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        # Update state based on verdict
        if verdict == "ACCEPTED":
            state["current_state"] = "set_decorator_review_required"
            state["next_allowed_action"] = "set_decorator_review_required"
        elif verdict == "REJECTED":
            state["current_state"] = "visual_corrective_plan_required"
            state["next_allowed_action"] = "visual_corrective_plan_required"
        else:
            state["current_state"] = "manual_visual_review_required"
            state["next_allowed_action"] = "manual_visual_review_required"
        
        state["production_accepted"] = False
        state["task_id"] = "RC-COMBINE-V2-PRODUCTION-DESIGNER-VERTICAL-SLICE-001"
        state["timestamp"] = datetime.now().isoformat()
        
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "current_state": state["current_state"],
            "next_allowed_action": state["next_allowed_action"]
        }
    
    def _update_artifact_index(self, verdict: str) -> Dict[str, Any]:
        """Update the artifact index."""
        artifact_index_path = self.project_root / "output" / "control" / "artifact_index.json"
        
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        artifact_index["current_state"] = artifact_index.get("current_state")
        artifact_index["next_allowed_action"] = artifact_index.get("next_allowed_action")
        artifact_index["production_design_review_executed"] = True
        artifact_index["production_design_verdict"] = verdict
        artifact_index["production_design_contract_created"] = True
        artifact_index["production_design_review_authorization_created"] = True
        artifact_index["production_design_review_report_created"] = True
        artifact_index["production_design_verdict_created"] = True
        
        if verdict == "REJECTED":
            artifact_index["production_design_corrective_plan_created"] = True
        
        with open(artifact_index_path, 'w') as f:
            json.dump(artifact_index, f, indent=2)
        
        return {"artifact_index_updated": True}
    
    def _update_episode_ledger(self, verdict: str) -> Dict[str, Any]:
        """Update the episode ledger."""
        episode_ledger_path = self.project_root / "output" / "control" / "episode_ledger.json"
        
        with open(episode_ledger_path, 'r') as f:
            episode_ledger = json.load(f)
        
        # Determine next state/action
        if verdict == "ACCEPTED":
            next_state = "set_decorator_review_required"
            next_action = "set_decorator_review_required"
        elif verdict == "REJECTED":
            next_state = "visual_corrective_plan_required"
            next_action = "visual_corrective_plan_required"
        else:
            next_state = "manual_visual_review_required"
            next_action = "manual_visual_review_required"
        
        # Add new event
        new_event = {
            "event_type": "production_design_review",
            "task_id": "RC-COMBINE-V2-PRODUCTION-DESIGNER-VERTICAL-SLICE-001",
            "stage": "production_design_review",
            "previous_task": "RC-COMBINE-V2-COLORIST-VERTICAL-SLICE-001",
            "previous_commit": "79c429f",
            "generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "image_editing_executed": False,
            "render_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "production_design_verdict": verdict,
            "current_state": next_state,
            "next_allowed_action": next_action,
            "timestamp": datetime.now().isoformat()
        }
        
        episode_ledger.append(new_event)
        
        with open(episode_ledger_path, 'w') as f:
            json.dump(episode_ledger, f, indent=2)
        
        return {"episode_ledger_updated": True}
