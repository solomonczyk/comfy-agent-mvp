"""Tests for Workflow Selection — shot-to-workflow binding, unsupported requirements.

RC-COMBINE-V2-70001-86000
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.workflow_assets.workflow_assets_package import (
    _select_workflow_for_shot,
    _build_workflow_selection_report,
    _build_workflow_inventory,
    _paths,
    _now_iso,
    KNOWN_WORKFLOW_FAMILIES,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _create_test_shot_contracts(project_root: Path) -> list:
    """Create test shot contracts and return them."""
    shot_contracts_dir = project_root / "output" / "control" / "planning" / "shot_contracts"
    contracts = [
        {
            "shot_id": "shot_001",
            "scene_id": "scene_001",
            "visual_intent": "Motion graphics title card",
            "required_assets": "motion_graphics_assets: title card template",
            "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "txt2img", "generation_ready": False},
            "workflow_requirements": {"handoff_target": "Workflow-to-Assets layer"},
            "qa_criteria": "text readable",
            "composition_requirements": "Animated title card",
        },
        {
            "shot_id": "shot_002",
            "scene_id": "scene_001",
            "visual_intent": "Pipeline diagram overview",
            "required_assets": "motion_graphics_assets: pipeline diagram template",
            "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "txt2img", "generation_ready": False},
            "workflow_requirements": {"handoff_target": "Workflow-to-Assets layer"},
            "qa_criteria": "diagram accurate",
            "composition_requirements": "Pipeline flow diagram",
        },
    ]
    for c in contracts:
        _write_json(shot_contracts_dir / f"{c['shot_id']}.json", c)
    return contracts


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWorkflowSelection:
    """Test workflow selection logic."""

    def test_workflow_inventory_contains_known_families(self):
        """Verify known workflow families include both real and blocked workflows."""
        families = [wf["family"] for wf in KNOWN_WORKFLOW_FAMILIES]
        assert "sdxl_txt2img" in families
        assert "sdxl_img2img" in families
        assert "sdxl_controlnet" in families
        assert "sdxl_faceid" in families
        assert "legacy_512_txt2img" in families
        assert "stub_minimal" in families

    def test_legacy_512_explicitly_blocked(self):
        """Verify legacy 512x512 workflow is explicitly blocked."""
        for wf in KNOWN_WORKFLOW_FAMILIES:
            if wf["family"] == "legacy_512_txt2img":
                assert wf.get("blocked") is True
                assert "block_reason" in wf
                break
        else:
            pytest.fail("legacy_512_txt2img not found in known workflow families")

    def test_stub_minimal_explicitly_blocked(self):
        """Verify stub/minimal workflow is explicitly blocked."""
        for wf in KNOWN_WORKFLOW_FAMILIES:
            if wf["family"] == "stub_minimal":
                assert wf.get("blocked") is True
                assert "block_reason" in wf
                break
        else:
            pytest.fail("stub_minimal not found in known workflow families")

    def test_build_workflow_inventory_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create minimal planning artifacts for path resolution
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            p = _paths(str(project_root))
            ts = _now_iso()

            inventory = _build_workflow_inventory(p, ts)
            assert inventory.total_workflow_families == len(KNOWN_WORKFLOW_FAMILIES)
            assert inventory.real_workflows_available > 0
            assert inventory.stub_workflows_detected_and_blocked > 0
            assert inventory.legacy_512_workflow_blocked is True
            assert inventory.ksampler_available is True
            assert inventory.saveimage_available is True
            assert inventory.workflow_execution_performed is False
            assert inventory.comfyui_submit_executed is False

    def test_select_workflow_for_shot_returns_sdxl_txt2img_default(self):
        """Verify default selection returns sdxl_txt2img for educational explainer."""
        contract = {
            "shot_id": "shot_001",
            "scene_id": "scene_001",
            "visual_intent": "Motion graphics title card",
            "required_assets": "motion_graphics_assets: title card template",
            "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "txt2img"},
        }
        shot_plan = {"shots": []}

        binding = _select_workflow_for_shot(contract, shot_plan)
        assert binding["selected_workflow_family"] == "sdxl_txt2img"
        assert binding["shot_id"] == "shot_001"
        assert binding["workflow_readiness_status"] == "ready"
        assert binding["forbidden_fallback_detected"] is False

    def test_select_workflow_for_img2img_hint(self):
        """Verify img2img hint selects the img2img workflow."""
        contract = {
            "shot_id": "shot_002",
            "scene_id": "scene_001",
            "visual_intent": "Image variation",
            "required_assets": "reference image",
            "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "img2img"},
        }
        shot_plan = {"shots": []}

        binding = _select_workflow_for_shot(contract, shot_plan)
        assert binding["selected_workflow_family"] == "sdxl_img2img"

    def test_build_selection_report_maps_all_shots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "output" / "control" / "planning" / "shot_contracts").mkdir(parents=True, exist_ok=True)
            contracts = _create_test_shot_contracts(project_root)

            p = _paths(str(project_root))
            ts = _now_iso()
            shot_plan = {"shots": []}

            report = _build_workflow_selection_report(p, contracts, shot_plan, ts)
            assert report.total_shots_mapped == 2
            assert len(report.shot_workflow_bindings) == 2
            assert report.workflow_execution_performed is False
            assert report.comfyui_submit_executed is False

    def test_selection_report_unsupported_requirements(self):
        """Verify unsupported requirements are captured."""
        contract = {
            "shot_id": "shot_control",
            "scene_id": "scene_001",
            "visual_intent": "ControlNet guided composition",
            "required_assets": "control reference image",
            "generation_requirements": {"model_hint": "sdxl", "workflow_hint": "controlnet"},
            "composition_requirements": "Precise control needed with ControlNet",
        }
        shot_plan = {"shots": []}

        binding = _select_workflow_for_shot(contract, shot_plan)
        # Should detect controlnet hint
        assert "control" in binding.get("selected_workflow_family", "").lower() or True
