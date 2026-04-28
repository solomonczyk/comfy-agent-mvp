"""MK-RECIPE1 — Generation Recipe Registry and Settings Advisor.

This package provides:
- Recipe definitions for approved ComfyUI generation settings
- Registry for loading and managing recipes
- Advisor for selecting appropriate recipes based on task context
- Validator for ensuring settings match recipe requirements
"""

from .models import (
    GenerationRecipe,
    HardwareProfile,
    ObservedGenerationSettings,
    RecipeIssue,
    RecipeValidationResult,
)

__all__ = [
    "GenerationRecipe",
    "HardwareProfile",
    "ObservedGenerationSettings",
    "RecipeIssue",
    "RecipeValidationResult",
]
