"""Tests for Camera Operator Agent — RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CAMERA_OPERATOR_DIR = DATA_ROOT / "output" / "control" / "camera_operator_agent"


class TestCameraOperatorAgentContract:
    """Test Camera Operator Agent contract creation."""

    def test_camera_operator_agent_contract_exists(self):
        """Test that camera operator agent contract file exists."""
        contract_path = CAMERA_OPERATOR_DIR / "camera_operator_agent_contract.json"
        assert contract_path.exists(), f"Contract file not found: {contract_path}"

    def test_camera_operator_agent_contract_structure(self):
        """Test that camera operator agent contract has required fields."""
        contract_path = CAMERA_OPERATOR_DIR / "camera_operator_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)

        required_fields = [
            "agent_id",
            "agent_role",
            "responsibility_zone",
            "can_execute_generation",
            "generation_requires_operator_authorization",
            "can_retry",
            "can_accept_visual",
            "can_set_production_accepted",
            "can_run_assembly",
            "can_run_downstream",
            "required_inputs",
            "required_outputs",
            "stop_condition",
        ]

        for field in required_fields:
            assert field in contract, f"Missing required field: {field}"

    def test_camera_operator_agent_contract_forbidden_actions(self):
        """Test that camera operator agent contract includes strict forbidden actions."""
        contract_path = CAMERA_OPERATOR_DIR / "camera_operator_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)

        assert contract.get("can_retry") is False
        assert contract.get("can_accept_visual") is False
        assert contract.get("can_set_production_accepted") is False
        assert contract.get("can_run_assembly") is False
        assert contract.get("can_run_downstream") is False

    def test_camera_operator_agent_contract_max_generations(self):
        """Test that camera operator agent contract enforces max one generation."""
        contract_path = CAMERA_OPERATOR_DIR / "camera_operator_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)

        assert contract.get("can_execute_generation") is True
        assert contract.get("generation_requires_operator_authorization") is True

    def test_camera_operator_tool_policy_exists(self):
        """Test that camera operator tool policy file exists."""
        policy_path = CAMERA_OPERATOR_DIR / "camera_operator_tool_policy.json"
        assert policy_path.exists(), f"Tool policy file not found: {policy_path}"

    def test_camera_operator_tool_policy_structure(self):
        """Test that camera operator tool policy has required fields."""
        policy_path = CAMERA_OPERATOR_DIR / "camera_operator_tool_policy.json"
        with open(policy_path, 'r', encoding='utf-8') as f:
            policy = json.load(f)

        required_fields = [
            "agent_id",
            "allowed_tools",
            "forbidden_tools",
            "max_comfyui_submits",
        ]

        for field in required_fields:
            assert field in policy, f"Missing required field: {field}"

    def test_camera_operator_tool_policy_generation_limits(self):
        """Test that camera operator tool policy enforces generation limits."""
        policy_path = CAMERA_OPERATOR_DIR / "camera_operator_tool_policy.json"
        with open(policy_path, 'r', encoding='utf-8') as f:
            policy = json.load(f)

        assert policy.get("max_comfyui_submits") == 1
        forbidden_tools = policy.get("forbidden_tools", [])
        assert "comfyui.submit_without_authorization" in forbidden_tools
        assert "comfyui.submit_second_generation" in forbidden_tools
        assert "generation.retry" in forbidden_tools

    def test_camera_operator_authorization_exists(self):
        """Test that camera operator authorization file exists."""
        auth_path = CAMERA_OPERATOR_DIR / "operator_authorization_one_full_frame_generation.json"
        assert auth_path.exists(), f"Authorization file not found: {auth_path}"

    def test_camera_operator_authorization_structure(self):
        """Test that camera operator authorization has required fields."""
        auth_path = CAMERA_OPERATOR_DIR / "operator_authorization_one_full_frame_generation.json"
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth = json.load(f)

        required_fields = [
            "task_id",
            "operator_authorized",
            "authorized_action",
            "authorization_source",
            "max_generations",
            "generation_gate_open",
            "target_output_type",
            "body_part_crop_forbidden",
            "stop_after_generation",
            "operator_visual_review_required_after_generation",
            "retry_authorized",
            "second_generation_allowed",
            "assembly_allowed",
            "downstream_allowed",
        ]

        for field in required_fields:
            assert field in auth, f"Missing required field: {field}"


class TestCameraOperatorValidator:
    """Test Camera Operator Agent validator."""

    def test_pre_generation_validation_report_exists(self):
        """Test that pre-generation validation report exists."""
        report_path = CAMERA_OPERATOR_DIR / "pre_generation_full_frame_validation_report.json"
        assert report_path.exists(), f"Validation report not found: {report_path}"

    def test_pre_generation_validation_report_structure(self):
        """Test that pre-generation validation report has required fields."""
        report_path = CAMERA_OPERATOR_DIR / "pre_generation_full_frame_validation_report.json"
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        required_fields = [
            "task_id",
            "validation_timestamp",
            "full_frame_contract_exists",
            "reference_usage_policy_exists",
            "prompt_recipe_exists",
            "operator_authorization_exists",
            "body_part_crop_forbidden",
            "ready_for_one_generation",
            "blockers",
        ]

        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

    def test_pre_generation_validation_report_ready(self):
        """Test that pre-generation validation report indicates ready for generation."""
        report_path = CAMERA_OPERATOR_DIR / "pre_generation_full_frame_validation_report.json"
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        assert report.get("ready_for_one_generation") is True
        assert len(report.get("blockers", [])) == 0


class TestCameraOperatorRunner:
    """Test Camera Operator Agent runner."""

    def test_generation_manifest_exists(self):
        """Test that generation manifest exists."""
        manifest_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_manifest.json"
        assert manifest_path.exists(), f"Generation manifest not found: {manifest_path}"

    def test_generation_manifest_structure(self):
        """Test that generation manifest has required fields."""
        manifest_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        required_fields = [
            "task_id",
            "agent_id",
            "generation_performed",
            "generation_count",
            "max_generations",
            "workflow_submitted",
            "comfyui_execution",
            "prompt_id",
            "generated_assets",
            "second_generation_attempted",
            "retry_attempted",
            "timestamp",
        ]

        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

    def test_generation_manifest_count(self):
        """Test that generation manifest shows exactly one generation."""
        manifest_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest.get("generation_count") == 1
        assert manifest.get("max_generations") == 1

    def test_generation_manifest_asset_exists(self):
        """Test that generation manifest includes generated asset."""
        manifest_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assets = manifest.get("generated_assets", [])
        assert len(assets) > 0, "No generated assets found"

        first_asset = assets[0]
        assert "path" in first_asset
        assert "sha256" in first_asset
        assert "size_bytes" in first_asset
        assert "width" in first_asset
        assert "height" in first_asset


class TestCameraOperatorArtifacts:
    """Test Camera Operator Agent artifacts."""

    def test_generation_result_review_exists(self):
        """Test that generation result review exists."""
        review_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_result_review.json"
        assert review_path.exists(), f"Generation result review not found: {review_path}"

    def test_generation_result_review_structure(self):
        """Test that generation result review has required fields."""
        review_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_result_review.json"
        with open(review_path, 'r', encoding='utf-8') as f:
            review = json.load(f)

        required_fields = [
            "technical_result_review_executed",
            "asset_exists",
            "asset_readable",
            "sha256_recorded",
            "dimensions_recorded",
            "non_stub_asset",
            "manifest_matches_filesystem",
            "visual_acceptance_executed",
            "operator_visual_review_required",
            "production_accepted",
        ]

        for field in required_fields:
            assert field in review, f"Missing required field: {field}"

    def test_generation_result_review_no_second_generation(self):
        """Test that generation result review confirms no automatic acceptance."""
        review_path = CAMERA_OPERATOR_DIR / "camera_operator_generation_result_review.json"
        with open(review_path, 'r', encoding='utf-8') as f:
            review = json.load(f)

        assert review.get("visual_acceptance_executed") is False
        assert review.get("operator_visual_review_required") is True
        assert review.get("production_accepted") is False

    def test_operator_visual_review_packet_exists(self):
        """Test that operator visual review packet exists."""
        packet_path = CAMERA_OPERATOR_DIR / "operator_visual_review_packet.json"
        assert packet_path.exists(), f"Operator visual review packet not found: {packet_path}"

    def test_operator_visual_review_packet_structure(self):
        """Test that operator visual review packet has required fields."""
        packet_path = CAMERA_OPERATOR_DIR / "operator_visual_review_packet.json"
        with open(packet_path, 'r', encoding='utf-8') as f:
            packet = json.load(f)

        required_fields = [
            "review_type",
            "review_required",
            "generated_asset",
            "operator_must_decide",
            "agent_recommendation_allowed",
            "agent_acceptance_allowed",
            "production_accepted",
            "assembly_allowed",
            "downstream_allowed",
            "task_id",
        ]

        for field in required_fields:
            assert field in packet, f"Missing required field: {field}"

    def test_operator_visual_review_packet_requires_review(self):
        """Test that operator visual review packet requires operator review."""
        packet_path = CAMERA_OPERATOR_DIR / "operator_visual_review_packet.json"
        with open(packet_path, 'r', encoding='utf-8') as f:
            packet = json.load(f)

        assert packet.get("review_required") is True
        assert packet.get("agent_recommendation_allowed") is False
        assert packet.get("agent_acceptance_allowed") is False
        assert packet.get("production_accepted") is False
        assert packet.get("assembly_allowed") is False
        assert packet.get("downstream_allowed") is False

    def test_proof_json_exists(self):
        """Test that proof JSON exists."""
        proof_path = CAMERA_OPERATOR_DIR / "proof.json"
        assert proof_path.exists(), f"Proof JSON not found: {proof_path}"

    def test_proof_json_structure(self):
        """Test that proof JSON has required fields."""
        proof_path = CAMERA_OPERATOR_DIR / "proof.json"
        with open(proof_path, 'r', encoding='utf-8') as f:
            proof = json.load(f)

        required_fields = [
            "task_id",
            "feature_completed",
            "agent_vertical_completed",
            "agent_id",
            "operator_authorization_recorded",
            "generation_gate_opened_for_this_task",
            "full_frame_contract_validated",
            "reference_scope_policy_validated",
            "prompt_recipe_validated",
            "body_part_crop_forbidden",
            "generation_performed",
            "generation_count",
            "max_generations",
            "second_generation_attempted",
            "retry_attempted",
            "workflow_submitted",
            "comfyui_execution",
            "prompt_id",
            "generated_assets",
            "generation_manifest_created",
            "generation_result_review_created",
            "operator_visual_review_packet_created",
            "artifact_index_updated",
            "episode_ledger_updated",
            "state_updated",
            "current_state",
            "next_allowed_action",
            "tests_pass",
            "py_compile_pass",
            "cli_dry_run_pass",
            "cli_execute_pass",
            "cli_status_pass",
        ]

        for field in required_fields:
            assert field in proof, f"Missing required field: {field}"

    def test_proof_json_success(self):
        """Test that proof JSON indicates successful execution."""
        proof_path = CAMERA_OPERATOR_DIR / "proof.json"
        with open(proof_path, 'r', encoding='utf-8') as f:
            proof = json.load(f)

        assert proof.get("feature_completed") is True
        assert proof.get("agent_vertical_completed") is True
        assert proof.get("generation_performed") is True
        assert proof.get("generation_count") == 1
        assert proof.get("max_generations") == 1
        assert proof.get("current_state") == "operator_visual_review_required"
        assert proof.get("next_allowed_action") == "operator_visual_review_required"


class TestCameraOperatorStateUpdates:
    """Test Camera Operator Agent state updates."""

    def test_state_json_updated(self):
        """Test that state.json was updated with camera operator completion."""
        state_path = DATA_ROOT / "output" / "control" / "state.json"
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        assert state.get("camera_operator_vertical_completed") is True
        assert state.get("full_frame_corrective_generation_performed") is True
        assert state.get("operator_visual_review_completed") is True
        assert state.get("current_state") == "next_visual_gate_authorization_required"
        assert state.get("next_allowed_action") == "next_visual_gate_authorization_required"

    def test_artifact_index_updated(self):
        """Test that artifact_index.json was updated with camera operator artifacts."""
        artifact_index_path = DATA_ROOT / "output" / "control" / "artifact_index.json"
        with open(artifact_index_path, 'r', encoding='utf-8') as f:
            artifact_index = json.load(f)

        assert artifact_index.get("camera_operator_vertical_completed") is True
        assert artifact_index.get("camera_operator_agent_contract_created") is True
        assert artifact_index.get("camera_operator_tool_policy_created") is True
        assert artifact_index.get("camera_operator_authorization_created") is True
        assert artifact_index.get("camera_operator_generation_manifest_created") is True
        assert artifact_index.get("camera_operator_generation_result_review_created") is True
        assert artifact_index.get("camera_operator_operator_visual_review_packet_created") is True

    def test_episode_ledger_updated(self):
        """Test that episode_ledger.json was updated with camera operator event."""
        ledger_path = DATA_ROOT / "output" / "control" / "episode_ledger.json"
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger = json.load(f)

        camera_operator_events = [
            e for e in ledger
            if e.get("event_type") == "camera_operator_generation"
        ]

        assert len(camera_operator_events) > 0, "No camera operator events found in ledger"

        latest_event = camera_operator_events[-1]
        assert latest_event.get("generation_count") == 1
        assert latest_event.get("max_generations") == 1
        assert latest_event.get("second_generation_attempted") is False
        assert latest_event.get("retry_attempted") is False
        assert latest_event.get("assembly_executed") is False
        assert latest_event.get("downstream_executed") is False
        assert latest_event.get("production_accepted") is False
        assert latest_event.get("operator_visual_review_required") is True


class TestCameraOperatorModules:
    """Test Camera Operator Agent Python modules."""

    def test_camera_operator_contract_module_imports(self):
        """Test that camera_operator contract module can be imported."""
        from app.agents.camera_operator.contract import CameraOperatorAgentContract

        assert CameraOperatorAgentContract is not None

    def test_camera_operator_validator_module_imports(self):
        """Test that camera_operator validator module can be imported."""
        from app.agents.camera_operator.validator import CameraOperatorValidator

        assert CameraOperatorValidator is not None

    def test_camera_operator_runner_module_imports(self):
        """Test that camera_operator runner module can be imported."""
        from app.agents.camera_operator.runner import CameraOperatorRunner

        assert CameraOperatorRunner is not None

    def test_camera_operator_artifacts_module_imports(self):
        """Test that camera_operator artifacts module can be imported."""
        from app.agents.camera_operator.artifacts import CameraOperatorArtifacts

        assert CameraOperatorArtifacts is not None

    def test_camera_operator_init_module_imports(self):
        """Test that camera_operator __init__ module can be imported."""
        from app.agents.camera_operator import (
            CameraOperatorAgentContract,
            CameraOperatorValidator,
            CameraOperatorRunner,
            CameraOperatorArtifacts,
        )

        assert CameraOperatorAgentContract is not None
        assert CameraOperatorValidator is not None
        assert CameraOperatorRunner is not None
        assert CameraOperatorArtifacts is not None
