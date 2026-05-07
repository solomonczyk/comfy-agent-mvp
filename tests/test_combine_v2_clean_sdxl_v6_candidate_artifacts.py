"""RC-COMBINE-V2-3601-3900 — Artifact integrity tests for v6 candidate generation."""
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


def test_result_artifact_exists():
    """combine_v2_clean_sdxl_v6_candidate_result.json must exist."""
    assert (CONTROL_DIR / "combine_v2_clean_sdxl_v6_candidate_result.json").exists()


def test_outputs_manifest_exists():
    """combine_v2_clean_sdxl_v6_candidate_outputs_manifest.json must exist."""
    assert (CONTROL_DIR / "combine_v2_clean_sdxl_v6_candidate_outputs_manifest.json").exists()


def test_operator_review_packet_exists():
    """combine_v2_visual_quality_recovery_operator_review_packet.json must exist."""
    assert (CONTROL_DIR / "combine_v2_visual_quality_recovery_operator_review_packet.json").exists()


def test_result_generation_count_is_one():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("generation_count") == 1


def test_result_has_prompt_id():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("prompt_id"), "prompt_id must be present and non-empty"


def test_result_has_canonical_assets():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assets = data.get("output_asset_paths", [])
    assert len(assets) >= 1, "At least one canonical asset must be registered"


def test_manifest_entries_have_sha256_and_dims():
    manifest = _load("combine_v2_clean_sdxl_v6_candidate_outputs_manifest.json")
    assert isinstance(manifest, list) and len(manifest) >= 1
    for entry in manifest:
        assert entry.get("sha256"), f"Missing sha256 in manifest entry: {entry}"
        assert entry.get("width", 0) > 0, f"Invalid width in entry: {entry}"
        assert entry.get("height", 0) > 0, f"Invalid height in entry: {entry}"
        assert entry.get("size_bytes", 0) >= 1024, f"Stub asset in entry: {entry}"


def test_canonical_asset_file_exists_on_disk():
    manifest = _load("combine_v2_clean_sdxl_v6_candidate_outputs_manifest.json")
    assert isinstance(manifest, list) and len(manifest) >= 1
    for entry in manifest:
        fname = entry.get("filename", "")
        assert fname, "Manifest entry missing filename"
        asset_path = ASSETS_DIR / fname
        assert asset_path.exists(), f"Canonical asset missing on disk: {asset_path}"
        assert asset_path.stat().st_size >= 1024, f"Canonical asset is a stub: {asset_path}"


def test_operator_review_packet_structure():
    data = _load("combine_v2_visual_quality_recovery_operator_review_packet.json")
    assert data.get("production_accepted") is False
    assert data.get("operator_visual_review_required") is True
    assert "production_acceptance" in data.get("forbidden_automatic_actions", [])
    assert "assembly" in data.get("forbidden_automatic_actions", [])
    assert data.get("current_state") == "operator_visual_review_required"


def test_artifact_index_updated():
    data = _load("artifact_index.json")
    assert data.get("clean_sdxl_v6_candidate_generated") is True
    assert data.get("production_accepted") is False
    assert data.get("operator_visual_review_required") is True
    assert data.get("assembly_allowed") is False
