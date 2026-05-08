"""Edit Decision Planner for Combine V2 editorial layer.

Produces an edit decision list (EDL) with operations that must have
apply_performed=False and requires_operator_review=True.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

VALID_OPERATIONS = {
    "insert_clip",
    "replace_segment",
    "overlay_clip",
    "add_subtitle",
    "apply_transition",
    "add_voiceover_placeholder",
    "create_preview_required_marker",
}

VALID_MODES = {"ripple", "overwrite", "overlay"}


@dataclass
class EditOperation:
    """A single edit decision operation."""

    operation_id: str = ""
    operation: str = ""
    anchor: str = ""
    mode: str = "ripple"
    apply_performed: bool = False
    requires_preview: bool = True
    requires_operator_review: bool = True

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.operation_id:
            errors.append("operation_id must be non-empty")
        if self.operation not in VALID_OPERATIONS:
            errors.append(
                f"operation must be one of {VALID_OPERATIONS}, got '{self.operation}'"
            )
        if self.mode not in VALID_MODES:
            errors.append(f"mode must be one of {VALID_MODES}, got '{self.mode}'")
        return errors


class EditDecisionPlanner:
    """Planner that builds an edit decision list.

    All operations start with apply_performed=False and
    requires_operator_review=True.
    """

    def __init__(self) -> None:
        self._operations: List[EditOperation] = []

    def add_operation(self, op: EditOperation) -> List[str]:
        errors = op.validate()
        if errors:
            return errors
        if op.apply_performed:
            return ["apply_performed must be False for new operations"]
        if not op.requires_operator_review:
            return ["requires_operator_review must be True for new operations"]
        self._operations.append(op)
        return []

    def list_operations(self) -> List[EditOperation]:
        return list(self._operations)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [asdict(op) for op in self._operations]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict_list(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict_list(cls, items: List[Dict[str, Any]]) -> "EditDecisionPlanner":
        planner = cls()
        for item in items:
            planner._operations.append(EditOperation(**item))
        return planner

    @classmethod
    def from_json(cls, text: str) -> "EditDecisionPlanner":
        return cls.from_dict_list(json.loads(text))
