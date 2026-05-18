"""Tests for standards pack schema validation.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_standards_pack_dir() -> Path:
    """Return the standards pack directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control/standards_pack")


class TestSchemaFiles:
    """Test that all required schema files exist and are valid."""

    def test_standard_schema_exists(self):
        """standard.schema.json must exist and be valid JSON."""
        path = get_standards_pack_dir() / "schemas" / "standard_schema.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "type" in data or "$schema" in data or "properties" in data

    def test_manifest_schema_exists(self):
        """standards_pack_manifest.schema.json must exist."""
        path = get_standards_pack_dir() / "schemas" / "standards_pack_manifest_schema.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_defect_taxonomy_schema_exists(self):
        """defect_taxonomy.schema.json must exist."""
        path = get_standards_pack_dir() / "schemas" / "defect_taxonomy_schema.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_decision_policy_schema_exists(self):
        """decision_policy.schema.json must exist."""
        path = get_standards_pack_dir() / "schemas" / "decision_policy_schema.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_role_standard_schema_exists(self):
        """role_standard.schema.json must exist."""
        path = get_standards_pack_dir() / "schemas" / "role_standard_schema.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_all_schemas_are_valid_json(self):
        """All schema files must be valid JSON."""
        schemas_dir = get_standards_pack_dir() / "schemas"
        schema_files = list(schemas_dir.glob("*.json"))
        assert len(schema_files) > 0, "No schema files found"

        for schema_file in schema_files:
            with open(schema_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {schema_file.name}: {e}")


class TestSchemaContent:
    """Test schema content requirements."""

    def test_role_standard_schema_has_required_fields(self):
        """Role standard schema must define required fields."""
        path = get_standards_pack_dir() / "schemas" / "role_standard_schema.json"
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Schema should have properties or required fields defined
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Either properties or required should be present
        assert properties or required, "Schema missing properties and required fields"

    def test_decision_policy_schema_has_rules(self):
        """Decision policy schema should reference rules."""
        path = get_standards_pack_dir() / "schemas" / "decision_policy_schema.json"
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        schema_str = json.dumps(schema)
        assert "rule" in schema_str.lower() or "policy" in schema_str.lower(), \
            "Decision policy schema should reference rules or policies"


class TestArtifactValidation:
    """Test that artifacts can be validated against schemas."""

    def test_manifest_validates_against_schema(self):
        """Manifest should conform to manifest schema."""
        sp_dir = get_standards_pack_dir()
        manifest_path = sp_dir / "standards_pack_manifest.json"
        schema_path = sp_dir / "schemas" / "standards_pack_manifest_schema.json"

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Basic check: manifest has the fields that schema requires
        required = schema.get("required", [])
        for field in required:
            assert field in manifest, f"Manifest missing field required by schema: {field}"

    def test_all_role_standards_are_valid_json(self):
        """All role standard files must be valid JSON."""
        roles_dir = get_standards_pack_dir() / "roles"
        role_files = list(roles_dir.glob("*.json"))
        assert len(role_files) > 0, "No role standard files found"

        for role_file in role_files:
            with open(role_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                    # Should have role_id
                    assert "role_id" in data, f"{role_file.name} missing role_id"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {role_file.name}: {e}")

    def test_all_policies_are_valid_json(self):
        """All policy files must be valid JSON."""
        policies_dir = get_standards_pack_dir() / "policies"
        policy_files = list(policies_dir.glob("*.json"))
        assert len(policy_files) > 0, "No policy files found"

        for policy_file in policy_files:
            with open(policy_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                    # Should have policy_id
                    assert "policy_id" in data, f"{policy_file.name} missing policy_id"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {policy_file.name}: {e}")

    def test_all_internal_standards_are_valid_json(self):
        """All internal standard files must be valid JSON."""
        internal_dir = get_standards_pack_dir() / "internal"
        internal_files = list(internal_dir.glob("*.json"))
        assert len(internal_files) > 0, "No internal standard files found"

        for internal_file in internal_files:
            with open(internal_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {internal_file.name}: {e}")

    def test_defect_taxonomy_has_required_defects(self):
        """Defect taxonomy must include required defect categories."""
        path = get_standards_pack_dir() / "internal" / "defect_taxonomy.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        defects = data.get("defects", [])
        defect_ids = {d.get("defect_id") for d in defects}

        # Check for key required defects from the task specification
        required_defects = [
            "blur",  # visual_defect
            "bad_anatomy",  # anatomy_defect
            "bad_hands",  # anatomy_defect
            "identity_drift",  # identity_drift
            "duplicate_frames",  # timeline_static_duplicate_frames
            "static_preview",  # preview_not_proving_scene_development
            "fake_operator_decision",  # fake_operator_decision
            "fake_generation",  # fake_success
        ]

        for defect_id in required_defects:
            assert defect_id in defect_ids, f"Required defect missing: {defect_id}"
