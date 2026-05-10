"""
RC-COMBINE-V2-BRAIN-RUNTIME-SMOKE-TEST-001
Tests for DeepSeek brain runtime smoke test gate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from argparse import Namespace

from app.agents.brain.brain_config import BrainProviderConfig
from app.agents.brain.brain_provider import (
    run_brain_runtime_smoke_test,
    BrainRuntimeSmokeTestResult,
    ENV_KEY_NAME,
)
from app.cli import combine_run_brain_runtime_smoke_test


@pytest.fixture
def authorized_env(tmp_path):
    """Set up a temporary project with valid operator authorization."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    auth = {
        "authorization_type": "brain_runtime_smoke_test",
        "authorized": True,
        "authorized_by": "human_operator",
        "target_provider": "deepseek",
        "target_model": "deepseek-v4-flash",
        "max_brain_calls": 1,
        "state_update_allowed": False,
        "visual_acceptance_allowed": False,
        "audio_acceptance_allowed": False,
        "generation_allowed": False,
        "preview_render_allowed": False,
        "voice_generation_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted_allowed": False,
    }
    with open(control_dir / "brain_runtime_smoke_test_operator_authorization.json", "w") as f:
        json.dump(auth, f)
    return tmp_path


@pytest.fixture
def mock_gate_authorized():
    """Patch BrainRuntimeGate to always authorize."""
    with patch("app.agents.brain.brain_runtime_gate.BrainRuntimeGate") as MockGate:
        instance = MagicMock()
        instance.check.return_value = MagicMock(
            runtime_call_authorized=True,
            external_api_call_allowed=True,
            operator_authorization_exists=True,
            provider_config_present=True,
            api_key_present=True,
            model_id_validated=True,
            budget_limit_defined=True,
            max_brain_calls_within_limit=True,
            brain_output_advisory_only=True,
            errors=[],
        )
        MockGate.return_value = instance
        yield


def _make_mock_run():
    """Return a mock run function that simulates a successful smoke test."""
    def mock_run(*a, **k):
        return BrainRuntimeSmokeTestResult(
            ok=True,
            provider="deepseek",
            model="deepseek-v4-flash",
            message="healthcheck ok",
            runtime_call_executed=True,
            brain_call_count=1,
            provider_runtime_available=True,
            model_runtime_available=True,
        )
    return mock_run


# ---------------------------------------------------------------------------
# Authorization requirement
# ---------------------------------------------------------------------------


def test_smoke_test_requires_operator_authorization(tmp_path):
    """Smoke test must be blocked if operator authorization artifact is missing."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    args = Namespace(
        project_root=str(tmp_path),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    result = combine_run_brain_runtime_smoke_test(args)
    assert result == 1

    # Check that no artifacts were created
    assert not (control_dir / "brain_runtime_smoke_test_request.json").exists()
    assert not (control_dir / "brain_runtime_smoke_test_response.json").exists()


def test_smoke_test_blocks_without_execute_flag(authorized_env):
    """Smoke test must be blocked if --execute flag is not provided."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=False,
        max_brain_calls=1,
        json=True,
    )

    result = combine_run_brain_runtime_smoke_test(args)
    assert result == 1


# ---------------------------------------------------------------------------
# Call limit
# ---------------------------------------------------------------------------


def test_smoke_test_limits_to_one_call(authorized_env, mock_gate_authorized):
    """Smoke test must enforce max_brain_calls = 1."""
    call_count = 0

    def mock_run(*a, **k):
        nonlocal call_count
        call_count += 1
        return BrainRuntimeSmokeTestResult(
            ok=True,
            provider="deepseek",
            model="deepseek-v4-flash",
            message="healthcheck ok",
            runtime_call_executed=True,
            brain_call_count=1,
            provider_runtime_available=True,
            model_runtime_available=True,
        )

    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=mock_run):
        result = combine_run_brain_runtime_smoke_test(args)

    assert result == 0
    assert call_count == 1

    # Verify response artifact says exactly 1 call
    control_dir = Path(authorized_env) / "output" / "control"
    with open(control_dir / "brain_runtime_smoke_test_result.json") as f:
        result_data = json.load(f)
    assert result_data["brain_call_count"] == 1
    assert result_data["max_brain_calls"] == 1
    assert result_data["second_brain_call_attempted"] is False


# ---------------------------------------------------------------------------
# API key secrecy
# ---------------------------------------------------------------------------


def test_smoke_test_does_not_log_api_key(authorized_env, mock_gate_authorized, capsys):
    """API key must never appear in CLI stdout/stderr."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=False,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    captured = capsys.readouterr()
    combined_output = captured.out + captured.err
    assert "sk-" not in combined_output, "API key leaked to stdout/stderr"


def test_smoke_test_does_not_write_api_key_to_artifacts(authorized_env, mock_gate_authorized):
    """API key must never be written to any artifact JSON."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"
    for artifact_name in [
        "brain_runtime_smoke_test_request.json",
        "brain_runtime_smoke_test_response.json",
        "brain_runtime_smoke_test_result.json",
        "brain_runtime_provider_status.json",
    ]:
        path = control_dir / artifact_name
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        artifact_str = json.dumps(data)
        assert "sk-" not in artifact_str, f"API key leaked in {artifact_name}"


# ---------------------------------------------------------------------------
# Advisory-only and forbidden actions
# ---------------------------------------------------------------------------


def test_smoke_test_output_is_advisory_only(authorized_env, mock_gate_authorized):
    """Brain output must be advisory only — may not mutate state."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"
    with open(control_dir / "brain_runtime_smoke_test_result.json") as f:
        result = json.load(f)
    assert result["brain_output_used_as_advisory_only"] is True
    assert result["brain_output_updated_state_directly"] is False


def test_smoke_test_cannot_update_state_directly(authorized_env, mock_gate_authorized):
    """Smoke test result must record that state was NOT updated by brain output."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"
    with open(control_dir / "brain_runtime_smoke_test_result.json") as f:
        result = json.load(f)
    assert result["brain_output_updated_state_directly"] is False
    assert result["generation_performed"] is False
    assert result["comfyui_submit_executed"] is False
    assert result["retry_attempted"] is False


def test_smoke_test_cannot_trigger_generation_preview_voice_assembly(authorized_env, mock_gate_authorized):
    """Smoke test must NOT trigger generation, preview, voice, assembly, or downstream."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"
    with open(control_dir / "brain_runtime_smoke_test_result.json") as f:
        result = json.load(f)
    assert result["generation_performed"] is False
    assert result["preview_render_executed"] is False
    assert result["voice_generation_executed"] is False
    assert result["assembly_executed"] is False
    assert result["downstream_executed"] is False
    assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Provider status recording
# ---------------------------------------------------------------------------


def test_smoke_test_records_provider_status(authorized_env, mock_gate_authorized):
    """Smoke test must create brain_runtime_provider_status.json."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"
    status_path = control_dir / "brain_runtime_provider_status.json"
    assert status_path.exists()
    with open(status_path) as f:
        status = json.load(f)
    assert "provider_runtime_available" in status
    assert "model_runtime_available" in status
    assert "api_key_logged" in status
    assert status["api_key_logged"] is False


# ---------------------------------------------------------------------------
# Artifact index and ledger updates
# ---------------------------------------------------------------------------


def test_smoke_test_updates_artifact_index_and_ledger(authorized_env, mock_gate_authorized):
    """Smoke test must update artifact_index.json and episode_ledger.json."""
    args = Namespace(
        project_root=str(authorized_env),
        execute=True,
        max_brain_calls=1,
        json=True,
    )

    with patch("app.agents.brain.brain_provider.run_brain_runtime_smoke_test", side_effect=_make_mock_run()):
        combine_run_brain_runtime_smoke_test(args)

    control_dir = Path(authorized_env) / "output" / "control"

    # Check artifact_index.json
    index_path = control_dir / "artifact_index.json"
    assert index_path.exists()
    with open(index_path) as f:
        index = json.load(f)
    assert index.get("brain_runtime_smoke_test_executed") is True
    assert index.get("brain_runtime_smoke_test_passed") is True
    assert "brain_runtime_smoke_test_request" in index
    assert "brain_runtime_smoke_test_response" in index
    assert "brain_runtime_smoke_test_result" in index
    assert "brain_runtime_provider_status" in index

    # Check episode_ledger.json
    ledger_path = control_dir / "episode_ledger.json"
    assert ledger_path.exists()
    with open(ledger_path) as f:
        ledger = json.load(f)
    assert isinstance(ledger, list)
    smoke_events = [e for e in ledger if e.get("event_type") == "brain_runtime_smoke_test"]
    assert len(smoke_events) >= 1
    event = smoke_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-BRAIN-RUNTIME-SMOKE-TEST-001"
    assert event["runtime_call_executed"] is True
    assert event["brain_call_count"] == 1
    assert event["production_accepted"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
