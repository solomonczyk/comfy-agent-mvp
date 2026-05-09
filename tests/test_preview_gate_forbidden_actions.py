"""Tests for RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001 — Preview Gate Forbidden Actions.

Verifies that the preview authorization gate correctly forbids:
  - preview render execution
  - voice generation
  - assembly
  - downstream operations
  - production acceptance

All forbidden actions must be False in the authorization packet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.orchestrator.state_machine import CombineStateMachine

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = PROJECT_ROOT / "data" / "rc2_multishot1_ep01"
CONTROL_DIR = DATA_ROOT / "output" / "control"


def _load_json(rel_path: str) -> dict | list | None:
    path = CONTROL_DIR / rel_path
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestAuthorizationPacketForbiddenActions:
    """All forbidden actions must be explicitly False."""

    def test_authorization_packet_exists(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet is not None, "preview_render_authorization_packet.json not found"

    def test_forbidden_actions_section_exists(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert "forbidden_actions" in packet, "missing forbidden_actions section"

    def test_new_generation_forbidden(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("new_generation") is False

    def test_retry_forbidden(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("retry") is False

    def test_comfyui_submit_forbidden(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("comfyui_submit") is False

    def test_preview_render_not_executed(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("preview_render_executed") is False

    def test_voice_generation_not_executed(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("voice_generation_executed") is False

    def test_assembly_not_executed(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("assembly_executed") is False

    def test_downstream_not_executed(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("downstream_executed") is False

    def test_production_not_accepted(self):
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("forbidden_actions", {}).get("production_accepted") is False


class TestForbiddenActionsOnArtifactIndex:
    """Artifact index must reflect all forbidden actions as False."""

    def test_artifact_index_exists(self):
        idx = _load_json("artifact_index.json")
        assert idx is not None, "artifact_index.json not found"

    def test_preview_render_not_executed(self):
        idx = _load_json("artifact_index.json")
        assert idx.get("preview_render_executed") is False

    def test_voice_generation_not_executed(self):
        idx = _load_json("artifact_index.json")
        assert idx.get("voice_generation_executed") is False

    def test_assembly_not_executed(self):
        idx = _load_json("artifact_index.json")
        assert idx.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        idx = _load_json("artifact_index.json")
        assert idx.get("downstream_executed") is False

    def test_production_accepted_false(self):
        idx = _load_json("artifact_index.json")
        assert idx.get("production_accepted") is False


class TestForbiddenActionsStateMachine:
    """State machine must forbid dangerous transitions from new states."""

    def setup_method(self):
        self.sm = CombineStateMachine()

    def test_timeline_to_preview_cannot_generate(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "generate_assets"
        ), "should forbid generate_assets from timeline_to_preview"

    def test_timeline_to_preview_cannot_real_generate(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "real_generate_assets"
        ), "should forbid real_generate_assets"

    def test_timeline_to_preview_cannot_visual_qa(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "visual_qa_required"
        ), "should forbid visual_qa_required"

    def test_timeline_to_preview_cannot_assembly(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "assembly_required"
        ), "should forbid assembly_required"

    def test_timeline_to_preview_cannot_completed(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "completed"
        ), "should forbid completed"

    def test_timeline_to_preview_cannot_production_accepted(self):
        assert not self.sm.can_transition(
            "timeline_to_preview_package_required", "production_accepted"
        ), "should forbid production_accepted"

    def test_preview_authorization_cannot_generate(self):
        assert not self.sm.can_transition(
            "preview_render_authorization_required", "generate_assets"
        ), "should forbid generate_assets from preview_render_authorization"

    def test_preview_authorization_cannot_real_generate(self):
        assert not self.sm.can_transition(
            "preview_render_authorization_required", "real_generate_assets"
        ), "should forbid real_generate_assets"

    def test_preview_authorization_cannot_assembly(self):
        assert not self.sm.can_transition(
            "preview_render_authorization_required", "assembly_required"
        ), "should forbid assembly_required"

    def test_preview_authorization_cannot_completed(self):
        assert not self.sm.can_transition(
            "preview_render_authorization_required", "completed"
        ), "should forbid completed"

    def test_preview_authorization_cannot_production_accepted(self):
        assert not self.sm.can_transition(
            "preview_render_authorization_required", "production_accepted"
        ), "should forbid production_accepted"


class TestForbiddenActionsOnContracts:
    """Each contract must enforce its own forbidden actions."""

    def test_voice_contract_generation_forbidden(self):
        voice = _load_json("voice_casting_contract.json")
        assert voice is not None, "voice_casting_contract.json not found"
        gen_allowed = voice.get("full_voiceover_generation_allowed", True)
        assert gen_allowed is False, \
            "full_voiceover_generation_allowed must be False"

    def test_preview_contract_render_forbidden(self):
        preview = _load_json("preview_proof_contract.json")
        assert preview is not None, "preview_proof_contract.json not found"
        assert preview.get("final_render_allowed") is False, \
            "final_render_allowed must be False"

    def test_transition_policy_forbidden_listed(self):
        policy = _load_json("transition_policy.json")
        assert policy is not None, "transition_policy.json not found"
        forbidden = policy.get("forbidden_transitions", [])
        assert len(forbidden) > 0, "forbidden_transitions must not be empty"

    def test_edl_no_operations_applied(self):
        edl = _load_json("edit_decision_list.json") or []
        for op in edl:
            assert op.get("apply_performed") is False, \
                f"operation '{op.get('operation_id')}' has apply_performed=True"


class TestForbiddenActionsOnLedger:
    """Ledger must record that no forbidden actions were taken."""

    def test_ledger_exists(self):
        ledger = _load_json("episode_ledger.json")
        assert ledger is not None, "episode_ledger.json not found"

    def test_last_event_has_preview_not_executed(self):
        ledger = _load_json("episode_ledger.json")
        assert isinstance(ledger, list), "ledger must be a list"
        # Find the preview_render_authorization_required event
        for event in reversed(ledger):
            if event.get("event_type") == "preview_render_authorization_required":
                assert event.get("preview_render_executed") is False
                assert event.get("voice_generation_executed") is False
                assert event.get("assembly_executed") is False
                assert event.get("downstream_executed") is False
                assert event.get("production_accepted") is False
                return
        pytest.fail("preview_render_authorization_required event not found in ledger")

    def test_dry_run_event_no_render(self):
        ledger = _load_json("episode_ledger.json")
        assert isinstance(ledger, list)
        for event in reversed(ledger):
            if event.get("event_type") == "timeline_preview_dry_run_completed":
                assert event.get("real_render_executed") is False
                assert event.get("generation_performed") is False
                assert event.get("apply_performed") is False
                return
        pytest.fail("timeline_preview_dry_run_completed event not found in ledger")

    def test_timeline_to_preview_package_started_event(self):
        ledger = _load_json("episode_ledger.json")
        assert isinstance(ledger, list)
        for event in reversed(ledger):
            if event.get("event_type") == "timeline_to_preview_package_started":
                assert event.get("production_accepted") is False
                assert event.get("approved_asset", ""), "approved_asset must be present"
                return
        pytest.fail("timeline_to_preview_package_started event not found in ledger")


class TestEdgeCases:
    """Edge cases for forbidden actions."""

    def test_voice_no_sample_bypass(self):
        """Voice contract must explicitly require a sample."""
        voice = _load_json("voice_casting_contract.json")
        assert voice.get("sample_required") is True, \
            "sample_required must be True — operator must review voice sample"

    def test_voice_no_operator_review_bypass(self):
        """Voice contract must require operator review."""
        voice = _load_json("voice_casting_contract.json")
        assert voice.get("operator_review_required") is True, \
            "operator_review_required must be True"

    def test_preview_contract_requires_operator_review(self):
        """Preview proof contract must require operator review."""
        preview = _load_json("preview_proof_contract.json")
        assert preview.get("operator_review_required") is True, \
            "operator_review_required must be True in preview contract"

    def test_auth_packet_authorization_gate(self):
        """Authorization packet must act as a gate, not bypass it."""
        packet = _load_json("preview_render_authorization_packet.json")
        assert packet.get("authorization_required") is True
        assert packet.get("authorization_granted") is False
        assert packet.get("operator_decision") is None

    def test_artifact_index_state_is_gate(self):
        """State must be preview_render_authorization_required, blocking render."""
        idx = _load_json("artifact_index.json")
        assert idx.get("current_state") == "preview_render_authorization_required", \
            "state must require authorization before render"


class TestStateMachineTransitions:
    """Test that the state machine allows the expected transitions."""

    def setup_method(self):
        self.sm = CombineStateMachine()

    def test_valid_state_transition_allowed(self):
        assert self.sm.can_transition(
            "visual_asset_operator_accepted", "timeline_to_preview_package_required"
        ), "visual_asset_operator_accepted -> timeline_to_preview_package_required should be allowed"

    def test_new_state_to_preview_authorization_allowed(self):
        assert self.sm.can_transition(
            "timeline_to_preview_package_required", "preview_render_authorization_required"
        ), "timeline_to_preview_package_required -> preview_render_authorization_required should be allowed"

    def test_new_state_to_blocked_allowed(self):
        assert self.sm.can_transition(
            "timeline_to_preview_package_required", "blocked_manual_review"
        ), "timeline_to_preview_package_required -> blocked_manual_review should be allowed"

    def test_preview_authorization_to_blocked_allowed(self):
        assert self.sm.can_transition(
            "preview_render_authorization_required", "blocked_manual_review"
        ), "preview_render_authorization_required -> blocked_manual_review should be allowed"

    def test_states_are_valid(self):
        assert self.sm.is_valid_state("timeline_to_preview_package_required"), \
            "timeline_to_preview_package_required must be a valid state"
        assert self.sm.is_valid_state("preview_render_authorization_required"), \
            "preview_render_authorization_required must be a valid state"
