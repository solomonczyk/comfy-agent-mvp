"""
RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001
Tests for brain runtime gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.brain.brain_runtime_gate import (
    BrainRuntimeGate,
    BrainRuntimeGateResult,
    MAX_BRAIN_CALLS_LIMIT,
)


# ---------------------------------------------------------------------------
# Runtime call blocked without explicit authorization
# ---------------------------------------------------------------------------


def test_runtime_call_blocked_without_explicit_authorization():
    """Runtime gate must block brain calls when operator authorization is missing."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=False,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.runtime_call_authorized is False
    assert result.external_api_call_allowed is False
    assert any("operator" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Hidden API calls forbidden
# ---------------------------------------------------------------------------


def test_hidden_api_call_forbidden():
    """Hidden API calls must be explicitly forbidden by the gate."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=False,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.hidden_api_calls_forbidden is True

    # Even when authorized, hidden calls remain forbidden
    gate2 = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result2 = gate2.check()
    assert result2.hidden_api_calls_forbidden is True


# ---------------------------------------------------------------------------
# Brain output cannot update state directly
# ---------------------------------------------------------------------------


def test_brain_output_cannot_update_state_directly():
    """Brain output must not be allowed to update state directly."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.brain_output_may_update_state_directly is False


# ---------------------------------------------------------------------------
# Brain output cannot accept visual or audio
# ---------------------------------------------------------------------------


def test_brain_output_cannot_accept_visual_or_audio():
    """Brain output must not be allowed to accept visual or audio results."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.brain_output_may_accept_visual is False
    assert result.brain_output_may_accept_audio is False


# ---------------------------------------------------------------------------
# Brain output cannot trigger generation, preview, voice, assembly
# ---------------------------------------------------------------------------


def test_brain_output_cannot_trigger_generation_preview_voice_assembly():
    """Brain output must not trigger generation, preview, voice, or assembly."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.brain_output_may_run_generation is False

    # Verify gate.to_dict also reports False
    d = gate.to_dict()
    assert d["brain_output_may_update_state_directly"] is False
    assert d["brain_output_may_accept_visual"] is False
    assert d["brain_output_may_accept_audio"] is False
    assert d["brain_output_may_run_generation"] is False
    assert d["hidden_api_calls_forbidden"] is True


# ---------------------------------------------------------------------------
# Gate result structure
# ---------------------------------------------------------------------------


def test_brain_runtime_gate_result_fields():
    """Gate result must contain all required fields."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=False,
        provider_config_present=False,
        api_key_present=False,
        model_id_validated=False,
        budget_limit_defined=False,
        brain_calls_used=0,
    )
    result = gate.check()
    d = result.to_dict()
    required_keys = [
        "runtime_call_authorized",
        "external_api_call_allowed",
        "operator_authorization_exists",
        "provider_config_present",
        "api_key_present",
        "model_id_validated",
        "budget_limit_defined",
        "max_brain_calls_within_limit",
        "max_brain_calls",
        "brain_output_advisory_only",
        "brain_output_may_update_state_directly",
        "brain_output_may_accept_visual",
        "brain_output_may_accept_audio",
        "brain_output_may_run_generation",
        "hidden_api_calls_forbidden",
        "errors",
    ]
    for key in required_keys:
        assert key in d, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Gate validation report artifact
# ---------------------------------------------------------------------------


def test_brain_runtime_gate_validation_report_exists():
    """brain_runtime_gate_validation_report.json must exist with correct shape."""
    path = Path("data/rc2_multishot1_ep01/output/control/brain_runtime_gate_validation_report.json")
    assert path.exists()

    with open(path, "r") as f:
        data = json.load(f)

    assert data["runtime_call_authorized"] is False
    assert data["external_api_call_allowed"] is False
    assert data["hidden_api_calls_forbidden"] is True
    assert data["brain_output_may_update_state_directly"] is False
    assert data["brain_output_may_accept_visual"] is False
    assert data["brain_output_may_accept_audio"] is False
    assert data["brain_output_may_run_generation"] is False


# ---------------------------------------------------------------------------
# Max brain calls enforcement
# ---------------------------------------------------------------------------


def test_max_brain_calls_enforced():
    """Gate must enforce max brain calls limit."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=MAX_BRAIN_CALLS_LIMIT,
        brain_output_advisory_only=True,
    )
    result = gate.check()
    assert result.runtime_call_authorized is False
    assert result.max_brain_calls_within_limit is False


# ---------------------------------------------------------------------------
# Gate to_dict serializability
# ---------------------------------------------------------------------------


def test_brain_runtime_gate_to_dict():
    """Gate to_dict must return expected serializable format."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=1,
        brain_output_advisory_only=True,
    )
    d = gate.to_dict()
    assert d["operator_authorization_exists"] is True
    assert d["brain_calls_used"] == 1
    assert d["max_brain_calls"] == MAX_BRAIN_CALLS_LIMIT
    assert d["brain_calls_remaining"] == MAX_BRAIN_CALLS_LIMIT - 1
    assert d["brain_output_advisory_only"] is True
    assert d["hidden_api_calls_forbidden"] is True
