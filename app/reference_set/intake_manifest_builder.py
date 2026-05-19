"""
Intake manifest builder for reference set.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .models import (
    IntakeManifest,
    ReferenceFileEntry,
    SlotMappingSummary,
    ReadinessStatus,
    ValidationStatus
)
from .file_validator import FileValidator
from .slot_mapper import SlotMapper


class IntakeManifestBuilder:
    """Builds intake manifest for reference files."""
    
    def __init__(self, dropzone_path: Path, validator: FileValidator, slot_mapper: SlotMapper):
        self.dropzone_path = dropzone_path
        self.validator = validator
        self.slot_mapper = slot_mapper
    
    def scan_dropzone(self) -> List[Path]:
        """Scan dropzone for image files."""
        if not self.dropzone_path.exists():
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        files = []
        
        for ext in image_extensions:
            files.extend(self.dropzone_path.glob(f"*{ext}"))
            files.extend(self.dropzone_path.glob(f"*{ext.upper()}"))
        
        return sorted(files)
    
    def build_manifest(
        self,
        blueprint_stage_id: str,
        manifest_version: str = "1.0.0"
    ) -> IntakeManifest:
        """Build intake manifest from scanned files."""
        scan_timestamp = datetime.now()
        file_entries = []
        
        # Scan for files
        files = self.scan_dropzone()
        
        # Validate each file and create entries
        for file_path in files:
            entry = self._create_file_entry(file_path)
            file_entries.append(entry)
        
        # Map files to slots
        slot_mappings, unmapped_files, unfilled_slots = self.slot_mapper.map_files_to_slots(file_entries)
        
        # Assign slot IDs to file entries
        self._assign_slots_to_entries(file_entries, slot_mappings)
        
        # Compute mapping summary
        mapping_summary = self.slot_mapper.compute_mapping_summary(slot_mappings, unfilled_slots)
        
        return IntakeManifest(
            manifest_version=manifest_version,
            blueprint_stage_id=blueprint_stage_id,
            dropzone_root_path=str(self.dropzone_path),
            scan_timestamp=scan_timestamp,
            reference_files=file_entries,
            slot_mapping_summary=mapping_summary
        )
    
    def _create_file_entry(self, file_path: Path) -> ReferenceFileEntry:
        """Create a file entry with validation."""
        # Get file info
        file_size = file_path.stat().st_size
        file_name = file_path.name
        file_ext = file_path.suffix.lower().lstrip('.')
        
        # Validate file
        validation_result = self.validator.validate_file(str(file_path))
        validation_status = self.validator.determine_validation_status(validation_result)
        
        # Extract SHA256 from validation if available
        sha256 = ""
        if "sha256" in validation_result.checks and validation_result.checks["sha256"].value:
            sha256 = validation_result.checks["sha256"].value
        
        # Extract dimensions if available
        dimensions = None
        if "dimensions" in validation_result.checks and validation_result.checks["dimensions"].value:
            dimensions = validation_result.checks["dimensions"].value
        
        # Determine readability
        readable = validation_result.checks.get("readability", validation_result.checks.get("existence")).passed
        
        return ReferenceFileEntry(
            file_path=str(file_path),
            file_name=file_name,
            file_size_bytes=file_size,
            sha256_checksum=sha256,
            validation_status=validation_status,
            image_dimensions=dimensions,
            file_format=file_ext,
            readable=readable,
            validation_errors=validation_result.errors
        )
    
    def _assign_slots_to_entries(
        self,
        file_entries: List[ReferenceFileEntry],
        slot_mappings: List[Any]
    ) -> None:
        """Assign slot IDs to file entries based on mappings."""
        # Build a mapping from file path to slot ID
        file_to_slot = {}
        for mapping in slot_mappings:
            for file_path in mapping.assigned_files:
                file_to_slot[file_path] = mapping.slot_id
        
        # Assign slot IDs to entries
        for entry in file_entries:
            if entry.file_path in file_to_slot:
                entry.assigned_slot_id = file_to_slot[entry.file_path]
    
    def save_manifest(self, manifest: IntakeManifest, output_path: Path) -> None:
        """Save manifest to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "manifest_version": manifest.manifest_version,
            "blueprint_stage_id": manifest.blueprint_stage_id,
            "dropzone_root_path": manifest.dropzone_root_path,
            "scan_timestamp": manifest.scan_timestamp.isoformat(),
            "reference_files": [
                {
                    "file_path": f.file_path,
                    "file_name": f.file_name,
                    "file_size_bytes": f.file_size_bytes,
                    "sha256_checksum": f.sha256_checksum,
                    "validation_status": f.validation_status.value,
                    "assigned_slot_id": f.assigned_slot_id,
                    "image_dimensions": f.image_dimensions,
                    "file_format": f.file_format,
                    "readable": f.readable,
                    "validation_errors": f.validation_errors
                }
                for f in manifest.reference_files
            ],
            "slot_mapping_summary": {
                "total_slots": manifest.slot_mapping_summary.total_slots,
                "filled_slots": manifest.slot_mapping_summary.filled_slots,
                "missing_required_slots": manifest.slot_mapping_summary.missing_required_slots,
                "readiness_status": manifest.slot_mapping_summary.readiness_status.value
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
