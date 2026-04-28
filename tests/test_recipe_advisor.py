"""Tests for generation settings advisor."""
import pytest

from app.recipes.advisor import GenerationSettingsAdvisor
from app.recipes.registry import HardwareProfileRegistry, RecipeRegistry


class TestGenerationSettingsAdvisor:
    """Test GenerationSettingsAdvisor."""

    def test_storyboard_task_selects_storyboard_recipe(self):
        """Test that storyboard task selects storyboard recipe."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)

        project_profile = {"reference_lock_required": False}
        recipe = advisor.recommend_recipe("storyboard_keyframes", project_profile)

        assert recipe.recipe_id == "sdxl_storyboard_keyframes_gtx1060"
        assert recipe.task_type == "storyboard_keyframes"

    def test_reference_lock_required_selects_reference_locked_recipe(self):
        """Test that reference lock required selects reference-locked recipe."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)

        project_profile = {"reference_lock_required": True}
        recipe = advisor.recommend_recipe("storyboard_keyframes", project_profile)

        assert recipe.recipe_id == "sdxl_reference_locked_character_gtx1060"
        assert recipe.task_type == "reference_locked_character"

    def test_phone_screen_task_selects_phone_overlay_recipe(self):
        """Test that phone/screen task selects phone overlay recipe."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)

        project_profile = {"reference_lock_required": False}

        # Test various phone/screen keywords
        for task_type in ["phone_screen_overlay", "screen_shot", "alarm_ui", "error_dialog"]:
            recipe = advisor.recommend_recipe(task_type, project_profile)
            assert recipe.recipe_id == "sdxl_phone_screen_overlay_gtx1060"
            assert recipe.task_type == "phone_screen_overlay"

    def test_advisor_is_deterministic(self):
        """Test that advisor returns the same recipe for the same inputs."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)

        project_profile = {"reference_lock_required": False}

        recipe1 = advisor.recommend_recipe("storyboard_keyframes", project_profile)
        recipe2 = advisor.recommend_recipe("storyboard_keyframes", project_profile)

        assert recipe1.recipe_id == recipe2.recipe_id

    def test_advisor_does_not_mutate_project_profile_dict(self):
        """Test that advisor does not mutate the project profile dict."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)

        project_profile = {"reference_lock_required": False, "custom_key": "custom_value"}
        original_profile = project_profile.copy()

        advisor.recommend_recipe("storyboard_keyframes", project_profile)

        assert project_profile == original_profile
