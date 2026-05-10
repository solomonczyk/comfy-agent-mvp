"""
RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001
Tests for brain config security.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.agents.brain.brain_config import BrainProviderConfig
from app.agents.brain.brain_provider import validate_brain_provider, ENV_KEY_NAME
from app.agents.brain.brain_runtime_gate import BrainRuntimeGate
from app.agents.brain.brain_call_contracts import (
    BrainCallContract,
    BrainCallContractBuilder,
)


# ---------------------------------------------------------------------------
# Config security — no hardcode
# ---------------------------------------------------------------------------


def test_brain_config_no_hardcode():
    """Brain config must declare hardcode forbidden."""
    config = BrainProviderConfig.default()
    assert config.hardcode_forbidden is True


def test_runtime_call_authorized_by_default_is_false():
    """Runtime calls must not be authorized by default."""
    config = BrainProviderConfig.default()
    assert config.runtime_call_authorized_by_default is False


def test_api_key_source_is_env_not_hardcode():
    """API key source must reference env, not contain a hardcoded key."""
    config = BrainProviderConfig.default()
    assert config.api_key_source == "env:DEEPSEEK_V4_FLASH_API_KEY"
    assert "sk-" not in config.api_key_source


# ---------------------------------------------------------------------------
# Provider config present
# ---------------------------------------------------------------------------


def test_provider_config_present():
    """Provider must be set to a real value, not empty or 'configurable'."""
    config = BrainProviderConfig.default()
    assert config.provider == "deepseek"
    assert config.provider not in ("", "configurable", None)


# ---------------------------------------------------------------------------
# Hidden API calls forbidden
# ---------------------------------------------------------------------------


def test_hidden_api_calls_forbidden_in_config():
    """Config must explicitly forbid hidden API calls."""
    config = BrainProviderConfig.default()
    assert config.hidden_api_calls_forbidden is True


# ---------------------------------------------------------------------------
# Brain call contract security
# ---------------------------------------------------------------------------


def test_brain_call_contract_advisory_enforcement():
    """Brain call contract must enforce advisory-only mode."""
    builder = BrainCallContractBuilder(
        task_id="RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001",
        agent_id="preview_repair_architect",
    )
    contract = builder.build()
    assert contract.brain_response_used_as_advisory is True
    assert contract.deterministic_validation_required is True
    assert contract.brain_may_not_update_state_directly is True
    assert contract.brain_may_not_accept_visual_result is True
    assert contract.brain_may_not_accept_audio_result is True
    assert contract.brain_may_not_trigger_generation is True
    assert contract.brain_may_not_trigger_preview_render is True
    assert contract.brain_may_not_trigger_voice_generation is True
    assert contract.brain_may_not_trigger_assembly is True
    assert contract.brain_may_not_trigger_downstream is True


# ---------------------------------------------------------------------------
# Provider validation does not execute runtime calls
# ---------------------------------------------------------------------------


def test_provider_validation_does_not_execute_runtime_call():
    """validate_brain_provider must never execute a runtime API call."""
    config = BrainProviderConfig.default()
    result = validate_brain_provider(config)
    assert result.runtime_call_executed is False
    assert result.availability_validated_by_api_call is False


# ---------------------------------------------------------------------------
# Config from env preserves security invariants
# ---------------------------------------------------------------------------


def test_from_env_preserves_security_invariants():
    """Loading config from env must keep security defaults."""
    with patch.dict(os.environ, {"BRAIN_PROVIDER": "anthropic"}, clear=False):
        config = BrainProviderConfig.from_env()
        assert config.hardcode_forbidden is True
        assert config.hidden_api_calls_forbidden is True
        assert config.runtime_call_authorized_by_default is False
        assert config.provider_base_url_configurable is True
