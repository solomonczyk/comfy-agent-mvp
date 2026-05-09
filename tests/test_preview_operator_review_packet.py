"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — Operator review packet tests.

Tests the preview_operator_review_packet.json construction, review items,
allowed verdicts, and the constraint that agent cannot accept preview.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from app.timeline.controlled_preview_render import (
    build_preview_render_report,
    build_preview_result_review,
    build_preview_operator_review_packet,
)


def _make_control_dir(tmp_path: Path) -> Path:
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return control_dir


def _make_test_asset(tmp_path: Path) -> Path:
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1344, 768), color=(100, 100, 200))
    path = assets_dir / "test_asset.png"
    img.save(path)
    return path


class TestPreviewRenderReport:
    """Tests for preview_render_report.json construction."""

    def test_report_has_required_fields(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        from app.timeline.controlled_preview_render import execute_preview_render
        render_result = execute_preview_render(asset, preview_dir)

        report = build_preview_render_report(
            render_result,
            source_timeline="timeline_model.json",
            control_dir=control_dir,
        )

        assert report["preview_render_executed"] is True
        assert report["preview_render_count"] == 1
        assert "renderer" in report
        assert "source_timeline" in report
        assert report["voice_generation_executed"] is False
        assert report["assembly_executed"] is False
        assert report["downstream_executed"] is False
        assert report["production_accepted"] is False

    def test_report_lists_all_outputs(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        from app.timeline.controlled_preview_render import execute_preview_render
        render_result = execute_preview_render(asset, preview_dir)

        report = build_preview_render_report(
            render_result,
            source_timeline="timeline_model.json",
            control_dir=control_dir,
        )

        outputs = report.get("outputs", {})
        assert "preview_lowres.mp4" in outputs
        assert "preview.gif" in outputs
        assert "contact_sheet.jpg" in outputs


class TestPreviewResultReview:
    """Tests for preview_result_review.json construction."""

    def test_operator_review_required(self, tmp_path: Path):
        artifact_validation = {
            "valid": True,
            "preview_lowres_mp4_valid": True,
            "preview_gif_valid": True,
            "contact_sheet_jpg_valid": True,
            "errors": [],
            "warnings": [],
        }
        review = build_preview_result_review(artifact_validation, render_success=True)

        assert review["operator_review_required"] is True
        assert review["production_accepted"] is False

    def test_preview_artifacts_valid_flag(self, tmp_path: Path):
        artifact_validation = {
            "valid": True,
            "preview_lowres_mp4_valid": True,
            "preview_gif_valid": True,
            "contact_sheet_jpg_valid": True,
            "errors": [],
            "warnings": [],
        }
        review = build_preview_result_review(artifact_validation, render_success=True)
        assert review["preview_artifacts_valid"] is True

    def test_preview_artifacts_invalid(self, tmp_path: Path):
        artifact_validation = {
            "valid": False,
            "preview_lowres_mp4_valid": False,
            "preview_gif_valid": False,
            "contact_sheet_jpg_valid": False,
            "errors": ["Missing preview artifact"],
            "warnings": [],
        }
        review = build_preview_result_review(artifact_validation, render_success=False)
        assert review["preview_artifacts_valid"] is False

    def test_production_not_accepted(self, tmp_path: Path):
        artifact_validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        review = build_preview_result_review(artifact_validation, render_success=True)
        assert review["production_accepted"] is False


class TestPreviewOperatorReviewPacket:
    """Tests for preview_operator_review_packet.json construction."""

    def test_packet_has_required_fields(self, tmp_path: Path):
        render_report = {
            "preview_render_executed": True,
            "preview_render_count": 1,
            "renderer": "pillow",
            "fps": 24,
            "resolution": {"width": 672, "height": 384},
            "duration_sec": 30.0,
            "outputs": {
                "preview_lowres.mp4": {},
                "preview.gif": {},
                "contact_sheet.jpg": {},
            },
        }
        result_review = {
            "preview_artifacts_valid": True,
            "errors": [],
        }
        packet = build_preview_operator_review_packet(render_report, result_review)

        assert packet["operator_preview_review_required"] is True
        assert packet["preview_render_executed"] is True
        assert packet["preview_render_count"] == 1

    def test_review_items_present(self, tmp_path: Path):
        render_report = {"preview_render_executed": True, "preview_render_count": 1}
        result_review = {"preview_artifacts_valid": True, "errors": []}
        packet = build_preview_operator_review_packet(render_report, result_review)

        items = packet["review_items"]
        assert "timeline pacing" in items
        assert "asset placement" in items
        assert "subtitle timing" in items
        assert "transition quality" in items
        assert "preview readability" in items
        assert "audio/voice placeholder policy" in items
        assert "overall preview acceptability" in items

    def test_allowed_verdicts(self, tmp_path: Path):
        render_report = {"preview_render_executed": True, "preview_render_count": 1}
        result_review = {"preview_artifacts_valid": True, "errors": []}
        packet = build_preview_operator_review_packet(render_report, result_review)

        verdicts = packet["allowed_operator_verdicts"]
        assert "accepted" in verdicts
        assert "rejected" in verdicts
        assert "needs_fix" in verdicts

    def test_agent_cannot_accept_preview(self, tmp_path: Path):
        """Agent is explicitly forbidden from accepting preview."""
        render_report = {"preview_render_executed": True, "preview_render_count": 1}
        result_review = {"preview_artifacts_valid": True, "errors": []}
        packet = build_preview_operator_review_packet(render_report, result_review)

        assert packet["agent_may_accept_preview"] is False

    def test_production_not_accepted(self, tmp_path: Path):
        render_report = {"preview_render_executed": True, "preview_render_count": 1}
        result_review = {"preview_artifacts_valid": True, "errors": []}
        packet = build_preview_operator_review_packet(render_report, result_review)

        assert packet["production_accepted"] is False

    def test_packet_serializable(self, tmp_path: Path):
        """Packet must be JSON-serializable."""
        render_report = {"preview_render_executed": True, "preview_render_count": 1}
        result_review = {"preview_artifacts_valid": True, "errors": []}
        packet = build_preview_operator_review_packet(render_report, result_review)

        json_str = json.dumps(packet, indent=2)
        assert json_str is not None
        parsed = json.loads(json_str)
        assert parsed["operator_preview_review_required"] is True
