"""Tests for combine corrective retry V4 visual QA preflight.

RC-COMBINE-V2-2481-2540 — Visual QA preflight for V4 canonical real asset.
"""

import json
import pytest
from pathlib import Path
import argparse


CANONICAL_ASSET_FILENAME = "combine_v2_corrective_retry_v4_shot02_00001_.png"
CANONICAL_ASSET_RELATIVE = "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"


def _make_project(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return project_root, control_dir, assets_dir


def _write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)


def _real_asset(assets_dir, size=2048):
    """Write a real (non-stub) asset."""
    path = assets_dir / CANONICAL_ASSET_FILENAME
    path.write_bytes(b"X" * size)
    return path


def _default_manifest(asset_relative=CANONICAL_ASSET_RELATIVE):
    return {
        "generated_assets": [asset_relative],
        "asset_count": 1,
        "stub_asset": False,
        "sha256": None,
    }


def _default_result_review():
    return {
        "branch_selected": "success",
        "manifest_success_policy_passed": True,
        "stub_asset_detected": False,
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
    }


def _make_args(project_root, shot_id="shot02", json_out=True):
    return argparse.Namespace(
        project_root=str(project_root),
        shot_id=shot_id,
        json=json_out,
    )


# ── Success branch ──────────────────────────────────────────────────────────

def test_canonical_asset_success_branch(tmp_path):
    """Test successful preflight with canonical real V4 asset."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 0

    preflight_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json"
    assert preflight_path.exists()
    with open(preflight_path) as f:
        pf = json.load(f)
    assert pf["visual_qa_preflight_executed"] is True
    assert pf["full_visual_qa_verdict_executed"] is False
    assert pf["operator_visual_review_executed"] is False
    assert pf["generation_performed"] is False
    assert pf["comfyui_execution"] is False
    assert pf["assembly_executed"] is False
    assert pf["downstream_executed"] is False
    assert pf["production_accepted"] is False
    assert pf["next_allowed_action"] == "corrective_retry_v4_visual_qa_required"
    assert pf["canonical_asset_path"] == CANONICAL_ASSET_RELATIVE


def test_visual_qa_input_packet_created(tmp_path):
    """Test that Visual QA input packet is created with required fields."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 0

    packet_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
    assert packet_path.exists()
    with open(packet_path) as f:
        packet = json.load(f)

    assert packet["shot_id"] == "shot02"
    assert packet["canonical_asset_path"] == CANONICAL_ASSET_RELATIVE
    assert packet["sha256"] is not None
    assert packet["file_size_bytes"] > 1024
    assert "technical_validation" in packet
    assert "operator_visual_concerns" in packet
    assert packet["operator_visual_concerns_recorded"] is True
    assert "subject_too_small" in packet["operator_visual_concerns"]
    assert "excessive_empty_space" in packet["operator_visual_concerns"]
    assert "weak_composition" in packet["operator_visual_concerns"]
    assert "shot_intent_not_satisfied" in packet["operator_visual_concerns"]
    assert "prompt_scene_alignment_weak" in packet["operator_visual_concerns"]
    assert packet["production_accepted"] is False
    assert packet["full_visual_qa_verdict_executed"] is False
    assert packet["operator_visual_review_executed"] is False


def test_artifact_index_updated(tmp_path):
    """Test artifact_index.json is updated correctly."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai["current_state"] == "corrective_retry_v4_visual_qa_preflight_required"
    assert ai["next_allowed_action"] == "corrective_retry_v4_visual_qa_required"
    assert ai["visual_qa_preflight_executed"] is True
    assert ai["visual_qa_input_packet_created"] is True
    assert ai["production_accepted"] is False
    assert ai["downstream_blocked"] is True


def test_state_transition_correct(tmp_path):
    """Test next_allowed_action is not none and is correct."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai["next_allowed_action"] != "none"
    assert ai["next_allowed_action"] == "corrective_retry_v4_visual_qa_required"


def test_episode_ledger_updated(tmp_path):
    """Test episode_ledger.json has new event appended."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "episode_ledger.json") as f:
        ledger = json.load(f)
    assert isinstance(ledger, list)
    assert len(ledger) > 0
    last = ledger[-1]
    assert last["event_type"] == "corrective_retry_v4_visual_qa_preflight_executed"
    assert last["task_id"] == "RC-COMBINE-V2-2481-2540"
    assert last["canonical_asset_path"] == CANONICAL_ASSET_RELATIVE
    assert last["next_allowed_action"] == "corrective_retry_v4_visual_qa_required"
    assert last["production_accepted"] is False


# ── Failure branches ─────────────────────────────────────────────────────────

def test_missing_asset_failure_branch(tmp_path):
    """Test blocker when canonical asset file does not exist on filesystem."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    # Do NOT create the asset file
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 1


def test_unreadable_asset_failure_branch(tmp_path):
    """Test blocker when asset is 0 bytes (unreadable / stub)."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    # Write empty file — treated as unreadable stub
    (assets_dir / CANONICAL_ASSET_FILENAME).write_bytes(b"")
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 1


def test_stub_asset_rejected(tmp_path):
    """Test blocker when asset size <= 1024 bytes (stub)."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    (assets_dir / CANONICAL_ASSET_FILENAME).write_bytes(b"stub" * 8)  # 32 bytes — stub
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 1


def test_old_shot01_asset_rejected(tmp_path):
    """Test blocker when manifest references a shot01 asset instead of shot02."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    shot01_asset = "output/assets/combine_v2_corrective_retry_v4_shot01_00001_.png"
    (assets_dir / "combine_v2_corrective_retry_v4_shot01_00001_.png").write_bytes(b"X" * 2048)
    manifest = _default_manifest(asset_relative=shot01_asset)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", manifest)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 1


def test_manifest_canonical_asset_mismatch_rejected(tmp_path):
    """Test blocker when manifest asset doesn't match canonical V4 filename."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    wrong_asset = "output/assets/combine_v2_some_other_asset_00001_.png"
    (assets_dir / "combine_v2_some_other_asset_00001_.png").write_bytes(b"X" * 2048)
    manifest = _default_manifest(asset_relative=wrong_asset)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", manifest)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    result = combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))
    assert result == 1


# ── Hard-boundary proof flags ────────────────────────────────────────────────

def test_full_visual_qa_verdict_not_executed(tmp_path):
    """Test that full visual QA verdict is not executed during preflight."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json") as f:
        pf = json.load(f)
    assert pf["full_visual_qa_verdict_executed"] is False


def test_operator_visual_review_not_executed(tmp_path):
    """Test that operator visual review is not executed during preflight."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json") as f:
        pf = json.load(f)
    assert pf["operator_visual_review_executed"] is False


def test_generation_forbidden(tmp_path):
    """Test that generation is not performed during preflight."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json") as f:
        pf = json.load(f)
    assert pf["generation_performed"] is False
    assert pf["comfyui_execution"] is False


def test_assembly_downstream_forbidden(tmp_path):
    """Test that assembly and downstream are not executed during preflight."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json") as f:
        pf = json.load(f)
    assert pf["assembly_executed"] is False
    assert pf["downstream_executed"] is False


def test_production_accepted_false(tmp_path):
    """Test that production_accepted is always False after preflight."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json") as f:
        pf = json.load(f)
    with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json") as f:
        packet = json.load(f)
    with open(control_dir / "artifact_index.json") as f:
        ai = json.load(f)

    assert pf["production_accepted"] is False
    assert packet["production_accepted"] is False
    assert ai["production_accepted"] is False


def test_next_allowed_action_not_none(tmp_path):
    """Test that next_allowed_action is never 'none'."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    project_root, control_dir, assets_dir = _make_project(tmp_path)
    _real_asset(assets_dir)
    _write_json(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", _default_manifest())
    _write_json(control_dir / "combine_v2_corrective_retry_v4_result_review.json", _default_result_review())

    combine_preflight_corrective_retry_v4_visual_qa(_make_args(project_root))

    with open(control_dir / "artifact_index.json") as f:
        ai = json.load(f)
    assert ai.get("next_allowed_action") not in (None, "none", "")
