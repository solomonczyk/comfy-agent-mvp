import json

from app.agents.real_generation_readiness_agent import RealGenerationReadinessAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineRetryRealGenerationReadinessPack:
    """RC-COMBINE-V2-171-220 — corrective retry real generation readiness pack tests."""

    def test_real_generation_readiness_with_corrective_retry_payload(self, tmp_path):
        """Test that real_generation_readiness_required stage recognizes corrective retry payload."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Base generation artifacts
        with open(control_dir / "combine_v2_generation_payload_stub.json", "w") as f:
            json.dump({"workflow_id": "wf_corrective_retry", "prompts": ["corrected prompt"]}, f)
        with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
            json.dump({"plan_id": "plan_corrective_retry"}, f)

        # Retry context artifacts
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)

        # Corrective retry payload artifacts
        with open(control_dir / "combine_v2_corrective_retry_generation_payload.json", "w") as f:
            json.dump({
                "payload_type": "corrective_retry_generation_payload",
                "corrective_plan_applied": True,
                "source_failure": "visual_quality_failure"
            }, f)

        agent = RealGenerationReadinessAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify readiness report created
        assert "combine_v2_real_generation_readiness_report.json" in result.artifacts
        assert (control_dir / "combine_v2_real_generation_readiness_report.json").exists()

        # Verify readiness status
        readiness_report = result.metadata["combine_v2_real_generation_readiness_report"]
        assert readiness_report["stage"] == "real_generation_readiness_required"
        assert readiness_report["next_allowed_action"] == "real_generation_preflight_required"

        # Verify boundary flags
        assert readiness_report["generation_performed"] is False
        assert readiness_report["comfyui_execution"] is False
        assert readiness_report["downstream_executed"] is False
        assert readiness_report["production_accepted"] is False

    def test_real_generation_payload_review_uses_corrective_retry_payload(self, tmp_path):
        """Test that real_generation_payload_review stage incorporates corrective retry context."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Base generation artifacts
        with open(control_dir / "combine_v2_generation_payload_stub.json", "w") as f:
            json.dump({
                "workflow_id": "wf_corrective_retry",
                "prompts": ["corrected prompt"],
                "retry_context": {
                    "retry_requested": True,
                    "operator_retry_authorized": True,
                    "corrective_plan_applied_to_payload": True,
                    "retry_execution_authorized": False
                }
            }, f)
        with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
            json.dump({"plan_id": "plan_corrective_retry"}, f)
        with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
            json.dump({"trace_id": "trace_001"}, f)
        with open(control_dir / "combine_v2_workflow_contract.json", "w") as f:
            json.dump({"workflow_id": "wf_corrective_retry"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", "w") as f:
            json.dump({"prompts": ["corrected prompt"]}, f)
        with open(control_dir / "combine_v2_asset_requirements_contract.json", "w") as f:
            json.dump({"assets": {}}, f)
        with open(control_dir / "combine_v2_preflight_contract.json", "w") as f:
            json.dump({"preflight_passed": True}, f)

        from app.agents.generation_agent import GenerationAgent
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="real_generation_payload_review",
            stage="real_generation_payload_review",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify artifacts created
        assert "combine_v2_real_generation_payload.json" in result.artifacts
        assert "combine_v2_real_generation_execution_contract.json" in result.artifacts

        # Verify corrective retry context preserved
        real_payload = result.metadata["combine_v2_real_generation_payload"]
        assert real_payload["retry_context"]["retry_requested"] is True
        assert real_payload["retry_context"]["operator_retry_authorized"] is True
        assert real_payload["retry_context"]["corrective_plan_applied_to_payload"] is True

        # Verify execution contract boundary flags
        execution_contract = result.metadata["combine_v2_real_generation_execution_contract"]
        assert execution_contract["generation_performed"] is False
        assert execution_contract["comfyui_execution"] is False
        assert execution_contract["workflow_submitted"] is False
        assert execution_contract["downstream_executed"] is False
        assert execution_contract["production_accepted"] is False

        # Verify next action
        assert result.next_recommended_stage == "operator_real_generation_authorization_required"
        assert execution_contract["next_allowed_action"] == "operator_real_generation_authorization_required"

    def test_operator_real_generation_authorization_request_created(self, tmp_path):
        """Test that operator_real_generation_authorization_required stage creates authorization request."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        agent = RealGenerationReadinessAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="operator_real_generation_authorization_required",
            stage="operator_real_generation_authorization_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify authorization request created
        assert "combine_v2_operator_real_generation_authorization_request.json" in result.artifacts
        assert (control_dir / "combine_v2_operator_real_generation_authorization_request.json").exists()

        # Verify authorization request structure
        auth_request = result.metadata["combine_v2_operator_real_generation_authorization_request"]
        assert auth_request["stage"] == "operator_real_generation_authorization_required"
        assert auth_request["request_type"] == "real_comfyui_generation_authorization"
        assert auth_request["requires_operator_confirmation"] is True
        assert auth_request["will_execute_comfyui_if_approved_later"] is True
        assert auth_request["current_layer_executes_comfyui"] is False

        # Verify boundary flags
        assert auth_request["generation_performed"] is False
        assert auth_request["comfyui_execution"] is False
        assert auth_request["downstream_executed"] is False
        assert auth_request["production_accepted"] is False

        # Verify next action
        assert result.next_recommended_stage == "operator_real_generation_authorization_required"
        assert auth_request["next_allowed_action"] == "operator_real_generation_authorization_required"

    def test_corrective_retry_chain_boundary_flags_maintained(self, tmp_path):
        """Test that the entire corrective retry chain maintains no-generation boundary."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Setup for full chain test
        artifacts_to_create = {
            "combine_v2_generation_payload_stub.json": {"workflow_id": "wf_test"},
            "combine_v2_generation_execution_plan.json": {"plan_id": "plan_test"},
            "combine_v2_retry_authorization_request.json": {"request_id": "REQ-001"},
            "combine_v2_corrective_retry_generation_payload.json": {"payload_type": "corrective_retry_generation_payload"},
        }

        for filename, content in artifacts_to_create.items():
            with open(control_dir / filename, "w") as f:
                json.dump(content, f)

        # Test real_generation_readiness_required
        agent = RealGenerationReadinessAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="real_generation_readiness_required",
            stage="real_generation_readiness_required",
            route_family="custom",
            dry_run=True,
        )
        result = agent.run(context)
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False

        # Test operator_real_generation_authorization_required
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="operator_real_generation_authorization_required",
            stage="operator_real_generation_authorization_required",
            route_family="custom",
            dry_run=True,
        )
        result = agent.run(context)
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.metadata["combine_v2_operator_real_generation_authorization_request"]["generation_performed"] is False
        assert result.metadata["combine_v2_operator_real_generation_authorization_request"]["comfyui_execution"] is False
        assert result.metadata["combine_v2_operator_real_generation_authorization_request"]["downstream_executed"] is False
        assert result.metadata["combine_v2_operator_real_generation_authorization_request"]["production_accepted"] is False
