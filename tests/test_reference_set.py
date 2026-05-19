"""
Tests for reference set dropzone/intake bridge.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from PIL import Image
import numpy as np

from app.reference_set import (
    ReferenceSlot,
    ValidationPolicy,
    SlotRole,
    FileValidator,
    SlotMapper,
    ValidationStatus,
    FillStatus,
    MappingConfidence,
    ReadinessStatus
)
from app.reference_set.models import ReferenceFileEntry


@pytest.fixture
def temp_image_file(tmp_path):
    """Create a temporary test image."""
    img = Image.fromarray(np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8))
    img_path = tmp_path / "test_image.jpg"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def validation_policy():
    """Default validation policy."""
    return ValidationPolicy(
        validate_existence=True,
        validate_readability=True,
        validate_sha256=True,
        validate_size=True,
        validate_dimensions=True
    )


class TestValidationPolicy:
    """Test ValidationPolicy model."""
    
    def test_default_policy(self):
        """Test default validation policy."""
        policy = ValidationPolicy()
        assert policy.validate_existence is True
        assert policy.validate_readability is True
        assert policy.validate_sha256 is True
        assert policy.validate_size is True
        assert policy.validate_dimensions is True
        assert policy.fail_on_missing_required is True
    
    def test_custom_policy(self):
        """Test custom validation policy."""
        policy = ValidationPolicy(
            validate_existence=False,
            validate_sha256=False
        )
        assert policy.validate_existence is False
        assert policy.validate_sha256 is False


class TestReferenceSlot:
    """Test ReferenceSlot model."""
    
    def test_slot_creation(self):
        """Test creating a reference slot."""
        slot = ReferenceSlot(
            slot_id="slot_001",
            slot_role=SlotRole.IDENTITY_REFERENCE,
            required=True
        )
        assert slot.slot_id == "slot_001"
        assert slot.slot_role == SlotRole.IDENTITY_REFERENCE
        assert slot.required is True
        assert slot.allowed_formats == ["jpg", "jpeg", "png", "webp"]
    
    def test_slot_with_constraints(self):
        """Test slot with size and dimension constraints."""
        slot = ReferenceSlot(
            slot_id="slot_002",
            slot_role=SlotRole.STYLE_REFERENCE,
            required=False,
            min_dimensions={"width": 1024, "height": 1024},
            max_file_size_mb=10.0
        )
        assert slot.min_dimensions == {"width": 1024, "height": 1024}
        assert slot.max_file_size_mb == 10.0


class TestFileValidator:
    """Test FileValidator."""
    
    def test_validate_existing_file(self, temp_image_file, validation_policy):
        """Test validating an existing file."""
        validator = FileValidator(validation_policy)
        result = validator.validate_file(temp_image_file)
        assert result.file_path == temp_image_file
        assert "existence" in result.checks
        assert result.checks["existence"].passed is True
        assert "readability" in result.checks
        assert result.checks["readability"].passed is True
        assert "sha256" in result.checks
        assert result.checks["sha256"].passed is True
        assert "size" in result.checks
        assert result.checks["size"].passed is True
        assert "dimensions" in result.checks
        assert result.checks["dimensions"].passed is True
    
    def test_validate_nonexistent_file(self, validation_policy):
        """Test validating a nonexistent file."""
        validator = FileValidator(validation_policy)
        result = validator.validate_file("/nonexistent/file.jpg")
        assert result.overall_valid is False
        assert result.checks["existence"].passed is False
    
    def test_determine_validation_status_valid(self, temp_image_file, validation_policy):
        """Test determining validation status for valid file."""
        validator = FileValidator(validation_policy)
        result = validator.validate_file(temp_image_file)
        status = validator.determine_validation_status(result)
        assert status == ValidationStatus.VALID
    
    def test_determine_validation_status_missing(self, validation_policy):
        """Test determining validation status for missing file."""
        validator = FileValidator(validation_policy)
        result = validator.validate_file("/nonexistent/file.jpg")
        status = validator.determine_validation_status(result)
        assert status == ValidationStatus.MISSING
    
    def test_validate_with_slot_constraints(self, temp_image_file, validation_policy):
        """Test validation with slot constraints."""
        slot = ReferenceSlot(
            slot_id="slot_001",
            slot_role=SlotRole.IDENTITY_REFERENCE,
            required=True,
            min_dimensions={"width": 256, "height": 256},
            max_file_size_mb=10.0
        )
        validator = FileValidator(validation_policy)
        result = validator.validate_file(temp_image_file, slot)
        # 512x512 image should pass 256x256 minimum
        assert result.checks["dimensions"].passed is True


class TestSlotMapper:
    """Test SlotMapper."""
    
    def test_exact_filename_matching(self):
        """Test exact filename matching for slots."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True),
            ReferenceSlot("slot_002", SlotRole.STYLE_REFERENCE, True)
        ]
        
        file_entries = [
            ReferenceFileEntry(
                file_path="/path/identity_reference.jpg",
                file_name="identity_reference.jpg",
                file_size_bytes=1024,
                sha256_checksum="abc123",
                validation_status=ValidationStatus.VALID
            ),
            ReferenceFileEntry(
                file_path="/path/style_reference.png",
                file_name="style_reference.png",
                file_size_bytes=2048,
                sha256_checksum="def456",
                validation_status=ValidationStatus.VALID
            )
        ]
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        
        assert len(mappings) == 2
        assert all(m.fill_status == FillStatus.FILLED for m in mappings)
        assert len(unmapped) == 0
        assert len(unfilled) == 0
    
    def test_pattern_matching(self):
        """Test pattern-based filename matching."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True)
        ]
        
        file_entries = [
            ReferenceFileEntry(
                file_path="/path/character_pose.jpg",
                file_name="character_pose.jpg",
                file_size_bytes=1024,
                sha256_checksum="abc123",
                validation_status=ValidationStatus.VALID
            )
        ]
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        
        # "character" should match identity patterns
        assert mappings[0].fill_status == FillStatus.FILLED
        assert mappings[0].mapping_confidence == MappingConfidence.ROLE_INFERENCE
    
    def test_unmapped_files(self):
        """Test detection of unmapped files."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True)
        ]
        
        file_entries = [
            ReferenceFileEntry(
                file_path="/path/random_file.jpg",
                file_name="random_file.jpg",
                file_size_bytes=1024,
                sha256_checksum="abc123",
                validation_status=ValidationStatus.VALID
            )
        ]
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        
        assert len(unmapped) == 1
        assert "/path/random_file.jpg" in unmapped
    
    def test_unfilled_required_slots(self):
        """Test detection of unfilled required slots."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True),
            ReferenceSlot("slot_002", SlotRole.STYLE_REFERENCE, True)
        ]
        
        file_entries = []
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        
        assert len(unfilled) == 2
        assert "slot_001" in unfilled
        assert "slot_002" in unfilled
    
    def test_mapping_summary_ready(self):
        """Test mapping summary when ready."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True)
        ]
        
        file_entries = [
            ReferenceFileEntry(
                file_path="/path/identity_reference.jpg",
                file_name="identity_reference.jpg",
                file_size_bytes=1024,
                sha256_checksum="abc123",
                validation_status=ValidationStatus.VALID
            )
        ]
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        summary = mapper.compute_mapping_summary(mappings, unfilled)
        
        assert summary.total_slots == 1
        assert summary.filled_slots == 1
        assert summary.readiness_status == ReadinessStatus.READY
    
    def test_mapping_summary_pending(self):
        """Test mapping summary when pending operator supply."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True),
            ReferenceSlot("slot_002", SlotRole.STYLE_REFERENCE, False)
        ]
        
        file_entries = [
            ReferenceFileEntry(
                file_path="/path/identity_reference.jpg",
                file_name="identity_reference.jpg",
                file_size_bytes=1024,
                sha256_checksum="abc123",
                validation_status=ValidationStatus.VALID
            )
        ]
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        summary = mapper.compute_mapping_summary(mappings, unfilled)
        
        assert summary.total_slots == 2
        assert summary.filled_slots == 1
        assert summary.readiness_status == ReadinessStatus.PENDING_OPERATOR_SUPPLY
    
    def test_mapping_summary_blocked(self):
        """Test mapping summary when blocked by missing required."""
        slots = [
            ReferenceSlot("slot_001", SlotRole.IDENTITY_REFERENCE, True)
        ]
        
        file_entries = []
        
        mapper = SlotMapper(slots)
        mappings, unmapped, unfilled = mapper.map_files_to_slots(file_entries)
        summary = mapper.compute_mapping_summary(mappings, unfilled)
        
        assert summary.total_slots == 1
        assert summary.filled_slots == 0
        assert summary.readiness_status == ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE


class TestReferenceFileEntry:
    """Test ReferenceFileEntry model."""
    
    def test_file_entry_creation(self):
        """Test creating a file entry."""
        entry = ReferenceFileEntry(
            file_path="/path/to/file.jpg",
            file_name="file.jpg",
            file_size_bytes=1024,
            sha256_checksum="abc123def456",
            validation_status=ValidationStatus.VALID
        )
        assert entry.file_path == "/path/to/file.jpg"
        assert entry.file_name == "file.jpg"
        assert entry.file_size_bytes == 1024
        assert entry.validation_status == ValidationStatus.VALID
    
    def test_file_entry_with_dimensions(self):
        """Test file entry with image dimensions."""
        entry = ReferenceFileEntry(
            file_path="/path/to/file.jpg",
            file_name="file.jpg",
            file_size_bytes=1024,
            sha256_checksum="abc123def456",
            validation_status=ValidationStatus.VALID,
            image_dimensions={"width": 1024, "height": 768}
        )
        assert entry.image_dimensions == {"width": 1024, "height": 768}


class TestEnums:
    """Test enum values."""
    
    def test_slot_role_values(self):
        """Test slot role enum values."""
        assert SlotRole.IDENTITY_REFERENCE.value == "identity_reference"
        assert SlotRole.STYLE_REFERENCE.value == "style_reference"
        assert SlotRole.CAMERA_REFERENCE.value == "camera_reference"
        assert SlotRole.LIGHTING_REFERENCE.value == "lighting_reference"
        assert SlotRole.ANATOMY_REFERENCE.value == "anatomy_reference"
        assert SlotRole.QUALITY_REFERENCE.value == "quality_reference"
        assert SlotRole.NEGATIVE_REFERENCE.value == "negative_reference"
    
    def test_validation_status_values(self):
        """Test validation status enum values."""
        assert ValidationStatus.VALID.value == "valid"
        assert ValidationStatus.MISSING.value == "missing"
        assert ValidationStatus.UNREADABLE.value == "unreadable"
    
    def test_fill_status_values(self):
        """Test fill status enum values."""
        assert FillStatus.FILLED.value == "filled"
        assert FillStatus.PARTIAL.value == "partial"
        assert FillStatus.EMPTY.value == "empty"
    
    def test_readiness_status_values(self):
        """Test readiness status enum values."""
        assert ReadinessStatus.READY.value == "ready"
        assert ReadinessStatus.PENDING_OPERATOR_SUPPLY.value == "pending_operator_supply"
        assert ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE.value == "blocked_missing_required_reference"
