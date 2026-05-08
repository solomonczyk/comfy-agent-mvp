"""Defect taxonomy — normalized defect IDs for the QA Canon Engine.

All defects map to stable identifiers shared across universal canons,
domain canons, and decision policies.
"""

from __future__ import annotations

from typing import Dict, List

DEFECT_TAXONOMY: Dict[str, Dict] = {
    # --- Universal defects ---
    "stub_asset": {
        "id": "stub_asset",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Asset is a stub (zero bytes, unreadable, or placeholder)",
    },
    "unreadable_asset": {
        "id": "unreadable_asset",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Asset file cannot be opened or decoded as an image",
    },
    "severe_blur": {
        "id": "severe_blur",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Image exhibits severe blur making details unrecognizable",
    },
    "major_anatomy_failure": {
        "id": "major_anatomy_failure",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Major anatomical deformation or missing body part",
    },
    "major_object_deformation": {
        "id": "major_object_deformation",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Major object deformation or structural failure",
    },
    "critical_uncanny_artifact": {
        "id": "critical_uncanny_artifact",
        "domain": "universal",
        "severity": "hard_reject",
        "description": "Uncanny valley artifact rendering output unusable",
    },
    "artifact_corruption": {
        "id": "artifact_corruption",
        "domain": "universal",
        "severity": "medium",
        "description": "Visible artifact corruption in the image",
    },
    "low_micro_detail": {
        "id": "low_micro_detail",
        "domain": "universal",
        "severity": "medium",
        "description": "Insufficient micro-detail and texture fidelity",
    },
    "blur": {
        "id": "blur",
        "domain": "universal",
        "severity": "medium",
        "description": "Noticeable blur reducing perceived sharpness",
    },
    "composition_failed": {
        "id": "composition_failed",
        "domain": "universal",
        "severity": "medium",
        "description": "Poor composition or framing",
    },
    # --- Human face domain defects ---
    "bad_teeth": {
        "id": "bad_teeth",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "Malformed, merged, or unrealistic teeth",
    },
    "unnatural_mouth": {
        "id": "unnatural_mouth",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "Unnatural mouth shape or expression",
    },
    "lip_teeth_boundary_failed": {
        "id": "lip_teeth_boundary_failed",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "Missing or unnatural lip-teeth boundary",
    },
    "facial_anatomy_failed": {
        "id": "facial_anatomy_failed",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "General facial anatomy failure",
    },
    "synthetic_doll_like_face": {
        "id": "synthetic_doll_like_face",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "Face has a synthetic, doll-like appearance",
    },
    "plastic_skin": {
        "id": "plastic_skin",
        "domain": "human_face",
        "severity": "hard_reject",
        "description": "Skin appears plastic, waxy, or lacks realistic microtexture",
    },
    # --- Borderline / operator review defects ---
    "borderline_skin_texture": {
        "id": "borderline_skin_texture",
        "domain": "human_face",
        "severity": "operator_review",
        "description": "Skin texture is borderline — may need operator review",
    },
    "minor_blur": {
        "id": "minor_blur",
        "domain": "universal",
        "severity": "operator_review",
        "description": "Minor blur that may or may not be acceptable",
    },
    "style_uncertainty": {
        "id": "style_uncertainty",
        "domain": "universal",
        "severity": "operator_review",
        "description": "Style or rendering uncertainty requiring operator judgment",
    },
}


def get_defect_taxonomy() -> Dict[str, Dict]:
    """Return the full defect taxonomy."""
    return dict(DEFECT_TAXONOMY)


def get_defect(defect_id: str) -> Dict | None:
    """Return a single defect definition or None."""
    return DEFECT_TAXONOMY.get(defect_id)


def get_defects_by_domain(domain: str) -> Dict[str, Dict]:
    """Return all defects for a given domain (e.g. 'universal', 'human_face')."""
    return {k: v for k, v in DEFECT_TAXONOMY.items() if v["domain"] == domain}


def get_defects_by_severity(severity: str) -> Dict[str, Dict]:
    """Return all defects at a given severity level."""
    return {k: v for k, v in DEFECT_TAXONOMY.items() if v["severity"] == severity}


def map_operator_feedback_to_defects(operator_feedback: str) -> List[str]:
    """Map free-text operator feedback to known defect IDs.

    Uses keyword matching. Returns a list of matched defect IDs.
    """
    feedback_lower = operator_feedback.lower()
    matched: List[str] = []

    keyword_map = {
        "teeth": "bad_teeth",
        "tooth": "bad_teeth",
        "mouth": "unnatural_mouth",
        "lip": "lip_teeth_boundary_failed",
        "lips": "lip_teeth_boundary_failed",
        "doll": "synthetic_doll_like_face",
        "plastic": "plastic_skin",
        "skin": "borderline_skin_texture",
        "blur": "blur",
        "blurry": "blur",
        "artifact": "artifact_corruption",
        "corrupt": "artifact_corruption",
        "anatomy": "facial_anatomy_failed",
        "uncanny": "critical_uncanny_artifact",
        "deform": "major_anatomy_failure",
        "composition": "composition_failed",
        "detail": "low_micro_detail",
    }

    seen: set = set()
    for keyword, defect_id in keyword_map.items():
        if keyword in feedback_lower and defect_id not in seen:
            matched.append(defect_id)
            seen.add(defect_id)

    return matched
