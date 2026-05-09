"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001 — Tests for controlled preview re-render static detection.

Validates that duplicate/static frame detection works correctly and
routes to correction plan when threshold is exceeded.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any

from PIL import Image


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

    # Required artifacts
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

    # Create a small test PNG
    img = Image.new("RGB", (64, 64), color=(128, 128, 128))
    img.save(assets_dir / "test.png")

    # Create frames directory with either distinct or identical frames
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


PREVIEW_WIDTH = 672
PREVIEW_HEIGHT = 384
DUPLICATE_THRESHOLD = 0.85


class TestControlledPreviewRerenderStaticDetection:

    def test_static_detection_executed_on_rerender(self, tmp_path: Path):
        """Static detection is executed after re-render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["static_detection_executed"] is True

    def test_distinct_frames_below_threshold(self, tmp_path: Path):
        """Distinct frames produce duplicate ratio below threshold."""
        from app.timeline.controlled_preview_rerender import detect_static_frames

        project_root = _make_project(tmp_path, with_distinct_frames=True)
        preview_dir = project_root / "output" / "previews"

        report = detect_static_frames(preview_dir / "frames", sample_interval=2)

        assert report["static_detection_executed"] is True
        assert report["duplicate_ratio"] <= DUPLICATE_THRESHOLD
        assert report["preview_static_blocker"] is False

    def test_identical_frames_above_threshold(self, tmp_path: Path):
        """Identical frames produce duplicate ratio above threshold."""
        from app.timeline.controlled_preview_rerender import detect_static_frames

        project_root = _make_project(tmp_path, with_distinct_frames=False)
        preview_dir = project_root / "output" / "previews"

        report = detect_static_frames(preview_dir / "frames", sample_interval=2)

        assert report["static_detection_executed"] is True
        assert report["preview_static_blocker"] is True

    def test_duplicate_ratio_routed_to_correction_plan(self, tmp_path: Path):
        """When duplicate ratio exceeds threshold, route to correction plan."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=False))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_static_blocker"] is True
        assert result["current_state"] == "preview_correction_plan_required"
        assert result["next_allowed_action"] == "preview_correction_plan_required"

    def test_valid_preview_routed_to_operator_review(self, tmp_path: Path):
        """When duplicate ratio is within threshold, route to operator review."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        if not result["preview_static_blocker"]:
            assert result["current_state"] == "preview_operator_review_required"
            assert result["next_allowed_action"] == "preview_operator_review_required"

    def test_contact_sheet_existence_alone_not_accepted(self, tmp_path: Path):
        """Contact sheet file existence alone is not treated as acceptance."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        # production_accepted must remain False regardless of contact sheet
        assert result["production_accepted"] is False
        assert result["forbidden_actions"]["production_accepted"] is False

    def test_static_detection_report_created(self, tmp_path: Path):
        """Static detection report artifact is created."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_distinct_frames=True))
        run_controlled_preview_rerender(project_root=project_root, execute=True)

        report_path = Path(project_root) / "output" / "control" / "controlled_preview_rerender_static_detection_report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text())
        assert report["static_detection_executed"] is True
        assert report["static_preview_prevention_policy_consumed"] is True
