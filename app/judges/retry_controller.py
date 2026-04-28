"""Retry controller for judge-based retry decisions.

DEPRECATED: This module is deprecated for action decision logic.
The canonical decision layer is now CorrectiveActionPolicy in app/agent/corrective_action_policy.py.
RetryController is kept for backward compatibility but should not be used for new action decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.judges.base_types import OrchestratorReport


@dataclass
class RetryDecision:
    action: str
    max_retries: int
    suggested_prompt_suffixes: list[str] = field(default_factory=list)
    suggested_negative_additions: list[str] = field(default_factory=list)
    suggested_settings_updates: dict[str, object] = field(default_factory=dict)
    target_workflow_id: str | None = None
    notes: list[str] = field(default_factory=list)


class RetryController:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def build_decision(self, report: OrchestratorReport) -> RetryDecision:
        if report.final_verdict == "pass":
            return RetryDecision(
                action="accept",
                max_retries=self.max_retries,
                notes=["Generation accepted"],
            )

        # Respect orchestrator's best_next_action - only populate details
        action = report.best_next_action

        if action == "retry_seed":
            return RetryDecision(
                action="retry_seed",
                max_retries=self.max_retries,
                notes=["Retry with new seed while keeping general workflow stable"],
            )

        if action == "retry_prompt":
            return RetryDecision(
                action="retry_prompt",
                max_retries=self.max_retries,
                suggested_prompt_suffixes=report.global_repairs,
                notes=["Prompt/intent alignment needs correction"],
            )

        if action == "retry_settings":
            settings_updates = {}
            repairs_text = " ".join(report.global_repairs)

            if "increase_steps_or_change_seed" in repairs_text:
                settings_updates["steps"] = 36
            if "reduce_highlights_or_cfg" in repairs_text:
                settings_updates["cfg"] = 5.5
            if "fix_output_resolution" in repairs_text:
                settings_updates["width"] = 1024
                settings_updates["height"] = 1024

            return RetryDecision(
                action="retry_settings",
                max_retries=self.max_retries,
                suggested_settings_updates=settings_updates,
                suggested_negative_additions=report.global_repairs,
                notes=["Technical quality needs repair through generation settings"],
            )

        if action == "switch_workflow":
            # Extract target workflow from repairs if specified
            repairs_text = " ".join(report.global_repairs).lower()
            target_workflow_id = None
            
            # Simple heuristic for target workflow based on repairs
            if "upscale" in repairs_text or "resolution" in repairs_text:
                target_workflow_id = "upscale_v1"
            elif "face" in repairs_text or "inpaint" in repairs_text:
                target_workflow_id = "inpaint_face_v1"
            
            return RetryDecision(
                action="switch_workflow",
                max_retries=self.max_retries,
                target_workflow_id=target_workflow_id,
                suggested_negative_additions=report.global_repairs,
                notes=["Workflow switch recommended based on judge feedback"],
            )

        # Default to reject if action is unrecognized
        return RetryDecision(
            action="reject",
            max_retries=self.max_retries,
            notes=["Reject after judge aggregation"],
        )
