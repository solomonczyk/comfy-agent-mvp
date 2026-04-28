"""Execution plan data structures for the agent system."""

from dataclasses import dataclass, field
from typing import Any

from app.agent.task_selector import TaskSelectionResult
from app.workflows.workflow_types import TaskType


@dataclass
class ExecutionPlan:
    """Execution plan for a generation task."""
    user_prompt: str
    task_type: TaskType
    workflow_id: str
    workflow_path: str
    preset_name: str
    rewrite_mode: str
    required_inputs: list[str]
    resolved_inputs: dict[str, Any]
    enable_judging: bool
    enable_retry_loop: bool
    canonical_recipe: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_prompt": self.user_prompt,
            "task_type": self.task_type.value,
            "workflow_id": self.workflow_id,
            "workflow_path": self.workflow_path,
            "preset_name": self.preset_name,
            "rewrite_mode": self.rewrite_mode,
            "required_inputs": self.required_inputs,
            "resolved_inputs": self.resolved_inputs,
            "enable_judging": self.enable_judging,
            "enable_retry_loop": self.enable_retry_loop,
            "canonical_recipe": self.canonical_recipe,
            "notes": self.notes,
        }


class ExecutionPlanBuilder:
    """Builder for creating execution plans."""

    def __init__(self) -> None:
        """Initialize execution plan builder."""
        self._notes: list[str] = []

    def build(
        self,
        user_prompt: str,
        task_selection: TaskSelectionResult,
        workflow_id: str,
        workflow_path: str,
        preset_name: str,
        rewrite_mode: str,
        required_inputs: list[str],
        resolved_inputs: dict[str, Any] | None = None,
        enable_judging: bool = True,
        enable_retry_loop: bool = True,
        canonical_recipe: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        """Build an execution plan from components."""
        # Validate required inputs are present
        self._validate_required_inputs(required_inputs, resolved_inputs, task_selection.task_type)
        
        plan = ExecutionPlan(
            user_prompt=user_prompt,
            task_type=task_selection.task_type,
            workflow_id=workflow_id,
            workflow_path=workflow_path,
            preset_name=preset_name,
            rewrite_mode=rewrite_mode,
            required_inputs=required_inputs,
            resolved_inputs=resolved_inputs,
            enable_judging=enable_judging,
            enable_retry_loop=enable_retry_loop,
            canonical_recipe=canonical_recipe,
            notes=self._notes.copy(),
        )
        self._notes.clear()
        return plan

    def _validate_required_inputs(
        self,
        required_inputs: list[str],
        resolved_inputs: dict[str, Any],
        task_type: TaskType,
    ) -> None:
        """Validate that required inputs are present in resolved_inputs.
        
        Args:
            required_inputs: List of required input keys
            resolved_inputs: Dictionary of resolved input values
            task_type: Task type for context
            
        Raises:
            ValueError: If required asset inputs are missing
        """
        # Asset-aware required inputs
        asset_inputs = {
            "image": "input image",
            "mask": "mask image",
            "input_image": "input image",
            "mask_image": "mask image",
        }
        
        missing_assets = []
        for required in required_inputs:
            if required in asset_inputs and (resolved_inputs.get(required) is None):
                missing_assets.append(f"{asset_inputs[required]} ({required})")
        
        if missing_assets:
            error_msg = f"Missing required assets for {task_type.value}: {', '.join(missing_assets)}"
            raise ValueError(error_msg)

    def add_note(self, note: str) -> None:
        """Add a note to the plan."""
        self._notes.append(note)
