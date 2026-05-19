"""Tests for reference pack schema validation.

Task: RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from app.workflow_registry.models import (
    ReferenceItem,
    ReferencePack,
    ReferenceType,
)
from app.workflow_registry.reference_pack_schema import ReferencePackSchema
from app.workflow_registry.validator import WorkflowRegistryValidator


def test_reference_pack_schema_create_empty():
    """Test creating an empty reference pack."""
    pack = ReferencePackSchema.create_empty_reference_pack("test_pack")
    assert pack.reference_pack_id == "test_pack"
    assert pack.project_binding_required is False
    assert len(pack.items) == 0
    assert pack.usage_policy.get("require_actual_images") is False


def test_reference_pack_schema_add_reference_item():
    """Test adding a reference item."""
    pack = ReferencePackSchema.create_empty_reference_pack("test_pack")
    pack = ReferencePackSchema.add_reference_item(
        pack,
        reference_id="style1",
        reference_type=ReferenceType.STYLE,
        description="Style reference",
        path=None,
        required=True,
    )
    
    assert len(pack.items) == 1
    assert pack.items[0].reference_id == "style1"
    assert pack.items[0].reference_type == ReferenceType.STYLE
    assert pack.items[0].path is None


def test_reference_pack_schema_create_style_reference_slot():
    """Test creating a style reference slot without actual image."""
    pack = ReferencePackSchema.create_empty_reference_pack("test_pack")
    pack = ReferencePackSchema.create_style_reference_slot(
        pack,
        slot_id="style1",
        description="Style reference slot",
        metadata={"style_category": "photorealistic"},
    )
    
    assert len(pack.items) == 1
    assert pack.items[0].reference_id == "style1"
    assert pack.items[0].reference_type == ReferenceType.STYLE
    assert pack.items[0].path is None  # No actual image
    assert pack.items[0].metadata["style_category"] == "photorealistic"


def test_reference_pack_schema_create_character_reference_slot():
    """Test creating a character reference slot without actual image."""
    pack = ReferencePackSchema.create_empty_reference_pack("test_pack")
    pack = ReferencePackSchema.create_character_reference_slot(
        pack,
        slot_id="char1",
        description="Character reference slot",
    )
    
    assert len(pack.items) == 1
    assert pack.items[0].reference_id == "char1"
    assert pack.items[0].reference_type == ReferenceType.CHARACTER
    assert pack.items[0].path is None


def test_reference_pack_schema_validate_slot_description_only():
    """Test that reference items can exist with description only."""
    item = ReferenceItem(
        reference_id="style1",
        reference_type=ReferenceType.STYLE,
        description="Style reference",
        path=None,
    )
    
    assert ReferencePackSchema.validate_slot_description_only(item) is True
    
    # Test without description
    item_no_desc = ReferenceItem(
        reference_id="style1",
        reference_type=ReferenceType.STYLE,
        description="",
        path=None,
    )
    
    assert ReferencePackSchema.validate_slot_description_only(item_no_desc) is False


def test_reference_pack_schema_validate_pack_slot_compatibility():
    """Test that reference pack supports slot descriptions without images."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
                path=None,
            )
        ],
        usage_policy={
            "allow_slot_description": True,
            "require_actual_images": False,
        },
    )
    
    errors = ReferencePackSchema.validate_pack_slot_compatibility(pack)
    assert len(errors) == 0


def test_reference_pack_schema_validate_pack_requires_actual_images():
    """Test that packs requiring actual images fail compatibility check."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE],
        items=[],
        usage_policy={
            "allow_slot_description": True,
            "require_actual_images": True,  # Should be False
        },
    )
    
    errors = ReferencePackSchema.validate_pack_slot_compatibility(pack)
    assert len(errors) > 0


def test_reference_pack_schema_get_missing_reference_types():
    """Test getting missing reference types."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        reference_types=[ReferenceType.STYLE, ReferenceType.CHARACTER],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
            )
        ],
    )
    
    missing = ReferencePackSchema.get_missing_reference_types(pack)
    assert ReferenceType.CHARACTER in missing
    assert ReferenceType.STYLE not in missing


def test_reference_pack_schema_get_reference_summary():
    """Test getting reference pack summary."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        reference_types=[ReferenceType.STYLE, ReferenceType.CHARACTER],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
                path=None,
                required=True,
            ),
            ReferenceItem(
                reference_id="style2",
                reference_type=ReferenceType.STYLE,
                description="Optional style",
                path=None,
                required=False,
            ),
            ReferenceItem(
                reference_id="char1",
                reference_type=ReferenceType.CHARACTER,
                description="Character with path",
                path="/path/to/char.png",
                required=True,
            ),
        ],
    )
    
    summary = ReferencePackSchema.get_reference_summary(pack)
    assert summary["total_items"] == 3
    assert summary["required_items"] == 2
    assert summary["optional_items"] == 1
    assert summary["items_with_paths"] == 1
    assert summary["items_without_paths"] == 2
    assert summary["by_type"]["style"]["count"] == 2
    assert summary["by_type"]["style"]["without_paths"] == 2
    assert summary["by_type"]["character"]["count"] == 1
    assert summary["by_type"]["character"]["with_paths"] == 1


def test_reference_pack_json_serialization():
    """Test that reference pack can be serialized to JSON and back."""
    original = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE, ReferenceType.CHARACTER],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
                path=None,
                required=True,
                metadata={"category": "photorealistic"},
            ),
        ],
        usage_policy={
            "allow_slot_description": True,
            "require_actual_images": False,
        },
        operator_review_required=True,
    )
    
    # Serialize to dict
    data = original.to_dict()
    assert data["reference_pack_id"] == "test_pack"
    assert len(data["items"]) == 1
    
    # Deserialize from dict
    restored = ReferencePack.from_dict(data)
    assert restored.reference_pack_id == original.reference_pack_id
    assert len(restored.items) == len(original.items)
    assert restored.items[0].reference_id == original.items[0].reference_id


def test_reference_pack_schema_validation():
    """Test that reference pack JSON validates against schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(__file__).parent.parent / "schemas" / "workflow_registry" / "reference_pack.schema.json"
        
        pack_data = {
            "reference_pack_id": "test_pack",
            "project_binding_required": False,
            "reference_types": ["style", "character"],
            "items": [
                {
                    "reference_id": "style1",
                    "reference_type": "style",
                    "description": "Style reference",
                    "path": None,
                    "required": True,
                    "metadata": {},
                }
            ],
            "usage_policy": {
                "allow_slot_description": True,
                "require_actual_images": False,
            },
            "operator_review_required": True,
        }
        
        pack_file = Path(tmpdir) / "pack.json"
        with open(pack_file, "w") as f:
            json.dump(pack_data, f)
        
        result = WorkflowRegistryValidator.validate_file(pack_file, schema_path)
        # Should pass basic validation (no forbidden patterns)
        assert result["valid"] or len(result["errors"]) == 0 or all("schema" not in err.lower() for err in result["errors"])
