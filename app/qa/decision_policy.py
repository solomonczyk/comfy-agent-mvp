"""Visual QA decision policy — determines reject / operator_review / candidate_ok.

The policy is driven by the merged canon's hard_reject_defects and a
configurable decision policy (loaded from file or built-in default).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Built-in default decision policy
# ---------------------------------------------------------------------------

DEFAULT_DECISION_POLICY: Dict[str, Any] = {
    "policy_id": "visual_qa_decision_policy_v1",
    "auto_reject_if": [
        "bad_teeth",
        "unnatural_mouth",
        "lip_teeth_boundary_failed",
        "facial_anatomy_failed",
        "synthetic_doll_like_face",
    ],
    "operator_review_if": [
        "borderline_skin_texture",
        "minor_blur",
        "style_uncertainty",
    ],
    "production_accepted_allowed": False,
}


def load_decision_policy(policy_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load decision policy from file, or return built-in default."""
    if policy_dir:
        file_path = policy_dir / "visual_qa_decision_policy.json"
        if file_path and file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    return dict(DEFAULT_DECISION_POLICY)


def apply_decision_policy(
    policy: Dict[str, Any],
    critical_failures: List[str],
    all_detected_defects: List[str],
) -> Dict[str, Any]:
    """Apply the decision policy against detected defects.

    Returns a structured decision with:
    - decision: "reject" | "operator_review_required" | "candidate_ok_for_pipeline_review"
    - auto_rejected_by: list of defect IDs that triggered auto-reject
    - operator_review_by: list of defect IDs that triggered operator review
    - production_accepted: always False
    - assembly_allowed: always False
    - downstream_allowed: always False
    """
    auto_reject_if = policy.get("auto_reject_if", [])
    operator_review_if = policy.get("operator_review_if", [])

    auto_rejected_by: List[str] = []
    operator_review_by: List[str] = []

    for defect_id in all_detected_defects:
        if defect_id in auto_reject_if:
            auto_rejected_by.append(defect_id)
        elif defect_id in operator_review_if:
            if defect_id not in operator_review_by:
                operator_review_by.append(defect_id)

    # Also check critical_failures explicitly
    for defect_id in critical_failures:
        if defect_id in auto_reject_if and defect_id not in auto_rejected_by:
            auto_rejected_by.append(defect_id)

    # Determine decision
    if auto_rejected_by:
        decision = "reject"
        recommended = "v13_correction_plan_required"
    elif operator_review_by:
        decision = "operator_review_required"
        recommended = "operator_visual_review_required"
    else:
        decision = "candidate_ok_for_pipeline_review"
        recommended = "pipeline_review_required"

    return {
        "decision": decision,
        "auto_rejected_by": auto_rejected_by,
        "operator_review_by": operator_review_by,
        "critical_failures": critical_failures,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "recommended_next_action": recommended,
    }
