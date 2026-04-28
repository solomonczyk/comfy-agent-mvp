"""Mutation-aware retry planning for targeted workflow retries.

This module provides the MutationRetryPlanner that builds targeted mutation overrides
based on execution plan, mutation report, and judge results.
"""

import random
from dataclasses import dataclass, field
from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.judges.base_types import OrchestratorReport
from app.workflows.workflow_types import TaskType


@dataclass
class MutationRetryPlan:
    """Plan for mutation-aware retry.
    
    Contains the strategy and specific overrides for a retry attempt.
    """
    action: str  # "retry_seed", "retry_prompt", "retry_settings", "accept", "reject"
    retry_overrides: dict[str, Any] = field(default_factory=dict)
    retry_reasoning: list[str] = field(default_factory=list)
    source_repairs: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action,
            "retry_overrides": self.retry_overrides,
            "retry_reasoning": self.retry_reasoning,
            "source_repairs": self.source_repairs,
        }


class MutationRetryPlanner:
    """Planner for building mutation-aware retry strategies."""
    
    def __init__(self) -> None:
        """Initialize mutation retry planner."""
        self._repair_to_override_map = self._build_repair_override_map()
    
    def _build_repair_override_map(self) -> dict[str, dict[str, Any]]:
        """Build mapping from repair codes to mutation overrides.
        
        Returns:
            Dictionary mapping repair codes to override configurations
        """
        return {
            # Technical repairs
            "increase_steps_or_change_seed": {
                "override_type": "settings_or_seed",
                "settings": {"steps": 6},  # Increase by 6
                "fallback": "seed",
            },
            "reduce_highlights_or_cfg": {
                "override_type": "settings",
                "settings": {"cfg": -0.5},  # Reduce CFG by 0.5
            },
            "lift_shadows_or_adjust_prompt_lighting": {
                "override_type": "prompt",
                "prompt_suffix": ", balanced exposure, soft shadow detail",
            },
            "fix_output_resolution": {
                "override_type": "resolution",
                "resolution": {"width": 1024, "height": 1024},  # Safe default
            },
            "increase_output_resolution": {
                "override_type": "resolution",
                "resolution": {"width": 1344, "height": 768},  # Higher res
            },
            
            # Semantic repairs
            "restore_subject_focus": {
                "override_type": "prompt",
                "prompt_suffix": ", sharp focus on main subject",
            },
            "improve_prompt_alignment": {
                "override_type": "prompt",
                "prompt_suffix": ", detailed and accurate to description",
            },
            "strengthen_camera_angle": {
                "override_type": "prompt",
                "prompt_suffix": ", clear camera angle and perspective",
            },
            "recover_intended_mood": {
                "override_type": "prompt",
                "prompt_suffix": ", consistent mood and atmosphere",
            },
            
            # Artistic repairs
            "increase_subject_separation": {
                "override_type": "prompt",
                "prompt_suffix": ", subject separation, rim light, depth",
            },
            "strengthen_cinematic_contrast": {
                "override_type": "prompt",
                "prompt_suffix": ", cinematic contrast, controlled highlights",
            },
            "reduce_flat_lighting": {
                "override_type": "prompt",
                "prompt_suffix": ", shaped light, directional lighting",
            },
            "improve_focal_hierarchy": {
                "override_type": "prompt",
                "prompt_suffix": ", strong focal subject, clean background",
            },
            "reduce_oversaturation": {
                "override_type": "negative",
                "negative_suffix": ", oversaturated, neon spill",
            },
            "enforce_premium_material_rendering": {
                "override_type": "prompt",
                "prompt_suffix": ", realistic material response, premium quality",
            },
        }
    
    def build_plan(
        self,
        execution_plan: ExecutionPlan,
        mutation_report: dict[str, Any],
        retry_decision: dict[str, Any],
        orchestrator_report: OrchestratorReport | None = None,
    ) -> MutationRetryPlan:
        """Build mutation retry plan from judge results.
        
        Args:
            execution_plan: Original execution plan
            mutation_report: Report from initial mutation
            retry_decision: Retry decision from controller
            orchestrator_report: Full orchestrator report if available
            
        Returns:
            MutationRetryPlan with retry strategy and overrides
        """
        action = retry_decision.get("action", "reject")
        
        # If not a retry action, return early
        if action in ["accept", "reject"]:
            return MutationRetryPlan(
                action=action,
                retry_reasoning=[f"No retry needed: action={action}"],
                source_repairs=[],
            )
        
        # Collect all repairs from judge reports
        source_repairs = self._collect_source_repairs(orchestrator_report, retry_decision)
        
        # Build overrides based on action and repairs
        retry_overrides = self._build_retry_overrides(
            action=action,
            execution_plan=execution_plan,
            mutation_report=mutation_report,
            source_repairs=source_repairs,
        )
        
        # Build reasoning
        retry_reasoning = self._build_retry_reasoning(
            action=action,
            source_repairs=source_repairs,
            orchestrator_report=orchestrator_report,
        )
        
        return MutationRetryPlan(
            action=action,
            retry_overrides=retry_overrides,
            retry_reasoning=retry_reasoning,
            source_repairs=source_repairs,
        )
    
    def _collect_source_repairs(
        self,
        orchestrator_report: OrchestratorReport | None,
        retry_decision: dict[str, Any],
    ) -> list[str]:
        """Collect all repair codes from judge reports.
        
        Args:
            orchestrator_report: Full orchestrator report
            retry_decision: Retry decision with suggested repairs
            
        Returns:
            List of repair codes
        """
        repairs = []
        
        if orchestrator_report:
            # Collect from individual judge reports
            for judge_report in [orchestrator_report.technical, orchestrator_report.semantic, orchestrator_report.artistic]:
                repairs.extend(judge_report.recommended_repairs)
            
            # Collect global repairs
            repairs.extend(orchestrator_report.global_repairs)
        
        # Collect from retry decision
        if "suggested_prompt_suffixes" in retry_decision:
            repairs.extend(retry_decision["suggested_prompt_suffixes"])
        if "suggested_negative_additions" in retry_decision:
            repairs.extend(retry_decision["suggested_negative_additions"])
        
        return list(set(repairs))  # Deduplicate
    
    def _build_retry_overrides(
        self,
        action: str,
        execution_plan: ExecutionPlan,
        mutation_report: dict[str, Any],
        source_repairs: list[str],
    ) -> dict[str, Any]:
        """Build retry overrides based on action and repairs.
        
        Args:
            action: Retry action (retry_seed, retry_prompt, retry_settings)
            execution_plan: Original execution plan
            mutation_report: Report from initial mutation
            source_repairs: List of repair codes
            
        Returns:
            Dictionary of retry overrides (delta values marked with _delta suffix)
        """
        overrides = {}
        applied_changes = mutation_report.get("applied_changes", {})
        
        if action == "retry_seed":
            # Only change seed, keep everything else
            overrides["seed"] = random.randint(1, 2**31 - 1)
            overrides["_keep_prompt"] = True
            overrides["_keep_settings"] = True
            
        elif action == "retry_prompt":
            # Change positive/negative prompt based on repairs
            prompt_overrides = self._build_prompt_overrides(
                source_repairs=source_repairs,
                current_positive=applied_changes.get("positive_prompt", ""),
                current_negative=applied_changes.get("negative_prompt", ""),
            )
            overrides.update(prompt_overrides)
            overrides["_keep_settings"] = True
            
        elif action == "retry_settings":
            # Change settings based on repairs (delta values)
            settings_overrides = self._build_settings_overrides(
                source_repairs=source_repairs,
                current_settings=applied_changes,
                task_type=execution_plan.task_type,
            )
            overrides.update(settings_overrides)
            overrides["_keep_prompt"] = True
            
        return overrides
    
    def _build_prompt_overrides(
        self,
        source_repairs: list[str],
        current_positive: str,
        current_negative: str,
    ) -> dict[str, Any]:
        """Build prompt overrides from repair codes.
        
        Args:
            source_repairs: List of repair codes
            current_positive: Current positive prompt
            current_negative: Current negative prompt
            
        Returns:
            Dictionary with positive_prompt and/or negative_prompt overrides
        """
        positive_suffixes = []
        negative_suffixes = []
        
        for repair in source_repairs:
            repair_lower = repair.lower()
            
            # Check each repair code
            for repair_code, config in self._repair_to_override_map.items():
                if repair_code.lower() in repair_lower:
                    override_type = config.get("override_type")
                    
                    if override_type == "prompt" and "prompt_suffix" in config:
                        positive_suffixes.append(config["prompt_suffix"])
                    elif override_type == "negative" and "negative_suffix" in config:
                        negative_suffixes.append(config["negative_suffix"])
        
        overrides = {}
        
        if positive_suffixes:
            # Append suffixes to current positive prompt
            new_positive = current_positive
            for suffix in positive_suffixes:
                if suffix not in new_positive:
                    new_positive += suffix
            overrides["positive_prompt"] = new_positive
        
        if negative_suffixes:
            # Append suffixes to current negative prompt
            new_negative = current_negative
            for suffix in negative_suffixes:
                if suffix not in new_negative:
                    new_negative += suffix
            overrides["negative_prompt"] = new_negative
        
        return overrides
    
    def _build_settings_overrides(
        self,
        source_repairs: list[str],
        current_settings: dict[str, Any],
        task_type: TaskType,
    ) -> dict[str, Any]:
        """Build settings overrides from repair codes.
        
        Args:
            source_repairs: List of repair codes
            current_settings: Current applied settings
            task_type: Task type for context
            
        Returns:
            Dictionary with settings overrides
        """
        overrides = {}
        
        for repair in source_repairs:
            repair_lower = repair.lower()
            
            # Check each repair code
            for repair_code, config in self._repair_to_override_map.items():
                if repair_code.lower() in repair_lower:
                    override_type = config.get("override_type")
                    
                    if override_type == "settings" and "settings" in config:
                        settings = config["settings"]
                        for key, value in settings.items():
                            if isinstance(value, (int, float)):
                                # Handle relative values
                                if key in current_settings:
                                    current_value = current_settings[key]
                                    if isinstance(current_value, (int, float)):
                                        overrides[key] = current_value + value
                            else:
                                overrides[key] = value
                    
                    elif override_type == "settings_or_seed" and "fallback" in config:
                        # Try settings first, fallback to seed
                        if "settings" in config:
                            settings = config["settings"]
                            for key, value in settings.items():
                                if isinstance(value, (int, float)):
                                    if key in current_settings:
                                        current_value = current_settings[key]
                                        if isinstance(current_value, (int, float)):
                                            overrides[key] = current_value + value
                                else:
                                    overrides[key] = value
                        else:
                            overrides["seed"] = random.randint(1, 2**31 - 1)
                    
                    elif override_type == "resolution" and "resolution" in config:
                        resolution = config["resolution"]
                        overrides.update(resolution)
        
        return overrides
    
    def _build_retry_reasoning(
        self,
        action: str,
        source_repairs: list[str],
        orchestrator_report: OrchestratorReport | None,
    ) -> list[str]:
        """Build reasoning for retry decision.
        
        Args:
            action: Retry action
            source_repairs: List of repair codes
            orchestrator_report: Full orchestrator report
            
        Returns:
            List of reasoning strings
        """
        reasoning = []
        
        if action == "retry_seed":
            reasoning.append("Retry with new seed to address stochastic variation")
        
        elif action == "retry_prompt":
            reasoning.append("Retry with refined prompt based on judge feedback")
            if orchestrator_report:
                if orchestrator_report.semantic.verdict == "retry":
                    reasoning.append("Semantic judge requested better prompt alignment")
                if orchestrator_report.artistic.verdict == "retry":
                    reasoning.append("Artistic judge requested composition/styling improvements")
        
        elif action == "retry_settings":
            reasoning.append("Retry with adjusted generation settings")
            if orchestrator_report:
                if orchestrator_report.technical.verdict == "retry":
                    reasoning.append("Technical judge requested settings repair")
        
        # Add repair-specific reasoning
        for repair in source_repairs[:3]:  # Limit to top 3 for brevity
            reasoning.append(f"Addressing repair: {repair}")
        
        return reasoning
