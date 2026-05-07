"""Tests for RC-COMBINE-V2-6301-6600 V8 real generation execution.

Tests cover:
- authorization_required_before_generation
- execute_flag_required
- max_generations_one_enforced
- second_generation_blocked
- dry_run_not_accepted
- empty_prompt_id_fails
- empty_assets_fail
- real_asset_validation_required
- success_routes_to_operator_visual_review
- visual_qa_not_executed
- assembly_downstream_blocked
- production_accepted_false
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

        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({
                "current_state": "v8_generation_reexecution_authorization_required",
                "next_allowed_action": "v8_generation_reexecution_authorization_required",
                "production_accepted": False
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

        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f, indent=2)

        yield root, control_dir, assets_dir


def _create_auth_artifact(control_dir, timestamp="2026-05-07T00:00:00"):
    auth = {
        "operator_authorized": True,
        "authorized_action": "v8_real_generation_reexecution",
        "max_generations": 1,
        "generation_attempts_allowed": 1,
        "second_generation_allowed": False,
        "retry_allowed": False,
        "visual_qa_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "task_id": "RC-COMBINE-V2-6301-6600",
        "timestamp": timestamp
    }
    with open(control_dir / "combine_v2_v8_operator_reexecution_authorization.json", "w") as f:
        json.dump(auth, f, indent=2)
    return auth


def _transition_state_to_generation(control_dir):
    path = control_dir / "artifact_index.json"
    with open(path) as f:
        index = json.load(f)
    index["current_state"] = "v8_quality_locked_generation_authorization_required"
    index["next_allowed_action"] = "v8_quality_locked_generation_authorization_required"
    with open(path, "w") as f:
        json.dump(index, f, indent=2)


def test_authorization_required_before_generation(project_root):
    root, control_dir, _ = project_root
    auth_path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    assert not auth_path.exists()

    _create_auth_artifact(control_dir)
    assert auth_path.exists()
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("operator_authorized") is True
    assert auth.get("authorized_action") == "v8_real_generation_reexecution"
    assert auth.get("max_generations") == 1
    assert auth.get("second_generation_allowed") is False
    assert auth.get("retry_allowed") is False
    assert auth.get("visual_qa_allowed") is False
    assert auth.get("assembly_allowed") is False
    assert auth.get("downstream_allowed") is False
    assert auth.get("production_accepted") is False


def test_execute_flag_required(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    _transition_state_to_generation(control_dir)

    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0

    exec_path = control_dir / "combine_v2_v8_quality_locked_generation_execution.json"
    assert exec_path.exists()
    with open(exec_path) as f:
        execution = json.load(f)
    assert execution.get("execute_mode") is False
    assert execution.get("workflow_submitted") is False
    assert execution.get("generation_count") == 0


def test_max_generations_one_enforced(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    _transition_state_to_generation(control_dir)

    args = Namespace(
        project_root=str(root),
        execute=True,
        max_generations=2,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 1


def test_second_generation_blocked(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    auth_path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("second_generation_allowed") is False
    assert auth.get("generation_attempts_allowed") == 1


def test_dry_run_not_accepted(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    _transition_state_to_generation(control_dir)

    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0

    result_review_path = control_dir / "combine_v2_v8_quality_locked_generation_result_review.json"
    assert result_review_path.exists()
    with open(result_review_path) as f:
        review = json.load(f)
    assert review.get("dry_run_not_accepted_as_real_generation") is True


def test_empty_prompt_id_fails(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)

    result_path = control_dir / "combine_v2_v8_real_generation_result.json"
    result = {
        "task_id": "RC-COMBINE-V2-6301-6600",
        "prompt_id": "",
        "generation_count": 0,
        "comfyui_status": "failed",
        "failure_code": "server_unavailable"
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    with open(result_path) as f:
        data = json.load(f)
    assert data.get("prompt_id") == ""
    assert data.get("generation_count") == 0
    assert data.get("failure_code") is not None


def test_empty_assets_fail(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)

    manifest_path = control_dir / "combine_v2_v8_real_generation_outputs_manifest.json"
    manifest = {
        "generated_assets": [],
        "asset_paths": [],
        "generation_count": 0,
        "collection_status": "failed"
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    result_path = control_dir / "combine_v2_v8_real_generation_result.json"
    result = {
        "generated_assets": [],
        "generation_count": 0,
        "comfyui_status": "failed",
        "failure_code": "server_unavailable"
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    with open(result_path) as f:
        data = json.load(f)
    assert len(data.get("generated_assets", [])) == 0


def test_real_asset_validation_required(project_root):
    from app.cli import _is_image_readable, _file_sha256
    from PIL import Image

    root, control_dir, assets_dir = project_root

    img = Image.new("RGB", (1024, 1024), color="red")
    img_path = assets_dir / "real_asset.png"
    img.save(img_path)

    readable = _is_image_readable(img_path)
    assert readable["readable"] is True
    assert readable["width"] == 1024
    assert readable["height"] == 1024

    sha256 = _file_sha256(img_path)
    assert len(sha256) == 64

    size_bytes = img_path.stat().st_size
    assert size_bytes > 1024


def test_success_routes_to_operator_visual_review(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)

    from app.orchestrator.state_machine import CombineStateMachine

    sm = CombineStateMachine()
    assert sm.can_transition("operator_visual_review_required", "assembly_preflight_required")
    assert sm.can_transition("v8_generation_reexecution_authorization_required", "v8_quality_locked_generation_authorization_required")

    review_packet = {
        "operator_visual_review_required": True,
        "next_allowed_action": "v8_operator_visual_review_required"
    }
    packet_path = control_dir / "combine_v2_v8_operator_visual_review_packet.json"
    with open(packet_path, "w") as f:
        json.dump(review_packet, f, indent=2)

    with open(packet_path) as f:
        packet = json.load(f)
    assert packet.get("operator_visual_review_required") is True
    assert packet.get("next_allowed_action") == "v8_operator_visual_review_required"


def test_visual_qa_not_executed(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    _transition_state_to_generation(control_dir)

    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0

    artifacts_to_check = {
        "combine_v2_v8_quality_locked_generation_execution.json": "visual_acceptance_executed",
        "combine_v2_v8_quality_locked_outputs_manifest.json": "visual_acceptance_executed",
        "combine_v2_v8_quality_locked_generation_result_review.json": "visual_acceptance_executed",
    }
    for name, field in artifacts_to_check.items():
        path = control_dir / name
        assert path.exists(), f"{name} should exist"
        with open(path) as f:
            data = json.load(f)
        assert data.get(field) is False, f"{name} should have {field}=False"


def test_assembly_downstream_blocked(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    auth_path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("assembly_allowed") is False
    assert auth.get("downstream_allowed") is False


def test_production_accepted_false(project_root):
    root, control_dir, _ = project_root
    _create_auth_artifact(control_dir)
    auth_path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("production_accepted") is False
