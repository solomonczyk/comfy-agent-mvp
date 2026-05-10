"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-AUTHORIZATION-002.

Tests for the controlled preview re-render authorization gate package.
Validates that the gate correctly requires operator authorization, blocks
agent self-approval, prevents rendering, and updates index and ledger.

RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-AUTHORIZATION-002-FIX:
Regression tests verify that summary/proof/state cannot disagree — if
operator authorization is validated, state must be execute_required; if
authorization is not yet present, state must remain authorization_required.
"""
import json
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine


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


def _make_operator_authorization(control_dir: Path) -> None:
    """Create a valid human operator authorization artifact."""
    auth = {
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
    }
    (control_dir / "controlled_preview_rerender_operator_authorization.json") \
        .write_text(json.dumps(auth, indent=2))


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
    """Create a temporary project with all repair artifacts present, no operator auth."""
    root = tmp_path / "project"
    ctrl = root / "output" / "control"
    ctrl.mkdir(parents=True)
    _make_repair_artifacts(ctrl)
    return root


@pytest.fixture
def project_with_auth(tmp_path):
    """Create a project with all repair artifacts AND valid operator authorization."""
    root = tmp_path / "project_auth"
    ctrl = root / "output" / "control"
    ctrl.mkdir(parents=True)
    _make_repair_artifacts(ctrl)
    _make_operator_authorization(ctrl)
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


class TestAuthorizationStateConsistency:
    """RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-AUTHORIZATION-002-FIX.

    Regression tests verifying summary/proof/state cannot disagree.
    """

    def test_state_consistency_with_valid_operator_auth(self, project_with_auth):
        """When valid operator authorization exists, state must be execute_required."""
        rc, out = run_gate(project_with_auth)
        assert rc == 0

        assert out["operator_authorization_exists"] is True
        assert out["operator_authorization_valid"] is True
        assert out["current_state"] == "controlled_preview_rerender_execute_required"
        assert out["next_allowed_action"] == \
            "controlled_preview_rerender_execute_required"
        assert out["next_task_recommendation"] == \
            "RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-EXECUTE-002"

        # Invariant: validated authorization + authorization_required cannot coexist
        assert out["operator_authorization_required"] is False

        assert out["preview_render_executed"] is False
        assert out["generation_performed"] is False
        assert out["assembly_executed"] is False
        assert out["production_accepted"] is False

    def test_state_consistency_without_operator_auth(self, project):
        """Without operator authorization, state must stay at authorization_required."""
        rc, out = run_gate(project)
        assert rc == 0

        assert out["operator_authorization_exists"] is False
        assert out["current_state"] == \
            "controlled_preview_rerender_authorization_required"
        assert out["next_allowed_action"] == \
            "operator_preview_rerender_authorization_required"
        assert out["next_task_recommendation"] == \
            "operator_must_provide_preview_rerender_authorization"

        assert out["operator_authorization_required"] is True

    def test_summary_proof_state_invariant(self, project, project_with_auth):
        """Core invariant: summary/proof/state must be consistent.

        If operator_authorization_validated == True then state must be
        execute_required AND operator_authorization_required must be False.
        If operator_authorization_validated == False then state must be
        authorization_required AND operator_authorization_required must be True.
        """
        _, out_a = run_gate(project)
        if not out_a["operator_authorization_exists"]:
            assert out_a["current_state"] == \
                "controlled_preview_rerender_authorization_required"
            assert out_a["operator_authorization_required"] is True
        else:
            assert out_a["current_state"] == \
                "controlled_preview_rerender_execute_required"
            assert out_a["operator_authorization_required"] is False

        _, out_b = run_gate(project_with_auth)
        assert out_b["operator_authorization_exists"] is True
        assert out_b["operator_authorization_valid"] is True
        assert out_b["current_state"] == \
            "controlled_preview_rerender_execute_required"
        assert out_b["operator_authorization_required"] is False

        assert out_a["current_state"] != out_b["current_state"]
        assert out_a["operator_authorization_required"] != \
            out_b["operator_authorization_required"]

    def test_state_machine_transition_allowed(self):
        """The state machine must allow authorization_required to execute_required."""
        assert CombineStateMachine.can_transition(
            "controlled_preview_rerender_authorization_required",
            "controlled_preview_rerender_execute_required",
        )

    def test_state_machine_execute_cannot_skip_to_downstream(self):
        """The execute state must be blocked from generation/assembly/downstream."""
        for forbidden_state in [
            "generate_assets",
            "real_generate_assets",
            "visual_qa_required",
            "completed",
            "production_accepted",
            "assembly_required",
            "assembly_preflight_required",
            "final_qc_required",
            "final_operator_acceptance",
            "voice_generation_authorization_required",
        ]:
            assert not CombineStateMachine.can_transition(
                "controlled_preview_rerender_execute_required",
                forbidden_state,
            ), f"transition to {forbidden_state} should be forbidden"

    def test_execute_state_is_valid(self):
        """The new execute state must be recognized as valid."""
        assert CombineStateMachine.is_valid_state(
            "controlled_preview_rerender_execute_required"
        )
