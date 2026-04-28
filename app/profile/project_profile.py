"""MK-PROFILE1 — Project profile system for reference staging strategies.

This module provides a project-profile-driven system for reference staging,
allowing different projects and characters to have custom clean reference
generation strategies without hardcoding character-specific logic in core code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CleanReferenceConfig:
    """Configuration for clean reference generation strategy.

    Attributes:
        strategy: The strategy to use (e.g., "single_panel_crop")
        output_name: The filename for the generated clean reference
        target_width: Target width in pixels
        target_height: Target height in pixels
        crop_box_mode: How to interpret crop_box ("relative" or "absolute")
        crop_box: Crop box as [left, top, right, bottom] (relative or absolute)
        centering: Centering for ImageOps.fit as [x, y]
        force_regenerate: Whether to always regenerate even if file exists
    """
    strategy: str
    output_name: str
    target_width: int
    target_height: int
    crop_box_mode: str = "relative"
    crop_box: list[float] = field(default_factory=lambda: [0.0, 0.0, 1.0, 1.0])
    centering: list[float] = field(default_factory=lambda: [0.5, 0.5])
    force_regenerate: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleanReferenceConfig:
        """Create CleanReferenceConfig from dictionary."""
        return cls(
            strategy=data.get("strategy", "single_panel_crop"),
            output_name=data.get("output_name", "clean_reference_480x640.png"),
            target_width=data.get("target_width", 480),
            target_height=data.get("target_height", 640),
            crop_box_mode=data.get("crop_box_mode", "relative"),
            crop_box=data.get("crop_box", [0.0, 0.0, 1.0, 1.0]),
            centering=data.get("centering", [0.5, 0.5]),
            force_regenerate=data.get("force_regenerate", True),
        )


@dataclass
class CharacterProfile:
    """Profile for a character in a project.

    Attributes:
        character_id: Unique character identifier
        name: Character display name
        aliases: Alternative names for the character
        reference_image_path: Path to the original reference image
        reference_role: Role of the reference (e.g., "character_identity")
        clean_reference: Configuration for clean reference generation
    """
    character_id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    reference_image_path: str = ""
    reference_role: str = "character_identity"
    clean_reference: CleanReferenceConfig | None = None

    @classmethod
    def from_dict(cls, character_id: str, data: dict[str, Any]) -> CharacterProfile:
        """Create CharacterProfile from dictionary."""
        clean_ref_data = data.get("clean_reference")
        clean_reference = None
        if clean_ref_data:
            clean_reference = CleanReferenceConfig.from_dict(clean_ref_data)

        return cls(
            character_id=character_id,
            name=data.get("name", character_id),
            aliases=data.get("aliases", []),
            reference_image_path=data.get("reference_image_path", ""),
            reference_role=data.get("reference_role", "character_identity"),
            clean_reference=clean_reference,
        )

    def matches_alias(self, name: str) -> bool:
        """Check if a name matches this character (case-insensitive)."""
        name_lower = name.lower()
        if name_lower == self.character_id.lower():
            return True
        if name_lower == self.name.lower():
            return True
        for alias in self.aliases:
            if name_lower == alias.lower():
                return True
        return False


@dataclass
class ProjectProfile:
    """Profile for a project containing character configurations.

    Attributes:
        project_id: Unique project identifier
        characters: Dictionary of character_id to CharacterProfile
    """
    project_id: str
    characters: dict[str, CharacterProfile] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectProfile:
        """Create ProjectProfile from dictionary."""
        characters = {}
        for char_id, char_data in data.get("characters", {}).items():
            characters[char_id] = CharacterProfile.from_dict(char_id, char_data)

        return cls(
            project_id=data.get("project_id", "unknown"),
            characters=characters,
        )

    def resolve_character(self, name: str) -> CharacterProfile | None:
        """Resolve a character by name or alias."""
        name_lower = name.lower()
        
        # First try direct character_id match
        if name_lower in self.characters:
            return self.characters[name_lower]
        
        # Then try matching by name or alias
        for char_profile in self.characters.values():
            if char_profile.matches_alias(name):
                return char_profile
        
        return None


def load_project_profile(project_root: Path | str) -> ProjectProfile | None:
    """Load project profile from project root.

    Args:
        project_root: Path to project root directory

    Returns:
        ProjectProfile if found, None otherwise
    """
    project_root = Path(project_root).resolve()
    
    # Try common profile locations
    profile_paths = [
        project_root / "output" / "control" / "project_profile.json",
        project_root / "data" / "project_profile.json",
        project_root / "project_profile.json",
    ]
    
    for profile_path in profile_paths:
        if profile_path.exists():
            with open(profile_path, encoding="utf-8") as f:
                data = json.load(f)
            return ProjectProfile.from_dict(data)
    
    return None


def resolve_character_profile(
    character_name: str,
    project_root: Path | str,
) -> CharacterProfile | None:
    """Resolve character profile by name using project profile.

    Args:
        character_name: Character name or alias
        project_root: Path to project root directory

    Returns:
        CharacterProfile if found, None otherwise
    """
    profile = load_project_profile(project_root)
    if profile is None:
        return None
    
    return profile.resolve_character(character_name)
