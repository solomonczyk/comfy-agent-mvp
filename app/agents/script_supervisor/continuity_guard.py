"""Continuity Guard — orchestrates all Script Supervisor audits.

Guards against fake operator decisions, blocked downstream states, and
ensures production_accepted remains false.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .standards_adapter import ScriptSupervisorStandardsAdapter


class ContinuityGuard:
    """Orchestrates continuity audits and guards forbidden states."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def audit_fake_operator_decision_absence(self) -> Dict[str, Any]:
        """Check that no fake operator decision exists."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        fake_detected = False
        human_decision_found = False
        artifacts_checked = []

        # Check post_preview_routing_decision.json
        routing_path = self.control_dir / "post_preview_routing_decision.json"
        if routing_path.is_file():
            artifacts_checked.append("post_preview_routing_decision.json")
            try:
                with open(routing_path, "r", encoding="utf-8") as f:
                    rd = json.load(f)
                decision_valid = rd.get("decision_valid", False)
                op_review = rd.get("visual_review_performed_by_operator", False)
                selected = rd.get("selected_branch", "")
                if not decision_valid and not op_review:
                    fake_detected = True
                elif selected == "invalid_agent_generated_decision":
                    fake_detected = True
                elif decision_valid and op_review:
                    human_decision_found = True
            except (json.JSONDecodeError, IOError):
                pass

        # Check reconciliation artifact
        recon_path = self.control_dir / "post_preview_operator_decision_reconciliation.json"
        if recon_path.is_file():
            artifacts_checked.append("post_preview_operator_decision_reconciliation.json")
            try:
                with open(recon_path, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                if rec.get("detection", {}).get("agent_may_not_choose_verdict_violation"):
                    fake_detected = True
            except (json.JSONDecodeError, IOError):
                pass

        # Check preview_operator_decision_input.json
        decision_input_path = self.control_dir / "preview_operator_decision_input.json"
        if decision_input_path.is_file():
            artifacts_checked.append("preview_operator_decision_input.json")
            try:
                with open(decision_input_path, "r", encoding="utf-8") as f:
                    di = json.load(f)
                source = di.get("operator_id") or di.get("source", "")
                if source and source not in ("agent", "cli_verification"):
                    human_decision_found = True
            except (json.JSONDecodeError, IOError):
                pass

        if fake_detected:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="Fake operator decision detected and invalidated",
                )
            )
        elif not human_decision_found:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="operator_review_required",
                    severity="warning",
                    detail="No human operator decision found — operator review required",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="Human operator decision verified",
                )
            )

        return {
            "report_id": "script_supervisor_fake_decision_audit",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "fake_operator_decision_checked": True,
            "fake_operator_decision_detected": fake_detected,
            "human_operator_decision_found": human_decision_found,
            "artifacts_checked": artifacts_checked,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

    def audit_downstream_blocked_state(self) -> Dict[str, Any]:
        """Check downstream blocked state and ensure voice/assembly/downstream are blocked."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        # Read current state from artifact_index if present
        index_path = self.control_dir / "artifact_index.json"
        state = {}
        if index_path.is_file():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        production_accepted = state.get("production_accepted", False)
        voice_generation_ready = state.get("voice_generation_ready", False)
        assembly_allowed = state.get("assembly_allowed", False)
        downstream_allowed = state.get("downstream_allowed", False)

        if production_accepted:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="production_accepted is true — script supervisor cannot allow this without operator review",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="production_accepted is false — correct",
                )
            )

        if voice_generation_ready:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="voice_generation_ready is true — script supervisor recommends operator review before voice",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="voice_generation_ready is false — blocked as expected",
                )
            )

        if assembly_allowed:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="assembly_allowed is true — script supervisor recommends operator review",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="assembly_allowed is false — blocked as expected",
                )
            )

        if downstream_allowed:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="downstream_allowed is true — script supervisor recommends operator review",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="downstream_allowed is false — blocked as expected",
                )
            )

        return {
            "report_id": "script_supervisor_downstream_guard_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "downstream_guard_checked": True,
            "voice_generation_blocked_checked": True,
            "production_accepted_false_checked": True,
            "production_accepted": production_accepted,
            "voice_generation_ready": voice_generation_ready,
            "assembly_allowed": assembly_allowed,
            "downstream_allowed": downstream_allowed,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

    def audit_path_consistency(self) -> Dict[str, Any]:
        """Audit path consistency between expected and actual output paths."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        preview_dir = self.project_root / "output" / "preview"
        previews_dir = self.project_root / "output" / "previews"
        assets_dir = self.project_root / "output" / "assets"

        mismatches = []
        if previews_dir.exists() and preview_dir.exists():
            mismatches.append("Both output/preview and output/previews exist")

        if not preview_dir.exists() and not previews_dir.exists():
            mismatches.append("Neither output/preview nor output/previews exists")

        if mismatches:
            for m in mismatches:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="warning",
                        severity="warning",
                        detail=m,
                    )
                )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="Preview path consistency ok",
                )
            )

        return {
            "report_id": "script_supervisor_path_consistency_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "path_consistency_checked": True,
            "mismatches": mismatches,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }
