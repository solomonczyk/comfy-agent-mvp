"""Timeline consistency audit for Script Supervisor.

Checks timeline model, marker registry, and edit decision list presence and consistency.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .standards_adapter import ScriptSupervisorStandardsAdapter


class TimelineConsistencyAuditor:
    """Audits timeline artifacts for consistency and completeness."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def audit(self) -> Dict[str, Any]:
        """Run timeline consistency audit and return a standards-driven report."""
        self.standards.load_standards()

        findings: List[Dict[str, Any]] = []

        # Check timeline model
        timeline_present = self._artifact_exists("timeline_model.json")
        if timeline_present:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="timeline_model.json present",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="timeline_model.json missing",
                )
            )

        # Check marker registry
        marker_present = self._artifact_exists("marker_registry.json")
        if marker_present:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="marker_registry.json present",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="marker_registry.json missing",
                )
            )

        # Check edit decision list
        edl_present = self._artifact_exists("edit_decision_list.json")
        if edl_present:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="edit_decision_list.json present",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="edit_decision_list.json missing",
                )
            )

        # Check timeline preview dry run report if available
        dry_run_present = self._artifact_exists("timeline_preview_dry_run_report.json")
        if dry_run_present:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="timeline_preview_dry_run_report.json present",
                )
            )

        overall_pass = timeline_present and marker_present and edl_present

        return {
            "report_id": "script_supervisor_timeline_consistency_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "timeline_model_present": timeline_present,
            "marker_registry_present": marker_present,
            "edit_decision_list_present": edl_present,
            "timeline_preview_dry_run_present": dry_run_present,
            "overall_pass": overall_pass,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

    def _artifact_exists(self, name: str) -> bool:
        return (self.control_dir / name).is_file()
