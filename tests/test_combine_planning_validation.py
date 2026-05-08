"""Tests for Planning Validation — schemas, completeness, blocked branch."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

from app.planning.director import (
    build_director_planning,
    validate_director_planning,
    PlanningValidationReport,
    ScenarioPlan,
    ProductionPlan,
)

TASK_ID = "RC-COMBINE-V2-62001-70000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _create_minimal_brief(project_root: Path) -> None:
    brief_dir = project_root / "output" / "control" / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)
    _write_json(brief_dir / "brief_contract.json", {
        "project_id": "test_project",
        "normalized_task_summary": "Test educational video",
        "content_type": "educational",
        "target_audience": "beginners",
        "goal": "Test planning validation",
        "expected_output": "test video",
        "readiness_for_director_planner": True,
        "production_accepted": False,
        "forbidden_actions": ["generation_without_authorization"],
        "assumptions": ["test assumption"],
        "missing_fields": [],
    })
    _write_json(brief_dir / "content_intent.json", {
        "content_type": "educational",
        "goal": "Test planning validation",
        "target_audience": "beginners",
        "expected_output": "test video",
        "primary_purpose": "test",
    })
    _write_json(brief_dir / "project_constraints.json", {
        "style_tone": "clear_practical",
        "constraints": [],
        "format_hint": None,
        "aspect_ratio": None,
    })
    _write_json(brief_dir / "success_criteria.json", {
        "criteria": ["test criterion"],
        "quality_bars": [],
        "acceptance_requirements": [],
    })
    _write_json(brief_dir / "forbidden_actions.json", {
        "forbidden_actions": ["generation_without_authorization"],
        "generation_blocked": True,
        "comfyui_submit_blocked": True,
    })
    _write_json(brief_dir / "brief_validation_report.json", {
        "brief_contract_created": True,
        "brief_validation_passed": True,
        "classification": "valid_for_director_planning",
        "brief_is_ready_for_director_planner": True,
        "production_accepted": False,
    })


def _init_project_state(project_root: Path) -> None:
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    _write_json(control_dir / "artifact_index.json", {
        "artifacts": [],
        "current_state": "brief_operator_review_required",
        "next_allowed_action": "brief_operator_review_required",
    })
    _write_json(control_dir / "episode_ledger.json", {"events": []})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPlanningValidationReportSchema:
    """Test PlanningValidationReport dataclass schema."""

    def test_default_values(self):
        report = PlanningValidationReport()
        d = report.to_dict()
        assert d["scenario_plan_created"] is False
        assert d["scene_plan_created"] is False
        assert d["shot_plan_created"] is False
        assert d["shot_contracts_created"] is False
        assert d["every_scene_has_at_least_one_shot"] is False
        assert d["every_shot_has_scene_id"] is False
        assert d["every_shot_has_visual_intent"] is False
        assert d["every_shot_has_qa_criteria"] is False
        assert d["every_shot_has_required_assets_or_explicit_none"] is False
        assert d["every_shot_routes_to_workflow_layer"] is False
        assert d["generation_performed"] is False
        assert d["comfyui_submit_performed"] is False
        assert d["assembly_performed"] is False
        assert d["downstream_performed"] is False
        assert d["production_accepted"] is False
        assert d["blocked_path_reached"] is False

    def test_success_values(self):
        report = PlanningValidationReport(
            scenario_plan_created=True,
            scene_plan_created=True,
            shot_plan_created=True,
            shot_contracts_created=True,
            every_scene_has_at_least_one_shot=True,
            every_shot_has_scene_id=True,
            every_shot_has_visual_intent=True,
            every_shot_has_qa_criteria=True,
            every_shot_has_required_assets_or_explicit_none=True,
            every_shot_routes_to_workflow_layer=True,
            generation_performed=False,
            comfyui_submit_performed=False,
            assembly_performed=False,
            downstream_performed=False,
            production_accepted=False,
        )
        d = report.to_dict()
        assert d["scenario_plan_created"] is True
        assert d["every_scene_has_at_least_one_shot"] is True
        assert d["every_shot_routes_to_workflow_layer"] is True
        assert d["generation_performed"] is False

    def test_errors_and_warnings(self):
        report = PlanningValidationReport(
            errors=["Scene scene_001 has no shots", "Shot shot_001 missing scene_id"],
            warnings=["Asset requirements not specified for shot_003"],
        )
        d = report.to_dict()
        assert len(d["errors"]) == 2
        assert len(d["warnings"]) == 1
        assert "Scene scene_001" in d["errors"][0]


class TestScenarioPlanSchema:
    """Test ScenarioPlan dataclass."""

    def test_default_fields(self):
        plan = ScenarioPlan()
        d = plan.to_dict()
        assert d["task_id"] == TASK_ID
        assert d["source_brief_reference"] == ""
        assert d["narrative_goal"] == ""
        assert d["target_audience"] == ""
        assert d["content_type"] == "unknown"
        assert d["forbidden_content_inherited"] == []
        assert isinstance(d["downstream_readiness_flags"], dict)

    def test_populated_fields(self):
        plan = ScenarioPlan(
            source_brief_reference="test brief",
            project_id="test_project",
            episode_id="ep01",
            narrative_goal="Test goal",
            target_audience="beginners",
            content_type="educational",
            scene_sequence=["scene_001", "scene_002"],
            downstream_readiness_flags={"ready_for_workflow": False, "production_accepted": False},
            forbidden_content_inherited=["generation_without_authorization"],
        )
        d = plan.to_dict()
        assert d["source_brief_reference"] == "test brief"
        assert d["narrative_goal"] == "Test goal"
        assert len(d["scene_sequence"]) == 2
        assert d["downstream_readiness_flags"]["ready_for_workflow"] is False
        assert "generation_without_authorization" in d["forbidden_content_inherited"]


class TestProductionPlanSchema:
    """Test ProductionPlan dataclass."""

    def test_default_values(self):
        plan = ProductionPlan()
        d = plan.to_dict()
        assert d["scene_count"] == 0
        assert d["shot_count"] == 0
        assert d["ready_for_workflow_to_assets"] is False
        assert d["ordered_production_stages"] == []
        assert d["dependency_map"] == {}

    def test_handoff_readiness(self):
        plan = ProductionPlan(
            scenario_summary="Test scenario",
            scene_count=5,
            shot_count=12,
            ordered_production_stages=["stage1", "stage2", "stage3"],
            dependency_map={"stage1": "stage2", "stage2": "stage3"},
            required_downstream_layers=["Workflow-to-Assets"],
            operator_gates_required=["planning_operator_review"],
            ready_for_workflow_to_assets=True,
        )
        d = plan.to_dict()
        assert d["scene_count"] == 5
        assert d["shot_count"] == 12
        assert d["ready_for_workflow_to_assets"] is True
        assert len(d["ordered_production_stages"]) == 3
        assert d["dependency_map"]["stage1"] == "stage2"


class TestValidationAfterBuild:
    """Test that validation report is correct after building."""

    def test_validation_passes_on_success_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))
            result = validate_director_planning(str(project_root))

            assert result.get("scenario_plan_created") is True
            assert result.get("scene_plan_created") is True
            assert result.get("shot_plan_created") is True
            assert result.get("shot_contracts_created") is True
            assert result.get("validation_passed") is True
            assert result.get("blocked_path_reached") is False

    def test_validation_fails_without_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = validate_director_planning(str(project_root))

            assert result.get("scenario_plan_created") is False
            assert result.get("validation_passed") is False
            assert result.get("blocked_path_reached") is True

    def test_forbidden_actions_remain_false_after_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = build_director_planning(str(project_root))
            assert result.get("generation_performed") is False
            assert result.get("comfyui_submit_executed") is False
            assert result.get("assembly_executed") is False
            assert result.get("downstream_executed") is False
            assert result.get("production_accepted") is False


import tempfile
