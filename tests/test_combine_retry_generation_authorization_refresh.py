import json

from app.agents.generation_agent import GenerationAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineRetryGenerationAuthorizationRefresh:
    """RC-COMBINE-V2-12 — refresh generation authorization with retry context."""

    def test_generation_authorization_refresh_is_retry_aware(self, tmp_path):
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Base generation inputs
        with open(control_dir / "combine_v2_asset_gate_decision.json", "w") as f:
            json.dump({"missing_assets": [], "inventory": {"hero": "asset_001"}}, f)
        with open(control_dir / "combine_v2_workflow_contract.json", "w") as f:
            json.dump({"workflow_id": "wf_retry_refresh"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", "w") as f:
            json.dump({"prompts": ["retry prompt"]}, f)
        with open(control_dir / "combine_v2_preflight_contract.json", "w") as f:
            json.dump({"preflight_passed": True}, f)

        # Retry-aware inputs that must be consumed
        with open(control_dir / "combine_v2_retry_failure_classification.json", "w") as f:
            json.dump({"classification": "visual_quality_failure", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-001", "actions": ["adjust_prompt"]}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)
        with open(control_dir / "combine_v2_operator_retry_authorization.json", "w") as f:
            json.dump({"operator_retry_authorized": True, "retry_gate_open": False}, f)
        with open(control_dir / "combine_v2_retry_gate_decision.json", "w") as f:
            json.dump({"retry_gate_open": False, "retry_executed": False}, f)

        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="generation_authorization_required",
            stage="generation_authorization_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)
        payload = result.metadata["combine_v2_generation_payload_stub"]
        retry_context = payload["retry_context"]
        decision = result.metadata["combine_v2_generation_authorization_decision"]

        # 1-3. Retry corrective/authorization/gate inputs are read
        assert "combine_v2_retry_corrective_plan.json" in result.metadata["loaded_retry_artifacts"]
        assert "combine_v2_operator_retry_authorization.json" in result.metadata["loaded_retry_artifacts"]
        assert "combine_v2_retry_gate_decision.json" in result.metadata["loaded_retry_artifacts"]

        # 4-5. payload has retry context and corrective plan is applied
        assert retry_context["retry_requested"] is True
        assert retry_context["operator_retry_authorized"] is True
        assert retry_context["corrective_plan_applied_to_payload"] is True
        assert result.metadata["corrective_plan_applied_to_payload"] is True

        # 6-12. Boundary behavior remains no-generation / no-downstream
        assert retry_context["retry_gate_open"] is False
        assert decision["generation_authorized"] is False
        assert decision["authorization_required"] is True
        assert decision["next_allowed_action"] == "operator_generation_authorization_required"
        assert decision["retry_executed"] is False
        assert decision["generation_performed"] is False
        assert decision["comfyui_execution"] is False
        assert decision["downstream_executed"] is False

