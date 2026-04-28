"""
GORYNYCH-COMFY Protocol Module
Knowledge-driven planning layer for ComfyUI combine.

This module provides:
- Knowledge loading from markdown files
- Contract definitions for story, character, and shot structures
- Planner that produces structured artifacts without calling ComfyUI

The GORYNYCH-COMFY protocol ensures:
- Knowledge files are loaded from disk, not hardcoded
- All artifacts are JSON serializable
- Downstream generation remains blocked until reference lock is completed
- No image generation occurs in the planning layer
"""

from app.gorynych.knowledge import (
    load_head_1,
    load_head_2,
    load_head_3,
    validate_knowledge_files,
    load_all_knowledge,
)

from app.gorynych.contracts import (
    StoryContract,
    ScenePlan,
    BeatSpec,
    CharacterCanon,
    CharacterAnchor,
    ReferenceLockContract,
    ShotContract,
    PromptPack,
)

from app.gorynych.planner import GorynychPlanner

__all__ = [
    # Knowledge
    "load_head_1",
    "load_head_2",
    "load_head_3",
    "validate_knowledge_files",
    "load_all_knowledge",
    # Contracts
    "StoryContract",
    "ScenePlan",
    "BeatSpec",
    "CharacterCanon",
    "CharacterAnchor",
    "ReferenceLockContract",
    "ShotContract",
    "PromptPack",
    # Planner
    "GorynychPlanner",
]
