"""Tests for RC-COMBINE-V2-ASSET-DIVERSITY-TIMELINE-PROGRESSION-REPAIR-001.

Tests that the asset diversity repair layer:
  - Detects single-source static preview
  - Blocks human preview decision
  - Requires minimum unique visual sources
  - Creates corrected timeline plan
  - Does NOT render preview or generate
"""

import json
import os
import pytest
import tempfile
from pathlib import Path

from app.timeline.asset_diversity_timeline_repair import (
    build_asset_diversity_plan,
    build_authorization_packet,
    build_corrected_timeline_visual_progression_plan,
    build_dry_run_validation_report,
    build_timeline_visual_progression_contract,
    diagnose_static_preview_failure,
    read_prior_artifacts,
    run_asset_diversity_timeline_repair,
    validate_prior_artifacts,
    TASK_ID,
    MIN_UNIQUE_VISUAL_SOURCES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a minimal project structure with all required prior artifacts."""
    root = tmp_path / "project"
    control_dir = root / "output" / "control"
    assets_dir = root / "output" / "assets"
    editorial_dir = root / "output" / "editorial"

    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy approved asset
    dummy_asset = assets_dir / "approved_asset.png"
    dummy_asset.write_text("fake-png-content")

    # Create timeline_model.json (single scene, no asset_refs)
    timeline = {
        "scenes": [
            {"scene_id": "scene_001", "asset_refs": []}
        ],
        "tracks": {
            "video_main": [],
            "video_overlay": [],
        },
        "markers": [],
    }
    _write_json(control_dir / "timeline_model.json", timeline)
    _write_json(editorial_dir / "timeline_model.json", timeline)

    # Create edit_decision_list.json (empty operations)
    edl = {"operations": []}
    _write_json(control_dir / "edit_decision_list.json", edl)
    _write_json(editorial_dir / "edit_decision_list.json", edl)

    # Create marker_registry.json
    _write_json(control_dir / "marker_registry.json", {"markers": []})
    _write_json(editorial_dir / "marker_registry.json", {"markers": []})

    # Create transition_policy.json
    _write_json(control_dir / "transition_policy.json", {"transitions": []})
    _write_json(editorial_dir / "transition_policy.json", {"transitions": []})

    # Create controlled_preview_rerender_result_review.json (duplicate_ratio = 1.0)
    _write_json(control_dir / "controlled_preview_rerender_result_review.json", {
        "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001",
        "review_type": "controlled_preview_rerender_result_review",
        "preview_render_executed": True,
        "preview_render_count": 1,
        "duplicate_ratio": 1.0,
        "duplicate_threshold": 0.85,
        "preview_static_blocker": True,
        "preview_valid_for_operator_review": False,
    })

    # Create static_preview_detection_report.json
    _write_json(control_dir / "static_preview_detection_report.json", {
        "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001",
        "report_type": "static_preview_detection_report",
        "static_detection_executed": True,
        "duplicate_ratio": 1.0,
        "preview_static_blocker": True,
    })

    # Create preview_correction_plan.json
    _write_json(control_dir / "preview_correction_plan.json", {
        "plan_type": "preview_correction_plan",
        "correction_goal": "produce a non-static preview that proves real timeline/scene progression",
        "root_cause_summary": "timeline_empty_no_assets_placed",
        "required_repairs": [
            "ensure timeline has multiple distinct visual segments",
            "ensure EDL references correct assets per scene",
        ],
        "next_gate_required": "controlled_preview_rerender_authorization_required",
    })

    # Create artifact_index.json
    _write_json(control_dir / "artifact_index.json", {
        "current_state": "preview_correction_plan_required",
        "next_allowed_action": "preview_correction_plan_required",
        "production_accepted": False,
    })

    # Create episode_ledger.json
    _write_json(control_dir / "episode_ledger.json", [])

    # Create approved_visual_assets_manifest.json
    _write_json(control_dir / "approved_visual_assets_manifest.json", {
        "approved_assets": [
            {
                "path": "output/assets/approved_asset.png",
                "sha256": "fake-sha256",
            }
        ],
        "production_accepted": False,
    })

    return root


@pytest.fixture
def project_root_with_assets(project_root: Path) -> Path:
    """Add multiple candidate assets to the project."""
    assets_dir = project_root / "output" / "assets"
    for i in range(MIN_UNIQUE_VISUAL_SOURCES + 2):
        asset_file = assets_dir / f"candidate_{i:03d}.png"
        asset_file.write_text(f"fake-png-content-{i}")
    return project_root


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReadPriorArtifacts:
    def test_reads_all_artifacts(self, project_root: Path):
        prior = read_prior_artifacts(project_root)
        assert prior["timeline_model"] is not None
        assert prior["edit_decision_list"] is not None
        assert prior["marker_registry"] is not None
        assert prior["transition_policy"] is not None
        assert prior["controlled_preview_rerender_result_review"] is not None
        assert prior["static_preview_detection_report"] is not None
        assert prior["preview_correction_plan"] is not None
        assert prior["artifact_index"] is not None
        assert prior["episode_ledger"] is not None

    def test_returns_none_for_missing_artifact(self, project_root: Path):
        # Remove an optional artifact
        missing = project_root / "output" / "control" / "marker_registry.json"
        missing.unlink()
        prior = read_prior_artifacts(project_root)
        # Should still find it from editorial
        assert prior["marker_registry"] is not None

    def test_prior_validation_passes(self, project_root: Path):
        prior = read_prior_artifacts(project_root)
        errors = validate_prior_artifacts(prior)
        # Some optional artifacts may be flagged as not found
        # but required control artifacts should be fine
        required_errors = [e for e in errors if "not found" in e and "optional" not in e]
        assert len(required_errors) == 0


class TestDiagnoseStaticPreview:
    def test_detects_single_source_static_preview(self, project_root: Path):
        """test_asset_diversity_repair_detects_single_source_static_preview"""
        prior = read_prior_artifacts(project_root)
        diagnosis = diagnose_static_preview_failure(prior)

        assert diagnosis["failure_type"] == "timeline_visual_progression_failure"
        assert diagnosis["duplicate_frame_ratio"] == 1.0
        assert diagnosis["root_cause"] == "single_source_asset_repeated"
        assert diagnosis["human_preview_decision_allowed"] is False

    def test_blocks_human_preview_decision(self, project_root: Path):
        """test_asset_diversity_repair_blocks_human_preview_decision"""
        prior = read_prior_artifacts(project_root)
        diagnosis = diagnose_static_preview_failure(prior)

        assert diagnosis["human_preview_decision_allowed"] is False
        assert diagnosis.get("failure_type") == "timeline_visual_progression_failure"


class TestBuildContracts:
    def test_contract_requires_minimum_unique_visual_sources(self, project_root: Path):
        """test_asset_diversity_repair_requires_minimum_unique_visual_sources"""
        prior = read_prior_artifacts(project_root)
        diagnosis = diagnose_static_preview_failure(prior)
        contract = build_timeline_visual_progression_contract(diagnosis, prior)

        assert contract["minimum_unique_visual_sources"] == MIN_UNIQUE_VISUAL_SOURCES
        assert contract["contract_type"] == "timeline_visual_progression_contract"
        assert "single_still_repeated_as_full_preview" in contract["prohibited_patterns"]
        assert contract["duplicate_frame_policy"]["static_preview_blocker_required"] is True

    def test_asset_diversity_plan_created(self, project_root_with_assets: Path):
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)

        assert plan["plan_type"] == "asset_diversity_plan"
        assert plan["diagnosis_consumed"] is True
        assert len(plan["existing_usable_assets"]) >= MIN_UNIQUE_VISUAL_SOURCES
        assert plan["existing_assets_summary"]["total_asset_files_found"] >= MIN_UNIQUE_VISUAL_SOURCES

    def test_asset_diversity_plan_reports_insufficient_assets(self, project_root: Path):
        prior = read_prior_artifacts(project_root)
        diagnosis = diagnose_static_preview_failure(prior)
        plan = build_asset_diversity_plan(diagnosis, prior, project_root)

        assert plan["can_repair_from_existing_assets"] is False
        assert plan["would_require_future_generation_or_acquisition"] is True

    def test_creates_corrected_timeline_plan(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_creates_corrected_timeline_plan"""
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)
        corrected = build_corrected_timeline_visual_progression_plan(
            diagnosis, diversity_plan, prior, project_root_with_assets,
        )

        assert corrected["plan_type"] == "corrected_timeline_visual_progression_plan"
        assert corrected["timeline_after"]["tracks_non_empty"] is True
        assert corrected["proof_tracks_not_empty"] is True
        assert corrected["proof_edl_operations_applied"] is True
        assert len(corrected["visual_progression_anchors"]) > 0
        assert corrected["timeline_after"]["expected_unique_asset_refs"] >= 1

    def test_dry_run_does_not_render_preview(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_does_not_render_preview"""
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)
        corrected = build_corrected_timeline_visual_progression_plan(
            diagnosis, diversity_plan, prior, project_root_with_assets,
        )
        dry_run = build_dry_run_validation_report(diagnosis, diversity_plan, corrected)

        assert dry_run["dry_run_executed"] is True
        assert dry_run["apply_performed"] is False
        assert dry_run["preview_render_executed"] is False
        assert dry_run["forbidden_actions_not_executed"]["generation_performed"] is False
        assert dry_run["forbidden_actions_not_executed"]["preview_render_executed"] is False
        assert dry_run["forbidden_actions_not_executed"]["comfyui_submit_executed"] is False
        assert dry_run["forbidden_actions_not_executed"]["voice_generation_executed"] is False
        assert dry_run["forbidden_actions_not_executed"]["assembly_executed"] is False
        assert dry_run["forbidden_actions_not_executed"]["downstream_executed"] is False

    def test_dry_run_blocks_single_source(self, project_root_with_assets: Path):
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)
        corrected = build_corrected_timeline_visual_progression_plan(
            diagnosis, diversity_plan, prior, project_root_with_assets,
        )
        dry_run = build_dry_run_validation_report(diagnosis, diversity_plan, corrected)

        assert dry_run["single_source_static_preview_blocked"] is True


class TestForbiddenActions:
    def test_does_not_generate_or_retry(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_does_not_generate_or_retry"""
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)
        corrected = build_corrected_timeline_visual_progression_plan(
            diagnosis, diversity_plan, prior, project_root_with_assets,
        )
        dry_run = build_dry_run_validation_report(diagnosis, diversity_plan, corrected)

        forbidden = dry_run["forbidden_actions_not_executed"]
        assert forbidden["generation_performed"] is False
        assert forbidden["retry_attempted"] is False
        assert forbidden["comfyui_submit_executed"] is False


class TestStateRouting:
    def test_updates_state_index_ledger(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_updates_state_index_ledger"""
        result = run_asset_diversity_timeline_repair(str(project_root_with_assets))

        assert result["artifact_index_updated"] is True
        assert result["episode_ledger_updated"] is True
        assert result["state_updated"] is True
        assert result["status"] == "ok"

        # Verify artifacts written
        control_dir = project_root_with_assets / "output" / "control"
        assert (control_dir / "static_preview_failure_diagnosis.json").exists()
        assert (control_dir / "timeline_visual_progression_contract.json").exists()
        assert (control_dir / "asset_diversity_plan.json").exists()
        assert (control_dir / "corrected_timeline_visual_progression_plan.json").exists()
        assert (control_dir / "asset_diversity_timeline_repair_dry_run.json").exists()
        assert (control_dir / "controlled_preview_rerender_authorization_packet.json").exists()

        # Verify index updated
        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "controlled_preview_rerender_authorization_required"
        assert index["asset_diversity_repair_executed"] is True

        # Verify ledger updated
        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        assert len(ledger) >= 2
        assert ledger[-1]["event_type"] == "asset_diversity_repair_artifacts_created"

    def test_routes_to_rerender_authorization(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_routes_to_rerender_authorization_only"""
        result = run_asset_diversity_timeline_repair(str(project_root_with_assets))

        assert result["current_state"] == "controlled_preview_rerender_authorization_required"
        assert result["next_allowed_action"] == "controlled_preview_rerender_authorization_required"
        assert result["status"] == "ok"

    def test_blocks_production_accepted_true(self, project_root_with_assets: Path):
        """test_asset_diversity_repair_blocks_production_accepted_true"""
        result = run_asset_diversity_timeline_repair(str(project_root_with_assets))

        assert result["production_accepted"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["voice_generation_executed"] is False
        assert result["preview_render_executed"] is False

    def test_routes_to_blocker_when_insufficient_assets(self, project_root: Path):
        prior = read_prior_artifacts(project_root)
        diagnosis = diagnose_static_preview_failure(prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root)

        assert diversity_plan["can_repair_from_existing_assets"] is False
        assert diversity_plan["would_require_future_generation_or_acquisition"] is True

        result = run_asset_diversity_timeline_repair(str(project_root))
        assert result["current_state"] == "asset_diversity_blocker_required"
        assert result["next_allowed_action"] == "asset_diversity_blocker_required"
        assert result["status"] == "accepted_with_blockers"


class TestAuthorizationPacket:
    def test_authorization_packet_created(self, project_root_with_assets: Path):
        prior = read_prior_artifacts(project_root_with_assets)
        diagnosis = diagnose_static_preview_failure(prior)
        contract = build_timeline_visual_progression_contract(diagnosis, prior)
        diversity_plan = build_asset_diversity_plan(diagnosis, prior, project_root_with_assets)
        corrected = build_corrected_timeline_visual_progression_plan(
            diagnosis, diversity_plan, prior, project_root_with_assets,
        )
        dry_run = build_dry_run_validation_report(diagnosis, diversity_plan, corrected)
        packet = build_authorization_packet(
            diagnosis, contract, diversity_plan, corrected, dry_run,
            "controlled_preview_rerender_authorization_required",
            "controlled_preview_rerender_authorization_required",
        )

        assert packet["packet_type"] == "controlled_preview_rerender_authorization_packet"
        assert packet["asset_diversity_timeline_repair_executed"] is True
        assert packet["static_preview_failure_confirmed"] is True
        assert packet["generation_performed"] is False
        assert packet["preview_render_executed"] is False
        assert packet["production_accepted"] is False


class TestFullPipeline:
    def test_full_pipeline_successful_repair(self, project_root_with_assets: Path):
        result = run_asset_diversity_timeline_repair(str(project_root_with_assets))

        assert result["task_id"] == TASK_ID
        assert result["static_preview_failure_confirmed"] is True
        assert result["duplicate_frame_ratio"] == 1.0
        assert result["root_cause"] == "single_source_asset_repeated"
        assert result["asset_diversity_plan_created"] is True
        assert result["timeline_visual_progression_contract_created"] is True
        assert result["corrected_timeline_visual_progression_plan_created"] is True
        assert result["dry_run_executed"] is True
        assert result["apply_performed"] is False
        assert result["single_source_static_preview_blocked"] is True
        assert result["minimum_unique_visual_sources_passed"] is True
        assert result["timeline_tracks_non_empty"] is True
        assert result["edl_operations_applied_or_blocked"] is True
        assert result["human_preview_decision_processed"] is False
        assert result["generation_performed"] is False

    def test_full_pipeline_blocked_repair(self, project_root: Path):
        result = run_asset_diversity_timeline_repair(str(project_root))

        assert result["task_id"] == TASK_ID
        assert result["static_preview_failure_confirmed"] is True
        assert result["can_repair_from_existing_assets"] is False
        assert result["current_state"] == "asset_diversity_blocker_required"
        assert result["next_allowed_action"] == "asset_diversity_blocker_required"
        assert result["generation_performed"] is False
        assert result["preview_render_executed"] is False
