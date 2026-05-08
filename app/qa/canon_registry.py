"""Canon registry — loads and merges universal + domain + task-specific canons.

Canons define the visual quality rules an output must satisfy.
The registry can load from canonical JSON files or use built-in defaults.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Built-in default canons (used when no file is available)
# ---------------------------------------------------------------------------

UNIVERSAL_CANON: Dict[str, Any] = {
    "canon_id": "universal_quality_v1",
    "applies_to": "all_visual_outputs",
    "must_have": [
        "readable_asset",
        "no_stub_asset",
        "sufficient_resolution",
        "main_subject_readable",
        "no_severe_blur",
        "no_major_artifact_corruption",
        "lighting_consistency",
        "perspective_consistency",
    ],
    "hard_reject_defects": [
        "stub_asset",
        "unreadable_asset",
        "severe_blur",
        "major_anatomy_failure",
        "major_object_deformation",
        "critical_uncanny_artifact",
    ],
}

HUMAN_FACE_CANON: Dict[str, Any] = {
    "canon_id": "human_face_photoreal_v1",
    "applies_to": "human_face_portrait",
    "critical_regions": [
        "eyes",
        "mouth",
        "teeth",
        "lips",
        "nose",
        "skin",
        "jawline",
    ],
    "hard_reject_defects": [
        "bad_teeth",
        "unnatural_mouth",
        "lip_teeth_boundary_failed",
        "facial_anatomy_failed",
        "synthetic_doll_like_face",
        "plastic_skin",
    ],
}

DOMAIN_CANONS: Dict[str, Dict[str, Any]] = {
    "human_face_portrait": HUMAN_FACE_CANON,
}


def load_canon_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a canon from a JSON file. Returns None if file is missing or invalid."""
    if not path or not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_universal_canon(canon_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load universal canon — from file if available, otherwise built-in default."""
    if canon_dir:
        file_path = canon_dir / "universal_quality_canon.json"
        loaded = load_canon_file(file_path)
        if loaded is not None:
            return loaded
    return dict(UNIVERSAL_CANON)


def load_domain_canon(domain: str, canon_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load a domain-specific canon.

    Tries file first (e.g. human_face_canon.json), falls back to built-in.
    """
    if canon_dir:
        domain_file = f"{domain.replace('_portrait', '')}_canon.json"
        # map human_face_portrait -> human_face_canon.json
        if domain == "human_face_portrait":
            domain_file = "human_face_canon.json"
        file_path = canon_dir / domain_file
        loaded = load_canon_file(file_path)
        if loaded is not None:
            return loaded

    return dict(DOMAIN_CANONS.get(domain, {}))


def merge_canons(
    universal: Dict[str, Any],
    domain: Dict[str, Any],
    task_contract: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge universal + domain + optional task-specific contract into one canon.

    The merged canon contains:
    - All must_have requirements (deduplicated)
    - All hard_reject_defects (deduplicated)
    - All critical_regions (deduplicated)
    - A canons_used list
    """
    merged: Dict[str, Any] = {
        "canon_id": f"{universal.get('canon_id', 'unknown')} + {domain.get('canon_id', 'none')}",
        "applies_to": domain.get("applies_to", universal.get("applies_to", "unknown")),
    }

    # Merge must_have
    must_have: List[str] = []
    seen: set = set()
    for item in universal.get("must_have", []):
        if item not in seen:
            must_have.append(item)
            seen.add(item)
    for item in domain.get("must_have", []):
        if item not in seen:
            must_have.append(item)
            seen.add(item)
    merged["must_have"] = must_have

    # Merge hard_reject_defects
    hard_reject: List[str] = []
    seen = set()
    for item in universal.get("hard_reject_defects", []):
        if item not in seen:
            hard_reject.append(item)
            seen.add(item)
    for item in domain.get("hard_reject_defects", []):
        if item not in seen:
            hard_reject.append(item)
            seen.add(item)
    merged["hard_reject_defects"] = hard_reject

    # Merge critical_regions
    regions: List[str] = []
    seen = set()
    for item in domain.get("critical_regions", []):
        if item not in seen:
            regions.append(item)
            seen.add(item)
    merged["critical_regions"] = regions

    # Track which canons were used
    merged["canons_used"] = []
    if universal.get("canon_id"):
        merged["canons_used"].append(universal["canon_id"])
    if domain.get("canon_id"):
        merged["canons_used"].append(domain["canon_id"])

    # Merge task-specific contract if provided
    if task_contract:
        merged["task_contract_used"] = True
        if "task_specific_requirements" in task_contract:
            merged["task_specific_requirements"] = task_contract["task_specific_requirements"]
        if task_contract.get("additional_defects"):
            for d in task_contract["additional_defects"]:
                if d not in merged["hard_reject_defects"]:
                    merged["hard_reject_defects"].append(d)

    return merged
