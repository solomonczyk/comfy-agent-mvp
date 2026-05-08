"""Tests for Workflow Assets Package — success branch, blocked branch, state transitions.

RC-COMBINE-V2-70001-86000
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine
from app.workflow_assets import build_workflow_assets_package, validate_workflow_assets_package


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _create_minimal_planning_artifacts(project_root: Path) -> None:
    """Create minimal valid planning artifacts for testing."""
    planning_dir = project_root / "output" / "control" / "planning"
    shot_contracts_dir = planning_dir / "shot_contracts"
    control_dir = project_root / "output" / "control"

    # Create planning artifacts
    _write_json(planning_dir / "scenario_plan.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "narrative_goal": "Test educational video",
        "content_type": "educational",
        "target_audience": "beginners",
        "downstream_readiness_flags": {
            "ready_for_workflow_to_assets": False,
            "operator_review_required": True,
            "production_accepted": False,
        },
    })
    _write_json(planning_dir / "scene_plan.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "scenes": [
            {"scene_id": "scene_001", "scene_purpose": "hook_and_context", "scene_summary": "Test"},
        ],
    })
    _write_json(planning_dir / "shot_plan.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "shots": [
            {
                "shot_id": "shot_001",
                "scene_id": "scene_001",
                "shot_purpose": "Test shot",
                "shot_description": "Test description",
                "camera_framing_intent": "Wide",
                "subject_object_requirements": "Test",
                "visual_style_constraints": "Test style",
                "duration_target_seconds": 8,
                "generation_readiness": False,
                "asset_requirements_summary": "motion_graphics_assets: test template",
                "qa_criteria_summary": "test criteria",
                "workflow_layer_handoff_status": "pending",
            },
        ],
    })
    _write_json(planning_dir / "production_plan.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "ready_for_workflow_to_assets": True,
        "ordered_production_stages": [],
        "dependency_map": {},
    })
    _write_json(planning_dir / "planning_validation_report.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "validation_passed": True,
        "scenario_plan_created": True,
        "scene_plan_created": True,
        "shot_plan_created": True,
        "shot_contracts_created": True,
        "errors": [],
        "warnings": [],
    })
    _write_json(planning_dir / "planning_operator_review_packet.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "production_accepted": False,
        "current_state": "planning_operator_review_required",
    })

    # Create shot contracts
    _write_json(shot_contracts_dir / "shot_001.json", {
        "task_id": "RC-COMBINE-V2-62001-70000",
        "shot_id": "shot_001",
        "scene_id": "scene_001",
        "visual_intent": "Test visual intent",
        "required_assets": "motion_graphics_assets: test template",
        "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "txt2img", "generation_ready": False},
        "workflow_requirements": {"handoff_target": "Workflow-to-Assets layer", "handoff_status": "pending", "required_downstream": ["frame_generation", "qa_validation"]},
        "qa_criteria": "test criteria",
        "composition_requirements": "Test composition",
        "camera_framing_requirements": "Wide",
        "subject_object_requirements": "Test",
        "negative_constraints": [],
        "forbidden_actions": [],
        "handoff_target": "Workflow-to-Assets layer",
        "production_accepted": False,
    })

    # Create a mock SDXL checkpoint so asset resolution succeeds
    (project_root / "models" / "checkpoints" / "sdxl").mkdir(parents=True, exist_ok=True)
    (project_root / "models" / "checkpoints" / "sdxl" / "sdxl_base.safetensors").write_text("fake checkpoint content for testing")

    # Create control directory with index and ledger
    _write_json(control_dir / "artifact_index.json", {
        "artifacts": [],
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
    })
    _write_json(control_dir / "episode_ledger.json", {"events": []})


def _create_blocked_planning_artifacts(project_root: Path) -> None:
    """Create planning artifacts that will trigger blocked path."""
    _create_minimal_planning_artifacts(project_root)
    planning_dir = project_root / "output" / "control" / "planning"
    # Set validation to failed
    _write_json(planning_dir / "planning_validation_report.json", {
        "validation_passed": False,
        "scenario_plan_created": False,
        "errors": ["Invalid planning artifacts"],
        "warnings": [],
    })


def _create_missing_contract_planning_artifacts(project_root: Path) -> None:
    """Create planning artifacts with missing shot contracts."""
    planning_dir = project_root / "output" / "control" / "planning"
    control_dir = project_root / "output" / "control"

    _write_json(planning_dir / "scenario_plan.json", {"narrative_goal": "Test", "downstream_readiness_flags": {"production_accepted": False}})
    _write_json(planning_dir / "scene_plan.json", {"scenes": []})
    _write_json(planning_dir / "shot_plan.json", {"shots": []})
    _write_json(planning_dir / "production_plan.json", {"ready_for_workflow_to_assets": True})
    _write_json(planning_dir / "planning_validation_report.json", {"validation_passed": True, "errors": [], "warnings": []})
    _write_json(planning_dir / "planning_operator_review_packet.json", {"production_accepted": False})
    # No shot_contracts directory
    _write_json(control_dir / "artifact_index.json", {"artifacts": [], "current_state": "planning_operator_review_required", "next_allowed_action": "planning_operator_review_required"})
    _write_json(control_dir / "episode_ledger.json", {"events": []})


# ---------------------------------------------------------------------------
# State machine tests
# ---------------------------------------------------------------------------

class TestWorkflowAssetsStateMachine:
    """Test state machine support for generation_preflight_operator_review_required."""

    def test_preflight_state_is_valid(self):
        assert CombineStateMachine.is_valid_state("generation_preflight_operator_review_required") is True

    def test_preflight_state_is_not_terminal(self):
        assert CombineStateMachine.is_terminal_state("generation_preflight_operator_review_required") is False

    def test_transition_from_planning_to_preflight_allowed(self):
        assert CombineStateMachine.can_transition(
            "planning_operator_review_required",
            "generation_preflight_operator_review_required",
        ) is True

    def test_preflight_self_loop_allowed(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "generation_preflight_operator_review_required",
        ) is True

    def test_preflight_can_go_back_to_planning(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "planning_operator_review_required",
        ) is True

    def test_preflight_cannot_skip_to_generation(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "generate_assets",
        ) is False

    def test_preflight_cannot_skip_to_real_generation(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "real_generate_assets",
        ) is False

    def test_preflight_cannot_skip_to_assembly(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "assembly_required",
        ) is False

    def test_preflight_cannot_skip_to_visual_qa(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "visual_qa_required",
        ) is False

    def test_preflight_cannot_skip_to_completed(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "completed",
        ) is False

    def test_preflight_cannot_skip_to_production_accepted(self):
        assert CombineStateMachine.is_valid_state("production_accepted") is False

    def test_preflight_cannot_skip_to_final_qc(self):
        assert CombineStateMachine.can_transition(
            "generation_preflight_operator_review_required",
            "final_qc_required",
        ) is False


# ---------------------------------------------------------------------------
# Success branch tests
# ---------------------------------------------------------------------------

class TestWorkflowAssetsSuccessBranch:
    """Test that the workflow assets package builds successfully on valid input."""

    def test_build_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("feature_completed") is True
            assert result.get("planning_artifacts_validated") is True
            assert result.get("workflow_inventory_created") is True
            assert result.get("workflow_selection_report_created") is True
            assert result.get("workflow_patch_plan_created") is True
            assert result.get("workflow_validation_report_created") is True
            assert result.get("submitted_workflow_contract_created") is True
            assert result.get("asset_requirements_created") is True
            assert result.get("asset_inventory_created") is True
            assert result.get("asset_resolution_plan_created") is True
            assert result.get("asset_verification_report_created") is True
            assert result.get("generation_preflight_operator_review_packet_created") is True
            assert result.get("shot_contract_binding_verified") is True
            assert result.get("legacy_512_workflow_blocked") is True
            assert result.get("stub_workflow_blocked") is True
            assert result.get("no_unapproved_downloads") is True
            assert result.get("no_unapproved_installs") is True

    def test_state_after_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("current_state") == "generation_preflight_operator_review_required"
            assert result.get("next_allowed_action") == "generation_preflight_operator_review_required"

            # Verify artifact_index state
            index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(index_path) as f:
                index = json.load(f)
            assert index.get("current_state") == "generation_preflight_operator_review_required"
            assert index.get("next_allowed_action") == "generation_preflight_operator_review_required"

    def test_production_accepted_remains_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("production_accepted") is False

    def test_forbidden_actions_remain_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("generation_performed") is False
            assert result.get("comfyui_submit_executed") is False
            assert result.get("workflow_execution_performed") is False
            assert result.get("assembly_executed") is False
            assert result.get("downstream_executed") is False
            assert result.get("visual_qa_executed") is False
            assert result.get("retry_attempted") is False

    def test_artifacts_created_on_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            build_workflow_assets_package(str(project_root))

            wa_dir = project_root / "output" / "control" / "workflow_assets"
            assert wa_dir.exists()
            assert (wa_dir / "workflow_inventory.json").exists()
            assert (wa_dir / "workflow_selection_report.json").exists()
            assert (wa_dir / "workflow_patch_plan.json").exists()
            assert (wa_dir / "workflow_validation_report.json").exists()
            assert (wa_dir / "submitted_workflow_contract.json").exists()
            assert (wa_dir / "asset_requirements.json").exists()
            assert (wa_dir / "asset_inventory.json").exists()
            assert (wa_dir / "asset_resolution_plan.json").exists()
            assert (wa_dir / "asset_verification_report.json").exists()
            assert (wa_dir / "generation_preflight_operator_review_packet.json").exists()

    def test_artifact_index_updated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            build_workflow_assets_package(str(project_root))

            index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(index_path) as f:
                index = json.load(f)
            assert index.get("workflow_assets_layer_completed") is True
            assert any("workflow_assets/workflow_inventory.json" in a for a in index.get("artifacts", []))

    def test_episode_ledger_updated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            build_workflow_assets_package(str(project_root))

            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path) as f:
                ledger = json.load(f)
            events = ledger if isinstance(ledger, list) else ledger.get("events", [])
            wa_events = [e for e in events if e.get("event") == "workflow_assets_layer_completed"]
            assert len(wa_events) >= 1
            assert wa_events[0].get("status") == "workflow_assets_completed"


# ---------------------------------------------------------------------------
# Blocked branch tests
# ---------------------------------------------------------------------------

class TestWorkflowAssetsBlockedBranch:
    """Test that the workflow assets package handles blocked paths correctly."""

    def test_planning_validation_failure_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_blocked_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("blocked") is True
            assert result.get("feature_completed") is False or result.get("feature_completed") is None

    def test_missing_shot_contracts_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_missing_contract_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("blocked") is True or result.get("blocked_path_reached") is True

    def test_blocker_report_created_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_blocked_planning_artifacts(project_root)

            build_workflow_assets_package(str(project_root))

            wa_dir = project_root / "output" / "control" / "workflow_assets"
            blocker = _load_json(wa_dir / "workflow_blocker_report.json")
            assert blocker is not None
            assert "blocker_type" in blocker

    def test_forbidden_runtime_not_executed_on_blocked_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_blocked_planning_artifacts(project_root)

            result = build_workflow_assets_package(str(project_root))
            assert result.get("generation_performed") is False
            assert result.get("comfyui_submit_executed") is False
            assert result.get("production_accepted") is False


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestWorkflowAssetsValidation:
    """Test validation of the workflow assets package."""

    def test_validation_passes_after_successful_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)
            build_workflow_assets_package(str(project_root))

            result = validate_workflow_assets_package(str(project_root))
            assert result.get("validation_passed") is True
            assert result.get("workflow_inventory_created") is True
            assert result.get("workflow_selection_report_created") is True
            assert result.get("shot_contract_binding_verified") is True

    def test_validation_fails_without_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _create_minimal_planning_artifacts(project_root)

            result = validate_workflow_assets_package(str(project_root))
            assert result.get("validation_passed") is False
            assert len(result.get("errors", [])) > 0


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
