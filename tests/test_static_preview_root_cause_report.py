"""RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001 — Tests for static preview root cause report.

Validates that the root cause report correctly diagnoses why a preview became static,
identifies the primary cause, collects evidence, and checks all possible causes.
"""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict


def _make_mock_project(tmp_path: Path, duplicate_ratio: float = 0.93) -> Path:
    """Create a mock project directory with test artifacts."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = control_dir / "editorial"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)

    # Empty timeline — single scene, no assets
    timeline = {
        "project_id": "test_ep01",
        "fps": 24,
        "resolution": {"width": 1344, "height": 768},
        "tracks": {"video_main": [], "video_overlay": []},
        "scenes": [
            {
                "scene_id": "scene_001",
                "duration_sec": 30.0,
                "shot_ids": ["shot_001", "shot_002"],
                "asset_refs": [],
                "status": "planned",
            }
        ],
        "markers": [],
    }
    _write_json(editorial_dir / "timeline_model.json", timeline)

    # Minimal marker registry
    markers = [
        {
            "marker_id": "marker_001",
            "scene_id": "scene_001",
            "timecode": "00:00:05",
            "description": "single marker",
        }
    ]
    _write_json(editorial_dir / "marker_registry.json", markers)

    # Unapplied EDL
    edl = [
        {
            "operation_id": "edl_001",
            "operation": "insert_clip",
            "apply_performed": False,
        }
    ]
    _write_json(editorial_dir / "edit_decision_list.json", edl)

    # Transition policy
    transition = {"default": "hard_cut", "forbidden_transitions": ["spin"]}
    _write_json(editorial_dir / "transition_policy.json", transition)

    # Preview proof contract
    proof = {
        "preview_lowres_required": True,
        "preview_gif_required": True,
        "contact_sheet_required": True,
        "final_render_allowed": False,
    }
    _write_json(editorial_dir / "preview_proof_contract.json", proof)

    # Preview render report
    render_report = {
        "fps": 24,
        "outputs": {
            "preview_lowres.mp4": {"duration_sec": 30.0},
            "preview.gif": {"frame_count": 50},
        },
    }
    _write_json(control_dir / "preview_render_report.json", render_report)

    # Preview result review
    result_review = {
        "preview_artifacts_valid": True,
        "operator_review_required": True,
    }
    _write_json(control_dir / "preview_result_review.json", result_review)

    # Script supervisor audit
    audit = {
        "total_frame_count": 720,
        "unique_frame_count": int(720 * (1 - duplicate_ratio)),
        "duplicate_frame_count": int(720 * duplicate_ratio),
        "duplicate_static_ratio": duplicate_ratio,
        "preview_duplicate_static_frames_detected": True,
        "preview_continuity_passed": False,
        "contact_sheet_useful": False,
        "timeline_progression_proven": False,
        "preview_path_mismatch_detected": False,
        "expected_preview_path": "output/preview",
        "actual_preview_path": "output/preview",
        "blocker_required": True,
    }
    _write_json(control_dir / "script_supervisor_preview_audit_report.json", audit)

    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestStaticPreviewRootCauseReport:

    def test_root_cause_created_when_duplicate_ratio_high(self, tmp_path: Path):
        """Root cause report is created when duplicate ratio is high."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path, duplicate_ratio=0.93))
        planner = PreviewCorrectionPlanner(project_root)
        report = planner.build_root_cause_report()

        assert report["report_type"] == "static_preview_root_cause"
        assert report["primary_root_cause"] is not None
        assert report["confidence"] in ("high", "medium", "low")
        assert len(report["evidence"]) > 0

    def test_root_cause_detects_empty_timeline(self, tmp_path: Path):
        """Report flags timeline with no assets as the primary cause."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path, duplicate_ratio=0.93))
        planner = PreviewCorrectionPlanner(project_root)
        report = planner.build_root_cause_report()

        causes = report["possible_causes_checked"]
        assert causes["timeline_has_single_repeated_asset"] is True
        assert causes["frame_sequence_not_progressing"] is True
        assert causes["contact_sheet_sampling_invalid"] is True
        assert "timeline_empty_no_assets_placed" in report["primary_root_cause"]

    def test_root_cause_all_causes_checked(self, tmp_path: Path):
        """Report checks all required possible causes."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        report = planner.build_root_cause_report()

        required_checks = [
            "timeline_has_single_repeated_asset",
            "edl_reuses_same_frame_or_asset",
            "preview_renderer_samples_same_source",
            "frame_sequence_not_progressing",
            "contact_sheet_sampling_invalid",
            "path_mismatch_affects_preview_collection",
        ]
        for check in required_checks:
            assert check in report["possible_causes_checked"], (
                f"Missing cause check: {check}"
            )

    def test_root_cause_with_varied_timeline(self, tmp_path: Path):
        """When timeline has varied assets, the root cause is different."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path, duplicate_ratio=0.93))
        # Add assets to the timeline to simulate a non-empty scenario
        control_dir = Path(project_root) / "output" / "control"
        timeline_path = control_dir / "editorial" / "timeline_model.json"
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        timeline["scenes"][0]["asset_refs"] = ["asset_001.png", "asset_002.png"]
        timeline["tracks"]["video_main"] = [
            {"clip_id": "clip_001", "asset": "asset_001.png"}
        ]
        timeline_path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")

        planner = PreviewCorrectionPlanner(str(project_root))
        report = planner.build_root_cause_report()

        # With assets in timeline, the cause should shift
        causes = report["possible_causes_checked"]
        assert causes["timeline_has_single_repeated_asset"] is False

    def test_root_cause_evidence_includes_specific_numbers(self, tmp_path: Path):
        """At least one evidence string includes quantitative data."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path, duplicate_ratio=0.93))
        planner = PreviewCorrectionPlanner(project_root)
        report = planner.build_root_cause_report()

        evidence_with_numbers = [
            ev for ev in report["evidence"] if any(c.isdigit() for c in ev)
        ]
        assert len(evidence_with_numbers) >= 1, (
            "At least one evidence item should contain quantitative data"
        )
