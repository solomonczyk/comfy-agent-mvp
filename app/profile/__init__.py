"""MK-PROFILE1 — Project profile system for reference staging strategies.

This module provides a project-profile-driven system for reference staging,
allowing different projects and characters to have custom clean reference
generation strategies without hardcoding character-specific logic in core code.
"""
from app.profile.project_profile import (
    ProjectProfile,
    CharacterProfile,
    CleanReferenceConfig,
    load_project_profile,
    resolve_character_profile,
)

__all__ = [
    "ProjectProfile",
    "CharacterProfile",
    "CleanReferenceConfig",
    "load_project_profile",
    "resolve_character_profile",
]
