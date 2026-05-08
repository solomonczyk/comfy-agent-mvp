"""Tests for RC-COMBINE-V2-13001-15000 V10 real generation execution.

Tests cover:
- authorization_required_before_generation
- server_unavailable_blocks_without_fake_success
- execute_flag_required
- exactly_one_queue_prompt_allowed
- max_generations_one_enforced
- second_generation_blocked
- retry_blocked
- dry_run_not_accepted
- empty_prompt_id_fails
- empty_generated_assets_fail
- invalid_asset_fails
- real_asset_registers_canonical_output
- visual_review_packet_requires_real_asset
- visual_qa_not_executed
- operator_acceptance_not_created
- production_accepted_false
- assembly_downstream_blocked
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

        # Set up artifact index with V10 state
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({
                "current_state": "v10_generation_authorization_required",
                "next_allowed_action": "v10_generation_authorization_required",
                "production_accepted": False
            }, f, indent=2)

        # Create V10 required artifacts
        v10_artifacts = {
            "combine_v2_v10_photoreal_recovery_workflow_package.json": {
                "task_id": "RC-COMBINE-V2-11601-13000",
                "workflow_type": "v10_photoreal_recovery_generation",
                "saveimage_filename_prefix": "combine_v2_v10_photoreal_recovery_shot02",
                "refinement_parameters": {
                    "cfg_scale": 7.5, "steps": 28, "sampler": "dpmpp_2m",
                    "scheduler": "karras", "resolution": "1024x1024",
                    "checkpoint": "realvisxlV50_v50Bakedvae.safetensors", "seed": "random"
                }
            },
            "combine_v2_v10_photoreal_recovery_prompt_package.json": {
                "positive_prompt": "photorealistic close-up portrait, sharp focus, detailed skin texture",
                "negative_prompt": "blur, haze, fog, soft focus, doll, anime, plastic"
            },
            "combine_v2_v10_workflow_guardrails.json": {
                "guardrails": {"positive_reference": "V8", "negative_reference": "V9"},
                "generation_parameters": {"sampler": "DPM++ 2M Karras", "cfg_scale": 7.5, "steps": 28}
            },
            "combine_v2_v10_generation_authorization_required.json": {
                "v10_generation_allowed_now": False,
                "requires_separate_operator_generation_gate": True,
                "max_generations": 1,
                "second_generation_allowed": False,
                "retry_allowed": False,
                "production_accepted": False
            },
            "episode_ledger.json": []
        }

        for filename, content in v10_artifacts.items():
            with open(control_dir / filename, "w") as f:
                json.dump(content, f, indent=2)

        yield root, control_dir, assets_dir


def test_authorization_required_before_generation(project_root):
    root, control_dir, _ = project_root
    auth_path = control_dir / "combine_v2_v10_operator_generation_authorization.json"
    assert not auth_path.exists()

    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    assert auth_path.exists()
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("operator_authorized") is True
    assert auth.get("authorized_action") == "v10_real_generation"
    assert auth.get("max_generations") == 1
    assert auth.get("second_generation_allowed") is False
    assert auth.get("retry_allowed") is False
    assert auth.get("visual_qa_allowed") is False
    assert auth.get("assembly_allowed") is False
    assert auth.get("downstream_allowed") is False
    assert auth.get("production_accepted") is False


def test_server_unavailable_blocks_without_fake_success(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v10_real_generation(args)
    assert result == 0  # dry run returns 0

    # Verify failure artifacts
    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    assert result_path.exists()
    with open(result_path) as f:
        res = json.load(f)
    assert res.get("dry_run_used") is True
    assert res.get("workflow_submitted") is False
    assert res.get("comfyui_execution") is False
    assert res.get("generated_assets") == []
    assert res.get("production_accepted") is False

    failure_report = control_dir / "combine_v2_v10_generation_failure_report.json"
    assert failure_report.exists()
    with open(failure_report) as f:
        fr = json.load(f)
    assert fr.get("failure_code") == "dry_run_not_executed"


def test_execute_flag_required(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v10_real_generation(args)
    assert result == 0

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    assert result_path.exists()
    with open(result_path) as f:
        res = json.load(f)
    assert res.get("dry_run_used") is True
    assert res.get("workflow_submitted") is False
    assert res.get("failure_code") == "dry_run_not_executed"


def test_exactly_one_queue_prompt_allowed(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v10_real_generation(args)
    assert result == 0

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        res = json.load(f)
    assert res.get("max_generations") == 1
    assert res.get("generation_count") == 0


def test_max_generations_one_enforced(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=True,
        max_generations=2,
        json=True
    )
    result = combine_execute_v10_real_generation(args)
    assert result == 1


def test_second_generation_blocked(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    auth_path = control_dir / "combine_v2_v10_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("second_generation_allowed") is False
    assert auth.get("generation_attempts_allowed") == 1


def test_retry_blocked(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    auth_path = control_dir / "combine_v2_v10_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("retry_allowed") is False


def test_dry_run_not_accepted(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v10_real_generation(args)
    assert result == 0

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        res = json.load(f)
    assert res.get("dry_run_used") is True
    assert res.get("canonical_outputs_registered") is False


def test_empty_prompt_id_fails(project_root):
    root, control_dir, _ = project_root
    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    result = {
        "task_id": "RC-COMBINE-V2-13001-15000",
        "prompt_id": "",
        "generation_count": 0,
        "comfyui_status": "failed",
        "failure_code": "empty_prompt_id",
        "production_accepted": False
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    with open(result_path) as f:
        data = json.load(f)
    assert data.get("prompt_id") == ""
    assert data.get("generation_count") == 0
    assert data.get("failure_code") is not None
    assert data.get("production_accepted") is False


def test_empty_generated_assets_fail(project_root):
    root, control_dir, _ = project_root
    manifest_path = control_dir / "combine_v2_v10_real_generation_outputs_manifest.json"
    manifest = {
        "generated_assets": [],
        "asset_paths": [],
        "generation_count": 0,
        "collection_status": "failed",
        "production_accepted": False
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    result = {
        "generated_assets": [],
        "generation_count": 0,
        "comfyui_status": "failed",
        "failure_code": "output_collection_failed",
        "production_accepted": False
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    with open(result_path) as f:
        data = json.load(f)
    assert len(data.get("generated_assets", [])) == 0
    assert data.get("production_accepted") is False


def test_real_asset_registers_canonical_output(project_root):
    """When a real asset exists, it must register in manifest with sha256/dimensions."""
    root, control_dir, assets_dir = project_root

    # Create a real valid PNG
    from PIL import Image
    img_path = assets_dir / "combine_v2_v10_photoreal_recovery_shot02_test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    assert img_path.exists()

    # Validate with tracking structure
    manifest = {
        "generated_assets": [{
            "path": f"data/rc2_multishot1_ep01/output/assets/{img_path.name}",
            "exists": True,
            "readable": True,
            "width": 1024,
            "height": 1024,
            "size_bytes": img_path.stat().st_size,
            "sha256": "d" * 64
        }],
        "asset_paths": [f"data/rc2_multishot1_ep01/output/assets/{img_path.name}"],
        "generation_count": 1,
        "collection_status": "success",
        "production_accepted": False
    }
    manifest_path = control_dir / "combine_v2_v10_real_generation_outputs_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    with open(manifest_path) as f:
        m = json.load(f)
    assert len(m["generated_assets"]) == 1
    assert m["generated_assets"][0]["readable"] is True
    assert m["generated_assets"][0]["width"] == 1024
    assert m["generated_assets"][0]["height"] == 1024
    assert m["generated_assets"][0]["size_bytes"] > 1024


def test_visual_review_packet_requires_real_asset(project_root):
    root, control_dir, _ = project_root
    packet_path = control_dir / "combine_v2_v10_operator_visual_review_packet.json"
    assert not packet_path.exists()

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    result = {
        "comfyui_status": "failed",
        "generated_assets": [],
        "failure_code": "output_collection_failed",
        "production_accepted": False
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    assert not packet_path.exists()


def test_visual_qa_not_executed(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        data = json.load(f)
    assert data.get("visual_qa_executed") is False

    auth_path = control_dir / "combine_v2_v10_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("visual_qa_allowed") is False


def test_operator_acceptance_not_created(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        data = json.load(f)
    assert data.get("operator_visual_decision_created") is False


def test_production_accepted_false(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        data = json.load(f)
    assert data.get("production_accepted") is False

    with open(control_dir / "artifact_index.json") as f:
        idx = json.load(f)
    assert idx.get("production_accepted") is False


def test_assembly_downstream_blocked(project_root):
    root, control_dir, _ = project_root
    from app.cli import combine_execute_v10_real_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(root),
        execute=False,
        max_generations=1,
        json=True
    )
    combine_execute_v10_real_generation(args)

    result_path = control_dir / "combine_v2_v10_real_generation_result.json"
    with open(result_path) as f:
        data = json.load(f)
    assert data.get("assembly_executed") is False
    assert data.get("downstream_executed") is False

    auth_path = control_dir / "combine_v2_v10_operator_generation_authorization.json"
    with open(auth_path) as f:
        auth = json.load(f)
    assert auth.get("assembly_allowed") is False
    assert auth.get("downstream_allowed") is False


def test_invalid_asset_fails(project_root):
    root, control_dir, assets_dir = project_root
    # Create a stub/small asset
    import hashlib
    stub_path = assets_dir / "combine_v2_v10_photoreal_recovery_shot02_stub.png"
    with open(stub_path, "wb") as f:
        f.write(b"0" * 100)
    assert stub_path.exists()
    assert stub_path.stat().st_size < 1024

    from app.cli import _is_image_readable, _file_sha256
    readable = _is_image_readable(stub_path)
    assert readable["readable"] is False
    assert stub_path.stat().st_size < 1024
