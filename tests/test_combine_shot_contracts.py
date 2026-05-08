"""Tests for Shot Contracts — schema, content, workflow routing."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.planning.director import (
    build_director_planning,
    _generate_shot_definitions,
    _write_shot_contracts,
    SCENARIO_STRUCTURE,
    DEFAULT_SCENES,
)


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
        "normalized_task_summary": "Test educational video about AI pipeline QA",
        "content_type": "educational",
        "target_audience": "beginners",
        "goal": "Explain AI pipeline frame checking",
        "expected_output": "educational video",
        "readiness_for_director_planner": True,
        "production_accepted": False,
        "forbidden_actions": ["generation_without_authorization", "comfyui_submit"],
        "assumptions": ["test assumption"],
        "missing_fields": [],
    })
    _write_json(brief_dir / "content_intent.json", {
        "content_type": "educational",
        "goal": "Explain AI pipeline frame checking",
        "target_audience": "beginners",
        "expected_output": "educational video",
        "primary_purpose": "educational explainer",
    })
    _write_json(brief_dir / "project_constraints.json", {
        "style_tone": "clear_practical",
        "constraints": [],
        "format_hint": None,
        "aspect_ratio": None,
    })
    _write_json(brief_dir / "success_criteria.json", {"criteria": ["test"]})
    _write_json(brief_dir / "forbidden_actions.json", {"forbidden_actions": ["generation_without_authorization"]})
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

class TestShotDefinitions:
    """Test _generate_shot_definitions function."""

    def test_generates_shots(self):
        brief = {
            "content_type": "educational",
            "goal": "Test explainer",
        }
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)
        assert len(shots) > 0

    def test_each_shot_has_required_fields(self):
        brief = {"content_type": "educational", "goal": "Test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)

        for shot in shots:
            assert shot.get("shot_id"), f"Shot missing shot_id: {shot}"
            assert shot.get("scene_id"), f"Shot {shot.get('shot_id')} missing scene_id"
            assert shot.get("shot_purpose"), f"Shot {shot.get('shot_id')} missing shot_purpose"
            assert shot.get("visual_intent"), f"Shot {shot.get('shot_id')} missing visual_intent"
            assert shot.get("qa_criteria_summary"), f"Shot {shot.get('shot_id')} missing qa_criteria_summary"
            assert shot.get("workflow_layer_handoff_status") is not None

    def test_shot_scene_id_maps_to_valid_scene(self):
        brief = {"content_type": "educational", "goal": "Test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)

        scene_ids = {s["scene_id"] for s in DEFAULT_SCENES}
        for shot in shots:
            assert shot["scene_id"] in scene_ids, \
                f"Shot {shot['shot_id']} references unknown scene {shot['scene_id']}"

    def test_all_shots_route_to_workflow_layer(self):
        brief = {"content_type": "educational", "goal": "Test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)

        for shot in shots:
            assert shot.get("workflow_layer_handoff_status") == "pending", \
                f"Shot {shot['shot_id']} not routing to workflow layer"

    def test_every_shot_has_generation_readiness_flag(self):
        brief = {"content_type": "educational", "goal": "Test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)

        for shot in shots:
            assert "generation_readiness" in shot
            assert shot["generation_readiness"] is False  # Not ready until authorized

    def test_shot_count_matches_scenes(self):
        """Each scene should have at least one shot."""
        brief = {"content_type": "educational", "goal": "Test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical"}
        shots = _generate_shot_definitions(brief, constraints)

        scene_ids = {s["scene_id"] for s in DEFAULT_SCENES}
        for sid in scene_ids:
            scene_shots = [s for s in shots if s["scene_id"] == sid]
            assert len(scene_shots) >= 1, f"Scene {sid} has no shots"


class TestShotContracts:
    """Test per-shot contract creation."""

    def test_contracts_created_during_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            result = build_director_planning(str(project_root))
            assert result.get("shot_contracts_created") is True

            # Verify actual files
            contracts_dir = project_root / "output" / "control" / "planning" / "shot_contracts"
            assert contracts_dir.exists()
            contracts = list(contracts_dir.glob("shot_*.json"))
            assert len(contracts) > 0

    def test_contract_has_required_fields(self):
        brief = {"content_type": "educational", "goal": "Test", "normalized_task_summary": "test", "forbidden_actions": []}
        constraints = {"style_tone": "clear_practical", "aspect_ratio": None}

        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "shot_contracts"
            contracts_dir.mkdir(parents=True)
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).isoformat()

            filenames = _write_shot_contracts(contracts_dir, [], brief, constraints, timestamp)
            assert len(filenames) > 0

            # Read first contract
            contract_path = contracts_dir / filenames[0]
            with open(contract_path) as f:
                contract = json.load(f)

            assert "shot_id" in contract
            assert "scene_id" in contract
            assert "source_brief_reference" in contract
            assert "narrative_purpose" in contract
            assert "visual_intent" in contract
            assert "composition_requirements" in contract
            assert "camera_framing_requirements" in contract
            assert "subject_object_requirements" in contract
            assert "required_assets" in contract
            assert "generation_requirements" in contract
            assert "workflow_requirements" in contract
            assert "resolution_aspect_expectations" in contract
            assert "negative_constraints" in contract
            assert "qa_criteria" in contract
            assert "forbidden_actions" in contract
            assert "handoff_target" in contract
            assert "production_accepted" in contract

    def test_contract_routes_to_workflow_layer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))
            contracts_dir = project_root / "output" / "control" / "planning" / "shot_contracts"

            for contract_file in contracts_dir.glob("shot_*.json"):
                with open(contract_file) as f:
                    contract = json.load(f)
                assert contract.get("handoff_target") == "Workflow-to-Assets layer", \
                    f"Contract {contract.get('shot_id')} does not route to workflow layer"
                assert contract.get("workflow_requirements", {}).get("handoff_target") == "Workflow-to-Assets layer"

    def test_contract_production_accepted_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))
            contracts_dir = project_root / "output" / "control" / "planning" / "shot_contracts"

            for contract_file in contracts_dir.glob("shot_*.json"):
                with open(contract_file) as f:
                    contract = json.load(f)
                assert contract.get("production_accepted") is False, \
                    f"Contract {contract.get('shot_id')} has production_accepted=true"


class TestSceneShotConsistency:
    """Test that scene and shot plans are consistent."""

    def test_every_scene_has_shots_in_built_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))

            # Verify via shot_plan.json
            shot_plan_path = project_root / "output" / "control" / "planning" / "shot_plan.json"
            with open(shot_plan_path) as f:
                shot_plan = json.load(f)

            scene_ids = {s["scene_id"] for s in DEFAULT_SCENES}
            shots = shot_plan.get("shots", [])
            for sid in scene_ids:
                scene_shots = [s for s in shots if s.get("scene_id") == sid]
                assert len(scene_shots) >= 1, f"Scene {sid} has no shots in shot_plan"

    def test_shot_contracts_match_shot_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief(project_root)

            build_director_planning(str(project_root))

            # Load shot plan
            shot_plan_path = project_root / "output" / "control" / "planning" / "shot_plan.json"
            with open(shot_plan_path) as f:
                shot_plan = json.load(f)
            shot_ids_in_plan = {s["shot_id"] for s in shot_plan.get("shots", [])}

            # Load contracts
            contracts_dir = project_root / "output" / "control" / "planning" / "shot_contracts"
            contract_shot_ids = set()
            for contract_file in contracts_dir.glob("shot_*.json"):
                with open(contract_file) as f:
                    contract = json.load(f)
                contract_shot_ids.add(contract.get("shot_id", ""))

            # All shot plan IDs should have corresponding contracts
            for sid in shot_ids_in_plan:
                assert sid in contract_shot_ids, \
                    f"Shot {sid} has no corresponding contract"


import tempfile
