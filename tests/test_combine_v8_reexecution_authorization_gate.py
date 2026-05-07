"""Tests for RC-COMBINE-V2-6001-6300 V8 reexecution authorization gate.

Tests cover:
- state_transition_correct
- production_accepted_false
- assembly_downstream_blocked
- generation_allowed_now_false
- gate_artifact_fields_correct
- episode_ledger_updated
"""

import json
import tempfile
from pathlib import Path

import pytest


def _create_prerequisite_artifacts(control_dir, state="v8_generation_runtime_blocked"):
    """Create prerequisite artifacts that the gate expects."""
    control_dir.mkdir(parents=True, exist_ok=True)
    agent_dir = control_dir / "agent_role_contracts"
    agent_dir.mkdir(parents=True, exist_ok=True)

    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": state,
            "next_allowed_action": "v8_generation_runtime_recovery_required" if state == "v8_generation_runtime_blocked" else state,
            "generated_assets": [],
            "new_generation_performed": False,
            "comfyui_execution": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_execution.json", "w") as f:
        json.dump({
            "workflow_submitted": True,
            "comfyui_execution": False,
            "execute_mode": False,
            "prompt_id": "",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": [],
            "collection_status": "dry_run",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_generation_result_review.json", "w") as f:
        json.dump({
            "generated_assets_count": 0,
            "next_allowed_action": "v8_operator_visual_review_required",
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_operator_visual_review_packet.json", "w") as f:
        json.dump({"generated_assets": []}, f, indent=2)

    with open(control_dir / "combine_v2_v8_generation_timeout_reconciliation.json", "w") as f:
        json.dump({
            "task_id": "RC-COMBINE-V2-5701-6000-RECOVERY",
            "current_state": state,
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_real_execution_readiness_diagnosis.json", "w") as f:
        json.dump({"diagnosis": "ok"}, f, indent=2)

    with open(control_dir / "combine_v2_v8_runtime_preflight_report.json", "w") as f:
        json.dump({"preflight": "ok"}, f, indent=2)

    with open(control_dir / "combine_v2_v8_dry_run_guard_report.json", "w") as f:
        json.dump({"guard": "ok"}, f, indent=2)


class TestV8ReexecutionAuthorizationGate:

    @pytest.fixture
    def project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_prerequisite_artifacts(root / "output" / "control")
            yield root

    def _run_gate(self, project_root):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
        from app.cli import combine_v8_generation_reexecution_authorization_gate
        import argparse
        args = argparse.Namespace(
            project_root=str(project_root),
            json=False,
            silent=True,
        )
        return combine_v8_generation_reexecution_authorization_gate(args)

    def _read_artifact_index(self, project_root):
        path = project_root / "output" / "control" / "artifact_index.json"
        with open(path) as f:
            return json.load(f)

    def _read_gate_artifact(self, project_root):
        path = project_root / "output" / "control" / "combine_v2_v8_generation_reexecution_authorization_required.json"
        with open(path) as f:
            return json.load(f)

    def _read_ledger(self, project_root):
        path = project_root / "output" / "control" / "episode_ledger.json"
        with open(path) as f:
            return json.load(f)

    def test_gate_creates_artifact(self, project_root):
        exit_code = self._run_gate(project_root)
        assert exit_code == 0
        gate = self._read_gate_artifact(project_root)
        assert gate.get("gate_type") == "v8_generation_reexecution_authorization_gate"
        assert gate.get("task_id") == "RC-COMBINE-V2-6001-6300"

    def test_state_transition_correct(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("current_state") == "v8_generation_reexecution_authorization_required"
        assert index.get("next_allowed_action") == "v8_generation_reexecution_authorization_required"

    def test_production_accepted_false(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("production_accepted") is False

    def test_assembly_downstream_blocked(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("assembly_allowed") is False
        assert index.get("downstream_allowed") is False

    def test_generation_allowed_now_false(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("generation_allowed_now") is False

    def test_no_new_generation_performed(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("new_generation_performed") is False
        assert index.get("workflow_submitted") is False
        assert index.get("new_comfyui_submit_executed") is False

    def test_no_retry_no_visual_qa_no_assembly(self, project_root):
        self._run_gate(project_root)
        index = self._read_artifact_index(project_root)
        assert index.get("retry_attempted") is False
        assert index.get("visual_qa_executed") is False
        assert index.get("operator_visual_decision_created") is False
        assert index.get("assembly_executed") is False
        assert index.get("downstream_executed") is False

    def test_gate_artifact_fields_correct(self, project_root):
        self._run_gate(project_root)
        gate = self._read_gate_artifact(project_root)
        assert gate.get("generation_allowed_now") is False
        assert gate.get("execute_mode_required_for_real_submit") is True
        assert gate.get("max_generations") == 1
        assert gate.get("second_generation_allowed") is False
        assert gate.get("retry_allowed") is False
        assert gate.get("production_accepted") is False
        assert gate.get("current_state") == "v8_generation_runtime_blocked"
        assert gate.get("reexecution_authorization_state") == "v8_generation_reexecution_authorization_required"

    def test_gate_provenance_correct(self, project_root):
        self._run_gate(project_root)
        gate = self._read_gate_artifact(project_root)
        provenance = gate.get("provenance", {})
        assert provenance.get("previous_layer") == "RC-COMBINE-V2-5701-6000-RECOVERY"
        assert provenance.get("previous_commit") == "478d592"
        assert provenance.get("previous_state") == "v8_generation_runtime_blocked"

    def test_episode_ledger_updated(self, project_root):
        self._run_gate(project_root)
        ledger = self._read_ledger(project_root)
        events = [e for e in ledger if e.get("event_type") == "v8_generation_reexecution_authorization_gate_created"]
        assert len(events) >= 1
        event = events[0]
        assert event.get("task_id") == "RC-COMBINE-V2-6001-6300"
        assert event.get("current_state") == "v8_generation_reexecution_authorization_required"
        assert event.get("new_generation_performed") is False
        assert event.get("production_accepted") is False
        assert event.get("generation_allowed_now") is False

    def test_gate_rejects_invalid_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_prerequisite_artifacts(root / "output" / "control", state="generate_assets")
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
            from app.cli import combine_v8_generation_reexecution_authorization_gate
            import argparse
            args = argparse.Namespace(
                project_root=str(root),
                json=False,
                silent=True,
            )
            exit_code = combine_v8_generation_reexecution_authorization_gate(args)
            assert exit_code == 1


class TestReexecutionAuthorizationGateStateMachine:

    def test_v8_generation_reexecution_authorization_required_is_valid(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.is_valid_state("v8_generation_reexecution_authorization_required")

    def test_v8_generation_reexecution_authorization_required_self_loop(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "v8_generation_reexecution_authorization_required"
        )

    def test_v8_generation_reexecution_authorization_required_to_generation_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "v8_quality_locked_generation_authorization_required"
        )

    def test_v8_generation_reexecution_authorization_required_forbidden_generate(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "generate_assets"
        )
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "real_generate_assets"
        )

    def test_v8_generation_reexecution_authorization_required_forbidden_visual_review(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "operator_visual_review_required"
        )

    def test_v8_generation_reexecution_authorization_required_forbidden_assembly(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "v8_generation_reexecution_authorization_required",
            "assembly_required"
        )

    def test_runtime_blocked_to_reexecution_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_blocked",
            "v8_generation_reexecution_authorization_required"
        )

    def test_runtime_recovery_to_reexecution_authorization(self):
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "v8_generation_runtime_recovery_required",
            "v8_generation_reexecution_authorization_required"
        )
