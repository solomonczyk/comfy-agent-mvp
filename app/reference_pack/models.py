"""Data models for reference pack intake and canonicalization.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SlotCategory(str, Enum):
    """Categories of reference slots."""
    CHARACTER_POSE = "character_pose"
    CHARACTER_EXPRESSION = "character_expression"
    CHARACTER_DETAIL = "character_detail"
    TECHNICAL_REFERENCE = "technical_reference"


class SlotStatus(str, Enum):
    """Status of a reference slot."""
    POPULATED = "populated"
    PENDING_OPERATOR_SUPPLY = "pending_operator_supply"
    OPTIONAL = "optional"


class AssetStatus(str, Enum):
    """Status of a reference asset."""
    PRESENT = "present"
    PENDING_OPERATOR_SUPPLY = "pending_operator_supply"


@dataclass
class ReferenceAsset:
    """Individual reference asset within a slot."""
    asset_id: str
    file_path: str | None = None
    canonical_name: str | None = None
    file_exists: bool = False
    sha256: str | None = None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    format: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: AssetStatus = AssetStatus.PENDING_OPERATOR_SUPPLY


@dataclass
class ReferenceSlot:
    """Individual reference slot definition."""
    slot_id: str
    category: SlotCategory
    description: str
    required: bool = False
    image_required: bool = False
    canonical_naming: str = ""
    accepted_formats: list[str] = field(default_factory=list)
    max_variants: int = 1
    usage_roles: list[str] = field(default_factory=list)
    assets: list[ReferenceAsset] = field(default_factory=list)
    status: SlotStatus = SlotStatus.PENDING_OPERATOR_SUPPLY


@dataclass
class ReferencePack:
    """Project-agnostic reference pack manifest."""
    document_type: str = "reference_pack_manifest"
    version: str = "1.0.0"
    task_id: str = "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001"
    project_agnostic: bool = True
    reference_pack_id: str = ""
    project_binding: str | None = None
    slots: dict[str, ReferenceSlot] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceUsagePolicy:
    """Policy governing reference asset usage."""
    document_type: str = "reference_usage_policy"
    version: str = "1.0.0"
    task_id: str = "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001"
    project_agnostic: bool = True
    usage_policy: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceCanonicalizationReport:
    """Report on canonicalization status."""
    document_type: str = "reference_canonicalization_report"
    version: str = "1.0.0"
    task_id: str = "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001"
    project_agnostic: bool = True
    reference_pack_id: str = ""
    canonicalization_status: str = "pending"
    slot_report: dict[str, Any] = field(default_factory=dict)
    validation_results: dict[str, Any] = field(default_factory=dict)
    readiness_assessment: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
