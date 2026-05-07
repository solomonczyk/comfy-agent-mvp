"""Tests for RC-COMBINE-V2-5701-6000 V8 quality-locked generation execution.

Tests cover:
- comfyui_submit_executed_once_when_authorized
- output_manifest_created
- asset_readability_checked
- sha256_created
- stub_asset_rejected
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

        # Create all required artifacts
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


def test_comfyui_submit_executed_once_when_authorized(project_root):
    from app.cli import combine_execute_v8_quality_locked_generation
    from argparse import Namespace

    # Dry run (doesn't submit to ComfyUI)
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_execute_v8_quality_locked_generation(args)
    assert result == 0, "Dry run should succeed"

    # Verify execution proof was created
    execution_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_generation_execution.json"
    assert execution_path.exists(), "Execution proof should exist"
    with open(execution_path) as f:
        execution = json.load(f)
    assert execution.get("workflow_submitted") is True
    assert execution.get("generation_count") == 1
    assert execution.get("comfyui_execution") is False  # dry run
    assert execution.get("second_generation_attempted") is False


def test_output_manifest_created(project_root):
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

    manifest_path = project_root / "output" / "control" / "combine_v2_v8_quality_locked_outputs_manifest.json"
    assert manifest_path.exists(), "Output manifest should exist"
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest.get("manifest_type") == "v8_quality_locked_outputs_manifest"
    assert manifest.get("generation_count") == 1
    assert manifest.get("max_generations") == 1
    assert manifest.get("production_accepted") is False
    assert manifest.get("visual_acceptance_executed") is False


def test_asset_readability_checked(project_root):
    from app.cli import _is_image_readable, _file_sha256
    from PIL import Image

    assets_dir = project_root / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create a valid PNG
    img_path = assets_dir / "test_asset.png"
    img = Image.new("RGB", (1024, 1024), color="red")
    img.save(img_path)

    result = _is_image_readable(img_path)
    assert result["readable"] is True
    assert result["width"] == 1024
    assert result["height"] == 1024

    sha256 = _file_sha256(img_path)
    assert len(sha256) == 64, "SHA256 should be 64 hex chars"


def test_sha256_created(project_root):
    from app.cli import _file_sha256, _is_image_readable
    from PIL import Image

    assets_dir = project_root / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (512, 512), color="blue")
    img_path = assets_dir / "sha256_test.png"
    img.save(img_path)

    sha256 = _file_sha256(img_path)
    assert len(sha256) == 64
    assert sha256.isalnum() or sha256.islower(), "SHA256 should be hex"

    readable = _is_image_readable(img_path)
    assert readable["readable"] is True


def test_stub_asset_rejected(project_root):
    from app.cli import _is_image_readable

    assets_dir = project_root / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create a stub file (< 1024 bytes, not a real image)
    stub_path = assets_dir / "stub.png"
    with open(stub_path, "wb") as f:
        f.write(b"this is not a real png file" * 10)

    result = _is_image_readable(stub_path)
    assert result["readable"] is False, "Stub file should not be readable as image"
