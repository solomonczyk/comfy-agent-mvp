"""Tests for V14 controlled generation execution.

Verifies authorization, exactly one generation, second-generation blocking,
blind retry blocking, and output validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

V14_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"
V14_PROJECT_ROOT = "data/rc2_multishot1_ep01"


class TestV14GenerationAuthorization:
    """Verify generation authorization constraints."""

    def test_authorization_exists(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        assert path.exists()

    def test_authorization_allows_exactly_one(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("generation_authorized") is True
        assert auth.get("max_generations") == 1
        assert auth.get("allowed_generation_count") == 1

    def test_authorization_blocks_second_generation(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("second_generation_forbidden") is True

    def test_authorization_blocks_blind_retry(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("blind_retry_forbidden") is True

    def test_authorization_blocks_assembly_and_downstream(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)
        assert auth.get("assembly_allowed") is False
        assert auth.get("downstream_allowed") is False
        assert auth.get("production_acceptance_allowed") is False


class TestV14GenerationExecution:
    """Verify generation was executed correctly."""

    def test_generation_result_exists(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        assert path.exists()

    def test_generation_count_is_one(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("generation_count") == 1
        assert result.get("max_generations") == 1

    def test_workflow_submitted_and_comfyui_executed(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("workflow_submitted") is True
        assert result.get("comfyui_execution") is True

    def test_real_prompt_id_is_valid_uuid(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        pid = result.get("prompt_id", "")
        assert pid and pid != "fake", f"Fake prompt_id detected: {pid}"
        assert pid != "dry-run", f"Dry-run prompt_id detected: {pid}"
        parts = pid.split("-")
        assert len(parts) == 5, f"Not a valid UUID format: {pid}"

    def test_no_second_generation_attempted(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("second_v14_generation_attempted") is False

    def test_no_blind_retry(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("blind_retry_attempted") is False

    def test_outputs_manifest_exists(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_outputs_manifest.json"
        assert path.exists()

    def test_submit_request_exists(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_submit_request.json"
        assert path.exists()


class TestV14OutputValidation:
    """Verify output asset validity."""

    def test_asset_exists_on_disk(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        asset_path = result.get("asset_path", "")
        assert asset_path, "No asset_path in generation result"
        disk_path = Path(V14_PROJECT_ROOT) / asset_path
        assert disk_path.exists(), f"Asset not found on disk: {disk_path}"

    def test_asset_readable(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("asset_readable") is True

    def test_asset_dimensions_valid(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("asset_width", 0) >= 512, "Width too small"
        assert result.get("asset_height", 0) >= 512, "Height too small"

    def test_asset_size_above_minimum(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("asset_size_bytes", 0) > 1024, "Asset is too small (stub-like)"

    def test_sha256_present(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        sha = result.get("asset_sha256", "")
        assert sha and len(sha) == 64, f"Invalid sha256: {sha}"

    def test_stub_asset_not_detected(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("stub_asset_detected") is False

    def test_asset_path_is_canonical(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        p = result.get("asset_path", "")
        assert "v14" in p, f"Asset path does not contain v14: {p}"
        assert p.startswith("output/assets/"), f"Asset not in canonical path: {p}"

    def test_asset_is_not_old_version(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        p = result.get("asset_path", "")
        assert "v10" not in p, f"Asset appears to be from V10: {p}"
        assert "v11" not in p, f"Asset appears to be from V11: {p}"
        assert "v12" not in p, f"Asset appears to be from V12: {p}"
        assert "v13" not in p, f"Asset appears to be from V13: {p}"


class TestV14ProductionGuards:
    """Verify production guard fields in artifact_index."""

    def test_production_accepted_false(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("production_accepted") is False

    def test_assembly_not_executed(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("assembly_executed") is False

    def test_downstream_not_executed(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("downstream_executed") is False


class TestV14StateTransition:
    """Verify correct state after successful generation."""

    def test_state_is_operator_review_required(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("current_state") == "v14_operator_visual_review_required"
        assert idx.get("next_allowed_action") == "v14_operator_visual_review_required"

    def test_generation_runtime_not_blocked(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("generation_runtime_blocked") is False or idx.get("generation_runtime_blocked") is None

    def test_v14_generation_succeeded(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("v14_generation_succeeded") is True


class TestFakeRejection:
    """Verify no fake/dry-run prompt data is present."""

    def test_no_fake_prompt_id(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        pid = result.get("prompt_id", "")
        assert pid and pid.strip(), "prompt_id must not be empty"
        assert pid != "fake", "Fake prompt_id detected"
        assert pid != "dry-run", "Dry-run prompt_id detected"

    def test_no_second_generation_trace(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)
        assert idx.get("second_v14_generation_attempted") is False
        assert idx.get("blind_retry_attempted") is False
