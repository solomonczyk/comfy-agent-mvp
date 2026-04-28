"""Tests for RecipeValidationSummaryBuilder (MK-RECIPE6)."""

import pytest

from app.recipes.models import RecipeIssue, RecipeValidationResult
from app.recipes.summary import RecipeValidationSummaryBuilder


class TestRecipeValidationSummaryBuilder:
    """Tests for RecipeValidationSummaryBuilder."""
    
    def test_pass_verdict_produces_title_recipe_ready_and_risk_level_low(self):
        """Test that pass verdict produces title 'Recipe ready' and risk_level 'low'."""
        result = RecipeValidationResult(
            verdict="pass",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=1.0,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["title"] == "Recipe ready"
        assert summary["risk_level"] == "low"
    
    def test_warn_score_08_produces_risk_level_low(self):
        """Test that warn score 0.8 produces risk_level 'low'."""
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.8,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["risk_level"] == "low"
    
    def test_warn_score_05_produces_risk_level_medium(self):
        """Test that warn score 0.5 produces risk_level 'medium'."""
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.5,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["risk_level"] == "medium"
    
    def test_warn_score_04_produces_risk_level_high(self):
        """Test that warn score 0.4 produces risk_level 'high'."""
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.4,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["risk_level"] == "high"
    
    def test_fail_verdict_produces_risk_level_critical(self):
        """Test that fail verdict produces risk_level 'critical'."""
        result = RecipeValidationResult(
            verdict="fail",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.75,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["risk_level"] == "critical"
        assert summary["title"] == "Recipe blocked"
    
    def test_top_reasons_max_length_is_5(self):
        """Test that top_reasons max length is 5."""
        issues = [
            RecipeIssue(severity="warning", code="CODE1", message="Issue 1"),
            RecipeIssue(severity="warning", code="CODE2", message="Issue 2"),
            RecipeIssue(severity="warning", code="CODE3", message="Issue 3"),
            RecipeIssue(severity="warning", code="CODE4", message="Issue 4"),
            RecipeIssue(severity="warning", code="CODE5", message="Issue 5"),
            RecipeIssue(severity="warning", code="CODE6", message="Issue 6"),
            RecipeIssue(severity="warning", code="CODE7", message="Issue 7"),
        ]
        
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.5,
            issues=issues,
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert len(summary["top_reasons"]) == 5
    
    def test_top_reasons_orders_errors_before_warnings_before_info(self):
        """Test that top_reasons orders errors before warnings before info."""
        issues = [
            RecipeIssue(severity="info", code="INFO1", message="Info issue"),
            RecipeIssue(severity="warning", code="WARN1", message="Warning issue"),
            RecipeIssue(severity="error", code="ERROR1", message="Error issue"),
            RecipeIssue(severity="warning", code="WARN2", message="Another warning"),
        ]
        
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.5,
            issues=issues,
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        # Error should come first
        assert summary["top_reasons"][0] == "Error issue"
        # Warnings should come before info
        assert "Warning issue" in summary["top_reasons"]
        assert "Another warning" in summary["top_reasons"]
        assert "Info issue" in summary["top_reasons"]
    
    def test_empty_issues_produces_fallback_reason(self):
        """Test that empty issues produces fallback reason."""
        result = RecipeValidationResult(
            verdict="pass",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=1.0,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["top_reasons"] == ["No blocking recipe issues found."]
    
    def test_warn_recommendation_mentions_missing_negative_terms_when_missing_negative_term_exists(self):
        """Test that warn recommendation mentions missing negative terms when MISSING_NEGATIVE_TERM exists."""
        issues = [
            RecipeIssue(
                severity="warning",
                code="MISSING_NEGATIVE_TERM",
                message="Missing required negative term: red skin",
                recommendation="Add red skin to negative prompt"
            ),
            RecipeIssue(
                severity="warning",
                code="MISSING_NEGATIVE_TERM",
                message="Missing required negative term: blue hoodie",
                recommendation="Add blue hoodie to negative prompt"
            ),
            RecipeIssue(
                severity="warning",
                code="MISSING_NEGATIVE_TERM",
                message="Missing required negative term: artifacts",
                recommendation="Add artifacts to negative prompt"
            ),
        ]
        
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.7,
            issues=issues,
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert "missing negative prompt terms" in summary["recommended_next_action"]
        assert "3" in summary["recommended_next_action"]
    
    def test_fail_recommendation_says_fix_blocking_errors(self):
        """Test that fail recommendation says fix blocking errors."""
        result = RecipeValidationResult(
            verdict="fail",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.75,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert "Fix blocking recipe errors" in summary["recommended_next_action"]
    
    def test_build_from_dict(self):
        """Test that build works with dict input (not just RecipeValidationResult)."""
        result_dict = {
            "verdict": "warn",
            "score": 0.7,
            "issues": [
                {
                    "severity": "warning",
                    "code": "MISSING_NEGATIVE_TERM",
                    "message": "Missing required negative term: red skin",
                }
            ],
        }
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result_dict)
        
        assert summary["title"] == "Recipe warning"
        # Score 0.7 is < 0.8, so risk level should be "medium"
        assert summary["risk_level"] == "medium"
        assert "missing negative prompt terms" in summary["recommended_next_action"]
    
    def test_pass_recommendation_says_proceed(self):
        """Test that pass recommendation says proceed."""
        result = RecipeValidationResult(
            verdict="pass",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=1.0,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["recommended_next_action"] == "Proceed with generate_frames."
    
    def test_warn_title_is_recipe_warning(self):
        """Test that warn title is 'Recipe warning'."""
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.7,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert summary["title"] == "Recipe warning"
    
    def test_operator_message_pass(self):
        """Test that operator message for pass is correct."""
        result = RecipeValidationResult(
            verdict="pass",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=1.0,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert "match the selected recipe" in summary["operator_message"]
    
    def test_operator_message_warn(self):
        """Test that operator message for warn is correct."""
        result = RecipeValidationResult(
            verdict="warn",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.7,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert "allowed, but settings may reduce quality" in summary["operator_message"]
    
    def test_operator_message_fail(self):
        """Test that operator message for fail is correct."""
        result = RecipeValidationResult(
            verdict="fail",
            recipe_id="sdxl_storyboard_keyframes_gtx1060",
            task_type="storyboard_keyframes",
            hardware_profile_id="gtx_1060_5gb",
            score=0.75,
            issues=[],
        )
        
        builder = RecipeValidationSummaryBuilder()
        summary = builder.build(result)
        
        assert "blocked because settings exceed safe limits" in summary["operator_message"]
