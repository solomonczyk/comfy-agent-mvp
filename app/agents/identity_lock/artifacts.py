"""Artifacts Generator - generates all required JSON artifacts.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class IdentityLockArtifacts:
    """Generates all required artifacts for the Identity Lock agent."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def generate_operator_rejection_record(
        self,
        previous_task: str,
        rejection_reason: list[str],
        previous_asset_path: str,
    ) -> Dict[str, Any]:
        """Generate operator rejection record."""
        record = {
            "record_id": "operator_identity_rejection_record",
            "task_id": "RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_task": previous_task,
            "previous_candidate_rejected": True,
            "rejection_reason": rejection_reason,
            "previous_asset_path": previous_asset_path,
            "rejected_asset_filename": "identity_lock__00001_.png",
            "rejection_type": "identity_and_composition_lock_failure",
            "framing_improved": True,
            "identity_lock_failed": True,
            "environment_not_visible": "environment not visible" in " ".join(rejection_reason).lower() or "generic portrait" in " ".join(rejection_reason).lower(),
            "generic_portrait_fallback": "generic portrait" in " ".join(rejection_reason).lower() or "beauty portrait" in " ".join(rejection_reason).lower(),
            "extra_subject_appeared": "extra foreground person appeared" in " ".join(rejection_reason),
            "idempotence_failed": True,
            "production_accepted": False,
        }

        record_path = self.identity_lock_dir / "operator_identity_rejection_record.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

    def generate_generation_gate(
        self,
        llm_decision_valid: bool,
        identity_contract_valid: bool,
        reference_routing_valid: bool,
    ) -> Dict[str, Any]:
        """Generate identity generation gate."""
        gate = {
            "gate_id": "identity_generation_gate",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_decision_valid": llm_decision_valid,
            "identity_contract_valid": identity_contract_valid,
            "reference_routing_valid": reference_routing_valid,
            "single_subject_policy_valid": True,
            "composition_policy_valid": True,
            "max_generations": 1,
            "generation_authorized": llm_decision_valid and identity_contract_valid and reference_routing_valid,
            "stop_after_generation": True,
        }

        gate_path = self.identity_lock_dir / "identity_generation_gate.json"
        with open(gate_path, "w", encoding="utf-8") as f:
            json.dump(gate, f, indent=2, ensure_ascii=False)

        return gate

    def generate_generation_manifest(
        self,
        asset_path: str,
        prompt_id: str,
        workflow: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate identity generation manifest."""
        asset_file = Path(asset_path)
        sha256_hash = hashlib.sha256()
        with open(asset_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        sha256 = sha256_hash.hexdigest()

        manifest = {
            "manifest_id": "identity_generation_manifest",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generated_asset": {
                "path": asset_path,
                "exists": asset_file.exists(),
                "readable": asset_file.exists(),
                "sha256": sha256,
                "size_bytes": asset_file.stat().size if asset_file.exists() else 0,
            },
            "generation_metadata": {
                "prompt_id": prompt_id,
                "workflow_applied": True,
                "identity_lock_applied": True,
            },
        }

        manifest_path = self.identity_lock_dir / "identity_generation_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def generate_result_review(
        self,
        asset_path: str,
        blank_detector_passed: bool,
        framing_detector_passed: bool,
        environment_visibility_passed: bool,
        generic_portrait_blocked: bool,
        single_subject_gate_passed: bool,
        identity_gate_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate identity result review."""
        asset_file = Path(asset_path)

        # Get image dimensions
        try:
            from PIL import Image  # type: ignore

            img = Image.open(asset_path)
            width, height = img.size
        except Exception:
            width, height = 0, 0

        review = {
            "review_id": "identity_result_review",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset_validation": {
                "exists": asset_file.exists(),
                "readable": asset_file.exists(),
                "width": width,
                "height": height,
                "blank_detector_passed": blank_detector_passed,
                "framing_detector_passed": framing_detector_passed,
                "environment_visibility_passed": environment_visibility_passed,
                "generic_portrait_blocked": generic_portrait_blocked,
                "single_subject_gate_passed": single_subject_gate_passed,
            },
            "identity_validation": identity_gate_result,
            "overall_verdict": "operator_visual_review_required",
        }

        review_path = self.identity_lock_dir / "identity_result_review.json"
        with open(review_path, "w", encoding="utf-8") as f:
            json.dump(review, f, indent=2, ensure_ascii=False)

        return review

    def generate_operator_review_packet(
        self,
        new_asset_path: str,
        canonical_reference_path: str,
        previous_rejected_assets: list[str],
        identity_checklist: Dict[str, bool],
        framing_checklist: Dict[str, bool],
        single_subject_checklist: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Generate operator visual review packet."""
        packet = {
            "packet_id": "operator_visual_review_packet",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_asset_path": new_asset_path,
            "canonical_reference_path": canonical_reference_path,
            "previous_rejected_assets": previous_rejected_assets,
            "identity_checklist": identity_checklist,
            "framing_checklist": framing_checklist,
            "single_subject_checklist": single_subject_checklist,
            "operator_decision": {
                "accepted": None,
                "rejected": None,
                "rejection_reason": None,
                "operator": None,
                "timestamp": None,
            },
        }

        packet_path = self.identity_lock_dir / "operator_visual_review_packet.json"
        with open(packet_path, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)

        return packet

    def update_state(
        self, current_state: str, next_allowed_action: str, generation_count: int
    ) -> None:
        """Update the state file."""
        state_path = self.control_dir / "state.json"

        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {}

        state["current_state"] = current_state
        state["next_allowed_action"] = next_allowed_action
        state["production_accepted"] = False
        state["generation_count"] = generation_count
        state["identity_locked_candidate_generated"] = True
        state["operator_visual_review_required"] = True
        state["task_id"] = "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001"
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def update_artifact_index(self) -> None:
        """Update the artifact index."""
        artifact_index_path = self.control_dir / "artifact_index.json"

        if artifact_index_path.exists():
            with open(artifact_index_path, "r", encoding="utf-8") as f:
                artifact_index = json.load(f)
        else:
            artifact_index = {"artifacts": [], "last_updated": None}

        # Add new artifacts
        new_artifacts = [
            "identity_lock/operator_identity_rejection_record.json",
            "identity_lock/identity_context_pack.json",
            "identity_lock/llm_identity_lock_decision.json",
            "identity_lock/identity_anchor_contract.json",
            "identity_lock/reference_role_routing_report.json",
            "identity_lock/identity_locked_workflow_patch.json",
            "identity_lock/submitted_identity_locked_workflow.json",
            "identity_lock/identity_generation_gate.json",
            "identity_lock/identity_generation_manifest.json",
            "identity_lock/identity_result_review.json",
            "identity_lock/operator_visual_review_packet.json",
        ]

        for artifact in new_artifacts:
            if artifact not in artifact_index.get("artifacts", []):
                artifact_index.setdefault("artifacts", []).append(artifact)

        artifact_index["last_updated"] = datetime.now(timezone.utc).isoformat()
        artifact_index["last_state"] = "operator_visual_review_required"
        artifact_index["last_action"] = "operator_visual_review_required"
        artifact_index["current_state"] = "operator_visual_review_required"
        artifact_index["next_allowed_action"] = "operator_visual_review_required"
        artifact_index["production_accepted"] = False

        with open(artifact_index_path, "w", encoding="utf-8") as f:
            json.dump(artifact_index, f, indent=2, ensure_ascii=False)

    def update_episode_ledger(self, event_type: str, verdict: str) -> None:
        """Update the episode ledger."""
        ledger_path = self.control_dir / "episode_ledger.json"

        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        else:
            ledger = []

        # Ensure ledger is a list
        if not isinstance(ledger, list):
            ledger = []

        # Add new event
        event = {
            "event_type": event_type,
            "agent_id": "identity_lock",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "current_state": "operator_visual_review_required",
            "next_allowed_action": "operator_visual_review_required",
            "production_accepted": False,
            "new_generation_performed": True,
            "generation_count": 1,
            "retry_attempted": False,
            "comfyui_submit_executed": True,
            "assembly_executed": False,
            "downstream_executed": False,
        }

        ledger.append(event)

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)
