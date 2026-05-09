"""
Tests for Operator Visual Decision Routing — RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001.

Verifies:
- Accepted branch routes to timeline_to_preview_package_required
- Rejected branch routes to qa_to_correction_package_required
- Needs-fix branch routes to visual_issue_triage_required
- Missing verdict does not change state
- Routing report is created
- Artifact index is updated
- Episode ledger is updated
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    (tmp_path / "output" / "control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "assets").mkdir(parents=True, exist_ok=True)
    return project_dir_with_artifacts(tmp_path)


def project_dir_with_artifacts(base: Path) -> Path:
    """Set up artifact_index.json and episode_ledger.json."""
    control_dir = base / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "operator_visual_review_required",
            "next_allowed_action": "operator_visual_review_required",
            "production_accepted": False,
            "stage_results": [],
        }, f)

    with open(control_dir / "episode_ledger.json", "w") as f:
        json.dump([], f)

    return base


class TestAcceptedBranch:
    """Tests for the accepted verdict branch."""

    def test_accepted_routes_to_timeline_to_preview(self, project_dir):
        """Accepted verdict must route to timeline_to_preview_package_required."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="Good quality",
        )

        assert result["accepted_branch_supported"] is True
        assert result["current_state"] == "visual_asset_operator_accepted"
        assert result["next_allowed_action"] == "timeline_to_preview_package_required"
        assert result["production_accepted"] is False

    def test_acceptance_record_created(self, project_dir):
        """Accepted branch must create visual_asset_acceptance_record.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="Good quality",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "visual_asset_acceptance_record.json").exists()

        with open(control_dir / "visual_asset_acceptance_record.json") as f:
            record = json.load(f)
        assert record["production_accepted"] is False
        assert record["operator_verdict"] == "accepted"

    def test_approved_manifest_created(self, project_dir):
        """Accepted branch must create approved_visual_assets_manifest.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="Good quality",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "approved_visual_assets_manifest.json").exists()

        with open(control_dir / "approved_visual_assets_manifest.json") as f:
            manifest = json.load(f)
        assert manifest["production_accepted"] is False
        assert len(manifest["approved_assets"]) == 1


class TestRejectedBranch:
    """Tests for the rejected verdict branch."""

    def test_rejected_routes_to_correction_package(self, project_dir):
        """Rejected verdict must route to qa_to_correction_package_required."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="Synthetic skin texture",
        )

        assert result["rejected_branch_supported"] is True
        assert result["current_state"] == "visual_correction_required"
        assert result["next_allowed_action"] == "qa_to_correction_package_required"
        assert result["production_accepted"] is False

    def test_rejection_record_created(self, project_dir):
        """Rejected branch must create operator_visual_rejection_record.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="Synthetic skin texture",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "operator_visual_rejection_record.json").exists()

        with open(control_dir / "operator_visual_rejection_record.json") as f:
            record = json.load(f)
        assert record["production_accepted"] is False
        assert record["operator_verdict"] == "rejected"

    def test_correction_seed_packet_created(self, project_dir):
        """Rejected branch must create visual_correction_seed_packet.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="Synthetic skin texture",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "visual_correction_seed_packet.json").exists()

        with open(control_dir / "visual_correction_seed_packet.json") as f:
            seed = json.load(f)
        assert seed["retry_authorized"] is False
        assert seed["generation_authorized"] is False
        assert seed["correction_plan_required"] is True
        assert seed["production_accepted"] is False


class TestNeedsFixBranch:
    """Tests for the needs_fix verdict branch."""

    def test_needs_fix_routes_to_triage(self, project_dir):
        """Needs_fix verdict must route to visual_issue_triage_required."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="needs_fix",
            reason="Lighting adjustment needed",
        )

        assert result["needs_fix_branch_supported"] is True
        assert result["current_state"] == "visual_review_needs_fix"
        assert result["next_allowed_action"] == "visual_issue_triage_required"
        assert result["production_accepted"] is False

    def test_needs_fix_record_created(self, project_dir):
        """Needs-fix branch must create operator_visual_needs_fix_record.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="needs_fix",
            reason="Lighting adjustment needed",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "operator_visual_needs_fix_record.json").exists()

        with open(control_dir / "operator_visual_needs_fix_record.json") as f:
            record = json.load(f)
        assert record["production_accepted"] is False
        assert record["operator_verdict"] == "needs_fix"

    def test_issue_triage_packet_created(self, project_dir):
        """Needs-fix branch must create visual_issue_triage_packet.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="needs_fix",
            reason="Lighting adjustment needed",
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "visual_issue_triage_packet.json").exists()

        with open(control_dir / "visual_issue_triage_packet.json") as f:
            packet = json.load(f)
        assert packet["production_accepted"] is False


class TestMissingVerdictBranch:
    """Tests for the missing verdict branch."""

    def test_missing_verdict_does_not_change_state(self, project_dir):
        """Missing verdict must not change the current state."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        assert result["missing_verdict_branch_supported"] is True
        assert result["state_updated"] is False
        assert result["current_state"] == "operator_visual_review_required"
        assert result["next_allowed_action"] == "operator_visual_review_required"
        assert result["production_accepted"] is False

    def test_pending_artifact_created(self, project_dir):
        """Missing verdict must create operator_visual_decision_pending.json."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        control_dir = project_dir / "output" / "control"
        assert (control_dir / "operator_visual_decision_pending.json").exists()


class TestRoutingReport:
    """Tests for the routing report."""

    def test_routing_report_created_all_branches(self, project_dir):
        """Routing report must be created for each branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        for v in ["accepted", "rejected", "needs_fix", None]:
            r = record_operator_visual_decision(
                project_root=str(project_dir),
                verdict=v,
                reason="test" if v else None,
            )
            assert r["routing_report_created"] is True

    def test_routing_report_has_correct_branch(self, project_dir):
        """Routing report must indicate the correct branch taken."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "operator_visual_decision_routing_report.json") as f:
            report = json.load(f)

        assert report["branch_taken"] == "accepted"
        assert report["verdict"] == "accepted"
        assert report["production_accepted"] is False


class TestArtifactIndex:
    """Tests that artifact_index.json is updated correctly."""

    def test_artifact_index_updated_accepted(self, project_dir):
        """Artifact index must be updated for accepted branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx["current_state"] == "visual_asset_operator_accepted"
        assert idx["next_allowed_action"] == "timeline_to_preview_package_required"
        assert idx["production_accepted"] is False
        assert idx["operator_visual_decision_recorded"] is True

    def test_artifact_index_updated_rejected(self, project_dir):
        """Artifact index must be updated for rejected branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx["current_state"] == "visual_correction_required"
        assert idx["production_accepted"] is False
        assert idx["operator_visual_decision_recorded"] is True

    def test_artifact_index_not_advanced_missing_verdict(self, project_dir):
        """Artifact index must not advance state for missing verdict."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx["current_state"] == "operator_visual_review_required"
        assert idx["production_accepted"] is False
        assert idx["operator_visual_decision_recorded"] is True


class TestEpisodeLedger:
    """Tests that episode_ledger.json is updated."""

    def test_ledger_updated_accepted(self, project_dir):
        """Ledger must have an event for accepted branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        # Get the last event
        events = ledger if isinstance(ledger, list) else ledger.get("events", [])
        last_event = events[-1] if events else {}

        assert last_event.get("event_type") == "operator_visual_decision_gate_executed"
        assert last_event.get("operator_verdict") == "accepted"
        assert last_event.get("production_accepted") is False

    def test_ledger_updated_rejected(self, project_dir):
        """Ledger must have an event for rejected branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        events = ledger if isinstance(ledger, list) else ledger.get("events", [])
        last_event = events[-1] if events else {}

        assert last_event.get("operator_verdict") == "rejected"

    def test_ledger_updated_missing_verdict(self, project_dir):
        """Ledger must have an event for missing verdict."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        events = ledger if isinstance(ledger, list) else ledger.get("events", [])
        last_event = events[-1] if events else {}

        assert last_event.get("operator_verdict") == "missing"
