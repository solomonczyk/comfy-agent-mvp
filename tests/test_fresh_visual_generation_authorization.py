"""Tests for RC-COMBINE-V2-FRESH-VISUAL-GENERATION-AUTHORIZATION-001."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
GATE_DIR = CONTROL_DIR / "fresh_visual_generation_gate"
GATE_PACKAGE = GATE_DIR / "fresh_visual_generation_gate_package.json"
ARTIFACT_INDEX = CONTROL_DIR / "artifact_index.json"
EPISODE_LEDGER = Path("F:/ComfyUI/comfy-agent-mvp/episode_ledger.json")


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _args(decision: str, operator_id: str, root: str, json_out: bool = True) -> MagicMock:
    a = MagicMock()
    a.project_root = root
    a.decision = decision
    a.operator_id = operator_id
    a.json = json_out
    return a


def _setup_gate(tmp_path: Path) -> None:
    gate_dir = tmp_path / "output" / "control" / "fresh_visual_generation_gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    pkg = {
        "gate_id": "fresh_visual_generation_gate_package_001",
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-GATE-001",
        "gate_status": "prepared_waiting_for_operator_authorization",
        "generation_authorized": False,
        "operator_authorization_required": True,
        "max_generations": 1,
        "blind_retry_allowed": False,
        "stop_after_generation": True,
        "visual_qa_allowed_after_generation": False,
        "assembly_allowed_after_generation": False,
        "downstream_allowed_after_generation": False,
        "production_acceptance_allowed_after_generation": False,
        "state_transition": {
            "previous_state": "fresh_visual_generation_plan_updated",
            "current_state": "fresh_visual_generation_gate_prepared",
            "next_allowed_action": "operator_generation_authorization_required",
        },
    }
    with open(gate_dir / "fresh_visual_generation_gate_package.json", "w") as f:
        json.dump(pkg, f, indent=2)


# ---------------------------------------------------------------------------
# Pre-condition: gate package state
# ---------------------------------------------------------------------------

class TestGatePackagePreConditions:
    def test_gate_package_exists(self):
        assert GATE_PACKAGE.exists()

    def test_generation_authorized_false(self):
        assert _load(GATE_PACKAGE)["generation_authorized"] is False

    def test_max_generations_one(self):
        assert _load(GATE_PACKAGE)["max_generations"] == 1

    def test_next_allowed_action(self):
        pkg = _load(GATE_PACKAGE)
        assert pkg["state_transition"]["next_allowed_action"] == "operator_generation_authorization_required"

    def test_operator_authorization_required(self):
        assert _load(GATE_PACKAGE)["operator_authorization_required"] is True

    def test_no_visual_qa_allowed(self):
        assert _load(GATE_PACKAGE)["visual_qa_allowed_after_generation"] is False

    def test_no_assembly_allowed(self):
        assert _load(GATE_PACKAGE)["assembly_allowed_after_generation"] is False

    def test_no_downstream_allowed(self):
        assert _load(GATE_PACKAGE)["downstream_allowed_after_generation"] is False


# ---------------------------------------------------------------------------
# Post-condition: authorization artifacts on real filesystem
# ---------------------------------------------------------------------------

class TestAuthorizationArtifacts:
    def test_operator_decision_exists(self):
        assert (CONTROL_DIR / "fresh_visual_generation_operator_decision.json").exists()

    def test_operator_decision_approved(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["operator_decision"] == "approved"

    def test_decision_source_human_operator(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["decision_source"] == "human_operator"

    def test_decision_scope_exactly_one(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["decision_scope"] == "exactly_one_future_fresh_visual_generation"
        assert doc["max_generations"] == 1

    def test_decision_generation_not_executed(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["generation_execution_in_this_task"] is False

    def test_decision_no_visual_qa_assembly_downstream(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["visual_qa_allowed"] is False
        assert doc["assembly_allowed"] is False
        assert doc["downstream_allowed"] is False

    def test_decision_production_accepted_false(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_operator_decision.json")
        assert doc["production_accepted"] is False

    def test_authorization_record_exists(self):
        assert (CONTROL_DIR / "fresh_visual_generation_authorization_record.json").exists()

    def test_authorization_record_authorized(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_record.json")
        assert doc["authorization_status"] == "authorized"
        assert doc["generation_authorized"] is True
        assert doc["max_generations"] == 1

    def test_authorization_record_no_generation(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_record.json")
        assert doc["generation_performed"] is False
        assert doc["comfyui_submit_executed"] is False
        assert doc["prompt_id_created"] is False
        assert doc["production_accepted"] is False

    def test_authorization_record_next_action(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_record.json")
        assert doc["next_allowed_action"] == "fresh_visual_generation_execute_required"

    def test_authorization_validation_exists_and_passed(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_validation.json")
        assert doc["validation_status"] == "passed"
        assert doc["errors"] == []

    def test_authorization_result_exists_and_authorized(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_result.json")
        assert doc["result"] == "authorized"
        assert doc["generation_authorized"] is True

    def test_authorization_proof_exists(self):
        assert (CONTROL_DIR / "fresh_visual_generation_authorization_proof.json").exists()

    def test_authorization_proof_no_forbidden_actions(self):
        doc = _load(CONTROL_DIR / "fresh_visual_generation_authorization_proof.json")
        assert doc["feature_completed"] is True
        assert doc["generation_performed"] is False
        assert doc["comfyui_submit_executed"] is False
        assert doc["prompt_id_created"] is False
        assert doc["retry_attempted"] is False
        assert doc["second_generation_attempted"] is False
        assert doc["visual_qa_executed"] is False
        assert doc["visual_acceptance_executed"] is False
        assert doc["assembly_executed"] is False
        assert doc["downstream_executed"] is False
        assert doc["production_accepted"] is False
        assert doc["forbidden_actions_not_executed"] is True


# ---------------------------------------------------------------------------
# State / index / ledger
# ---------------------------------------------------------------------------

class TestStateAndLedger:
    def test_artifact_index_state(self):
        doc = _load(ARTIFACT_INDEX)
        assert doc["current_state"] == "fresh_visual_generation_authorized"
        assert doc["next_allowed_action"] == "fresh_visual_generation_execute_required"

    def test_artifact_index_authorization_registered(self):
        doc = _load(ARTIFACT_INDEX)
        assert doc.get("fresh_visual_generation_authorization_created") is True
        assert "fresh_visual_generation_operator_decision" in doc
        assert "fresh_visual_generation_authorization_record" in doc
        assert "fresh_visual_generation_authorization_result" in doc
        assert "fresh_visual_generation_authorization_proof" in doc

    def test_episode_ledger_state(self):
        doc = _load(EPISODE_LEDGER)
        assert doc["current_state"] == "fresh_visual_generation_authorized"
        assert doc["next_allowed_action"] == "fresh_visual_generation_execute_required"

    def test_episode_ledger_authorization_event(self):
        doc = _load(EPISODE_LEDGER)
        events = doc.get("events", [])
        ev = next((e for e in events if e.get("event") == "fresh_visual_generation_authorization_recorded"), None)
        assert ev is not None
        assert ev["operator_decision"] == "approved"
        assert ev["decision_source"] == "human_operator"
        assert ev["generation_authorized"] is True
        assert ev["max_generations"] == 1
        assert ev["generation_performed"] is False
        assert ev["comfyui_submit_executed"] is False
        assert ev["production_accepted"] is False


# ---------------------------------------------------------------------------
# CLI unit tests — approval branch
# ---------------------------------------------------------------------------

class TestCLIApproval:
    def test_approved_returns_zero(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        assert rc == 0

    def test_approved_creates_record(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_record.json")
        assert doc["authorization_status"] == "authorized"
        assert doc["generation_authorized"] is True
        assert doc["max_generations"] == 1

    def test_approved_next_action(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["next_allowed_action"] == "fresh_visual_generation_execute_required"
        assert doc["current_state"] == "fresh_visual_generation_authorized"

    def test_approved_generation_not_performed(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["generation_performed"] is False
        assert doc["comfyui_submit_executed"] is False
        assert doc["prompt_id_created"] is False

    def test_approved_production_accepted_false(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["production_accepted"] is False


# ---------------------------------------------------------------------------
# CLI unit tests — rejection branch
# ---------------------------------------------------------------------------

class TestCLIRejection:
    def test_rejected_returns_zero(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("rejected", "andrey", str(tmp_path)))
        assert rc == 0

    def test_rejected_generation_unauthorized(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("rejected", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["result"] == "rejected"
        assert doc["generation_authorized"] is False
        assert doc["max_generations"] == 0

    def test_rejected_next_action(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("rejected", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["next_allowed_action"] == "fresh_visual_generation_gate_revision_required"
        assert doc["current_state"] == "fresh_visual_generation_rejected"

    def test_rejected_creates_rejection_artifact(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("rejected", "andrey", str(tmp_path)))
        assert (tmp_path / "output" / "control" / "fresh_visual_generation_operator_rejection.json").exists()
        assert (tmp_path / "output" / "control" / "fresh_visual_generation_gate_revision_blocker.json").exists()

    def test_rejected_production_accepted_false(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("rejected", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["production_accepted"] is False


# ---------------------------------------------------------------------------
# CLI unit tests — blocker / invalid decision cases
# ---------------------------------------------------------------------------

class TestCLIBlockers:
    def test_missing_operator_id_returns_one(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("approved", "", str(tmp_path)))
        assert rc == 1

    def test_missing_operator_id_creates_blocker(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "", str(tmp_path)))
        blocker = _load(tmp_path / "output" / "control" / "fresh_visual_generation_operator_authorization_blocker.json")
        assert blocker["blocker_type"] == "missing_operator_id"
        assert blocker["generation_authorized"] is False
        assert blocker["next_allowed_action"] == "operator_generation_authorization_required"

    def test_missing_operator_id_creates_fake_report(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "", str(tmp_path)))
        assert (tmp_path / "output" / "control" / "fake_or_missing_operator_decision_report.json").exists()

    def test_ambiguous_decision_returns_one(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("maybe", "andrey", str(tmp_path)))
        assert rc == 1

    def test_ambiguous_decision_blocks_generation(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("maybe", "andrey", str(tmp_path)))
        blocker = _load(tmp_path / "output" / "control" / "fresh_visual_generation_operator_authorization_blocker.json")
        assert blocker["generation_authorized"] is False
        assert blocker["next_allowed_action"] == "operator_generation_authorization_required"

    def test_agent_generated_decision_blocked(self, tmp_path, capsys):
        """Any non-human value (e.g. 'auto_approved') must be blocked."""
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("auto_approved", "agent_bot", str(tmp_path)))
        assert rc == 1

    def test_empty_decision_blocked(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("", "andrey", str(tmp_path)))
        assert rc == 1

    def test_missing_gate_package_returns_one(self, tmp_path, capsys):
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        assert rc == 1

    def test_max_generations_gt_one_blocked(self, tmp_path, capsys):
        """Gate package with max_generations>1 must be blocked."""
        gate_dir = tmp_path / "output" / "control" / "fresh_visual_generation_gate"
        gate_dir.mkdir(parents=True, exist_ok=True)
        pkg = {
            "gate_id": "x",
            "task_id": "x",
            "gate_status": "prepared_waiting_for_operator_authorization",
            "generation_authorized": False,
            "operator_authorization_required": True,
            "max_generations": 3,
            "state_transition": {
                "next_allowed_action": "operator_generation_authorization_required"
            },
        }
        with open(gate_dir / "fresh_visual_generation_gate_package.json", "w") as f:
            json.dump(pkg, f)
        from app.cli import combine_record_fresh_visual_generation_authorization
        rc = combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        assert rc == 1

    def test_comfyui_submit_not_executed(self, tmp_path, capsys):
        """Approval must never set comfyui_submit_executed=True."""
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["comfyui_submit_executed"] is False

    def test_production_accepted_always_false(self, tmp_path, capsys):
        _setup_gate(tmp_path)
        from app.cli import combine_record_fresh_visual_generation_authorization
        combine_record_fresh_visual_generation_authorization(_args("approved", "andrey", str(tmp_path)))
        doc = _load(tmp_path / "output" / "control" / "fresh_visual_generation_authorization_result.json")
        assert doc["production_accepted"] is False
