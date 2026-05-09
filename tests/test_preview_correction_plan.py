"""RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001 — Tests for preview correction plan.

Validates that the correction plan includes required repairs, duplicate frame policy,
contact sheet policy, and the correct next gate.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Dict


def _make_mock_project(tmp_path: Path) -> Path:
    """Create a mock project directory with basic test artifacts."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = control_dir / "editorial"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)

    # Minimal timeline
    timeline = {
        "tracks": {"video_main": [], "video_overlay": []},
        "scenes": [{"scene_id": "scene_001", "asset_refs": []}],
    }
    _write_json(editorial_dir / "timeline_model.json", timeline)

    # Minimal EDL
    _write_json(editorial_dir / "edit_decision_list.json", [
        {"operation_id": "edl_001", "apply_performed": False},
    ])

    # Script supervisor audit
    _write_json(control_dir / "script_supervisor_preview_audit_report.json", {
        "total_frame_count": 720,
        "unique_frame_count": 50,
        "duplicate_frame_count": 670,
        "duplicate_static_ratio": 0.93,
    })

    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestPreviewCorrectionPlan:

    def test_correction_plan_created_when_duplicate_ratio_high(self, tmp_path: Path):
        """Correction plan is created when duplicate ratio is high."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        root_cause = planner.build_root_cause_report()
        plan = planner.build_correction_plan(root_cause)

        assert plan["plan_type"] == "preview_correction_plan"
        assert plan["correction_goal"] is not None
        assert len(plan["required_repairs"]) > 0

    def test_contact_sheet_file_existence_not_proof(self, tmp_path: Path):
        """Plan explicitly states that contact_sheet file existence is not proof of progression."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        root_cause = planner.build_root_cause_report()
        plan = planner.build_correction_plan(root_cause)

        assert plan["contact_sheet_policy"]["technical_file_exists_is_not_enough"] is True
        assert plan["contact_sheet_policy"]["must_prove_timeline_progression"] is True

    def test_duplicate_frame_policy_has_threshold(self, tmp_path: Path):
        """Duplicate frame policy includes a max ratio threshold and blocker requirement."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        root_cause = planner.build_root_cause_report()
        plan = planner.build_correction_plan(root_cause)

        policy = plan["duplicate_frame_policy"]
        assert "max_duplicate_ratio" in policy
        assert isinstance(policy["max_duplicate_ratio"], (int, float))
        assert policy["static_preview_blocker_required"] is True

    def test_next_gate_is_controlled_rerender(self, tmp_path: Path):
        """Plan requires controlled_preview_rerender_authorization_required as next gate."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        root_cause = planner.build_root_cause_report()
        plan = planner.build_correction_plan(root_cause)

        assert plan["next_gate_required"] == "controlled_preview_rerender_authorization_required"

    def test_required_repairs_include_timeline_and_edl(self, tmp_path: Path):
        """Required repairs list includes timeline, EDL, and sampling related items."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        root_cause = planner.build_root_cause_report()
        plan = planner.build_correction_plan(root_cause)

        repairs = " ".join(plan["required_repairs"]).lower()
        assert "timeline" in repairs
        assert "edl" in repairs or "asset" in repairs
        assert "contact_sheet" in repairs or "sample" in repairs
