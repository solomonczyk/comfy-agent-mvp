"""
Reference Set Dropzone / Intake Bridge

Project-agnostic layer for managing reference images placed by operators.
Provides validation, slot mapping, and intake manifest generation.
"""

from .models import (
    ReferenceSlot,
    ValidationPolicy,
    ReferenceFileEntry,
    SlotMapping,
    FileValidationResult,
    ValidationCheck
)
from .dropzone_contract import DropzoneContract
from .intake_manifest_builder import IntakeManifestBuilder
from .slot_mapper import SlotMapper
from .file_validator import FileValidator

__all__ = [
    "ReferenceSlot",
    "ValidationPolicy",
    "ReferenceFileEntry",
    "SlotMapping",
    "FileValidationResult",
    "ValidationCheck",
    "DropzoneContract",
    "IntakeManifestBuilder",
    "SlotMapper",
    "FileValidator",
]
