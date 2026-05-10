"""Contact sheet audit for Script Supervisor.

Validates contact sheet usefulness and whether it proves scene development.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .standards_adapter import ScriptSupervisorStandardsAdapter


class ContactSheetAuditor:
    """Audits contact sheet validity and usefulness."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.preview_dir = self.project_root / "output" / "preview"
        self.control_dir = self.project_root / "output" / "control"
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def audit(self, duplicate_static_ratio: float = 0.0) -> Dict[str, Any]:
        """Run contact sheet audit and return a standards-driven report."""
        self.standards.load_standards()

        findings: List[Dict[str, Any]] = []

        contact_sheet_path = self.preview_dir / "contact_sheet.jpg"
        contact_sheet_found = contact_sheet_path.is_file()

        if contact_sheet_found:
            # Contact sheet exists, but is it useful?
            if duplicate_static_ratio >= 0.5:
                useful = False
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="operator_review_required",
                        severity="warning",
                        detail="Contact sheet exists but high duplicate ratio makes it insufficient to prove scene development",
                    )
                )
            else:
                useful = True
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="pass",
                        severity="info",
                        detail="Contact sheet exists and duplicate ratio is acceptable — useful for scene development proof",
                    )
                )
        else:
            useful = False
            findings.append(
                self.standards.get_traceable_finding(
                    decision="operator_review_required",
                    severity="warning",
                    detail="Contact sheet not found — cannot validate scene development visually",
                )
            )

        # Also check for contact_sheet_source_map if available
        source_map_path = self.control_dir / "contact_sheet_source_map_v3.json"
        source_map_present = source_map_path.is_file()

        return {
            "report_id": "script_supervisor_contact_sheet_audit_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "contact_sheet_found": contact_sheet_found,
            "contact_sheet_useful": useful,
            "contact_sheet_usefulness_checked": True,
            "contact_sheet_source_map_present": source_map_present,
            "duplicate_static_ratio_at_audit": duplicate_static_ratio,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }
