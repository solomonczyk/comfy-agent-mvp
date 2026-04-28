"""
Reference-Locked Generation Gate for preventing prompt-only generation.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.projects.characters import CharacterRegistry, CharacterRegistryLoader, CharacterStatus


@dataclass
class GateDecision:
    """Decision for whether generation is allowed."""
    allowed: bool
    reason: str
    missing_references: List[str] = field(default_factory=list)
    approved_references: List[str] = field(default_factory=list)
    checked_characters: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "missing_references": self.missing_references,
            "approved_references": self.approved_references,
            "checked_characters": self.checked_characters,
            "warnings": self.warnings,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GateDecision":
        return cls(**data)


class ReferenceLockGate:
    """
    Gate that checks reference lock status before allowing generation.
    
    This gate prevents prompt-only generation for characters that require
    approved references. It is project-agnostic and uses character registry
    to determine requirements.
    """
    
    def __init__(self, base_data_dir: str = "output/control"):
        """Initialize the gate with base data directory."""
        self.base_data_dir = Path(base_data_dir)
        self.registry_loader = CharacterRegistryLoader(base_data_dir)
    
    def can_generate_character(
        self, 
        project_root: Path, 
        character_id: str
    ) -> GateDecision:
        """
        Check if generation is allowed for a specific character.
        
        Args:
            project_root: Path to project root directory
            character_id: Character identifier (e.g., "alya", "kael")
            
        Returns:
            GateDecision: Decision with allowed status and reason
            
        Rules:
        - If character does not exist in registry: deny
        - If character.reference_required=true and lock file missing: deny
        - If lock exists but reference_lock_status != "approved": deny
        - If downstream_generation_allowed != true: deny
        - If all required character locks are approved: allow
        - If character.reference_required=false: allow with warning
        """
        # Load character registry
        try:
            character_registry = self.registry_loader.load(project_root)
        except FileNotFoundError:
            return GateDecision(
                allowed=False,
                reason=f"character_registry.json not found for project",
            )
        
        # Check if character exists in registry
        character = character_registry.get_character(character_id)
        if character is None:
            return GateDecision(
                allowed=False,
                reason=f"character not found in registry: {character_id}",
            )
        
        decision = GateDecision(
            allowed=False,
            reason="",
            checked_characters=[character_id],
        )
        
        # Check if reference is required
        if not character.reference_required:
            decision.allowed = True
            decision.reason = f"prompt-only allowed for non-critical character: {character_id}"
            decision.warnings.append(f"Character {character_id} does not require reference lock")
            return decision
        
        # Reference is required - check for lock file
        control_dir = project_root / "output" / "control"
        reference_locks_dir = control_dir / "reference_locks"
        character_lock_path = reference_locks_dir / f"{character_id}_reference_lock.json"
        
        if not character_lock_path.exists():
            decision.reason = f"missing reference lock for character: {character_id}"
            decision.missing_references.append(f"{character_id}_reference_lock")
            return decision
        
        # Load and validate reference lock
        try:
            with open(character_lock_path, 'r', encoding='utf-8') as f:
                character_lock = json.load(f)
        except Exception:
            decision.reason = f"reference lock invalid for character: {character_id}"
            return decision
        
        # Check reference lock status
        if character_lock.get("reference_lock_status") != "approved":
            decision.reason = f"reference lock not approved for character: {character_id}"
            return decision
        
        # Check downstream generation allowed
        if not character_lock.get("downstream_generation_allowed", False):
            decision.reason = f"downstream_generation_allowed=false for character: {character_id}"
            return decision
        
        # Check approved references
        approved_refs = character_lock.get("approved_references", [])
        if not approved_refs:
            decision.reason = f"approved_references list is empty for character: {character_id}"
            decision.missing_references.append(f"ref_{character_id}")
            return decision
        
        # All checks passed
        decision.allowed = True
        decision.reason = f"Reference lock approved for character: {character_id}"
        decision.approved_references = approved_refs
        return decision
    
    def can_generate_prompt_pack(
        self, 
        project_root: Path, 
        prompt_pack: dict
    ) -> GateDecision:
        """
        Check if generation is allowed for a prompt pack.
        
        Args:
            project_root: Path to project root directory
            prompt_pack: Prompt pack dictionary containing character information
            
        Returns:
            GateDecision: Decision with allowed status and reason
            
        If prompt_pack contains characters without approved references:
        - deny generation
        - reason: "missing reference lock for character: <name>"
        """
        # Load character registry
        try:
            character_registry = self.registry_loader.load(project_root)
        except FileNotFoundError:
            return GateDecision(
                allowed=False,
                reason=f"character_registry.json not found for project",
            )
        
        # Extract character IDs from prompt pack
        character_ids = self._extract_characters_from_prompt_pack(prompt_pack)
        
        if not character_ids:
            # No characters specified, allow generation (scenic shots, etc.)
            return GateDecision(
                allowed=True,
                reason="No characters specified in prompt pack",
            )
        
        # Check each character
        missing_refs = []
        approved_refs = []
        all_warnings = []
        all_checked = []
        
        for character_id in character_ids:
            decision = self.can_generate_character(project_root, character_id)
            
            all_checked.append(character_id)
            all_warnings.extend(decision.warnings)
            
            if decision.allowed:
                approved_refs.extend(decision.approved_references)
            else:
                missing_refs.append(character_id)
        
        if missing_refs:
            return GateDecision(
                allowed=False,
                reason=f"missing reference lock for character(s): {', '.join(missing_refs)}",
                missing_references=missing_refs,
                approved_references=approved_refs,
                checked_characters=all_checked,
                warnings=all_warnings,
            )
        
        # All characters approved
        return GateDecision(
            allowed=True,
            reason=f"All character reference locks approved: {', '.join(character_ids)}",
            approved_references=approved_refs,
            checked_characters=all_checked,
            warnings=all_warnings,
        )
    
    def _extract_characters_from_prompt_pack(self, prompt_pack: dict) -> List[str]:
        """
        Extract character IDs from prompt pack.
        
        Supports both:
        - Top-level characters: {"characters": ["alya"], "beats": [...]}
        - Beat-level characters: {"beats": [{"beat_id": "...", "characters": ["alya"]}]}
        
        If both exist, merges and dedupes.
        """
        characters = []
        
        # Check for top-level characters
        if "characters" in prompt_pack and isinstance(prompt_pack["characters"], list):
            characters.extend(prompt_pack["characters"])
        
        # Check for character_id field (legacy)
        if "character_id" in prompt_pack:
            characters.append(prompt_pack["character_id"])
        
        # Check for protagonist field (legacy)
        if "protagonist" in prompt_pack:
            characters.append(prompt_pack["protagonist"])
        
        # Check for beat-level characters
        if "beats" in prompt_pack and isinstance(prompt_pack["beats"], list):
            for beat in prompt_pack["beats"]:
                if isinstance(beat, dict) and "characters" in beat:
                    if isinstance(beat["characters"], list):
                        characters.extend(beat["characters"])
                    else:
                        characters.append(beat["characters"])
        
        # Dedupe while preserving order
        seen = set()
        unique_characters = []
        for char in characters:
            if char and char not in seen:
                seen.add(char)
                unique_characters.append(char)
        
        return unique_characters
