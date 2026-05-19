"""
Reference set intake validation for operator-supplied canonical references.

Read-only validation of reference images including:
- Source folder scanning
- File validation (existence, readability, sha256, size, dimensions, extension)
- Slot mapping using existing taxonomy
- Readiness assessment (ready_for_operator_reference_review only)
- Evidence trace recording

NO visual acceptance, NO generation, NO retry, NO ComfyUI submit, NO image editing.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import uuid

from .models import (
    ValidationPolicy,
    ReferenceSlot,
    SlotRole,
    FillStatus,
    MappingConfidence,
    ReadinessStatus,
    ValidationStatus
)


class ReferenceSetIntakeValidator:
    """Validates operator-supplied reference images for intake."""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    MIN_FILE_SIZE_BYTES = 1024  # 1KB minimum
    
    def __init__(
        self,
        source_path: str,
        blueprint_stage_id: str,
        output_path: str,
        validation_policy: Optional[ValidationPolicy] = None
    ):
        self.source_path = Path(source_path)
        self.blueprint_stage_id = blueprint_stage_id
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        if validation_policy is None:
            validation_policy = ValidationPolicy()
        self.validation_policy = validation_policy
        
        # Define slot taxonomy based on folder structure
        self.slots = self._define_slot_taxonomy()
    
    def _define_slot_taxonomy(self) -> List[ReferenceSlot]:
        """Define reference slot taxonomy based on folder structure."""
        return [
            ReferenceSlot(
                slot_id="01_identity",
                slot_role=SlotRole.IDENTITY_REFERENCE,
                required=True,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            ),
            ReferenceSlot(
                slot_id="02_face_details",
                slot_role=SlotRole.IDENTITY_REFERENCE,
                required=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            ),
            ReferenceSlot(
                slot_id="03_costume_materials",
                slot_role=SlotRole.STYLE_REFERENCE,
                required=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            ),
            ReferenceSlot(
                slot_id="04_style_light",
                slot_role=SlotRole.LIGHTING_REFERENCE,
                required=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            ),
            ReferenceSlot(
                slot_id="05_environment",
                slot_role=SlotRole.STYLE_REFERENCE,
                required=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            ),
            ReferenceSlot(
                slot_id="06_quality_negative",
                slot_role=SlotRole.NEGATIVE_REFERENCE,
                required=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                min_dimensions={"width": 512, "height": 512},
                max_file_size_mb=10.0
            )
        ]
    
    def validate_intake(self) -> Dict[str, Any]:
        """Perform complete intake validation and generate all artifacts."""
        # Step 1: Source scan
        scan_report = self._scan_source()
        
        # Step 2: File validation
        validation_report = self._validate_files(scan_report["discovered_files"])
        
        # Step 3: Slot mapping
        slot_mapping_report = self._map_slots(scan_report["discovered_files"])
        
        # Step 4: Readiness assessment
        readiness_report = self._assess_readiness(slot_mapping_report)
        
        # Step 5: Evidence trace event
        evidence_event = self._create_evidence_event(validation_report)
        
        # Step 6: Write all artifacts
        artifacts = {
            "source_scan_report": self._write_scan_report(scan_report),
            "validation_report": self._write_validation_report(validation_report),
            "slot_mapping_report": self._write_slot_mapping_report(slot_mapping_report),
            "readiness_report": self._write_readiness_report(readiness_report),
            "evidence_event": self._write_evidence_event(evidence_event)
        }
        
        return {
            "status": "completed",
            "artifacts": artifacts,
            "scan_report": scan_report,
            "validation_report": validation_report,
            "slot_mapping_report": slot_mapping_report,
            "readiness_report": readiness_report,
            "evidence_event": evidence_event
        }
    
    def _scan_source(self) -> Dict[str, Any]:
        """Scan source folder for image files."""
        scan_timestamp = datetime.now().isoformat()
        discovered_files = []
        slot_file_counts = {}
        
        if not self.source_path.exists():
            return {
                "scan_timestamp": scan_timestamp,
                "source_folder_exists": False,
                "source_folder_path": str(self.source_path),
                "discovered_files": [],
                "slot_file_counts": {},
                "total_files": 0,
                "scan_status": "blocked_missing_source_folder"
            }
        
        # Scan each slot folder
        for slot in self.slots:
            slot_path = self.source_path / slot.slot_id
            slot_files = []
            
            if slot_path.exists() and slot_path.is_dir():
                for ext in self.ALLOWED_EXTENSIONS:
                    slot_files.extend(slot_path.glob(f"*{ext}"))
                    slot_files.extend(slot_path.glob(f"*{ext.upper()}"))
            
            # Deduplicate files (case-insensitive on Windows)
            seen = set()
            unique_files = []
            for f in slot_files:
                normalized = str(f).lower()
                if normalized not in seen:
                    seen.add(normalized)
                    unique_files.append(f)
            slot_files = unique_files
            
            slot_file_counts[slot.slot_id] = len(slot_files)
            discovered_files.extend([
                {"file_path": str(f), "slot_id": slot.slot_id}
                for f in slot_files
            ])
        
        return {
            "scan_timestamp": scan_timestamp,
            "source_folder_exists": True,
            "source_folder_path": str(self.source_path),
            "discovered_files": discovered_files,
            "slot_file_counts": slot_file_counts,
            "total_files": len(discovered_files),
            "scan_status": "scanned" if discovered_files else "pending_operator_supply"
        }
    
    def _validate_files(self, discovered_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate discovered files."""
        validation_timestamp = datetime.now().isoformat()
        file_validations = []
        
        for file_info in discovered_files:
            file_path = file_info["file_path"]
            slot_id = file_info["slot_id"]
            slot = next((s for s in self.slots if s.slot_id == slot_id), None)
            
            validation = self._validate_single_file(file_path, slot)
            validation["slot_id"] = slot_id
            file_validations.append(validation)
        
        # Determine overall status
        if not file_validations:
            overall_status = "no_files"
        elif all(v["overall_valid"] for v in file_validations):
            overall_status = "all_valid"
        elif any(v["overall_valid"] for v in file_validations):
            overall_status = "some_invalid"
        else:
            overall_status = "all_invalid"
        
        return {
            "report_version": "1.0.0",
            "blueprint_stage_id": self.blueprint_stage_id,
            "validation_timestamp": validation_timestamp,
            "validation_policy": {
                "validate_existence": self.validation_policy.validate_existence,
                "validate_readability": self.validation_policy.validate_readability,
                "validate_sha256": self.validation_policy.validate_sha256,
                "validate_size": self.validation_policy.validate_size,
                "validate_dimensions": self.validation_policy.validate_dimensions,
                "fail_on_missing_required": self.validation_policy.fail_on_missing_required
            },
            "file_validations": file_validations,
            "overall_status": overall_status,
            "validation_summary": {
                "total_files": len(file_validations),
                "valid_files": sum(1 for v in file_validations if v["overall_valid"]),
                "invalid_files": sum(1 for v in file_validations if not v["overall_valid"]),
                "missing_files": 0
            }
        }
    
    def _validate_single_file(self, file_path: str, slot: Optional[ReferenceSlot]) -> Dict[str, Any]:
        """Validate a single file."""
        checks = {}
        errors = []
        
        # Existence check
        path = Path(file_path)
        exists = path.exists() and path.is_file()
        checks["existence"] = {
            "passed": exists,
            "message": "File exists" if exists else "File does not exist"
        }
        
        if not exists:
            return {
                "file_path": file_path,
                "checks": checks,
                "overall_valid": False,
                "errors": ["File does not exist"]
            }
        
        # Extension check
        ext = path.suffix.lower()
        valid_ext = ext in self.ALLOWED_EXTENSIONS
        checks["extension"] = {
            "passed": valid_ext,
            "message": f"Extension {ext} allowed" if valid_ext else f"Extension {ext} not allowed",
            "value": ext
        }
        
        if not valid_ext:
            errors.append(f"Invalid extension: {ext}")
            return {
                "file_path": file_path,
                "checks": checks,
                "overall_valid": False,
                "errors": errors
            }
        
        # Readability check
        try:
            with open(path, 'rb') as f:
                f.read(1)
            checks["readability"] = {
                "passed": True,
                "message": "File is readable"
            }
        except Exception as e:
            checks["readability"] = {
                "passed": False,
                "message": f"File is not readable: {str(e)}"
            }
            errors.append(checks["readability"]["message"])
            return {
                "file_path": file_path,
                "checks": checks,
                "overall_valid": False,
                "errors": errors
            }
        
        # SHA256 checksum
        if self.validation_policy.validate_sha256:
            try:
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                checksum = sha256_hash.hexdigest()
                checks["sha256"] = {
                    "passed": True,
                    "message": "SHA256 checksum computed",
                    "value": checksum
                }
            except Exception as e:
                checks["sha256"] = {
                    "passed": False,
                    "message": f"Failed to compute SHA256: {str(e)}"
                }
                errors.append(checks["sha256"]["message"])
        
        # File size
        if self.validation_policy.validate_size:
            try:
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)
                
                size_ok = size_bytes >= self.MIN_FILE_SIZE_BYTES
                if slot and slot.max_file_size_mb:
                    size_ok = size_ok and size_mb <= slot.max_file_size_mb
                
                checks["size"] = {
                    "passed": size_ok,
                    "message": f"File size {size_mb:.2f}MB",
                    "value": size_bytes
                }
                
                if not size_ok:
                    if size_bytes < self.MIN_FILE_SIZE_BYTES:
                        errors.append(f"File too small: {size_bytes} bytes")
                    elif slot and slot.max_file_size_mb and size_mb > slot.max_file_size_mb:
                        errors.append(f"File too large: {size_mb:.2f}MB exceeds {slot.max_file_size_mb}MB")
            except Exception as e:
                checks["size"] = {
                    "passed": False,
                    "message": f"Failed to check file size: {str(e)}"
                }
                errors.append(checks["size"]["message"])
        
        # Dimensions
        if self.validation_policy.validate_dimensions:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    
                    dim_ok = True
                    if slot and slot.min_dimensions:
                        min_width = slot.min_dimensions.get("width", 0)
                        min_height = slot.min_dimensions.get("height", 0)
                        dim_ok = width >= min_width and height >= min_height
                    
                    checks["dimensions"] = {
                        "passed": dim_ok,
                        "message": f"Dimensions {width}x{height}",
                        "value": {"width": width, "height": height}
                    }
                    
                    if not dim_ok:
                        errors.append(f"Dimensions insufficient: {width}x{height}")
            except Exception as e:
                checks["dimensions"] = {
                    "passed": False,
                    "message": f"Failed to check dimensions: {str(e)}"
                }
                errors.append(checks["dimensions"]["message"])
        
        overall_valid = all(check["passed"] for check in checks.values())
        
        return {
            "file_path": file_path,
            "checks": checks,
            "overall_valid": overall_valid,
            "errors": errors
        }
    
    def _map_slots(self, discovered_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Map files to slots."""
        mapping_timestamp = datetime.now().isoformat()
        slot_mappings = []
        unmapped_files = []
        unfilled_slots = []
        
        # Build file list by slot
        files_by_slot = {slot.slot_id: [] for slot in self.slots}
        for file_info in discovered_files:
            slot_id = file_info["slot_id"]
            if slot_id in files_by_slot:
                files_by_slot[slot_id].append(file_info["file_path"])
        
        # Create slot mappings
        for slot in self.slots:
            assigned_files = files_by_slot.get(slot.slot_id, [])
            
            if assigned_files:
                fill_status = "filled"
                mapping_confidence = "exact_match"
            else:
                fill_status = "empty"
                mapping_confidence = "none"
                if slot.required:
                    unfilled_slots.append(slot.slot_id)
            
            slot_mappings.append({
                "slot_id": slot.slot_id,
                "slot_role": slot.slot_role.value,
                "required": slot.required,
                "assigned_files": assigned_files,
                "fill_status": fill_status,
                "mapping_confidence": mapping_confidence
            })
        
        # Find unmapped files (should be none with folder-based structure)
        mapped_files = set()
        for mapping in slot_mappings:
            mapped_files.update(mapping["assigned_files"])
        
        for file_info in discovered_files:
            if file_info["file_path"] not in mapped_files:
                unmapped_files.append(file_info["file_path"])
        
        return {
            "report_version": "1.0.0",
            "blueprint_stage_id": self.blueprint_stage_id,
            "mapping_timestamp": mapping_timestamp,
            "slot_mappings": slot_mappings,
            "unmapped_files": unmapped_files,
            "unfilled_slots": unfilled_slots
        }
    
    def _assess_readiness(self, slot_mapping_report: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness status."""
        unfilled_required = [
            s["slot_id"] for s in slot_mapping_report["slot_mappings"]
            if s["required"] and s["fill_status"] == "empty"
        ]
        
        if unfilled_required:
            readiness_status = "pending_operator_supply"
        else:
            readiness_status = "ready_for_operator_reference_review"
        
        # Build slot status list
        slot_status = []
        for mapping in slot_mapping_report["slot_mappings"]:
            if mapping["fill_status"] == "empty":
                status = "missing"
                blocker = mapping["required"]
            else:
                status = "satisfied"
                blocker = False
            
            slot_status.append({
                "slot_id": mapping["slot_id"],
                "slot_role": mapping["slot_role"],
                "status": status,
                "required": mapping["required"],
                "blocker": blocker
            })
        
        return {
            "readiness_version": "1.0.0",
            "blueprint_stage_id": self.blueprint_stage_id,
            "readiness_timestamp": datetime.now().isoformat(),
            "readiness_status": readiness_status,
            "stage_readiness": [
                {
                    "stage_id": self.blueprint_stage_id,
                    "readiness_status": readiness_status,
                    "slot_status": slot_status
                }
            ],
            "generation_gate_status": {
                "gate_open": False,  # Never open for intake-only validation
                "blocking_slots": unfilled_required,
                "blocking_stages": [self.blueprint_stage_id] if unfilled_required else []
            },
            "metadata": {
                "visual_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "generation_authorized": False
            }
        }
    
    def _create_evidence_event(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence trace event."""
        event_id = str(uuid.uuid4())
        
        # Determine decision status based on validation
        if validation_report["overall_status"] == "no_files":
            decision_status = "pending"
        elif validation_report["overall_status"] == "all_valid":
            decision_status = "ready"
        else:
            decision_status = "blocked"
        
        # Determine blocked actions
        blocked_actions = []
        if decision_status == "blocked":
            blocked_actions = ["generation", "assembly", "downstream"]
        elif decision_status == "pending":
            blocked_actions = ["generation", "assembly", "downstream"]
        
        # Determine allowed next action
        if decision_status == "pending":
            allowed_next_action = "operator_reference_review_required"
        elif decision_status == "ready":
            allowed_next_action = "operator_reference_review_required"
        else:
            allowed_next_action = "fix_references_required"
        
        return {
            "event_id": event_id,
            "task_id": "RC-COMBINE-V2-REFERENCE-SET-INTAKE-VALIDATION-001",
            "source_layer": "reference_set",
            "artifact_path": str(self.output_path),
            "artifact_sha256": "",  # Would compute for actual artifact
            "decision_status": decision_status,
            "blocked_actions": blocked_actions,
            "allowed_next_action": allowed_next_action,
            "timestamp": datetime.now().isoformat(),
            "created_by": "reference_set_intake_validator",
            "metadata": {
                "validation_status": validation_report["overall_status"],
                "total_files": validation_report["validation_summary"]["total_files"],
                "valid_files": validation_report["validation_summary"]["valid_files"]
            }
        }
    
    def _write_scan_report(self, scan_report: Dict[str, Any]) -> str:
        """Write source scan report."""
        output_path = self.output_path / "reference_source_scan_report.json"
        with open(output_path, 'w') as f:
            json.dump(scan_report, f, indent=2)
        return str(output_path)
    
    def _write_validation_report(self, validation_report: Dict[str, Any]) -> str:
        """Write validation report."""
        output_path = self.output_path / "reference_file_validation_report.json"
        with open(output_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        return str(output_path)
    
    def _write_slot_mapping_report(self, slot_mapping_report: Dict[str, Any]) -> str:
        """Write slot mapping report."""
        output_path = self.output_path / "reference_slot_mapping_report.json"
        with open(output_path, 'w') as f:
            json.dump(slot_mapping_report, f, indent=2)
        return str(output_path)
    
    def _write_readiness_report(self, readiness_report: Dict[str, Any]) -> str:
        """Write readiness report."""
        output_path = self.output_path / "reference_readiness_report.json"
        with open(output_path, 'w') as f:
            json.dump(readiness_report, f, indent=2)
        return str(output_path)
    
    def _write_evidence_event(self, evidence_event: Dict[str, Any]) -> str:
        """Write evidence trace event."""
        output_path = self.output_path / "reference_intake_evidence_event.json"
        with open(output_path, 'w') as f:
            json.dump(evidence_event, f, indent=2)
        return str(output_path)
