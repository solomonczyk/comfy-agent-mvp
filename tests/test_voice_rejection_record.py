"""Tests for Voice Rejection Record.

Validates that voice rejection is correctly recorded, voice_generation_ready
remains false, and all downstream steps are blocked.
"""

import json
import os
import pytest
from pathlib import Path


def test_voice_rejection_record_exists():
    """Voice rejection record artifact exists at canonical path."""
    path = Path("data/rc2_multishot1_ep01/output/control/voice_rejection_record.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["voice_status"] == "operator_rejected"


def test_voice_rejection_blocks_generation():
    """Voice rejection record correctly blocks voice generation."""
    path = Path("data/rc2_multishot1_ep01/output/control/voice_rejection_record.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["voice_generation_ready"] is False
    assert data["voice_generation_allowed"] is False
    assert data["voice_stage_allowed"] is False


def test_voice_rejection_blocks_downstream():
    """Voice rejection record blocks all audio/assembly/downstream steps."""
    path = Path("data/rc2_multishot1_ep01/output/control/voice_rejection_record.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["audio_stage_allowed"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False
    assert data["production_accepted"] is False


def test_voice_rejection_builds_correctly():
    """build_voice_rejection_record produces correct rejection state."""
    from app.agents.film_crew.audit import build_voice_rejection_record

    project_root = "data/rc2_multishot1_ep01"
    record = build_voice_rejection_record(project_root)

    assert record.voice_status == "operator_rejected"
    assert record.voice_generation_ready is False
    assert record.voice_generation_allowed is False
    assert record.assembly_allowed is False
    assert record.downstream_allowed is False
    assert record.production_accepted is False


def test_voice_rejection_blocking_artifacts():
    """Voice rejection record references correct blocking artifacts."""
    from app.agents.film_crew.audit import build_voice_rejection_record

    project_root = "data/rc2_multishot1_ep01"
    record = build_voice_rejection_record(project_root)

    assert len(record.blocking_artifacts) >= 2
    assert "post_preview_routing_decision.json" in record.blocking_artifacts


def test_voice_generation_ready_false_in_index():
    """artifact_index.json correctly shows voice_generation_ready=false."""
    path = Path("data/rc2_multishot1_ep01/output/control/artifact_index.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("voice_generation_ready") is False


def test_voice_generation_allowed_false():
    """voice_generation_allowed remains false after script supervisor audit."""
    from app.agents.film_crew.audit import build_voice_rejection_record

    project_root = "data/rc2_multishot1_ep01"
    record = build_voice_rejection_record(project_root)

    assert record.voice_generation_allowed is False
    assert record.voice_stage_allowed is False
