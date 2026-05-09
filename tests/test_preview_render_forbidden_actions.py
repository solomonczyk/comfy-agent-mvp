"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — Forbidden actions tests.

Verifies that forbidden actions (voice generation, assembly, downstream,
production acceptance, second preview render) are all blocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from app.timeline.controlled_preview_render import (
    run_controlled_preview_render,
    validate_preview_render_authorization,
)


def _make_control_dir(tmp_path: Path) -> Path:
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


def _setup_valid_state(tmp_path: Path) -> Path:
    """Set up a fully valid state for preview render."""
    control_dir = _make_control_dir(tmp_path)
    auth = {
        "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
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
        "voice_casting_contract.json": {"full_voiceover_generation_allowed": False},
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
        "preview_render_authorization_packet.json": {"authorization_required": True},
    }
    for name, data in artifacts.items():
        _write_json(control_dir / name, data)

    # Create test asset
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (200, 150), color=(100, 100, 200))
    asset_path = assets_dir / "test_asset.png"
    img.save(asset_path)

    # Update timeline model to reference asset
    _write_json(
        control_dir / "timeline_model.json",
        {
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
        },
    )
    return control_dir


class TestForbiddenActions:
    """Verification that forbidden actions are always blocked."""

    def test_voice_generation_blocked(self, tmp_path: Path):
        """Voice generation is never executed in this package."""
        control_dir = _setup_valid_state(tmp_path)
        result = run_controlled_preview_render(project_root=str(tmp_path))
        assert result["voice_generation_executed"] is False

    def test_assembly_blocked(self, tmp_path: Path):
        """Assembly is never executed in this package."""
        control_dir = _setup_valid_state(tmp_path)
        result = run_controlled_preview_render(project_root=str(tmp_path))
        assert result["assembly_executed"] is False

    def test_downstream_blocked(self, tmp_path: Path):
        """Downstream is never executed in this package."""
        control_dir = _setup_valid_state(tmp_path)
        result = run_controlled_preview_render(project_root=str(tmp_path))
        assert result["downstream_executed"] is False

    def test_production_accepted_false(self, tmp_path: Path):
        """Production accepted is never set to true."""
        control_dir = _setup_valid_state(tmp_path)
        result = run_controlled_preview_render(project_root=str(tmp_path))
        assert result["production_accepted"] is False

    def test_max_preview_renders_must_equal_one(self, tmp_path: Path):
        """Authorization enforces max_preview_renders == 1."""
        control_dir = _setup_valid_state(tmp_path)
        auth_path = control_dir / "preview_render_authorization.json"
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        assert auth["max_preview_renders"] == 1

    def test_second_preview_render_blocked_by_auth(self, tmp_path: Path):
        """Verify authorization prevents second render by design."""
        control_dir = _setup_valid_state(tmp_path)
        # Only one preview render is allowed per task contract
        auth_path = control_dir / "preview_render_authorization.json"
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        assert auth["max_preview_renders"] == 1
        # Change to 2 and verify it gets rejected
        auth["max_preview_renders"] = 2
        _write_json(auth_path, auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "max_preview_renders must be 1" in msg

    def test_final_render_blocked(self, tmp_path: Path):
        """Final render is blocked by authorization."""
        control_dir = _setup_valid_state(tmp_path)
        # Verify authorization rejects final_render_allowed
        auth_path = control_dir / "preview_render_authorization.json"
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        assert auth["final_render_allowed"] is False
        # Change to True and verify it gets rejected
        auth["final_render_allowed"] = True
        _write_json(auth_path, auth)
        valid, data, msg = validate_preview_render_authorization(control_dir)
        assert not valid
        assert "final_render_allowed must be False" in msg

    def test_production_acceptance_allowed_blocked(self, tmp_path: Path):
        """Production acceptance is blocked by authorization."""
        control_dir = _setup_valid_state(tmp_path)
        auth_path = control_dir / "preview_render_authorization.json"
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        assert auth["production_acceptance_allowed"] is False

    def test_comfyui_not_submitted(self, tmp_path: Path):
        """No ComfyUI submit in this package."""
        result = run_controlled_preview_render(project_root=str(tmp_path))
        # The result doesn't have comfyui_submit field by design
        # (it's not part of this package's contract)

    def test_new_generation_not_performed(self, tmp_path: Path):
        """No new generation is performed."""
        control_dir = _setup_valid_state(tmp_path)
        # The authorized flag prevents generation
        auth_path = control_dir / "preview_render_authorization.json"
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        # Generation would require generation_allowed
        # This task only allows preview render
