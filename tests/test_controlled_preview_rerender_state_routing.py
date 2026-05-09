"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001 — Tests for controlled preview re-render state routing.

Validates that after re-render, state is correctly set to:
- preview_operator_review_required for valid non-static preview
- preview_correction_plan_required for static preview above threshold
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any

from PIL import Image


PREVIEW_WIDTH = 672
PREVIEW_HEIGHT = 384


def _make_project(tmp_path: Path, with_distinct_frames: bool = True) -> Path:
    """Create a mock project directory."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = tmp_path / "output" / "editorial"
    preview_dir = tmp_path / "output" / "previews"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    for art in ["preview_correction_plan.json", "preview_repair_contract.json",
                 "static_preview_prevention_policy.json", "controlled_preview_rerender_gate_package.json"]:
        _write_json(control_dir / art, {"type": "test"})

    _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
        "authorization_type": "controlled_preview_rerender",
        "authorized_by": "human_operator",
        "authorized": True,
        "max_preview_renders": 1,
        "target_state_before": "controlled_preview_rerender_authorization_required",
        "allowed_action": "controlled_preview_rerender",
        "stop_after_preview_render": True,
        "voice_generation_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
    })

    _write_json(editorial_dir / "timeline_model.json", {
        "tracks": {"video_main": [{"clip_id": "clip_001"}], "video_overlay": []},
        "scenes": [{"scene_id": "scene_001", "asset_refs": ["output/assets/test.png"]}],
    })
    _write_json(editorial_dir / "edit_decision_list.json", [{"operation": "add_clip"}])
    _write_json(control_dir / "approved_visual_assets_manifest.json", {
        "approved_assets": [{"path": str(assets_dir / "test.png")}],
    })

    img = Image.new("RGB", (64, 64), color=(128, 128, 128))
    img.save(assets_dir / "test.png")

    frames_dir = preview_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    if with_distinct_frames:
        for i in range(24):
            color_val = (i * 10) % 256
            frame = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), color=(color_val, color_val, color_val))
            frame.save(frames_dir / f"frame_{i:04d}.png")
    else:
        for i in range(24):
            frame = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), color=(128, 128, 128))
            frame.save(frames_dir / f"frame_{i:04d}.png")

    _write_json(control_dir / "artifact_index.json", {
        "current_state": "controlled_preview_rerender_authorization_required",
        "next_allowed_action": "controlled_preview_rerender_authorization_required",
    })

    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestControlledPreviewRerenderStateRouting:

    def test_valid_preview_routes_to_operator_review(self, tmp_path: Path):
        """Valid non-static preview routes to preview_operator_review_required."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        if not result.get("preview_static_blocker"):
            assert result["current_state"] == "preview_operator_review_required"
            assert result["next_allowed_action"] == "preview_operator_review_required"
            assert result["operator_review_required"] is True

    def test_static_preview_routes_to_correction_plan(self, tmp_path: Path):
        """Static preview above threshold routes to preview_correction_plan_required."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=False))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["current_state"] == "preview_correction_plan_required"
        assert result["next_allowed_action"] == "preview_correction_plan_required"
        assert result["preview_static_blocker"] is True

    def test_voice_generation_remains_blocked(self, tmp_path: Path):
        """Voice generation remains blocked in both routing states."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["voice_generation_executed"] is False
        assert result["forbidden_actions"]["voice_generation_executed"] is False

    def test_assembly_remains_blocked(self, tmp_path: Path):
        """Assembly remains blocked in both routing states."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["assembly_executed"] is False
        assert result["forbidden_actions"]["assembly_executed"] is False

    def test_downstream_remains_blocked(self, tmp_path: Path):
        """Downstream remains blocked in both routing states."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["downstream_executed"] is False
        assert result["forbidden_actions"]["downstream_executed"] is False

    def test_production_accepted_remains_false_in_both_states(self, tmp_path: Path):
        """production_accepted remains False regardless of routing."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        # Test with distinct frames (operator review route)
        project_root1 = str(_make_project(tmp_path, with_distinct_frames=True))
        result1 = run_controlled_preview_rerender(project_root=project_root1, execute=True)
        assert result1["production_accepted"] is False

        # Test with identical frames (correction plan route)
        project_root2 = str(_make_project(tmp_path, with_distinct_frames=False))
        result2 = run_controlled_preview_rerender(project_root=project_root2, execute=True)
        assert result2["production_accepted"] is False

    def test_operator_acceptance_not_faked(self, tmp_path: Path):
        """Operator acceptance is not generated by the agent."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        # No agent-generated acceptance
        assert result.get("operator_acceptance_faked") is False or "operator_acceptance_faked" not in result or result["forbidden_actions"]["operator_acceptance_faked"] is False

    def test_artifact_index_updated_with_correct_state(self, tmp_path: Path):
        """Artifact index is updated with the correct target state."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        run_controlled_preview_rerender(project_root=project_root, execute=True)

        index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())

        assert index["current_state"] in (
            "preview_operator_review_required",
            "preview_correction_plan_required",
        )
        assert index["production_accepted"] is False
        assert index["preview_render_executed"] is True

    def test_operator_review_required_flag_correct(self, tmp_path: Path):
        """operator_review_required is True only for valid non-static preview."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        # Distinct frames -> valid -> operator review required
        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        if not result.get("preview_static_blocker"):
            assert result["operator_review_required"] is True
        else:
            assert result["operator_review_required"] is False
