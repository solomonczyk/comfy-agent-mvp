from __future__ import annotations

from typing import Any


class MockVisionJudgeClient:
    """
    Mock vision client for Judge Layer v0.
    Returns deterministic mock responses for testing the judge pipeline.

    Repair 3: 3 scenarios:
    - "good": high-quality image → pass
    - "semantic_wrong": semantically incorrect image → retry_prompt
    - "technical_broken": technically broken image → retry_settings or reject
    """

    def __init__(self, mode: str = "good") -> None:
        """
        mode: "good", "semantic_wrong", "technical_broken"
        """
        self.mode = mode

    def judge_image(self, image_path: str, prompt: str) -> dict[str, Any]:
        """
        Mock implementation of vision_client.judge_image.
        Returns structured JSON matching the judge schema.
        Detects which judge is calling based on prompt content.
        """
        if "SemanticJudge" in prompt:
            return self._semantic_response()
        elif "ArtisticJudge" in prompt:
            return self._artistic_response()
        else:
            return self._good_response()

    def _semantic_response(self) -> dict[str, Any]:
        """
        Repair 2: SemanticJudge focuses on object, camera angle, mood, meaning.
        NO composition, cinematic, premium look in strengths.
        """
        if self.mode == "good":
            return {
                "score": 0.88,
                "verdict": "pass",
                "blocking_issues": [],
                "issues": [],
                "strengths": [
                    "subject_correctly_identified",
                    "camera_angle_matches_intent",
                    "mood_aligns_with_prompt",
                    "meaning_preserved",
                    "scene_elements_present",
                ],
                "recommended_repairs": [],
                "subscores": {
                    "prompt_alignment_score": 0.90,
                    "subject_presence_score": 0.92,
                    "camera_angle_score": 0.85,
                    "mood_match_score": 0.88,
                    "meaning_preservation_score": 0.87,
                },
            }
        elif self.mode == "semantic_wrong":
            return {
                "score": 0.38,
                "verdict": "reject",
                "blocking_issues": [
                    {
                        "code": "subject_mismatch",
                        "message": "Generated subject does not match user request",
                        "severity": "critical",
                    }
                ],
                "issues": [
                    {
                        "code": "wrong_camera_angle",
                        "message": "Camera angle contradicts prompt specification",
                        "severity": "high",
                    },
                    {
                        "code": "mood_mismatch",
                        "message": "Emotional tone does not match requested mood",
                        "severity": "medium",
                    },
                ],
                "strengths": ["some_elements_present"],
                "recommended_repairs": [
                    "clarify_subject_in_prompt",
                    "specify_camera_angle_explicitly",
                    "reinforce_mood_keywords",
                ],
                "subscores": {
                    "prompt_alignment_score": 0.35,
                    "subject_presence_score": 0.30,
                    "camera_angle_score": 0.40,
                    "mood_match_score": 0.42,
                    "meaning_preservation_score": 0.38,
                },
            }
        else:  # technical_broken - semantic might still be ok
            return {
                "score": 0.72,
                "verdict": "pass",
                "blocking_issues": [],
                "issues": [],
                "strengths": [
                    "subject_correctly_identified",
                    "camera_angle_acceptable",
                    "mood_reasonable",
                ],
                "recommended_repairs": [],
                "subscores": {
                    "prompt_alignment_score": 0.75,
                    "subject_presence_score": 0.78,
                    "camera_angle_score": 0.70,
                    "mood_match_score": 0.68,
                    "meaning_preservation_score": 0.72,
                },
            }

    def _artistic_response(self) -> dict[str, Any]:
        """
        Repair 2: ArtisticJudge focuses on composition, cinematic, premium look, color, cohesion.
        NO prompt_alignment, NO subject_presence in strengths.
        """
        if self.mode == "good":
            return {
                "score": 0.86,
                "verdict": "pass",
                "blocking_issues": [],
                "issues": [],
                "strengths": [
                    "strong_compositional_hierarchy",
                    "cinematic_lighting_quality",
                    "premium_material_rendering",
                    "disciplined_color_palette",
                    "image_cohesive_and_polished",
                    "expressive_and_dynamic",
                ],
                "recommended_repairs": [],
                "subscores": {
                    "composition_score": 0.88,
                    "cinematic_score": 0.85,
                    "color_discipline_score": 0.90,
                    "expressiveness_score": 0.82,
                    "premium_look_score": 0.87,
                    "image_cohesion_score": 0.86,
                },
            }
        elif self.mode == "semantic_wrong":
            # Even if semantic is wrong, artistic might still be technically good
            return {
                "score": 0.75,
                "verdict": "pass",
                "blocking_issues": [],
                "issues": [],
                "strengths": [
                    "good_composition",
                    "decent_lighting",
                    "acceptable_color_balance",
                ],
                "recommended_repairs": [],
                "subscores": {
                    "composition_score": 0.78,
                    "cinematic_score": 0.72,
                    "color_discipline_score": 0.76,
                    "expressiveness_score": 0.70,
                    "premium_look_score": 0.74,
                    "image_cohesion_score": 0.75,
                },
            }
        else:  # technical_broken
            return {
                "score": 0.35,
                "verdict": "reject",
                "blocking_issues": [
                    {
                        "code": "poor_composition",
                        "message": "Composition lacks focal point and hierarchy",
                        "severity": "critical",
                    }
                ],
                "issues": [
                    {
                        "code": "flat_lighting",
                        "message": "Lighting is flat and lacks depth",
                        "severity": "high",
                    },
                    {
                        "code": "muddy_colors",
                        "message": "Color palette lacks discipline and vibrancy",
                        "severity": "high",
                    },
                    {
                        "code": "low_premium_look",
                        "message": "Image lacks premium production quality",
                        "severity": "medium",
                    },
                ],
                "strengths": ["some_structure_present"],
                "recommended_repairs": [
                    "strengthen_compositional_hierarchy",
                    "add_cinematic_lighting",
                    "enforce_color_discipline",
                    "increase_subject_separation",
                    "enhance_premium_rendering",
                ],
                "subscores": {
                    "composition_score": 0.32,
                    "cinematic_score": 0.30,
                    "color_discipline_score": 0.35,
                    "expressiveness_score": 0.38,
                    "premium_look_score": 0.33,
                    "image_cohesion_score": 0.40,
                },
            }

    def _good_response(self) -> dict[str, Any]:
        """Legacy fallback for non-judge prompts."""
        return {
            "score": 0.85,
            "verdict": "pass",
            "blocking_issues": [],
            "issues": [],
            "strengths": ["acceptable_quality"],
            "recommended_repairs": [],
            "subscores": {},
        }
