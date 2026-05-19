"""State Audit Guard Validator - performs all validation audits.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .standards_adapter import StateAuditStandardsAdapter


class StateAuditGuardValidator:
    """Performs state consistency and audit trail validation."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.standards = StateAuditStandardsAdapter(self.project_root)

    def validate_state_consistency(self) -> Dict[str, Any]:
        """Validate state.json consistency."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        state_path = self.control_dir / "state.json"
        if not state_path.is_file():
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="state.json does not exist",
                )
            )
            return {
                "report_id": "state_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"state.json is invalid JSON or unreadable: {e}",
                )
            )
            return {
                "report_id": "state_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check required fields
        current_state = state.get("current_state", "")
        next_allowed_action = state.get("next_allowed_action", "")
        production_accepted = state.get("production_accepted", False)

        if not current_state:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="state.json missing current_state field",
                )
            )

        if not next_allowed_action:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="state.json missing next_allowed_action field",
                )
            )

        if production_accepted:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="production_accepted is true without final production gate",
                )
            )

        # Check for forbidden action flags
        forbidden_flags_checked = [
            "new_generation_performed",
            "comfyui_submit_executed",
            "voice_generation_executed",
            "assembly_executed",
            "downstream_executed",
        ]

        for flag in forbidden_flags_checked:
            if state.get(flag, False):
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Forbidden action flag {flag} is true without explicit gate",
                    )
                )

        valid = len([f for f in findings if f.get("severity") == "blocker"]) == 0
        if valid:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="State consistency validated",
                )
            )

        return {
            "report_id": "state_consistency_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "production_accepted": production_accepted,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_artifact_index_consistency(self) -> Dict[str, Any]:
        """Validate artifact_index.json consistency."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        index_path = self.control_dir / "artifact_index.json"
        if not index_path.is_file():
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="artifact_index.json does not exist",
                )
            )
            return {
                "report_id": "artifact_index_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"artifact_index.json is invalid JSON or unreadable: {e}",
                )
            )
            return {
                "report_id": "artifact_index_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check that listed artifacts exist
        artifacts = index.get("artifacts", [])
        missing_artifacts: List[str] = []

        for artifact in artifacts:
            artifact_path = self.project_root / artifact
            if not artifact_path.exists():
                artifact_path = self.control_dir / artifact
                if not artifact_path.exists():
                    missing_artifacts.append(artifact)

        if missing_artifacts:
            for missing in missing_artifacts:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Missing canonical artifact: {missing}",
                    )
                )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="All canonical artifacts present",
                )
            )

        valid = len([f for f in findings if f.get("severity") == "blocker"]) == 0

        return {
            "report_id": "artifact_index_consistency_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "artifacts_listed": len(artifacts),
            "missing_artifacts": missing_artifacts,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_episode_ledger_consistency(self) -> Dict[str, Any]:
        """Validate episode_ledger.json consistency."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        ledger_path = self.control_dir / "episode_ledger.json"
        if not ledger_path.is_file():
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="episode_ledger.json does not exist",
                )
            )
            return {
                "report_id": "episode_ledger_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"episode_ledger.json is invalid JSON or unreadable: {e}",
                )
            )
            return {
                "report_id": "episode_ledger_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check ledger consistency with state
        state_path = self.control_dir / "state.json"
        state_current_state = ""
        if state_path.is_file():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                state_current_state = state.get("current_state", "")
            except (json.JSONDecodeError, IOError):
                pass

        if ledger and isinstance(ledger, list) and len(ledger) > 0:
            latest_event = ledger[-1]
            ledger_state = latest_event.get("current_state", "")

            if ledger_state and state_current_state and ledger_state != state_current_state:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Ledger current_state mismatch: ledger={ledger_state}, state={state_current_state}",
                    )
                )
            else:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="pass",
                        severity="info",
                        detail="Ledger consistency validated",
                    )
                )

        valid = len([f for f in findings if f.get("severity") == "blocker"]) == 0

        return {
            "report_id": "episode_ledger_consistency_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "ledger_entries": len(ledger) if isinstance(ledger, list) else 0,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_proof_consistency(self) -> Dict[str, Any]:
        """Validate proof JSON consistency."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        # Check for proof JSON for the current layer
        proof_files = list(self.project_root.glob("*proof.json"))
        proof_files.extend(list(self.control_dir.glob("*proof.json")))

        if not proof_files:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="No proof JSON found for current layer",
                )
            )
            return {
                "report_id": "proof_consistency_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Validate proof claims
        for proof_file in proof_files:
            try:
                with open(proof_file, "r", encoding="utf-8") as f:
                    proof = json.load(f)

                # Check tests_pass claim
                tests_pass = proof.get("tests_pass", False)
                if tests_pass:
                    # Verify test evidence exists
                    test_file = self.project_root / "tests" / "test_state_audit_guard_agent.py"
                    if not test_file.exists():
                        findings.append(
                            self.standards.get_traceable_finding(
                                decision="blocked",
                                severity="blocker",
                                detail=f"Proof claims tests_pass but test file not found: {proof_file.name}",
                            )
                        )

                # Check git clean claim
                git_clean = proof.get("git_status_clean", False)
                if git_clean:
                    # Verify git is actually clean
                    result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.stdout.strip() != "":
                        findings.append(
                            self.standards.get_traceable_finding(
                                decision="blocked",
                                severity="blocker",
                                detail=f"Proof claims git clean but repository is dirty: {proof_file.name}",
                            )
                        )

            except (json.JSONDecodeError, IOError) as e:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Proof file invalid or unreadable: {proof_file.name} - {e}",
                    )
                )

        if not findings:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="Proof consistency validated",
                )
            )

        valid = len([f for f in findings if f.get("severity") == "blocker"]) == 0

        return {
            "report_id": "proof_consistency_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "proof_files_checked": len(proof_files),
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_forbidden_actions(self) -> Dict[str, Any]:
        """Validate that forbidden actions were not executed."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        state_path = self.control_dir / "state.json"
        if not state_path.is_file():
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="state.json does not exist",
                )
            )
            return {
                "report_id": "forbidden_actions_audit_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"state.json is invalid JSON or unreadable: {e}",
                )
            )
            return {
                "report_id": "forbidden_actions_audit_report",
                "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
                "role": "state_audit_guard",
                "valid": False,
                "findings": findings,
                "traceable": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check forbidden action flags
        forbidden_flags = [
            ("new_generation_performed", "generation"),
            ("comfyui_submit_executed", "comfyui submit"),
            ("retry_attempted", "retry"),
            ("preview_render_executed", "preview render"),
            ("final_render_executed", "final render"),
            ("voice_generation_executed", "voice generation"),
            ("audio_generation_executed", "audio generation"),
            ("assembly_executed", "assembly"),
            ("downstream_executed", "downstream"),
            ("production_accepted", "production acceptance"),
        ]

        violations: List[str] = []
        for flag, action_name in forbidden_flags:
            if state.get(flag, False):
                violations.append(f"{action_name} executed without gate ({flag}=true)")

        if violations:
            for violation in violations:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=violation,
                    )
                )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="No forbidden actions detected",
                )
            )

        valid = len(violations) == 0

        return {
            "report_id": "forbidden_actions_audit_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "violations": violations,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_operator_decisions(self) -> Dict[str, Any]:
        """Validate operator decision artifacts for fakes."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        # Check for operator decision artifacts
        operator_decision_files = [
            "post_preview_routing_decision.json",
            "post_preview_operator_decision_reconciliation.json",
            "preview_operator_decision_input.json",
            "fresh_visual_generation_authorization.json",
            "corrective_visual_generation_authorization.json",
        ]

        fake_detected = False
        artifacts_checked = []

        for decision_file in operator_decision_files:
            decision_path = self.control_dir / decision_file
            if decision_path.is_file():
                artifacts_checked.append(decision_file)
                try:
                    with open(decision_path, "r", encoding="utf-8") as f:
                        decision_data = json.load(f)

                    # Check for agent-generated decisions without human review
                    source = decision_data.get("source", "")
                    operator_id = decision_data.get("operator_id", "")

                    if source == "agent" and not operator_id:
                        fake_detected = True
                        findings.append(
                            self.standards.get_traceable_finding(
                                decision="blocked",
                                severity="blocker",
                                detail=f"Fake operator decision detected in {decision_file}: agent-generated without human operator",
                            )
                        )

                except (json.JSONDecodeError, IOError):
                    pass

        if not fake_detected:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="No fake operator decisions detected",
                )
            )

        valid = not fake_detected

        return {
            "report_id": "operator_decision_audit_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "fake_decision_detected": fake_detected,
            "artifacts_checked": artifacts_checked,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate_git_proof(self) -> Dict[str, Any]:
        """Validate git proof."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            git_dirty = result.stdout.strip() != ""

            if git_dirty:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail="Git repository is dirty - uncommitted changes detected",
                    )
                )
            else:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="pass",
                        severity="info",
                        detail="Git repository is clean",
                    )
                )

            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            current_branch = branch_result.stdout.strip()

            # Get latest commit hash
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            commit_hash = commit_result.stdout.strip()

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"Failed to check git status: {e}",
                )
            )
            git_dirty = True
            current_branch = "unknown"
            commit_hash = "unknown"

        valid = not git_dirty

        return {
            "report_id": "git_proof_audit_report",
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "valid": valid,
            "git_dirty": git_dirty,
            "current_branch": current_branch,
            "commit_hash": commit_hash,
            "findings": findings,
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation audits and aggregate results."""
        state_consistency = self.validate_state_consistency()
        artifact_index_consistency = self.validate_artifact_index_consistency()
        episode_ledger_consistency = self.validate_episode_ledger_consistency()
        proof_consistency = self.validate_proof_consistency()
        forbidden_actions = self.validate_forbidden_actions()
        operator_decisions = self.validate_operator_decisions()
        git_proof = self.validate_git_proof()

        # Aggregate all findings
        all_findings = []
        all_findings.extend(state_consistency.get("findings", []))
        all_findings.extend(artifact_index_consistency.get("findings", []))
        all_findings.extend(episode_ledger_consistency.get("findings", []))
        all_findings.extend(proof_consistency.get("findings", []))
        all_findings.extend(forbidden_actions.get("findings", []))
        all_findings.extend(operator_decisions.get("findings", []))
        all_findings.extend(git_proof.get("findings", []))

        blocker_findings = [f for f in all_findings if f.get("severity") == "blocker"]
        has_blocker = len(blocker_findings) > 0

        verdict = "BLOCKED" if has_blocker else "ACCEPTED"
        
        # Determine next state and action based on verdict
        if verdict == "ACCEPTED":
            next_state = "production_gate_review_required"
            next_action = "production_gate_review_required"
        else:
            next_state = "state_audit_blocker_resolution_required"
            next_action = "state_audit_blocker_resolution_required"

        return {
            "task_id": "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001",
            "role": "state_audit_guard",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_consistency": state_consistency,
            "artifact_index_consistency": artifact_index_consistency,
            "episode_ledger_consistency": episode_ledger_consistency,
            "proof_consistency": proof_consistency,
            "forbidden_actions_audit": forbidden_actions,
            "operator_decision_audit": operator_decisions,
            "git_proof_audit": git_proof,
            "all_findings": all_findings,
            "blocker_count": len(blocker_findings),
            "has_blocker": has_blocker,
            "verdict": verdict,
            "next_state": next_state,
            "next_action": next_action,
            "traceable": True,
        }
