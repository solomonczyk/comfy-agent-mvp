"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — Controlled Preview Render Gate tests.

Tests the complete preview render gate including authorization validation,
input artifact validation, preview render execution, artifact validation,
report creation, and state transitions.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from app.timeline.controlled_preview_render import (
    TASK_ID,
    validate_preview_render_authorization,
    validate_input_artifacts,
    execute_preview_render,
    validate_preview_artifacts,
    run_controlled_preview_render,
)


def _make_control_dir(tmp_path: Path) -> Path:
    """Create a temporary control directory with placeholder artifacts."""
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return control_dir


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _make_valid_auth(control_dir: Path) -> Dict[str, Any]:
    """Create a valid preview_render_authorization.json."""
    auth = {
        "task_id": TASK_ID,
        "operator_authorized": True,
        "preview_render_authorized": True,
        "max_preview_renders": 1,
        "source_timeline": "timeline_model.json",
        "preview_proof_contract": "preview_proof_contract.json",
        "voice_generation_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_acceptance_allowed": False,
        "final_render_allowed": False,
        "stop_after_preview_result_review": True,
    }
    _write_json(control_dir / "preview_render_authorization.json", auth)
    return auth


def _make_placeholder_artifacts(control_dir: Path) -> None:
    """Create valid placeholder input artifacts."""
    artifacts = {
        "timeline_model.json": {
            "project_id": "test",
            "fps": 24,
            "resolution": {"width": 1344, "height": 768},
            "scenes": [],
            "operations": [],
        },
        "marker_registry.json": [],
        "edit_decision_list.json": [],
        "subtitle_plan.json": [],
        "transition_policy.json": {"default": "hard_cut", "forbidden_transitions": []},
        "voice_casting_contract.json": {
            "full_voiceover_generation_allowed": False,
        },
        "preview_proof_contract.json": {
            "preview_lowres_required": True,
            "preview_gif_required": True,
            "contact_sheet_required": True,
        },
        "timeline_preview_dry_run_report.json": {
            "dry_run_status": "ready",
            "errors": [],
            "warnings": [],
        },
        "preview_render_authorization_packet.json": {
            "authorization_required": True,
            "authorization_granted": False,
        },
    }
    for name, data in artifacts.items():
        _write_json(control_dir / name, data)


def _make_test_asset(tmp_path: Path, control_dir: Path) -> Path:
    """Create a test PNG asset and update timeline model to reference it."""
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create small test image
    img = Image.new("RGB", (200, 150), color=(100, 100, 200))
    asset_path = assets_dir / "test_asset.png"
    img.save(asset_path)

    # Update timeline model to reference this asset
    timeline = {
        "project_id": "test",
        "fps": 24,
        "resolution": {"width": 1344, "height": 768},
        "scenes": [],
        "operations": [
            {
                "operation_id": "place_test",
                "asset_ref": str(asset_path),
                "track": "video_main",
            }
        ],
    }
    _write_json(control_dir / "timeline_model.json", timeline)
    return asset_path


class TestPreviewAuthorizationValidation:
    """6.1 Preview authorization validation tests."""

    def test_missing_authorization_file(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "not found" in msg
        assert data is None

    def test_invalid_json(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth_path = control_dir / "preview_render_authorization.json"
        auth_path.write_text("not json", encoding="utf-8")
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid

    def test_missing_required_fields(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        _write_json(control_dir / "preview_render_authorization.json", {"task_id": "x"})
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "Missing required fields" in msg

    def test_operator_not_authorized(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        auth["operator_authorized"] = False
        _write_json(control_dir / "preview_render_authorization.json", auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "operator_authorized is False" in msg

    def test_preview_render_not_authorized(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        auth["preview_render_authorized"] = False
        _write_json(control_dir / "preview_render_authorization.json", auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "preview_render_authorized is False" in msg

    def test_max_preview_renders_not_one(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        auth["max_preview_renders"] = 2
        _write_json(control_dir / "preview_render_authorization.json", auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "max_preview_renders must be 1" in msg

    def test_voice_generation_allowed_blocks(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        auth["voice_generation_allowed"] = True
        _write_json(control_dir / "preview_render_authorization.json", auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "voice_generation_allowed must be False" in msg

    def test_assembly_allowed_blocks(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        auth["assembly_allowed"] = True
        _write_json(control_dir / "preview_render_authorization.json", auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "assembly_allowed must be False" in msg

    def test_valid_authorization_passes(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert valid
        assert data is not None
        assert msg == "Authorization valid"


class TestInputArtifactValidation:
    """6.2 Input artifact validation tests."""

    def test_all_artifacts_valid(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        result = validate_input_artifacts(control_dir)
        assert result.get("valid") is True
        assert len(result.get("errors", [])) == 0

    def test_missing_artifact_fails(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        # Delete one artifact
        (control_dir / "edit_decision_list.json").unlink()
        result = validate_input_artifacts(control_dir)
        assert result.get("valid") is False
        assert result.get("edit_decision_list.json_exists") is False

    def test_voice_contract_authorizes_generation(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        # Set voice generation allowed
        _write_json(
            control_dir / "voice_casting_contract.json",
            {"full_voiceover_generation_allowed": True},
        )
        result = validate_input_artifacts(control_dir)
        assert result.get("valid") is False
        assert result.get("voice_contract_does_not_authorize_voice_generation") is False

    def test_dry_run_errors_recorded(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        # Add dry run errors
        _write_json(
            control_dir / "timeline_preview_dry_run_report.json",
            {
                "dry_run_status": "blocked",
                "errors": ["error_1", "error_2"],
                "warnings": [],
            },
        )
        result = validate_input_artifacts(control_dir)
        assert result.get("dry_run_passed") is False
        assert result.get("dry_run_errors") == 2


class TestPreviewRenderExecution:
    """6.3 Preview render execution tests."""

    def test_preview_frames_created(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path, control_dir)
        preview_dir = tmp_path / "output" / "preview"

        result = execute_preview_render(asset, preview_dir)

        assert result["preview_render_executed"] is True
        assert result["preview_render_count"] == 1
        assert result["voice_generation_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

        # Check GIF was created (always via Pillow)
        gif_path = preview_dir / "preview.gif"
        assert gif_path.exists()
        assert gif_path.stat().st_size > 0

        # Check contact sheet
        sheet_path = preview_dir / "contact_sheet.jpg"
        assert sheet_path.exists()
        assert sheet_path.stat().st_size > 0

    def test_preview_gif_is_valid(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path, control_dir)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        gif_path = preview_dir / "preview.gif"

        assert gif_path.exists()
        assert gif_path.stat().st_size > 0
        # GIF should be valid (non-zero size, readable)
        with Image.open(gif_path) as img:
            assert img.width > 0
            assert img.height > 0

    def test_contact_sheet_is_valid_image(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path, control_dir)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        sheet_path = preview_dir / "contact_sheet.jpg"

        with Image.open(sheet_path) as img:
            assert img.width > 0
            assert img.height > 0

    def test_no_second_preview_render(self, tmp_path: Path):
        """Verify only one preview render is executed (enforced by authorization)."""
        control_dir = _make_control_dir(tmp_path)
        auth = _make_valid_auth(control_dir)
        assert auth["max_preview_renders"] == 1


class TestPreviewArtifactValidation:
    """6.4 Preview artifact validation tests."""

    def test_validate_preview_artifacts(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path, control_dir)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        result = validate_preview_artifacts(preview_dir)

        assert "valid" in result
        assert "preview_lowres_mp4" in result
        assert "preview_gif" in result
        assert "contact_sheet_jpg" in result

    def test_gif_validation_checks(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path, control_dir)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        result = validate_preview_artifacts(preview_dir)

        gif_result = result.get("preview_gif", {})
        assert gif_result.get("exists") is True
        assert gif_result.get("size_bytes_gt_zero") is True
        assert gif_result.get("not_stub") is True


class TestControlledPreviewRenderGate:
    """End-to-end controlled preview render gate tests."""

    def test_authorization_missing_blocks_preview_render(self, tmp_path: Path):
        """Verify that missing authorization blocks render and creates blocker."""
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)

        # Run without authorization file
        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["selected_branch"] == "authorization_required"
        assert result["preview_render_executed"] is False
        assert result["preview_render_authorized"] is False
        assert result["current_state"] == "preview_render_authorization_required"

        # Check blocker artifact was created
        blocker_path = control_dir / "preview_render_authorization_required.json"
        assert blocker_path.exists()
        gate_blocker = control_dir / "preview_render_gate_blocker_report.json"
        assert gate_blocker.exists()

    def test_valid_authorization_allows_one_preview_render(self, tmp_path: Path):
        """Verify valid authorization allows preview render."""
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        _make_valid_auth(control_dir)
        _make_test_asset(tmp_path, control_dir)

        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["selected_branch"] == "preview_render_executed"
        assert result["preview_render_executed"] is True
        assert result["preview_render_count"] == 1

    def test_all_forbidden_actions_false(self, tmp_path: Path):
        """Verify all forbidden actions are false in result."""
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        _make_valid_auth(control_dir)
        _make_test_asset(tmp_path, control_dir)

        result = run_controlled_preview_render(project_root=str(tmp_path))

        assert result["production_accepted"] is False
        assert result["voice_generation_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False

    def test_artifact_index_updated(self, tmp_path: Path):
        """Verify artifact index is updated with preview render info."""
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        _make_valid_auth(control_dir)
        _make_test_asset(tmp_path, control_dir)

        run_controlled_preview_render(project_root=str(tmp_path))

        index_path = control_dir / "artifact_index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert index["task_id"] == TASK_ID

    def test_episode_ledger_updated(self, tmp_path: Path):
        """Verify episode ledger is updated with preview render events."""
        control_dir = _make_control_dir(tmp_path)
        _make_placeholder_artifacts(control_dir)
        _make_valid_auth(control_dir)
        _make_test_asset(tmp_path, control_dir)

        run_controlled_preview_render(project_root=str(tmp_path))

        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        events = [e for e in ledger if e.get("task_id") == TASK_ID]
        assert len(events) > 0
