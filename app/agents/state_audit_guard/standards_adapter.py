"""State Audit Guard Standards Adapter — loads and applies standards pack.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class StateAuditStandardsAdapter:
    """Adapter for loading and applying state audit guard standards."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.standards_pack_dir = self.control_dir / "standards_pack"
        self._standards: Dict[str, Any] = {}
        self._standards_loaded = False

    def load_standards(self) -> None:
        """Load the state audit guard standard from the standards pack."""
        if self._standards_loaded:
            return

        standard_path = self.standards_pack_dir / "roles" / "state_audit_guard_standard.json"

        if standard_path.is_file():
            try:
                with open(standard_path, "r", encoding="utf-8") as f:
                    self._standards = json.load(f)
                self._standards_loaded = True
            except (json.JSONDecodeError, IOError):
                self._standards = {}
        else:
            self._standards = {}

    def get_standards_version(self) -> str:
        """Get the standards pack version."""
        self.load_standards()
        return self._standards.get("version", "1.0.0")

    def get_traceable_finding(
        self, decision: str, severity: str, detail: str
    ) -> Dict[str, Any]:
        """Generate a traceable finding with metadata."""
        return {
            "decision": decision,
            "severity": severity,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": "state_audit_guard",
            "traceable": True,
        }

    def get_forbidden_actions(self) -> list:
        """Get the list of forbidden actions from standards."""
        self.load_standards()
        return self._standards.get("forbidden_actions", [])

    def get_blocker_rules(self) -> list:
        """Get the blocker rules from standards."""
        self.load_standards()
        return self._standards.get("blocker_rules", [])

    def get_responsibilities(self) -> list:
        """Get the responsibilities from standards."""
        self.load_standards()
        return self._standards.get("responsibilities", [])
