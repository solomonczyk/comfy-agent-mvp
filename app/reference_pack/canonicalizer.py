"""Canonicalizer for reference pack assets.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from app.reference_pack.models import (
    ReferenceAsset,
    ReferenceCanonicalizationReport,
    ReferencePack,
    ReferenceSlot,
    SlotStatus,
)


class ReferenceCanonicalizer:
    """Canonicalizes reference pack naming and structure."""

    # Reference slot taxonomy
    SLOT_TAXONOMY: dict[str, dict[str, Any]] = {
        "character_front_full_body": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_front_full_body.{ext}",
            "max_variants": 3,
        },
        "character_3_4_full_body": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_3_4_full_body.{ext}",
            "max_variants": 3,
        },
        "character_medium_front": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_medium_front.{ext}",
            "max_variants": 3,
        },
        "character_headshot_front": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_headshot_front.{ext}",
            "max_variants": 5,
        },
        "character_profile_left": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_profile_left.{ext}",
            "max_variants": 3,
        },
        "character_profile_right": {
            "category": "character_pose",
            "canonical_naming": "{project_id}_{character_id}_profile_right.{ext}",
            "max_variants": 3,
        },
        "expression_variants": {
            "category": "character_expression",
            "canonical_naming": "{project_id}_{character_id}_expression_{variant}.{ext}",
            "max_variants": 10,
        },
        "hands_detail": {
            "category": "character_detail",
            "canonical_naming": "{project_id}_{character_id}_hands_{variant}.{ext}",
            "max_variants": 8,
        },
        "costume_detail": {
            "category": "character_detail",
            "canonical_naming": "{project_id}_{character_id}_costume_{detail}.{ext}",
            "max_variants": 10,
        },
        "lighting_reference": {
            "category": "technical_reference",
            "canonical_naming": "{project_id}_lighting_{mood}.{ext}",
            "max_variants": 5,
        },
        "quality_reference": {
            "category": "technical_reference",
            "canonical_naming": "{project_id}_quality_{style}.{ext}",
            "max_variants": 5,
        },
        "negative_reference": {
            "category": "technical_reference",
            "canonical_naming": "{project_id}_negative_{category}.{ext}",
            "max_variants": 10,
        },
    }

    @staticmethod
    def compute_sha256(file_path: Path) -> str | None:
        """Compute SHA256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash or None if file doesn't exist
        """
        if not file_path.exists():
            return None

        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def generate_canonical_name(
        slot_id: str,
        variant: int = 0,
        project_id: str = "project",
        character_id: str = "char",
        ext: str = "png",
    ) -> str:
        """Generate canonical name for a reference asset.

        Args:
            slot_id: Slot identifier
            variant: Variant number
            project_id: Project identifier
            character_id: Character identifier
            ext: File extension

        Returns:
            Canonical filename
        """
        taxonomy = ReferenceCanonicalizer.SLOT_TAXONOMY.get(slot_id, {})
        template = taxonomy.get("canonical_naming", "{project_id}_{slot_id}_{variant}.{ext}")

        return template.format(
            project_id=project_id,
            character_id=character_id,
            slot_id=slot_id,
            variant=variant,
            ext=ext,
        )

    @staticmethod
    def canonicalize_pack(pack: ReferencePack) -> ReferenceCanonicalizationReport:
        """Generate canonicalization report for a reference pack.

        Args:
            pack: Reference pack to canonicalize

        Returns:
            Canonicalization report
        """
        timestamp = datetime.now().isoformat()
        slot_report: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []

        total_slots = len(pack.slots)
        populated_slots = 0
        pending_slots = 0

        for slot_id, slot in pack.slots.items():
            slot_data = {
                "slot_id": slot_id,
                "canonical_name_compliant": True,
                "format_compliant": True,
                "assets_canonicalized": 0,
                "assets_pending": 0,
                "status": slot.status.value,
            }

            # Check asset canonicalization
            for asset in slot.assets:
                if asset.file_path and asset.file_exists:
                    slot_data["assets_canonicalized"] += 1
                    populated_slots += 1
                else:
                    slot_data["assets_pending"] += 1
                    pending_slots += 1

                # Validate canonical name
                if asset.canonical_name:
                    expected = ReferenceCanonicalizer.generate_canonical_name(
                        slot_id, 0, "project", "char", asset.format or "png"
                    )
                    if not asset.canonical_name.startswith(expected.split("{")[0]):
                        slot_data["canonical_name_compliant"] = False
                        warnings.append(
                            f"Asset {asset.asset_id} may not follow canonical naming"
                        )

            slot_report[slot_id] = slot_data

        # Determine overall status
        if pending_slots == 0:
            canonicalization_status = "complete"
        elif populated_slots > 0:
            canonicalization_status = "partial"
        else:
            canonicalization_status = "pending"

        # Readiness assessment
        readiness_assessment = {
            "ready_for_generation": False,  # Never true without real assets
            "missing_critical_slots": [],
            "pending_operator_supply_count": pending_slots,
        }

        # Update pack metadata
        pack.metadata.update({
            "total_slots": total_slots,
            "populated_slots": populated_slots,
            "pending_slots": pending_slots,
        })

        return ReferenceCanonicalizationReport(
            reference_pack_id=pack.reference_pack_id,
            canonicalization_status=canonicalization_status,
            slot_report=slot_report,
            validation_results={"errors": errors, "warnings": warnings},
            readiness_assessment=readiness_assessment,
            metadata={
                "created": timestamp,
                "project_agnostic": True,
            },
        )
