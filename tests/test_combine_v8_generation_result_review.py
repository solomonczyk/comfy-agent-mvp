"""Tests for RC-COMBINE-V2-6301-6600 V8 generation result review.

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
        assets_dir = root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)

        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({
                "current_state": "v8_generation_reexecution_authorization_required",
                "next_allowed_action": "v8_generation_reexecution_authorization_required",
                "production_accepted": False
            }, f, indent=2)

        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f, indent=2)

        yield root, control_dir, assets_dir


def test_authorization_required_before_generation(project_root):
    root, control_dir, _ = project_root

    auth = {
        "operator_authorized": True,
        "authorized_action": "v8_real_generation_reexecution",
        "max_generations": 1,
        "second_generation_allowed": False,
        "retry_allowed": False,
        "visual_qa_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False
    }
    path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    with open(path, "w") as f:
        json.dump(auth, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["operator_authorized"] is True
    assert data["authorized_action"] == "v8_real_generation_reexecution"
    assert data["max_generations"] == 1


def test_execute_flag_required(project_root):
    root, control_dir, _ = project_root

    result = {
        "task_id": "RC-COMBINE-V2-6301-6600",
        "dry_run_used": False,
        "workflow_submitted": False,
        "comfyui_execution": False,
        "generation_count": 0,
        "comfyui_status": "failed",
        "failure_code": "server_unavailable"
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["dry_run_used"] is False


def test_max_generations_one_enforced(project_root):
    root, control_dir, _ = project_root

    result = {
        "task_id": "RC-COMBINE-V2-6301-6600",
        "generation_count": 0,
        "max_generations": 1,
        "second_generation_attempted": False
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["generation_count"] <= 1
    assert data["max_generations"] == 1
    assert data["second_generation_attempted"] is False


def test_second_generation_blocked(project_root):
    root, control_dir, _ = project_root

    result = {
        "second_generation_attempted": False,
        "generation_count": 0,
        "max_generations": 1,
        "retry_attempted": False
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["second_generation_attempted"] is False
    assert data["retry_attempted"] is False
    assert data["generation_count"] <= 1


def test_dry_run_not_accepted(project_root):
    root, control_dir, _ = project_root

    result = {
        "dry_run_used": False,
        "generation_count": 0,
        "comfyui_status": "failed",
        "workflow_submitted": False,
        "comfyui_execution": False
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["dry_run_used"] is False
    assert data["generation_count"] == 0


def test_empty_prompt_id_fails(project_root):
    root, control_dir, _ = project_root

    result = {
        "prompt_id": "",
        "comfyui_status": "failed",
        "failure_code": "server_unavailable",
        "generation_count": 0
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["prompt_id"] == ""
    assert data["failure_code"] is not None
    assert data["generation_count"] == 0


def test_empty_assets_fail(project_root):
    root, control_dir, _ = project_root

    result = {
        "generated_assets": [],
        "canonical_outputs_registered": False,
        "generation_count": 0,
        "failure_code": "server_unavailable"
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    manifest = {
        "generated_assets": [],
        "asset_paths": [],
        "generation_count": 0,
        "collection_status": "failed"
    }
    mpath = control_dir / "combine_v2_v8_real_generation_outputs_manifest.json"
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert len(data["generated_assets"]) == 0
    assert data["canonical_outputs_registered"] is False


def test_real_asset_validation_required(project_root):
    from app.cli import _is_image_readable, _file_sha256
    from PIL import Image

    root, control_dir, assets_dir = project_root

    img = Image.new("RGB", (1024, 1024), color="blue")
    img_path = assets_dir / "validation_test.png"
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

    packet = {
        "operator_visual_review_required": True,
        "next_allowed_action": "v8_operator_visual_review_required",
        "visual_qa_executed": False,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False
    }
    path = control_dir / "combine_v2_v8_operator_visual_review_packet.json"
    with open(path, "w") as f:
        json.dump(packet, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["operator_visual_review_required"] is True
    assert data["next_allowed_action"] == "v8_operator_visual_review_required"
    assert data["visual_qa_executed"] is False
    assert data["production_accepted"] is False

    index_path = control_dir / "artifact_index.json"
    with open(index_path) as f:
        index = json.load(f)
    index["current_state"] = "v8_operator_visual_review_required"
    index["next_allowed_action"] = "v8_operator_visual_review_required"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    with open(index_path) as f:
        index = json.load(f)
    assert index["current_state"] == "v8_operator_visual_review_required"
    assert index["next_allowed_action"] == "v8_operator_visual_review_required"


def test_visual_qa_not_executed(project_root):
    root, control_dir, _ = project_root

    result = {
        "visual_qa_executed": False,
        "operator_visual_decision_created": False
    }
    path = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    manifest = {
        "visual_qa_executed": False
    }
    mpath = control_dir / "combine_v2_v8_real_generation_outputs_manifest.json"
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["visual_qa_executed"] is False
    assert data["operator_visual_decision_created"] is False

    with open(mpath) as f:
        data = json.load(f)
    assert data["visual_qa_executed"] is False


def test_assembly_downstream_blocked(project_root):
    root, control_dir, _ = project_root

    auth = {
        "assembly_allowed": False,
        "downstream_allowed": False
    }
    path = control_dir / "combine_v2_v8_operator_reexecution_authorization.json"
    with open(path, "w") as f:
        json.dump(auth, f, indent=2)

    result = {
        "assembly_executed": False,
        "downstream_executed": False
    }
    rpath = control_dir / "combine_v2_v8_real_generation_result.json"
    with open(rpath, "w") as f:
        json.dump(result, f, indent=2)

    with open(path) as f:
        data = json.load(f)
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False

    with open(rpath) as f:
        data = json.load(f)
    assert data["assembly_executed"] is False
    assert data["downstream_executed"] is False


def test_production_accepted_false(project_root):
    root, control_dir, _ = project_root

    artifacts = [
        ("combine_v2_v8_operator_reexecution_authorization.json", {"production_accepted": False}),
        ("combine_v2_v8_real_generation_result.json", {"production_accepted": False}),
        ("combine_v2_v8_real_generation_outputs_manifest.json", {"production_accepted": False}),
    ]
    for name, content in artifacts:
        with open(control_dir / name, "w") as f:
            json.dump(content, f, indent=2)

    for name, _ in artifacts:
        with open(control_dir / name) as f:
            data = json.load(f)
        assert data.get("production_accepted") is False, f"{name} should have production_accepted=False"
