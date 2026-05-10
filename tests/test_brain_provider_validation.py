"""
RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001
Tests for brain provider validation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.agents.brain.brain_config import BrainProviderConfig
from app.agents.brain.brain_provider import (
    validate_brain_provider,
    ENV_KEY_NAME,
    _detect_api_key,
    BrainProviderValidationResult,
)


# ---------------------------------------------------------------------------
# API key detection
# ---------------------------------------------------------------------------


def test_deepseek_api_key_detected_from_env_without_logging_value():
    """API key must be detectable from env without ever logging its value."""
    # The _detect_api_key function must return bool, never the key value.
    result = _detect_api_key(ENV_KEY_NAME)
    assert isinstance(result, bool)
    # The validation result must not contain the key value.
    config = BrainProviderConfig.default()
    validation = validate_brain_provider(config)
    assert validation.api_key_logged is False
    assert validation.api_key_stored_in_artifact is False
    d = validation.to_dict()
    # Ensure no API key value (sk-...) leaks into the serialized dict
    dict_str = str(d)
    assert "sk-" not in dict_str, "API key value leaked in validation result dict"


# ---------------------------------------------------------------------------
# Model ID config-driven
# ---------------------------------------------------------------------------


def test_brain_model_id_is_config_driven():
    """Brain model ID must be configurable, not hardcoded in business logic."""
    config = BrainProviderConfig.default()
    assert config.primary_model_id == "deepseek-v4-flash"
    assert config.hardcode_forbidden is True

    # Overridable via env
    with patch.dict(os.environ, {"BRAIN_PRIMARY_MODEL_ID": "claude-sonnet-4-6"}, clear=False):
        env_config = BrainProviderConfig.from_env()
        assert env_config.primary_model_id == "claude-sonnet-4-6"
        assert env_config.hardcode_forbidden is True


def test_deepseek_v4_flash_is_primary_model_id():
    """Default primary model ID must be deepseek-v4-flash."""
    config = BrainProviderConfig.default()
    assert config.primary_model_id == "deepseek-v4-flash"


# ---------------------------------------------------------------------------
# Provider base URL configurability
# ---------------------------------------------------------------------------


def test_provider_base_url_is_configurable():
    """Provider base URL must be flagged as configurable."""
    config = BrainProviderConfig.default()
    assert config.provider_base_url_configurable is True


# ---------------------------------------------------------------------------
# Fallback policy
# ---------------------------------------------------------------------------


def test_fallback_policy_required():
    """Fallback model policy must be present in config."""
    config = BrainProviderConfig.default()
    assert config.fallback_model_required is True

    validation = validate_brain_provider(config)
    assert validation.fallback_policy_present is True


# ---------------------------------------------------------------------------
# Provider validation report behavior
# ---------------------------------------------------------------------------


def test_provider_validation_report_masks_secret():
    """Provider validation report must never contain the API key value."""
    config = BrainProviderConfig.default()
    validation = validate_brain_provider(config)
    d = validation.to_dict()
    # Ensure no accidental key leakage in dict
    for key, value in d.items():
        if isinstance(value, str) and value.startswith("sk-"):
            pytest.fail(f"API key value leaked in to_dict under key {key}")
    assert d["api_key_logged"] is False
    assert d["api_key_stored_in_artifact"] is False


# ---------------------------------------------------------------------------
# Validation result structure
# ---------------------------------------------------------------------------


def test_provider_validation_result_fields():
    """Validation result must contain all required fields."""
    config = BrainProviderConfig.default()
    result = validate_brain_provider(config)
    d = result.to_dict()
    required_keys = [
        "provider",
        "primary_model_id",
        "env_key_name",
        "api_key_present",
        "api_key_logged",
        "api_key_stored_in_artifact",
        "model_id_config_driven",
        "provider_config_present",
        "fallback_policy_present",
        "runtime_call_executed",
        "availability_validated_by_api_call",
        "validation_status",
        "errors",
    ]
    for key in required_keys:
        assert key in d, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Smoke test authorization request artifact
# ---------------------------------------------------------------------------


def test_smoke_test_authorization_request_created_but_not_executed():
    """Smoke test authorization request artifact must exist and not be executed."""
    control_dir = Path("data/rc2_multishot1_ep01/output/control")
    path = control_dir / "brain_runtime_smoke_test_authorization_request.json"
    assert path.exists(), "brain_runtime_smoke_test_authorization_request.json not found"

    with open(path, "r") as f:
        data = json.load(f)

    assert data["authorization_type"] == "brain_runtime_smoke_test"
    assert data["operator_authorization_required"] is True
    assert data["authorized_now"] is False
    assert data["max_brain_calls_after_authorization"] == 1
    assert data["brain_output_is_advisory_only"] is True
    assert data["state_update_allowed"] is False
    assert data["generation_allowed"] is False
    assert data["preview_render_allowed"] is False
    assert data["voice_generation_allowed"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False
    assert data["production_accepted_allowed"] is False


# ---------------------------------------------------------------------------
# Artifact index and ledger updated
# ---------------------------------------------------------------------------


def test_artifact_index_and_ledger_updated():
    """artifact_index.json and episode_ledger.json must reference brain validation."""
    artifact_index_path = Path("data/rc2_multishot1_ep01/output/control/artifact_index.json")
    with open(artifact_index_path, "r") as f:
        index = json.load(f)

    assert index.get("brain_provider_config_validated") is True
    assert index.get("runtime_smoke_test_pending") is True
    assert "brain_provider_validation_report" in index
    assert "brain_runtime_gate_validation_report" in index

    episode_ledger_path = Path("episode_ledger.json")
    with open(episode_ledger_path, "r") as f:
        ledger = json.load(f)

    assert ledger.get("brain_provider_config_validated") is True
    assert ledger.get("runtime_smoke_test_pending") is True
    assert any(
        e.get("task_id") == "RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001"
        for e in ledger.get("events", [])
    )
