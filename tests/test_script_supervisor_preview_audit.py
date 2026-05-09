"""Tests for Script Supervisor Preview Continuity Audit.

Validates that the audit correctly detects duplicate/static frames,
evaluates contact sheet usefulness, and reports path mismatches.
"""

import hashlib
import json
import os
import pytest
from pathlib import Path


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_preview_audit_detects_duplicate_frames():
    """Audit detects that preview frames are mostly duplicate/static."""
    from app.agents.film_crew.audit import audit_preview_frames

    project_root = "data/rc2_multishot1_ep01"
    report = audit_preview_frames(project_root)

    assert report.total_frame_count == 720
    assert report.duplicate_frame_count > 0
    assert report.duplicate_static_ratio > 0.5
    assert report.preview_duplicate_static_frames_detected is True
    assert report.preview_continuity_passed is False
    assert report.blocker_required is True


def test_preview_audit_contact_sheet_not_useful():
    """Contact sheet is correctly flagged as not useful when frames are static."""
    from app.agents.film_crew.audit import audit_preview_frames

    project_root = "data/rc2_multishot1_ep01"
    report = audit_preview_frames(project_root)

    assert report.contact_sheet_found is True
    assert report.contact_sheet_useful is False
    assert report.timeline_progression_proven is False


def test_preview_audit_artifact_exists():
    """Preview audit report artifact exists in canonical location."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor_preview_audit_report.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_frame_count"] == 720
    assert data["duplicate_frame_count"] >= 670
    assert data["preview_continuity_passed"] is False


def test_preview_audit_path_consistency():
    """Preview path consistency is checked (output/preview vs output/previews)."""
    from app.agents.film_crew.audit import audit_preview_frames

    project_root = "data/rc2_multishot1_ep01"
    report = audit_preview_frames(project_root)

    # The report should at minimum report the expected path
    assert report.expected_preview_path == "output/preview"
    # Path exists check
    assert report.preview_found is True


def test_preview_audit_all_main_artifacts_found():
    """Audit should find main preview artifacts (mp4, gif, contact sheet, frames)."""
    from app.agents.film_crew.audit import audit_preview_frames

    project_root = "data/rc2_multishot1_ep01"
    report = audit_preview_frames(project_root)

    assert report.preview_found is True
    assert report.preview_gif_found is True
    assert report.contact_sheet_found is True
    assert report.frames_dir_found is True


def test_preview_audit_blocker_required():
    """Blocker is required when preview continuity fails."""
    from app.agents.film_crew.audit import audit_preview_frames

    project_root = "data/rc2_multishot1_ep01"
    report = audit_preview_frames(project_root)

    assert report.blocker_required is True
    assert report.preview_continuity_passed is False
