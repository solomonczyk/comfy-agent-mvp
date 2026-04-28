"""Tests for recipe and hardware profile registry."""
import pytest

from app.recipes.models import GenerationRecipe, HardwareProfile
from app.recipes.registry import HardwareProfileRegistry, RecipeRegistry


class TestRecipeRegistry:
    """Test RecipeRegistry."""

    def test_loads_generation_recipes_json(self):
        """Test that generation_recipes.json can be loaded."""
        registry = RecipeRegistry()
        recipes = registry.load()
        assert len(recipes) == 3
        assert all(isinstance(r, GenerationRecipe) for r in recipes)

    def test_get_known_recipe_by_recipe_id(self):
        """Test getting a known recipe by ID."""
        registry = RecipeRegistry()
        recipe = registry.get("sdxl_storyboard_keyframes_gtx1060")
        assert recipe.recipe_id == "sdxl_storyboard_keyframes_gtx1060"
        assert recipe.task_type == "storyboard_keyframes"
        assert recipe.model_family == "sdxl"

    def test_unknown_recipe_raises_clear_error(self):
        """Test that unknown recipe raises KeyError."""
        registry = RecipeRegistry()
        with pytest.raises(KeyError, match="Recipe not found"):
            registry.get("unknown_recipe")

    def test_find_for_task(self):
        """Test finding recipes by task type."""
        registry = RecipeRegistry()
        recipes = registry.find_for_task("storyboard_keyframes")
        assert len(recipes) == 1
        assert recipes[0].recipe_id == "sdxl_storyboard_keyframes_gtx1060"

    def test_find_for_task_with_model_family(self):
        """Test finding recipes by task type and model family."""
        registry = RecipeRegistry()
        recipes = registry.find_for_task("storyboard_keyframes", "sdxl")
        assert len(recipes) == 1
        assert recipes[0].model_family == "sdxl"

    def test_all_recipes(self):
        """Test getting all recipes."""
        registry = RecipeRegistry()
        recipes = registry.all()
        assert len(recipes) == 3


class TestHardwareProfileRegistry:
    """Test HardwareProfileRegistry."""

    def test_loads_hardware_profiles_json(self):
        """Test that hardware_profiles.json can be loaded."""
        registry = HardwareProfileRegistry()
        profiles = registry.load()
        assert len(profiles) == 1
        assert all(isinstance(p, HardwareProfile) for p in profiles)

    def test_get_known_hardware_profile_gtx_1060_5gb(self):
        """Test getting GTX 1060 5GB profile."""
        registry = HardwareProfileRegistry()
        profile = registry.get("gtx_1060_5gb")
        assert profile.profile_id == "gtx_1060_5gb"
        assert profile.gpu_name == "GTX 1060 5GB"
        assert profile.vram_gb == 5
        assert profile.max_pixels_sdxl == 307200
        assert profile.max_batch_size_sdxl == 3
        assert profile.recommended_batch_size_sdxl == 2

    def test_unknown_hardware_profile_raises_clear_error(self):
        """Test that unknown hardware profile raises KeyError."""
        registry = HardwareProfileRegistry()
        with pytest.raises(KeyError, match="Hardware profile not found"):
            registry.get("unknown_profile")

    def test_all_profiles(self):
        """Test getting all hardware profiles."""
        registry = HardwareProfileRegistry()
        profiles = registry.all()
        assert len(profiles) == 1
