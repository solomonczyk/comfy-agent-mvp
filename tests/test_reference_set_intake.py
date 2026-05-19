"""
Tests for reference set intake validation.

Tests read-only validation of operator-supplied canonical references.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from reference_set.reference_set_intake import ReferenceSetIntakeValidator
from reference_set.models import ValidationPolicy


class TestReferenceSetIntakeValidator:
    """Test reference set intake validation."""
    
    def test_source_folder_missing(self):
        """Test validation when source folder is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "nonexistent"
            output_path = Path(tmpdir) / "output"
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            assert result["status"] == "completed"
            assert result["scan_report"]["source_folder_exists"] == False
            assert result["scan_report"]["scan_status"] == "blocked_missing_source_folder"
            assert result["scan_report"]["total_files"] == 0
    
    def test_empty_source_folder(self):
        """Test validation when source folder exists but is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create empty slot folders
            for slot_id in ["01_identity", "02_face_details", "03_costume_materials"]:
                (source_path / slot_id).mkdir()
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            assert result["status"] == "completed"
            assert result["scan_report"]["source_folder_exists"] == True
            assert result["scan_report"]["total_files"] == 0
            assert result["scan_report"]["scan_status"] == "pending_operator_supply"
            assert result["validation_report"]["overall_status"] == "no_files"
            assert result["readiness_report"]["readiness_status"] == "pending_operator_supply"
    
    def test_valid_images(self):
        """Test validation with valid images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with valid image
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            # Create a test PNG image
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "test_identity.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            assert result["status"] == "completed"
            assert result["scan_report"]["source_folder_exists"] == True
            assert result["scan_report"]["total_files"] == 1
            assert result["scan_report"]["scan_status"] == "scanned"
            assert result["validation_report"]["overall_status"] == "all_valid"
            assert result["validation_report"]["validation_summary"]["valid_files"] == 1
            assert result["validation_report"]["validation_summary"]["invalid_files"] == 0
    
    def test_invalid_extension(self):
        """Test validation with invalid file extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with invalid file
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            # Create a text file (invalid)
            test_file = identity_path / "test.txt"
            test_file.write_text("invalid")
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            assert result["status"] == "completed"
            assert result["scan_report"]["total_files"] == 0  # Invalid extensions are filtered out
            assert result["validation_report"]["overall_status"] == "no_files"
    
    def test_unreadable_file(self):
        """Test validation with unreadable file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            # Create a corrupted PNG file
            test_file = identity_path / "corrupted.png"
            test_file.write_bytes(b"NOT A REAL PNG FILE")
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            assert result["status"] == "completed"
            # File should be discovered but fail validation
            assert result["scan_report"]["total_files"] == 1
            assert result["validation_report"]["overall_status"] == "all_invalid"
            assert result["validation_report"]["validation_summary"]["invalid_files"] == 1
    
    def test_sha256_calculation(self):
        """Test SHA256 checksum calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with valid image
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            # Create a test PNG image
            img = Image.new('RGB', (512, 512), color='blue')
            test_file = identity_path / "test.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path),
                validation_policy=ValidationPolicy(validate_sha256=True)
            )
            
            result = validator.validate_intake()
            
            # Check that SHA256 was calculated
            validation = result["validation_report"]["file_validations"][0]
            assert "sha256" in validation["checks"]
            assert validation["checks"]["sha256"]["passed"] == True
            assert validation["checks"]["sha256"]["value"] is not None
            assert len(validation["checks"]["sha256"]["value"]) == 64  # SHA256 hex length
    
    def test_dimensions_check(self):
        """Test image dimensions validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with small image (below minimum)
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            # Create a small image (below 512x512 minimum)
            img = Image.new('RGB', (256, 256), color='green')
            test_file = identity_path / "small.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path),
                validation_policy=ValidationPolicy(validate_dimensions=True)
            )
            
            result = validator.validate_intake()
            
            # Check dimensions validation
            validation = result["validation_report"]["file_validations"][0]
            assert "dimensions" in validation["checks"]
            # Small image should fail minimum dimension check
            assert validation["checks"]["dimensions"]["passed"] == False
            # Check that dimensions were actually measured
            assert validation["checks"]["dimensions"]["value"] == {"width": 256, "height": 256}
            # Check that overall validation failed due to dimensions
            assert validation["overall_valid"] == False
            assert any("insufficient" in error.lower() for error in validation["errors"])
    
    def test_slot_mapping(self):
        """Test slot mapping of files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folders with images
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "identity_test.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            # Check slot mapping
            slot_mapping = result["slot_mapping_report"]
            assert len(slot_mapping["slot_mappings"]) == 6  # All slots defined
            assert slot_mapping["unmapped_files"] == []
            
            # Check identity slot is filled
            identity_mapping = next(m for m in slot_mapping["slot_mappings"] if m["slot_id"] == "01_identity")
            assert identity_mapping["fill_status"] == "filled"
            assert len(identity_mapping["assigned_files"]) == 1
    
    def test_readiness_assessment(self):
        """Test readiness assessment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folders
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "identity.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            # Check readiness
            readiness = result["readiness_report"]
            assert readiness["readiness_status"] == "ready_for_operator_reference_review"
            assert readiness["generation_gate_status"]["gate_open"] == False
            assert readiness["metadata"]["visual_acceptance_executed"] == False
            assert readiness["metadata"]["operator_visual_acceptance_executed"] == False
            assert readiness["metadata"]["generation_authorized"] == False
    
    def test_evidence_event_creation(self):
        """Test evidence trace event creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with valid image
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "identity.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            # Check evidence event
            evidence = result["evidence_event"]
            assert evidence["task_id"] == "RC-COMBINE-V2-REFERENCE-SET-INTAKE-VALIDATION-001"
            assert evidence["source_layer"] == "reference_set"
            assert evidence["decision_status"] == "ready"
            assert evidence["allowed_next_action"] == "operator_reference_review_required"
            assert "event_id" in evidence
            assert "timestamp" in evidence
    
    def test_no_visual_acceptance(self):
        """Test that visual acceptance is never executed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with valid image
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "identity.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            # Verify constraints
            readiness = result["readiness_report"]
            assert readiness["metadata"]["visual_acceptance_executed"] == False
            assert readiness["metadata"]["operator_visual_acceptance_executed"] == False
            assert readiness["metadata"]["generation_authorized"] == False
            assert readiness["generation_gate_status"]["gate_open"] == False
    
    def test_no_generation_authorized(self):
        """Test that generation is never authorized during intake validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "canonical_references"
            source_path.mkdir()
            output_path = Path(tmpdir) / "output"
            
            # Create slot folder with valid image
            identity_path = source_path / "01_identity"
            identity_path.mkdir()
            
            img = Image.new('RGB', (1024, 1024), color='red')
            test_file = identity_path / "identity.png"
            img.save(test_file)
            
            validator = ReferenceSetIntakeValidator(
                source_path=str(source_path),
                blueprint_stage_id="TEST-001",
                output_path=str(output_path)
            )
            
            result = validator.validate_intake()
            
            # Verify generation is never authorized
            readiness = result["readiness_report"]
            assert readiness["generation_gate_status"]["gate_open"] == False
            assert readiness["metadata"]["generation_authorized"] == False
            
            evidence = result["evidence_event"]
            assert "generation" in evidence["blocked_actions"] or evidence["decision_status"] == "ready"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
