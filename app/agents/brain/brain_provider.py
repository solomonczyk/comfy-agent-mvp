"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Brain provider validation — checks if the configured model/provider is available.

deepseek-v4-flash is a planned brain/model id, not proof of availability.
If provider/model/API is unavailable, route to brain_provider_validation_blocker_required.
No hidden API calls. No faked availability.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from app.agents.brain.brain_config import BrainProviderConfig


@dataclass
class BrainProviderValidationResult:
    """Result of provider validation."""

    provider_available: bool = False
    model_id_validated: bool = False
    api_key_present: bool = False
    provider_config_present: bool = False
    budget_limit_defined: bool = False
    fallback_available: bool = False
    errors: list = field(default_factory=list)
    validation_passed: bool = False

    def to_dict(self) -> dict:
        return {
            "provider_available": self.provider_available,
            "model_id_validated": self.model_id_validated,
            "api_key_present": self.api_key_present,
            "provider_config_present": self.provider_config_present,
            "budget_limit_defined": self.budget_limit_defined,
            "fallback_available": self.fallback_available,
            "errors": self.errors,
            "validation_passed": self.validation_passed,
        }


def validate_brain_provider(
    config: Optional[BrainProviderConfig] = None,
) -> BrainProviderValidationResult:
    """Validate the configured brain provider.

    Checks:
    1. Provider config exists (provider != "configurable" or explicitly set)
    2. API key is present in environment
    3. Model ID is a known/valid identifier
    4. Budget limits are defined
    5. Fallback model is available

    Since deepseek-v4-flash is a planned model ID, not a confirmed available
    provider, this will likely validate with blocker status unless the
    provider is actually configured.
    """
    result = BrainProviderValidationResult()

    if config is None:
        config = BrainProviderConfig.default()

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

    # Check API key in environment
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
        "BRAIN_API_KEY"
    )
    result.api_key_present = bool(api_key and api_key.strip())
    if not result.api_key_present:
        result.errors.append(
            "No API key found in environment (checked OPENROUTER_API_KEY, BRAIN_API_KEY)"
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

    # Budget check
    result.budget_limit_defined = config.budget_limit_defined
    if config.budget_limit_defined and config.max_budget_per_task <= 0:
        result.errors.append("Budget limit defined but max_budget_per_task <= 0")

    # Fallback check
    result.fallback_available = config.fallback_model_id not in (
        "",
        "configurable",
        None,
    )
    if config.fallback_model_required and not result.fallback_available:
        result.errors.append(
            "Fallback model required but not configured "
            "(fallback_model_id is 'configurable')"
        )

    # Determine availability
    # For the planned deepseek-v4-flash, we don't have a real provider
    # configured. Unless all checks pass, treat as unavailable.
    provider_available = (
        result.provider_config_present
        and result.api_key_present
        and result.model_id_validated
        and result.budget_limit_defined
        and result.fallback_available
    )

    result.provider_available = provider_available
    result.validation_passed = provider_available

    if not provider_available:
        result.errors.append(
            "Brain provider validation failed: one or more checks did not pass. "
            "Routing to brain_provider_validation_blocker_required."
        )

    return result
