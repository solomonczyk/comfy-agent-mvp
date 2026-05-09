"""RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001 — Tests for preview repair contract.

Validates that the repair contract defines what the next render must prove,
duplicate frame justification rules, and blocked downstream stages.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any


def _make_mock_project(tmp_path: Path) -> Path:
    """Create a mock project directory."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = control_dir / "editorial"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)

    _write_json(editorial_dir / "timeline_model.json", {
        "tracks": {"video_main": [], "video_overlay": []},
        "scenes": [{"scene_id": "scene_001", "asset_refs": []}],
    })
    _write_json(control_dir / "script_supervisor_preview_audit_report.json", {
        "total_frame_count": 720,
        "unique_frame_count": 50,
        "duplicate_frame_count": 670,
        "duplicate_static_ratio": 0.93,
    })
    _write_json(editorial_dir / "edit_decision_list.json", [])
    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestPreviewRepairContract:

    def test_contract_requires_non_static_progression(self, tmp_path: Path):
        """Repair contract requires non-static visual progression."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        contract = planner.build_repair_contract()

        assert contract["contract_type"] == "preview_repair_contract"
        render_must = contract["render_must_prove"]
        assert "non_static_visual_progression" in render_must
        assert "valid_frame_sampling" in render_must
        assert "useful_contact_sheet" in render_must

    def test_preview_render_not_executed_by_contract(self, tmp_path: Path):
        """Contract itself does not execute any render."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        pipeline = planner.run_correction_pipeline()

        forbidden = pipeline["forbidden_actions_not_executed"]
        assert forbidden["preview_render_executed"] is False
        assert forbidden["voice_generation_executed"] is False

    def test_voice_generation_remains_blocked(self, tmp_path: Path):
        """Voice generation is blocked by the contract."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        contract = planner.build_repair_contract()

        blocked = contract["blocked_downstream_stages"]
        assert blocked["voice_generation"] is False
        assert blocked["assembly"] is False
        assert blocked["downstream"] is False
        assert blocked["production_acceptance"] is False

    def test_assembly_downstream_blocked(self, tmp_path: Path):
        """Assembly and downstream remain blocked in the pipeline result."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        pipeline = planner.run_correction_pipeline()

        forbidden = pipeline["forbidden_actions_not_executed"]
        assert forbidden["assembly_executed"] is False
        assert forbidden["downstream_executed"] is False
        assert forbidden["production_accepted"] is False

    def test_contract_includes_canonical_path_requirement(self, tmp_path: Path):
        """Contract requires canonical preview path (singular, not plural)."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        contract = planner.build_repair_contract()

        render_must = contract["render_must_prove"]
        path_req = render_must["canonical_preview_path"]
        assert "preview/" in path_req or "singular" in path_req

    def test_duplicate_frame_justification_defined(self, tmp_path: Path):
        """Contract defines max allowed duplicate ratio and justification requirement."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        contract = planner.build_repair_contract()

        justification = contract["duplicate_frame_justification"]
        assert "max_allowed_ratio" in justification
        assert justification["above_threshold_requires_explicit_still_scene_contract"] is True
