"""
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
Fresh Visual Strategy Operator Review — strategy acceptance processing.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


VALID_VERDICTS = {
    "accepted_for_controlled_generation_gate_planning",
    "rejected_revision_required",
    "modification_required",
}

VALID_SOURCES = {"human_operator"}


class StrategyOperatorReviewBuilder:
    """Builds operator review artifacts for fresh visual strategy acceptance."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.strategy_dir = self.control_dir / "fresh_visual_strategy"
        self.review_dir = self.control_dir / "fresh_visual_strategy_operator_review"
        self.task_id = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_review_packet(self) -> Dict[str, Any]:
        """Build operator_review_packet.json from strategy artifacts."""
        self.review_dir.mkdir(parents=True, exist_ok=True)

        readiness = self._load_json("fresh_visual_strategy_readiness_report.json")
        review_packet_src = self._load_json("visual_strategy_operator_review_packet.json")
        brief = self._load_json("fresh_visual_strategy_brief.json")

        packet = {
            "task_id": self.task_id,
            "packet_type": "fresh_visual_strategy_operator_review_packet",
            "timestamp": self._now(),
            "strategy_readiness": {
                "overall_readiness": readiness.get("readiness_assessment", {}).get(
                    "overall_readiness", "ready_for_operator_review"
                ),
                "all_artifacts_valid": readiness.get("readiness_checklist", {}).get(
                    "all_artifacts_valid", True
                ),
                "qa_repairability_gate_active": readiness.get("policy_readiness", {}).get(
                    "qa_repairability_gate_active", True
                ),
            },
            "strategy_summary": review_packet_src.get("strategy_summary", {}),
            "operator_decision_options": [
                {
                    "verdict": "accepted_for_controlled_generation_gate_planning",
                    "description": "Accept strategy and proceed to controlled generation gate planning",
                    "next_state": "controlled_visual_generation_gate_planning_required",
                    "generation_authorized": False,
                },
                {
                    "verdict": "rejected_revision_required",
                    "description": "Reject — requires strategy revision",
                    "next_state": "fresh_visual_strategy_revision_required",
                    "generation_authorized": False,
                },
            ],
            "what_this_acceptance_authorizes": [
                "controlled_visual_generation_gate_planning_required",
            ],
            "what_this_acceptance_does_not_authorize": [
                "generation",
                "retry",
                "visual_acceptance",
                "assembly",
                "downstream",
                "production_accepted",
            ],
            "current_state": "fresh_visual_strategy_operator_review_required",
            "next_allowed_action": "fresh_visual_strategy_operator_review_required",
            "production_accepted": False,
            "generation_allowed": False,
        }

        self._write(self.review_dir / "operator_review_packet.json", packet)
        return packet

    def build_decision_schema(self) -> Dict[str, Any]:
        """Build operator_decision_schema.json."""
        schema = {
            "task_id": self.task_id,
            "schema_type": "operator_decision_schema",
            "timestamp": self._now(),
            "required_fields": {
                "decision_source": {
                    "type": "string",
                    "allowed_values": list(VALID_SOURCES),
                    "required": True,
                },
                "operator_name": {"type": "string", "required": True},
                "operator_verdict": {
                    "type": "string",
                    "allowed_values": list(VALID_VERDICTS),
                    "required": True,
                },
                "generation_authorized_by_strategy_review": {
                    "type": "boolean",
                    "must_be": False,
                    "required": True,
                },
                "production_accepted": {
                    "type": "boolean",
                    "must_be": False,
                    "required": True,
                },
            },
            "validation_rules": [
                "decision_source must be 'human_operator'",
                "generation_authorized_by_strategy_review must be false — strategy review does not authorize generation",
                "production_accepted must be false",
                "operator_verdict must be one of the allowed values",
            ],
        }
        self._write(self.review_dir / "operator_decision_schema.json", schema)
        return schema

    def process_operator_decision(
        self,
        operator_verdict: str,
        operator_source: str,
        operator_name: str = "Андрей",
    ) -> Dict[str, Any]:
        """Validate and record operator decision. Returns validation report."""
        errors: list[str] = []

        if operator_source not in VALID_SOURCES:
            errors.append(
                f"Invalid decision_source '{operator_source}': must be one of {VALID_SOURCES}"
            )
        if operator_verdict not in VALID_VERDICTS:
            errors.append(
                f"Invalid operator_verdict '{operator_verdict}': must be one of {VALID_VERDICTS}"
            )

        decision = {
            "task_id": self.task_id,
            "document_type": "operator_decision",
            "timestamp": self._now(),
            "decision_source": operator_source,
            "operator_name": operator_name,
            "operator_verdict": operator_verdict,
            "generation_authorized_by_strategy_review": False,
            "production_accepted": False,
            "validation_errors": errors,
            "decision_valid": len(errors) == 0,
        }

        validation_report = {
            "task_id": self.task_id,
            "report_type": "operator_decision_validation_report",
            "timestamp": self._now(),
            "decision_valid": len(errors) == 0,
            "errors": errors,
            "decision_source_valid": operator_source in VALID_SOURCES,
            "verdict_valid": operator_verdict in VALID_VERDICTS,
            "generation_authorized_locked_false": True,
            "production_accepted_locked_false": True,
        }

        # Routing decision
        if len(errors) == 0 and operator_verdict == "accepted_for_controlled_generation_gate_planning":
            next_state = "controlled_visual_generation_gate_planning_required"
            next_action = "controlled_visual_generation_gate_planning_required"
            generation_authorized = False
        else:
            next_state = "fresh_visual_strategy_operator_review_required"
            next_action = "fresh_visual_strategy_operator_review_required"
            generation_authorized = False

        routing_decision = {
            "task_id": self.task_id,
            "document_type": "operator_review_routing_decision",
            "timestamp": self._now(),
            "operator_verdict": operator_verdict,
            "decision_valid": len(errors) == 0,
            "next_state": next_state,
            "next_allowed_action": next_action,
            "generation_authorized": generation_authorized,
            "production_accepted": False,
        }

        state_transition = {
            "task_id": self.task_id,
            "document_type": "operator_review_state_transition_report",
            "timestamp": self._now(),
            "previous_state": "fresh_visual_strategy_operator_review_required",
            "previous_allowed_action": "fresh_visual_strategy_operator_review_required",
            "new_state": next_state,
            "new_allowed_action": next_action,
            "transition_trigger": "operator_strategy_review_decision",
            "operator_verdict": operator_verdict,
            "generation_performed": False,
            "retry_attempted": False,
            "production_accepted": False,
        }

        proof = {
            "task_id": self.task_id,
            "document_type": "operator_review_proof",
            "timestamp": self._now(),
            "operator_strategy_review_executed": True,
            "decision_source": operator_source,
            "operator_name": operator_name,
            "operator_verdict": operator_verdict,
            "decision_valid": len(errors) == 0,
            "next_state": next_state,
            "generation_authorized_by_strategy_review": False,
            "generation_performed": False,
            "retry_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        }

        self._write(self.review_dir / "operator_decision_validation_report.json", validation_report)
        self._write(self.review_dir / "operator_review_routing_decision.json", routing_decision)
        self._write(self.review_dir / "operator_review_state_transition_report.json", state_transition)
        self._write(self.review_dir / "operator_review_proof.json", proof)

        return {
            "decision": decision,
            "validation_report": validation_report,
            "routing_decision": routing_decision,
            "state_transition": state_transition,
            "proof": proof,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.strategy_dir / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
