"""Script Supervisor Continuity Review Agent — agent verdict continuity review.

RC-COMBINE-V2-SCRIPT-SUPERVISOR-CONTINUITY-VERTICAL-SLICE-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .continuity_guard import ContinuityGuard
from .standards_adapter import ScriptSupervisorStandardsAdapter


class ContinuityReviewAgent:
    """Agent that reviews continuity across prior agent verdicts."""

    AGENT_ID = "script_supervisor_continuity_guard"
    TASK_ID = "RC-COMBINE-V2-SCRIPT-SUPERVISOR-CONTINUITY-VERTICAL-SLICE-001"

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.script_supervisor_dir = self.control_dir / "script_supervisor_agent"
        self.guard = ContinuityGuard(self.project_root)
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def run_continuity_review(
        self,
        candidate_path: str,
        candidate_sha256: str,
        previous_costume_commit: str,
    ) -> Dict[str, Any]:
        """Execute the full continuity review."""
        self.standards.load_standards()

        # Run all continuity audits
        agent_verdict_chain = self.guard.audit_agent_verdict_chain(
            candidate_path, candidate_sha256
        )
        state_transition_chain = self.guard.audit_state_transition_chain()
        downstream_guard = self.guard.audit_downstream_blocked_state()

        # Note: fake_decision_audit is skipped for continuity review as it's for preview stage
        # We only check agent verdict continuity and state transitions

        # Determine overall verdict
        all_findings = []
        all_findings.extend(agent_verdict_chain.get("findings", []))
        all_findings.extend(state_transition_chain.get("findings", []))
        all_findings.extend(downstream_guard.get("findings", []))

        blocker_findings = [f for f in all_findings if f.get("severity") == "blocker"]
        has_blocker = len(blocker_findings) > 0

        if has_blocker:
            verdict = "BLOCKED"
            next_state = "continuity_blocker_resolution_required"
            next_action = "continuity_blocker_resolution_required"
        else:
            verdict = "ACCEPTED"
            next_state = "state_audit_guard_review_required"
            next_action = "state_audit_guard_review_required"

        # Verify Costume proof tracking
        costume_proof_tracked = self._verify_costume_proof_tracked(previous_costume_commit)

        review_result = {
            "agent_id": self.AGENT_ID,
            "task_id": self.TASK_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": "script_supervisor",
            "candidate_path": candidate_path,
            "candidate_sha256": candidate_sha256,
            "previous_costume_commit": previous_costume_commit,
            "costume_proof_tracked": costume_proof_tracked,
            "agent_verdict_chain_report": agent_verdict_chain,
            "state_transition_chain_report": state_transition_chain,
            "downstream_guard_report": downstream_guard,
            "all_findings": all_findings,
            "blocker_count": len(blocker_findings),
            "has_blocker": has_blocker,
            "verdict": verdict,
            "new_generation_performed": False,
            "retry_attempted": False,
            "second_generation_attempted": False,
            "comfyui_submit_executed": False,
            "image_editing_executed": False,
            "render_executed": False,
            "visual_qa_final_acceptance_executed": False,
            "operator_acceptance_executed_by_agent": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }

        # Determine state transition
        state_update = {
            "current_state": next_state,
            "next_allowed_action": next_action,
            "production_accepted": False,
            "previous_task": self.TASK_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "review_result": review_result,
            "state_update": state_update,
            "verdict": verdict,
            "next_state": next_state,
            "next_action": next_action,
        }

    def _verify_costume_proof_tracked(self, expected_commit: str) -> bool:
        """Verify that the Costume proof is tracked in git."""
        costume_proof_path = (
            self.control_dir
            / "costume_agent"
            / "RC-COMBINE-V2-COSTUME-VERTICAL-SLICE-001_proof.json"
        )
        if not costume_proof_path.exists():
            return False

        try:
            with open(costume_proof_path, "r", encoding="utf-8") as f:
                proof = json.load(f)
            tracked_commit = proof.get("commit_hash", "")
            return tracked_commit == expected_commit
        except (json.JSONDecodeError, IOError):
            return False

    def write_all_artifacts(self, review_result: Dict[str, Any]) -> Dict[str, str]:
        """Write all required artifacts."""
        out_dir = self.script_supervisor_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        written: Dict[str, str] = {}

        # Agent contract
        written["agent_contract"] = self._write_json(
            out_dir / "script_supervisor_agent_contract.json",
            self._build_agent_contract(),
        )

        # Review authorization
        written["review_authorization"] = self._write_json(
            out_dir / "continuity_review_authorization.json",
            self._build_review_authorization(review_result),
        )

        # Continuity review report
        written["continuity_review_report"] = self._write_json(
            out_dir / "continuity_review_report.json",
            self._build_continuity_review_report(review_result),
        )

        # Agent verdict chain report
        written["agent_verdict_chain_report"] = self._write_json(
            out_dir / "agent_verdict_chain_report.json",
            review_result["review_result"]["agent_verdict_chain_report"],
        )

        # State transition chain report
        written["state_transition_chain_report"] = self._write_json(
            out_dir / "state_transition_chain_report.json",
            review_result["review_result"]["state_transition_chain_report"],
        )

        # Script supervisor verdict
        written["script_supervisor_verdict"] = self._write_json(
            out_dir / "script_supervisor_verdict.json",
            self._build_verdict(review_result),
        )

        # Blocker report if blocked
        if review_result["review_result"]["has_blocker"]:
            written["blocker_report"] = self._write_json(
                out_dir / "continuity_blocker_report.json",
                self._build_blocker_report(review_result),
            )

        return written

    def _write_json(self, path: Path, data: Dict[str, Any]) -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(path)

    def _build_agent_contract(self) -> Dict[str, Any]:
        return {
            "agent_id": self.AGENT_ID,
            "role": "script_supervisor_continuity_guard",
            "task_id": self.TASK_ID,
            "responsibility_zone": "agent_verdict_continuity_review",
            "allowed_inputs": [
                "candidate_path",
                "candidate_sha256",
                "prior_agent_proofs",
                "state_json",
                "artifact_index_json",
                "episode_ledger_json",
            ],
            "required_artifacts": [
                "camera_operator_proof",
                "dop_proof",
                "actor_character_control_proof",
                "colorist_proof",
                "production_designer_proof",
                "set_decorator_proof",
                "props_proof",
                "costume_proof",
            ],
            "forbidden_actions": [
                "new_generation",
                "retry",
                "comfyui_submit",
                "image_editing",
                "preview_render",
                "final_render",
                "visual_qa_final_acceptance",
                "operator_acceptance_by_agent",
                "assembly",
                "downstream",
                "production_accepted_true",
            ],
            "blocker_conditions": [
                "missing_prior_agent_proof",
                "candidate_sha_mismatch",
                "invalid_state_transition",
                "production_accepted_true",
                "fake_operator_acceptance",
                "forbidden_action_detected",
            ],
            "decision_outputs": ["ACCEPTED", "BLOCKED", "UNCERTAIN"],
            "may_set_production_accepted": False,
            "may_authorize_generation": False,
            "may_authorize_retry": False,
            "may_authorize_render": False,
            "may_authorize_downstream": False,
            "traceable": True,
        }

    def _build_review_authorization(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "authorization_id": "continuity_review_authorization",
            "task_id": self.TASK_ID,
            "role": "script_supervisor",
            "source_state": "script_supervisor_continuity_review_required",
            "reviewed_candidate_path": review_result["review_result"]["candidate_path"],
            "reviewed_candidate_sha256": review_result["review_result"]["candidate_sha256"],
            "reviewed_prior_agent_chain": [
                "camera_operator_agent",
                "dop_agent",
                "actor_character_control_agent",
                "colorist_agent",
                "production_designer_agent",
                "set_decorator_agent",
                "props_agent",
                "costume_agent",
            ],
            "no_generation_authorized": True,
            "no_retry_authorized": True,
            "no_render_authorized": True,
            "no_downstream_authorized": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "traceable": True,
        }

    def _build_continuity_review_report(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "report_id": "continuity_review_report",
            "task_id": self.TASK_ID,
            "role": "script_supervisor",
            "timestamp": review_result["review_result"]["timestamp"],
            "candidate_path": review_result["review_result"]["candidate_path"],
            "candidate_sha256": review_result["review_result"]["candidate_sha256"],
            "previous_costume_commit": review_result["review_result"]["previous_costume_commit"],
            "costume_proof_tracked": review_result["review_result"]["costume_proof_tracked"],
            "agent_verdict_chain_summary": {
                "total_agents": len(
                    review_result["review_result"]["agent_verdict_chain_report"][
                        "verdict_chain"
                    ]
                ),
                "all_accepted": all(
                    v["verdict"] in ("ACCEPTED", "ACCEPTED_FOR_NEXT_GATE")
                    for v in review_result["review_result"]["agent_verdict_chain_report"][
                        "verdict_chain"
                    ]
                ),
                "sha_consistent": len(
                    review_result["review_result"]["agent_verdict_chain_report"][
                        "sha_mismatches"
                    ]
                )
                == 0,
            },
            "state_transition_summary": {
                "state_valid": review_result["review_result"][
                    "state_transition_chain_report"
                ]["state_valid"],
                "production_accepted_false": not review_result["review_result"][
                    "state_transition_chain_report"
                ]["production_accepted"],
            },
            "downstream_guard_summary": {
                "production_accepted_false": not review_result["review_result"][
                    "downstream_guard_report"
                ]["production_accepted"],
                "voice_generation_blocked": not review_result["review_result"][
                    "downstream_guard_report"
                ]["voice_generation_ready"],
                "assembly_blocked": not review_result["review_result"][
                    "downstream_guard_report"
                ]["assembly_allowed"],
                "downstream_blocked": not review_result["review_result"][
                    "downstream_guard_report"
                ]["downstream_allowed"],
            },
            "forbidden_actions_absent": review_result["review_result"][
                "blocker_count"
            ]
            == 0,
            "total_findings": len(review_result["review_result"]["all_findings"]),
            "blocker_findings": review_result["review_result"]["blocker_count"],
            "verdict": review_result["verdict"],
            "traceable": True,
        }

    def _build_verdict(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "verdict_id": "script_supervisor_verdict",
            "task_id": self.TASK_ID,
            "role": "script_supervisor",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_path": review_result["review_result"]["candidate_path"],
            "candidate_sha256": review_result["review_result"]["candidate_sha256"],
            "verdict": review_result["verdict"],
            "next_state": review_result["next_state"],
            "next_allowed_action": review_result["next_action"],
            "costume_proof_tracked": review_result["review_result"]["costume_proof_tracked"],
            "agent_verdict_chain_valid": all(
                v["verdict"] in ("ACCEPTED", "ACCEPTED_FOR_NEXT_GATE")
                for v in review_result["review_result"]["agent_verdict_chain_report"][
                    "verdict_chain"
                ]
            ),
            "state_transition_valid": review_result["review_result"][
                "state_transition_chain_report"
            ]["state_valid"],
            "no_forbidden_actions": review_result["review_result"]["blocker_count"] == 0,
            "production_accepted": False,
            "traceable": True,
        }

    def _build_blocker_report(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        blocker_findings = [
            f for f in review_result["review_result"]["all_findings"]
            if f.get("severity") == "blocker"
        ]
        return {
            "blocker_report_id": "continuity_blocker_report",
            "task_id": self.TASK_ID,
            "role": "script_supervisor",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocker_type": "continuity_blocker",
            "blocked": True,
            "blocker_reasons": [f.get("detail", "") for f in blocker_findings],
            "blocker_count": len(blocker_findings),
            "required_resolution": "manual_review_and_correction",
            "verdict": "BLOCKED",
            "next_state": "continuity_blocker_resolution_required",
            "next_allowed_action": "continuity_blocker_resolution_required",
            "traceable": True,
        }

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update state.json with the new state."""
        state_path = self.control_dir / "state.json"
        state: Dict[str, Any] = {}
        if state_path.is_file():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                state = {}

        state.update(state_update)

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return state

    def update_artifact_index(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update artifact_index.json with continuity review results."""
        index_path = self.control_dir / "artifact_index.json"
        index: Dict[str, Any] = {}
        if index_path.is_file():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                index = {}

        index["script_supervisor_continuity_review_executed"] = True
        index["script_supervisor_continuity_review_timestamp"] = review_result[
            "review_result"
        ]["timestamp"]
        index["script_supervisor_verdict"] = review_result["verdict"]
        index["current_state"] = review_result["next_state"]
        index["next_allowed_action"] = review_result["next_action"]
        index["production_accepted"] = False
        index["costume_proof_tracked"] = review_result["review_result"][
            "costume_proof_tracked"
        ]

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def update_episode_ledger(self, review_result: Dict[str, Any]) -> list:
        """Record continuity review event in episode ledger."""
        ledger_path = self.control_dir / "episode_ledger.json"
        ledger: list = []
        if ledger_path.is_file():
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except (json.JSONDecodeError, IOError):
                ledger = []

        event = {
            "event_type": "script_supervisor_continuity_review",
            "agent_id": self.AGENT_ID,
            "task_id": self.TASK_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_path": review_result["review_result"]["candidate_path"],
            "candidate_sha256": review_result["review_result"]["candidate_sha256"],
            "previous_costume_commit": review_result["review_result"][
                "previous_costume_commit"
            ],
            "costume_proof_tracked": review_result["review_result"]["costume_proof_tracked"],
            "verdict": review_result["verdict"],
            "has_blocker": review_result["review_result"]["has_blocker"],
            "current_state": review_result["next_state"],
            "next_allowed_action": review_result["next_action"],
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
