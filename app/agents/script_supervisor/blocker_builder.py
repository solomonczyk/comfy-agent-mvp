"""Blocker builder for Script Supervisor.

Builds blocker packets, operator review packets, and readiness reports
based on all audit findings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .standards_adapter import ScriptSupervisorStandardsAdapter


class BlockerBuilder:
    """Builds blocker and operator review packets from audit findings."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def build_blocker_packet(
        self,
        findings: List[Dict[str, Any]],
        blocker_reasons: List[str],
    ) -> Dict[str, Any]:
        """Build a blocker packet if preview is invalid/static."""
        self.standards.load_standards()

        traceable = self.standards.get_traceable_finding(
            decision="blocked",
            severity="blocker",
            detail="; ".join(blocker_reasons) if blocker_reasons else "Preview audit blocker",
        )

        return {
            "report_id": "script_supervisor_blocker_packet",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "blocker_type": "invalid_or_static_preview",
            "blocker_detected": True,
            "blocker_reasons": blocker_reasons,
            "next_allowed_action": "preview_correction_plan_required",
            "production_accepted": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "traceable_finding": traceable,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

    def build_operator_review_packet(
        self,
        findings: List[Dict[str, Any]],
        review_reasons: List[str],
    ) -> Dict[str, Any]:
        """Build an operator review packet if artifacts are insufficient."""
        self.standards.load_standards()

        traceable = self.standards.get_traceable_finding(
            decision="operator_review_required",
            severity="warning",
            detail="; ".join(review_reasons) if review_reasons else "Operator review required",
        )

        return {
            "report_id": "script_supervisor_operator_review_packet",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "operator_review_required": True,
            "review_reasons": review_reasons,
            "next_allowed_action": "script_supervisor_operator_review_required",
            "production_accepted": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "traceable_finding": traceable,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

    def build_readiness_report(
        self,
        audit_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build overall readiness report from all audit results."""
        self.standards.load_standards()

        # Determine overall state
        has_blocker = audit_results.get("blocker_detected", False)
        operator_review = audit_results.get("operator_review_required", False)

        if has_blocker:
            current_state = "preview_correction_plan_required"
            next_allowed_action = "preview_correction_plan_required"
        elif operator_review:
            current_state = "script_supervisor_operator_review_required"
            next_allowed_action = "script_supervisor_operator_review_required"
        else:
            current_state = "script_supervisor_operator_review_required"
            next_allowed_action = "script_supervisor_operator_review_required"

        return {
            "report_id": "script_supervisor_readiness_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "blocker_detected": has_blocker,
            "operator_review_required": operator_review,
            "production_accepted": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "audit_results": audit_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }
