"""Workflow switch policy for controlled workflow switching.

NOTE: This module is now a validation layer only.
The canonical decision layer for WHAT action to take is CorrectiveActionPolicy in app/agent/corrective_action_policy.py.
WorkflowSwitchPolicy validates IF a switch is safe and builds the switched execution plan.
It does not decide whether to switch - that decision comes from CorrectiveActionPolicy.
"""

from dataclasses import dataclass, field
from typing import Any

from app.agent.task_selector import TaskSelectionResult
from app.agent.execution_plan import ExecutionPlan


# Allowed workflow transitions (switch matrix)
ALLOWED_SWITCHES = {
    # img2img_v1 can switch to upscale or inpaint_face
    "img2img_v1": ["upscale_v1", "inpaint_face_v1"],
    # upscale_v1 can switch back to img2img
    "upscale_v1": ["img2img_v1"],
    # inpaint_face_v1 can switch back to img2img (if assets valid)
    "inpaint_face_v1": ["img2img_v1"],
    # txt2img family should not switch to edit branches without assets
    # (handled in policy logic)
}

# Asset requirements for target workflows
WORKFLOW_ASSET_REQUIREMENTS = {
    "img2img_v1": ["input_image"],
    "inpaint_face_v1": ["input_image", "mask_image"],
    "upscale_v1": ["input_image"],
    "txt2img_portrait": [],
    "txt2img_cinematic": [],
    "txt2img_product": [],
    "txt2img_fashion": [],
}


@dataclass
class WorkflowSwitchDecision:
    """Decision about whether to switch workflows.
    
    This dataclass represents the policy decision for workflow switching,
    including the target workflow, reason for switch, and validation status.
    """
    action: str  # "keep_current" | "retry_current" | "switch_workflow" | "reject"
    switch_allowed: bool
    from_workflow_id: str | None = None
    to_workflow_id: str | None = None
    switch_reason: str = ""
    source_trigger: str | None = None
    missing_inputs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action,
            "switch_allowed": self.switch_allowed,
            "from_workflow_id": self.from_workflow_id,
            "to_workflow_id": self.to_workflow_id,
            "switch_reason": self.switch_reason,
            "source_trigger": self.source_trigger,
            "missing_inputs": self.missing_inputs,
            "notes": self.notes,
        }


class WorkflowSwitchPolicy:
    """Policy for deciding when to switch between known workflows."""
    
    def __init__(self) -> None:
        """Initialize workflow switch policy."""
        # No stateful flags - anti-multi-hop guard is per-run via parameter
    
    def evaluate(
        self,
        task_selection: TaskSelectionResult | None,
        execution_plan: ExecutionPlan | None,
        mutation_report: dict[str, Any] | None,
        retry_decision: dict[str, Any] | None,
        orchestrator_report: dict[str, Any] | None,
        assets: dict[str, Any] | None,
        switch_applied_this_run: bool = False,
    ) -> WorkflowSwitchDecision:
        """Evaluate whether to switch workflows.
        
        Args:
            task_selection: Task selection result
            execution_plan: Current execution plan
            mutation_report: Mutation report from current attempt
            retry_decision: Retry decision from judge controller
            orchestrator_report: Judge orchestrator report
            assets: Available assets (input_image, mask_image, etc.)
            switch_applied_this_run: Whether a switch has already been applied in this run
            
        Returns:
            WorkflowSwitchDecision with action and target workflow
        """
        # Guard against multi-hop switching (per-run guard via parameter)
        if switch_applied_this_run:
            return WorkflowSwitchDecision(
                action="keep_current",
                switch_allowed=False,
                from_workflow_id=execution_plan.workflow_id if execution_plan else None,
                to_workflow_id=None,
                switch_reason="Multi-hop switching not allowed",
                source_trigger="guard",
                notes=["Switch already applied this run"],
            )
        
        # If no retry decision, keep current
        if not retry_decision:
            return WorkflowSwitchDecision(
                action="keep_current",
                switch_allowed=False,
                from_workflow_id=execution_plan.workflow_id if execution_plan else None,
                to_workflow_id=None,
                switch_reason="No retry decision",
                source_trigger=None,
            )
        
        # Check if retry decision explicitly requests switch
        retry_action = retry_decision.get("action")
        
        if retry_action == "reject":
            return WorkflowSwitchDecision(
                action="reject",
                switch_allowed=False,
                from_workflow_id=execution_plan.workflow_id if execution_plan else None,
                to_workflow_id=None,
                switch_reason="Judge rejected result",
                source_trigger="retry_decision",
            )
        
        if retry_action == "accept":
            return WorkflowSwitchDecision(
                action="keep_current",
                switch_allowed=False,
                from_workflow_id=execution_plan.workflow_id if execution_plan else None,
                to_workflow_id=None,
                switch_reason="Judge accepted result",
                source_trigger="retry_decision",
            )
        
        # Evaluate switch based on orchestrator report
        target_workflow_id = self._determine_target_workflow(
            orchestrator_report=orchestrator_report,
            current_workflow_id=execution_plan.workflow_id if execution_plan else None,
            assets=assets,
        )
        
        if target_workflow_id:
            # Validate asset requirements
            missing_inputs = self._validate_asset_requirements(
                target_workflow_id=target_workflow_id,
                assets=assets,
            )
            
            if missing_inputs:
                return WorkflowSwitchDecision(
                    action="retry_current",
                    switch_allowed=False,
                    from_workflow_id=execution_plan.workflow_id if execution_plan else None,
                    to_workflow_id=target_workflow_id,
                    switch_reason=f"Switch blocked by missing assets: {', '.join(missing_inputs)}",
                    source_trigger="asset_validation",
                    missing_inputs=missing_inputs,
                    notes=["Target workflow requires assets not available"],
                )
            
            # Validate switch is allowed in matrix
            current_workflow_id = execution_plan.workflow_id if execution_plan else None
            if not self._is_switch_allowed(current_workflow_id, target_workflow_id):
                return WorkflowSwitchDecision(
                    action="retry_current",
                    switch_allowed=False,
                    from_workflow_id=current_workflow_id,
                    to_workflow_id=target_workflow_id,
                    switch_reason=f"Switch not allowed in matrix: {current_workflow_id} -> {target_workflow_id}",
                    source_trigger="switch_matrix",
                    notes=["Transition not in allowed switch matrix"],
                )
            
            switch_reason = self._generate_switch_reason(
                orchestrator_report=orchestrator_report,
                target_workflow_id=target_workflow_id,
            )
            
            return WorkflowSwitchDecision(
                action="switch_workflow",
                switch_allowed=True,
                from_workflow_id=current_workflow_id,
                to_workflow_id=target_workflow_id,
                switch_reason=switch_reason,
                source_trigger="orchestrator_report",
                notes=["Switch approved by policy"],
            )
        
        # Default to normal retry
        return WorkflowSwitchDecision(
            action="retry_current",
            switch_allowed=False,
            from_workflow_id=execution_plan.workflow_id if execution_plan else None,
            to_workflow_id=None,
            switch_reason="Normal retry sufficient",
            source_trigger="default",
        )
    
    def _determine_target_workflow(
        self,
        orchestrator_report: dict[str, Any] | None,
        current_workflow_id: str | None,
        assets: dict[str, Any] | None,
    ) -> str | None:
        """Determine target workflow based on orchestrator report.
        
        Args:
            orchestrator_report: Judge orchestrator report
            current_workflow_id: Current workflow ID
            assets: Available assets
            
        Returns:
            Target workflow ID or None if no switch needed
        """
        if not orchestrator_report:
            return None
        
        # Extract repair recommendations
        technical = orchestrator_report.get("technical", {})
        semantic = orchestrator_report.get("semantic", {})
        artistic = orchestrator_report.get("artistic", {})
        
        recommended_repairs = []
        for judge_report in [technical, semantic, artistic]:
            repairs = judge_report.get("recommended_repairs", [])
            recommended_repairs.extend(repairs)
        
        repairs_str = " ".join(recommended_repairs).lower()
        
        # Case A: img2img -> upscale
        # Trigger: resolution-focused repair, sharper detail, output resolution issue
        upscale_keywords = [
            "resolution",
            "sharper",
            "detail",
            "upscale",
            "low resolution",
            "blurry",
            "pixelated",
        ]
        
        if current_workflow_id == "img2img_v1":
            if any(keyword in repairs_str for keyword in upscale_keywords):
                return "upscale_v1"
        
        # Case B: img2img -> inpaint_face
        # Trigger: face repair, eye artifacts, skin cleanup, portrait-localized repair
        face_keywords = [
            "face",
            "eye",
            "skin",
            "portrait",
            "artifact",
            "cleanup",
            "inpaint",
        ]
        
        if current_workflow_id == "img2img_v1":
            if any(keyword in repairs_str for keyword in face_keywords):
                return "inpaint_face_v1"
        
        # Case C: upscale -> img2img
        # Trigger: general quality issues not resolution-specific
        if current_workflow_id == "upscale_v1":
            if "composition" in repairs_str or "style" in repairs_str:
                return "img2img_v1"
        
        # Case D: inpaint_face -> img2img
        # Trigger: broader issues beyond face region
        if current_workflow_id == "inpaint_face_v1":
            if "background" in repairs_str or "composition" in repairs_str:
                return "img2img_v1"
        
        return None
    
    def _is_switch_allowed(self, from_workflow: str | None, to_workflow: str) -> bool:
        """Check if switch is allowed in the switch matrix.
        
        Args:
            from_workflow: Source workflow ID
            to_workflow: Target workflow ID
            
        Returns:
            True if switch is allowed, False otherwise
        """
        if not from_workflow:
            return False
        
        allowed_targets = ALLOWED_SWITCHES.get(from_workflow, [])
        return to_workflow in allowed_targets
    
    def _validate_asset_requirements(
        self,
        target_workflow_id: str,
        assets: dict[str, Any] | None,
    ) -> list[str]:
        """Validate that required assets are available for target workflow.
        
        Args:
            target_workflow_id: Target workflow ID
            assets: Available assets dictionary
            
        Returns:
            List of missing asset keys
        """
        required_assets = WORKFLOW_ASSET_REQUIREMENTS.get(target_workflow_id, [])
        missing = []
        
        for asset_key in required_assets:
            if not assets or assets.get(asset_key) is None:
                missing.append(asset_key)
        
        return missing
    
    def _generate_switch_reason(
        self,
        orchestrator_report: dict[str, Any] | None,
        target_workflow_id: str,
    ) -> str:
        """Generate human-readable switch reason.
        
        Args:
            orchestrator_report: Judge orchestrator report
            target_workflow_id: Target workflow ID
            
        Returns:
            Human-readable switch reason
        """
        if not orchestrator_report:
            return f"Switching to {target_workflow_id}"
        
        technical = orchestrator_report.get("technical", {})
        semantic = orchestrator_report.get("semantic", {})
        artistic = orchestrator_report.get("artistic", {})
        
        # Collect repair recommendations
        repairs = []
        for judge_report in [technical, semantic, artistic]:
            repairs.extend(judge_report.get("recommended_repairs", []))
        
        if repairs:
            repairs_str = "; ".join(repairs[:3])  # Limit to first 3 repairs
            return f"Judge recommended repairs: {repairs_str} -> switching to {target_workflow_id}"
        
        return f"Switching to {target_workflow_id} based on judge feedback"
