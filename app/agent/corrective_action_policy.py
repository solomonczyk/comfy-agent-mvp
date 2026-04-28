"""Corrective Action Policy for unified decision layer.

This module provides the canonical policy layer for deciding what corrective action
to take after judge evaluation. It centralizes the decision logic that was previously
drifted between RetryController, WorkflowSwitchPolicy, and workflow_agent_service.py.

The policy decides WHAT to do (accept, retry_seed, retry_prompt, retry_settings, 
switch_workflow, reject) based on judge feedback, while WorkflowSwitchPolicy handles
feasibility validation and planning.
"""

from dataclasses import dataclass, field
from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.agent.task_selector import TaskSelectionResult
from app.judges.base_types import OrchestratorReport


# Normalized reason codes for corrective actions
REASON_CODE_ACCEPTED_BY_JUDGE = "accepted_by_judge"
REASON_CODE_SEMANTIC_ALIGNMENT_RETRY = "semantic_alignment_retry"
REASON_CODE_TECHNICAL_SETTINGS_RETRY = "technical_settings_retry"
REASON_CODE_SEED_VARIATION_RETRY = "seed_variation_retry"
REASON_CODE_RESOLUTION_REPAIR_SWITCH = "resolution_repair_switch"
REASON_CODE_FACE_REPAIR_SWITCH = "face_repair_switch"
REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS = "switch_blocked_missing_inputs"
REASON_CODE_REJECT_AFTER_JUDGE = "reject_after_judge"
REASON_CODE_NO_SAFE_CORRECTIVE_ACTION = "no_safe_corrective_action"

# Allowed reason codes
ALLOWED_REASON_CODES = {
    REASON_CODE_ACCEPTED_BY_JUDGE,
    REASON_CODE_SEMANTIC_ALIGNMENT_RETRY,
    REASON_CODE_TECHNICAL_SETTINGS_RETRY,
    REASON_CODE_SEED_VARIATION_RETRY,
    REASON_CODE_RESOLUTION_REPAIR_SWITCH,
    REASON_CODE_FACE_REPAIR_SWITCH,
    REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS,
    REASON_CODE_REJECT_AFTER_JUDGE,
    REASON_CODE_NO_SAFE_CORRECTIVE_ACTION,
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
class CorrectiveActionDecision:
    """Canonical decision for corrective action.
    
    This dataclass represents the single source of truth for what action to take
    after judge evaluation. All downstream layers (retry path, switch path) should
    use this decision without reinterpreting.
    """
    action: str  # accept | retry_seed | retry_prompt | retry_settings | switch_workflow | reject
    reason_code: str
    reason: str
    source_repairs: list[str] = field(default_factory=list)
    selected_workflow_id: str | None = None
    target_workflow_id: str | None = None
    required_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    switch_allowed: bool | None = None
    notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "source_repairs": self.source_repairs,
            "selected_workflow_id": self.selected_workflow_id,
            "target_workflow_id": self.target_workflow_id,
            "required_inputs": self.required_inputs,
            "missing_inputs": self.missing_inputs,
            "switch_allowed": self.switch_allowed,
            "notes": self.notes,
        }


class CorrectiveActionPolicy:
    """Policy for deciding corrective action after judge evaluation.
    
    This policy centralizes the decision logic for what corrective action to take.
    It maps judge feedback to canonical actions with normalized reason codes.
    
    Responsibility separation:
    - CorrectiveActionPolicy: decides WHAT to do
    - WorkflowSwitchPolicy: validates IF switch is safe and builds switched plan
    """
    
    def __init__(self) -> None:
        """Initialize corrective action policy."""
        pass
    
    def evaluate(
        self,
        task_selection: TaskSelectionResult | None,
        execution_plan: ExecutionPlan | None,
        mutation_report: dict[str, Any] | None,
        orchestrator_report: dict[str, Any] | None,
        assets: dict[str, Any] | None,
    ) -> CorrectiveActionDecision:
        """Evaluate corrective action based on judge feedback.
        
        Args:
            task_selection: Task selection result
            execution_plan: Current execution plan
            mutation_report: Mutation report from current attempt
            orchestrator_report: Judge orchestrator report
            assets: Available assets (input_image, mask_image, etc.)
            
        Returns:
            CorrectiveActionDecision with canonical action and reason
        """
        # Extract orchestrator report data
        final_verdict = orchestrator_report.get("final_verdict") if orchestrator_report else None
        best_next_action = orchestrator_report.get("best_next_action") if orchestrator_report else None
        global_repairs = orchestrator_report.get("global_repairs", []) if orchestrator_report else []
        
        current_workflow_id = execution_plan.workflow_id if execution_plan else None
        
        # Case A: pass -> accept
        if final_verdict == "pass":
            return CorrectiveActionDecision(
                action="accept",
                reason_code=REASON_CODE_ACCEPTED_BY_JUDGE,
                reason="Generation accepted by judge",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=None,
                switch_allowed=False,
                notes=["Judge approved the result"],
            )
        
        # Case B: img2img + resolution-focused repair -> switch_workflow upscale (check before general technical settings)
        if current_workflow_id == "img2img_v1" and self._is_resolution_repair(orchestrator_report):
            target_workflow_id = "upscale_v1"
            required_inputs = WORKFLOW_ASSET_REQUIREMENTS.get(target_workflow_id, [])
            missing_inputs = self._validate_asset_requirements(target_workflow_id, assets)
            
            if missing_inputs:
                # Deterministic fallback to retry_settings when switch blocked
                return CorrectiveActionDecision(
                    action="retry_settings",
                    reason_code=REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS,
                    reason=f"Switch to upscale blocked by missing assets: {', '.join(missing_inputs)}",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=target_workflow_id,
                    required_inputs=required_inputs,
                    missing_inputs=missing_inputs,
                    switch_allowed=False,
                    notes=["Deterministic fallback: switch blocked, falling back to settings retry"],
                )
            
            return CorrectiveActionDecision(
                action="switch_workflow",
                reason_code=REASON_CODE_RESOLUTION_REPAIR_SWITCH,
                reason="Technical judge requested resolution-focused repair for img2img result",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=target_workflow_id,
                required_inputs=required_inputs,
                missing_inputs=[],
                switch_allowed=True,
                notes=["Switch to upscale workflow for resolution repair"],
            )
        
        # Case C: img2img + face-specific repair -> switch_workflow inpaint_face (check before general technical settings)
        if current_workflow_id == "img2img_v1" and self._is_face_repair(orchestrator_report):
            target_workflow_id = "inpaint_face_v1"
            required_inputs = WORKFLOW_ASSET_REQUIREMENTS.get(target_workflow_id, [])
            missing_inputs = self._validate_asset_requirements(target_workflow_id, assets)
            
            if missing_inputs:
                # Deterministic fallback to retry_settings when switch blocked
                return CorrectiveActionDecision(
                    action="retry_settings",
                    reason_code=REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS,
                    reason=f"Switch to inpaint_face blocked by missing assets: {', '.join(missing_inputs)}",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=target_workflow_id,
                    required_inputs=required_inputs,
                    missing_inputs=missing_inputs,
                    switch_allowed=False,
                    notes=["Deterministic fallback: switch blocked, falling back to settings retry"],
                )
            
            return CorrectiveActionDecision(
                action="switch_workflow",
                reason_code=REASON_CODE_FACE_REPAIR_SWITCH,
                reason="Technical judge requested face-specific repair for img2img result",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=target_workflow_id,
                required_inputs=required_inputs,
                missing_inputs=[],
                switch_allowed=True,
                notes=["Switch to inpaint_face workflow for face repair"],
            )
        
        # Case D: semantic mismatch / prompt alignment issue -> retry_prompt
        if self._is_semantic_mismatch(orchestrator_report):
            return CorrectiveActionDecision(
                action="retry_prompt",
                reason_code=REASON_CODE_SEMANTIC_ALIGNMENT_RETRY,
                reason="Semantic mismatch detected - prompt/intent alignment needs correction",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=None,
                switch_allowed=False,
                notes=["Judge recommended prompt or intent alignment repair"],
            )
        
        # Case E: technical generation settings issue -> retry_settings
        if self._is_technical_settings_issue(orchestrator_report):
            return CorrectiveActionDecision(
                action="retry_settings",
                reason_code=REASON_CODE_TECHNICAL_SETTINGS_RETRY,
                reason="Technical quality needs repair through generation settings",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=None,
                switch_allowed=False,
                notes=["Judge recommended settings-based repair (steps, cfg, resolution, etc.)"],
            )
        
        # Case F: pure variation / composition improvement -> retry_seed
        if self._is_pure_variation_request(orchestrator_report):
            return CorrectiveActionDecision(
                action="retry_seed",
                reason_code=REASON_CODE_SEED_VARIATION_RETRY,
                reason="Retry with new seed while keeping general workflow stable",
                source_repairs=global_repairs,
                selected_workflow_id=current_workflow_id,
                target_workflow_id=None,
                switch_allowed=False,
                notes=["Judge recommended variation without structural changes"],
            )
        
        # Case G: respect orchestrator's best_next_action if set
        if best_next_action:
            if best_next_action == "retry_seed":
                return CorrectiveActionDecision(
                    action="retry_seed",
                    reason_code=REASON_CODE_SEED_VARIATION_RETRY,
                    reason="Retry with new seed based on orchestrator recommendation",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=None,
                    switch_allowed=False,
                    notes=["Orchestrator recommended seed variation"],
                )
            elif best_next_action == "retry_prompt":
                return CorrectiveActionDecision(
                    action="retry_prompt",
                    reason_code=REASON_CODE_SEMANTIC_ALIGNMENT_RETRY,
                    reason="Retry with prompt adjustment based on orchestrator recommendation",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=None,
                    switch_allowed=False,
                    notes=["Orchestrator recommended prompt alignment"],
                )
            elif best_next_action == "retry_settings":
                return CorrectiveActionDecision(
                    action="retry_settings",
                    reason_code=REASON_CODE_TECHNICAL_SETTINGS_RETRY,
                    reason="Retry with settings adjustment based on orchestrator recommendation",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=None,
                    switch_allowed=False,
                    notes=["Orchestrator recommended settings repair"],
                )
            elif best_next_action == "switch_workflow":
                # Fallback: switch requested but no specific target determined
                # Use retry_settings as deterministic fallback
                return CorrectiveActionDecision(
                    action="retry_settings",
                    reason_code=REASON_CODE_NO_SAFE_CORRECTIVE_ACTION,
                    reason="Switch requested but no specific target determined - using settings retry as fallback",
                    source_repairs=global_repairs,
                    selected_workflow_id=current_workflow_id,
                    target_workflow_id=None,
                    switch_allowed=False,
                    notes=["Orchestrator recommended switch but target unclear - deterministic fallback"],
                )
        
        # Default: reject if no safe corrective action identified
        return CorrectiveActionDecision(
            action="reject",
            reason_code=REASON_CODE_REJECT_AFTER_JUDGE,
            reason="Reject after judge aggregation - no safe corrective action identified",
            source_repairs=global_repairs,
            selected_workflow_id=current_workflow_id,
            target_workflow_id=None,
            switch_allowed=False,
            notes=["No safe corrective action could be determined"],
        )
    
    def _is_semantic_mismatch(self, orchestrator_report: dict[str, Any] | None) -> bool:
        """Check if the issue is semantic/prompt alignment.
        
        Args:
            orchestrator_report: Judge orchestrator report
            
        Returns:
            True if semantic mismatch detected
        """
        if not orchestrator_report:
            return False
        
        # Check semantic judge specifically
        semantic = orchestrator_report.get("semantic", {})
        if semantic.get("final_verdict") == "fail":
            return True
        
        # Check for semantic-related keywords in global repairs
        global_repairs = orchestrator_report.get("global_repairs", [])
        repairs_text = " ".join(global_repairs).lower()
        
        semantic_keywords = [
            "prompt",
            "intent",
            "meaning",
            "subject",
            "style mismatch",
            "not what was requested",
            "wrong subject",
            "wrong style",
        ]
        
        return any(keyword in repairs_text for keyword in semantic_keywords)
    
    def _is_technical_settings_issue(self, orchestrator_report: dict[str, Any] | None) -> bool:
        """Check if the issue is technical settings-related.
        
        Args:
            orchestrator_report: Judge orchestrator report
            
        Returns:
            True if technical settings issue detected
        """
        if not orchestrator_report:
            return False
        
        # Check technical judge specifically
        technical = orchestrator_report.get("technical", {})
        if technical.get("final_verdict") == "fail":
            repairs = technical.get("recommended_repairs", [])
            repairs_text = " ".join(repairs).lower()
            
            # Look for settings-related keywords
            settings_keywords = [
                "steps",
                "cfg",
                "resolution",
                "sampler",
                "scheduler",
                "denoise",
                "highlights",
                "fix_output",
            ]
            
            return any(keyword in repairs_text for keyword in settings_keywords)
        
        # Check global repairs for settings keywords
        global_repairs = orchestrator_report.get("global_repairs", [])
        repairs_text = " ".join(global_repairs).lower()
        
        settings_keywords = [
            "increase_steps",
            "reduce_highlights",
            "fix_output_resolution",
            "cfg",
            "denoise",
        ]
        
        return any(keyword in repairs_text for keyword in settings_keywords)
    
    def _is_pure_variation_request(self, orchestrator_report: dict[str, Any] | None) -> bool:
        """Check if the request is for pure variation without structural changes.
        
        Args:
            orchestrator_report: Judge orchestrator report
            
        Returns:
            True if pure variation request detected
        """
        if not orchestrator_report:
            return False
        
        # Check best_next_action
        best_next_action = orchestrator_report.get("best_next_action")
        if best_next_action == "retry_seed":
            return True
        
        # Check for variation-related keywords
        global_repairs = orchestrator_report.get("global_repairs", [])
        repairs_text = " ".join(global_repairs).lower()
        
        variation_keywords = [
            "variation",
            "different composition",
            "try again",
            "another attempt",
            "seed",
        ]
        
        # Only return True if no semantic or technical issues are present
        if self._is_semantic_mismatch(orchestrator_report):
            return False
        if self._is_technical_settings_issue(orchestrator_report):
            return False
        
        return any(keyword in repairs_text for keyword in variation_keywords)
    
    def _is_resolution_repair(self, orchestrator_report: dict[str, Any] | None) -> bool:
        """Check if the repair is resolution-focused (for switch to upscale).
        
        This should only return True for upscale/sharpen operations, not general
        resolution fixes which are handled by retry_settings.
        
        Args:
            orchestrator_report: Judge orchestrator report
            
        Returns:
            True if resolution repair detected (for switch)
        """
        if not orchestrator_report:
            return False
        
        # Collect all repairs from judges and global
        repairs = []
        for judge_key in ["technical", "semantic", "artistic"]:
            judge_report = orchestrator_report.get(judge_key, {})
            repairs.extend(judge_report.get("recommended_repairs", []))
        
        # Also include global_repairs
        global_repairs = orchestrator_report.get("global_repairs", [])
        repairs.extend(global_repairs)
        
        repairs_text = " ".join(repairs).lower()
        
        # Only trigger switch for explicit upscale/sharpen keywords
        # Exclude "fix_output_resolution" which is a settings issue
        resolution_switch_keywords = [
            "upscale",
            "sharper",
            "sharpen",
            "enhance detail",
            "increase resolution",
            "higher resolution",
            "low resolution",  # Only if requesting to fix low res via upscale
            "blurry",  # Only if requesting to fix blur via upscale
        ]
        
        # Exclude settings-related resolution fixes
        if "fix_output_resolution" in repairs_text:
            return False
        
        return any(keyword in repairs_text for keyword in resolution_switch_keywords)
    
    def _is_face_repair(self, orchestrator_report: dict[str, Any] | None) -> bool:
        """Check if the repair is face-specific.
        
        Args:
            orchestrator_report: Judge orchestrator report
            
        Returns:
            True if face repair detected
        """
        if not orchestrator_report:
            return False
        
        # Collect all repairs
        repairs = []
        for judge_key in ["technical", "semantic", "artistic"]:
            judge_report = orchestrator_report.get(judge_key, {})
            repairs.extend(judge_report.get("recommended_repairs", []))
        
        repairs_text = " ".join(repairs).lower()
        
        face_keywords = [
            "face",
            "eye",
            "skin",
            "portrait",
            "artifact",
            "cleanup",
            "inpaint",
        ]
        
        return any(keyword in repairs_text for keyword in face_keywords)
    
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
