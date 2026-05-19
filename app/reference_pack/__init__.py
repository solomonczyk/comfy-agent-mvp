"""Project-agnostic reference pack intake and canonicalization layer.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001

This module provides infrastructure for managing reference packs without
binding to specific projects or requiring real image files.
"""
from __future__ import annotations

from app.reference_pack.models import (
    ReferenceAsset,
    ReferencePack,
    ReferenceSlot,
    ReferenceUsagePolicy,
    ReferenceCanonicalizationReport,
)
from app.reference_pack.validator import ReferencePackValidator
from app.reference_pack.canonicalizer import ReferenceCanonicalizer
from app.reference_pack.intake import ReferencePackIntake

__all__ = [
    "ReferenceAsset",
    "ReferencePack",
    "ReferenceSlot",
    "ReferenceUsagePolicy",
    "ReferenceCanonicalizationReport",
    "ReferencePackValidator",
    "ReferenceCanonicalizer",
    "ReferencePackIntake",
]
