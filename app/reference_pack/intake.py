"""Intake layer for reference pack initialization and loading.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.reference_pack.canonicalizer import ReferenceCanonicalizer
from app.reference_pack.models import (
    ReferenceAsset,
    ReferencePack,
    ReferenceSlot,
    ReferenceUsagePolicy,
    SlotCategory,
    SlotStatus,
)
from app.reference_pack.validator import ReferencePackValidator


class ReferencePackIntake:
    """Intake layer for project-agnostic reference pack management."""

    @staticmethod
    def create_default_pack(pack_id: str = "default_reference_pack") -> ReferencePack:
        """Create a default project-agnostic reference pack.

        Args:
            pack_id: Reference pack identifier

        Returns:
            Initialized reference pack
        """
        timestamp = datetime.now().isoformat()

        # Create slots from taxonomy
        slots: dict[str, ReferenceSlot] = {}
        for slot_id, taxonomy in ReferenceCanonicalizer.SLOT_TAXONOMY.items():
            slot = ReferenceSlot(
                slot_id=slot_id,
                category=SlotCategory(taxonomy["category"]),
                description=f"{slot_id} reference slot",
                required=False,
                image_required=False,  # Project-agnostic: images optional
                canonical_naming=taxonomy["canonical_naming"],
                accepted_formats=["png", "jpg", "jpeg"],
                max_variants=taxonomy["max_variants"],
                usage_roles=[],
                assets=[],
                status=SlotStatus.PENDING_OPERATOR_SUPPLY,
            )
            slots[slot_id] = slot

        return ReferencePack(
            reference_pack_id=pack_id,
            project_binding=None,
            slots=slots,
            metadata={
                "created": timestamp,
                "supports_future_references": True,
                "missing_file_status": "pending_operator_supply",
                "total_slots": len(slots),
                "populated_slots": 0,
                "pending_slots": len(slots),
            },
        )

    @staticmethod
    def create_default_usage_policy() -> ReferenceUsagePolicy:
        """Create default usage policy for reference assets.

        Returns:
            Reference usage policy
        """
        timestamp = datetime.now().isoformat()

        # Build slot usage rules
        slot_usage_rules: dict[str, Any] = {}
        for slot_id in ReferenceCanonicalizer.SLOT_TAXONOMY:
            slot_usage_rules[slot_id] = {
                "required_for_generation": False,  # Project-agnostic: no requirements
                "fallback_allowed": True,
                "max_concurrent_usage": 1,
                "weight": 0.5,
            }

        return ReferenceUsagePolicy(
            usage_policy={
                "slot_usage_rules": slot_usage_rules,
                "asset_validation": {
                    "require_file_existence": False,  # Project-agnostic: no file check
                    "require_sha256": False,
                    "require_dimensions": False,
                    "min_resolution": {"width": 512, "height": 512},
                    "max_file_size_mb": 50,
                },
                "generation_integration": {
                    "ip_adapter_enabled": True,
                    "controlnet_enabled": True,
                    "reference_strength_range": {"min": 0.3, "max": 0.8},
                },
            },
            constraints={
                "forbidden_actions": [
                    "generation_without_references",
                    "visual_acceptance_automation",
                    "automatic_downstream_routing",
                    "hardcoded_project_binding",
                    "fake_file_existence_check",
                ],
                "required_validations": [
                    "project_agnostic_check",
                    "no_visual_acceptance",
                    "no_hardcoded_paths",
                ],
            },
            metadata={
                "created": timestamp,
                "project_agnostic": True,
            },
        )

    @staticmethod
    def load_pack_from_file(pack_path: Path) -> ReferencePack:
        """Load reference pack from JSON file.

        Args:
            pack_path: Path to reference pack JSON file

        Returns:
            Loaded reference pack
        """
        with open(pack_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert dict to ReferencePack
        slots: dict[str, ReferenceSlot] = {}
        for slot_id, slot_data in data.get("slots", {}).items():
            assets: list[ReferenceAsset] = []
            for asset_data in slot_data.get("assets", []):
                asset = ReferenceAsset(
                    asset_id=asset_data.get("asset_id", ""),
                    file_path=asset_data.get("file_path"),
                    canonical_name=asset_data.get("canonical_name"),
                    file_exists=asset_data.get("file_exists", False),
                    sha256=asset_data.get("sha256"),
                    width=asset_data.get("width"),
                    height=asset_data.get("height"),
                    format=asset_data.get("format"),
                    metadata=asset_data.get("metadata", {}),
                    status=asset_data.get("status", "pending_operator_supply"),
                )
                assets.append(asset)

            slot = ReferenceSlot(
                slot_id=slot_id,
                category=SlotCategory(slot_data.get("category", "technical_reference")),
                description=slot_data.get("description", ""),
                required=slot_data.get("required", False),
                image_required=slot_data.get("image_required", False),
                canonical_naming=slot_data.get("canonical_naming", ""),
                accepted_formats=slot_data.get("accepted_formats", []),
                max_variants=slot_data.get("max_variants", 1),
                usage_roles=slot_data.get("usage_roles", []),
                assets=assets,
                status=SlotStatus(slot_data.get("status", "pending_operator_supply")),
            )
            slots[slot_id] = slot

        return ReferencePack(
            document_type=data.get("document_type", "reference_pack_manifest"),
            version=data.get("version", "1.0.0"),
            task_id=data.get("task_id", "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001"),
            project_agnostic=data.get("project_agnostic", True),
            reference_pack_id=data.get("reference_pack_id", ""),
            project_binding=data.get("project_binding"),
            slots=slots,
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def save_pack_to_file(pack: ReferencePack, pack_path: Path) -> None:
        """Save reference pack to JSON file.

        Args:
            pack: Reference pack to save
            pack_path: Path to save to
        """
        pack_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        slots_dict: dict[str, Any] = {}
        for slot_id, slot in pack.slots.items():
            assets_list = []
            for asset in slot.assets:
                assets_list.append({
                    "asset_id": asset.asset_id,
                    "file_path": asset.file_path,
                    "canonical_name": asset.canonical_name,
                    "file_exists": asset.file_exists,
                    "sha256": asset.sha256,
                    "width": asset.width,
                    "height": asset.height,
                    "format": asset.format,
                    "metadata": asset.metadata,
                    "status": asset.status.value if isinstance(asset.status, SlotStatus) else asset.status,
                })

            slots_dict[slot_id] = {
                "slot_id": slot.slot_id,
                "category": slot.category.value if isinstance(slot.category, SlotCategory) else slot.category,
                "description": slot.description,
                "required": slot.required,
                "image_required": slot.image_required,
                "canonical_naming": slot.canonical_naming,
                "accepted_formats": slot.accepted_formats,
                "max_variants": slot.max_variants,
                "usage_roles": slot.usage_roles,
                "assets": assets_list,
                "status": slot.status.value if isinstance(slot.status, SlotStatus) else slot.status,
            }

        data = {
            "document_type": pack.document_type,
            "version": pack.version,
            "task_id": pack.task_id,
            "project_agnostic": pack.project_agnostic,
            "reference_pack_id": pack.reference_pack_id,
            "project_binding": pack.project_binding,
            "slots": slots_dict,
            "metadata": pack.metadata,
        }

        with open(pack_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def validate_pack(pack: ReferencePack) -> tuple[bool, list[str]]:
        """Validate a reference pack.

        Args:
            pack: Reference pack to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = ReferencePackValidator.validate_reference_pack(pack)
        return (len(errors) == 0, errors)
