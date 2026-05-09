"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RERENDER-001 — Tests for controlled preview re-render execution.

Validates that exactly one preview re-render is executed and
second render attempts are blocked.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any

from PIL import Image


def _make_project(tmp_path: Path) -> Path:
    """Create a mock project directory with valid authorization."""
    control_dir = tmp_path / "output" / "control"
    editorial_dir = tmp_path / "output" / "editorial"
    preview_dir = tmp_path / "output" / "previews"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    editorial_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Required correction plan artifacts
    _write_json(control_dir / "preview_correction_plan.json", {"plan_type": "preview_correction_plan"})
    _write_json(control_dir / "preview_repair_contract.json", {"contract_type": "preview_repair_contract"})
    _write_json(control_dir / "static_preview_prevention_policy.json", {"policy_type": "static_preview_prevention_policy"})
    _write_json(control_dir / "controlled_preview_rerender_gate_package.json", {"gate_type": "controlled_preview_rerender_authorization"})

    # Operator authorization
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

    # Editorial layer
    _write_json(editorial_dir / "timeline_model.json", {
        "tracks": {"video_main": [{"clip_id": "clip_001"}], "video_overlay": []},
        "scenes": [{"scene_id": "scene_001", "asset_refs": ["output/assets/test_asset.png"]}],
    })
    _write_json(editorial_dir / "edit_decision_list.json", [
        {"operation": "add_clip", "scene_id": "scene_001", "source": "test_asset.png"},
    ])

    # Approved asset manifest
    _write_json(control_dir / "approved_visual_assets_manifest.json", {
        "approved_assets": [{"path": str(assets_dir / "test_asset.png")}],
    })

    # Create a valid PNG for preview rendering using PIL
    img = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), color=(128, 128, 128))
    img.save(assets_dir / "test_asset.png")

    # Artifact index
    _write_json(control_dir / "artifact_index.json", {
        "current_state": "controlled_preview_rerender_authorization_required",
        "next_allowed_action": "controlled_preview_rerender_authorization_required",
    })

    return tmp_path


PREVIEW_WIDTH = 672
PREVIEW_HEIGHT = 384


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestControlledPreviewRerenderExecution:

    def test_exactly_one_preview_render_allowed(self, tmp_path: Path):
        """Exactly one preview re-render is executed."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True, max_renders=1)

        assert result["preview_render_executed"] is True
        assert result["preview_render_count"] == 1
        assert result["second_preview_render_attempted"] is False

    def test_render_blocked_if_execute_false(self, tmp_path: Path):
        """Re-render is not executed when execute=False."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=False)

        assert result["preview_render_executed"] is False
        assert result["preview_render_count"] == 0
        assert result["selected_branch"] == "preview_rerender_prepared_not_executed"

    def test_second_render_not_attempted_in_single_call(self, tmp_path: Path):
        """A single call does not attempt a second render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["preview_render_count"] == 1
        assert result["second_preview_render_attempted"] is False
        assert result["forbidden_actions"]["second_preview_render_attempted"] is False

    def test_voice_generation_not_executed(self, tmp_path: Path):
        """Voice generation remains blocked after re-render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["voice_generation_executed"] is False
        assert result["forbidden_actions"]["voice_generation_executed"] is False

    def test_assembly_not_executed(self, tmp_path: Path):
        """Assembly remains blocked after re-render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["assembly_executed"] is False
        assert result["forbidden_actions"]["assembly_executed"] is False

    def test_downstream_not_executed(self, tmp_path: Path):
        """Downstream remains blocked after re-render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["downstream_executed"] is False
        assert result["forbidden_actions"]["downstream_executed"] is False

    def test_production_accepted_remains_false(self, tmp_path: Path):
        """production_accepted remains False after re-render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        result = run_controlled_preview_rerender(project_root=project_root, execute=True)

        assert result["production_accepted"] is False
        assert result["forbidden_actions"]["production_accepted"] is False

    def test_preview_artifacts_directory_created(self, tmp_path: Path):
        """Preview artifacts directory is created after render."""
        from app.timeline.controlled_preview_rerender import run_controlled_preview_rerender

        project_root = str(_make_project(tmp_path))
        run_controlled_preview_rerender(project_root=project_root, execute=True)

        preview_dir = Path(project_root) / "output" / "previews"
        assert preview_dir.exists()
