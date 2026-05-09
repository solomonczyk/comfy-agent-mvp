"""Tests for Post-Preview Reconciliation Report.

Validates that the reconciliation correctly aggregates preview audit,
operator decision, voice rejection, and blocker state into a single report.
"""

import json
import os
import pytest
from pathlib import Path


def test_reconciliation_report_exists():
    """Post-preview reconciliation report artifact exists."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["reconciliation_type"] == "post_preview_state_reconciliation"


def test_reconciliation_preview_invalid():
    """Reconciliation correctly reports preview as invalid."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["preview_valid"] is False
    assert data["preview_reason"] == "duplicate_static_frames_detected"


def test_reconciliation_contact_sheet_not_useful():
    """Reconciliation correctly reports contact sheet as not useful."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["contact_sheet_useful"] is False


def test_reconciliation_fake_decision_detected():
    """Reconciliation correctly detects fake operator decision."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fake_operator_decision_detected"] is True
    assert data["fake_operator_decision_invalidated"] is True


def test_reconciliation_voice_rejected():
    """Reconciliation correctly reports voice as rejected and blocked."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["voice_rejected"] is True
    assert data["voice_rejection_recorded"] is True
    assert data["voice_generation_allowed"] is False
    assert data["voice_generation_ready"] is False


def test_reconciliation_all_downstream_blocked():
    """Reconciliation blocks all assembly/downstream/production."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False
    assert data["production_accepted"] is False


def test_reconciliation_next_safe_action():
    """Reconciliation recommends next safe action as preview_correction_plan_required."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["next_safe_action"] == "preview_correction_plan_required"


def test_reconciliation_blocker_detected():
    """Reconciliation reports blocker as detected."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_reconciliation_report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["blocker_detected"] is True
    assert data["blocker_type"] == "invalid_static_preview_and_rejected_voice"


def test_reconciliation_builds_correctly():
    """build_post_preview_reconciliation produces correct aggregated state."""
    from app.agents.film_crew.audit import (
        audit_preview_frames,
        check_operator_decision_authenticity,
        build_post_preview_reconciliation,
    )

    project_root = "data/rc2_multishot1_ep01"
    preview_audit = audit_preview_frames(project_root)
    operator_check = check_operator_decision_authenticity(project_root)
    reconciliation = build_post_preview_reconciliation(project_root, preview_audit, operator_check)

    assert reconciliation.preview_valid is False
    assert reconciliation.contact_sheet_useful is False
    assert reconciliation.fake_operator_decision_detected is True
    assert reconciliation.voice_rejected is True
    assert reconciliation.assembly_allowed is False
    assert reconciliation.downstream_allowed is False
    assert reconciliation.production_accepted is False
    assert reconciliation.blocker_detected is True
