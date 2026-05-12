"""
Data models for Fresh Visual Strategy artifacts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DefectClassification(Enum):
    """Classification of visual defects for repairability assessment."""
    REPAIRABLE_WITH_VALIDATED_TOOLS = "repairable_with_validated_tools"
    NOT_REPAIRABLE_WITH_CURRENT_TOOLS = "not_repairable_with_current_tools"
    UNKNOWN_REPAIRABILITY = "unknown_repairability"
    OPERATOR_REVIEW_REQUIRED = "operator_review_required"
    GENERATION_RECIPE_MUST_CHANGE = "generation_recipe_must_change"


@dataclass
class FreshVisualStrategyManifest:
    """Manifest for the fresh visual strategy package."""
    task_id: str
    version: str
    timestamp: str
    strategy_type: str
    previous_task: str
    previous_commit: str
    visuals_purged: bool
    purge_reason: str
    strategy_purpose: str
    strategy_scope: List[str]
    generation_authorized: bool
    generation_blocked_until: str
    qa_repairability_gate_active: bool
    unknown_repairability_blocks: bool
    artifacts: List[str]
    forbidden_actions: Dict[str, bool]


@dataclass
class VisualStyleDirection:
    """Visual style direction and requirements."""
    target_style: str
    style_reference: str
    mood: str
    lighting_approach: str
    color_palette: Dict[str, Any]
    composition_requirements: Dict[str, Any]
    character_identity_requirements: Dict[str, Any]
    technical_style_parameters: Dict[str, Any]
    style_enforcement: Dict[str, Any]


@dataclass
class VisualQualityTargets:
    """Quality targets and defect classification."""
    face_quality: Dict[str, Any]
    hands_quality: Dict[str, Any]
    composition_quality: Dict[str, Any]
    detail_quality: Dict[str, Any]
    style_quality: Dict[str, Any]
    quality_barriers: Dict[str, Any]
    quality_validation: Dict[str, Any]


@dataclass
class NegativeReference:
    """A negative reference documenting a visual defect."""
    defect_type: str
    description: str
    reference_asset: Optional[str]
    repairability: DefectClassification
    prevention_strategy: str


@dataclass
class RepairabilityAwarePolicy:
    """Policy for repairability-aware visual quality assessment."""
    policy_purpose: str
    qa_repairability_gate_required: bool
    unknown_repairability_blocks: bool
    downstream_requires_validated_repairability: bool
    technical_pass_is_not_visual_pass: bool
    visual_operator_review_required: bool
    production_accepted_must_remain_false: bool
    defect_classification: Dict[str, Any]
    repairability_assessment_workflow: Dict[str, Any]
    repair_tool_registry: Dict[str, str]
    defect_repairability_matrix: Dict[str, str]
    enforcement_points: List[str]
    policy_version: str
    policy_status: str


@dataclass
class GenerationGateRequirements:
    """Requirements for the future generation gate."""
    generation_authorized: bool
    future_generation_requires_explicit_gate: bool
    gate_purpose: str
    prerequisite_checks: Dict[str, Any]
    post_generation_requirements: Dict[str, Any]
    generation_count_tracking: Dict[str, Any]
    gate_authorization: Dict[str, Any]
    gate_status: Dict[str, Any]
    forbidden_without_gate: List[str]


@dataclass
class StrategyReadinessResult:
    """Result of strategy readiness assessment."""
    task_id: str
    timestamp: str
    overall_readiness: str
    ready_for_generation: bool
    generation_blocked_until: str
    artifact_readiness: Dict[str, Any]
    policy_readiness: Dict[str, bool]
    reference_readiness: Dict[str, Any]
    forbidden_actions_verification: Dict[str, bool]
    state_verification: Dict[str, str]
    readiness_checklist: Dict[str, bool]
    blockers: List[str]
    warnings: List[str]
    recommendation: str
