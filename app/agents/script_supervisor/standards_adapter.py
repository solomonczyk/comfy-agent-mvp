"""Standards adapter for Script Supervisor.

Connects the Script Supervisor to the standards integration layer so that
all findings reference standard_id, policy_id, rule_id, role, severity, and decision.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.standards import StandardsIntegration, StandardsTraceability


class ScriptSupervisorStandardsAdapter:
    """Adapts standards integration for the script_supervisor role."""

    ROLE = "script_supervisor"
    SOURCE_ARTIFACT = "roles/script_supervisor_standard.json"

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.integration = StandardsIntegration(self.project_root)
        self.traceability = StandardsTraceability(self.project_root)
        self._pack_loaded = False

    def load_standards(self) -> Dict[str, Any]:
        """Load standards pack and return load result."""
        result = self.integration.load_standards_pack()
        self._pack_loaded = result.get("success", False)
        return result

    def get_traceable_finding(
        self,
        decision: str,
        severity: str,
        detail: str = "",
    ) -> Dict[str, Any]:
        """Return a traceable finding with standards references."""
        self._ensure_loaded()
        trace = self.traceability.trace(
            role=self.ROLE,
            decision=decision,
            severity=severity,
            source_artifact=self.SOURCE_ARTIFACT,
        )
        trace["detail"] = detail
        return trace

    def produce_role_decision(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Produce a role-specific decision via the policy engine."""
        self._ensure_loaded()
        return self.integration.produce_role_specific_decision(self.ROLE, conditions)

    def map_defect(self, defect_id: str) -> Dict[str, Any]:
        """Map a defect ID to severity."""
        self._ensure_loaded()
        return self.integration.map_defect_to_severity(defect_id)

    def map_severity(self, severity: str) -> Dict[str, Any]:
        """Map a severity level to a decision."""
        self._ensure_loaded()
        return self.integration.map_severity_to_decision(severity)

    def get_standards_version(self) -> str:
        """Return the loaded standards pack version."""
        return self.integration._pack_version

    def _ensure_loaded(self) -> None:
        if not self._pack_loaded:
            self.load_standards()
            self._pack_loaded = True
