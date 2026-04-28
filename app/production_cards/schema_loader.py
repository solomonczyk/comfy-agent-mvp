"""
Schema Loader for Production Cards

This module provides functionality to load and validate production card schemas.
It supports listing supported card types, valid statuses, and valid owner roles.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class SchemaLoader:
    """Loads and manages production card schemas."""

    def __init__(self, schemas_dir: Optional[str] = None):
        """
        Initialize the schema loader.

        Args:
            schemas_dir: Path to the schemas directory. If None, uses default.
        """
        if schemas_dir is None:
            # Default to app/production_cards/schemas relative to this file
            self.schemas_dir = Path(__file__).parent / "schemas"
        else:
            self.schemas_dir = Path(schemas_dir)

        self._schemas_cache: Optional[Dict[str, dict]] = None

    def load_schema(self, card_type: str) -> dict:
        """
        Load a schema for a specific card type.

        Args:
            card_type: The card type (e.g., "ProjectCard", "EpisodeCard")

        Returns:
            The schema as a dictionary

        Raises:
            FileNotFoundError: If schema file doesn't exist
            ValueError: If card_type is unknown
        """
        schema_file = self.schemas_dir / f"{card_type}.schema.json"
        if not schema_file.exists():
            raise ValueError(f"Unknown card type: {card_type}")

        with open(schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_supported_card_types(self) -> List[str]:
        """
        List all supported card types.

        Returns:
            List of card type names (without .schema.json suffix)
        """
        if not self.schemas_dir.exists():
            return []

        schema_files = self.schemas_dir.glob("*.schema.json")
        return [f.stem.replace(".schema", "") for f in schema_files if f.is_file()]

    def list_valid_statuses(self) -> List[str]:
        """
        List all valid card statuses.

        Returns:
            List of valid status values
        """
        return [
            "draft",
            "needs_references",
            "needs_role_work",
            "ready_for_review",
            "approved",
            "blocked",
            "deprecated"
        ]

    def list_valid_owner_roles(self) -> List[str]:
        """
        List all valid owner roles.

        Returns:
            List of valid role names
        """
        return [
            "Executive Producer / Product Owner",
            "Director / Orchestrator",
            "Screenwriter / Script Agent",
            "Shot Designer / Storyboard Agent",
            "Character Director",
            "Environment / Art Director",
            "Cinematographer / Camera + Lighting Director",
            "Workflow TD / ComfyUI Technical Director",
            "Image Generation Agent",
            "Video / Motion Agent",
            "Audio / Voice Agent",
            "Editor / Final QA Supervisor"
        ]

    def validate_card_type(self, card_type: str) -> bool:
        """
        Validate that a card type is supported.

        Args:
            card_type: The card type to validate

        Returns:
            True if card type is supported, False otherwise
        """
        supported_types = self.list_supported_card_types()
        return card_type in supported_types

    def validate_status(self, status: str) -> bool:
        """
        Validate that a status is valid.

        Args:
            status: The status to validate

        Returns:
            True if status is valid, False otherwise
        """
        valid_statuses = self.list_valid_statuses()
        return status in valid_statuses

    def validate_owner_role(self, role: str) -> bool:
        """
        Validate that an owner role is valid.

        Args:
            role: The role to validate

        Returns:
            True if role is valid, False otherwise
        """
        valid_roles = self.list_valid_owner_roles()
        return role in valid_roles

    def get_all_schemas(self) -> Dict[str, dict]:
        """
        Load all schemas at once.

        Returns:
            Dictionary mapping card types to their schemas
        """
        if self._schemas_cache is not None:
            return self._schemas_cache

        schemas = {}
        for card_type in self.list_supported_card_types():
            schemas[card_type] = self.load_schema(card_type)

        self._schemas_cache = schemas
        return schemas


# Singleton instance for convenience
_default_loader: Optional[SchemaLoader] = None


def get_schema_loader(schemas_dir: Optional[str] = None) -> SchemaLoader:
    """
    Get the default schema loader instance.

    Args:
        schemas_dir: Optional path to schemas directory

    Returns:
        SchemaLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = SchemaLoader(schemas_dir)
    return _default_loader


def load_schema(card_type: str) -> dict:
    """
    Load a schema for a specific card type using the default loader.

    Args:
        card_type: The card type (e.g., "ProjectCard", "EpisodeCard")

    Returns:
        The schema as a dictionary
    """
    loader = get_schema_loader()
    return loader.load_schema(card_type)


def list_supported_card_types() -> List[str]:
    """
    List all supported card types using the default loader.

    Returns:
        List of card type names
    """
    loader = get_schema_loader()
    return loader.list_supported_card_types()


def list_valid_statuses() -> List[str]:
    """
    List all valid card statuses.

    Returns:
        List of valid status values
    """
    loader = get_schema_loader()
    return loader.list_valid_statuses()


def list_valid_owner_roles() -> List[str]:
    """
    List all valid owner roles.

    Returns:
        List of valid role names
    """
    loader = get_schema_loader()
    return loader.list_valid_owner_roles()
