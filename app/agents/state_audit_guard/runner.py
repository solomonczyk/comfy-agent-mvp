"""State Audit Guard Runner - CLI runner for the agent.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .artifacts import StateAuditGuardArtifacts
from .contract import StateAuditGuardContract
from .validator import StateAuditGuardValidator


class StateAuditGuardRunner:
    """Runner for the State Audit Guard agent."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.validator = StateAuditGuardValidator(self.project_root)
        self.artifacts = StateAuditGuardArtifacts(self.project_root)

    def run(self) -> Dict[str, Any]:
        """Execute the full state audit guard run."""
        # Run all validations
        validation_results = self.validator.run_all_validations()

        # Determine verdict and next state
        has_blocker = validation_results["has_blocker"]
        verdict = validation_results["verdict"]

        if has_blocker:
            next_state = "state_audit_blocker_resolution_required"
            next_action = "state_audit_blocker_resolution_required"
        else:
            next_state = "production_gate_review_required"
            next_action = "production_gate_review_required"

        # Generate all artifacts
        self.artifacts.generate_all_artifacts(validation_results, verdict, next_state, next_action)

        # Update canonical files
        self.artifacts.update_artifact_index(verdict, next_state, next_action)
        self.artifacts.update_episode_ledger(verdict, next_state, next_action)
        self.artifacts.update_state(next_state, next_action)

        return {
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "next_state": next_state,
            "next_action": next_action,
            "has_blocker": has_blocker,
            "blocker_count": validation_results["blocker_count"],
            "validation_results": validation_results,
            "traceable": True,
        }

    def inspect(self) -> Dict[str, Any]:
        """Inspect current state without making changes."""
        # Run all validations
        validation_results = self.validator.run_all_validations()

        return {
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inspection_only": True,
            "validation_results": validation_results,
            "traceable": True,
        }
