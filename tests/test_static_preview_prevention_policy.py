"""RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001 — Tests for static preview prevention policy.

Validates that the prevention policy defines detection requirements, thresholds,
and rules to prevent future static preview acceptance.
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


class TestStaticPreviewPreventionPolicy:

    def test_detection_required_flag(self, tmp_path: Path):
        """Policy requires static preview detection."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        assert policy["policy_type"] == "static_preview_prevention_policy"
        assert policy["static_preview_detection_required"] is True

    def test_duplicate_frame_threshold_defined(self, tmp_path: Path):
        """Policy defines a duplicate frame threshold."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        assert "duplicate_frame_threshold" in policy
        assert isinstance(policy["duplicate_frame_threshold"], (int, float))
        assert policy["duplicate_frame_threshold"] > 0

    def test_contact_sheet_must_show_progression(self, tmp_path: Path):
        """Policy requires contact sheet to prove visual progression."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        assert policy["contact_sheet_must_show_progression"] is True

    def test_technical_success_not_operator_acceptance(self, tmp_path: Path):
        """Policy enforces that technical preview success != operator acceptance."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        key = "technical_preview_success_is_not_operator_acceptance"
        assert policy[key] is True

    def test_voice_stage_blocked_until_real_approval(self, tmp_path: Path):
        """Policy blocks voice stage until real operator preview approval."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        assert policy["voice_stage_blocked_until_real_operator_preview_approval"] is True

    def test_prevention_rules_defined(self, tmp_path: Path):
        """Policy includes explicit prevention rules."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        assert len(policy["prevention_rules"]) > 0
        assert any("duplicate" in rule.lower() for rule in policy["prevention_rules"])

    def test_no_fake_operator_acceptance(self, tmp_path: Path):
        """Policy prevents agents from accepting preview on behalf of operators."""
        from app.agents.film_crew.preview_correction_planner import (
            PreviewCorrectionPlanner,
        )

        project_root = str(_make_mock_project(tmp_path))
        planner = PreviewCorrectionPlanner(project_root)
        policy = planner.build_prevention_policy()

        rules_text = " ".join(policy["prevention_rules"]).lower()
        assert "operator" in rules_text or "agent" in rules_text
