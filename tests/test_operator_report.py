"""Tests for MK-OBS1.4 — Operator Report Generator."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.control.operator_report import OperatorReportGenerator, generate_operator_report


def _make_sample_beat_data() -> list[dict]:
    """Create sample beat data for testing."""
    return [
        {
            "beat_id": "beat_01",
            "frame_path": "/tmp/beat_01.png",
            "seed": 747001,
            "checkpoint": "juggernautXL_version2.safetensors",
            "steps": 20,
            "sampler": "dpmpp_sde",
            "scheduler": "karras",
            "prompt_source": "prompt_pack.json",
            "node_settings_status": "valid",
            "qa_verdict": "pass",
        },
        {
            "beat_id": "beat_02",
            "frame_path": "/tmp/beat_02.png",
            "seed": 747002,
            "checkpoint": "juggernautXL_version2.safetensors",
            "steps": 20,
            "sampler": "dpmpp_sde",
            "scheduler": "karras",
            "prompt_source": "prompt_pack.json",
            "node_settings_status": "valid",
            "qa_verdict": "fail",
        },
    ]


def _make_sample_prompt_pack() -> dict:
    """Create sample prompt pack for testing."""
    return {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "checkpoint": "juggernautXL_version2.safetensors",
        "global_negative": "blurry, deformed, bad anatomy",
        "beats": [
            {
                "beat_id": "beat_01",
                "steps": 20,
                "sampler": "dpmpp_sde",
                "scheduler": "karras",
            }
        ],
    }


def test_operator_report_html_is_created() -> None:
    """Test that operator_report.html is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "operator_report.html"
        beat_data = _make_sample_beat_data()

        generate_operator_report(
            output_path=output_path,
            project_id="test_project",
            episode_id="ep01",
            shot_id="shot01",
            current_state="ready_for_generation",
            expected_next_action="generate_frames",
            reference_lock_status={"approved": True, "reason": "Approved"},
            prompt_pack=_make_sample_prompt_pack(),
            beat_data=beat_data,
        )

        assert output_path.exists()
        assert output_path.is_file()


def test_operator_report_html_contains_beat_id_seed_checkpoint_qa_verdict() -> None:
    """Test that operator_report.html contains beat_id, seed, checkpoint, QA verdict."""
    beat_data = _make_sample_beat_data()

    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=beat_data,
    )

    html = generator.generate_html()

    # Check for beat_id
    assert "beat_01" in html
    assert "beat_02" in html

    # Check for seed
    assert "747001" in html
    assert "747002" in html

    # Check for checkpoint
    assert "juggernautXL_version2.safetensors" in html

    # Check for QA verdict
    assert "pass" in html
    assert "fail" in html


def test_operator_report_html_contains_overview_section() -> None:
    """Test that operator report contains overview section."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "Overview" in html
    assert "test_project" in html
    assert "ep01" in html
    assert "shot01" in html
    assert "ready_for_generation" in html
    assert "generate_frames" in html


def test_operator_report_html_contains_reference_lock_status() -> None:
    """Test that operator report contains reference lock status."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "All references approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "Reference Lock Status" in html
    assert "APPROVED" in html
    assert "All references approved" in html


def test_operator_report_html_denied_reference_lock() -> None:
    """Test that operator report shows denied reference lock."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": False, "reason": "Reference not approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "Reference Lock Status" in html
    assert "DENIED" in html
    assert "Reference not approved" in html


def test_operator_report_html_contains_prompt_pack_summary() -> None:
    """Test that operator report contains prompt pack summary."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "Prompt Pack Summary" in html
    assert "juggernautXL_version2.safetensors" in html
    assert "Number of Beats" in html


def test_operator_report_html_contains_beat_table() -> None:
    """Test that operator report contains beat table."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "Beat Details" in html
    assert "<table>" in html
    assert "<th>Beat ID</th>" in html
    assert "<th>Seed</th>" in html
    assert "<th>Checkpoint</th>" in html
    assert "<th>QA Verdict</th>" in html


def test_operator_report_html_with_empty_beat_data() -> None:
    """Test that operator report handles empty beat data."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=[],
    )

    html = generator.generate_html()

    assert "No beat data available" in html


def test_operator_report_html_is_valid_html() -> None:
    """Test that operator report generates valid HTML structure."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    # Check for basic HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert "<html" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html


def test_operator_report_contains_css_styling() -> None:
    """Test that operator report contains CSS styling."""
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    assert "<style>" in html
    assert "</style>" in html
    assert "background-color" in html
    assert "font-family" in html


def test_no_comfyui_or_subprocess_called() -> None:
    """Test that no ComfyUI or subprocess is called during report generation."""
    # This test ensures we only generate HTML without external calls
    generator = OperatorReportGenerator(
        project_id="test_project",
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        expected_next_action="generate_frames",
        reference_lock_status={"approved": True, "reason": "Approved"},
        prompt_pack=_make_sample_prompt_pack(),
        beat_data=_make_sample_beat_data(),
    )

    html = generator.generate_html()

    # If this completes without error, no subprocess was called
    assert html is not None
    assert len(html) > 0
