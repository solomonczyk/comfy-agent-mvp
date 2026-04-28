"""MK-RECIPE1 — Generation recipe validator."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import (
        GenerationRecipe,
        HardwareProfile,
        ObservedGenerationSettings,
        RecipeIssue,
        RecipeValidationResult,
    )


class GenerationRecipeValidator:
    """Validator for generation settings against recipes."""

    def validate(
        self,
        observed: ObservedGenerationSettings | dict,
        recipe: GenerationRecipe,
        hardware: HardwareProfile,
        task_type: str,
    ) -> RecipeValidationResult:
        """Validate observed generation settings against a recipe.
        
        Args:
            observed: Observed generation settings (ObservedGenerationSettings or dict).
            recipe: The generation recipe to validate against.
            hardware: The hardware profile.
            task_type: The task type.
            
        Returns:
            RecipeValidationResult with verdict, issues, and recommendations.
        """
        from .models import ObservedGenerationSettings, RecipeIssue, RecipeValidationResult

        # Convert dict to ObservedGenerationSettings if needed
        if isinstance(observed, dict):
            observed = ObservedGenerationSettings.from_dict(observed)

        issues: list[RecipeIssue] = []
        score = 1.0

        # Hard errors
        if observed.batch_size is not None and observed.batch_size > recipe.batch_size_max:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="BATCH_SIZE_EXCEEDED",
                    message=f"Batch size {observed.batch_size} exceeds maximum {recipe.batch_size_max}",
                    expected=recipe.batch_size_max,
                    actual=observed.batch_size,
                    recommendation=f"Reduce batch size to {recipe.batch_size_max} or less",
                )
            )
            score -= 0.25

        if observed.width and observed.height:
            pixels = observed.width * observed.height
            max_pixels = min(recipe.max_pixels, hardware.max_pixels_sdxl)
            if pixels > max_pixels:
                issues.append(
                    RecipeIssue(
                        severity="error",
                        code="PIXEL_LIMIT_EXCEEDED",
                        message=f"Resolution {observed.width}x{observed.height} ({pixels} pixels) exceeds limit {max_pixels}",
                        expected=max_pixels,
                        actual=pixels,
                        recommendation=f"Reduce resolution to stay within {max_pixels} pixels",
                    )
                )
                score -= 0.25

        if not observed.checkpoint:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_CHECKPOINT",
                    message="Checkpoint is missing",
                    expected="non-empty string",
                    actual=None,
                    recommendation="Specify a checkpoint model",
                )
            )
            score -= 0.25

        if not observed.sampler_name:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_SAMPLER",
                    message="Sampler name is missing",
                    expected="non-empty string",
                    actual=None,
                    recommendation="Specify a sampler name",
                )
            )
            score -= 0.25

        if not observed.scheduler:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_SCHEDULER",
                    message="Scheduler is missing",
                    expected="non-empty string",
                    actual=None,
                    recommendation="Specify a scheduler",
                )
            )
            score -= 0.25

        if observed.steps is None:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_STEPS",
                    message="Steps is missing",
                    expected=f"{recipe.steps_min}-{recipe.steps_max}",
                    actual=None,
                    recommendation=f"Specify steps between {recipe.steps_min} and {recipe.steps_max}",
                )
            )
            score -= 0.25

        if observed.cfg is None:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_CFG",
                    message="CFG is missing",
                    expected=f"{recipe.cfg_min}-{recipe.cfg_max}",
                    actual=None,
                    recommendation=f"Specify CFG between {recipe.cfg_min} and {recipe.cfg_max}",
                )
            )
            score -= 0.25

        if observed.width is None:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_WIDTH",
                    message="Width is missing",
                    expected="positive integer",
                    actual=None,
                    recommendation="Specify image width",
                )
            )
            score -= 0.25

        if observed.height is None:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_HEIGHT",
                    message="Height is missing",
                    expected="positive integer",
                    actual=None,
                    recommendation="Specify image height",
                )
            )
            score -= 0.25

        if observed.batch_size is None:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="MISSING_BATCH_SIZE",
                    message="Batch size is missing",
                    expected="positive integer",
                    actual=None,
                    recommendation="Specify batch size",
                )
            )
            score -= 0.25

        # Unsupported scheduler
        if observed.scheduler and observed.scheduler not in recipe.scheduler_allowlist:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="UNSUPPORTED_SCHEDULER",
                    message=f"Scheduler '{observed.scheduler}' is not in allowlist",
                    expected=recipe.scheduler_allowlist,
                    actual=observed.scheduler,
                    recommendation=f"Use one of: {', '.join(recipe.scheduler_allowlist)}",
                )
            )
            score -= 0.25

        # Unsupported sampler
        if observed.sampler_name and observed.sampler_name not in recipe.sampler_allowlist:
            issues.append(
                RecipeIssue(
                    severity="error",
                    code="UNSUPPORTED_SAMPLER",
                    message=f"Sampler '{observed.sampler_name}' is not in allowlist",
                    expected=recipe.sampler_allowlist,
                    actual=observed.sampler_name,
                    recommendation=f"Use one of: {', '.join(recipe.sampler_allowlist)}",
                )
            )
            score -= 0.25

        # Steps outside range by more than 100% (error)
        if observed.steps is not None:
            steps_range = recipe.steps_max - recipe.steps_min
            steps_threshold = steps_range * 1.5
            if observed.steps < recipe.steps_min - steps_threshold or observed.steps > recipe.steps_max + steps_threshold:
                issues.append(
                    RecipeIssue(
                        severity="error",
                        code="STEPS_OUT_OF_RANGE",
                        message=f"Steps {observed.steps} is far outside recommended range {recipe.steps_min}-{recipe.steps_max}",
                        expected=f"{recipe.steps_min}-{recipe.steps_max}",
                        actual=observed.steps,
                        recommendation=f"Use steps between {recipe.steps_min} and {recipe.steps_max}",
                    )
                )
                score -= 0.25

        # CFG outside range by more than 50%
        if observed.cfg is not None:
            cfg_range = recipe.cfg_max - recipe.cfg_min
            cfg_threshold = cfg_range * 0.5
            if observed.cfg < recipe.cfg_min - cfg_threshold or observed.cfg > recipe.cfg_max + cfg_threshold:
                issues.append(
                    RecipeIssue(
                        severity="error",
                        code="CFG_OUT_OF_RANGE",
                        message=f"CFG {observed.cfg} is far outside recommended range {recipe.cfg_min}-{recipe.cfg_max}",
                        expected=f"{recipe.cfg_min}-{recipe.cfg_max}",
                        actual=observed.cfg,
                        recommendation=f"Use CFG between {recipe.cfg_min} and {recipe.cfg_max}",
                    )
                )
                score -= 0.25

        # Denoise outside allowed range when recipe defines denoise_min/max
        if recipe.denoise_min is not None and recipe.denoise_max is not None:
            if observed.denoise is not None and (observed.denoise < recipe.denoise_min or observed.denoise > recipe.denoise_max):
                issues.append(
                    RecipeIssue(
                        severity="error",
                        code="DENOISE_OUT_OF_RANGE",
                        message=f"Denoise {observed.denoise} is outside allowed range {recipe.denoise_min}-{recipe.denoise_max}",
                        expected=f"{recipe.denoise_min}-{recipe.denoise_max}",
                        actual=observed.denoise,
                        recommendation=f"Use denoise between {recipe.denoise_min} and {recipe.denoise_max}",
                    )
                )
                score -= 0.25

        # MK-REF1 — Reference-locked mode specific validations
        if getattr(observed, "generation_mode", None) == "reference_locked":
            # Denoise > 0.75 should warn for reference_locked mode
            if observed.denoise is not None and observed.denoise > 0.75:
                issues.append(
                    RecipeIssue(
                        severity="warning",
                        code="REFERENCE_DENOISE_TOO_HIGH",
                        message=f"Denoise {observed.denoise} is too high for reference-locked mode, may lose character identity",
                        expected="<= 0.75",
                        actual=observed.denoise,
                        recommendation="Reduce denoise to 0.65 or lower for better character identity preservation",
                    )
                )
                score -= 0.1

            # Batch size > 1 should fail for reference identity generation
            if observed.batch_size is not None and observed.batch_size > 1:
                issues.append(
                    RecipeIssue(
                        severity="error",
                        code="REFERENCE_BATCH_SIZE_EXCEEDED",
                        message=f"Batch size {observed.batch_size} is not allowed for reference-locked mode",
                        expected=1,
                        actual=observed.batch_size,
                        recommendation="Set batch_size to 1 for reference-locked mode to preserve character identity",
                    )
                )
                score -= 0.25

        # Warnings
        if observed.checkpoint and observed.checkpoint not in recipe.checkpoint_allowlist:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="CHECKPOINT_NOT_IN_ALLOWLIST",
                    message=f"Checkpoint '{observed.checkpoint}' is not in allowlist",
                    expected=recipe.checkpoint_allowlist,
                    actual=observed.checkpoint,
                    recommendation=f"Consider using one of: {', '.join(recipe.checkpoint_allowlist)}",
                )
            )
            score -= 0.1

        if observed.steps is not None and observed.steps < recipe.steps_min:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="STEPS_BELOW_MIN",
                    message=f"Steps {observed.steps} is below minimum {recipe.steps_min}",
                    expected=f">= {recipe.steps_min}",
                    actual=observed.steps,
                    recommendation=f"Increase steps to at least {recipe.steps_min} for better quality",
                )
            )
            score -= 0.1

        if observed.steps is not None and observed.steps > recipe.steps_max:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="STEPS_ABOVE_MAX",
                    message=f"Steps {observed.steps} is above maximum {recipe.steps_max}",
                    expected=f"<= {recipe.steps_max}",
                    actual=observed.steps,
                    recommendation=f"Reduce steps to {recipe.steps_max} or less",
                )
            )
            score -= 0.1

        if observed.cfg is not None and observed.cfg < recipe.cfg_min:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="CFG_BELOW_MIN",
                    message=f"CFG {observed.cfg} is below minimum {recipe.cfg_min}",
                    expected=f">= {recipe.cfg_min}",
                    actual=observed.cfg,
                    recommendation=f"Increase CFG to at least {recipe.cfg_min}",
                )
            )
            score -= 0.1

        if observed.cfg is not None and observed.cfg > recipe.cfg_max:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="CFG_ABOVE_MAX",
                    message=f"CFG {observed.cfg} is above maximum {recipe.cfg_max}",
                    expected=f"<= {recipe.cfg_max}",
                    actual=observed.cfg,
                    recommendation=f"Reduce CFG to {recipe.cfg_max} or less",
                )
            )
            score -= 0.1

        # Missing required negative prompt terms
        if observed.negative_prompt:
            for term in recipe.required_negative_terms:
                if term.lower() not in observed.negative_prompt.lower():
                    issues.append(
                        RecipeIssue(
                            severity="warning",
                            code="MISSING_NEGATIVE_TERM",
                            message=f"Required negative term '{term}' not found in negative prompt",
                            expected=f"contains '{term}'",
                            actual=observed.negative_prompt,
                            recommendation=f"Add '{term}' to negative prompt",
                        )
                    )
                    score -= 0.1

        # 9:16 resolution is not 480x640 on GTX 1060 5GB
        if observed.width == 480 and observed.height == 848:
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="SUBOPTIMAL_9_16_RESOLUTION",
                    message="9:16 resolution 480x848 is suboptimal for GTX 1060 5GB",
                    expected="480x640",
                    actual="480x848",
                    recommendation="Use 480x640 for 9:16 on GTX 1060 5GB",
                )
            )
            score -= 0.1

        # Batch size above recommended but still below max
        if (
            observed.batch_size is not None
            and observed.batch_size > hardware.recommended_batch_size_sdxl
            and observed.batch_size <= recipe.batch_size_max
        ):
            issues.append(
                RecipeIssue(
                    severity="warning",
                    code="BATCH_SIZE_ABOVE_RECOMMENDED",
                    message=f"Batch size {observed.batch_size} is above recommended {hardware.recommended_batch_size_sdxl}",
                    expected=f"<= {hardware.recommended_batch_size_sdxl}",
                    actual=observed.batch_size,
                    recommendation=f"Consider reducing batch size to {hardware.recommended_batch_size_sdxl}",
                )
            )
            score -= 0.1

        # Info messages
        # Settings match recipe
        all_checks_pass = True
        for issue in issues:
            if issue.severity in ["error", "warning"]:
                all_checks_pass = False
                break

        if all_checks_pass:
            issues.append(
                RecipeIssue(
                    severity="info",
                    code="SETTINGS_MATCH_RECIPE",
                    message="All settings match the recipe requirements",
                    expected="pass",
                    actual="pass",
                    recommendation="No changes needed",
                )
            )

        # Hardware profile recognized
        issues.append(
            RecipeIssue(
                severity="info",
                code="HARDWARE_PROFILE_RECOGNIZED",
                message=f"Hardware profile '{hardware.profile_id}' recognized",
                expected=hardware.profile_id,
                actual=hardware.profile_id,
                recommendation="Settings are appropriate for this hardware",
            )
        )

        # Pixel count is within safe limit
        if observed.width and observed.height:
            pixels = observed.width * observed.height
            max_pixels = min(recipe.max_pixels, hardware.max_pixels_sdxl)
            if pixels <= max_pixels:
                issues.append(
                    RecipeIssue(
                        severity="info",
                        code="PIXEL_COUNT_WITHIN_LIMIT",
                        message=f"Pixel count {pixels} is within safe limit {max_pixels}",
                        expected=f"<= {max_pixels}",
                        actual=pixels,
                        recommendation="Resolution is safe for this hardware",
                    )
                )

        # Determine verdict
        has_errors = any(issue.severity == "error" for issue in issues)
        has_warnings = any(issue.severity == "warning" for issue in issues)

        if has_errors:
            verdict = "fail"
        elif has_warnings:
            verdict = "warn"
        else:
            verdict = "pass"

        # Ensure score never below 0.0
        score = max(0.0, score)

        # Build recommended settings
        recommended_settings = {
            "checkpoint": recipe.checkpoint_allowlist[0] if recipe.checkpoint_allowlist else None,
            "sampler_name": recipe.sampler_allowlist[0] if recipe.sampler_allowlist else None,
            "scheduler": recipe.scheduler_allowlist[0] if recipe.scheduler_allowlist else None,
            "steps_min": recipe.steps_min,
            "steps_max": recipe.steps_max,
            "cfg_min": recipe.cfg_min,
            "cfg_max": recipe.cfg_max,
            "batch_size_max": recipe.batch_size_max,
            "recommended_batch_size": hardware.recommended_batch_size_sdxl,
            "max_pixels": min(recipe.max_pixels, hardware.max_pixels_sdxl),
            "required_negative_terms": recipe.required_negative_terms,
        }

        # Add recommended resolution for 9:16 if applicable
        if "9:16" in recipe.allowed_aspect_ratios:
            recommended_settings["recommended_9_16_resolution"] = recipe.allowed_aspect_ratios["9:16"]

        return RecipeValidationResult(
            verdict=verdict,
            recipe_id=recipe.recipe_id,
            task_type=task_type,
            hardware_profile_id=hardware.profile_id,
            score=score,
            issues=issues,
            observed_settings=observed.to_dict(),
            recommended_settings=recommended_settings,
        )
