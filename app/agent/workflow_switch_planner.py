"""Workflow switch planner for building switched execution plans.

This module provides the planner layer for building execution plans for
target workflows when a switch is approved by the policy.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelectionResult
from app.agent.workflow_switch_policy import WorkflowSwitchDecision
from app.workflows.workflow_types import TaskType


# Mapping from workflow IDs to task types
WORKFLOW_TO_TASK_TYPE = {
    "img2img_v1": TaskType.IMG2IMG,
    "inpaint_face_v1": TaskType.INPAINT_FACE,
    "upscale_v1": TaskType.UPSCALE,
    "txt2img_portrait": TaskType.PORTRAIT_TXT2IMG,
    "txt2img_cinematic": TaskType.CINEMATIC_TXT2IMG,
    "txt2img_product": TaskType.PRODUCT_TXT2IMG,
    "txt2img_fashion": TaskType.FASHION_TXT2IMG,
}


@dataclass
class WorkflowSwitchPlan:
    """Plan for switching to a target workflow.
    
    This dataclass represents the plan for executing a workflow switch,
    including the target workflow, task type, and validation status.
    """
    switch_applied: bool
    from_workflow_id: str | None
    to_workflow_id: str | None
    target_task_type: str | None
    switch_reason: str
    source_trigger: str | None
    required_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    switched_execution_plan: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "switch_applied": self.switch_applied,
            "from_workflow_id": self.from_workflow_id,
            "to_workflow_id": self.to_workflow_id,
            "target_task_type": self.target_task_type,
            "switch_reason": self.switch_reason,
            "source_trigger": self.source_trigger,
            "required_inputs": self.required_inputs,
            "missing_inputs": self.missing_inputs,
            "notes": self.notes,
            "switched_execution_plan": self.switched_execution_plan,
        }


class WorkflowSwitchPlanner:
    """Planner for building switched execution plans."""
    
    def __init__(self, workflows_dir: str | Path) -> None:
        """Initialize workflow switch planner.
        
        Args:
            workflows_dir: Directory containing workflow templates
        """
        self.workflows_dir = Path(workflows_dir)
        self.plan_builder = ExecutionPlanBuilder()
    
    def build_switch_plan(
        self,
        current_execution_plan: ExecutionPlan,
        switch_decision: WorkflowSwitchDecision,
        task_selection: TaskSelectionResult,
        assets: dict[str, Any] | None,
        registry: Any,  # WorkflowRegistry
    ) -> WorkflowSwitchPlan:
        """Build a plan for switching to a target workflow.
        
        Args:
            current_execution_plan: Current execution plan
            switch_decision: Switch decision from policy
            task_selection: Original task selection result
            assets: Available assets
            registry: Workflow registry for getting workflow specs
            
        Returns:
            WorkflowSwitchPlan with target workflow details
        """
        if switch_decision.action != "switch_workflow":
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=None,
                target_task_type=None,
                switch_reason=switch_decision.switch_reason or "No switch requested",
                source_trigger=switch_decision.source_trigger,
                notes=["Switch not requested by policy"],
            )
        
        target_workflow_id = switch_decision.to_workflow_id
        if not target_workflow_id:
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=None,
                target_task_type=None,
                switch_reason="No target workflow specified",
                source_trigger=switch_decision.source_trigger,
                notes=["Switch decision missing target workflow"],
            )
        
        # Get target workflow spec
        workflow_spec = registry.get_by_id(target_workflow_id)
        if not workflow_spec:
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=target_workflow_id,
                target_task_type=None,
                switch_reason=f"Target workflow not found: {target_workflow_id}",
                source_trigger=switch_decision.source_trigger,
                notes=["Target workflow not in registry"],
            )
        
        if not workflow_spec.implemented:
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=target_workflow_id,
                target_task_type=None,
                switch_reason=f"Target workflow not implemented: {target_workflow_id}",
                source_trigger=switch_decision.source_trigger,
                notes=["Target workflow marked as not implemented"],
            )
        
        # Determine target task type
        target_task_type = WORKFLOW_TO_TASK_TYPE.get(target_workflow_id)
        if not target_task_type:
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=target_workflow_id,
                target_task_type=None,
                switch_reason=f"Unknown target workflow: {target_workflow_id}",
                source_trigger=switch_decision.source_trigger,
                notes=["Target workflow not in task type mapping"],
            )
        
        # Build switched execution plan
        try:
            switched_execution_plan = self._build_switched_execution_plan(
                current_plan=current_execution_plan,
                target_workflow_spec=workflow_spec,
                target_task_type=target_task_type,
                assets=assets,
            )
            
            return WorkflowSwitchPlan(
                switch_applied=True,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=target_workflow_id,
                target_task_type=target_task_type.value,
                switch_reason=switch_decision.switch_reason,
                source_trigger=switch_decision.source_trigger,
                required_inputs=workflow_spec.required_inputs,
                missing_inputs=switch_decision.missing_inputs,
                notes=["Switch plan built successfully"],
                switched_execution_plan=switched_execution_plan.to_dict(),
            )
        except Exception as e:
            return WorkflowSwitchPlan(
                switch_applied=False,
                from_workflow_id=current_execution_plan.workflow_id,
                to_workflow_id=target_workflow_id,
                target_task_type=target_task_type.value,
                switch_reason=f"Failed to build switched plan: {str(e)}",
                source_trigger=switch_decision.source_trigger,
                required_inputs=workflow_spec.required_inputs,
                missing_inputs=switch_decision.missing_inputs,
                notes=[f"Error building switched plan: {str(e)}"],
            )
    
    def _build_switched_execution_plan(
        self,
        current_plan: ExecutionPlan,
        target_workflow_spec: Any,
        target_task_type: TaskType,
        assets: dict[str, Any] | None,
    ) -> ExecutionPlan:
        """Build execution plan for target workflow.
        
        Args:
            current_plan: Current execution plan
            target_workflow_spec: Target workflow specification
            target_task_type: Target task type
            assets: Available assets
            
        Returns:
            Execution plan for target workflow
        """
        # Preserve original user prompt
        user_prompt = current_plan.user_prompt
        
        # Build resolved inputs, preserving current inputs and adding assets
        resolved_inputs = dict(current_plan.resolved_inputs) if current_plan.resolved_inputs else {}
        resolved_inputs["prompt"] = user_prompt
        
        # Add assets if present
        if assets:
            for key, value in assets.items():
                if value is not None:
                    resolved_inputs[key] = value
        
        # Build new task selection (preserve original but update task type)
        # Note: We're not re-running task selection, just updating the task type
        # This is a controlled switch, not a full re-routing
        from app.agent.task_selector import TaskSelectionResult
        
        switched_task_selection = TaskSelectionResult(
            task_type=target_task_type,
            confidence=0.8,  # Switch confidence
            reason=f"Switched from {current_plan.workflow_id}",
            routing_source="rules",  # Normalized to canonical values
            required_inputs=target_workflow_spec.required_inputs,
            missing_inputs=[],  # Should be validated before this point
            ambiguity_level="low",
            safe_fallback_used=False,
        )
        
        # Build execution plan
        execution_plan = self.plan_builder.build(
            user_prompt=user_prompt,
            task_selection=switched_task_selection,
            workflow_id=target_workflow_spec.workflow_id,
            workflow_path=target_workflow_spec.workflow_path,
            preset_name=target_workflow_spec.preset_name,
            rewrite_mode=current_plan.rewrite_mode,
            required_inputs=target_workflow_spec.required_inputs,
            resolved_inputs=resolved_inputs,
            enable_judging=current_plan.enable_judging,
            enable_retry_loop=False,  # Disable internal retry for switched attempt
        )
        
        # Add note about switch
        execution_plan.notes.append(f"Switched from {current_plan.workflow_id} to {target_workflow_spec.workflow_id}")
        
        return execution_plan
