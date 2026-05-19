"""
Artifact writer for reference set dropzone/intake bridge.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .models import (
    DropzoneContract,
    IntakeManifest,
    SlotMapping,
    SlotMappingSummary,
    ValidationStatus,
    ReadinessStatus
)
from .file_validator import FileValidator, FileValidationResult


class ArtifactWriter:
    """Writes reference set artifacts to disk."""
    
    def __init__(self, output_root: Path):
        self.output_root = output_root
        self.reference_set_output = output_root / "project_agnostic" / "reference_set"
    
    def write_dropzone_contract(self, contract: DropzoneContract) -> Path:
        """Write dropzone contract artifact."""
        output_path = self.reference_set_output / "reference_set_dropzone_contract.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "contract_version": contract.contract_version,
            "blueprint_stage_id": contract.blueprint_stage_id,
            "dropzone_root_path": contract.dropzone_root_path,
            "required_reference_slots": [
                {
                    "slot_id": s.slot_id,
                    "slot_role": s.slot_role.value,
                    "required": s.required,
                    "allowed_formats": s.allowed_formats,
                    "min_dimensions": s.min_dimensions,
                    "max_file_size_mb": s.max_file_size_mb
                }
                for s in contract.required_reference_slots
            ],
            "validation_policy": {
                "validate_existence": contract.validation_policy.validate_existence,
                "validate_readability": contract.validation_policy.validate_readability,
                "validate_sha256": contract.validation_policy.validate_sha256,
                "validate_size": contract.validation_policy.validate_size,
                "validate_dimensions": contract.validation_policy.validate_dimensions,
                "fail_on_missing_required": contract.validation_policy.fail_on_missing_required
            },
            "intake_manifest_path": contract.intake_manifest_path,
            "created_at": contract.created_at.isoformat(),
            "operator_instructions": contract.operator_instructions
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def write_intake_manifest(self, manifest: IntakeManifest) -> Path:
        """Write intake manifest artifact."""
        output_path = self.reference_set_output / "reference_file_intake_manifest.json"
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
        
        return output_path
    
    def write_slot_mapping_report(
        self,
        blueprint_stage_id: str,
        slot_mappings: List[SlotMapping],
        unmapped_files: List[str],
        unfilled_slots: List[str]
    ) -> Path:
        """Write slot mapping report artifact."""
        output_path = self.reference_set_output / "reference_slot_mapping_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "report_version": "1.0.0",
            "blueprint_stage_id": blueprint_stage_id,
            "mapping_timestamp": datetime.now().isoformat(),
            "slot_mappings": [
                {
                    "slot_id": m.slot_id,
                    "slot_role": m.slot_role.value,
                    "required": m.required,
                    "assigned_files": m.assigned_files,
                    "fill_status": m.fill_status.value,
                    "mapping_confidence": m.mapping_confidence.value
                }
                for m in slot_mappings
            ],
            "unmapped_files": unmapped_files,
            "unfilled_slots": unfilled_slots
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def write_validation_report(
        self,
        blueprint_stage_id: str,
        validation_policy: Any,
        file_validations: List[FileValidationResult],
        overall_status: str
    ) -> Path:
        """Write validation report artifact."""
        output_path = self.reference_set_output / "reference_file_validation_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Compute summary
        total_files = len(file_validations)
        valid_files = sum(1 for v in file_validations if v.overall_valid)
        invalid_files = total_files - valid_files
        missing_files = sum(
            1 for v in file_validations
            if not v.checks.get("existence", type('obj', (object,), {'passed': True})()).passed
        )
        
        data = {
            "report_version": "1.0.0",
            "blueprint_stage_id": blueprint_stage_id,
            "validation_timestamp": datetime.now().isoformat(),
            "validation_policy": {
                "validate_existence": validation_policy.validate_existence,
                "validate_readability": validation_policy.validate_readability,
                "validate_sha256": validation_policy.validate_sha256,
                "validate_size": validation_policy.validate_size,
                "validate_dimensions": validation_policy.validate_dimensions,
                "fail_on_missing_required": validation_policy.fail_on_missing_required
            },
            "file_validations": [
                {
                    "file_path": v.file_path,
                    "checks": {
                        check_name: {
                            "passed": check.passed,
                            "message": check.message,
                            "value": check.value
                        }
                        for check_name, check in v.checks.items()
                    },
                    "overall_valid": v.overall_valid,
                    "errors": v.errors
                }
                for v in file_validations
            ],
            "overall_status": overall_status,
            "validation_summary": {
                "total_files": total_files,
                "valid_files": valid_files,
                "invalid_files": invalid_files,
                "missing_files": missing_files
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
