"""
Data models for reference set dropzone and intake bridge.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class SlotRole(str, Enum):
    """Reference slot roles."""
    IDENTITY_REFERENCE = "identity_reference"
    STYLE_REFERENCE = "style_reference"
    CAMERA_REFERENCE = "camera_reference"
    LIGHTING_REFERENCE = "lighting_reference"
    ANATOMY_REFERENCE = "anatomy_reference"
    QUALITY_REFERENCE = "quality_reference"
    NEGATIVE_REFERENCE = "negative_reference"


class ValidationStatus(str, Enum):
    """File validation status."""
    VALID = "valid"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    INVALID_FORMAT = "invalid_format"
    SIZE_EXCEEDED = "size_exceeded"
    DIMENSIONS_INSUFFICIENT = "dimensions_insufficient"
    CHECKSUM_FAILED = "checksum_failed"


class FillStatus(str, Enum):
    """Slot fill status."""
    FILLED = "filled"
    PARTIAL = "partial"
    EMPTY = "empty"


class MappingConfidence(str, Enum):
    """Mapping confidence level."""
    EXACT_MATCH = "exact_match"
    ROLE_INFERENCE = "role_inference"
    MANUAL = "manual"
    NONE = "none"


class ReadinessStatus(str, Enum):
    """Overall readiness status."""
    READY = "ready"
    PENDING_OPERATOR_SUPPLY = "pending_operator_supply"
    BLOCKED_MISSING_REQUIRED_REFERENCE = "blocked_missing_required_reference"
    BLOCKED_INVALID_REFERENCE = "blocked_invalid_reference"


@dataclass
class ValidationPolicy:
    """Validation policy for reference files."""
    validate_existence: bool = True
    validate_readability: bool = True
    validate_sha256: bool = True
    validate_size: bool = True
    validate_dimensions: bool = True
    fail_on_missing_required: bool = True


@dataclass
class ReferenceSlot:
    """Reference slot definition."""
    slot_id: str
    slot_role: SlotRole
    required: bool
    allowed_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "webp"])
    min_dimensions: Optional[Dict[str, int]] = None
    max_file_size_mb: Optional[float] = None


@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    passed: bool
    message: str
    value: Optional[Any] = None


@dataclass
class FileValidationResult:
    """Validation result for a single file."""
    file_path: str
    checks: Dict[str, ValidationCheck]
    overall_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class ReferenceFileEntry:
    """Reference file entry in intake manifest."""
    file_path: str
    file_name: str
    file_size_bytes: int
    sha256_checksum: str
    validation_status: ValidationStatus
    assigned_slot_id: Optional[str] = None
    image_dimensions: Optional[Dict[str, int]] = None
    file_format: Optional[str] = None
    readable: bool = False
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class SlotMappingSummary:
    """Summary of slot mapping."""
    total_slots: int
    filled_slots: int
    missing_required_slots: List[str]
    readiness_status: ReadinessStatus


@dataclass
class SlotMapping:
    """Mapping of a slot to files."""
    slot_id: str
    slot_role: SlotRole
    required: bool
    assigned_files: List[str]
    fill_status: FillStatus
    mapping_confidence: MappingConfidence = MappingConfidence.NONE


@dataclass
class DropzoneContract:
    """Dropzone contract defining reference set requirements."""
    contract_version: str
    blueprint_stage_id: str
    dropzone_root_path: str
    required_reference_slots: List[ReferenceSlot]
    validation_policy: ValidationPolicy
    intake_manifest_path: str
    created_at: datetime
    operator_instructions: Optional[str] = None


@dataclass
class IntakeManifest:
    """Intake manifest for reference files."""
    manifest_version: str
    blueprint_stage_id: str
    dropzone_root_path: str
    scan_timestamp: datetime
    reference_files: List[ReferenceFileEntry]
    slot_mapping_summary: SlotMappingSummary
