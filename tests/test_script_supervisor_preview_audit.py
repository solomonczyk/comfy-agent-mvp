"""Tests for Script Supervisor PreviewAuditor (standards-driven).

Validates that the preview audit correctly detects static/duplicate frames,
evaluates contact sheet usefulness, and produces traceable standards findings.
"""

import json
import pytest
from pathlib import Path


def test_preview_auditor_class_exists():
    """PreviewAuditor class can be imported and instantiated."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    assert auditor.DUP_THRESHOLD == 0.5
    assert auditor.STATIC_THRESHOLD == 0.9


def test_preview_audit_loads_standards():
    """PreviewAuditor loads standards and produces traceable findings."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    assert report["standards_pack_version"] == "1.0.0"
    assert report["traceable"] is True
    assert report["role"] == "script_supervisor"

    # All findings must have traceable references
    for f in report["findings"]:
        assert "standard_id" in f
        assert "policy_id" in f
        assert "rule_id" in f
        assert "role" in f
        assert "severity" in f
        assert "decision" in f
        assert f.get("traceable") is True


def test_preview_audit_checks_preview_artifacts():
    """PreviewAuditor checks for preview artifact presence."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    assert "preview_artifacts_registered" in report
    assert "preview_mp4_found" in report
    assert "preview_gif_found" in report
    assert "contact_sheet_found" in report
    assert "frames_dir_found" in report


def test_preview_audit_checks_static_duplicate_risk():
    """PreviewAuditor checks and reports static/duplicate frame risk."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    assert report["preview_static_or_duplicate_risk_checked"] is True
    assert "duplicate_static_ratio" in report
    assert "duplicate_frame_count" in report
    assert "total_frame_count" in report
    assert "static_or_duplicate_risk" in report


def test_preview_audit_path_consistency_checked():
    """PreviewAuditor checks preview path consistency."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    assert report["path_consistency_checked"] is True
    assert "path_mismatch_detected" in report


def test_preview_audit_report_structure():
    """Preview audit report has correct structure and metadata."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    assert report["report_id"] == "script_supervisor_preview_audit_report"
    assert report["version"] == "1.0.0"
    assert report["role"] == "script_supervisor"


def test_preview_audit_findings_have_script_supervisor_role():
    """All findings in the preview audit reference script_supervisor role."""
    from app.agents.script_supervisor import PreviewAuditor

    auditor = PreviewAuditor("data/rc2_multishot1_ep01")
    report = auditor.audit()

    for f in report["findings"]:
        assert f.get("role") == "script_supervisor", f"Finding missing script_supervisor role: {f}"


def test_preview_audit_artifact_exists():
    """Preview audit report artifact exists at canonical path."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor/script_supervisor_preview_audit_report.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["report_id"] == "script_supervisor_preview_audit_report"
    assert data["preview_static_or_duplicate_risk_checked"] is True
