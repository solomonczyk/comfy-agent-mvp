"""Tests for RC-COMBINE-V2-5701-6000 V8 quality-locked generation result review.

Tests cover:
- visual_acceptance_not_executed
- production_accepted_false
- assembly_downstream_blocked
- state_moves_to_operator_visual_review
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
        agent_contracts_dir = control_dir / "agent_role_contracts"
        assets_dir = root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        agent_contracts_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create all required artifacts for V8 generation
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({
                "current_state": "v8_quality_locked_generation_authorization_required",
                "next_allowed_action": "v8_quality_locked_generation_authorization_required"
            }, f, indent=2)

        with open(control_dir / "combine_v2_v8_quality_locked_refinement_package.json", "w") as f:
            json.dump({
                "artifact_id": "test",
                "references": {
                    "concept_reference": {"path": "test.png"},
                    "quality_reference": {"path": "test.png"},
                    "failed_candidate": {"path": "test.png"}
                }
            }, f, indent=2)

        with open(control_dir / "combine_v2_v8_quality_guardrails.json", "w") as f:
            json.dump({"artifact_id": "test"}, f, indent=2)

        with open(control_dir / "combine_v2_v8_quality_locked_generation_gate.json", "w") as f:
            json.dump({"artifact_id": "test"}, f, indent=2)

        with open(control_dir / "combine_v2_agent_role_contract_index.json", "w") as f:
            json.dump({"combine_v2_agent_role_contract_index": {"total_agents": 9, "agents": []}}, f, indent=2)

        with open(agent_contracts_dir / "visual_quality_agent_contract.json", "w") as f:
            json.dump({"agent_id": "vqa_combine_v2_01"}, f, indent=2)

        yield root


def test_visual_acceptance_not_executed(project_root):
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

    result_review_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_generation_result_review.json"
    assert result_review_path.exists()
    with open(result_review_path) as f:
        review = json.load(f)
    assert review.get("visual_acceptance_executed") is False
    assert review.get("operator_visual_review_required") is True

    manifest_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_outputs_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest.get("visual_acceptance_executed") is False

    visual_review_packet_path = project_root / "output" / "control" / "combine_v2_v8_operator_visual_review_packet.json"
    with open(visual_review_packet_path) as f:
        packet = json.load(f)
    assert packet.get("visual_acceptance_executed") is False


def test_production_accepted_false(project_root):
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

    # Check all artifacts for production_accepted=false
    artifacts_to_check = [
        "combine_v2_v8_operator_generation_authorization.json",
        "combine_v2_v8_quality_locked_generation_execution.json",
        "combine_v2_v8_quality_locked_outputs_manifest.json",
        "combine_v2_v8_quality_locked_generation_result_review.json",
        "combine_v2_v8_operator_visual_review_packet.json",
    ]
    control_dir = project_root / "output" / "control"
    for artifact_name in artifacts_to_check:
        path = control_dir / artifact_name
        assert path.exists(), f"{artifact_name} should exist"
        with open(path) as f:
            data = json.load(f)
        assert data.get("production_accepted") is False, f"{artifact_name} should have production_accepted=false"


def test_assembly_downstream_blocked(project_root):
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

    auth_path = project_root / "output" / "control" / "combine_v2_v8_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("assembly_allowed") is False
    assert auth.get("downstream_allowed") is False

    manifest_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_outputs_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest.get("assembly_allowed") is False
    assert manifest.get("downstream_allowed") is False

    review_packet_path = project_root / "output" / "control" / "combine_v2_v8_operator_visual_review_packet.json"
    with open(review_packet_path) as f:
        packet = json.load(f)
    assert packet.get("assembly_allowed") is False
    assert packet.get("downstream_allowed") is False


def test_state_moves_to_operator_visual_review(project_root):
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

    # Check artifact_index state
    artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path) as f:
        index = json.load(f)
    assert index.get("current_state") == "v8_operator_visual_review_required"
    assert index.get("next_allowed_action") == "v8_operator_visual_review_required"

    # Check execution proof
    execution_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_generation_execution.json"
    with open(execution_path) as f:
        execution = json.load(f)
    assert execution.get("next_allowed_action") == "v8_operator_visual_review_required"

    # Check result review
    review_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_generation_result_review.json"
    with open(review_path) as f:
        review = json.load(f)
    assert review.get("next_allowed_action") == "v8_operator_visual_review_required"
    assert review.get("operator_visual_review_required") is True

    # Check visual review packet
    packet_path = project_root / "output" / "control" / "combine_v2_v8_operator_visual_review_packet.json"
    with open(packet_path) as f:
        packet = json.load(f)
    assert packet.get("operator_visual_review_required") is True
    assert packet.get("next_allowed_action") == "v8_operator_visual_review_required"
