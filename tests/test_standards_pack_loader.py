"""Tests for standards pack loader."""

import json
from pathlib import Path

import pytest

from app.standards.standards_pack_loader import StandardsPackLoader


@pytest.fixture
def sample_standards_pack(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test_manifest",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"internal": "internal"},
        "artifacts": {
            "universal_quality_standard": "internal/universal_quality_standard.json",
            "missing_artifact": "internal/missing.json",
        },
    }
    (pack_dir / "standards_pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    universal = {
        "standard_id": "universal_quality_standard",
        "version": "1.0.0",
        "applies_to": ["qa", "qc"],
    }
    (pack_dir / "internal").mkdir()
    (pack_dir / "internal" / "universal_quality_standard.json").write_text(
        json.dumps(universal), encoding="utf-8"
    )
    return pack_dir


def test_load_manifest(sample_standards_pack):
    loader = StandardsPackLoader(sample_standards_pack)
    manifest = loader.load_manifest()
    assert manifest["manifest_id"] == "test_manifest"


def test_load_all_artifacts(sample_standards_pack):
    loader = StandardsPackLoader(sample_standards_pack)
    data = loader.load_all()
    assert "manifest" in data
    assert "artifacts" in data
    assert data["artifacts"]["universal_quality_standard"]["standard_id"] == "universal_quality_standard"
    assert data["artifacts"]["missing_artifact"].get("_missing") is True


def test_list_standards(sample_standards_pack):
    loader = StandardsPackLoader(sample_standards_pack)
    standards = loader.list_standards()
    ids = [s["standard_id"] for s in standards]
    assert "universal_quality_standard" in ids
    assert "missing_artifact" in ids


def test_inspect_standard(sample_standards_pack):
    loader = StandardsPackLoader(sample_standards_pack)
    data = loader.inspect_standard("universal_quality_standard")
    assert data["standard_id"] == "universal_quality_standard"


def test_inspect_missing_standard(sample_standards_pack):
    loader = StandardsPackLoader(sample_standards_pack)
    data = loader.inspect_standard("nonexistent")
    assert "error" in data
