"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Brain provider configuration — model-driven, not hardcoded.

No model id hardcoded inside business logic.
primary_model_id is declared at config level and validated at runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrainProviderConfig:
    """Configuration for the brain model provider.

    All model IDs are declared here, not in business logic.
    Runtime call requires explicit gate authorization.
    """

    primary_model_id: str = "deepseek-v4-flash"
    provider: str = "deepseek"
    api_key_source: str = "env:DEEPSEEK_V4_FLASH_API_KEY"
    fallback_model_id: str = "configurable"
    max_calls_per_task: int = 2
    max_tokens_per_call: int = 4096
    runtime_call_authorized: bool = False
    runtime_call_authorized_by_default: bool = False

    # Hardcode prevention
    hardcode_forbidden: bool = True
    provider_validation_required: bool = True
    exact_model_id_validation_required: bool = True
    availability_validation_required: bool = True
    pricing_limits_validation_required: bool = True
    fallback_model_required: bool = True
    hidden_api_calls_forbidden: bool = True

    # Configurability
    provider_base_url_configurable: bool = True

    # Budget
    budget_limit_defined: bool = False
    max_budget_per_task: float = 0.0

    @classmethod
    def default(cls) -> "BrainProviderConfig":
        return cls()

    @classmethod
    def from_env(cls) -> "BrainProviderConfig":
        """Load config from environment variables with sensible defaults."""
        return cls(
            primary_model_id=os.environ.get(
                "BRAIN_PRIMARY_MODEL_ID", "deepseek-v4-flash"
            ),
            provider=os.environ.get("BRAIN_PROVIDER", "deepseek"),
            api_key_source=os.environ.get(
                "BRAIN_API_KEY_SOURCE", "env:DEEPSEEK_V4_FLASH_API_KEY"
            ),
            fallback_model_id=os.environ.get(
                "BRAIN_FALLBACK_MODEL_ID", "configurable"
            ),
            max_calls_per_task=int(
                os.environ.get("BRAIN_MAX_CALLS_PER_TASK", "2")
            ),
            max_tokens_per_call=int(
                os.environ.get("BRAIN_MAX_TOKENS_PER_CALL", "4096")
            ),
            runtime_call_authorized=False,
            runtime_call_authorized_by_default=False,
            provider_base_url_configurable=True,
        )

    def to_dict(self) -> dict:
        return {
            "primary_model_id": self.primary_model_id,
            "provider": self.provider,
            "api_key_source": self.api_key_source,
            "fallback_model_id": self.fallback_model_id,
            "max_calls_per_task": self.max_calls_per_task,
            "max_tokens_per_call": self.max_tokens_per_call,
            "runtime_call_authorized": self.runtime_call_authorized,
            "runtime_call_authorized_by_default": self.runtime_call_authorized_by_default,
            "hardcode_forbidden": self.hardcode_forbidden,
            "provider_validation_required": self.provider_validation_required,
            "exact_model_id_validation_required": self.exact_model_id_validation_required,
            "availability_validation_required": self.availability_validation_required,
            "pricing_limits_validation_required": self.pricing_limits_validation_required,
            "fallback_model_required": self.fallback_model_required,
            "hidden_api_calls_forbidden": self.hidden_api_calls_forbidden,
            "provider_base_url_configurable": self.provider_base_url_configurable,
            "budget_limit_defined": self.budget_limit_defined,
            "max_budget_per_task": self.max_budget_per_task,
        }
