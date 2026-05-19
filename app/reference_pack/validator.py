"""Validator for reference pack structures.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.reference_pack.models import (
    ReferencePack,
    ReferenceSlot,
    SlotCategory,
    SlotStatus,
)


class ReferencePackValidator:
    """Validates reference pack structures and constraints."""

    # Forbidden patterns that indicate project hardcoding
    FORBIDDEN_PATH_PATTERNS = [
        "rc2_multishot1_ep01",
        "rc2_multishot1",
        "ep01",
        "episode_01",
        "episode01",
    ]

    @staticmethod
    def validate_reference_pack(pack: ReferencePack) -> list[str]:
        """Validate a reference pack structure.

        Args:
            pack: Reference pack to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Validate project-agnostic constraint
        if not pack.project_agnostic:
            errors.append("project_agnostic must be true")

        # Validate no project binding
        if pack.project_binding is not None:
            errors.append("project_binding must be null for project-agnostic packs")

        # Validate task ID
        if pack.task_id != "RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001":
            errors.append(f"Invalid task_id: {pack.task_id}")

        # Validate metadata
        if not pack.metadata.get("supports_future_references"):
            errors.append("metadata.supports_future_references must be true")

        if pack.metadata.get("missing_file_status") != "pending_operator_supply":
            errors.append("metadata.missing_file_status must be pending_operator_supply")

        # Validate slots
        for slot_id, slot in pack.slots.items():
            slot_errors = ReferencePackValidator._validate_slot(slot, slot_id)
            errors.extend(slot_errors)

        return errors

    @staticmethod
    def _validate_slot(slot: ReferenceSlot, slot_id: str) -> list[str]:
        """Validate a reference slot.

        Args:
            slot: Reference slot to validate
            slot_id: Slot identifier for error messages

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        # Validate no image requirement for project-agnostic
        if slot.image_required:
            errors.append(f"Slot {slot_id}: image_required must be false for project-agnostic")

        # Validate status is not production_accepted
        if slot.status == SlotStatus.POPULATED:
            # Check that assets don't have fake file existence
            for asset in slot.assets:
                if asset.file_path and not asset.file_exists:
                    # This is OK for future references
                    if asset.status != "pending_operator_supply":
                        errors.append(
                            f"Slot {slot_id}: Asset {asset.asset_id} has missing file but "
                            f"status is {asset.status}"
                        )

                # Check for forbidden path patterns
                if asset.file_path:
                    for pattern in ReferencePackValidator.FORBIDDEN_PATH_PATTERNS:
                        if pattern in asset.file_path.lower():
                            errors.append(
                                f"Slot {slot_id}: Asset {asset.asset_id} contains "
                                f"forbidden pattern '{pattern}' in file path"
                            )

        return errors

    @staticmethod
    def validate_file_path(path: str | None) -> list[str]:
        """Validate a file path for project-agnostic constraints.

        Args:
            path: File path to validate

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        if path is None:
            return errors

        # Check for forbidden patterns
        for pattern in ReferencePackValidator.FORBIDDEN_PATH_PATTERNS:
            if pattern in path.lower():
                errors.append(f"Path contains forbidden pattern '{pattern}'")

        return errors

    @staticmethod
    def validate_schema_compliance(data: dict[str, Any], schema_path: Path) -> tuple[bool, list[str]]:
        """Validate data against a JSON schema.

        Args:
            data: Data to validate
            schema_path: Path to JSON schema file

        Returns:
            Tuple of (is_valid, errors)
        """
        errors: list[str] = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            # Basic structural validation (would use jsonschema in production)
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Validate const fields
            properties = schema.get("properties", {})
            for field, prop_def in properties.items():
                if "const" in prop_def:
                    if data.get(field) != prop_def["const"]:
                        errors.append(
                            f"Field {field} must be {prop_def['const']}, got {data.get(field)}"
                        )

        except Exception as e:
            errors.append(f"Schema validation error: {e}")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_no_visual_acceptance(data: dict[str, Any]) -> list[str]:
        """Ensure visual acceptance fields are not present or false.

        Args:
            data: Data to validate

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        forbidden_fields = [
            "visual_acceptance_executed",
            "visual_qa_acceptance",
            "production_accepted",
            "operator_visual_acceptance",
        ]

        for field in forbidden_fields:
            if field in data and data[field] is True:
                errors.append(f"Forbidden field {field} is True")

        return errors
