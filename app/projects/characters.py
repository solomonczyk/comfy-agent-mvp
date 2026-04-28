"""
Character registry loader for generic character management.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class CharacterStatus(str, Enum):
    """Character reference status."""
    APPROVED = "approved"
    MISSING = "missing"
    PENDING = "pending"
    REJECTED = "rejected"


@dataclass
class CharacterEntry:
    """Character entry in registry."""
    character_id: str
    name: str
    role: str
    reference_required: bool = True
    status: CharacterStatus = CharacterStatus.MISSING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "role": self.role,
            "reference_required": self.reference_required,
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterEntry":
        # Use character_id if present, otherwise derive from name
        character_id = data.get("character_id")
        if not character_id:
            # Derive character_id from name (lowercase, replace spaces with underscores)
            name = data.get("name", "")
            character_id = name.lower().replace(" ", "_") if name else "unknown"
        return cls(
            character_id=character_id,
            name=data["name"],
            role=data.get("role", "character"),
            reference_required=data.get("reference_required", True),
            status=CharacterStatus(data.get("status", "missing")),
        )


@dataclass
class CharacterRegistry:
    """Character registry with all project characters."""
    characters: List[CharacterEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": [c.to_dict() for c in self.characters],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterRegistry":
        characters = [CharacterEntry.from_dict(c) for c in data.get("characters", [])]
        return cls(characters=characters)
    
    def get_character(self, character_id: str) -> Optional[CharacterEntry]:
        """Get character by ID (case-insensitive)."""
        character_id_lower = character_id.lower()
        for char in self.characters:
            if char.character_id.lower() == character_id_lower:
                return char
        return None
    
    def list_reference_required_characters(self) -> List[CharacterEntry]:
        """List all characters that require references."""
        return [c for c in self.characters if c.reference_required]


class CharacterRegistryLoader:
    """Loader for character registries."""
    
    def __init__(self, base_data_dir: str = "data"):
        """Initialize the loader with base data directory."""
        self.base_data_dir = Path(base_data_dir)
    
    def load(self, project_root: Path) -> CharacterRegistry:
        """
        Load character registry from project root.
        
        Args:
            project_root: Path to project root directory (e.g., data/projects/popadanka_erdan)
            
        Returns:
            CharacterRegistry: Loaded character registry
            
        Raises:
            FileNotFoundError: If character_registry.json is not found
        """
        registry_path = project_root / "output" / "control" / "character_registry.json"
        
        if not registry_path.exists():
            raise FileNotFoundError(f"character_registry.json not found at {registry_path}")
        
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return CharacterRegistry.from_dict(data)
    
    def load_by_id(self, project_id: str) -> CharacterRegistry:
        """
        Load character registry by project ID.
        
        Args:
            project_id: Project identifier
            
        Returns:
            CharacterRegistry: Loaded character registry
        """
        project_root = self.base_data_dir / "projects" / project_id
        return self.load(project_root)
