"""Observed settings resolver for recipe validation."""
from __future__ import annotations

import json
from pathlib import Path

from app.recipes.models import ObservedGenerationSettings


class ObservedSettingsResolver:
    """Resolve observed generation settings from multiple possible locations.
    
    Resolution order (priority):
    1. output/control/{episode_id}_{shot_id}_observed_settings.json
    2. output/observability/{episode_id}_{shot_id}_observed_settings.json
    3. data/observed_settings/{episode_id}_{shot_id}.json
    4. return None
    
    Supports both formats:
    - Direct observed settings
    - Wrapped: {"observed_settings": {...}, "raw_nodes": {...}}
    """
    
    def __init__(self, project_root: Path | str):
        """Initialize resolver with project root.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
    
    def resolve_for_shot(self, episode_id: str, shot_id: str) -> ObservedGenerationSettings | None:
        """Resolve observed settings for a specific shot.
        
        Args:
            episode_id: Episode ID (e.g., "ep01")
            shot_id: Shot ID (e.g., "shot01")
            
        Returns:
            ObservedGenerationSettings if found, None otherwise
            
        Raises:
            ValueError: If file exists but contains invalid JSON or invalid structure
        """
        # Resolution paths in priority order
        resolution_paths = [
            self.project_root / "output" / "control" / f"{episode_id}_{shot_id}_observed_settings.json",
            self.project_root / "output" / "observability" / f"{episode_id}_{shot_id}_observed_settings.json",
            self.project_root / "data" / "observed_settings" / f"{episode_id}_{shot_id}.json",
        ]
        
        for settings_path in resolution_paths:
            if settings_path.exists():
                try:
                    with open(settings_path, encoding="utf-8") as f:
                        settings_data = json.load(f)
                    
                    # Normalize format
                    if "observed_settings" in settings_data:
                        observed_dict = settings_data["observed_settings"]
                        raw_nodes = settings_data.get("raw_nodes", {})
                    else:
                        observed_dict = settings_data
                        raw_nodes = {}
                    
                    # Add raw_nodes if not present
                    observed_dict["raw_nodes"] = raw_nodes
                    
                    # Create ObservedGenerationSettings
                    return ObservedGenerationSettings.from_dict(observed_dict)
                    
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON in settings file {settings_path}: {e}"
                    ) from e
                except (KeyError, TypeError) as e:
                    raise ValueError(
                        f"Invalid structure in settings file {settings_path}: {e}"
                    ) from e
        
        # No settings file found
        return None
