"""Tests for standards pack validator."""

import json
from pathlib import Path

import pytest

from app.standards.standards_pack_validator import StandardsPackValidator


@pytest.fixture
def valid_standards_pack(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test_manifest",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {"schemas": "schemas", "internal": "internal"},
        "artifacts": {
            "universal_quality_standard": "internal/universal_quality_standard.json",
        },
    }
    (pack_dir / "standards_pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (pack_dir / "schemas").mkdir()
    (pack_dir / "schemas" / "standard_schema.json").write_text(
        json.dumps({"type": "object"}), encoding="utf-8"
    )
    (pack_dir / "internal").mkdir()
    (pack_dir / "internal" / "universal_quality_standard.json").write_text(
        json.dumps({"standard_id": "universal_quality_standard", "version": "1.0.0", "applies_to": ["qa"]}),
        encoding="utf-8",
    )
    return pack_dir


def test_validate_passes(valid_standards_pack):
    validator = StandardsPackValidator(valid_standards_pack)
    result = validator.validate()
    assert result["valid"] is True
    assert not result["errors"]


def test_validate_fails_missing_manifest(tmp_path):
    validator = StandardsPackValidator(tmp_path / "standards_pack")
    result = validator.validate()
    assert result["valid"] is False
    assert any("manifest" in err.lower() for err in result["errors"])


def test_validate_fails_missing_artifact(tmp_path):
    pack_dir = tmp_path / "standards_pack"
    pack_dir.mkdir()
    manifest = {
        "manifest_id": "test",
        "version": "1.0.0",
        "task_id": "TEST-001",
        "directories": {},
        "artifacts": {"missing": "missing.json"},
    }
    (pack_dir / "standards_pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    validator = StandardsPackValidator(pack_dir)
    result = validator.validate()
    assert result["valid"] is False
    assert any("missing" in err.lower() for err in result["errors"])
