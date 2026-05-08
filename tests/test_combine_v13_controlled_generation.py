"""Tests for V13 controlled generation execution.

Verifies authorization, exactly one generation, second-generation blocking,
fake/stub rejection, and output validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

V13_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"
V13_ASSETS_DIR = "data/rc2_multishot1_ep01/output/assets"
V13_PROJECT_ROOT = "data/rc2_multishot1_ep01"


class TestV13GenerationAuthorization:
    """Verify generation authorization constraints."""

    def test_authorization_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_authorization.json"
        assert path.exists()

    def test_authorization_allows_exactly_one(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("operator_generation_authorized") is True
        assert auth.get("max_generations") == 1
        assert auth.get("allowed_generation_count") == 1

    def test_authorization_blocks_second_generation(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("second_generation_forbidden") is True

    def test_authorization_blocks_blind_retry(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("blind_retry_forbidden") is True

    def test_authorization_blocks_assembly_and_downstream(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("assembly_allowed") is False
        assert auth.get("downstream_allowed") is False
        assert auth.get("production_acceptance_allowed") is False


class TestV13GenerationExecution:
    """Verify generation was executed correctly."""

    def test_generation_result_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        assert path.exists()

    def test_generation_count_is_one(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("generation_attempts") == 1
        assert result.get("max_generations") == 1

    def test_workflow_submitted_and_comfyui_executed(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("workflow_submitted") is True
        assert result.get("comfyui_execution") is True

    def test_generated_assets_count_is_one(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("generated_assets_count") == 1
        assert len(result.get("generated_assets", [])) == 1

    def test_prompt_id_from_trace(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_trace.json"
        with open(path) as f:
            trace = json.load(f)
        events = trace.get("events", [])
        prompt_ids = [
            e.get("prompt_id")
            for e in events
            if e.get("event") == "workflow_submitted"
        ]
        assert len(prompt_ids) == 1
        assert prompt_ids[0] and str(prompt_ids[0]).strip(), "prompt_id must not be empty"

    def test_outputs_manifest_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_outputs_manifest.json"
        assert path.exists()

    def test_no_second_generation_attempted(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("second_generation_attempted") is False or \
            "second_generation_attempted" not in result

    def test_no_blind_retry(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("blind_retry_allowed") is False


class TestV13OutputValidation:
    """Verify output asset validity."""

    def test_asset_exists_on_disk(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assets = result.get("generated_assets", [])
        assert len(assets) >= 1
        disk_path = Path(V13_PROJECT_ROOT) / assets[0]["path"]
        assert disk_path.exists(), f"Asset not found on disk: {disk_path}"

    def test_asset_readable(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        assert asset.get("readable") is True

    def test_asset_dimensions_valid(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        assert asset.get("width", 0) >= 512, "Width too small"
        assert asset.get("height", 0) >= 512, "Height too small"

    def test_asset_size_above_minimum(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        assert asset.get("size_bytes", 0) > 1024, "Asset is too small (stub-like)"

    def test_sha256_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        sha = asset.get("sha256", "")
        assert sha and len(sha) == 64, f"Invalid sha256: {sha}"

    def test_stub_asset_not_detected(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_outputs_manifest.json"
        with open(path) as f:
            manifest = json.load(f)
        assert manifest.get("collection_status") != "stub"
        for asset in manifest.get("generated_assets", []):
            assert asset.get("size_bytes", 0) > 1024

    def test_asset_path_is_canonical(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        p = asset["path"]
        assert "v13" in p, f"Asset path does not contain v13: {p}"
        assert p.startswith("output/assets/"), f"Asset not in canonical path: {p}"

    def test_asset_is_not_old_version(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        p = asset["path"]
        assert "v10" not in p, f"Asset appears to be from V10: {p}"
        assert "v11" not in p, f"Asset appears to be from V11: {p}"
        assert "v12" not in p, f"Asset appears to be from V12: {p}"

    def test_asset_is_not_test_noise(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset = result["generated_assets"][0]
        p = asset["path"]
        assert "test" not in p.lower(), f"Asset appears to be test noise: {p}"


class TestV13ProductionGuards:
    """Verify production guard fields are set correctly."""

    def test_production_accepted_false(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("production_accepted") is False

    def test_assembly_not_executed(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("downstream_executed") is False

    def test_visual_qa_not_executed(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("visual_qa_executed") is False

    def test_artifact_index_production_guards(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("production_accepted") is False
        assert idx.get("assembly_executed") is False
        assert idx.get("downstream_executed") is False
        assert idx.get("visual_acceptance_executed") is False


class TestFakeRejection:
    """Tests that verify fake/dry-run results are not accepted as real."""

    def test_real_prompt_id_is_not_fake(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_trace.json"
        with open(path) as f:
            trace = json.load(f)
        events = trace.get("events", [])
        for e in events:
            if e.get("event") == "workflow_submitted":
                pid = e.get("prompt_id", "")
                assert pid and pid != "fake", f"Fake prompt_id detected: {pid}"
                assert pid != "dry-run", f"Dry-run prompt_id detected: {pid}"
                # UUID format check
                parts = pid.split("-")
                assert len(parts) == 5, f"Not a valid UUID format: {pid}"

    def test_asset_not_fake(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("generated_assets_count", 0) > 0
        assert result.get("status") == "completed"
