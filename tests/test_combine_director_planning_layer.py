"""Tests for Director Planning Layer — success branch, blocked branch, CLI integration."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_minimal_brief_artifacts(project_root: Path) -> None:
    """Create minimal brief artifacts needed for planning preflight."""
    brief_dir = project_root / "output" / "control" / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)

    _write_json(brief_dir / "brief_contract.json", {
        "project_id": "test_project",
        "normalized_task_summary": "Create an educational video about AI pipeline QA for beginners",
        "content_type": "educational",
        "target_audience": "beginners",
        "goal": "Explain AI pipeline frame checking for beginners",
        "expected_output": "video about AI pipeline frame checking",
        "language": "en",
        "style_tone": "clear_practical",
        "topic_domain": "artificial_intelligence",
        "constraints": [],
        "forbidden_actions": [
            "generation_without_operator_authorization",
            "comfyui_submit",
            "production_acceptance",
        ],
        "success_criteria": [
            "All assets valid",
            "Content matches intent",
        ],
        "missing_fields": [],
        "assumptions": ["No generation performed"],
        "readiness_for_director_planner": True,
        "operator_review_required": True,
        "production_accepted": False,
    })

    _write_json(brief_dir / "content_intent.json", {
        "content_type": "educational",
        "goal": "Explain AI pipeline frame checking for beginners",
        "target_audience": "beginners",
        "expected_output": "video about AI pipeline frame checking",
        "primary_purpose": "educational explainer",
        "secondary_purposes": [],
        "key_message": "Automated QA ensures quality",
        "call_to_action": None,
    })

    _write_json(brief_dir / "project_constraints.json", {
        "duration_target": None,
        "format_hint": None,
        "aspect_ratio": None,
        "language": "en",
        "style_tone": "clear_practical",
        "topic_domain": "artificial_intelligence",
        "constraints": [],
        "technical_restrictions": [],
    })

    _write_json(brief_dir / "success_criteria.json", {
        "criteria": ["All assets valid", "Content matches intent"],
        "quality_bars": ["Assets valid", "Content matches intent"],
        "acceptance_requirements": ["Operator review required"],
        "generated_defaults": True,
    })

    _write_json(brief_dir / "forbidden_actions.json", {
        "forbidden_actions": ["generation_without_operator_authorization", "comfyui_submit", "production_acceptance"],
        "generation_blocked": True,
        "comfyui_submit_blocked": True,
        "assembly_blocked": True,
        "downstream_blocked": True,
        "production_acceptance_blocked": True,
        "visual_qa_skip_blocked": True,
    })

    _write_json(brief_dir / "brief_validation_report.json", {
        "brief_contract_created": True,
        "brief_validation_passed": True,
        "classification": "valid_for_director_planning",
        "brief_is_ready_for_director_planner": True,
        "operator_review_required": True,
        "production_accepted": False,
        "generation_performed": False,
        "downstream_executed": False,
    })


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _init_project_state(project_root: Path) -> None:
    """Create minimal project state (artifact_index + episode_ledger)."""
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

class TestBuildDirectorPlanningCLI:
    """Test combine-build-director-planning command."""

    def test_help_registered(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-build-director-planning", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-build-director-planning" in result.stdout

    def test_validate_help_registered(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-validate-director-planning", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-validate-director-planning" in result.stdout

    def test_operator_review_help_registered(self):
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-build-planning-operator-review", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "combine-build-planning-operator-review" in result.stdout

    def test_success_branch_builds_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief_artifacts(project_root)

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-director-planning",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)

            assert output.get("scenario_plan_created") is True
            assert output.get("scene_plan_created") is True
            assert output.get("shot_plan_created") is True
            assert output.get("shot_contracts_created") is True
            assert output.get("production_plan_created") is True
            assert output.get("planning_validation_report_created") is True
            assert output.get("planning_operator_review_packet_created") is True

            assert output.get("current_state") == "planning_operator_review_required"
            assert output.get("next_allowed_action") == "planning_operator_review_required"
            assert output.get("generation_performed") is False
            assert output.get("comfyui_submit_executed") is False
            assert output.get("assembly_executed") is False
            assert output.get("downstream_executed") is False
            assert output.get("production_accepted") is False

            # Verify artifact files exist
            planning_dir = project_root / "output" / "control" / "planning"
            assert (planning_dir / "scenario_plan.json").exists()
            assert (planning_dir / "scene_plan.json").exists()
            assert (planning_dir / "shot_plan.json").exists()
            assert (planning_dir / "production_plan.json").exists()
            assert (planning_dir / "planning_validation_report.json").exists()
            assert (planning_dir / "planning_operator_review_packet.json").exists()

            # Verify shot contracts exist
            shot_contracts_dir = planning_dir / "shot_contracts"
            assert shot_contracts_dir.exists()
            contract_files = list(shot_contracts_dir.glob("shot_*.json"))
            assert len(contract_files) > 0

            # Verify artifact_index updated
            index = json.loads((project_root / "output" / "control" / "artifact_index.json").read_text())
            assert index.get("current_state") == "planning_operator_review_required"
            assert index.get("planning_layer_completed") is True
            assert any("planning/scenario_plan.json" in a for a in index.get("artifacts", []))

            # Verify episode_ledger updated
            ledger = json.loads((project_root / "output" / "control" / "episode_ledger.json").read_text())
            events = ledger if isinstance(ledger, list) else ledger.get("events", [])
            planning_events = [e for e in events if e.get("event") == "director_planning_layer_completed"]
            assert len(planning_events) == 1

    def test_blocked_when_brief_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-director-planning",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 1  # blocked
            output = json.loads(result.stdout)
            assert output.get("blocked") is True or output.get("blocked_path_reached") is True

    def test_blocked_when_brief_not_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)

            # Create brief artifacts with readiness_for_director_planner=false
            brief_dir = project_root / "output" / "control" / "brief"
            brief_dir.mkdir(parents=True, exist_ok=True)
            _write_json(brief_dir / "brief_contract.json", {
                "project_id": "test",
                "normalized_task_summary": "test",
                "content_type": "educational",
                "target_audience": "beginners",
                "goal": "test goal",
                "expected_output": "test output",
                "readiness_for_director_planner": False,
                "production_accepted": False,
            })
            _write_json(brief_dir / "content_intent.json", {"content_type": "educational", "goal": "test"})
            _write_json(brief_dir / "project_constraints.json", {"constraints": []})
            _write_json(brief_dir / "success_criteria.json", {"criteria": []})
            _write_json(brief_dir / "forbidden_actions.json", {"forbidden_actions": []})
            _write_json(brief_dir / "brief_validation_report.json", {"classification": "valid"})

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-director-planning",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 1  # blocked
            output = json.loads(result.stdout)
            assert output.get("blocked") is True or output.get("blocked_path_reached") is True

    def test_forbidden_actions_remain_false(self):
        """Verify that no generation-related actions are accidentally set to true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief_artifacts(project_root)

            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-build-director-planning",
                    "--project-root", str(project_root),
                    "--json",
                ],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)

            assert output.get("generation_performed") is False
            assert output.get("comfyui_submit_executed") is False
            assert output.get("retry_attempted") is False
            assert output.get("visual_qa_executed") is False
            assert output.get("visual_acceptance_executed") is False
            assert output.get("preview_render_executed") is False
            assert output.get("voice_generation_executed") is False
            assert output.get("assembly_executed") is False
            assert output.get("downstream_executed") is False
            assert output.get("production_accepted") is False
            assert output.get("new_generation_performed") is False


class TestValidateDirectorPlanning:
    """Test combine-validate-director-planning command."""

    def test_validate_after_build_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief_artifacts(project_root)

            # Build first
            subprocess.run(
                [sys.executable, "-m", "app.cli", "combine-build-director-planning",
                 "--project-root", str(project_root), "--json"],
                capture_output=True, text=True,
            )

            # Then validate
            result = subprocess.run(
                [sys.executable, "-m", "app.cli", "combine-validate-director-planning",
                 "--project-root", str(project_root), "--json"],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)
            assert output.get("scenario_plan_created") is True
            assert output.get("scene_plan_created") is True
            assert output.get("shot_plan_created") is True
            assert output.get("shot_contracts_created") is True
            assert output.get("validation_passed") is True
            assert output.get("generation_performed") is False
            assert output.get("production_accepted") is False


class TestBuildPlanningOperatorReview:
    """Test combine-build-planning-operator-review command."""

    def test_operator_review_after_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            _init_project_state(project_root)
            _create_minimal_brief_artifacts(project_root)

            # Build first
            subprocess.run(
                [sys.executable, "-m", "app.cli", "combine-build-director-planning",
                 "--project-root", str(project_root), "--json"],
                capture_output=True, text=True,
            )

            # Build operator review
            result = subprocess.run(
                [sys.executable, "-m", "app.cli", "combine-build-planning-operator-review",
                 "--project-root", str(project_root), "--json"],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"STDERR: {result.stderr}"
            output = json.loads(result.stdout)
            packet = output.get("packet", output)
            assert packet.get("packet_type") == "planning_operator_review"
            assert packet.get("shot_count", 0) > 0
            assert packet.get("scene_count", 0) > 0
            assert packet.get("current_state") == "planning_operator_review_required"
            assert packet.get("production_accepted") is False
            assert packet.get("generation_performed") is False


import tempfile
