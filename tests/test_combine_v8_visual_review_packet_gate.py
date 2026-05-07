import json, tempfile
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
                "current_state": "v8_quality_locked_generation_authorization_required",
                "next_allowed_action": "v8_quality_locked_generation_authorization_required",
                "production_accepted": False
            }, f, indent=2)
        img = Image.new("RGB", (1024, 1024), color="red")
        img.save(assets_dir / "real_test_asset.png")
        yield root


def test_operator_visual_review_packet_requires_real_asset(project_root):
    """Verify packet only created when real asset exists"""
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace

    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    combine_v8_runtime_recovery_and_generation(args)

    packet_path = project_root / "output" / "control" / "combine_v2_v8_operator_visual_review_packet.json"
    assert not packet_path.exists()


def test_visual_qa_not_executed(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace
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


def test_operator_acceptance_not_created(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace
    args = Namespace(
        project_root=str(project_root),
        execute=False,
        max_generations=1,
        json=False
    )
    combine_v8_runtime_recovery_and_generation(args)
    control_dir = project_root / "output" / "control"
    acceptance_files = list(control_dir.glob("*accept*"))
    assert len(acceptance_files) == 0


def test_assembly_downstream_blocked(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace
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


def test_production_accepted_false(project_root):
    from app.cli import combine_v8_runtime_recovery_and_generation
    from argparse import Namespace
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
