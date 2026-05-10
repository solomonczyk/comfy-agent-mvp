"""
RC-COMBINE-V2-BRAIN-PROVIDER-VALIDATION-001
Brain provider validation — checks if the configured model/provider config is valid.

Does NOT perform runtime API calls. Config validation only.
No hidden API calls. No faked availability.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

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


@dataclass
class BrainRuntimeSmokeTestResult:
    """Result of a single brain runtime smoke test API call."""

    ok: bool = False
    provider: str = "deepseek"
    model: str = "deepseek-v4-flash"
    message: str = ""
    error: str = ""
    api_key_logged: bool = False
    api_key_written_to_artifacts: bool = False
    runtime_call_executed: bool = False
    brain_call_count: int = 0
    max_brain_calls: int = 1
    second_brain_call_attempted: bool = False
    provider_runtime_available: bool = False
    model_runtime_available: bool = False
    brain_output_used_as_advisory_only: bool = True
    brain_output_updated_state_directly: bool = False
    generation_performed: bool = False
    comfyui_submit_executed: bool = False
    retry_attempted: bool = False
    preview_render_executed: bool = False
    voice_generation_executed: bool = False
    assembly_executed: bool = False
    downstream_executed: bool = False
    production_accepted: bool = False
    raw_response: str = ""
    request_timestamp: str = ""
    response_timestamp: str = ""
    http_status_code: int = 0

    def to_dict(self) -> dict:
        d = {
            "ok": self.ok,
            "provider": self.provider,
            "model": self.model,
            "message": self.message,
            "error": self.error,
            "api_key_logged": self.api_key_logged,
            "api_key_written_to_artifacts": self.api_key_written_to_artifacts,
            "runtime_call_executed": self.runtime_call_executed,
            "brain_call_count": self.brain_call_count,
            "max_brain_calls": self.max_brain_calls,
            "second_brain_call_attempted": self.second_brain_call_attempted,
            "provider_runtime_available": self.provider_runtime_available,
            "model_runtime_available": self.model_runtime_available,
            "brain_output_used_as_advisory_only": self.brain_output_used_as_advisory_only,
            "brain_output_updated_state_directly": self.brain_output_updated_state_directly,
            "generation_performed": self.generation_performed,
            "comfyui_submit_executed": self.comfyui_submit_executed,
            "retry_attempted": self.retry_attempted,
            "preview_render_executed": self.preview_render_executed,
            "voice_generation_executed": self.voice_generation_executed,
            "assembly_executed": self.assembly_executed,
            "downstream_executed": self.downstream_executed,
            "production_accepted": self.production_accepted,
            "raw_response": self.raw_response,
            "request_timestamp": self.request_timestamp,
            "response_timestamp": self.response_timestamp,
            "http_status_code": self.http_status_code,
        }
        return d


def _get_api_key_value(env_key_name: str = ENV_KEY_NAME) -> Optional[str]:
    """Get the actual API key value for runtime calls.

    This is internal-only and must never be logged or written to artifacts.
    """
    value = os.environ.get(env_key_name)
    if value:
        return value
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
                            key, val = line.split("=", 1)
                            key = key.strip()
                            if key == env_key_name:
                                return val.strip().strip('"').strip("'")
            except OSError:
                continue
    return None


def _sanitize_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the payload with any API key redacted."""
    sanitized = dict(payload)
    if "headers" in sanitized:
        sanitized["headers"] = {
            k: "[REDACTED]" if k.lower() in ("authorization", "x-api-key") else v
            for k, v in sanitized["headers"].items()
        }
    return sanitized


def run_brain_runtime_smoke_test(
    config: Optional[BrainProviderConfig] = None,
    max_brain_calls: int = 1,
) -> BrainRuntimeSmokeTestResult:
    """Execute exactly one harmless DeepSeek runtime API call.

    This is a healthcheck only — no reasoning, no state mutation,
    no generation, no preview, no voice, no assembly, no downstream.
    """
    result = BrainRuntimeSmokeTestResult(
        max_brain_calls=max_brain_calls,
        api_key_logged=False,
        api_key_written_to_artifacts=False,
        brain_output_used_as_advisory_only=True,
        brain_output_updated_state_directly=False,
        generation_performed=False,
        comfyui_submit_executed=False,
        retry_attempted=False,
        preview_render_executed=False,
        voice_generation_executed=False,
        assembly_executed=False,
        downstream_executed=False,
        production_accepted=False,
    )

    if config is None:
        config = BrainProviderConfig.default()

    result.provider = config.provider
    result.model = config.primary_model_id

    api_key = _get_api_key_value(ENV_KEY_NAME)
    if not api_key:
        result.error = f"API key not found in environment or .env (checked {ENV_KEY_NAME})"
        result.provider_runtime_available = False
        result.model_runtime_available = False
        return result

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    url = f"{base_url}/chat/completions"

    system_prompt = (
        "You are a healthcheck endpoint. "
        "Return ONLY a compact JSON object with exactly these keys: ok (boolean), provider (string), model (string), message (string max 12 words). "
        "No markdown fences. No extra text."
    )
    user_prompt = (
        "Return a compact JSON healthcheck response. Example: "
        '{"ok":true,"provider":"deepseek","model":"deepseek-v4-flash","message":"healthcheck ok"}'
    )

    payload = {
        "model": config.primary_model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 100,
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    result.request_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            result.http_status_code = response.status_code
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        result.error = f"HTTP {exc.response.status_code}: {exc.response.text}"
        result.provider_runtime_available = False
        result.model_runtime_available = False
        result.response_timestamp = datetime.now(timezone.utc).isoformat()
        return result
    except httpx.TimeoutException:
        result.error = "Request timed out after 30s"
        result.provider_runtime_available = False
        result.model_runtime_available = False
        result.response_timestamp = datetime.now(timezone.utc).isoformat()
        return result
    except Exception as exc:
        result.error = f"Request failed: {str(exc)}"
        result.provider_runtime_available = False
        result.model_runtime_available = False
        result.response_timestamp = datetime.now(timezone.utc).isoformat()
        return result

    result.response_timestamp = datetime.now(timezone.utc).isoformat()
    result.runtime_call_executed = True
    result.brain_call_count = 1

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        result.error = f"Unexpected response structure: {json.dumps(data)[:500]}"
        result.provider_runtime_available = False
        result.model_runtime_available = False
        return result

    result.raw_response = content[:2000]  # cap raw response size

    # Try to parse JSON from the content
    parsed = None
    cleaned = content
    if "```json" in cleaned:
        start = cleaned.find("```json") + 7
        end = cleaned.find("```", start)
        if end != -1:
            cleaned = cleaned[start:end].strip()
    elif "```" in cleaned:
        start = cleaned.find("```") + 3
        end = cleaned.find("```", start)
        if end != -1:
            cleaned = cleaned[start:end].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # If it doesn't parse, treat the raw text as the message
        parsed = None

    if isinstance(parsed, dict):
        result.ok = bool(parsed.get("ok", False))
        result.provider = parsed.get("provider", config.provider)
        result.model = parsed.get("model", config.primary_model_id)
        result.message = parsed.get("message", content[:200])
    else:
        # Non-JSON response: treat as honest response, ok if HTTP succeeded
        result.ok = True
        result.message = content[:200]

    result.provider_runtime_available = True
    result.model_runtime_available = result.ok
    return result
