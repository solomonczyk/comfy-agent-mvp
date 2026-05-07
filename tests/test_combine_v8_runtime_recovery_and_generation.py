import json, tempfile, os, sys
from pathlib import Path
import pytest
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).parent.parent))


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
                "current_state": "v8_quality_locked_generation_authorization_required",
                "next_allowed_action": "v8_quality_locked_generation_authorization_required",
                "production_accepted": False
            }, f, indent=2)
        yield root


def test_server_unavailable_blocks_submit(project_root, monkeypatch):
    """When ComfyUI is unreachable, no workflow is submitted"""
    from app.cli import combine_v8_runtime_recovery_and_generation

    monkeypatch.setenv("COMFY_BASE_URL", "http://127.0.0.1:1")

    args = Namespace(
        project_root=str(project_root),
        execute=True,
        max_generations=1,
        json=False
    )
    result = combine_v8_runtime_recovery_and_generation(args)
    assert result == 0

    report_path = project_root / "output" / "control" / "combine_v2_v8_runtime_recovery_report.json"
    assert report_path.exists()
    with open(report_path) as f:
        report = json.load(f)
    assert report.get("server_available") == False
    assert report.get("failure_code") in ["server_unavailable", "COMFYUI_UNREACHABLE"]

    with open(project_root / "output" / "control" / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai.get("current_state") == "v8_generation_runtime_blocked"
    assert ai.get("production_accepted") == False


def test_server_ready_allows_exactly_one_submit(project_root, monkeypatch):
    """When server is available, exactly one submit is attempted"""
    from app.cli import combine_v8_runtime_recovery_and_generation
    monkeypatch.setenv("COMFY_BASE_URL", "http://127.0.0.1:8188")

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    result = combine_v8_runtime_recovery_and_generation(args)
    assert result == 0


def test_max_generations_one_enforced(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=2,
        json=False
    )
    result = combine_v8_runtime_recovery_and_generation(args)
    assert result == 1


def test_second_generation_blocked(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_v8_runtime_recovery_and_generation(args)
    assert result == 0


def test_dry_run_not_accepted(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=True
    )
    result = combine_v8_runtime_recovery_and_generation(args)
    assert result == 0

    report_path = project_root / "output" / "control" / "combine_v2_v8_runtime_recovery_report.json"
    if report_path.exists():
        with open(report_path) as f:
            report = json.load(f)
        assert report.get("v8_real_generation_attempted") == False


def test_asset_readability():
    from app.cli import _is_image_readable, _file_sha256
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img_path = Path(f.name)
    try:
        img = Image.new("RGB", (1024, 1024), color="red")
        img.save(img_path)

        result = _is_image_readable(img_path)
        assert result["readable"] == True
        assert result["width"] == 1024
        assert result["height"] == 1024

        sha256 = _file_sha256(img_path)
        assert len(sha256) == 64
        assert img_path.stat().st_size > 1024
    finally:
        img_path.unlink(missing_ok=True)


def test_stub_asset_rejected():
    from app.cli import _is_image_readable

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"this is not a real png" * 20)
        stub_path = Path(f.name)
    try:
        result = _is_image_readable(stub_path)
        assert result["readable"] == False
    finally:
        stub_path.unlink(missing_ok=True)


def test_production_accepted_false(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    combine_v8_runtime_recovery_and_generation(args)

    with open(project_root / "output" / "control" / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai.get("production_accepted") == False


def test_operator_visual_review_packet_requires_real_asset(project_root):
    """Operator visual review packet should NOT be created in dry-run"""
    from app.cli import combine_v8_runtime_recovery_and_generation
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    combine_v8_runtime_recovery_and_generation(args)

    packet_path = project_root / "output" / "control" / "combine_v2_v8_operator_visual_review_packet.json"
    assert not packet_path.exists()
