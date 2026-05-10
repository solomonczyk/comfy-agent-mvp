"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-AUTHORIZATION-002.

Tests for the controlled preview re-render authorization gate package.
Validates that the gate correctly requires operator authorization, blocks
agent self-approval, prevents rendering, and updates index and ledger.
"""
import json
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_repair_artifacts(control_dir: Path) -> None:
    """Create a full set of valid repair artifacts in *control_dir*."""
    data = {
        "static_preview_failure_diagnosis.json": {
            "diagnosis_type": "static_preview_failure_diagnosis",
            "failure_type": "timeline_visual_progression_failure",
            "duplicate_frame_ratio": 1.0,
            "root_cause": "single_source_asset_repeated",
        },
        "asset_diversity_plan.json": {
            "plan_type": "asset_diversity_plan",
            "can_repair_from_existing_assets": True,
            "existing_usable_assets": [],
        },
        "timeline_visual_progression_contract.json": {
            "contract_type": "timeline_visual_progression_contract",
            "minimum_unique_visual_sources": 3,
        },
        "corrected_timeline_visual_progression_plan.json": {
            "plan_type": "corrected_timeline_visual_progression_plan",
            "proof_tracks_not_empty": True,
            "proof_edl_operations_applied": True,
            "no_generation_performed": True,
            "no_preview_render_performed": True,
            "expected_frame_sample_diversity": {
                "minimum_unique_visual_sources": 3,
            },
        },
        "asset_diversity_timeline_repair_dry_run.json": {
            "dry_run_executed": True,
            "minimum_unique_visual_sources_passed": True,
            "single_source_static_preview_blocked": True,
            "timeline_tracks_non_empty": True,
            "edl_operations_applied_or_blocked": True,
            "ready_for_controlled_preview_rerender_authorization": True,
        },
        "controlled_preview_rerender_authorization_packet.json": {
            "packet_type": "controlled_preview_rerender_authorization_packet",
            "ready_for_controlled_preview_rerender_authorization": True,
        },
    }
    for name, content in data.items():
        (control_dir / name).write_text(json.dumps(content, indent=2))


def run_gate(project_root: Path) -> tuple:
    """Invoke the CLI handler directly and return (exit_code, output_dict)."""
    from app.cli import combine_build_controlled_preview_rerender_authorization

    ns = Namespace(project_root=str(project_root), json=True)
    buf = StringIO()
    with redirect_stdout(buf):
        rc = combine_build_controlled_preview_rerender_authorization(ns)
    return rc, json.loads(buf.getvalue())


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project(tmp_path):
    """Create a temporary project with all repair artifacts present."""
    root = tmp_path / "project"
    ctrl = root / "output" / "control"
    ctrl.mkdir(parents=True)
    _make_repair_artifacts(ctrl)
    return root


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestControlledPreviewRerenderAuthorizationGate:
    """RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-AUTHORIZATION-002 gate tests."""

    def test_preview_rerender_authorization_requires_human_operator(self, project):
        """The authorization request must declare operator_authorization_required."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["operator_authorization_required"] is True

        req = project / "output" / "control" / \
            "controlled_preview_rerender_operator_authorization_request.json"
        assert req.is_file()
        body = json.loads(req.read_text())
        assert body["operator_authorization_required"] is True

    def test_preview_rerender_authorization_blocks_agent_approval(self, project):
        """Agent must not be able to self-authorize."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["agent_authorization_blocked"] is True

        req = project / "output" / "control" / \
            "controlled_preview_rerender_operator_authorization_request.json"
        body = json.loads(req.read_text())
        assert body["agent_may_authorize"] is False

    def test_preview_rerender_authorization_validates_asset_diversity_repair(self, project):
        """Asset diversity repair artifacts must be validated."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["asset_diversity_repair_validated"] is True

    def test_preview_rerender_authorization_sets_max_one_render(self, project):
        """Gate must enforce exactly one preview render max."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["max_preview_renders"] == 1
        assert out["stop_after_preview_render"] is True

    def test_preview_rerender_authorization_does_not_render(self, project):
        """No preview render or generation must occur."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["preview_render_executed"] is False
        assert out["generation_performed"] is False
        assert out["comfyui_submit_executed"] is False
        assert out["retry_attempted"] is False

    def test_preview_rerender_authorization_blocks_voice_assembly_downstream(self, project):
        """Voice, assembly, and downstream must remain blocked."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["voice_generation_executed"] is False
        assert out["audio_generation_executed"] is False
        assert out["assembly_executed"] is False
        assert out["downstream_executed"] is False

    def test_preview_rerender_authorization_does_not_set_production_accepted(self, project):
        """production_accepted must remain False."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["production_accepted"] is False

    def test_preview_rerender_authorization_updates_index_and_ledger(self, project):
        """artifact_index and episode_ledger must be updated."""
        rc, out = run_gate(project)
        assert rc == 0
        assert out["artifact_index_updated"] is True
        assert out["episode_ledger_updated"] is True

        ctrl = project / "output" / "control"

        # index checks
        idx = json.loads((ctrl / "artifact_index.json").read_text())
        assert idx["current_state"] == \
            "controlled_preview_rerender_authorization_required"
        assert idx["next_allowed_action"] == \
            "operator_preview_rerender_authorization_required"
        assert idx["controlled_preview_rerender_authorization_gate_built"] is True
        assert idx["operator_authorization_request_created"] is True
        assert idx["rerender_execution_contract_created"] is True
        assert idx["preflight_report_created"] is True
        assert idx["production_accepted"] is False

        # ledger checks
        ledger = json.loads((ctrl / "episode_ledger.json").read_text())
        assert isinstance(ledger, list)
        assert len(ledger) > 0
        last = ledger[-1]
        assert last["event_type"] == \
            "controlled_preview_rerender_authorization_gate_built"
        assert last["current_state"] == \
            "controlled_preview_rerender_authorization_required"
        assert last["operator_authorization_required"] is True
        assert last["agent_may_authorize"] is False
        assert last["max_preview_renders"] == 1
        assert last["production_accepted"] is False
