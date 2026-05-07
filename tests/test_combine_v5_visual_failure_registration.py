"""RC-COMBINE-V2-3361-3600 — V5 visual failure registration tests."""
from __future__ import annotations

import json
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)
ASSETS_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/assets"
)


def _load(name: str) -> dict:
    p = CONTROL_DIR / name
    assert p.exists(), f"Missing: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_v5_failure_artifact_exists():
    p = CONTROL_DIR / "combine_v2_v5_operator_visual_failure.json"
    assert p.exists()


def test_v5_failure_required_fields():
    data = _load("combine_v2_v5_operator_visual_failure.json")
    assert "v5_asset" in data
    assert data["operator_visual_failed"] is True
    assert data["visual_quality_failed"] is True
    assert data["production_accepted"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False


def test_v5_failure_defects_complete():
    data = _load("combine_v2_v5_operator_visual_failure.json")
    defects = data.get("defects", {})
    expected_defects = [
        "muddy_low_contrast",
        "hazy_gray_output",
        "soft_blurry_details",
        "face_detail_weak",
        "composition_still_weak",
        "style_uncontrolled",
        "generation_time_too_high_for_quality",
    ]
    for d in expected_defects:
        assert defects.get(d) is True, f"Defect '{d}' must be True"


def test_v5_source_asset_exists():
    data = _load("combine_v2_v5_operator_visual_failure.json")
    asset_rel = data["v5_asset"]
    # Resolve relative to project root
    asset_path = Path("F:/ComfyUI/comfy-agent-mvp") / asset_rel
    assert asset_path.exists(), f"V5 asset not found: {asset_path}"


def test_v5_workflow_audit_blocks_blind_retry():
    data = _load("combine_v2_v5_workflow_quality_audit.json")
    assert data["v5_blind_retry_allowed"] is False
    assert data["v5_recipe_trusted"] is False


def test_v5_workflow_audit_identifies_denoise_defect():
    data = _load("combine_v2_v5_workflow_quality_audit.json")
    denoise_risk = data.get("denoise_risk", {})
    assert denoise_risk.get("denoise_too_low_causes_gray_hazy_output") is True


def test_v5_workflow_audit_identifies_resolution_defect():
    data = _load("combine_v2_v5_workflow_quality_audit.json")
    res = data.get("resolution", {})
    assert res.get("resolution_below_policy_minimum") is True
