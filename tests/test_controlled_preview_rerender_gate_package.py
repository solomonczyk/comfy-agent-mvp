"""RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001 — Tests for controlled preview re-render gate package.

Validates that the gate package requires explicit authorization, does NOT authorize
renders, blocks all downstream stages, and lists required preconditions.
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


class TestControlledPreviewRerenderGatePackage:

    def test_render_not_authorized(self, tmp_path: Path):
        """Gate package does NOT authorize render."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["gate_type"] == "controlled_preview_rerender_authorization"
        assert gate["render_authorized_now"] is False

    def test_requires_operator_authorization(self, tmp_path: Path):
        """Gate requires explicit operator authorization before render."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["requires_operator_authorization"] is True

    def test_max_preview_renders_limited(self, tmp_path: Path):
        """Gate limits to exactly 1 preview render after authorization."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["max_preview_renders_after_authorization"] == 1

    def test_stop_after_preview_render(self, tmp_path: Path):
        """Gate stops after preview render, blocking downstream stages."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["stop_after_preview_render"] is True

    def test_voice_generation_blocked(self, tmp_path: Path):
        """Gate blocks voice generation."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["voice_generation_allowed"] is False

    def test_assembly_downstream_blocked(self, tmp_path: Path):
        """Gate blocks assembly and downstream."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        assert gate["assembly_allowed"] is False
        assert gate["downstream_allowed"] is False
        assert gate["production_accepted"] is False

    def test_required_preconditions_listed(self, tmp_path: Path):
        """Gate lists required preconditions before render can proceed."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        gate = planner.build_rerender_gate_package()

        preconditions = gate["required_preconditions"]
        assert len(preconditions) > 0
        assert "preview_correction_plan_exists" in preconditions
        assert "preview_repair_contract_exists" in preconditions
        assert "static_preview_prevention_policy_exists" in preconditions
        assert "script_supervisor_blocker_acknowledged" in preconditions

    def test_state_moves_to_controlled_rerender(self, tmp_path: Path):
        """Pipeline result reflects correct state transition."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        pipeline = planner.run_correction_pipeline()

        # The pipeline outputs should include a gate package with the target state
        gate = pipeline["controlled_preview_rerender_gate_package"]
        assert gate["gate_type"] == "controlled_preview_rerender_authorization"
        assert gate["render_authorized_now"] is False

        # Forbidden actions must all be false
        forbidden = pipeline["forbidden_actions_not_executed"]
        for action, value in forbidden.items():
            assert value is False, f"Action {action} should be False"
