"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001 — Tests for controlled preview re-render authorization.

Validates that re-render is blocked without human operator authorization artifact.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any


def _make_project(tmp_path: Path, with_authorization: bool = False) -> Path:
    """Create a mock project with optional authorization."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = tmp_path / "output" / "editorial"
    preview_dir = tmp_path / "output" / "previews"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Required correction plan artifacts
    _write_json(control_dir / "preview_correction_plan.json", {
        "plan_type": "preview_correction_plan",
        "correction_goal": "test",
        "next_gate_required": "controlled_preview_rerender_authorization_required",
    })
    _write_json(control_dir / "preview_repair_contract.json", {
        "contract_type": "preview_repair_contract",
        "governs_render_type": "controlled_preview_rerender",
    })
    _write_json(control_dir / "static_preview_prevention_policy.json", {
        "policy_type": "static_preview_prevention_policy",
        "duplicate_frame_threshold": 0.85,
    })
    _write_json(control_dir / "controlled_preview_rerender_gate_package.json", {
        "gate_type": "controlled_preview_rerender_authorization",
        "render_authorized_now": False,
        "requires_operator_authorization": True,
        "max_preview_renders_after_authorization": 1,
    })

    # Editorial layer
    _write_json(editorial_dir / "timeline_model.json", {
        "tracks": {"video_main": [{"clip_id": "clip_001"}], "video_overlay": []},
        "scenes": [{"scene_id": "scene_001", "asset_refs": ["data/assets/test_asset.png"]}],
    })
    _write_json(editorial_dir / "edit_decision_list.json", [
        {"operation": "add_clip", "scene_id": "scene_001", "source": "test_asset.png"},
    ])

    # Approved asset manifest
    _write_json(control_dir / "approved_visual_assets_manifest.json", {
        "approved_assets": [{"path": str(tmp_path / "output" / "assets" / "test_asset.png")}],
    })

    # Create a dummy asset
    (tmp_path / "output" / "assets").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "output" / "assets" / "test_asset.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    # Create artifact_index.json
    _write_json(control_dir / "artifact_index.json", {
        "current_state": "controlled_preview_rerender_authorization_required",
        "next_allowed_action": "controlled_preview_rerender_authorization_required",
    })

    if with_authorization:
        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": True,
            "max_preview_renders": 1,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
        })

    return tmp_path


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestControlledPreviewRerenderAuthorization:

    def test_render_blocked_without_authorization(self, tmp_path: Path):
        """Re-render is blocked when operator authorization artifact does not exist."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["preview_render_count"] == 0
        assert result["status"] == "blocked"
        assert result["selected_branch"] == "preflight_blocked"
        assert result["authorized"] is False

    def test_render_blocked_with_authorization_false(self, tmp_path: Path):
        """Re-render is blocked when operator authorization has authorized=False."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        control_dir = Path(project_root) / "output" / "control"

        # Write authorization with authorized=False
        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": False,
            "max_preview_renders": 1,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
        })

        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["authorized"] is False
        assert result["status"] == "blocked"

    def test_render_blocked_with_wrong_max_renders(self, tmp_path: Path):
        """Re-render is blocked when max_preview_renders is not 1."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        control_dir = Path(project_root) / "output" / "control"

        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": True,
            "max_preview_renders": 2,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
        })

        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["authorized"] is False
        assert result["status"] == "blocked"

    def test_render_blocked_with_voice_allowed(self, tmp_path: Path):
        """Re-render is blocked when voice_generation_allowed is True in authorization."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        control_dir = Path(project_root) / "output" / "control"

        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": True,
            "max_preview_renders": 1,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": True,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
        })

        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["authorized"] is False
        assert result["status"] == "blocked"

    def test_render_blocked_with_assembly_allowed(self, tmp_path: Path):
        """Re-render is blocked when assembly_allowed is True in authorization."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        control_dir = Path(project_root) / "output" / "control"

        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": True,
            "max_preview_renders": 1,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": True,
            "downstream_allowed": False,
            "production_accepted": False,
        })

        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["authorized"] is False
        assert result["status"] == "blocked"

    def test_render_blocked_with_production_accepted(self, tmp_path: Path):
        """Re-render is blocked when production_accepted is True in authorization."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path, with_authorization=False))
        control_dir = Path(project_root) / "output" / "control"

        _write_json(control_dir / "controlled_preview_rerender_operator_authorization.json", {
            "authorization_type": "controlled_preview_rerender",
            "authorized_by": "human_operator",
            "authorized": True,
            "max_preview_renders": 1,
            "target_state_before": "controlled_preview_rerender_authorization_required",
            "allowed_action": "controlled_preview_rerender",
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": True,
        })

        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_executed"] is False
        assert result["authorized"] is False
        assert result["status"] == "blocked"
