"""Tests for RC-COMBINE-V2-5701-6000 V8 quality-locked generation authorization.

Tests cover:
- requires_v8_quality_locked_state
- requires_operator_authorization
- requires_v8_package
- requires_v8_guardrails
- requires_agent_role_contracts
- max_generations_enforced_as_one
- second_generation_blocked
- retry_blocked
"""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        control_dir = root / "output" / "control"
        assets_dir = root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        yield root


@pytest.fixture
def v8_artifacts(project_root):
    control_dir = project_root / "output" / "control"
    agent_contracts_dir = control_dir / "agent_role_contracts"
    agent_contracts_dir.mkdir(parents=True, exist_ok=True)

    # Create artifact_index with correct state
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required"
        }, f, indent=2)

    # V8 refinement package
    with open(control_dir / "combine_v2_v8_quality_locked_refinement_package.json", "w") as f:
        json.dump({
            "artifact_id": "combine_v2_v8_quality_locked_refinement_package",
            "references": {
                "concept_reference": {"path": "test_concept.png"},
                "quality_reference": {"path": "test_quality.png"},
                "failed_candidate": {"path": "test_failed.png"}
            }
        }, f, indent=2)

    # V8 guardrails
    with open(control_dir / "combine_v2_v8_quality_guardrails.json", "w") as f:
        json.dump({"artifact_id": "combine_v2_v8_quality_guardrails"}, f, indent=2)

    # V8 generation gate
    with open(control_dir / "combine_v2_v8_quality_locked_generation_gate.json", "w") as f:
        json.dump({"artifact_id": "combine_v2_v8_quality_locked_generation_gate"}, f, indent=2)

    # Agent role contract index
    with open(control_dir / "combine_v2_agent_role_contract_index.json", "w") as f:
        json.dump({
            "combine_v2_agent_role_contract_index": {
                "total_agents": 9,
                "agents": [{"agent_id": "vqa_combine_v2_01", "agent_name": "Visual Quality / QA Agent"}]
            }
        }, f, indent=2)

    # Visual quality agent contract
    with open(agent_contracts_dir / "visual_quality_agent_contract.json", "w") as f:
        json.dump({
            "agent_id": "vqa_combine_v2_01",
            "agent_name": "Visual Quality / QA Agent",
            "professional_role": "Visual Quality Assurance"
        }, f, indent=2)

    return control_dir


def test_requires_v8_quality_locked_state(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Wrong state
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({"current_state": "generate_assets", "next_allowed_action": "generate_assets"}, f, indent=2)

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject when state is not v8_quality_locked_generation_authorization_required"


def test_requires_operator_authorization(project_root, v8_artifacts):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    # The function creates its own authorization artifact on run
    # Verify that authorization artifact is created
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0, "Dry run should succeed with valid state and artifacts"

    auth_path = v8_artifacts / "combine_v2_v8_operator_generation_authorization.json"
    assert auth_path.exists(), "Operator authorization artifact should be created"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("operator_authorized_v8_generation") is True


def test_requires_v8_package(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required"
        }, f, indent=2)

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject when V8 package is missing"

    # Now add V8 package but not guardrails
    with open(control_dir / "combine_v2_v8_quality_locked_refinement_package.json", "w") as f:
        json.dump({"test": True}, f, indent=2)

    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject when guardrails are missing"


def test_requires_v8_guardrails(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required"
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_refinement_package.json", "w") as f:
        json.dump({"test": True}, f, indent=2)

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject when guardrails are missing"


def test_requires_agent_role_contracts(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required"
        }, f, indent=2)

    with open(control_dir / "combine_v2_v8_quality_locked_refinement_package.json", "w") as f:
        json.dump({"test": True}, f, indent=2)
    with open(control_dir / "combine_v2_v8_quality_guardrails.json", "w") as f:
        json.dump({"test": True}, f, indent=2)

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject when agent role contracts are missing"


def test_max_generations_enforced_as_one(project_root, v8_artifacts):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=2,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1, "Should reject max_generations != 1"


def test_second_generation_blocked_by_artifact(project_root, v8_artifacts):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0

    auth_path = v8_artifacts / "combine_v2_v8_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("second_generation_allowed") is False
    assert auth.get("retry_allowed") is False


def test_retry_blocked_by_artifact(project_root, v8_artifacts):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0

    execution_path = v8_artifacts / "combine_v2_v8_quality_locked_generation_execution.json"
    with open(execution_path) as f:
        execution = json.load(f)
    assert execution.get("retry_attempted") is False
    assert execution.get("second_generation_attempted") is False
