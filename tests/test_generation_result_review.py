"""Test generation result review — validate output quality and state.

RC-COMBINE-V2-99001-102000

Validates:
- Result review created after generation
- Visual QA not executed
- Assembly not executed
- Downstream not executed
- Production_accepted false
"""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"


def _read_json(name: str) -> dict:
    path = CONTROL_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestResultReview:
    def test_result_review_exists(self):
        """generation_result_review.json must exist."""
        review = _read_json("generation_result_review.json")
        assert review, "generation_result_review.json missing"

    def test_generation_performed(self):
        """Generation must be recorded as performed."""
        review = _read_json("generation_result_review.json")
        assert review.get("status") in (
            "generation_result_review_required",
            "generation_result_review_blocked",
        )

    def test_generation_count_recorded(self):
        """generation_count must be recorded."""
        review = _read_json("generation_result_review.json")
        assert review.get("generation_count", 0) >= 1

    def test_workflow_submitted(self):
        """Workflow must be recorded as submitted."""
        review = _read_json("generation_result_review.json")
        assert review.get("workflow_submitted") is True

    def test_comfyui_execution_recorded(self):
        """ComfyUI execution must be recorded."""
        review = _read_json("generation_result_review.json")
        assert review.get("comfyui_execution") is True

    def test_generated_assets_count_positive(self):
        """At least one generated asset must be recorded."""
        review = _read_json("generation_result_review.json")
        assert review.get("generated_assets_count", 0) > 0

    def test_generated_assets_list_present(self):
        """generated_assets list must exist with entries."""
        review = _read_json("generation_result_review.json")
        assets = review.get("generated_assets", [])
        assert len(assets) > 0

    def test_assets_exist_on_filesystem(self):
        """Assets must exist on filesystem."""
        review = _read_json("generation_result_review.json")
        assert review.get("assets_exist") is True

    def test_assets_readable(self):
        """Assets must be readable."""
        review = _read_json("generation_result_review.json")
        assert review.get("assets_readable") is True

    def test_sha256_valid(self):
        """SHA256 checksum must be valid."""
        review = _read_json("generation_result_review.json")
        assert review.get("sha256_valid") is True

    def test_dimensions_valid(self):
        """Image dimensions must be valid."""
        review = _read_json("generation_result_review.json")
        assert review.get("dimensions_valid") is True

    def test_prompt_id_present(self):
        """Prompt ID must be present and valid."""
        review = _read_json("generation_result_review.json")
        assert review.get("prompt_id_present") is True
        assert review.get("prompt_id", "") != ""
        assert review.get("prompt_id", "") != "fake_prompt_id"

    def test_no_second_generation(self):
        """No second generation must have been attempted."""
        review = _read_json("generation_result_review.json")
        assert review.get("second_generation_attempted") is False

    def test_no_blind_retry(self):
        """No blind retry must have been attempted."""
        review = _read_json("generation_result_review.json")
        assert review.get("blind_retry_attempted") is False

    def test_no_fake_prompt_id(self):
        """No fake prompt_id detected."""
        review = _read_json("generation_result_review.json")
        assert review.get("fake_prompt_id_detected") is False

    def test_no_fake_assets(self):
        """No fake assets detected."""
        review = _read_json("generation_result_review.json")
        assert review.get("fake_assets_detected") is False

    def test_no_legacy_512_workflow(self):
        """No legacy 512 workflow detected in result."""
        review = _read_json("generation_result_review.json")
        assert review.get("legacy_512_workflow_detected") is False

    def test_no_stub_workflow(self):
        """No stub workflow detected in result."""
        review = _read_json("generation_result_review.json")
        assert review.get("stub_workflow_detected") is False

    def test_visual_qa_not_executed(self):
        """Visual QA must NOT have been executed."""
        review = _read_json("generation_result_review.json")
        assert review.get("visual_qa_executed") is False

    def test_visual_acceptance_not_executed(self):
        """Visual acceptance must NOT have been executed."""
        review = _read_json("generation_result_review.json")
        assert review.get("visual_acceptance_executed") is False

    def test_assembly_not_executed(self):
        """Assembly must NOT have been executed."""
        review = _read_json("generation_result_review.json")
        assert review.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        """Downstream must NOT have been executed."""
        review = _read_json("generation_result_review.json")
        assert review.get("downstream_executed") is False

    def test_production_not_accepted(self):
        """Production acceptance must be false."""
        review = _read_json("generation_result_review.json")
        assert review.get("production_accepted") is False

    def test_next_action_is_review_required(self):
        """Next allowed action must be generation_result_review_required."""
        review = _read_json("generation_result_review.json")
        action = review.get("next_allowed_action", "")
        assert action == "generation_result_review_required"


class TestCanonicalManifest:
    def test_canonical_manifest_exists(self):
        """canonical_outputs_manifest.json must exist."""
        manifest = _read_json("canonical_outputs_manifest.json")
        assert manifest, "canonical_outputs_manifest.json missing"

    def test_manifest_has_assets(self):
        """Manifest must list generated assets."""
        manifest = _read_json("canonical_outputs_manifest.json")
        assert manifest.get("generated_assets_count", 0) > 0
        assert len(manifest.get("generated_assets", [])) > 0

    def test_manifest_no_downstream(self):
        """Manifest must not have downstream executed."""
        manifest = _read_json("canonical_outputs_manifest.json")
        assert manifest.get("downstream_executed") is False

    def test_manifest_no_production(self):
        """Manifest must not have production accepted."""
        manifest = _read_json("canonical_outputs_manifest.json")
        assert manifest.get("production_accepted") is False

    def test_asset_paths_valid(self):
        """Asset paths must be relative and exist."""
        manifest = _read_json("canonical_outputs_manifest.json")
        for asset in manifest.get("generated_assets", []):
            path_str = asset.get("path", "")
            assert path_str, "Asset path must not be empty"
            assert path_str.startswith("output/assets/"), f"Asset must be in output/assets: {path_str}"
            abs_path = PROJECT_ROOT / path_str
            assert abs_path.exists(), f"Asset file not found: {abs_path}"

    def test_asset_sha256_valid_format(self):
        """Asset SHA256 must be 64 hex chars."""
        manifest = _read_json("canonical_outputs_manifest.json")
        for asset in manifest.get("generated_assets", []):
            sha = asset.get("sha256", "")
            assert len(sha) == 64, f"Invalid SHA256 length for {asset.get('path')}"
            int(sha, 16)  # validates hex

    def test_asset_dimensions_present(self):
        """Asset dimensions must be positive integers."""
        manifest = _read_json("canonical_outputs_manifest.json")
        for asset in manifest.get("generated_assets", []):
            assert isinstance(asset.get("width"), int) and asset["width"] > 0
            assert isinstance(asset.get("height"), int) and asset["height"] > 0
