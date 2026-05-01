"""Real Generation Readiness Agent.

Builds readiness and authorization artifacts for controlled real generation
without executing ComfyUI generation.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.agents.base import AgentResult, BaseRoleAgent
from app.orchestrator.contracts import CombineRunContext


class RealGenerationReadinessAgent(BaseRoleAgent):
    """Prepare execution-readiness artifacts for real generation."""

    @property
    def supported_stages(self) -> List[str]:
        return [
            "real_generation_readiness_required",
            "real_generation_preflight_required",
            "operator_real_generation_authorization_required",
            "operator_real_generation_approved",
        ]

    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]

    @property
    def output_contract_type(self) -> str:
        return "RealGenerationReadinessContract"

    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)

    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=True,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="none",
            metadata={"action": "real_generation_readiness_stub"},
        )

    @staticmethod
    def _read_json_if_exists(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        stage = context.stage
        project_root = Path(context.project_root)
        control_dir = project_root / "output" / "control"
        timestamp = datetime.utcnow().isoformat()

        if stage == "real_generation_readiness_required":
            required_artifacts = {
                "combine_v2_generation_payload_stub.json": "generation_payload_stub_available",
                "combine_v2_generation_execution_plan.json": "execution_plan_available",
                "combine_v2_retry_authorization_request.json": "retry_context_available",
            }
            checks = {
                "canonical_state_available": True,
                "generation_gate_open": True,
                "retry_context_available": False,
                "generation_payload_stub_available": False,
                "execution_plan_available": False,
                "project_root_is_absolute": project_root.is_absolute(),
                "output_control_available": control_dir.exists(),
            }
            for filename, key in required_artifacts.items():
                checks[key] = (control_dir / filename).exists()

            blockers: List[str] = []
            if not checks["project_root_is_absolute"]:
                blockers.append("PROJECT_ROOT_NOT_ABSOLUTE")
            if not checks["output_control_available"]:
                blockers.append("OUTPUT_CONTROL_MISSING")
            if not checks["generation_payload_stub_available"]:
                blockers.append("GENERATION_PAYLOAD_STUB_MISSING")
            if not checks["execution_plan_available"]:
                blockers.append("GENERATION_EXECUTION_PLAN_MISSING")
            if not checks["retry_context_available"]:
                blockers.append("RETRY_CONTEXT_MISSING")

            status = "ready_for_preflight" if not blockers else "blocked"
            next_allowed_action = (
                "real_generation_preflight_required"
                if status == "ready_for_preflight"
                else "real_generation_readiness_required"
            )
            report = {
                "stage": stage,
                "status": status,
                "checks": checks,
                "blockers": blockers,
                "next_allowed_action": next_allowed_action,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "production_accepted": False,
                "timestamp": timestamp,
            }
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok" if status != "blocked" else "blocked",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_real_generation_readiness_report.json"],
                next_recommended_stage=next_allowed_action,
                metadata={
                    "next_allowed_action": next_allowed_action,
                    "combine_v2_real_generation_readiness_report": report,
                },
            )

        if stage == "operator_real_generation_authorization_required":
            request = {
                "stage": stage,
                "request_type": "real_comfyui_generation_authorization",
                "requires_operator_confirmation": True,
                "will_execute_comfyui_if_approved_later": True,
                "current_layer_executes_comfyui": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "production_accepted": False,
                "next_allowed_action": "operator_real_generation_authorization_required",
                "timestamp": timestamp,
            }
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_operator_real_generation_authorization_request.json"],
                next_recommended_stage="operator_real_generation_authorization_required",
                metadata={
                    "next_allowed_action": "operator_real_generation_authorization_required",
                    "combine_v2_operator_real_generation_authorization_request": request,
                },
            )

        if stage == "operator_real_generation_approved":
            approved = {
                "stage": stage,
                "operator_real_generation_authorized": True,
                "real_generation_gate_open": True,
                "next_allowed_action": "real_generate_assets",
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "production_accepted": False,
                "timestamp": timestamp,
            }
            return AgentResult(
                agent=self.role_name,
                stage=stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=[],
                next_recommended_stage="real_generate_assets",
                metadata={
                    "next_allowed_action": "real_generate_assets",
                    "operator_real_generation_approved": approved,
                },
            )

        # Preflight report is produced by CLI preflight contract; stage kept for compatibility.
        preflight_report = self._read_json_if_exists(
            control_dir / "combine_v2_real_generation_preflight_report.json"
        )
        next_allowed_action = preflight_report.get(
            "next_allowed_action", "real_generation_preflight_required"
        )
        status = "ok" if preflight_report else "blocked"
        return AgentResult(
            agent=self.role_name,
            stage=stage,
            status=status,
            dry_run=True,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=["combine_v2_real_generation_preflight_report.json"] if preflight_report else [],
            next_recommended_stage=next_allowed_action,
            metadata={
                "next_allowed_action": next_allowed_action,
                "combine_v2_real_generation_preflight_report": preflight_report,
            },
        )
