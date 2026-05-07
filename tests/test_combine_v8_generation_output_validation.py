import json, tempfile, hashlib
from pathlib import Path
from PIL import Image
import pytest


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assets_dir = root / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        yield root


def test_asset_exists_true(project_root):
    from app.cli import _is_image_readable
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    assert img_path.exists()
    result = _is_image_readable(img_path)
    assert result["readable"] == True


def test_asset_readable_true(project_root):
    from app.cli import _is_image_readable
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    result = _is_image_readable(img_path)
    assert result["readable"] == True


def test_sha256_present(project_root):
    from app.cli import _file_sha256
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    sha256 = _file_sha256(img_path)
    assert len(sha256) == 64


def test_dimensions_present(project_root):
    from app.cli import _is_image_readable
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    result = _is_image_readable(img_path)
    assert result["width"] == 1024
    assert result["height"] == 1024


def test_size_bytes_gt_1024(project_root):
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    assert img_path.stat().st_size > 1024


def test_stub_asset_detected_false(project_root):
    from app.cli import _is_image_readable
    img_path = project_root / "output" / "assets" / "test.png"
    img = Image.new("RGB", (1024, 1024))
    img.save(img_path)
    result = _is_image_readable(img_path)
    assert result["readable"] == True
    assert img_path.stat().st_size > 1024


def test_visual_qa_not_executed(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump({
            "current_state": "v8_quality_locked_generation_authorization_required",
            "next_allowed_action": "v8_quality_locked_generation_authorization_required",
            "production_accepted": False
        }, f, indent=2)
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    combine_v8_runtime_recovery_and_generation(args)
    with open(control_dir / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai.get("production_accepted") == False
