"""
Project profile loader for generic project configuration.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class GenerationPolicy:
    """Generation policy configuration."""
    require_kb_ready: bool = True
    require_reference_lock_for_main_characters: bool = True
    allow_prompt_only_for_background_characters: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_kb_ready": self.require_kb_ready,
            "require_reference_lock_for_main_characters": self.require_reference_lock_for_main_characters,
            "allow_prompt_only_for_background_characters": self.allow_prompt_only_for_background_characters,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationPolicy":
        return cls(**data)


@dataclass
class SafeResolution:
    """Safe resolution configuration."""
    width: int = 480
    height: int = 640
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "width": self.width,
            "height": self.height,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "SafeResolution":
        return cls(**data)


@dataclass
class ProjectProfile:
    """Project profile with project-specific configuration."""
    project_id: str
    title: str
    source_root: Optional[str] = None
    default_aspect_ratio: str = "16:9"
    safe_resolution: SafeResolution = field(default_factory=SafeResolution)
    generation_policy: GenerationPolicy = field(default_factory=GenerationPolicy)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "source_root": self.source_root,
            "default_aspect_ratio": self.default_aspect_ratio,
            "safe_resolution": self.safe_resolution.to_dict(),
            "generation_policy": self.generation_policy.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectProfile":
        safe_resolution = SafeResolution.from_dict(data.get("safe_resolution", {}))
        generation_policy = GenerationPolicy.from_dict(data.get("generation_policy", {}))
        
        return cls(
            project_id=data["project_id"],
            title=data["title"],
            source_root=data.get("source_root"),
            default_aspect_ratio=data.get("default_aspect_ratio", "16:9"),
            safe_resolution=safe_resolution,
            generation_policy=generation_policy,
        )


class ProjectProfileLoader:
    """Loader for project profiles."""
    
    def __init__(self, base_data_dir: str = "data"):
        """Initialize the loader with base data directory."""
        self.base_data_dir = Path(base_data_dir)
    
    def load(self, project_root: Path) -> ProjectProfile:
        """
        Load project profile from project root.
        
        Args:
            project_root: Path to project root directory (e.g., data/projects/popadanka_erdan)
            
        Returns:
            ProjectProfile: Loaded project profile
            
        Raises:
            FileNotFoundError: If project_profile.json is not found
        """
        profile_path = project_root / "output" / "control" / "project_profile.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"project_profile.json not found at {profile_path}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return ProjectProfile.from_dict(data)
    
    def load_by_id(self, project_id: str) -> ProjectProfile:
        """
        Load project profile by project ID.
        
        Args:
            project_id: Project identifier
            
        Returns:
            ProjectProfile: Loaded project profile
        """
        project_root = self.base_data_dir / "projects" / project_id
        return self.load(project_root)
