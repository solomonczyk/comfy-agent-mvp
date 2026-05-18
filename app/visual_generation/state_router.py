"""
State router for controlled fresh visual generation.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class GenerationStateRouter:
    """Updates artifact_index, episode_ledger, and state after generation."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"

    def route_success(self, manifest: Dict[str, Any], proof: Dict[str, Any]) -> Dict[str, Any]:
        """Route to fresh_visual_candidate_operator_review_required state."""
        state = {
            "current_state": "fresh_visual_candidate_operator_review_required",
            "next_allowed_action": "fresh_visual_candidate_operator_review_required",
            "generation_performed": True,
            "generation_count": 1,
            "retry_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "task_id": self.TASK_ID,
            "timestamp": self._now(),
        }
        self._update_state(state)
        self._update_artifact_index(state, manifest)
        self._update_episode_ledger(state, manifest)
        return state

    def route_blocker(self, preflight_report: Dict[str, Any]) -> Dict[str, Any]:
        """Route to controlled_visual_generation_blocked state."""
        state = {
            "current_state": "controlled_visual_generation_blocked",
            "next_allowed_action": "controlled_visual_generation_blocker_review_required",
            "generation_performed": False,
            "generation_count": 0,
            "retry_attempted": False,
            "production_accepted": False,
            "task_id": self.TASK_ID,
            "timestamp": self._now(),
            "blockers": preflight_report.get("blockers", []),
        }
        self._update_state(state)
        self._update_artifact_index(state, {})
        self._update_episode_ledger(state, {})
        return state

    def route_execution_failure(self, exec_report: Dict[str, Any]) -> Dict[str, Any]:
        """Route to fresh_visual_generation_result_reconciliation_required state."""
        state = {
            "current_state": "fresh_visual_generation_result_reconciliation_required",
            "next_allowed_action": "fresh_visual_generation_result_reconciliation_required",
            "generation_attempted": True,
            "generation_count": 1,
            "retry_attempted": False,
            "production_accepted": False,
            "task_id": self.TASK_ID,
            "timestamp": self._now(),
            "failure_reason": exec_report.get("failure_reason"),
        }
        self._update_state(state)
        self._update_artifact_index(state, {})
        self._update_episode_ledger(state, {})
        return state

    def _update_state(self, new_state: Dict[str, Any]) -> None:
        state_path = self.control_dir / "state.json"
        existing: Dict[str, Any] = {}
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.update(new_state)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def _update_artifact_index(
        self, state: Dict[str, Any], manifest: Dict[str, Any]
    ) -> None:
        index_path = self.control_dir / "artifact_index.json"
        index: Dict[str, Any] = {}
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)

        index["current_state"] = state["current_state"]
        index["next_allowed_action"] = state["next_allowed_action"]
        index["production_accepted"] = False
        index["fresh_visual_candidate_task"] = self.TASK_ID
        index["fresh_visual_candidate_dir"] = "fresh_visual_candidate/"
        index["fresh_visual_strategy_operator_review_dir"] = "fresh_visual_strategy_operator_review/"
        index["controlled_visual_generation_gate_dir"] = "controlled_visual_generation_gate/"

        if manifest.get("generated_assets"):
            index["fresh_visual_candidate_manifest"] = (
                "fresh_visual_candidate/generated_candidate_manifest.json"
            )
            index["fresh_visual_candidate_proof"] = (
                "fresh_visual_candidate/generated_candidate_proof.json"
            )

        stage_entry = {
            "stage": "fresh_visual_candidate_generation",
            "success": state.get("generation_performed", False),
            "message": (
                "Fresh visual candidate generated via controlled generation gate."
                if state.get("generation_performed")
                else f"Controlled generation blocked: {state.get('blockers', state.get('failure_reason', 'unknown'))}"
            ),
            "artifacts": [
                "fresh_visual_strategy_operator_review/operator_review_packet.json",
                "fresh_visual_strategy_operator_review/operator_review_proof.json",
                "controlled_visual_generation_gate/generation_gate_plan.json",
                "controlled_visual_generation_gate/generation_gate_authorization.json",
                "controlled_visual_generation_gate/generation_preflight_report.json",
                "fresh_visual_candidate/generation_execution_report.json",
                "fresh_visual_candidate/generated_candidate_manifest.json",
                "fresh_visual_candidate/generated_candidate_proof.json",
            ],
            "metadata": {
                "task_id": self.TASK_ID,
                "generation_performed": state.get("generation_performed", False),
                "generation_count": state.get("generation_count", 0),
                "retry_attempted": False,
                "second_generation_attempted": False,
                "visual_qa_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "production_accepted": False,
                "prompt_id": manifest.get("prompt_id"),
            },
            "timestamp": self._now(),
            "no_generation_performed": not state.get("generation_performed", False),
        }

        if "stage_results" not in index:
            index["stage_results"] = []
        index["stage_results"].append(stage_entry)
        index["timestamp"] = self._now()

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _update_episode_ledger(
        self, state: Dict[str, Any], manifest: Dict[str, Any]
    ) -> None:
        ledger_path = self.control_dir / "episode_ledger.json"
        ledger: list = []
        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)

        entry = {
            "event_type": "fresh_visual_candidate_generation",
            "task_id": self.TASK_ID,
            "stage": "fresh_visual_candidate_generation",
            "generation_performed": state.get("generation_performed", False),
            "generation_count": state.get("generation_count", 0),
            "max_generations": 1,
            "second_generation_attempted": False,
            "retry_attempted": False,
            "workflow_submitted": state.get("generation_performed", False),
            "comfyui_execution": state.get("generation_performed", False),
            "prompt_id": manifest.get("prompt_id"),
            "generated_assets": [
                a.get("path") for a in manifest.get("generated_assets", []) if a.get("path")
            ],
            "asset_count": len(
                [a for a in manifest.get("generated_assets", []) if a.get("exists")]
            ),
            "production_accepted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "current_state": state["current_state"],
            "next_allowed_action": state["next_allowed_action"],
            "timestamp": self._now(),
        }

        ledger.append(entry)
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
