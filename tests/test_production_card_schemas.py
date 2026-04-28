"""
Tests for production card schemas and templates.

This test suite validates:
- All 15 schemas exist
- All template card folders exist
- Neutral example cards parse as JSON
- Every example card has required fields
- Every example card uses valid status
- Every example card uses valid owner_role
- No Alya/Mir Erdan hardcode in schemas or templates
- Schema loader functionality
"""

import json
import os
from pathlib import Path

import pytest

from app.production_cards.schema_loader import (
    SchemaLoader,
    get_schema_loader,
    list_supported_card_types,
    list_valid_statuses,
    list_valid_owner_roles,
    load_schema,
)


class TestSchemaExistence:
    """Test that all required schema files exist."""

    def test_all_15_schemas_exist(self):
        """Test that all 15 schema files exist in the schemas directory."""
        schemas_dir = Path(__file__).parent.parent / "app" / "production_cards" / "schemas"
        required_schemas = [
            "ProjectCard.schema.json",
            "EpisodeCard.schema.json",
            "ScenarioCard.schema.json",
            "ShotCard.schema.json",
            "CharacterCard.schema.json",
            "EnvironmentCard.schema.json",
            "LightingCard.schema.json",
            "CameraCard.schema.json",
            "StyleCard.schema.json",
            "WardrobeCard.schema.json",
            "PropCard.schema.json",
            "VoiceCard.schema.json",
            "WorkflowRecipeCard.schema.json",
            "QARequirementCard.schema.json",
            "ReleasePackageCard.schema.json",
        ]
        for schema_file in required_schemas:
            schema_path = schemas_dir / schema_file
            assert schema_path.exists(), f"Schema file {schema_file} does not exist"
            assert schema_path.is_file(), f"Schema file {schema_file} is not a file"

    def test_schemas_parse_as_json(self):
        """Test that all schema files can be parsed as valid JSON."""
        schemas_dir = Path(__file__).parent.parent / "app" / "production_cards" / "schemas"
        for schema_file in schemas_dir.glob("*.schema.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                assert isinstance(schema, dict), f"Schema {schema_file} is not a dict"
                assert "$schema" in schema, f"Schema {schema_file} missing $schema key"


class TestTemplateFolders:
    """Test that all required template card folders exist."""

    def test_all_template_folders_exist(self):
        """Test that all template card folders exist."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        required_folders = [
            "project",
            "episodes",
            "scenarios",
            "shots",
            "characters",
            "environments",
            "lighting",
            "camera",
            "style",
            "wardrobe",
            "props",
            "voices",
            "workflows",
            "qa",
            "release",
        ]
        for folder in required_folders:
            folder_path = templates_dir / folder
            assert folder_path.exists(), f"Template folder {folder} does not exist"
            assert folder_path.is_dir(), f"Template folder {folder} is not a directory"


class TestTemplateCards:
    """Test that neutral example cards are valid."""

    def test_example_cards_parse_as_json(self):
        """Test that all example cards can be parsed as valid JSON."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
                assert isinstance(card, dict), f"Card {card_file} is not a dict"

    def test_example_cards_have_required_fields(self):
        """Test that every example card has card_id, card_type, project_id, owner_role, and status."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        required_fields = ["card_id", "card_type", "project_id", "owner_role", "status"]
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
                for field in required_fields:
                    assert field in card, f"Card {card_file} missing required field: {field}"

    def test_example_cards_use_valid_status(self):
        """Test that every example card uses a valid status."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        valid_statuses = list_valid_statuses()
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
                status = card.get("status")
                assert status in valid_statuses, f"Card {card_file} has invalid status: {status}"

    def test_example_cards_use_valid_owner_role(self):
        """Test that every example card uses a valid owner_role."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        valid_roles = list_valid_owner_roles()
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                card = json.load(f)
                owner_role = card.get("owner_role")
                assert owner_role in valid_roles, f"Card {card_file} has invalid owner_role: {owner_role}"


class TestNoProjectSpecificHardcode:
    """Test that no project-specific hardcode (Alya/Mir Erdan) is added."""

    def test_schemas_no_alya_hardcode(self):
        """Test that schemas do not contain 'Alya' hardcode."""
        schemas_dir = Path(__file__).parent.parent / "app" / "production_cards" / "schemas"
        for schema_file in schemas_dir.glob("*.schema.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                assert "alya" not in content, f"Schema {schema_file} contains 'Alya' hardcode"

    def test_schemas_no_mir_erdan_hardcode(self):
        """Test that schemas do not contain 'Mir Erdan' hardcode."""
        schemas_dir = Path(__file__).parent.parent / "app" / "production_cards" / "schemas"
        for schema_file in schemas_dir.glob("*.schema.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                assert "mir erdan" not in content, f"Schema {schema_file} contains 'Mir Erdan' hardcode"

    def test_template_cards_no_alya_hardcode(self):
        """Test that template cards do not contain 'Alya' hardcode."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                assert "alya" not in content, f"Card {card_file} contains 'Alya' hardcode"

    def test_template_cards_no_mir_erdan_hardcode(self):
        """Test that template cards do not contain 'Mir Erdan' hardcode."""
        templates_dir = Path(__file__).parent.parent / "data" / "project_templates" / "film_project" / "cards"
        for card_file in templates_dir.rglob("*.json"):
            with open(card_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                assert "mir erdan" not in content, f"Card {card_file} contains 'Mir Erdan' hardcode"


class TestSchemaLoader:
    """Test schema loader functionality."""

    def test_schema_loader_lists_all_supported_card_types(self):
        """Test that schema loader lists all supported card types."""
        loader = SchemaLoader()
        card_types = loader.list_supported_card_types()
        expected_count = 15
        assert len(card_types) == expected_count, f"Expected {expected_count} card types, got {len(card_types)}"
        expected_types = [
            "ProjectCard",
            "EpisodeCard",
            "ScenarioCard",
            "ShotCard",
            "CharacterCard",
            "EnvironmentCard",
            "LightingCard",
            "CameraCard",
            "StyleCard",
            "WardrobeCard",
            "PropCard",
            "VoiceCard",
            "WorkflowRecipeCard",
            "QARequirementCard",
            "ReleasePackageCard",
        ]
        for expected_type in expected_types:
            assert expected_type in card_types, f"Expected card type {expected_type} not found"

    def test_schema_loader_lists_valid_statuses(self):
        """Test that schema loader lists all valid statuses."""
        loader = SchemaLoader()
        statuses = loader.list_valid_statuses()
        expected_count = 7
        assert len(statuses) == expected_count, f"Expected {expected_count} statuses, got {len(statuses)}"
        expected_statuses = [
            "draft",
            "needs_references",
            "needs_role_work",
            "ready_for_review",
            "approved",
            "blocked",
            "deprecated",
        ]
        for expected_status in expected_statuses:
            assert expected_status in statuses, f"Expected status {expected_status} not found"

    def test_schema_loader_lists_valid_owner_roles(self):
        """Test that schema loader lists all valid owner roles."""
        loader = SchemaLoader()
        roles = loader.list_valid_owner_roles()
        expected_count = 12
        assert len(roles) == expected_count, f"Expected {expected_count} roles, got {len(roles)}"
        expected_roles = [
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
            "Editor / Final QA Supervisor",
        ]
        for expected_role in expected_roles:
            assert expected_role in roles, f"Expected role {expected_role} not found"

    def test_schema_loader_loads_known_card_type(self):
        """Test that schema loader can load a known card type."""
        loader = SchemaLoader()
        schema = loader.load_schema("ProjectCard")
        assert isinstance(schema, dict), "Schema should be a dict"
        assert "$schema" in schema, "Schema should have $schema key"
        assert schema["title"] == "ProjectCard", "Schema title should match card type"

    def test_schema_loader_rejects_unknown_card_type(self):
        """Test that schema loader rejects unknown card types."""
        loader = SchemaLoader()
        with pytest.raises(ValueError, match="Unknown card type"):
            loader.load_schema("UnknownCard")

    def test_schema_loader_validates_card_type(self):
        """Test that schema loader validates card types."""
        loader = SchemaLoader()
        assert loader.validate_card_type("ProjectCard") is True
        assert loader.validate_card_type("UnknownCard") is False

    def test_schema_loader_validates_status(self):
        """Test that schema loader validates statuses."""
        loader = SchemaLoader()
        assert loader.validate_status("draft") is True
        assert loader.validate_status("approved") is True
        assert loader.validate_status("invalid_status") is False

    def test_schema_loader_validates_owner_role(self):
        """Test that schema loader validates owner roles."""
        loader = SchemaLoader()
        assert loader.validate_owner_role("Director / Orchestrator") is True
        assert loader.validate_owner_role("invalid_role") is False

    def test_module_functions(self):
        """Test that module-level convenience functions work."""
        card_types = list_supported_card_types()
        assert len(card_types) == 15

        statuses = list_valid_statuses()
        assert len(statuses) == 7

        roles = list_valid_owner_roles()
        assert len(roles) == 12

        schema = load_schema("ProjectCard")
        assert isinstance(schema, dict)
