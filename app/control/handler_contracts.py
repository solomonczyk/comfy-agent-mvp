"""MK-CTRL10 — Production handler contracts.

Structured payload and result dataclasses for production-safe handler adapters.
Every handler receives a HandlerPayload and every handler returns a HandlerResult.
Dry-validation mode is the default; real execution requires explicit double opt-in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandlerPayload:
    """Structured input passed to every production handler adapter."""

    episode_id: str
    shot_id: str
    action: str
    state_report: dict
    action_plan: dict
    dry_validate: bool = True
    allow_real_execution: bool = False
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "action": self.action,
            "state_report": self.state_report,
            "action_plan": self.action_plan,
            "dry_validate": self.dry_validate,
            "allow_real_execution": self.allow_real_execution,
            "extra": self.extra,
        }


@dataclass
class HandlerResult:
    """Structured output returned by every production handler adapter."""

    handler: str
    status: str  # "validated" | "mocked" | "executed" | "blocked" | "failed"
    would_execute: bool
    executed: bool
    reason: str
    artifacts: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "handler": self.handler,
            "status": self.status,
            "would_execute": self.would_execute,
            "executed": self.executed,
            "reason": self.reason,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }
