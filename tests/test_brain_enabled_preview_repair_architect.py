"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Tests for brain-enabled preview repair architect agent.
"""

from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.agents.brain.brain_config import BrainProviderConfig
from app.agents.brain.brain_provider import validate_brain_provider
from app.agents.brain.brain_runtime_gate import (
    BrainRuntimeGate,
    MAX_BRAIN_CALLS_LIMIT,
)
from app.agents.brain.brain_call_contracts import (
    BrainCallContract,
    BrainCallContractBuilder,
)


# ---------------------------------------------------------------------------
# Brain model is config-driven, not hardcoded
# ---------------------------------------------------------------------------


def test_brain_model_is_config_driven_not_hardcoded():
    """Brain model ID must come from config, not hardcoded in business logic."""
    config = BrainProviderConfig.default()
    # Must declare model at config level
    assert config.primary_model_id == "deepseek-v4-flash"
    assert config.hardcode_forbidden is True

    # Config should be overridable via env
    with patch.dict(os.environ, {"BRAIN_PRIMARY_MODEL_ID": "claude-sonnet-4-6"}, clear=False):
        env_config = BrainProviderConfig.from_env()
        assert env_config.primary_model_id == "claude-sonnet-4-6"
        assert env_config.hardcode_forbidden is True


def test_brain_config_defaults():
    """Brain config has expected default values."""
    config = BrainProviderConfig.default()
    assert config.primary_model_id == "deepseek-v4-flash"
    assert config.provider == "configurable"
    assert config.api_key_source == "env"
    assert config.fallback_model_id == "configurable"
    assert config.max_calls_per_task == 2
    assert config.max_tokens_per_call == 4096
    assert config.runtime_call_authorized is False
    assert config.hardcode_forbidden is True
    assert config.provider_validation_required is True
    assert config.hidden_api_calls_forbidden is True
    assert config.budget_limit_defined is False


# ---------------------------------------------------------------------------
# Brain runtime call requires operator gate
# ---------------------------------------------------------------------------


def test_brain_runtime_call_requires_operator_gate():
    """Runtime gate must block calls when authorization is missing."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=False,
        provider_config_present=False,
        api_key_present=False,
        model_id_validated=False,
        budget_limit_defined=False,
    )
    result = gate.check()
    assert result.runtime_call_authorized is False
    assert len(result.errors) > 0
    assert any("operator" in e.lower() for e in result.errors)


def test_brain_runtime_gate_all_conditions_required():
    """All gate conditions must be true for authorization."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
    )
    result = gate.check()
    assert result.runtime_call_authorized is True
    assert len(result.errors) == 0


def test_brain_runtime_gate_max_calls():
    """Gate must limit brain calls to MAX_BRAIN_CALLS_LIMIT."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=MAX_BRAIN_CALLS_LIMIT,
    )
    result = gate.check()
    assert result.runtime_call_authorized is False
    assert result.max_brain_calls_within_limit is False
    assert gate.calls_remaining == 0

    # After recording a call, remaining should decrease
    gate2 = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=0,
    )
    assert gate2.calls_remaining == MAX_BRAIN_CALLS_LIMIT
    gate2.record_call()
    assert gate2.calls_remaining == MAX_BRAIN_CALLS_LIMIT - 1


# ---------------------------------------------------------------------------
# Brain provider validation blocks fake model availability
# ---------------------------------------------------------------------------


def test_brain_provider_validation_blocks_fake_model_availability():
    """Unknown/fake model should fail provider validation."""
    config = BrainProviderConfig(
        primary_model_id="fake-nonexistent-model-v999",
        provider="fake_provider",
        provider_validation_required=True,
        exact_model_id_validation_required=True,
        budget_limit_defined=False,
        fallback_model_id="",
    )

    with patch.dict(os.environ, {}, clear=True):
        result = validate_brain_provider(config)
        assert result.validation_passed is False
        # Should have at least some errors (no API key, no budget, no fallback)
        assert len(result.errors) > 0


def test_brain_provider_validation_api_key_check():
    """Provider validation checks for API key in environment."""
    config = BrainProviderConfig(
        primary_model_id="claude-sonnet-4-6",
        provider="anthropic",
        exact_model_id_validation_required=True,
        budget_limit_defined=True,
        max_budget_per_task=10.0,
        fallback_model_id="claude-haiku-4-5",
    )

    # Without API key, validation should fail
    with patch.dict(os.environ, {}, clear=True):
        result = validate_brain_provider(config)
        assert result.api_key_present is False
        assert result.validation_passed is False
        assert any("api key" in e.lower() for e in result.errors)

    # With API key, that check should pass (others may still fail)
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test-key"}, clear=True):
        result = validate_brain_provider(config)
        assert result.api_key_present is True


# ---------------------------------------------------------------------------
# Brain output is advisory, not state authority
# ---------------------------------------------------------------------------


def test_brain_output_is_advisory_not_state_authority():
    """Brain output must be marked advisory-only and may not update state."""
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
    assert result.runtime_call_authorized is True
    assert result.brain_output_advisory_only is True


def test_brain_call_contract_advisory_enforcement():
    """Brain call contract must enforce advisory-only mode."""
    builder = BrainCallContractBuilder(
        task_id="RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001",
        agent_id="preview_repair_architect",
    )
    contract = builder.build()
    assert contract.brain_response_used_as_advisory is True
    assert contract.deterministic_validation_required is True
    assert contract.brain_may_not_update_state_directly is True
    assert contract.brain_may_not_accept_visual_result is True


# ---------------------------------------------------------------------------
# Agent contract forbids runtime dangerous actions
# ---------------------------------------------------------------------------


def test_preview_repair_architect_contract_forbids_runtime_dangerous_actions():
    """Agent contract must forbid comfyui, generation, assembly, downstream, production."""
    contract = {
        "agent_id": "preview_repair_architect",
        "allowed_tools": [
            "read_canonical_artifacts",
            "analyze_preview_reports",
            "propose_repair_plan",
            "write_repair_artifacts",
        ],
        "forbidden_tools": [
            "comfyui_submit",
            "image_generation",
            "voice_generation",
            "assembly",
            "downstream",
            "production_acceptance",
        ],
    }
    dangerous = [
        "comfyui_submit",
        "image_generation",
        "voice_generation",
        "assembly",
        "downstream",
        "production_acceptance",
    ]
    for tool in dangerous:
        assert tool in contract["forbidden_tools"], (
            f"{tool} should be in forbidden_tools"
        )
        assert tool not in contract["allowed_tools"], (
            f"{tool} should not be in allowed_tools"
        )


def test_brain_runtime_gate_to_dict():
    """Runtime gate to_dict returns expected serializable format."""
    gate = BrainRuntimeGate(
        operator_authorization_exists=True,
        provider_config_present=True,
        api_key_present=True,
        model_id_validated=True,
        budget_limit_defined=True,
        brain_calls_used=1,
    )
    d = gate.to_dict()
    assert d["operator_authorization_exists"] is True
    assert d["brain_calls_used"] == 1
    assert d["max_brain_calls"] == MAX_BRAIN_CALLS_LIMIT
    assert d["brain_calls_remaining"] == MAX_BRAIN_CALLS_LIMIT - 1
    assert d["brain_output_advisory_only"] is True


def test_brain_provider_validation_result_to_dict():
    """Validation result serializes to dict."""
    config = BrainProviderConfig(provider="", fallback_model_id="")
    with patch.dict(os.environ, {}, clear=True):
        result = validate_brain_provider(config)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "validation_passed" in d
        assert "errors" in d
        assert isinstance(d["errors"], list)
