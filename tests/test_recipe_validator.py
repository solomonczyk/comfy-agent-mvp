"""Tests for generation recipe validator."""
import pytest

from app.recipes.models import ObservedGenerationSettings
from app.recipes.registry import HardwareProfileRegistry, RecipeRegistry
from app.recipes.validator import GenerationRecipeValidator


class TestGenerationRecipeValidator:
    """Test GenerationRecipeValidator."""

    def test_valid_gtx_1060_storyboard_settings_verdict_pass(self):
        """Test that valid GTX 1060 storyboard settings pass."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "pass"
        assert result.score == 1.0

    def test_batch_size_12_verdict_fail(self):
        """Test that batch_size 12 results in fail verdict."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=12,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "fail"
        assert any(issue.code == "BATCH_SIZE_EXCEEDED" for issue in result.issues)
        assert result.score < 1.0

    def test_480x848_on_gtx_1060_verdict_fail_or_warning(self):
        """Test that 480x848 on GTX 1060 results in fail or warning with pixel-limit issue."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=848,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # 480x848 = 407,040 pixels, which exceeds 307,200 limit
        assert result.verdict in ["fail", "warn"]
        assert any(issue.code in ["PIXEL_LIMIT_EXCEEDED", "SUBOPTIMAL_9_16_RESOLUTION"] for issue in result.issues)

    def test_480x640_9_16_no_pixel_limit_issue(self):
        """Test that 480x640 9:16 has no pixel-limit issue."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # 480x640 = 307,200 pixels, which is exactly at the limit
        assert not any(issue.code == "PIXEL_LIMIT_EXCEEDED" for issue in result.issues)
        assert not any(issue.code == "SUBOPTIMAL_9_16_RESOLUTION" for issue in result.issues)

    def test_steps_6_warning_for_quality_risk(self):
        """Test that steps=6 results in warning for quality risk."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=6,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "warn"
        assert any(issue.code == "STEPS_BELOW_MIN" for issue in result.issues)
        assert result.score < 1.0

    def test_steps_40_warning_or_error(self):
        """Test that steps=40 results in warning or error."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=40,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict in ["warn", "fail"]
        assert any(issue.code in ["STEPS_ABOVE_MAX", "STEPS_OUT_OF_RANGE"] for issue in result.issues)

    def test_missing_checkpoint_fail(self):
        """Test that missing checkpoint results in fail."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint=None,
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "fail"
        assert any(issue.code == "MISSING_CHECKPOINT" for issue in result.issues)

    def test_missing_required_negative_term_warn(self):
        """Test that missing required negative term results in warning."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face",  # Missing some required terms
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "warn"
        assert any(issue.code == "MISSING_NEGATIVE_TERM" for issue in result.issues)

    def test_unsupported_sampler_fail(self):
        """Test that unsupported sampler results in fail."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="euler_a",  # Not in allowlist
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "fail"
        assert any(issue.code == "UNSUPPORTED_SAMPLER" for issue in result.issues)

    def test_cfg_too_low_warning_or_fail(self):
        """Test that CFG too low results in warning or fail."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=2.0,  # Below min of 5.0
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict in ["warn", "fail"]
        assert any(issue.code in ["CFG_BELOW_MIN", "CFG_OUT_OF_RANGE"] for issue in result.issues)

    def test_reference_recipe_validates_denoise_range(self):
        """Test that reference recipe validates denoise range."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_reference_locked_character_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        # Test denoise within range
        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            denoise=0.6,  # Within 0.45-0.75 range
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "reference_locked_character")

        assert not any(issue.code == "DENOISE_OUT_OF_RANGE" for issue in result.issues)

        # Test denoise outside range
        observed.denoise = 0.9  # Above 0.75
        result = validator.validate(observed, recipe, hardware, "reference_locked_character")

        assert any(issue.code == "DENOISE_OUT_OF_RANGE" for issue in result.issues)

    def test_phone_overlay_recipe_warns_if_text_missing_from_negative_prompt(self):
        """Test that phone overlay recipe warns if 'text' is missing from negative prompt."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_phone_screen_overlay_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",  # Missing 'text'
        )

        result = validator.validate(observed, recipe, hardware, "phone_screen_overlay")

        assert result.verdict == "warn"
        assert any(
            issue.code == "MISSING_NEGATIVE_TERM" and "text" in issue.message
            for issue in result.issues
        )

    def test_score_decreases_with_warnings_errors(self):
        """Test that score decreases with warnings and errors."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        # Perfect score
        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")
        assert result.score == 1.0

        # With warning
        observed.steps = 6
        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")
        assert result.score < 1.0

        # With error
        observed.batch_size = 12
        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")
        assert result.score < 1.0

    def test_output_is_json_serializable(self):
        """Test that output is JSON-serializable."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # Should not raise an exception
        import json

        json_str = json.dumps(result.to_dict())
        assert json_str is not None

    def test_warning_score_subtracts_point_one_per_warning(self):
        """Test that score subtracts 0.1 for each warning."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        # Create exactly two warnings
        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=15,  # Below min (1 warning)
            cfg=4.0,  # Below min (1 warning)
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # Count warnings
        warnings = [issue for issue in result.issues if issue.severity == "warning"]
        assert len(warnings) == 2
        assert result.score == 0.8  # 1.0 - 2 * 0.1

    def test_each_missing_negative_term_reported(self):
        """Test that each missing required negative term is reported separately."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        # Missing 4 required negative terms
        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=20,
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face",  # Missing: red skin, orange skin, blue hoodie, artifacts
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # Count MISSING_NEGATIVE_TERM issues
        missing_term_issues = [
            issue for issue in result.issues
            if issue.code == "MISSING_NEGATIVE_TERM"
        ]
        assert len(missing_term_issues) == 4

        # Verify each missing term is reported
        missing_terms = [issue.message for issue in missing_term_issues]
        assert any("red skin" in msg for msg in missing_terms)
        assert any("orange skin" in msg for msg in missing_terms)
        assert any("blue hoodie" in msg for msg in missing_terms)
        assert any("artifacts" in msg for msg in missing_terms)

    def test_score_matches_visible_issue_count(self):
        """Test that score matches visible warning/error issue counts."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        # Create mix of warnings and errors
        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=15,  # Below min (1 warning)
            cfg=7.0,
            width=480,
            height=640,
            batch_size=5,  # Exceeds max (1 error)
            negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        # Count warnings and errors
        warnings = [issue for issue in result.issues if issue.severity == "warning"]
        errors = [issue for issue in result.issues if issue.severity == "error"]

        expected_score = 1.0 - len(warnings) * 0.1 - len(errors) * 0.25
        expected_score = max(0.0, expected_score)

        assert result.score == expected_score

    def test_warn_sample_steps_6_and_missing_terms_score_consistent(self):
        """Test that warn sample with steps=6 and missing terms has consistent score."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed = ObservedGenerationSettings(
            checkpoint="realvisxlV50_v50Bakedvae.safetensors",
            sampler_name="dpmpp_2m",
            scheduler="karras",
            steps=6,  # Below min (1 warning)
            cfg=7.0,
            width=480,
            height=640,
            batch_size=2,
            negative_prompt="bad anatomy, distorted face",  # Missing: red skin, orange skin, blue hoodie, artifacts (4 warnings)
        )

        result = validator.validate(observed, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "warn"

        # Count MISSING_NEGATIVE_TERM issues
        missing_term_issues = [
            issue for issue in result.issues
            if issue.code == "MISSING_NEGATIVE_TERM"
        ]
        assert len(missing_term_issues) == 4

        # Verify each missing term is reported
        missing_terms = [issue.message for issue in missing_term_issues]
        assert any("red skin" in msg for msg in missing_terms)
        assert any("orange skin" in msg for msg in missing_terms)
        assert any("blue hoodie" in msg for msg in missing_terms)
        assert any("artifacts" in msg for msg in missing_terms)

        # Total warnings should be 5 (1 for steps + 4 for missing terms)
        warnings = [issue for issue in result.issues if issue.severity == "warning"]
        assert len(warnings) == 5

        # Score should be 0.5 (1.0 - 5 * 0.1)
        assert result.score == pytest.approx(0.5)

    def test_validates_from_dict(self):
        """Test that validator can accept observed settings as dict."""
        recipe_registry = RecipeRegistry()
        hardware_registry = HardwareProfileRegistry()
        validator = GenerationRecipeValidator()

        recipe = recipe_registry.get("sdxl_storyboard_keyframes_gtx1060")
        hardware = hardware_registry.get("gtx_1060_5gb")

        observed_dict = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }

        result = validator.validate(observed_dict, recipe, hardware, "storyboard_keyframes")

        assert result.verdict == "pass"
