"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001 — Tests for corrected preview timeline input.

Validates that the corrected timeline input is created correctly from
editorial timeline model, EDL, and repair contract.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any


def _make_project(tmp_path: Path, timeline_empty: bool = False, no_edl: bool = False) -> Path:
    """Create a mock project directory."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = tmp_path / "output" / "editorial"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)

    _write_json(control_dir / "preview_correction_plan.json", {"plan_type": "test"})
    _write_json(control_dir / "preview_repair_contract.json", {"contract_type": "test"})
    _write_json(control_dir / "static_preview_prevention_policy.json", {"policy_type": "test"})
    _write_json(control_dir / "controlled_preview_rerender_gate_package.json", {"gate_type": "test"})
    _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
        "authorization_type": "controlled_preview_rerender",
        "authorized": True,
        "max_preview_renders": 1,
        "stop_after_preview_render": True,
        "voice_generation_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
    })
    _write_json(control_dir / "approved_visual_assets_manifest.json", {
        "approved_assets": [{"path": "output/assets/test.png"}],
    })

    if timeline_empty:
        _write_json(editorial_dir / "timeline_model.json", {
            "tracks": {"video_main": [], "video_overlay": []},
            "scenes": [],
        })
    else:
        _write_json(editorial_dir / "timeline_model.json", {
            "tracks": {"video_main": [{"clip_id": "clip_001"}], "video_overlay": []},
            "scenes": [{"scene_id": "scene_001", "asset_refs": ["output/assets/test.png"]}],
        })

    if no_edl:
        _write_json(editorial_dir / "edit_decision_list.json", [])
    else:
        _write_json(editorial_dir / "edit_decision_list.json", [
            {"operation": "add_clip", "scene_id": "scene_001", "source": "test.png"},
            {"operation": "place_asset", "scene_id": "scene_001", "source": "test.png"},
        ])

    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestCorrectedPreviewTimelineInput:

    def test_corrected_input_created(self, tmp_path: Path):
        """Corrected timeline input is created with correct structure."""
        from app.timeline.controlled_preview_rerender import build_corrected_preview_timeline_input

        project_root = _make_project(tmp_path, timeline_empty=False)
        result = build_corrected_preview_timeline_input(project_root)

        assert result["timeline_empty"] is False
        assert result["video_tracks_empty"] is False
        assert result["asset_refs_present"] is True
        assert result["edl_operations_applied"] is True
        assert result["ready_for_preview_render"] is True
        assert result["expected_visual_segments"] >= 1
        assert result["repair_contract_consumed"] is True

    def test_corrected_input_shows_empty_timeline(self, tmp_path: Path):
        """Corrected timeline input correctly reports empty timeline."""
        from app.timeline.controlled_preview_rerender import build_corrected_preview_timeline_input

        project_root = _make_project(tmp_path, timeline_empty=True)
        result = build_corrected_preview_timeline_input(project_root)

        assert result["timeline_empty"] is True
        assert result["video_tracks_empty"] is True
        assert result["asset_refs_present"] is False
        assert result["ready_for_preview_render"] is False

    def test_corrected_input_without_edl(self, tmp_path: Path):
        """Corrected timeline input handles missing EDL gracefully."""
        from app.timeline.controlled_preview_rerender import build_corrected_preview_timeline_input

        project_root = _make_project(tmp_path, timeline_empty=False, no_edl=True)
        result = build_corrected_preview_timeline_input(project_root)

        # Should still attempt to apply operations from manifest
        assert result["timeline_empty"] is False
        assert result["asset_refs_present"] is True

    def test_corrected_input_has_edl_operations(self, tmp_path: Path):
        """Corrected timeline input lists applied EDL operations."""
        from app.timeline.controlled_preview_rerender import build_corrected_preview_timeline_input

        project_root = _make_project(tmp_path, timeline_empty=False)
        result = build_corrected_preview_timeline_input(project_root)

        assert len(result["edl_operations"]) > 0
        for op in result["edl_operations"]:
            assert op["applied"] is True

    def test_corrected_input_tracks_scenes_and_clips(self, tmp_path: Path):
        """Corrected timeline input reports scene and clip counts."""
        from app.timeline.controlled_preview_rerender import build_corrected_preview_timeline_input

        project_root = _make_project(tmp_path, timeline_empty=False)
        result = build_corrected_preview_timeline_input(project_root)

        assert result["scenes_count"] > 0
        assert isinstance(result["video_main_clips"], int)
        assert isinstance(result["video_overlay_clips"], int)
        assert result["asset_refs_count"] > 0
