"""
Combine Internal Orchestrator

Thin orchestrator skeleton for the internal multi-agent system.
This orchestrator manages state, routes, and stage execution.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from .contracts import (
    CombineStatus,
    CombineRunContext,
    CombineStageResult,
    StageTransitionRequest,
    StageTransitionResult
)
from .state_machine import CombineStateMachine
from .routing import RouteFamilyRegistry


class CombineOrchestrator:
    """Internal orchestrator for Combine multi-agent system"""
    
    def __init__(self, project_root: str):
        """
        Initialize the orchestrator.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.state_machine = CombineStateMachine()
        self.route_registry = RouteFamilyRegistry()
        
        # Artifact index path
        self.artifact_index_path = self.project_root / "artifact_index.json"
        
        # Ledger path
        self.ledger_path = self.project_root / "ledger.json"
    
    def _read_artifact_index(self) -> Dict[str, Any]:
        """Read artifact index if it exists"""
        if self.artifact_index_path.exists():
            with open(self.artifact_index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _read_ledger(self) -> List[Dict[str, Any]]:
        """Read ledger if it exists"""
        if self.ledger_path.exists():
            with open(self.ledger_path, 'r') as f:
                return json.load(f)
        return []
    
    def _infer_current_state(self) -> str:
        """
        Infer current state from project structure.
        
        This is a safe inference that defaults to brief_intake_required
        if no state information is found.
        """
        artifact_index = self._read_artifact_index()
        ledger = self._read_ledger()
        
        # Check ledger for last state
        if ledger:
            last_event = ledger[-1]
            if "to_state" in last_event:
                return last_event["to_state"]
        
        # Check artifact index for state
        if "current_state" in artifact_index:
            return artifact_index["current_state"]
        
        # Default to initial state
        return "brief_intake_required"
    
    def _get_next_allowed_action(self, current_state: str) -> str:
        """Get next allowed action based on current state"""
        allowed_states = self.state_machine.get_allowed_next_states(current_state)
        if allowed_states:
            return allowed_states[0]
        return "none"
    
    def get_status(self) -> CombineStatus:
        """
        Get current status of the Combine project.
        
        Returns:
            CombineStatus with current project state
        """
        current_state = self._infer_current_state()
        next_allowed_action = self._get_next_allowed_action(current_state)
        
        artifact_index = self._read_artifact_index()
        route_family = artifact_index.get("route_family")
        
        return CombineStatus(
            project_root=str(self.project_root),
            current_state=current_state,
            next_allowed_action=next_allowed_action,
            route_family=route_family,
            artifacts=artifact_index,
            ledger_events=self._read_ledger(),
            windsurf_runtime_dependency=False,
            generation_performed=False,
            comfyui_execution=False,
            combine_v2=True
        )
    
    def _validate_stage_execution(self, stage: str, current_state: str) -> bool:
        """
        Validate if a stage can be executed.
        
        Args:
            stage: Stage to execute
            current_state: Current state
            
        Returns:
            True if stage can be executed, False otherwise
        """
        # Check if stage matches current state
        if stage != current_state:
            # Check if stage is an allowed next state
            allowed_states = self.state_machine.get_allowed_next_states(current_state)
            if stage not in allowed_states:
                return False
        
        return True
    
    def _write_stage_result(self, result: CombineStageResult) -> None:
        """
        Write stage result to artifact index.
        
        Args:
            result: Stage execution result
        """
        artifact_index = self._read_artifact_index()
        
        # Update artifact index with stage result
        if "stage_results" not in artifact_index:
            artifact_index["stage_results"] = []
        
        artifact_index["stage_results"].append({
            "stage": result.stage,
            "success": result.success,
            "message": result.message,
            "artifacts": result.artifacts,
            "metadata": result.metadata,
            "timestamp": result.timestamp,
            "no_generation_performed": result.no_generation_performed
        })
        
        # Write artifact index
        with open(self.artifact_index_path, 'w') as f:
            json.dump(artifact_index, f, indent=2)
    
    def _append_ledger_event(self, event: Dict[str, Any]) -> None:
        """
        Append event to ledger.
        
        Args:
            event: Event to append
        """
        ledger = self._read_ledger()
        ledger.append(event)
        
        with open(self.ledger_path, 'w') as f:
            json.dump(ledger, f, indent=2)
    
    def run_stage(self, stage: str, dry_run: bool = True) -> CombineStageResult:
        """
        Run a stage (stub/dry only).
        
        This method does NOT call ComfyUI.
        This method does NOT call generation service.
        This method does NOT run QA/downstream.
        All stage execution in this layer is stub/dry only.
        
        Args:
            stage: Stage to run
            dry_run: If True, perform dry run only
            
        Returns:
            CombineStageResult with execution result
        """
        current_state = self._infer_current_state()
        
        # Validate stage execution
        if not self._validate_stage_execution(stage, current_state):
            return CombineStageResult(
                stage=stage,
                success=False,
                message=f"Stage {stage} cannot be executed from current state {current_state}",
                no_generation_performed=True
            )
        
        # Stub execution - no actual work performed
        if dry_run:
            result = CombineStageResult(
                stage=stage,
                success=True,
                message=f"Dry run: Stage {stage} validated successfully",
                no_generation_performed=True
            )
        else:
            # Even in non-dry mode, this is still a stub
            # Actual implementation will be added in later phases
            result = CombineStageResult(
                stage=stage,
                success=True,
                message=f"Stub execution: Stage {stage} completed (stub)",
                no_generation_performed=True
            )
        
        # Write stage result
        self._write_stage_result(result)
        
        # Append ledger event
        self._append_ledger_event({
            "event_type": "stage_execution",
            "stage": stage,
            "success": result.success,
            "message": result.message,
            "dry_run": dry_run,
            "timestamp": result.timestamp
        })
        
        return result
