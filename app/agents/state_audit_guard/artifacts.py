"""State Audit Guard Artifacts - generates required audit artifacts.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .contract import StateAuditGuardContract


class StateAuditGuardArtifacts:
    """Generates required audit artifacts."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.artifacts_dir = self.control_dir / "state_audit_guard"

    def generate_all_artifacts(
        self, validation_results: Dict[str, Any], verdict: str, next_state: str, next_action: str
    ) -> Dict[str, str]:
        """Generate all required artifacts."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        written: Dict[str, str] = {}

        # Agent contract
        written["agent_contract"] = self._write_json(
            self.artifacts_dir / "state_audit_guard_agent_contract.json",
            StateAuditGuardContract.get_contract(),
        )

        # Tool policy
        written["tool_policy"] = self._write_json(
            self.artifacts_dir / "state_audit_guard_tool_policy.json",
            StateAuditGuardContract.get_tool_policy(),
        )

        # State consistency report
        written["state_consistency_report"] = self._write_json(
            self.artifacts_dir / "state_consistency_report.json",
            validation_results["state_consistency"],
        )

        # Artifact index consistency report
        written["artifact_index_consistency_report"] = self._write_json(
            self.artifacts_dir / "artifact_index_consistency_report.json",
            validation_results["artifact_index_consistency"],
        )

        # Episode ledger consistency report
        written["episode_ledger_consistency_report"] = self._write_json(
            self.artifacts_dir / "episode_ledger_consistency_report.json",
            validation_results["episode_ledger_consistency"],
        )

        # Proof consistency report
        written["proof_consistency_report"] = self._write_json(
            self.artifacts_dir / "proof_consistency_report.json",
            validation_results["proof_consistency"],
        )

        # Forbidden actions audit report
        written["forbidden_actions_audit_report"] = self._write_json(
            self.artifacts_dir / "forbidden_actions_audit_report.json",
            validation_results["forbidden_actions_audit"],
        )

        # Operator decision audit report
        written["operator_decision_audit_report"] = self._write_json(
            self.artifacts_dir / "operator_decision_audit_report.json",
            validation_results["operator_decision_audit"],
        )

        # Git proof audit report
        written["git_proof_audit_report"] = self._write_json(
            self.artifacts_dir / "git_proof_audit_report.json",
            validation_results["git_proof_audit"],
        )

        # Final report
        written["final_report"] = self._write_json(
            self.artifacts_dir / "state_audit_guard_final_report.json",
            self._build_final_report(validation_results, verdict, next_state, next_action),
        )

        # Blocker packet if blocked
        if validation_results["has_blocker"]:
            written["blocker_packet"] = self._write_json(
                self.artifacts_dir / "state_audit_guard_blocker_packet.json",
                self._build_blocker_packet(validation_results),
            )

        return written

    def _write_json(self, path: Path, data: Dict[str, Any]) -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(path)

    def _build_final_report(
        self, validation_results: Dict[str, Any], verdict: str, next_state: str, next_action: str
    ) -> Dict[str, Any]:
        blocker_findings = [
            f for f in validation_results["all_findings"]
            if f.get("severity") == "blocker"
        ]

        return {
            "report_id": "state_audit_guard_final_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "next_state": next_state,
            "next_action": next_action,
            "state_consistency_valid": validation_results["state_consistency"]["valid"],
            "artifact_index_consistency_valid": validation_results["artifact_index_consistency"][
                "valid"
            ],
            "episode_ledger_consistency_valid": validation_results["episode_ledger_consistency"][
                "valid"
            ],
            "proof_consistency_valid": validation_results["proof_consistency"]["valid"],
            "forbidden_actions_valid": validation_results["forbidden_actions_audit"]["valid"],
            "operator_decision_valid": validation_results["operator_decision_audit"]["valid"],
            "git_proof_valid": validation_results["git_proof_audit"]["valid"],
            "total_findings": len(validation_results["all_findings"]),
            "blocker_count": len(blocker_findings),
            "blocker_findings": blocker_findings,
            "production_accepted": False,
            "traceable": True,
        }

    def _build_blocker_packet(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        blocker_findings = [
            f for f in validation_results["all_findings"]
            if f.get("severity") == "blocker"
        ]

        return {
            "packet_id": "state_audit_guard_blocker_packet",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocker_detected": True,
            "blocker_count": len(blocker_findings),
            "blockers": [
                {"type": "validation_blocker", "reason": f.get("detail", ""), "severity": "blocker"}
                for f in blocker_findings
            ],
            "required_next_action": "state_audit_blocker_resolution_required",
            "verdict": "BLOCKED",
            "next_state": "state_audit_blocker_resolution_required",
            "next_allowed_action": "state_audit_blocker_resolution_required",
            "production_accepted": False,
            "downstream_blocked": True,
            "traceable": True,
        }

    def update_artifact_index(self, verdict: str, next_state: str, next_action: str) -> Dict[str, Any]:
        """Update artifact_index.json."""
        index_path = self.control_dir / "artifact_index.json"
        index: Dict[str, Any] = {}
        if index_path.is_file():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                index = {}

        index["state_audit_guard_review_executed"] = True
        index["state_audit_guard_review_timestamp"] = datetime.now(timezone.utc).isoformat()
        index["state_audit_guard_verdict"] = verdict
        index["current_state"] = next_state
        index["next_allowed_action"] = next_action
        index["production_accepted"] = False

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def update_episode_ledger(self, verdict: str, next_state: str, next_action: str) -> list:
        """Update episode_ledger.json."""
        ledger_path = self.control_dir / "episode_ledger.json"
        ledger: list = []
        if ledger_path.is_file():
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except (json.JSONDecodeError, IOError):
                ledger = []

        event = {
            "event_type": "state_audit_guard_review",
            "agent_id": "state_audit_guard",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "has_blocker": verdict == "BLOCKED",
            "current_state": next_state,
            "next_allowed_action": next_action,
            "production_accepted": False,
            "new_generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
        }
        ledger.append(event)

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)

        return ledger

    def update_state(self, next_state: str, next_action: str) -> Dict[str, Any]:
        """Update state.json."""
        state_path = self.control_dir / "state.json"
        state: Dict[str, Any] = {}
        if state_path.is_file():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                state = {}

        state["current_state"] = next_state
        state["next_allowed_action"] = next_action
        state["production_accepted"] = False
        state["previous_task"] = "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return state
