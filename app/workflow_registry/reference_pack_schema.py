"""Reference pack schema and validation.

Provides schema definition and validation for reference packs,
ensuring they can describe image slots without requiring actual images.
"""

from __future__ import annotations

from typing import Any

from app.workflow_registry.models import ReferenceItem, ReferencePack, ReferenceType


class ReferencePackSchema:
    """Schema and validation for reference packs."""

    @staticmethod
    def create_empty_reference_pack(
        pack_id: str,
        reference_types: list[ReferenceType] | None = None,
    ) -> ReferencePack:
        """Create an empty reference pack with specified types."""
        if reference_types is None:
            reference_types = [
                ReferenceType.STYLE,
                ReferenceType.CHARACTER,
                ReferenceType.LOCATION,
                ReferenceType.CAMERA,
                ReferenceType.LIGHTING,
                ReferenceType.QUALITY,
                ReferenceType.NEGATIVE,
            ]

        return ReferencePack(
            reference_pack_id=pack_id,
            project_binding_required=False,
            reference_types=reference_types,
            items=[],
            usage_policy={
                "allow_slot_description": True,
                "allow_optional_paths": True,
                "require_actual_images": False,
                "allow_metadata_only": True,
            },
            operator_review_required=True,
        )

    @staticmethod
    def add_reference_item(
        pack: ReferencePack,
        reference_id: str,
        reference_type: ReferenceType,
        description: str,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
        required: bool = True,
    ) -> ReferencePack:
        """Add a reference item to the pack."""
        if metadata is None:
            metadata = {}

        item = ReferenceItem(
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            path=path,
            metadata=metadata,
            required=required,
        )

        pack.items.append(item)
        return pack

    @staticmethod
    def create_style_reference_slot(
        pack: ReferencePack,
        slot_id: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> ReferencePack:
        """Create a style reference slot (without actual image)."""
        return ReferencePackSchema.add_reference_item(
            pack,
            reference_id=slot_id,
            reference_type=ReferenceType.STYLE,
            description=description,
            path=None,  # No actual image required
            metadata=metadata or {},
            required=True,
        )

    @staticmethod
    def create_character_reference_slot(
        pack: ReferencePack,
        slot_id: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> ReferencePack:
        """Create a character reference slot (without actual image)."""
        return ReferencePackSchema.add_reference_item(
            pack,
            reference_id=slot_id,
            reference_type=ReferenceType.CHARACTER,
            description=description,
            path=None,  # No actual image required
            metadata=metadata or {},
            required=True,
        )

    @staticmethod
    def validate_slot_description_only(
        item: ReferenceItem,
    ) -> bool:
        """Validate that a reference item can exist with description only."""
        # In project-agnostic context, reference items should be able to
        # exist with just a description and metadata, without actual paths
        if item.path is None:
            # This is OK if the item has a description
            return bool(item.description)
        return True

    @staticmethod
    def validate_pack_slot_compatibility(
        pack: ReferencePack,
    ) -> list[str]:
        """Validate that the reference pack supports slot descriptions without images."""
        errors: list[str] = []

        # Check that usage policy allows slot descriptions
        usage_policy = pack.usage_policy
        if not usage_policy.get("allow_slot_description", True):
            errors.append("Usage policy must allow slot descriptions")

        if usage_policy.get("require_actual_images", False):
            errors.append(
                "Usage policy must not require actual images in project-agnostic context"
            )

        # Check that items can exist without paths
        for item in pack.items:
            if not ReferencePackSchema.validate_slot_description_only(item):
                errors.append(
                    f"Reference item {item.reference_id} cannot exist with description only"
                )

        return errors

    @staticmethod
    def get_missing_reference_types(
        pack: ReferencePack,
    ) -> list[ReferenceType]:
        """Get reference types that are declared but have no items."""
        declared_types = set(pack.reference_types)
        used_types = {item.reference_type for item in pack.items}
        return list(declared_types - used_types)

    @staticmethod
    def get_reference_summary(
        pack: ReferencePack,
    ) -> dict[str, Any]:
        """Get a summary of the reference pack contents."""
        summary: dict[str, Any] = {
            "reference_pack_id": pack.reference_pack_id,
            "total_items": len(pack.items),
            "required_items": sum(1 for item in pack.items if item.required),
            "optional_items": sum(1 for item in pack.items if not item.required),
            "items_with_paths": sum(1 for item in pack.items if item.path),
            "items_without_paths": sum(1 for item in pack.items if not item.path),
            "by_type": {},
        }

        for ref_type in pack.reference_types:
            type_items = [item for item in pack.items if item.reference_type == ref_type]
            summary["by_type"][ref_type.value] = {
                "count": len(type_items),
                "with_paths": sum(1 for item in type_items if item.path),
                "without_paths": sum(1 for item in type_items if not item.path),
            }

        return summary
