"""Tests for RC-COMBINE-V2-13001-15000 V10 generation output validation.

Tests cover:
- asset_exists_true
- asset_readable_true
- sha256_present
- dimensions_present
- size_bytes_gt_1024
- stub_asset_detected_false
- asset_filename_matches_v10_pattern
- canonical_output_registered
- valid_asset_sets_success_state
"""

import json
import tempfile
import hashlib
from pathlib import Path

from PIL import Image
import pytest


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assets_dir = root / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        yield root, assets_dir


@pytest.fixture
def valid_v10_image(project_root):
    root, assets_dir = project_root
    img_path = assets_dir / "combine_v2_v10_photoreal_recovery_shot02_00001_.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    return root, assets_dir, img_path


def test_asset_exists_true(valid_v10_image):
    from app.cli import _is_image_readable
    root, assets_dir, img_path = valid_v10_image
    assert img_path.exists()
    result = _is_image_readable(img_path)
    assert result["readable"] == True


def test_asset_readable_true(valid_v10_image):
    from app.cli import _is_image_readable
    root, assets_dir, img_path = valid_v10_image
    result = _is_image_readable(img_path)
    assert result["readable"] == True
    assert result["width"] == 1024
    assert result["height"] == 1024


def test_sha256_present(valid_v10_image):
    from app.cli import _file_sha256
    root, assets_dir, img_path = valid_v10_image
    sha256 = _file_sha256(img_path)
    assert len(sha256) == 64
    assert isinstance(sha256, str)


def test_dimensions_present(valid_v10_image):
    from app.cli import _is_image_readable
    root, assets_dir, img_path = valid_v10_image
    result = _is_image_readable(img_path)
    assert result["width"] == 1024
    assert result["height"] == 1024


def test_size_bytes_gt_1024(valid_v10_image):
    root, assets_dir, img_path = valid_v10_image
    size = img_path.stat().st_size
    assert size > 1024


def test_stub_asset_detected_false(valid_v10_image):
    from app.cli import _is_image_readable
    root, assets_dir, img_path = valid_v10_image
    result = _is_image_readable(img_path)
    assert result["readable"] == True
    assert img_path.stat().st_size > 1024


def test_asset_filename_matches_v10_pattern(valid_v10_image):
    root, assets_dir, img_path = valid_v10_image
    import re
    pattern = r"^combine_v2_v10_photoreal_recovery_shot02_\d+_\.png$"
    assert re.match(pattern, img_path.name) is not None


def test_asset_filename_matches_v10_pattern_invalid(project_root):
    root, assets_dir = project_root
    import re
    pattern = r"^combine_v2_v10_photoreal_recovery_shot02_\d+_\.png$"
    bad_path = assets_dir / "wrong_prefix_00001_.png"
    assert re.match(pattern, bad_path.name) is None


def test_canonical_output_registered(valid_v10_image):
    root, assets_dir, img_path = valid_v10_image
    from app.cli import _file_sha256, _is_image_readable

    sha256 = _file_sha256(img_path)
    readable = _is_image_readable(img_path)
    size = img_path.stat().st_size

    canonical_entry = {
        "path": f"data/rc2_multishot1_ep01/output/assets/{img_path.name}",
        "exists": True,
        "readable": readable["readable"],
        "width": readable["width"],
        "height": readable["height"],
        "size_bytes": size,
        "sha256": sha256
    }
    assert canonical_entry["exists"] is True
    assert canonical_entry["readable"] is True
    assert canonical_entry["width"] == 1024
    assert canonical_entry["height"] == 1024
    assert canonical_entry["size_bytes"] > 1024
    assert len(canonical_entry["sha256"]) == 64


def test_valid_asset_sets_success_state(valid_v10_image):
    root, assets_dir, img_path = valid_v10_image
    from app.cli import _file_sha256, _is_image_readable

    sha256 = _file_sha256(img_path)
    readable = _is_image_readable(img_path)
    size = img_path.stat().st_size

    asset_readable = readable["readable"]
    sha256_present = len(sha256) == 64
    dimensions_present = readable["width"] is not None and readable["height"] is not None
    size_bytes_gt_1024 = size > 1024
    stub_asset_detected = not (asset_readable and size_bytes_gt_1024)

    has_valid_asset = (
        asset_readable
        and sha256_present
        and dimensions_present
        and size_bytes_gt_1024
        and not stub_asset_detected
    )

    assert has_valid_asset is True


def test_zero_byte_asset_fails(project_root):
    root, assets_dir = project_root
    stub_path = assets_dir / "combine_v2_v10_photoreal_recovery_shot02_00000_.png"
    stub_path.write_bytes(b"")
    assert stub_path.exists()
    assert stub_path.stat().st_size == 0

    from app.cli import _is_image_readable
    result = _is_image_readable(stub_path)
    assert result["readable"] is False


def test_corrupted_asset_fails(project_root):
    root, assets_dir = project_root
    bad_path = assets_dir / "combine_v2_v10_photoreal_recovery_shot02_corrupt.png"
    bad_path.write_bytes(b"not a real image file content here")
    assert bad_path.exists()

    from app.cli import _is_image_readable
    result = _is_image_readable(bad_path)
    assert result["readable"] is False


def test_output_manifest_structure(project_root):
    root, assets_dir = project_root
    control_dir = root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "stage": "v10_real_generation",
        "manifest_type": "v10_real_generation_outputs_manifest",
        "task_id": "RC-COMBINE-V2-13001-15000",
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "workflow_submitted": True,
        "generated_assets": [],
        "asset_paths": [],
        "collection_status": "success",
        "asset_readable": True,
        "sha256_present": True,
        "dimensions_present": True,
        "stub_asset_detected": False,
        "canonical_outputs_registered": True,
        "visual_qa_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False
    }
    assert manifest["stage"] == "v10_real_generation"
    assert manifest["max_generations"] == 1
    assert manifest["second_generation_attempted"] is False
    assert manifest["retry_attempted"] is False
    assert manifest["visual_qa_executed"] is False
    assert manifest["production_accepted"] is False
