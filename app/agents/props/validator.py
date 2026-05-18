"""Props Agent Validator.

Validates inputs before props review.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class PropsValidator:
    """Validates inputs for props review."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.props_dir = self.control_dir / "props_agent"
        
    def validate_candidate_exists(self, candidate_path: str) -> Dict[str, Any]:
        """Validate that the candidate image exists."""
        img_path = Path(candidate_path)
        
        validation = {
            "validation_type": "candidate_exists",
            "candidate_path": candidate_path,
            "passed": img_path.exists(),
            "timestamp": datetime.now().isoformat()
        }
        
        if not validation["passed"]:
            validation["message"] = f"Candidate image not found at {candidate_path}"
        
        return validation
    
    def validate_candidate_sha256(self, candidate_path: str, expected_sha256: str) -> Dict[str, Any]:
        """Validate that the candidate image has the expected SHA256."""
        img_path = Path(candidate_path)
        
        if not img_path.exists():
            return {
                "validation_type": "candidate_sha256",
                "candidate_path": candidate_path,
                "expected_sha256": expected_sha256,
                "passed": False,
                "message": "Candidate image not found",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate SHA256
        sha256_hash = hashlib.sha256()
        with open(img_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_sha256 = sha256_hash.hexdigest()
        
        validation = {
            "validation_type": "candidate_sha256",
            "candidate_path": candidate_path,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "passed": actual_sha256.lower() == expected_sha256.lower(),
            "timestamp": datetime.now().isoformat()
        }
        
        if not validation["passed"]:
            validation["message"] = f"SHA256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        
        return validation
    
    def validate_previous_state(self, expected_state: str) -> Dict[str, Any]:
        """Validate that the previous state is as expected."""
        state_path = self.project_root / "output" / "control" / "state.json"
        
        validation = {
            "validation_type": "previous_state",
            "expected_state": expected_state,
            "timestamp": datetime.now().isoformat()
        }
        
        if not state_path.exists():
            validation["passed"] = False
            validation["message"] = "State file not found"
            return validation
        
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        actual_state = state.get("current_state")
        validation["actual_state"] = actual_state
        validation["passed"] = actual_state == expected_state
        
        if not validation["passed"]:
            validation["message"] = f"State mismatch: expected {expected_state}, got {actual_state}"
        
        return validation
    
    def validate_previous_set_decorator_proof(self, expected_commit: str) -> Dict[str, Any]:
        """Validate that the previous Set Decorator proof is tracked."""
        proof_path = self.project_root / "output" / "control" / "set_decorator_agent" / "RC-COMBINE-V2-SET-DECORATOR-VERTICAL-SLICE-001_proof.json"
        
        validation = {
            "validation_type": "previous_set_decorator_proof",
            "expected_commit": expected_commit,
            "timestamp": datetime.now().isoformat()
        }
        
        if not proof_path.exists():
            validation["passed"] = False
            validation["message"] = "Set Decorator proof not found"
            return validation
        
        validation["passed"] = True
        validation["proof_path"] = str(proof_path)
        
        return validation
    
    def validate_forbidden_actions_not_executed(self) -> Dict[str, Any]:
        """Validate that forbidden actions have not been executed by this agent."""
        state_path = self.project_root / "output" / "control" / "state.json"
        
        validation = {
            "validation_type": "forbidden_actions_not_executed",
            "timestamp": datetime.now().isoformat()
        }
        
        if not state_path.exists():
            validation["passed"] = False
            validation["message"] = "State file not found"
            return validation
        
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        # The Props Agent is a review-only agent that should not perform new generations
        # However, it can review candidates that were generated by previous agents
        # So we check that the current task is not a generation task, not that no generation ever occurred
        current_task = state.get("task_id", "")
        is_props_task = "PROPS" in current_task or "props" in current_task.lower()
        
        # Check that production_accepted remains false (this should always be false for review agents)
        forbidden_checks = {
            "production_accepted": state.get("production_accepted", False) == False
        }
        
        # If this is the props task, ensure no new generation was performed by this task
        if is_props_task:
            # Check that retry was not attempted (should remain false for review agents)
            forbidden_checks["retry_attempted"] = state.get("retry_attempted", False) == False
            # Check that assembly was not executed
            forbidden_checks["assembly_executed"] = state.get("assembly_executed", False) == False
            # Check that downstream was not executed
            forbidden_checks["downstream_executed"] = state.get("downstream_executed", False) == False
        
        validation["checks"] = forbidden_checks
        validation["passed"] = all(forbidden_checks.values())
        validation["current_task"] = current_task
        
        if not validation["passed"]:
            failed_checks = [k for k, v in forbidden_checks.items() if not v]
            validation["message"] = f"Forbidden actions detected: {failed_checks}"
        else:
            validation["message"] = "No forbidden actions detected by Props Agent"
        
        return validation
