"""Artifacts Generator - generates all required JSON artifacts.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class VisualReferenceCuratorArtifacts:
    """Generates all required artifacts for the Visual Reference Curator agent."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"

    def generate_all_artifacts(
        self,
        classification_results: Dict[str, Any],
        negative_reference: Dict[str, Any],
        misuse_diagnosis: Dict[str, Any],
        corrective_package: Dict[str, Any],
        next_state: str,
        next_action: str,
    ) -> None:
        """Generate all required artifacts."""
        self.control_dir.mkdir(parents=True, exist_ok=True)

        # Generate individual artifacts
        self._generate_agent_contract()
        self._generate_canonical_reference_role_map(classification_results)
        self._generate_reference_usage_policy(classification_results)
        self._generate_negative_reference_evidence(negative_reference)
        self._generate_reference_misuse_diagnosis(misuse_diagnosis)
        self._generate_corrective_package(corrective_package)
        self._generate_authorization_packet(corrective_package, next_state, next_action)

    def _generate_agent_contract(self) -> None:
        """Generate the agent contract artifact."""
        from .contract import VisualReferenceCuratorContract

        contract = VisualReferenceCuratorContract.get_contract()
        contract_path = self.control_dir / "visual_reference_curator_agent_contract.json"

        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2, ensure_ascii=False)

    def _generate_canonical_reference_role_map(
        self, classification_results: Dict[str, Any]
    ) -> None:
        """Generate the canonical reference role map artifact."""
        role_map_path = self.control_dir / "canonical_reference_role_map.json"

        with open(role_map_path, "w", encoding="utf-8") as f:
            json.dump(classification_results, f, indent=2, ensure_ascii=False)

    def _generate_reference_usage_policy(
        self, classification_results: Dict[str, Any]
    ) -> None:
        """Generate the reference usage policy artifact."""
        policy = {
            "policy_id": "reference_usage_policy",
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quality_only_refs": classification_results.get("quality_only_refs", []),
            "composition_refs": classification_results.get("composition_refs", []),
            "constraints": {
                "quality_reference_only": [
                    "Cannot be used as composition target",
                    "Cannot be used as framing target",
                    "Only for quality/style reference",
                ],
                "composition_reference": [
                    "Can be used for composition/framing",
                    "Must respect original framing",
                    "No extreme crop allowed",
                ],
            },
            "forbidden_usage_patterns": [
                "close-up eye/skin refs as composition target",
                "quality refs as framing target",
                "extreme face crop from composition refs",
            ],
        }

        policy_path = self.control_dir / "reference_usage_policy.json"

        with open(policy_path, "w", encoding="utf-8") as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)

    def _generate_negative_reference_evidence(
        self, negative_reference: Dict[str, Any]
    ) -> None:
        """Generate the negative reference evidence artifact."""
        evidence_path = self.control_dir / "negative_reference_evidence.json"

        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(negative_reference, f, indent=2, ensure_ascii=False)

    def _generate_reference_misuse_diagnosis(
        self, misuse_diagnosis: Dict[str, Any]
    ) -> None:
        """Generate the reference misuse diagnosis artifact."""
        diagnosis_path = self.control_dir / "reference_misuse_diagnosis.json"

        with open(diagnosis_path, "w", encoding="utf-8") as f:
            json.dump(misuse_diagnosis, f, indent=2, ensure_ascii=False)

    def _generate_corrective_package(
        self, corrective_package: Dict[str, Any]
    ) -> None:
        """Generate the corrective generation package artifact."""
        package_path = (
            self.control_dir / "corrective_reference_bound_generation_package.json"
        )

        with open(package_path, "w", encoding="utf-8") as f:
            json.dump(corrective_package, f, indent=2, ensure_ascii=False)

    def _generate_authorization_packet(
        self, corrective_package: Dict[str, Any], next_state: str, next_action: str
    ) -> None:
        """Generate the corrective generation authorization packet."""
        authorization_packet = {
            "packet_id": "corrective_generation_authorization_packet",
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "next_state": next_state,
            "next_allowed_action": next_action,
            "corrective_package": corrective_package,
            "authorizations": {
                "generation_authorized": True,
                "generation_type": "corrective_reference_bound",
                "comfyui_submit_authorized": False,
                "retry_authorized": False,
                "downstream_authorized": False,
                "production_accepted": False,
            },
        }

        packet_path = (
            self.control_dir / "corrective_generation_authorization_packet.json"
        )

        with open(packet_path, "w", encoding="utf-8") as f:
            json.dump(authorization_packet, f, indent=2, ensure_ascii=False)

    def update_artifact_index(
        self, verdict: str, next_state: str, next_action: str
    ) -> None:
        """Update the artifact index."""
        artifact_index_path = self.control_dir / "artifact_index.json"

        if artifact_index_path.exists():
            with open(artifact_index_path, "r", encoding="utf-8") as f:
                artifact_index = json.load(f)
        else:
            artifact_index = {"artifacts": [], "last_updated": None}

        # Add new artifacts
        new_artifacts = [
            "visual_reference_curator_agent_contract.json",
            "canonical_reference_role_map.json",
            "reference_usage_policy.json",
            "negative_reference_evidence.json",
            "reference_misuse_diagnosis.json",
            "corrective_reference_bound_generation_package.json",
            "corrective_generation_authorization_packet.json",
        ]

        for artifact in new_artifacts:
            if artifact not in artifact_index["artifacts"]:
                artifact_index["artifacts"].append(artifact)

        artifact_index["last_updated"] = datetime.now(timezone.utc).isoformat()
        artifact_index["last_verdict"] = verdict
        artifact_index["last_state"] = next_state
        artifact_index["last_action"] = next_action

        with open(artifact_index_path, "w", encoding="utf-8") as f:
            json.dump(artifact_index, f, indent=2, ensure_ascii=False)

    def update_episode_ledger(
        self, verdict: str, next_state: str, next_action: str
    ) -> None:
        """Update the episode ledger."""
        ledger_path = self.control_dir / "episode_ledger.json"

        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        else:
            ledger = {"episodes": []}

        # Ensure ledger has episodes key
        if not isinstance(ledger, dict):
            ledger = {"episodes": []}
        if "episodes" not in ledger:
            ledger["episodes"] = []
        if not isinstance(ledger["episodes"], list):
            ledger["episodes"] = []

        # Add new episode entry
        episode = {
            "episode_id": f"visual_reference_curator_{int(datetime.now(timezone.utc).timestamp())}",
            "agent": "visual_reference_curator",
            "task_id": "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001",
            "verdict": verdict,
            "next_state": next_state,
            "next_action": next_action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        }

        ledger["episodes"].append(episode)

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)

    def update_state(self, next_state: str, next_action: str) -> None:
        """Update the state file."""
        state_path = self.control_dir / "state.json"

        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {}

        state["current_state"] = next_state
        state["next_allowed_action"] = next_action
        state["production_accepted"] = False
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
