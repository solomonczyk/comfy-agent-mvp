"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Brain runtime gate — controls when external LLM/API calls are allowed.

External LLM/API call is allowed ONLY if ALL are true:
  - operator_brain_runtime_authorization_exists
  - provider_config_present
  - api_key_present_in_env
  - model_id_validated
  - budget_limit_defined
  - max_brain_calls <= MAX_BRAIN_CALLS_LIMIT
  - brain_output_is_advisory_only

No hidden API calls. No bypass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


MAX_BRAIN_CALLS_LIMIT = 2


@dataclass
class BrainRuntimeGateResult:
    """Result of runtime gate check."""

    runtime_call_authorized: bool = False
    external_api_call_allowed: bool = False
    operator_authorization_exists: bool = False
    provider_config_present: bool = False
    api_key_present: bool = False
    model_id_validated: bool = False
    budget_limit_defined: bool = False
    max_brain_calls_within_limit: bool = False
    max_brain_calls: int = 0
    brain_output_advisory_only: bool = False
    brain_output_may_update_state_directly: bool = False
    brain_output_may_accept_visual: bool = False
    brain_output_may_accept_audio: bool = False
    brain_output_may_run_generation: bool = False
    hidden_api_calls_forbidden: bool = True
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "runtime_call_authorized": self.runtime_call_authorized,
            "external_api_call_allowed": self.external_api_call_allowed,
            "operator_authorization_exists": self.operator_authorization_exists,
            "provider_config_present": self.provider_config_present,
            "api_key_present": self.api_key_present,
            "model_id_validated": self.model_id_validated,
            "budget_limit_defined": self.budget_limit_defined,
            "max_brain_calls_within_limit": self.max_brain_calls_within_limit,
            "max_brain_calls": self.max_brain_calls,
            "brain_output_advisory_only": self.brain_output_advisory_only,
            "brain_output_may_update_state_directly": self.brain_output_may_update_state_directly,
            "brain_output_may_accept_visual": self.brain_output_may_accept_visual,
            "brain_output_may_accept_audio": self.brain_output_may_accept_audio,
            "brain_output_may_run_generation": self.brain_output_may_run_generation,
            "hidden_api_calls_forbidden": self.hidden_api_calls_forbidden,
            "errors": self.errors,
        }


class BrainRuntimeGate:
    """Runtime gate for brain API calls.

    All conditions must be true for a brain call to be authorized.
    Brain output is always advisory-only — it may not update state directly,
    may not accept visual results, and must be validated deterministically.
    """

    def __init__(
        self,
        operator_authorization_exists: bool = False,
        provider_config_present: bool = False,
        api_key_present: bool = False,
        model_id_validated: bool = False,
        budget_limit_defined: bool = False,
        brain_calls_used: int = 0,
        brain_output_advisory_only: bool = True,
    ):
        self._operator_authorization_exists = operator_authorization_exists
        self._provider_config_present = provider_config_present
        self._api_key_present = api_key_present
        self._model_id_validated = model_id_validated
        self._budget_limit_defined = budget_limit_defined
        self._brain_calls_used = brain_calls_used
        self._brain_output_advisory_only = brain_output_advisory_only

    def check(self) -> BrainRuntimeGateResult:
        """Evaluate all gate conditions. Returns result with full detail."""
        within_limit = self._brain_calls_used < MAX_BRAIN_CALLS_LIMIT
        authorized = (
            self._operator_authorization_exists
            and self._provider_config_present
            and self._api_key_present
            and self._model_id_validated
            and self._budget_limit_defined
            and within_limit
            and self._brain_output_advisory_only
        )

        result = BrainRuntimeGateResult(
            runtime_call_authorized=authorized,
            external_api_call_allowed=authorized,
            operator_authorization_exists=self._operator_authorization_exists,
            provider_config_present=self._provider_config_present,
            api_key_present=self._api_key_present,
            model_id_validated=self._model_id_validated,
            budget_limit_defined=self._budget_limit_defined,
            max_brain_calls_within_limit=within_limit,
            max_brain_calls=MAX_BRAIN_CALLS_LIMIT if authorized else 0,
            brain_output_advisory_only=self._brain_output_advisory_only,
            brain_output_may_update_state_directly=False,
            brain_output_may_accept_visual=False,
            brain_output_may_accept_audio=False,
            brain_output_may_run_generation=False,
            hidden_api_calls_forbidden=True,
        )

        errors = []

        if not self._operator_authorization_exists:
            errors.append(
                "Operator brain runtime authorization does not exist. "
                "A human operator must authorize brain API calls."
            )
        if not self._provider_config_present:
            errors.append("Provider config not present.")
        if not self._api_key_present:
            errors.append("API key not present in environment.")
        if not self._model_id_validated:
            errors.append("Model ID not validated.")
        if not self._budget_limit_defined:
            errors.append("Budget limit not defined.")
        if not within_limit:
            errors.append(
                f"Brain calls used ({self._brain_calls_used}) >= max "
                f"({MAX_BRAIN_CALLS_LIMIT})."
            )
        if not self._brain_output_advisory_only:
            errors.append("Brain output must be advisory-only.")

        result.errors = errors
        return result

    def record_call(self) -> None:
        """Increment the brain call counter after a call is made."""
        self._brain_calls_used += 1

    @property
    def calls_remaining(self) -> int:
        return max(0, MAX_BRAIN_CALLS_LIMIT - self._brain_calls_used)

    def to_dict(self) -> dict:
        return {
            "operator_authorization_exists": self._operator_authorization_exists,
            "provider_config_present": self._provider_config_present,
            "api_key_present": self._api_key_present,
            "model_id_validated": self._model_id_validated,
            "budget_limit_defined": self._budget_limit_defined,
            "brain_calls_used": self._brain_calls_used,
            "max_brain_calls": MAX_BRAIN_CALLS_LIMIT,
            "brain_calls_remaining": self.calls_remaining,
            "brain_output_advisory_only": self._brain_output_advisory_only,
            "brain_output_may_update_state_directly": False,
            "brain_output_may_accept_visual": False,
            "brain_output_may_accept_audio": False,
            "brain_output_may_run_generation": False,
            "hidden_api_calls_forbidden": True,
        }
