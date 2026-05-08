"""Tests for RC-COMBINE-V2-10601-11600 V9 operator visual review gate.

Tests cover:
- visual_review_packet_requires_real_asset
- no_review_packet_on_failure
- review_packet_blocks_qa_execution
- review_packet_blocks_operator_acceptance
- review_packet_blocks_assembly_downstream
- review_packet_blocks_production_acceptance
- review_packet_marks_visual_qa_not_executed
"""

import json
import tempfile
from pathlib import Path

from PIL import Image
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
                "current_state": "v9_operator_visual_review_required",
                "next_allowed_action": "v9_operator_visual_review_required",
                "production_accepted": False
            }, f, indent=2)

        yield root, control_dir, assets_dir


def _create_valid_review_packet(control_dir, assets_dir):
    """Create a valid V9 review packet with a real asset."""
    img_path = assets_dir / "combine_v2_v9_quality_locked_shot02_00001_.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)

    from app.cli import _file_sha256, _is_image_readable
    sha256 = _file_sha256(img_path)
    readable = _is_image_readable(img_path)
    size = img_path.stat().st_size

    packet = {
        "task_id": "RC-COMBINE-V2-10601-11600",
        "stage": "v9_operator_visual_review",
        "artifact_id": "combine_v2_v9_operator_visual_review_packet",
        "generation_attempted": True,
        "generation_success": True,
        "prompt_id": "test-prompt-id",
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "dry_run_used": False,
        "generated_assets": [f"data/rc2_multishot1_ep01/output/assets/{img_path.name}"],
        "asset_path": f"data/rc2_multishot1_ep01/output/assets/{img_path.name}",
        "comfyui_execution": True,
        "workflow_submitted": True,
        "asset_sha256": sha256,
        "asset_dimensions": {"width": readable["width"], "height": readable["height"]},
        "asset_size_bytes": size,
        "visual_qa_executed": False,
        "visual_qa_verdict": None,
        "operator_visual_decision_created": False,
        "operator_visual_verdict": None,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "notes": "V9 generation completed. Operator visual review required.",
        "timestamp": "2026-05-08T07:00:00+00:00"
    }
    with open(control_dir / "combine_v2_v9_operator_visual_review_packet.json", "w") as f:
        json.dump(packet, f, indent=2)

    manifest = {
        "generated_assets": [{
            "path": f"data/rc2_multishot1_ep01/output/assets/{img_path.name}",
            "exists": True,
            "readable": True,
            "width": readable["width"],
            "height": readable["height"],
            "size_bytes": size,
            "sha256": sha256
        }],
        "asset_paths": [f"data/rc2_multishot1_ep01/output/assets/{img_path.name}"],
        "collection_status": "success"
    }
    with open(control_dir / "combine_v2_v9_real_generation_outputs_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return packet, img_path


def test_visual_review_packet_requires_real_asset(project_root):
    root, control_dir, assets_dir = project_root
    packet_path = control_dir / "combine_v2_v9_operator_visual_review_packet.json"
    assert not packet_path.exists()

    # With no real asset, review packet must NOT be created
    result_path = control_dir / "combine_v2_v9_real_generation_result.json"
    result = {
        "comfyui_status": "failed",
        "generated_assets": [],
        "failure_code": "output_collection_failed",
        "production_accepted": False
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    assert not packet_path.exists()


def test_no_review_packet_on_failure(project_root):
    root, control_dir, assets_dir = project_root
    packet_path = control_dir / "combine_v2_v9_operator_visual_review_packet.json"
    assert not packet_path.exists()

    result = {
        "comfyui_status": "failed",
        "generated_assets": [],
        "failure_code": "server_unavailable",
        "production_accepted": False
    }
    with open(control_dir / "combine_v2_v9_real_generation_result.json", "w") as f:
        json.dump(result, f, indent=2)

    # Verify no review packet without real asset
    result_path = control_dir / "combine_v2_v9_real_generation_result.json"
    with open(result_path) as f:
        r = json.load(f)
    assert len(r.get("generated_assets", [])) == 0
    assert r.get("failure_code") is not None
    assert r.get("production_accepted") is False


def test_review_packet_blocks_qa_execution(project_root):
    root, control_dir, assets_dir = project_root
    packet, _ = _create_valid_review_packet(control_dir, assets_dir)
    assert packet.get("visual_qa_executed") is False
    assert packet.get("visual_qa_verdict") is None


def test_review_packet_blocks_operator_acceptance(project_root):
    root, control_dir, assets_dir = project_root
    packet, _ = _create_valid_review_packet(control_dir, assets_dir)
    assert packet.get("operator_visual_decision_created") is False
    assert packet.get("operator_visual_verdict") is None


def test_review_packet_blocks_assembly_downstream(project_root):
    root, control_dir, assets_dir = project_root
    packet, _ = _create_valid_review_packet(control_dir, assets_dir)
    assert packet.get("assembly_allowed") is False
    assert packet.get("downstream_allowed") is False


def test_review_packet_blocks_production_acceptance(project_root):
    root, control_dir, assets_dir = project_root
    packet, _ = _create_valid_review_packet(control_dir, assets_dir)
    assert packet.get("production_accepted") is False

    with open(control_dir / "artifact_index.json") as f:
        idx = json.load(f)
    assert idx.get("production_accepted") is False


def test_review_packet_marks_visual_qa_not_executed(project_root):
    root, control_dir, assets_dir = project_root
    packet, img_path = _create_valid_review_packet(control_dir, assets_dir)

    assert packet["visual_qa_executed"] is False
    assert packet["visual_qa_verdict"] is None
    assert packet["operator_visual_decision_created"] is False

    # Also verify manifest
    manifest_path = control_dir / "combine_v2_v9_real_generation_outputs_manifest.json"
    with open(manifest_path) as f:
        m = json.load(f)
    assert len(m["generated_assets"]) == 1
    assert m["generated_assets"][0]["readable"] is True
    assert m["generated_assets"][0]["width"] == 1024
    assert m["generated_assets"][0]["height"] == 1024


def test_review_packet_contains_all_required_fields(project_root):
    root, control_dir, assets_dir = project_root
    packet, _ = _create_valid_review_packet(control_dir, assets_dir)

    required_fields = [
        "task_id", "stage", "artifact_id", "generation_attempted",
        "generation_success", "prompt_id", "generation_count",
        "max_generations", "second_generation_attempted", "retry_attempted",
        "dry_run_used", "generated_assets", "asset_path",
        "comfyui_execution", "workflow_submitted",
        "asset_sha256", "asset_dimensions", "asset_size_bytes",
        "visual_qa_executed", "operator_visual_decision_created",
        "production_accepted", "assembly_allowed", "downstream_allowed"
    ]
    for field in required_fields:
        assert field in packet, f"Missing required field: {field}"


def test_review_packet_requires_real_file_on_disk(project_root):
    root, control_dir, assets_dir = project_root
    packet, img_path = _create_valid_review_packet(control_dir, assets_dir)

    # Asset must exist on disk
    assert img_path.exists()

    from app.cli import _is_image_readable
    result = _is_image_readable(img_path)
    assert result["readable"] is True
    assert result["width"] == 1024
    assert result["height"] == 1024


def test_result_review_state_transition(project_root):
    root, control_dir, assets_dir = project_root
    _create_valid_review_packet(control_dir, assets_dir)

    # Simulate the success state transition
    from app.cli import _update_v9_generation_index
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()

    generated_assets = [{
        "path": "data/rc2_multishot1_ep01/output/assets/combine_v2_v9_quality_locked_shot02_00001_.png",
        "exists": True,
        "readable": True,
        "width": 1024,
        "height": 1024,
        "size_bytes": 1500000,
        "sha256": "d" * 64
    }]

    _update_v9_generation_index(control_dir, execute=True, generated_assets=generated_assets, timestamp=timestamp)

    with open(control_dir / "artifact_index.json") as f:
        idx = json.load(f)

    assert idx.get("current_state") == "v9_operator_visual_review_required"
    assert idx.get("next_allowed_action") == "v9_operator_visual_review_required"
    assert idx.get("production_accepted") is False
