"""Repairability taxonomy and assessment — determines if defects can be fixed downstream.

This module defines:
- Repairability classes (taxonomy of how defects can be fixed)
- Defect-to-repairability matrix (which defects map to which repairability classes)
- Repair tool registry (available repair mechanisms)
- Repairability assessment logic
"""

from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Repairability taxonomy
# ---------------------------------------------------------------------------

REPAIRABILITY_CLASSES: List[str] = [
    "repairable_downstream",
    "repairable_with_custom_nodes",
    "repairable_with_standard_nodes",
    "repairable_with_workflow_patch",
    "repairable_with_timeline_repair",
    "requires_controlled_regeneration",
    "requires_operator_review",
    "not_repairable_downstream",
    "unknown_repairability_blocked",
]

# ---------------------------------------------------------------------------
# Defect-to-repairability matrix
# ---------------------------------------------------------------------------

DEFECT_REPAIRABILITY_MATRIX: Dict[str, Dict[str, Any]] = {
    "duplicate_static_frames": {
        "defect_id": "duplicate_static_frames",
        "severity": "blocker",
        "downstream_repairability": "repairable_with_timeline_repair",
        "allowed_fix_paths": [
            "timeline_segment_repair",
            "controlled_preview_rerender_authorization_required"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "preview_correction_plan_required"
    },
    "empty_timeline_no_assets_placed": {
        "defect_id": "empty_timeline_no_assets_placed",
        "severity": "blocker",
        "downstream_repairability": "repairable_with_timeline_repair",
        "allowed_fix_paths": [
            "timeline_segment_repair",
            "controlled_generation_authorization_required"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "preview_correction_plan_required"
    },
    "heavy_blur": {
        "defect_id": "heavy_blur",
        "severity": "blocker",
        "downstream_repairability": "requires_controlled_regeneration",
        "allowed_fix_paths": [
            "controlled_retry_or_generation_authorization_required"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "bad_face_eyes_mouth_artifacts": {
        "defect_id": "bad_face_eyes_mouth_artifacts",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_identity_constraints",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "anatomy_defects": {
        "defect_id": "anatomy_defects",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_anatomy_constraints",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "hand_defects": {
        "defect_id": "hand_defects",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "identity_drift": {
        "defect_id": "identity_drift",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_identity_constraints",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "style_mismatch": {
        "defect_id": "style_mismatch",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_style_constraints",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "low_detail": {
        "defect_id": "low_detail",
        "severity": "medium",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_detail_enhancement",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "wrong_object_props": {
        "defect_id": "wrong_object_props",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "bad_composition": {
        "defect_id": "bad_composition",
        "severity": "medium",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_regeneration_with_composition_constraints",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_retry_or_generation_authorization_required"
    },
    "subtitle_overlap": {
        "defect_id": "subtitle_overlap",
        "severity": "medium",
        "downstream_repairability": "repairable_with_timeline_repair",
        "allowed_fix_paths": [
            "timeline_segment_repair",
            "subtitle_position_adjustment"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "preview_correction_plan_required"
    },
    "bad_transition_fade": {
        "defect_id": "bad_transition_fade",
        "severity": "medium",
        "downstream_repairability": "repairable_with_timeline_repair",
        "allowed_fix_paths": [
            "timeline_segment_repair",
            "transition_adjustment"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "preview_correction_plan_required"
    },
    "audio_voice_mismatch": {
        "defect_id": "audio_voice_mismatch",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "voice_regeneration",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "voice_generation_authorization_required"
    },
    "fake_operator_decision": {
        "defect_id": "fake_operator_decision",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "operator_visual_review_required"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "operator_visual_review_required"
    },
    "missing_asset": {
        "defect_id": "missing_asset",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "controlled_asset_resolution",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "controlled_asset_resolution_required"
    },
    "manifest_filesystem_contradiction": {
        "defect_id": "manifest_filesystem_contradiction",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "manifest_reconciliation",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "manifest_reconciliation_required"
    },
    "technical_only_pass_treated_as_visual_pass": {
        "defect_id": "technical_only_pass_treated_as_visual_pass",
        "severity": "blocker",
        "downstream_repairability": "not_repairable_downstream",
        "allowed_fix_paths": [
            "visual_qa_reexecution",
            "operator_review"
        ],
        "forbidden_next_stages": [
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance"
        ],
        "qa_decision": "blocked",
        "required_fix_stage": "visual_qa_reexecution_required"
    },
}

# ---------------------------------------------------------------------------
# Repair tool registry
# ---------------------------------------------------------------------------

REPAIR_TOOL_REGISTRY: List[Dict[str, Any]] = [
    {
        "tool_id": "standard_comfyui_inpaint",
        "tool_type": "standard_node_workflow",
        "available": True,
        "validated": False,
        "can_fix": [
            "small_local_artifact",
            "minor_background_defect"
        ],
        "cannot_fix": [
            "global_identity_drift",
            "bad_full_body_anatomy",
            "empty_timeline",
            "fake_operator_decision"
        ],
        "requires_gate": True
    },
    {
        "tool_id": "timeline_segment_repair",
        "tool_type": "editorial_repair",
        "available": True,
        "validated": True,
        "can_fix": [
            "empty_timeline",
            "duplicate_static_frames_if_assets_available",
            "subtitle_overlap",
            "bad_transition_fade"
        ],
        "requires_preview_rerender_gate": True
    },
    {
        "tool_id": "identity_adapter_sdxl_faceid",
        "tool_type": "custom_node",
        "available": False,
        "validated": False,
        "can_fix": [
            "identity_drift"
        ],
        "cannot_fix": [
            "bad_full_body_anatomy",
            "empty_timeline",
            "fake_operator_decision"
        ],
        "requires_controlled_asset_resolution": True
    },
    {
        "tool_id": "controlled_regeneration",
        "tool_type": "generation_workflow",
        "available": True,
        "validated": True,
        "can_fix": [
            "heavy_blur",
            "bad_face_eyes_mouth_artifacts",
            "anatomy_defects",
            "hand_defects",
            "style_mismatch",
            "low_detail",
            "wrong_object_props",
            "bad_composition"
        ],
        "requires_generation_gate": True
    }
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_repairability_classes() -> List[str]:
    """Return the list of repairability classes."""
    return list(REPAIRABILITY_CLASSES)


def get_defect_repairability_matrix() -> Dict[str, Dict[str, Any]]:
    """Return the full defect-to-repairability matrix."""
    return dict(DEFECT_REPAIRABILITY_MATRIX)


def get_defect_repairability(defect_id: str) -> Dict[str, Any] | None:
    """Return repairability info for a specific defect."""
    return DEFECT_REPAIRABILITY_MATRIX.get(defect_id)


def get_repair_tool_registry() -> List[Dict[str, Any]]:
    """Return the full repair tool registry."""
    return list(REPAIR_TOOL_REGISTRY)


def get_repair_tool(tool_id: str) -> Dict[str, Any] | None:
    """Return a specific repair tool or None."""
    for tool in REPAIR_TOOL_REGISTRY:
        if tool["tool_id"] == tool_id:
            return dict(tool)
    return None


def is_tool_available_and_validated(tool_id: str) -> bool:
    """Check if a repair tool is both available AND validated."""
    tool = get_repair_tool(tool_id)
    if tool is None:
        return False
    return tool.get("available", False) and tool.get("validated", False)


def can_defect_be_fixed_by_tool(defect_id: str, tool_id: str) -> bool:
    """Check if a defect can be fixed by a specific tool."""
    tool = get_repair_tool(tool_id)
    if tool is None:
        return False
    return defect_id in tool.get("can_fix", [])


def assess_repairability(
    defects: List[str],
    available_tools: List[str] | None = None
) -> Dict[str, Any]:
    """Assess whether detected defects can be repaired downstream.
    
    Returns:
        - all_defects_repairable_before_next_stage: bool
        - unrepairable_defects: list of defect IDs
        - unknown_repairability_defects: list of defect IDs
        - required_fix_stage: str
        - allowed_next_stage: str
        - blocked_next_stages: list of stage names
    """
    if available_tools is None:
        available_tools = [
            t["tool_id"] for t in REPAIR_TOOL_REGISTRY
            if t.get("available", False) and t.get("validated", False)
        ]
    
    unrepairable_defects: List[str] = []
    unknown_repairability_defects: List[str] = []
    required_fix_stages: set = set()
    blocked_stages: set = set()
    
    for defect_id in defects:
        repair_info = get_defect_repairability(defect_id)
        
        if repair_info is None:
            unknown_repairability_defects.append(defect_id)
            blocked_stages.update([
                "voice_generation",
                "assembly",
                "downstream",
                "production_acceptance"
            ])
            continue
        
        downstream_repairability = repair_info.get("downstream_repairability")
        
        # Check if defect is not repairable downstream
        if downstream_repairability in [
            "not_repairable_downstream",
            "unknown_repairability_blocked"
        ]:
            unrepairable_defects.append(defect_id)
            blocked_stages.update(repair_info.get("forbidden_next_stages", []))
        
        # Check if repair requires custom nodes that are not available/validated
        if downstream_repairability == "repairable_with_custom_nodes":
            # Check if required custom nodes are available and validated
            required_tools = repair_info.get("allowed_fix_paths", [])
            for tool_id in required_tools:
                if not is_tool_available_and_validated(tool_id):
                    unrepairable_defects.append(defect_id)
                    blocked_stages.update(repair_info.get("forbidden_next_stages", []))
                    break
        
        # Collect required fix stage
        fix_stage = repair_info.get("required_fix_stage")
        if fix_stage:
            required_fix_stages.add(fix_stage)
    
    # Determine if all defects are repairable
    all_repairable = (
        len(unrepairable_defects) == 0 and
        len(unknown_repairability_defects) == 0
    )
    
    # Determine allowed next stage
    if all_repairable and required_fix_stages:
        allowed_next_stage = list(required_fix_stages)[0]
    elif unrepairable_defects or unknown_repairability_defects:
        allowed_next_stage = "blocked_unrepairable_quality_failure"
    else:
        allowed_next_stage = "next_authorization_gate"
    
    return {
        "all_defects_repairable_before_next_stage": all_repairable,
        "unrepairable_defects": unrepairable_defects,
        "unknown_repairability_defects": unknown_repairability_defects,
        "required_fix_stage": list(required_fix_stages)[0] if required_fix_stages else "",
        "allowed_next_stage": allowed_next_stage,
        "blocked_next_stages": sorted(list(blocked_stages)),
    }


def apply_stage_routing_policy(repairability_assessment: Dict[str, Any]) -> str:
    """Apply stage routing policy based on repairability assessment.
    
    Returns the next action/state.
    """
    allowed_next_stage = repairability_assessment.get("allowed_next_stage", "")
    required_fix_stage = repairability_assessment.get("required_fix_stage", "")
    
    routing_policy = {
        "preview_correction_plan_required": "preview_correction_plan_required",
        "controlled_node_asset_resolution_required": "controlled_node_asset_resolution_required",
        "custom_node_repair_authorization_required": "custom_node_repair_authorization_required",
        "controlled_retry_or_generation_authorization_required": "controlled_retry_or_generation_authorization_required",
        "operator_visual_review_required": "operator_visual_review_required",
        "voice_generation_authorization_required": "voice_generation_authorization_required",
        "controlled_asset_resolution_required": "controlled_asset_resolution_required",
        "manifest_reconciliation_required": "manifest_reconciliation_required",
        "visual_qa_reexecution_required": "visual_qa_reexecution_required",
        "blocked_unrepairable_quality_failure": "blocked_unrepairable_quality_failure",
        "next_authorization_gate": "controlled_preview_rerender_authorization_required",
    }
    
    return routing_policy.get(
        required_fix_stage or allowed_next_stage,
        "blocked_unrepairable_quality_failure"
    )
