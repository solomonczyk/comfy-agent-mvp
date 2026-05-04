import json

from app.agents.generation_agent import GenerationAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineCorrectiveRetryPayloadRebuild:
    """RC-COMBINE-V2-171-220 — corrective retry payload rebuild stage tests."""

    def test_corrective_retry_payload_rebuild_creates_required_artifacts(self, tmp_path):
        """Test that corrective_retry_payload_rebuild_required stage creates all required artifacts."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Required input artifacts
        with open(control_dir / "combine_v2_visual_failure_classification.json", "w") as f:
            json.dump({"classification": "visual_quality_failure", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-001", "actions": ["adjust_prompt", "increase_steps"]}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)
        with open(control_dir / "combine_v2_operator_retry_authorization.json", "w") as f:
            json.dump({"operator_retry_authorized": True, "retry_gate_open": False}, f)
        with open(control_dir / "combine_v2_generation_payload_stub.json", "w") as f:
            json.dump({"workflow_id": "wf_retry", "prompts": ["original prompt"]}, f)
        with open(control_dir / "combine_v2_real_generation_payload.json", "w") as f:
            json.dump({"payload_type": "real_generation_candidate"}, f)
        with open(control_dir / "combine_v2_real_generation_execution_contract.json", "w") as f:
            json.dump({"contract_type": "real_generation_execution_contract"}, f)

        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="corrective_retry_payload_rebuild_required",
            stage="corrective_retry_payload_rebuild_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify artifacts created
        assert "combine_v2_corrective_retry_payload_rebuild_report.json" in result.artifacts
        assert "combine_v2_corrective_retry_prompt_patch.json" in result.artifacts
        assert "combine_v2_corrective_retry_generation_payload.json" in result.artifacts
        assert "combine_v2_corrective_retry_execution_contract.json" in result.artifacts

        # Verify artifact files exist
        assert (control_dir / "combine_v2_corrective_retry_payload_rebuild_report.json").exists()
        assert (control_dir / "combine_v2_corrective_retry_prompt_patch.json").exists()
        assert (control_dir / "combine_v2_corrective_retry_generation_payload.json").exists()
        assert (control_dir / "combine_v2_corrective_retry_execution_contract.json").exists()

    def test_corrective_retry_payload_rebuild_applies_corrective_plan(self, tmp_path):
        """Test that corrective plan is applied to payload."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Required input artifacts
        with open(control_dir / "combine_v2_visual_failure_classification.json", "w") as f:
            json.dump({"classification": "visual_quality_failure", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-001", "actions": ["adjust_prompt", "increase_steps"]}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)
        with open(control_dir / "combine_v2_operator_retry_authorization.json", "w") as f:
            json.dump({"operator_retry_authorized": True, "retry_gate_open": False}, f)
        with open(control_dir / "combine_v2_generation_payload_stub.json", "w") as f:
            json.dump({"workflow_id": "wf_retry", "prompts": ["original prompt"]}, f)

        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="corrective_retry_payload_rebuild_required",
            stage="corrective_retry_payload_rebuild_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify corrective plan applied
        assert result.metadata["corrective_plan_applied_to_payload"] is True
        assert result.metadata["prompt_patch_created"] is True
        assert result.metadata["generation_payload_refreshed"] is True
        assert result.metadata["execution_contract_refreshed"] is True

        # Verify source failure captured
        assert result.metadata["source_failure"] == "visual_quality_failure"

        # Verify next action
        assert result.next_recommended_stage == "real_generation_readiness_required"
        assert result.metadata["next_allowed_action"] == "real_generation_readiness_required"

    def test_corrective_retry_payload_rebuild_maintains_boundary_flags(self, tmp_path):
        """Test that boundary flags are maintained (no generation, no comfyui, no downstream)."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Required input artifacts
        with open(control_dir / "combine_v2_visual_failure_classification.json", "w") as f:
            json.dump({"classification": "visual_quality_failure", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-001", "actions": ["adjust_prompt"]}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)
        with open(control_dir / "combine_v2_operator_retry_authorization.json", "w") as f:
            json.dump({"operator_retry_authorized": True, "retry_gate_open": False}, f)

        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="corrective_retry_payload_rebuild_required",
            stage="corrective_retry_payload_rebuild_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify boundary flags
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False

        # Verify metadata boundary flags
        assert result.metadata["retry_execution_authorized"] is False
        assert result.metadata["generation_performed"] is False
        assert result.metadata["comfyui_execution"] is False
        assert result.metadata["workflow_submitted"] is False
        assert result.metadata["downstream_executed"] is False
        assert result.metadata["production_accepted"] is False

    def test_corrective_retry_payload_rebuild_report_structure(self, tmp_path):
        """Test that rebuild report has correct structure."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Required input artifacts
        with open(control_dir / "combine_v2_visual_failure_classification.json", "w") as f:
            json.dump({"classification": "production_quality_failed", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-002", "actions": ["adjust_prompt"]}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-002", "status": "pending_authorization"}, f)
        with open(control_dir / "combine_v2_operator_retry_authorization.json", "w") as f:
            json.dump({"operator_retry_authorized": True, "retry_gate_open": False}, f)

        agent = GenerationAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="corrective_retry_payload_rebuild_required",
            stage="corrective_retry_payload_rebuild_required",
            route_family="custom",
            dry_run=True,
        )

        result = agent.run(context)

        # Verify rebuild report structure
        rebuild_report = result.metadata["combine_v2_corrective_retry_payload_rebuild_report"]
        assert rebuild_report["stage"] == "corrective_retry_payload_rebuild_required"
        assert rebuild_report["corrective_plan_applied_to_payload"] is True
        assert rebuild_report["source_failure"] == "production_quality_failed"
        assert rebuild_report["prompt_patch_created"] is True
        assert rebuild_report["generation_payload_refreshed"] is True
        assert rebuild_report["execution_contract_refreshed"] is True
        assert rebuild_report["retry_execution_authorized"] is False
        assert rebuild_report["next_allowed_action"] == "real_generation_readiness_required"
        assert rebuild_report["generation_performed"] is False
        assert rebuild_report["comfyui_execution"] is False
        assert rebuild_report["workflow_submitted"] is False
        assert rebuild_report["downstream_executed"] is False
        assert rebuild_report["production_accepted"] is False
