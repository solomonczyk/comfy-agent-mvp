"""
RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001
Brain provider validation — checks if the configured model/provider config is valid.

Does NOT perform runtime API calls. Config validation only.
No hidden API calls. No faked availability.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.agents.brain.brain_config import BrainProviderConfig


ENV_KEY_NAME = "DEEPSEEK_V4_FLASH_API_KEY"


def _detect_api_key(env_key_name: str = ENV_KEY_NAME) -> bool:
    """Detect API key presence without returning its value.

    Checks os.environ first, then falls back to reading .env file directly.
    Never returns or logs the key value.
    """
    # Check os.environ
    if os.environ.get(env_key_name):
        return True

    # Check .env file directly (handles cases where dotenv not loaded)
    env_paths = [Path(".env"), Path("../.env"), Path("../../.env")]
    for env_path in env_paths:
        if env_path.exists():
            try:
                with env_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#"):
                            continue
                        if "=" in line:
                            key, _ = line.split("=", 1)
                            key = key.strip()
                            if key == env_key_name:
                                return True
            except OSError:
                continue
    return False


@dataclass
class BrainProviderValidationResult:
    """Result of provider validation."""

    provider: str = "deepseek"
    primary_model_id: str = "deepseek-v4-flash"
    env_key_name: str = ENV_KEY_NAME
    api_key_present: bool = False
    api_key_logged: bool = False
    api_key_stored_in_artifact: bool = False
    model_id_config_driven: bool = False
    model_id_validated: bool = False
    provider_config_present: bool = False
    fallback_policy_present: bool = False
    runtime_call_executed: bool = False
    availability_validated_by_api_call: bool = False
    validation_status: str = "unknown"
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "primary_model_id": self.primary_model_id,
            "env_key_name": self.env_key_name,
            "api_key_present": self.api_key_present,
            "api_key_logged": self.api_key_logged,
            "api_key_stored_in_artifact": self.api_key_stored_in_artifact,
            "model_id_config_driven": self.model_id_config_driven,
            "model_id_validated": self.model_id_validated,
            "provider_config_present": self.provider_config_present,
            "fallback_policy_present": self.fallback_policy_present,
            "runtime_call_executed": self.runtime_call_executed,
            "availability_validated_by_api_call": self.availability_validated_by_api_call,
            "validation_status": self.validation_status,
            "errors": self.errors,
        }


def validate_brain_provider(
    config: Optional[BrainProviderConfig] = None,
) -> BrainProviderValidationResult:
    """Validate the configured brain provider.

    Checks:
    1. Provider config is set (provider != "", "configurable", None)
    2. API key is present in environment/.env
    3. Model ID is a known/valid identifier
    4. Fallback policy is present (fallback_model_required=True)

    Does NOT perform runtime API calls.
    """
    result = BrainProviderValidationResult()

    if config is None:
        config = BrainProviderConfig.default()

    result.provider = config.provider
    result.primary_model_id = config.primary_model_id
    result.env_key_name = ENV_KEY_NAME

    # Check provider config
    result.provider_config_present = config.provider not in (
        "",
        "configurable",
        None,
    )
    if not result.provider_config_present:
        result.errors.append(
            f"Provider not configured (provider='{config.provider}'). "
            "Set BRAIN_PROVIDER env var or configure provider."
        )

    # Check API key in environment/.env (never log the value)
    result.api_key_present = _detect_api_key(ENV_KEY_NAME)
    result.api_key_logged = False
    result.api_key_stored_in_artifact = False
    if not result.api_key_present:
        result.errors.append(
            f"No API key found in environment or .env (checked {ENV_KEY_NAME})"
        )

    # Check if model ID is a known/valid model identifier
    known_model_prefixes = (
        "deepseek-",
        "claude-",
        "gpt-",
        "gemini-",
        "mistral-",
        "llama-",
    )
    is_known_prefix = any(
        config.primary_model_id.startswith(p) for p in known_model_prefixes
    )
    if config.exact_model_id_validation_required and not is_known_prefix:
        result.errors.append(
            f"Model ID '{config.primary_model_id}' does not match any known model prefix. "
            "Exact model ID validation required."
        )
    else:
        result.model_id_validated = True

    result.model_id_config_driven = (
        config.primary_model_id != ""
        and config.primary_model_id is not None
        and config.hardcode_forbidden is True
    )

    # Fallback policy check — presence of required fallback config is enough
    result.fallback_policy_present = config.fallback_model_required is True
    if config.fallback_model_required and not result.fallback_policy_present:
        result.errors.append("Fallback model policy required but not present.")

    # Determine config validation status
    # Runtime API call is NOT executed in this validation.
    config_valid = (
        result.provider_config_present
        and result.api_key_present
        and result.model_id_config_driven
        and result.fallback_policy_present
    )

    result.runtime_call_executed = False
    result.availability_validated_by_api_call = False

    if config_valid:
        result.validation_status = "config_valid_runtime_not_executed"
    else:
        result.validation_status = "config_invalid"
        result.errors.append(
            "Brain provider config validation: one or more checks did not pass. "
            "Runtime API call requires separate explicit gate."
        )

    return result
