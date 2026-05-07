"""RC-COMBINE-V2-3361-3600 — Visual Quality Baseline Reset tests."""
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
    assert p.exists(), f"Missing control artifact: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_v5_visual_failure_registered():
    data = _load("combine_v2_v5_operator_visual_failure.json")
    assert data["operator_visual_failed"] is True
    assert data["visual_quality_failed"] is True
    assert data["production_accepted"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False


def test_v5_workflow_quality_audit_created():
    data = _load("combine_v2_v5_workflow_quality_audit.json")
    assert data["v5_recipe_trusted"] is False
    assert data["v5_blind_retry_allowed"] is False
    assert data["baseline_benchmark_required"] is True


def test_baseline_default_sdxl_workflow_created():
    data = _load("shot02_baseline_default_sdxl_workflow.json")
    # Must be a valid node graph (no top-level non-node metadata)
    for key, val in data.items():
        if isinstance(val, dict):
            assert "class_type" in val, f"Node {key} missing class_type"


def test_baseline_workflow_has_saveimage_prefix():
    data = _load("shot02_baseline_default_sdxl_workflow.json")
    prefixes = [
        node.get("inputs", {}).get("filename_prefix")
        for node in data.values()
        if isinstance(node, dict) and node.get("class_type") == "SaveImage"
    ]
    assert "combine_v2_baseline_default_sdxl_shot02" in prefixes


def test_baseline_workflow_blocks_legacy_512():
    data = _load("shot02_baseline_default_sdxl_workflow.json")
    for node in data.values():
        if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
            w = node["inputs"]["width"]
            h = node["inputs"]["height"]
            assert min(w, h) >= 1024, f"Resolution {w}x{h} violates minimum short side 1024"


def test_benchmark_result_created():
    data = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    assert data["baseline_generation_performed"] is True
    assert data["workflow_submitted"] is True
    assert data["comfyui_execution"] is True
    assert data["production_accepted"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False
    assert data["operator_visual_review_required"] is True
    assert data["current_state"] == "operator_visual_review_required"
    assert data["next_allowed_action"] == "operator_visual_review_required"
    assert data.get("prompt_id", "")  # non-empty


def test_canonical_artifacts_updated():
    artifact_index = _load("artifact_index.json")
    assert artifact_index.get("current_state") == "operator_visual_review_required"
    assert artifact_index.get("next_allowed_action") == "operator_visual_review_required"
    assert artifact_index.get("production_accepted") is False
    assert artifact_index.get("baseline_generation_performed") is True


def test_state_transition_correct():
    result = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    assert result["current_state"] == "operator_visual_review_required"
    assert result["next_allowed_action"] == "operator_visual_review_required"
    assert result["production_accepted"] is False


def test_operator_visual_review_required():
    result = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    assert result["operator_visual_review_required"] is True


def test_production_accepted_false():
    for fname in [
        "combine_v2_v5_operator_visual_failure.json",
        "combine_v2_visual_quality_baseline_benchmark_result.json",
        "combine_v2_visual_quality_recipe_decision.json",
        "combine_v2_visual_quality_operator_review_packet.json",
    ]:
        data = _load(fname)
        assert data.get("production_accepted") is False, f"{fname}: production_accepted must be False"


def test_assembly_blocked():
    for fname in [
        "combine_v2_v5_operator_visual_failure.json",
        "combine_v2_visual_quality_baseline_benchmark_result.json",
    ]:
        data = _load(fname)
        assert data.get("assembly_allowed") is False, f"{fname}: assembly_allowed must be False"


def test_downstream_blocked():
    for fname in [
        "combine_v2_v5_operator_visual_failure.json",
        "combine_v2_visual_quality_baseline_benchmark_result.json",
    ]:
        data = _load(fname)
        assert data.get("downstream_allowed") is False, f"{fname}: downstream_allowed must be False"
