"""
Tests for Project Profile and Character Registry loaders.

MK-PROFILE1 — Tests for new project-profile-driven reference staging system.
"""
import json
from pathlib import Path

import pytest

from app.profile.project_profile import (
    CharacterProfile,
    CleanReferenceConfig,
    ProjectProfile,
    load_project_profile,
    resolve_character_profile,
)

# Legacy tests for old profile system (app.projects.profile)
try:
    from app.projects.profile import ProjectProfile as LegacyProjectProfile, ProjectProfileLoader, GenerationPolicy, SafeResolution
    from app.projects.characters import CharacterRegistry, CharacterRegistryLoader, CharacterEntry, CharacterStatus
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False


class TestCleanReferenceConfig:
    """MK-PROFILE1 — Test CleanReferenceConfig model."""

    def test_from_dict_default_values(self):
        """Test CleanReferenceConfig.from_dict with defaults."""
        data = {
            "strategy": "single_panel_crop",
            "output_name": "clean_480x640.png",
            "target_width": 480,
            "target_height": 640,
        }
        config = CleanReferenceConfig.from_dict(data)

        assert config.strategy == "single_panel_crop"
        assert config.output_name == "clean_480x640.png"
        assert config.target_width == 480
        assert config.target_height == 640
        assert config.crop_box_mode == "relative"
        assert config.crop_box == [0.0, 0.0, 1.0, 1.0]
        assert config.centering == [0.5, 0.5]
        assert config.force_regenerate is True

    def test_from_dict_full_values(self):
        """Test CleanReferenceConfig.from_dict with all values."""
        data = {
            "strategy": "single_panel_crop",
            "output_name": "alya_clean_single_portrait_v2_480x640.png",
            "target_width": 480,
            "target_height": 640,
            "crop_box_mode": "relative",
            "crop_box": [0.0, 0.0, 0.3333, 0.42],
            "centering": [0.5, 0.35],
            "force_regenerate": True,
        }
        config = CleanReferenceConfig.from_dict(data)

        assert config.strategy == "single_panel_crop"
        assert config.output_name == "alya_clean_single_portrait_v2_480x640.png"
        assert config.target_width == 480
        assert config.target_height == 640
        assert config.crop_box_mode == "relative"
        assert config.crop_box == [0.0, 0.0, 0.3333, 0.42]
        assert config.centering == [0.5, 0.35]
        assert config.force_regenerate is True


class TestCharacterProfile:
    """MK-PROFILE1 — Test CharacterProfile model."""

    def test_from_dict_without_clean_reference(self):
        """Test CharacterProfile.from_dict without clean_reference."""
        data = {
            "character_id": "alya",
            "name": "Alya",
            "aliases": ["Аля", "alya"],
            "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
            "reference_role": "character_identity",
        }
        profile = CharacterProfile.from_dict("alya", data)

        assert profile.character_id == "alya"
        assert profile.name == "Alya"
        assert profile.aliases == ["Аля", "alya"]
        assert profile.reference_image_path == "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png"
        assert profile.reference_role == "character_identity"
        assert profile.clean_reference is None

    def test_from_dict_with_clean_reference(self):
        """Test CharacterProfile.from_dict with clean_reference."""
        data = {
            "character_id": "alya",
            "name": "Alya",
            "aliases": ["Аля", "alya"],
            "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
            "reference_role": "character_identity",
            "clean_reference": {
                "strategy": "single_panel_crop",
                "output_name": "alya_clean_single_portrait_v2_480x640.png",
                "target_width": 480,
                "target_height": 640,
                "crop_box_mode": "relative",
                "crop_box": [0.0, 0.0, 0.3333, 0.42],
                "centering": [0.5, 0.35],
                "force_regenerate": True,
            },
        }
        profile = CharacterProfile.from_dict("alya", data)

        assert profile.character_id == "alya"
        assert profile.clean_reference is not None
        assert profile.clean_reference.strategy == "single_panel_crop"
        assert profile.clean_reference.output_name == "alya_clean_single_portrait_v2_480x640.png"

    def test_matches_alias_case_insensitive(self):
        """Test that alias matching is case-insensitive."""
        profile = CharacterProfile(
            character_id="alya",
            name="Alya",
            aliases=["Аля", "alya", "ALYA"],
        )

        assert profile.matches_alias("alya")
        assert profile.matches_alias("Alya")
        assert profile.matches_alias("ALYA")
        assert profile.matches_alias("аля")
        assert profile.matches_alias("АЛЯ")
        assert not profile.matches_alias("kael")
        assert not profile.matches_alias("unknown")


class TestProjectProfile:
    """MK-PROFILE1 — Test ProjectProfile model."""

    def test_from_dict(self):
        """Test ProjectProfile.from_dict."""
        data = {
            "project_id": "mir_erdan",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
                    "reference_role": "character_identity",
                },
            },
        }
        profile = ProjectProfile.from_dict(data)

        assert profile.project_id == "mir_erdan"
        assert "alya" in profile.characters
        assert profile.characters["alya"].name == "Alya"

    def test_resolve_character_by_character_id(self):
        """Test resolving character by character_id."""
        data = {
            "project_id": "mir_erdan",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля"],
                },
            },
        }
        profile = ProjectProfile.from_dict(data)

        char = profile.resolve_character("alya")
        assert char is not None
        assert char.character_id == "alya"

    def test_resolve_character_by_alias(self):
        """Test resolving character by alias."""
        data = {
            "project_id": "mir_erdan",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                },
            },
        }
        profile = ProjectProfile.from_dict(data)

        # Test by alias
        char = profile.resolve_character("Аля")
        assert char is not None
        assert char.character_id == "alya"

        char = profile.resolve_character("alya")
        assert char is not None
        assert char.character_id == "alya"

    def test_resolve_character_returns_none_for_unknown(self):
        """Test that resolve_character returns None for unknown character."""
        data = {
            "project_id": "mir_erdan",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                },
            },
        }
        profile = ProjectProfile.from_dict(data)

        char = profile.resolve_character("unknown")
        assert char is None


class TestLoadProjectProfile:
    """MK-PROFILE1 — Test load_project_profile function."""

    def test_load_profile_from_r6_project(self):
        """Test loading profile from real_reference_locked_alya_r6."""
        project_root = Path(__file__).parent.parent / "data" / "real_reference_locked_alya_r6"
        
        profile = load_project_profile(project_root)
        
        assert profile is not None
        assert profile.project_id == "mir_erdan"
        assert "alya" in profile.characters

    def test_load_profile_returns_none_if_not_found(self, tmp_path):
        """Test that load_profile returns None if no profile exists."""
        profile = load_project_profile(tmp_path)
        assert profile is None


class TestResolveCharacterProfile:
    """MK-PROFILE1 — Test resolve_character_profile function."""

    def test_resolve_character_by_alias_alya(self):
        """Test resolving Alya by alias 'Аля' (Cyrillic)."""
        project_root = Path(__file__).parent.parent / "data" / "real_reference_locked_alya_r6"
        
        profile = resolve_character_profile("Аля", project_root)
        
        assert profile is not None
        assert profile.character_id == "alya"
        assert profile.name == "Alya"

    def test_resolve_character_by_alias_alya_latin(self):
        """Test resolving Alya by alias 'Alya' (Latin)."""
        project_root = Path(__file__).parent.parent / "data" / "real_reference_locked_alya_r6"
        
        profile = resolve_character_profile("Alya", project_root)
        
        assert profile is not None
        assert profile.character_id == "alya"

    def test_resolve_character_returns_none_for_unknown(self, tmp_path):
        """Test that resolve_character_profile returns None for unknown character."""
        profile = resolve_character_profile("unknown", tmp_path)
        assert profile is None

    def test_resolve_dummy_mira_by_alias(self, tmp_path):
        """RC-CORE1 — Test resolving dummy Mira character by alias."""
        import json

        # Create project profile with Mira
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        project_profile = {
            "project_id": "test_project",
            "characters": {
                "mira": {
                    "character_id": "mira",
                    "name": "Mira",
                    "aliases": ["Мира", "mira", "Mira"],
                    "reference_image_path": "D:\\DummyProject\\refs\\Mira.png",
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "mira_clean_single_portrait_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.33, 0.0, 0.66, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }

        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        # Test Mira resolution by various aliases
        profile = resolve_character_profile("Mira", tmp_path)
        assert profile is not None
        assert profile.character_id == "mira"

        profile = resolve_character_profile("Мира", tmp_path)
        assert profile is not None
        assert profile.character_id == "mira"

        profile = resolve_character_profile("mira", tmp_path)
        assert profile is not None
        assert profile.character_id == "mira"

    def test_dummy_mira_clean_reference_config(self, tmp_path):
        """RC-CORE1 — Test dummy Mira clean reference config is correct."""
        import json

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        project_profile = {
            "project_id": "test_project",
            "characters": {
                "mira": {
                    "character_id": "mira",
                    "name": "Mira",
                    "aliases": ["Мира", "mira"],
                    "reference_image_path": "D:\\DummyProject\\refs\\Mira.png",
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "mira_clean_single_portrait_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.33, 0.0, 0.66, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }

        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        profile = load_project_profile(tmp_path)
        mira = profile.characters["mira"]

        assert mira.clean_reference is not None
        assert mira.clean_reference.strategy == "single_panel_crop"
        assert mira.clean_reference.output_name == "mira_clean_single_portrait_480x640.png"
        assert mira.clean_reference.target_width == 480
        assert mira.clean_reference.target_height == 640
        assert mira.clean_reference.crop_box == [0.33, 0.0, 0.66, 0.42]

    def test_portability_second_character_without_core_changes(self, tmp_path):
        """RC-CORE1 — Prove second character works without core code changes."""
        import json

        # This test proves that adding a new character (Mira) only requires
        # changes to project_profile.json, not core code.

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create profile with both Alya and Mira
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": "F:\\VideoProjects\\МИР\\Эрдан\\референсы\\Аля.png",
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
                "mira": {
                    "character_id": "mira",
                    "name": "Mira",
                    "aliases": ["Мира", "mira"],
                    "reference_image_path": "D:\\DummyProject\\refs\\Mira.png",
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "mira_clean_single_portrait_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.33, 0.0, 0.66, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }

        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        profile = load_project_profile(tmp_path)

        # Both characters should resolve without core code changes
        alya = profile.resolve_character("Alya")
        mira = profile.resolve_character("Mira")

        assert alya is not None
        assert alya.character_id == "alya"
        assert mira is not None
        assert mira.character_id == "mira"

        # Both should have clean reference configs
        assert alya.clean_reference is not None
        assert mira.clean_reference is not None

        # Configs should have different crop boxes (proving they're profile-driven)
        assert alya.clean_reference.crop_box == [0.0, 0.0, 0.3333, 0.42]
        assert mira.clean_reference.crop_box == [0.33, 0.0, 0.66, 0.42]


# Legacy tests for old profile system (only run if available)
if LEGACY_AVAILABLE:
    class TestLegacyProjectProfile:
        """Test ProjectProfileLoader functionality."""
        
        @pytest.fixture
        def loader(self):
            """Create a loader with default data directory."""
            return ProjectProfileLoader(base_data_dir="data")
        
        def test_project_profile_loads_for_popadanka_erdan(self, loader):
            """Test that project_profile loads for popadanka_erdan."""
            project_root = Path("data/projects/popadanka_erdan")
            
            profile = loader.load(project_root)
            
            assert profile.project_id == "popadanka_erdan"
            assert profile.title == "Попаданка / Erdan"
            assert profile.default_aspect_ratio == "9:16"
            assert profile.safe_resolution.width == 480
            assert profile.safe_resolution.height == 640
            assert profile.generation_policy.require_kb_ready is True
            assert profile.generation_policy.require_reference_lock_for_main_characters is True
            assert profile.generation_policy.allow_prompt_only_for_background_characters is False
        
        def test_project_profile_to_dict(self, loader):
            """Test that project profile can be serialized to dict."""
            project_root = Path("data/projects/popadanka_erdan")
            
            profile = loader.load(project_root)
            profile_dict = profile.to_dict()
            
            assert profile_dict["project_id"] == "popadanka_erdan"
            assert profile_dict["title"] == "Попаданка / Erdan"
            assert profile_dict["default_aspect_ratio"] == "9:16"
            assert "safe_resolution" in profile_dict
            assert "generation_policy" in profile_dict
        
        def test_project_profile_from_dict(self):
            """Test that project profile can be deserialized from dict."""
            data = {
                "project_id": "test_project",
                "title": "Test Project",
                "source_root": "/path/to/source",
                "default_aspect_ratio": "16:9",
                "safe_resolution": {"width": 1920, "height": 1080},
                "generation_policy": {
                    "require_kb_ready": False,
                    "require_reference_lock_for_main_characters": False,
                    "allow_prompt_only_for_background_characters": True,
                },
            }
            
            profile = LegacyProjectProfile.from_dict(data)
            
            assert profile.project_id == "test_project"
            assert profile.title == "Test Project"
            assert profile.safe_resolution.width == 1920
            assert profile.safe_resolution.height == 1080
            assert profile.generation_policy.require_kb_ready is False
            assert profile.generation_policy.allow_prompt_only_for_background_characters is True


    class TestLegacyCharacterRegistry:
        """Test CharacterRegistryLoader functionality."""
        
        @pytest.fixture
        def loader(self):
            """Create a loader with default data directory."""
            return CharacterRegistryLoader(base_data_dir="data")
        
        def test_character_registry_loads_all_5_main_characters(self, loader):
            """Test that character_registry loads all 5 main characters."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            
            assert len(registry.characters) == 5
            
            character_ids = [c.character_id for c in registry.characters]
            assert "alya" in character_ids
            assert "kael" in character_ids
            assert "sera" in character_ids
            assert "lord_naris" in character_ids
            assert "master_eydon" in character_ids
        
        def test_alya_is_reference_required_and_approved(self, loader):
            """Test that Alya is reference_required and approved."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            alya = registry.get_character("alya")
            
            assert alya is not None
            assert alya.character_id == "alya"
            assert alya.name == "Аля"
            assert alya.role == "protagonist"
            assert alya.reference_required is True
            assert alya.status == CharacterStatus.APPROVED
        
        def test_kael_is_reference_required_and_missing(self, loader):
            """Test that Kael is reference_required and missing."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            kael = registry.get_character("kael")
            
            assert kael is not None
            assert kael.character_id == "kael"
            assert kael.name == "Kael"
            assert kael.role == "main_character"
            assert kael.reference_required is True
            assert kael.status == CharacterStatus.MISSING
        
        def test_list_reference_required_characters(self, loader):
            """Test that list_reference_required_characters returns all required characters."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            required_chars = registry.list_reference_required_characters()
            
            assert len(required_chars) == 5  # All 5 main characters require references
            
            for char in required_chars:
                assert char.reference_required is True
        
        def test_get_character_returns_none_for_unknown(self, loader):
            """Test that get_character returns None for unknown character."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            unknown = registry.get_character("unknown_character")
            
            assert unknown is None
        
        def test_character_entry_to_dict(self, loader):
            """Test that character entry can be serialized to dict."""
            project_root = Path("data/projects/popadanka_erdan")
            
            registry = loader.load(project_root)
            alya = registry.get_character("alya")
            alya_dict = alya.to_dict()
            
            assert alya_dict["character_id"] == "alya"
            assert alya_dict["name"] == "Аля"
            assert alya_dict["reference_required"] is True
            assert alya_dict["status"] == "approved"
        
        def test_character_entry_from_dict(self):
            """Test that character entry can be deserialized from dict."""
            data = {
                "character_id": "test_char",
                "name": "Test Character",
                "role": "supporting",
                "reference_required": False,
                "status": "pending",
            }
            
            char = CharacterEntry.from_dict(data)
            
            assert char.character_id == "test_char"
            assert char.name == "Test Character"
            assert char.reference_required is False
            assert char.status == CharacterStatus.PENDING
