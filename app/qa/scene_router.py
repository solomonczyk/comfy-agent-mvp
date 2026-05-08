"""Scene router — classifies image scene type from metadata and task context.

This is intentionally simple: it uses existing metadata fields and the
task contract to route to an appropriate domain canon. No ML inference.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

SUPPORTED_SCENE_TYPES = [
    "human_face_portrait",
    "unknown",
]

# Keywords in task contract or metadata that hint at scene type
SCENE_KEYWORDS: Dict[str, list] = {
    "human_face_portrait": [
        "portrait",
        "face",
        "headshot",
        "close-up",
        "closeup",
        "facial",
        "person",
        "character",
        "human",
        "elderly",
        "woman",
        "man",
        "people",
        "photoreal",
    ],
}


def classify_scene_type(
    candidate_version: str,
    task_contract: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Classify the scene type for a given candidate.

    Uses, in order:
    1. Explicit scene_type in task_contract
    2. Task description / subject clues in task_contract
    3. Metadata hints (e.g. filename, description)
    4. Default to 'human_face_portrait' for known character workflows

    For the current V12/V13 workflow, we default to human_face_portrait
    since we are in a character photoreal pipeline.
    """
    # If task_contract explicitly says scene_type, use it
    if task_contract and task_contract.get("scene_type"):
        scene_type = task_contract["scene_type"]
        if scene_type in SUPPORTED_SCENE_TYPES:
            return scene_type

    # Check for keyword hints in task_contract
    if task_contract:
        text_to_check = " ".join([
            str(task_contract.get("task_description", "")),
            str(task_contract.get("subject", "")),
            str(task_contract.get("prompt_hint", "")),
            str(candidate_version),
        ]).lower()

        for scene_type, keywords in SCENE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_to_check:
                    return scene_type

    # Check metadata
    if metadata:
        text_to_check = " ".join([
            str(metadata.get("description", "")),
            str(metadata.get("filename", "")),
            str(metadata.get("prompt", "")),
        ]).lower()

        for scene_type, keywords in SCENE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_to_check:
                    return scene_type

    # Default for V12/V13 character pipeline
    if "v12" in candidate_version or "v13" in candidate_version:
        return "human_face_portrait"

    return "unknown"


def get_supported_scene_types() -> list:
    """Return list of supported scene types."""
    return list(SUPPORTED_SCENE_TYPES)
