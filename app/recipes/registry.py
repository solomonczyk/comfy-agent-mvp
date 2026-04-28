"""MK-RECIPE1 — Recipe and hardware profile registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import GenerationRecipe, HardwareProfile


class RecipeRegistry:
    """Registry for generation recipes."""

    def __init__(self, recipes_path: Path | str = "data/generation_recipes.json"):
        """Initialize the recipe registry.
        
        Args:
            recipes_path: Path to the recipes JSON file.
        """
        self.recipes_path = Path(recipes_path)
        self._recipes: dict[str, "GenerationRecipe"] = {}

    def load(self) -> list["GenerationRecipe"]:
        """Load recipes from the JSON file.
        
        Returns:
            List of loaded recipes.
        """
        if not self.recipes_path.exists():
            raise FileNotFoundError(f"Recipes file not found: {self.recipes_path}")
        
        with open(self.recipes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        from .models import GenerationRecipe
        
        recipes = [GenerationRecipe.from_dict(item) for item in data]
        self._recipes = {recipe.recipe_id: recipe for recipe in recipes}
        return recipes

    def get(self, recipe_id: str) -> "GenerationRecipe":
        """Get a recipe by ID.
        
        Args:
            recipe_id: The recipe ID to retrieve.
            
        Returns:
            The generation recipe.
            
        Raises:
            KeyError: If recipe ID not found.
        """
        if not self._recipes:
            self.load()
        
        if recipe_id not in self._recipes:
            raise KeyError(f"Recipe not found: {recipe_id}")
        
        return self._recipes[recipe_id]

    def find_for_task(
        self, task_type: str, model_family: str | None = None
    ) -> list["GenerationRecipe"]:
        """Find recipes for a given task type.
        
        Args:
            task_type: The task type to search for.
            model_family: Optional model family filter.
            
        Returns:
            List of matching recipes.
        """
        if not self._recipes:
            self.load()
        
        matching = []
        for recipe in self._recipes.values():
            if recipe.task_type == task_type:
                if model_family is None or recipe.model_family == model_family:
                    matching.append(recipe)
        
        return matching

    def all(self) -> list["GenerationRecipe"]:
        """Get all loaded recipes.
        
        Returns:
            List of all recipes.
        """
        if not self._recipes:
            self.load()
        
        return list(self._recipes.values())


class HardwareProfileRegistry:
    """Registry for hardware profiles."""

    def __init__(self, profiles_path: Path | str = "data/hardware_profiles.json"):
        """Initialize the hardware profile registry.
        
        Args:
            profiles_path: Path to the hardware profiles JSON file.
        """
        self.profiles_path = Path(profiles_path)
        self._profiles: dict[str, "HardwareProfile"] = {}

    def load(self) -> list["HardwareProfile"]:
        """Load hardware profiles from the JSON file.
        
        Returns:
            List of loaded hardware profiles.
        """
        if not self.profiles_path.exists():
            raise FileNotFoundError(f"Hardware profiles file not found: {self.profiles_path}")
        
        with open(self.profiles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        from .models import HardwareProfile
        
        profile = HardwareProfile.from_dict(data)
        self._profiles = {profile.profile_id: profile}
        return [profile]

    def get(self, profile_id: str) -> "HardwareProfile":
        """Get a hardware profile by ID.
        
        Args:
            profile_id: The profile ID to retrieve.
            
        Returns:
            The hardware profile.
            
        Raises:
            KeyError: If profile ID not found.
        """
        if not self._profiles:
            self.load()
        
        if profile_id not in self._profiles:
            raise KeyError(f"Hardware profile not found: {profile_id}")
        
        return self._profiles[profile_id]

    def all(self) -> list["HardwareProfile"]:
        """Get all loaded hardware profiles.
        
        Returns:
            List of all hardware profiles.
        """
        if not self._profiles:
            self.load()
        
        return list(self._profiles.values())
