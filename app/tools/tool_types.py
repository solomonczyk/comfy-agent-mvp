"""Tool types for the internal tool layer.

Small, explicit data structures that every tool module emits. Kept dependency-
free so tests and tools can import this module without pulling in heavy
application layers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolStatus(str, Enum):
    """Result status for a single tool invocation."""

    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class ToolResult:
    """Single tool invocation record.

    Emitted to the ToolTrace by each tool module once the underlying call
    completes (successfully or not). `inputs_summary` and `outputs_summary`
    should be small, JSON-serializable summaries — not full payloads.
    """

    name: str
    status: ToolStatus
    inputs_summary: dict[str, Any] = field(default_factory=dict)
    outputs_summary: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    notes: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "name": self.name,
            "status": self.status.value if isinstance(self.status, ToolStatus) else self.status,
            "inputs_summary": self.inputs_summary,
            "outputs_summary": self.outputs_summary,
            "duration_ms": self.duration_ms,
            "notes": self.notes,
            "error": self.error,
        }
