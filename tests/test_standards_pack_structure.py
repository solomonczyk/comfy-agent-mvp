"""Tests for standards pack structure and directory layout.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_standards_pack_dir() -> Path:
    """Return the standards pack directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control/standards_pack")


class TestStandardsPackStructure:
    """Test that the standards pack has the required directory structure."""

    def test_standards_pack_directory_exists(self):
        """Standards pack directory must exist."""
        sp_dir = get_standards_pack_dir()
        assert sp_dir.exists(), f"Standards pack directory not found: {sp_dir}"
        assert sp_dir.is_dir(), f"Standards pack path is not a directory: {sp_dir}"

    def test_external_registry_directory_exists(self):
        """external_registry/ directory must exist."""
        dir_path = get_standards_pack_dir() / "external_registry"
        assert dir_path.exists(), f"external_registry directory not found"
        assert dir_path.is_dir()

    def test_schemas_directory_exists(self):
        """schemas/ directory must exist."""
        dir_path = get_standards_pack_dir() / "schemas"
        assert dir_path.exists(), f"schemas directory not found"
        assert dir_path.is_dir()

    def test_internal_directory_exists(self):
        """internal/ directory must exist."""
        dir_path = get_standards_pack_dir() / "internal"
        assert dir_path.exists(), f"internal directory not found"
        assert dir_path.is_dir()

    def test_roles_directory_exists(self):
        """roles/ directory must exist."""
        dir_path = get_standards_pack_dir() / "roles"
        assert dir_path.exists(), f"roles directory not found"
        assert dir_path.is_dir()

    def test_policies_directory_exists(self):
        """policies/ directory must exist."""
        dir_path = get_standards_pack_dir() / "policies"
        assert dir_path.exists(), f"policies directory not found"
        assert dir_path.is_dir()

    def test_references_directory_exists(self):
        """references/ directory must exist."""
        dir_path = get_standards_pack_dir() / "references"
        assert dir_path.exists(), f"references directory not found"
        assert dir_path.is_dir()

    def test_reports_directory_exists(self):
        """reports/ directory must exist."""
        dir_path = get_standards_pack_dir() / "reports"
        assert dir_path.exists(), f"reports directory not found"
        assert dir_path.is_dir()


class TestStandardsPackManifest:
    """Test the standards pack manifest."""

    def test_manifest_exists(self):
        """standards_pack_manifest.json must exist."""
        manifest_path = get_standards_pack_dir() / "standards_pack_manifest.json"
        assert manifest_path.exists(), "Manifest file not found"

    def test_manifest_is_valid_json(self):
        """Manifest must be valid JSON."""
        manifest_path = get_standards_pack_dir() / "standards_pack_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_manifest_has_required_fields(self):
        """Manifest must have all required fields."""
        manifest_path = get_standards_pack_dir() / "standards_pack_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_fields = [
            "manifest_id",
            "version",
            "task_id",
            "directories",
            "artifacts",
        ]
        for field in required_fields:
            assert field in data, f"Manifest missing required field: {field}"

    def test_manifest_task_id_correct(self):
        """Manifest must have the correct task ID."""
        manifest_path = get_standards_pack_dir() / "standards_pack_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("task_id") == "RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001"

    def test_manifest_artifacts_exist(self):
        """All artifacts referenced in manifest must exist."""
        sp_dir = get_standards_pack_dir()
        manifest_path = sp_dir / "standards_pack_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        artifacts = data.get("artifacts", {})
        missing = []
        for key, rel_path in artifacts.items():
            artifact_path = sp_dir / rel_path
            if not artifact_path.exists():
                missing.append(f"{key} -> {rel_path}")

        assert not missing, f"Missing artifacts: {missing}"


class TestExternalRegistry:
    """Test external registry artifacts."""

    def test_external_standards_sources_exists(self):
        """external_standards_sources.json must exist."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        assert path.exists()

    def test_external_standards_acquisition_plan_exists(self):
        """external_standards_acquisition_plan.json must exist."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_plan.json"
        assert path.exists()

    def test_external_standards_acquisition_status_exists(self):
        """external_standards_acquisition_status.json must exist."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_status.json"
        assert path.exists()

    def test_external_standards_not_downloaded(self):
        """External standards must be registered but not downloaded."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        for source in sources:
            assert source.get("download_performed") is False, \
                f"{source.get('standard_id')} has download_performed=true"
            assert source.get("local_copy_available") is False, \
                f"{source.get('standard_id')} has local_copy_available=true"

    def test_all_required_external_standards_registered(self):
        """All required external standards must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        registered_ids = {s.get("standard_id") for s in sources}

        required = [
            "owasp_asvs",
            "mitre_cwe",
            "mitre_capec",
            "nist_oscal",
            "cyclonedx",
            "spdx",
            "openssf_scorecard",
        ]

        for std_id in required:
            assert std_id in registered_ids, f"Required external standard not registered: {std_id}"
