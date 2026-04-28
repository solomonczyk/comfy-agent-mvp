"""MK-RECIPE1 — Generation settings advisor."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import GenerationRecipe
    from .registry import HardwareProfileRegistry, RecipeRegistry


class GenerationSettingsAdvisor:
    """Advisor for selecting appropriate generation recipes based on task context."""

    def __init__(
        self,
        recipe_registry: RecipeRegistry,
        hardware_registry: HardwareProfileRegistry,
    ):
        """Initialize the advisor.
        
        Args:
            recipe_registry: The recipe registry.
            hardware_registry: The hardware profile registry.
        """
        self.recipe_registry = recipe_registry
        self.hardware_registry = hardware_registry

    def recommend_recipe(
        self,
        task_type: str,
        project_profile: dict,
        hardware_profile_id: str = "gtx_1060_5gb",
        generation_mode: str | None = None,
    ) -> GenerationRecipe:
        """Recommend a recipe for the given task and project profile.
        
        Rules:
        - If task_type contains phone/screen/alarm/error UI intent → choose phone_screen_overlay recipe.
        - If generation_mode is "reference_locked" → choose reference_locked_character recipe.
        - If reference lock is required → choose reference_locked_character recipe.
        - Otherwise choose storyboard_keyframes recipe.
        
        Args:
            task_type: The generation task type.
            project_profile: Project profile dictionary.
            hardware_profile_id: Hardware profile ID (default: gtx_1060_5gb).
            generation_mode: Optional generation mode.
            
        Returns:
            The recommended generation recipe.
        """
        task_type_lower = task_type.lower()
        
        # Check for phone/screen/alarm/error UI intent
        if any(keyword in task_type_lower for keyword in ["phone", "screen", "alarm", "error"]):
            return self.recipe_registry.get("sdxl_phone_screen_overlay_gtx1060")
        
        # MK-REF1R-5 — Check if generation_mode is reference_locked
        if generation_mode == "reference_locked":
            return self.recipe_registry.get("sdxl_reference_locked_character_gtx1060")
        
        # Check if reference lock is required
        reference_lock_required = project_profile.get("reference_lock_required", False)
        if reference_lock_required:
            return self.recipe_registry.get("sdxl_reference_locked_character_gtx1060")
        
        # Default to storyboard keyframes
        return self.recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
