"""Tests for project-agnostic reference pack intake/canonicalization layer.

RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from app.reference_pack.models import (
    ReferenceSlot,
    ReferenceAsset,
    ReferenceUsagePolicy,
    ReferencePack,
    ReferenceCanonicalizationReport,
    SlotCategory,
    SlotStatus,
    AssetStatus,
)
from app.reference_pack.canonicalizer import ReferenceCanonicalizer
from app.reference_pack.intake import ReferencePackIntake
from app.reference_pack.validator import ReferencePackValidator


class TestReferenceSlotTaxonomy:
    """Tests for reference slot taxonomy loaded from JSON."""

    def test_taxonomy_file_exists(self):
        """Test taxonomy JSON file exists."""
        taxonomy_path = Path(__file__).parent.parent / "app" / "reference_pack" / "reference_slot_taxonomy.json"
        assert taxonomy_path.exists()

    def test_taxonomy_structure(self):
        """Test taxonomy has required structure."""
        taxonomy_path = Path(__file__).parent.parent / "app" / "reference_pack" / "reference_slot_taxonomy.json"
        with open(taxonomy_path) as f:
            taxonomy = json.load(f)
        
        assert taxonomy["document_type"] == "reference_slot_taxonomy"
        assert taxonomy["version"] == "1.0"
        assert taxonomy["task_id"] == "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001"
        assert taxonomy["project_agnostic"] is True
        assert len(taxonomy["slots"]) > 0

    def test_slot_categories(self):
        """Test slots are organized by category."""
        taxonomy_path = Path(__file__).parent.parent / "app" / "reference_pack" / "reference_slot_taxonomy.json"
        with open(taxonomy_path) as f:
            taxonomy = json.load(f)
        
        categories = set(slot["category"] for slot in taxonomy["slots"])
        expected_categories = {
            "character_pose",
            "character_expression",
            "character_detail",
            "technical_reference",
        }
        assert categories == expected_categories


class TestReferenceSlot:
    """Tests for ReferenceSlot model."""

    def test_slot_creation(self):
        """Test creating a reference slot."""
        slot = ReferenceSlot(
            slot_id="character_front_full_body",
            category=SlotCategory.CHARACTER_POSE,
            description="Front full body character pose",
            required=False,
            status=SlotStatus.PENDING_OPERATOR_SUPPLY,
        )
        
        assert slot.slot_id == "character_front_full_body"
        assert slot.category == SlotCategory.CHARACTER_POSE
        assert slot.required is False
        assert slot.status == SlotStatus.PENDING_OPERATOR_SUPPLY
        assert len(slot.assets) == 0

    def test_slot_with_assets(self):
        """Test slot with assets."""
        asset = ReferenceAsset(
            asset_id="asset_001",
            file_path="/path/to/image.jpg",
            format="jpg",
            width=1920,
            height=1080,
            status=AssetStatus.PRESENT,
        )
        slot = ReferenceSlot(
            slot_id="character_front_full_body",
            category=SlotCategory.CHARACTER_POSE,
            description="Front full body character pose",
            required=False,
            status=SlotStatus.POPULATED,
            assets=[asset],
        )
        
        assert len(slot.assets) == 1
        assert slot.assets[0].asset_id == "asset_001"
        assert slot.status == SlotStatus.POPULATED


class TestReferenceAsset:
    """Tests for ReferenceAsset model."""

    def test_asset_creation(self):
        """Test creating a reference asset."""
        asset = ReferenceAsset(
            asset_id="asset_001",
            file_path="/path/to/image.jpg",
            format="jpg",
            width=1920,
            height=1080,
        )
        
        assert asset.asset_id == "asset_001"
        assert asset.file_path == "/path/to/image.jpg"
        assert asset.format == "jpg"
        assert asset.width == 1920
        assert asset.height == 1080


class TestReferenceUsagePolicy:
    """Tests for ReferenceUsagePolicy model."""

    def test_policy_creation(self):
        """Test creating a usage policy."""
        policy = ReferenceUsagePolicy(
            usage_policy={
                "character_references": "allowed_for_visual_generation",
                "style_references": "allowed_for_visual_generation",
                "negative_references": "allowed_for_rejection_guidance",
            },
            constraints={
                "no_face_substitution": True,
                "no_background_substitution": True,
            },
        )
        
        assert policy.document_type == "reference_usage_policy"
        assert policy.project_agnostic is True
        assert policy.usage_policy["character_references"] == "allowed_for_visual_generation"
        assert policy.constraints["no_face_substitution"] is True


class TestReferencePack:
    """Tests for ReferencePack model."""

    def test_pack_creation(self):
        """Test creating a reference pack."""
        pack = ReferencePack(
            reference_pack_id="test_pack",
        )
        
        assert pack.document_type == "reference_pack_manifest"
        assert pack.reference_pack_id == "test_pack"
        assert pack.project_agnostic is True
        assert len(pack.slots) == 0

    def test_pack_with_slots(self):
        """Test pack with slots."""
        slot = ReferenceSlot(
            slot_id="character_front_full_body",
            category=SlotCategory.CHARACTER_POSE,
            description="Front full body character pose",
            required=False,
            status=SlotStatus.PENDING_OPERATOR_SUPPLY,
        )
        pack = ReferencePack(
            reference_pack_id="test_pack",
            slots={"character_front_full_body": slot},
        )
        
        assert len(pack.slots) == 1
        assert pack.slots["character_front_full_body"].slot_id == "character_front_full_body"


class TestReferenceCanonicalizationReport:
    """Tests for ReferenceCanonicalizationReport model."""

    def test_report_creation(self):
        """Test creating a canonicalization report."""
        report = ReferenceCanonicalizationReport(
            reference_pack_id="test_pack",
            canonicalization_status="complete",
        )
        
        assert report.document_type == "reference_canonicalization_report"
        assert report.project_agnostic is True
        assert report.canonicalization_status == "complete"


class TestReferencePackCanonicalizer:
    """Tests for ReferenceCanonicalizer."""

    def test_init_pack(self, tmp_path):
        """Test initializing a reference pack."""
        pack = ReferencePackIntake.create_default_pack("test_pack")
        
        assert pack is not None
        assert pack.reference_pack_id == "test_pack"
        assert pack.project_agnostic is True
        assert len(pack.slots) > 0

    def test_validate_pack(self, tmp_path):
        """Test validating a reference pack."""
        pack = ReferencePackIntake.create_default_pack("test_pack")
        is_valid, errors = ReferencePackIntake.validate_pack(pack)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_generate_readiness_report(self, tmp_path):
        """Test generating readiness report."""
        pack = ReferencePackIntake.create_default_pack("test_pack")
        report = ReferenceCanonicalizer.canonicalize_pack(pack)
        
        assert report is not None
        assert report.document_type == "reference_canonicalization_report"
        assert report.canonicalization_status == "complete"


class TestReferencePackValidator:
    """Tests for ReferencePackValidator."""

    def test_validate_empty_pack(self, tmp_path):
        """Test validating an empty pack."""
        pack = ReferencePack(
            reference_pack_id="test_pack",
            metadata={
                "supports_future_references": True,
                "missing_file_status": "pending_operator_supply",
            },
        )
        is_valid, errors = ReferencePackIntake.validate_pack(pack)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_required_slots(self, tmp_path):
        """Test that required slots are validated."""
        # Create pack with only optional slots
        pack = ReferencePack(
            reference_pack_id="test_pack",
            slots={},
            metadata={
                "supports_future_references": True,
                "missing_file_status": "pending_operator_supply",
            },
        )
        is_valid, errors = ReferencePackIntake.validate_pack(pack)
        
        # Should still be valid since optional slots can be empty
        assert is_valid is True


class TestReferencePackIntegration:
    """Integration tests for reference pack workflow."""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow: init -> validate -> report."""
        # Initialize pack
        pack = ReferencePackIntake.create_default_pack("test_pack")
        pack_path = tmp_path / "reference_pack_manifest.json"
        ReferencePackIntake.save_pack_to_file(pack, pack_path)
        
        # Validate pack
        loaded_pack = ReferencePackIntake.load_pack_from_file(pack_path)
        is_valid, errors = ReferencePackIntake.validate_pack(loaded_pack)
        
        assert is_valid is True
        
        # Generate readiness report
        report = ReferenceCanonicalizer.canonicalize_pack(loaded_pack)
        
        assert report.canonicalization_status == "complete"
        
        # Verify file exists
        assert pack_path.exists()

    def test_inspect_pack(self, tmp_path):
        """Test inspecting a reference pack."""
        pack = ReferencePackIntake.create_default_pack("test_pack")
        pack_path = tmp_path / "reference_pack_manifest.json"
        ReferencePackIntake.save_pack_to_file(pack, pack_path)
        
        loaded_pack = ReferencePackIntake.load_pack_from_file(pack_path)
        
        assert loaded_pack is not None
        assert loaded_pack.reference_pack_id == "test_pack"
        assert len(loaded_pack.slots) > 0
