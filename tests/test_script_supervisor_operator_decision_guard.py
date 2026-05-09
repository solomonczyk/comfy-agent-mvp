"""Tests for Script Supervisor Operator Decision Guard.

Validates that the guard correctly detects fake agent-generated operator
decisions and prevents voice stage progression without real human input.
"""

import json
import os
import pytest
from pathlib import Path


def test_operator_decision_guard_detects_fake_decision():
    """Guard detects that the operator decision was agent-generated, not human."""
    from app.agents.film_crew.audit import check_operator_decision_authenticity

    project_root = "data/rc2_multishot1_ep01"
    result = check_operator_decision_authenticity(project_root)

    assert result["fake_operator_decision_detected"] is True
    assert result["human_operator_decision_found"] is False
    assert result["accepted_for_voice_stage_blocked"] is True


def test_operator_decision_guard_invalidation_verified():
    """Guard confirms that the fake operator decision was already invalidated."""
    from app.agents.film_crew.audit import check_operator_decision_authenticity

    project_root = "data/rc2_multishot1_ep01"
    result = check_operator_decision_authenticity(project_root)

    assert result["invalidation_verified"] is True
    assert result["agent_generated_decision_found"] is True


def test_operator_decision_guard_artifacts_checked():
    """Guard checks the expected artifacts for operator decision authenticity."""
    from app.agents.film_crew.audit import check_operator_decision_authenticity

    project_root = "data/rc2_multishot1_ep01"
    result = check_operator_decision_authenticity(project_root)

    assert len(result["artifacts_checked"]) >= 1
    assert "post_preview_routing_decision.json" in result["artifacts_checked"]


def test_operator_decision_guard_no_human_decision():
    """Guard correctly reports that no human operator decision exists."""
    from app.agents.film_crew.audit import check_operator_decision_authenticity

    project_root = "data/rc2_multishot1_ep01"
    result = check_operator_decision_authenticity(project_root)

    assert result["human_operator_decision_found"] is False
    assert result["operator_decision_valid"] is False
    assert result["accepted_for_voice_stage_blocked"] is True


def test_routing_decision_invalid():
    """The post_preview_routing_decision.json shows decision as invalid."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_routing_decision.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("decision_valid") is False
    assert data.get("visual_review_performed_by_operator") is False
    assert data.get("selected_branch") == "invalid_agent_generated_decision"


def test_reconciliation_confirms_violation():
    """The reconciliation artifact confirms agent_may_not_choose_verdict violation."""
    path = Path("data/rc2_multishot1_ep01/output/control/post_preview_operator_decision_reconciliation.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    detection = data.get("detection", {})
    assert detection.get("agent_may_not_choose_verdict_violation") is True


def test_accepted_for_voice_stage_blocked():
    """Agent-generated accepted_for_voice_stage is blocked without real operator."""
    from app.agents.film_crew.audit import check_operator_decision_authenticity

    project_root = "data/rc2_multishot1_ep01"
    result = check_operator_decision_authenticity(project_root)

    # The accepted_for_voice_stage verdict must NOT allow voice to proceed
    assert result["accepted_for_voice_stage_blocked"] is True
