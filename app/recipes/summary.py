"""Recipe validation summary builder for human-readable operator diagnosis.

This module provides a compact, operator-friendly summary of recipe validation
results without changing gating behavior or mutating workflows.
"""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from app.recipes.models import RecipeValidationResult


class RecipeValidationSummaryBuilder:
    """Build human-readable operator summaries from recipe validation results.
    
    This builder creates a compact summary that operators can quickly understand
    without parsing the full JSON issues list. It is read-only and does not
    mutate workflows, run ComfyUI, or auto-fix settings.
    """
    
    def build(self, validation_result: Union[dict, "RecipeValidationResult"]) -> dict:
        """Build a human-readable summary from a validation result.
        
        Args:
            validation_result: Recipe validation result as dict or RecipeValidationResult
            
        Returns:
            Dictionary with keys: title, risk_level, operator_message, top_reasons, recommended_next_action
        """
        # Normalize to dict
        if hasattr(validation_result, "verdict"):
            # RecipeValidationResult object
            result_dict = {
                "verdict": validation_result.verdict,
                "score": validation_result.score,
                "issues": [issue.to_dict() for issue in validation_result.issues],
            }
        else:
            # Already a dict
            result_dict = validation_result
        
        verdict = result_dict.get("verdict", "pass")
        score = result_dict.get("score", 1.0)
        issues = result_dict.get("issues", [])
        
        # Determine title
        title = self._get_title(verdict)
        
        # Determine risk level
        risk_level = self._get_risk_level(verdict, score)
        
        # Build operator message
        operator_message = self._get_operator_message(verdict, risk_level)
        
        # Build top reasons
        top_reasons = self._get_top_reasons(issues)
        
        # Build recommended next action
        recommended_next_action = self._get_recommended_next_action(
            verdict, risk_level, issues
        )
        
        return {
            "title": title,
            "risk_level": risk_level,
            "operator_message": operator_message,
            "top_reasons": top_reasons,
            "recommended_next_action": recommended_next_action,
        }
    
    def _get_title(self, verdict: str) -> str:
        """Get title based on verdict."""
        if verdict == "pass":
            return "Recipe ready"
        elif verdict == "warn":
            return "Recipe warning"
        elif verdict == "fail":
            return "Recipe blocked"
        else:
            return "Recipe unknown"
    
    def _get_risk_level(self, verdict: str, score: float) -> str:
        """Get risk level based on verdict and score."""
        if verdict == "pass":
            return "low"
        elif verdict == "warn":
            if score >= 0.8:
                return "low"
            elif score >= 0.5:
                return "medium"
            else:
                return "high"
        elif verdict == "fail":
            return "critical"
        else:
            return "low"
    
    def _get_operator_message(self, verdict: str, risk_level: str) -> str:
        """Get operator message based on verdict and risk level."""
        if verdict == "pass":
            return "Generation settings match the selected recipe and GTX 1060 5GB constraints."
        elif verdict == "warn":
            return "Generation is allowed, but settings may reduce quality or visual consistency."
        elif verdict == "fail":
            return "Generation is blocked because settings exceed safe limits for the selected recipe/hardware."
        else:
            return "Unable to determine recipe validation status."
    
    def _get_top_reasons(self, issues: list) -> list[str]:
        """Get top 5 most important issue messages, ordered by severity."""
        if not issues:
            return ["No blocking recipe issues found."]
        
        # Order by severity: error > warning > info
        severity_order = {"error": 0, "warning": 1, "info": 2}
        sorted_issues = sorted(
            issues,
            key=lambda i: severity_order.get(i.get("severity", "info"), 2)
        )
        
        # Extract messages
        messages = [issue.get("message", "") for issue in sorted_issues]
        
        # Return top 5
        return messages[:5]
    
    def _get_recommended_next_action(self, verdict: str, risk_level: str, issues: list) -> str:
        """Get recommended next action based on verdict, risk level, and issues."""
        if verdict == "pass":
            return "Proceed with generate_frames."
        elif verdict == "fail":
            return "Fix blocking recipe errors before running generate_frames."
        elif verdict == "warn":
            # Check for missing negative terms
            missing_term_issues = [
                i for i in issues
                if i.get("code") == "MISSING_NEGATIVE_TERM"
            ]
            
            if missing_term_issues:
                term_count = len(missing_term_issues)
                if term_count >= 3:
                    return f"Add {term_count} missing negative prompt terms and consider increasing steps before generation."
                else:
                    return f"Add missing negative prompt terms and consider increasing steps before generation."
            else:
                # Build from issue recommendations
                recommendations = [
                    i.get("recommendation", "")
                    for i in issues
                    if i.get("recommendation")
                ]
                if recommendations:
                    return recommendations[0]
                else:
                    return "Review recipe issues and consider adjustments before generation."
        else:
            return "Review recipe validation status before proceeding."
