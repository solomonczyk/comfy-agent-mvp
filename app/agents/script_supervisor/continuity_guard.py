"""Continuity Guard — orchestrates all Script Supervisor audits.

Guards against fake operator decisions, blocked downstream states, and
ensures production_accepted remains false.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
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

    def audit_agent_verdict_chain(self, candidate_path: str, candidate_sha256: str) -> Dict[str, Any]:
        """Audit the chain of prior agent verdicts for continuity."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []
        
        # Expected agent chain in order
        expected_agents = [
            "camera_operator_agent",
            "dop_agent",
            "actor_character_control_agent",
            "colorist_agent",
            "production_designer_agent",
            "set_decorator_agent",
            "props_agent",
            "costume_agent",
        ]
        
        agent_proofs: Dict[str, Any] = {}
        missing_proofs: List[str] = []
        sha_mismatches: List[str] = []
        verdict_chain: List[Dict[str, Any]] = []
        
        for agent in expected_agents:
            agent_dir = self.control_dir / agent
            proof_files = list(agent_dir.glob("*_proof.json"))
            
            if not proof_files:
                missing_proofs.append(agent)
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Missing proof file for agent: {agent}",
                    )
                )
                continue
            
            # Read the most recent proof
            proof_file = sorted(proof_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            try:
                with open(proof_file, "r", encoding="utf-8") as f:
                    proof = json.load(f)
                agent_proofs[agent] = proof
                
                # Check verdict
                verdict_key = None
                if agent == "camera_operator_agent":
                    verdict_key = "operator_verdict"
                elif agent == "dop_agent":
                    verdict_key = "dop_verdict"
                elif agent == "actor_character_control_agent":
                    verdict_key = "actor_character_verdict"
                elif agent == "colorist_agent":
                    verdict_key = "colorist_verdict"
                elif agent == "production_designer_agent":
                    verdict_key = "production_design_verdict"
                elif agent == "set_decorator_agent":
                    verdict_key = "set_decorator_verdict"
                elif agent == "props_agent":
                    verdict_key = "props_verdict"
                elif agent == "costume_agent":
                    verdict_key = "costume_verdict"
                
                verdict = proof.get(verdict_key, "UNKNOWN")
                verdict_chain.append({
                    "agent": agent,
                    "verdict": verdict,
                    "proof_file": str(proof_file.name),
                    "commit": proof.get("commit_hash", ""),
                })
                
                # Check SHA256 consistency if present
                proof_candidate_sha = proof.get("candidate_sha256")
                if proof_candidate_sha and proof_candidate_sha != candidate_sha256:
                    sha_mismatches.append(agent)
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"SHA256 mismatch for {agent}: expected {candidate_sha256}, got {proof_candidate_sha}",
                        )
                    )
                
                # Check for forbidden actions
                if proof.get("new_generation_performed", False):
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"{agent} performed new generation - forbidden",
                        )
                    )
                if proof.get("retry_attempted", False):
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"{agent} attempted retry - forbidden",
                        )
                    )
                if proof.get("comfyui_submit_executed", False):
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"{agent} executed ComfyUI submit - forbidden",
                        )
                    )
                if proof.get("production_accepted", False):
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"{agent} set production_accepted=true - forbidden",
                        )
                    )
                    
            except (json.JSONDecodeError, IOError) as e:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail=f"Failed to read proof for {agent}: {e}",
                    )
                )
        
        if missing_proofs:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"Missing proofs for agents: {', '.join(missing_proofs)}",
                )
            )
        
        if not sha_mismatches and not missing_proofs:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="All agent verdicts present and SHA256 consistent",
                )
            )
        
        # Check that all verdicts are ACCEPTED or ACCEPTED_FOR_NEXT_GATE
        non_accepted = [v for v in verdict_chain if v["verdict"] not in ("ACCEPTED", "ACCEPTED_FOR_NEXT_GATE")]
        if non_accepted:
            non_accepted_desc = ", ".join([f"{v['agent']}: {v['verdict']}" for v in non_accepted])
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"Non-accepted verdicts found: {non_accepted_desc}",
                )
            )
        
        return {
            "report_id": "script_supervisor_agent_verdict_chain_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-CONTINUITY-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "candidate_path": candidate_path,
            "candidate_sha256": candidate_sha256,
            "expected_agents": expected_agents,
            "agent_proofs_found": list(agent_proofs.keys()),
            "missing_proofs": missing_proofs,
            "sha_mismatches": sha_mismatches,
            "verdict_chain": verdict_chain,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def audit_state_transition_chain(self) -> Dict[str, Any]:
        """Audit the state transition chain for validity."""
        self.standards.load_standards()
        findings: List[Dict[str, Any]] = []
        
        # Read state
        state_path = self.control_dir / "state.json"
        state: Dict[str, Any] = {}
        if state_path.is_file():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="blocked",
                        severity="blocker",
                        detail="Failed to read state.json",
                    )
                )
        
        current_state = state.get("current_state", "")
        expected_state = "script_supervisor_continuity_review_required"
        
        if current_state != expected_state:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail=f"State mismatch: expected {expected_state}, got {current_state}",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail=f"State is correct: {current_state}",
                )
            )
        
        # Check that production_accepted is false
        production_accepted = state.get("production_accepted", False)
        if production_accepted:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="blocked",
                    severity="blocker",
                    detail="production_accepted is true - forbidden",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="production_accepted is false - correct",
                )
            )
        
        # Check that no generation occurred after Camera Operator
        new_image_generation_performed = state.get("new_image_generation_performed", False)
        comfyui_submit_executed = state.get("comfyui_submit_executed", False)
        
        if new_image_generation_performed or comfyui_submit_executed:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="Generation flags are true - verify this is the original Camera Operator generation",
                )
            )
        
        return {
            "report_id": "script_supervisor_state_transition_chain_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-CONTINUITY-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "current_state": current_state,
            "expected_state": expected_state,
            "state_valid": current_state == expected_state,
            "production_accepted": production_accepted,
            "new_image_generation_performed": new_image_generation_performed,
            "comfyui_submit_executed": comfyui_submit_executed,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
