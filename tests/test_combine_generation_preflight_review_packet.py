"""Tests for Generation Preflight Operator Review Packet.

RC-COMBINE-V2-70001-86000
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.workflow_assets import build_generation_preflight_operator_review
from app.workflow_assets.workflow_assets_package import (
    _build_generation_preflight_operator_review_packet,
    _paths,
    _now_iso,
    WorkflowValidationReport,
    AssetVerificationReport,
    AssetResolutionPlan,
    WorkflowSelectionReport,
    GenerationPreflightOperatorReviewPacket,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _create_all_workflow_assets(project_root: Path, ready: bool = True) -> None:
    """Create all workflow_assets artifacts for testing operator review packet."""
    wa_dir = project_root / "output" / "control" / "workflow_assets"
    control_dir = project_root / "output" / "control"

    # Workflow inventory
    _write_json(wa_dir / "workflow_inventory.json", {
        "total_workflow_families": 6,
        "real_workflows_available": 4,
        "stub_workflows_detected_and_blocked": 2,
        "legacy_512_workflow_blocked": True,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
    })

    # Workflow selection report
    _write_json(wa_dir / "workflow_selection_report.json", {
        "total_shots_mapped": 2,
        "shot_workflow_bindings": [
            {
                "shot_id": "shot_001", "scene_id": "scene_001",
                "selected_workflow_family": "sdxl_txt2img",
                "workflow_readiness_status": "ready",
            },
            {
                "shot_id": "shot_002", "scene_id": "scene_001",
                "selected_workflow_family": "sdxl_txt2img",
                "workflow_readiness_status": "ready",
            },
        ],
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
    })

    # Workflow patch plan
    _write_json(wa_dir / "workflow_patch_plan.json", {
        "legacy_512_workflow_blocked": True,
        "stub_workflow_blocked": True,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
    })

    # Workflow validation report
    _write_json(wa_dir / "workflow_validation_report.json", {
        "shot_contract_binding_verified": ready,
        "ksampler_required": True,
        "saveimage_required": True,
        "filename_prefix_policy_defined": True,
        "resolution_policy_enforced": True,
        "legacy_512_workflow_blocked": True,
        "stub_workflow_blocked": True,
        "validation_passed": ready,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
        "production_accepted": False,
        "errors": [] if ready else ["Workflow validation failed"],
        "warnings": [],
    })

    # Submitted workflow contract
    _write_json(wa_dir / "submitted_workflow_contract.json", {
        "total_shot_contracts": 2,
        "forbidden_fake_prompt_id": True,
        "forbidden_fake_asset": True,
        "comfyui_submit_executed": False,
        "workflow_execution_performed": False,
    })

    # Asset requirements
    _write_json(wa_dir / "asset_requirements.json", {
        "total_requirements": 3,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
    })

    # Asset inventory
    _write_json(wa_dir / "asset_inventory.json", {
        "total_discovered": 0,
        "install_performed": False,
        "download_performed": False,
        "no_unapproved_downloads": True,
        "no_unapproved_installs": True,
    })

    # Asset resolution plan
    _write_json(wa_dir / "asset_resolution_plan.json", {
        "total_assets_evaluated": 3,
        "assets_ready": 3 if ready else 0,
        "assets_missing": 0 if ready else 1,
        "assets_unknown": 0,
        "missing_assets": [] if ready else ["checkpoint_sdxl_base"],
        "controlled_acquisition_plan_created": not ready,
        "manual_gate_required": not ready,
        "unapproved_download_performed": False,
        "unapproved_install_performed": False,
    })

    # Asset verification report
    _write_json(wa_dir / "asset_verification_report.json", {
        "required_assets_available": ready,
        "required_assets_blocked": not ready,
        "checksum_size_path_validation_policy_defined": True,
        "invalid_candidate_substitutions_rejected": True,
        "missing_assets_not_hidden": True,
        "generation_readiness": ready,
        "errors": [] if ready else ["Required assets missing"],
        "warnings": [],
    })

    # Control directory
    _write_json(control_dir / "artifact_index.json", {
        "artifacts": ["workflow_assets/workflow_inventory.json"],
        "current_state": "generation_preflight_operator_review_required",
        "next_allowed_action": "generation_preflight_operator_review_required",
    })
    _write_json(control_dir / "episode_ledger.json", {"events": []})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerationPreflightOperatorReview:
    """Test generation preflight operator review packet."""

    def test_packet_created_with_all_fields(self):
        """Verify packet is created with all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=True)

            packet = build_generation_preflight_operator_review(str(project_root))
            assert packet.get("packet_type") == "generation_preflight_operator_review"
            assert packet.get("current_state") == "generation_preflight_operator_review_required"
            assert packet.get("next_allowed_action") == "generation_preflight_operator_review_required"
            assert packet.get("production_accepted") is False
            assert packet.get("generation_performed") is False
            assert packet.get("comfyui_submit_executed") is False

    def test_ready_when_all_assets_available(self):
        """Verify preflight is ready when all assets and workflows are ready."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=True)

            packet = build_generation_preflight_operator_review(str(project_root))
            assert packet.get("generation_preflight_ready") is True
            assert packet.get("workflow_readiness", {}).get("status") == "ready"
            assert packet.get("asset_readiness", {}).get("status") == "ready"
            assert len(packet.get("blockers", [])) == 0

    def test_not_ready_when_assets_missing(self):
        """Verify preflight is not ready when assets are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=False)

            packet = build_generation_preflight_operator_review(str(project_root))
            assert packet.get("generation_preflight_ready") is False

    def test_no_runtime_execution_performed(self):
        """Verify packet asserts no runtime execution was performed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=True)

            packet = build_generation_preflight_operator_review(str(project_root))
            assert packet.get("comfyui_submit_executed") is False
            assert packet.get("generation_performed") is False
            assert packet.get("workflow_execution_performed") is False

    def test_next_layer_recommended(self):
        """Verify the next recommended layer is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=True)

            packet = build_generation_preflight_operator_review(str(project_root))
            assert "Generation-to-QA" in packet.get("next_recommended_layer", "")

    def test_shot_workflow_bindings_included(self):
        """Verify shot-workflow bindings are included in the packet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_all_workflow_assets(project_root, ready=True)

            packet = build_generation_preflight_operator_review(str(project_root))
            bindings = packet.get("shot_workflow_bindings", [])
            assert len(bindings) >= 1
            assert bindings[0].get("shot_id") == "shot_001"
            assert bindings[0].get("workflow_family") == "sdxl_txt2img"
