"""
Controlled visual generation gate plan builder.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class GatePlanBuilder:
    """Builds the controlled generation gate plan artifacts."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.gate_dir = self.control_dir / "controlled_visual_generation_gate"
        self.strategy_dir = self.control_dir / "fresh_visual_strategy"

    def build(self, max_generations: int = 1) -> Dict[str, Any]:
        """Build gate_plan.json."""
        self.gate_dir.mkdir(parents=True, exist_ok=True)

        plan = {
            "task_id": self.TASK_ID,
            "document_type": "generation_gate_plan",
            "timestamp": self._now(),
            "gate_purpose": "Controlled fresh visual generation — exactly one candidate",
            "max_generations": max_generations,
            "gate_checks": {
                "fresh_visual_strategy_ready": True,
                "operator_strategy_acceptance_required": True,
                "qa_repairability_gate_active": True,
                "unknown_repairability_blocks": True,
                "workflow_must_be_selected": True,
                "workflow_file_must_exist": True,
                "workflow_validation_required": True,
                "required_models_must_be_available": True,
                "resolution_policy_must_pass": True,
                "output_path_must_be_canonical": True,
                "negative_references_must_be_loaded": True,
                "generation_count_before_run_must_be_zero": True,
            },
            "stop_conditions": {
                "stop_after_generation": True,
                "visual_qa_acceptance_allowed": False,
                "operator_visual_acceptance_allowed": False,
                "assembly_allowed": False,
                "downstream_allowed": False,
                "production_accepted": False,
                "retry_authorized": False,
                "second_generation_allowed": False,
            },
            "output_path_canonical": str(
                self.project_root / "output" / "assets" / "fresh_visual_candidates"
            ),
            "generation_authorized": False,
            "authorization_required_from": "human_operator",
        }

        self._write(self.gate_dir / "generation_gate_plan.json", plan)

        stop_conditions = {
            "task_id": self.TASK_ID,
            "document_type": "generation_stop_conditions",
            "timestamp": self._now(),
            "stop_after_first_generation": True,
            "max_generations": max_generations,
            "retry_authorized": False,
            "second_generation_authorized": False,
            "visual_qa_acceptance_authorized": False,
            "operator_visual_acceptance_authorized": False,
            "assembly_authorized": False,
            "downstream_authorized": False,
            "production_accepted": False,
            "stop_on_preflight_failure": True,
            "stop_on_generation_failure": True,
            "stop_on_reconciliation_failure": True,
        }
        self._write(self.gate_dir / "generation_stop_conditions.json", stop_conditions)

        return plan

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
