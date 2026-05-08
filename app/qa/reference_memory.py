"""Reference memory — stores positive/negative reference metadata.

This module does NOT copy or store actual image assets. It stores metadata
pointers (asset paths) with labels and defect information.

The memory is persisted as JSON files and can be loaded/updated.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_operator_feedback_memory(feedback_dir: Path) -> Dict[str, Any]:
    """Load operator feedback memory from JSON file."""
    path = feedback_dir / "operator_feedback_memory.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "feedback_entries": [],
    }


def save_operator_feedback_memory(feedback_dir: Path, memory: Dict[str, Any]) -> None:
    """Save operator feedback memory to JSON file."""
    feedback_dir.mkdir(parents=True, exist_ok=True)
    path = feedback_dir / "operator_feedback_memory.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def add_feedback_entry(
    feedback_dir: Path,
    candidate_version: str,
    asset_path: str,
    label: str,
    failed_regions: Optional[List[str]] = None,
    defects: Optional[List[str]] = None,
    operator_comment: str = "",
) -> Dict[str, Any]:
    """Add a new feedback entry to the operator feedback memory."""
    memory = load_operator_feedback_memory(feedback_dir)
    entries = memory.setdefault("feedback_entries", [])

    entry = {
        "candidate_version": candidate_version,
        "asset_path": asset_path,
        "label": label,
        "failed_regions": failed_regions or [],
        "defects": defects or [],
        "operator_comment": operator_comment,
        "timestamp": datetime.now().isoformat(),
    }
    entries.append(entry)

    save_operator_feedback_memory(feedback_dir, memory)
    return entry


def get_negative_references(feedback_dir: Path) -> List[Dict[str, Any]]:
    """Get all negative reference entries from feedback memory."""
    memory = load_operator_feedback_memory(feedback_dir)
    return [e for e in memory.get("feedback_entries", []) if e.get("label") == "negative"]


def get_positive_references(feedback_dir: Path) -> List[Dict[str, Any]]:
    """Get all positive reference entries from feedback memory."""
    memory = load_operator_feedback_memory(feedback_dir)
    return [e for e in memory.get("feedback_entries", []) if e.get("label") == "positive"]


def save_negative_reference(
    ref_dir: Path,
    candidate_version: str,
    asset_path: str,
    failed_regions: Optional[List[str]] = None,
    defects: Optional[List[str]] = None,
    operator_comment: str = "",
) -> Dict[str, Any]:
    """Save a negative reference metadata file.

    Creates a JSON file in the negative references directory.
    """
    neg_dir = ref_dir / "negative"
    neg_dir.mkdir(parents=True, exist_ok=True)

    reference = {
        "candidate_version": candidate_version,
        "asset_path": asset_path,
        "label": "negative",
        "failed_regions": failed_regions or [],
        "defects": defects or [],
        "operator_comment": operator_comment,
        "timestamp": datetime.now().isoformat(),
    }

    filename = f"{candidate_version}_bad_teeth_reference.json".replace(" ", "_")
    path = neg_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(reference, f, indent=2)

    return reference
