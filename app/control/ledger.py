"""MK-CTRL4 — Persistent shot execution ledger.

Records control events (inspect, gate decisions, actions) to JSON.
Does not trigger generation, ffmpeg, or TTS.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def compact_recipe_validation_for_ledger(recipe_validation: dict | None) -> dict | None:
    """Create a compact version of recipe_validation for ledger storage.
    
    Extracts only the essential fields to avoid storing large issue lists in the ledger.
    
    Args:
        recipe_validation: Full recipe_validation dict from ActionPlan
        
    Returns:
        Compact dict with verdict, recipe_id, score, settings_source, issue_codes, and summary
    """
    if recipe_validation is None:
        return None
    
    if not recipe_validation.get("available", False):
        # Return unavailable status as-is
        return {
            "available": False,
            "reason": recipe_validation.get("reason", "unknown"),
        }
    
    # Extract compact version
    issues = recipe_validation.get("issues", [])
    issue_codes = [issue.get("code") for issue in issues if issue.get("code")]
    
    compact = {
        "available": True,
        "settings_source": recipe_validation.get("settings_source"),
        "verdict": recipe_validation.get("verdict"),
        "recipe_id": recipe_validation.get("recipe_id"),
        "score": recipe_validation.get("score"),
        "issue_codes": issue_codes,
    }
    
    # Include summary if available
    summary = recipe_validation.get("summary")
    if summary:
        compact["summary"] = {
            "title": summary.get("title"),
            "risk_level": summary.get("risk_level"),
            "recommended_next_action": summary.get("recommended_next_action"),
        }
    
    return compact


@dataclass
class ShotLedgerRecord:
    timestamp: str
    episode_id: str
    shot_id: str
    event_type: str  # inspect, gate_decision, action_executed, action_denied, action_failed, action_blocked, state_transition
    requested_action: str | None = None
    allowed: bool | None = None
    executed: bool | None = None
    success: bool | None = None
    current_state: str | None = None
    expected_next_action: str | None = None
    reason: str | None = None
    handler_result: dict | None = None
    control_executed: bool | None = None
    production_executed: bool | None = None
    handler_status: str | None = None
    # MK-CTRL19 — State transition fields
    from_state: str | None = None
    to_state: str | None = None
    artifact_path: str | None = None
    # MK-RECIPE7 — Recipe validation evidence
    recipe_validation: dict | None = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "event_type": self.event_type,
            "requested_action": self.requested_action,
            "allowed": self.allowed,
            "executed": self.executed,
            "success": self.success,
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "reason": self.reason,
            "handler_result": self.handler_result,
            "control_executed": self.control_executed,
            "production_executed": self.production_executed,
            "handler_status": self.handler_status,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "artifact_path": self.artifact_path,
            "recipe_validation": self.recipe_validation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ShotLedgerRecord":
        return cls(
            timestamp=d["timestamp"],
            episode_id=d["episode_id"],
            shot_id=d["shot_id"],
            event_type=d["event_type"],
            requested_action=d.get("requested_action"),
            allowed=d.get("allowed"),
            executed=d.get("executed"),
            success=d.get("success"),
            current_state=d.get("current_state"),
            expected_next_action=d.get("expected_next_action"),
            reason=d.get("reason"),
            handler_result=d.get("handler_result"),
            control_executed=d.get("control_executed"),
            production_executed=d.get("production_executed"),
            handler_status=d.get("handler_status"),
            from_state=d.get("from_state"),
            to_state=d.get("to_state"),
            artifact_path=d.get("artifact_path"),
            recipe_validation=d.get("recipe_validation"),
        )


@dataclass
class ShotLedger:
    episode_id: str
    shot_id: str
    records: list[ShotLedgerRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ShotLedger":
        return cls(
            episode_id=d["episode_id"],
            shot_id=d["shot_id"],
            records=[ShotLedgerRecord.from_dict(r) for r in d.get("records", [])],
        )


class ShotLedgerStorage:
    """Persistent JSON storage for shot control events."""

    def __init__(self, root_dir: Path | str = ".") -> None:
        self.root = Path(root_dir)

    def ledger_path(self, episode_id: str, shot_id: str) -> Path:
        out_dir = self.root / "output" / "control"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"{episode_id}_{shot_id}_ledger.json"

    def exists(self, episode_id: str, shot_id: str) -> bool:
        return self.ledger_path(episode_id, shot_id).exists()

    def load(self, episode_id: str, shot_id: str) -> ShotLedger:
        path = self.ledger_path(episode_id, shot_id)
        if not path.exists():
            return ShotLedger(episode_id=episode_id, shot_id=shot_id)
        text = path.read_text(encoding="utf-8")
        return ShotLedger.from_dict(json.loads(text))

    def append(self, episode_id: str, shot_id: str, record: ShotLedgerRecord) -> Path:
        path = self.ledger_path(episode_id, shot_id)
        ledger = self.load(episode_id, shot_id)
        ledger.records.append(record)
        return self._atomic_write(path, ledger.to_dict())

    def _atomic_write(self, path: Path, data: dict) -> Path:
        """Write to temp then rename for atomicity."""
        fd, tmp = tempfile.mkstemp(
            dir=path.parent, prefix=path.stem + "_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
        return path
