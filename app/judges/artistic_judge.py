from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.judges.base_types import JudgeInput, JudgeIssue, JudgeReport


class ArtisticJudge:
    def __init__(self, vision_client: Any) -> None:
        self.vision_client = vision_client

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return default

    def _build_prompt(self, judge_input: JudgeInput) -> str:
        task_text = judge_input.user_prompt.strip()
        final_prompt = (judge_input.final_positive_prompt or "").strip()
        preset_name = judge_input.preset_name or "unknown"

        return f"""
You are ArtisticJudge for image generation QA.

Evaluate the image like a demanding senior art director.
Focus on:
- composition strength
- cinematic quality
- color discipline
- expressiveness
- premium look
- image cohesion

Return STRICT JSON only.

Task:
{task_text}

Generation prompt:
{final_prompt}

Preset:
{preset_name}

Scoring:
0.0 = failed badly
1.0 = excellent

Required JSON schema:
{{
  "score": 0.0,
  "verdict": "pass|retry|reject",
  "blocking_issues": [{{"code": "string", "message": "string", "severity": "low|medium|high|critical"}}],
  "issues": [{{"code": "string", "message": "string", "severity": "low|medium|high|critical"}}],
  "strengths": ["string"],
  "recommended_repairs": ["string"],
  "subscores": {{
    "composition_score": 0.0,
    "cinematic_score": 0.0,
    "color_discipline_score": 0.0,
    "expressiveness_score": 0.0,
    "premium_look_score": 0.0,
    "image_cohesion_score": 0.0
  }}
}}
""".strip()

    def evaluate(self, judge_input: JudgeInput) -> JudgeReport:
        image_path = Path(judge_input.primary_image_path)
        if not image_path.exists():
            return JudgeReport(
                judge_name="artistic",
                score=None,  # None instead of 0.0 to indicate invalid
                verdict="retry",  # retry instead of reject for missing image
                blocking_issues=[
                    JudgeIssue(
                        code="missing_image_for_artistic_judge",
                        message=f"Image not found: {image_path}",
                        severity="critical",
                    )
                ],
                recommended_repairs=["regenerate_output"],
                subscores={},
                raw_notes={"_vision_status": "missing_image"},
            )

        try:
            raw = self.vision_client.judge_image(
                image_path=str(image_path),
                prompt=self._build_prompt(judge_input),
            )
        except RuntimeError as e:
            # Handle vision API failure
            return JudgeReport(
                judge_name="artistic",
                score=None,  # None instead of 0.0 to indicate invalid
                verdict="retry",
                blocking_issues=[
                    JudgeIssue(
                        code="vision_api_failure",
                        message=f"Vision API failed: {str(e)}",
                        severity="high",
                    )
                ],
                recommended_repairs=["retry_with_different_model"],
                subscores={},
                raw_notes={"_vision_status": "api_failure", "_error": str(e)},
            )

        if isinstance(raw, str):
            if not raw or raw.strip() == "":
                return JudgeReport(
                    judge_name="artistic",
                    score=None,  # None instead of 0.5 to indicate invalid
                    verdict="retry",
                    blocking_issues=[
                        JudgeIssue(
                            code="empty_vision_response",
                            message="Vision model returned empty response",
                            severity="medium",
                        )
                    ],
                    recommended_repairs=["retry_with_different_model"],
                    subscores={},
                    raw_notes={"_vision_status": "empty_response"},
                )
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                return JudgeReport(
                    judge_name="artistic",
                    score=None,  # None instead of 0.5 to indicate invalid
                    verdict="retry",
                    blocking_issues=[
                        JudgeIssue(
                            code="invalid_json_response",
                            message=f"Vision model returned invalid JSON: {str(exc)}",
                            severity="medium",
                        )
                    ],
                    recommended_repairs=["retry_with_different_model"],
                    subscores={},
                    raw_notes={"raw_response": raw, "_vision_status": "invalid_json", "_parse_error": str(exc)},
                )
        else:
            data = raw

        # Check if vision response is valid
        vision_status = data.get("_vision_status", "unknown")
        if vision_status in ["invalid_json", "api_failure", "unknown"]:
            # Return report with None score to indicate invalid vision response
            return JudgeReport(
                judge_name="artistic",
                score=None,  # None instead of 0.0 to indicate invalid
                verdict="retry",
                blocking_issues=[
                    JudgeIssue(
                        code="invalid_vision_response",
                        message=f"Vision response invalid: {vision_status}",
                        severity="high",
                    )
                ],
                recommended_repairs=["retry_with_different_model"],
                subscores={},
                raw_notes=data,
            )

        subscores = data.get("subscores", {})
        normalized_subscores = {
            "composition_score": self._safe_float(subscores.get("composition_score")),
            "cinematic_score": self._safe_float(subscores.get("cinematic_score")),
            "color_discipline_score": self._safe_float(subscores.get("color_discipline_score")),
            "expressiveness_score": self._safe_float(subscores.get("expressiveness_score")),
            "premium_look_score": self._safe_float(subscores.get("premium_look_score")),
            "image_cohesion_score": self._safe_float(subscores.get("image_cohesion_score")),
        }

        # Only use score if it's not None
        score = data.get("score")
        if score is None:
            score = None  # Keep as None to indicate invalid
        else:
            score = self._safe_float(score)

        return JudgeReport(
            judge_name="artistic",
            score=score,
            verdict=data.get("verdict", "retry"),
            blocking_issues=[
                JudgeIssue(**item) for item in data.get("blocking_issues", [])
            ],
            issues=[
                JudgeIssue(**item) for item in data.get("issues", [])
            ],
            strengths=[str(x) for x in data.get("strengths", [])],
            recommended_repairs=[str(x) for x in data.get("recommended_repairs", [])],
            subscores=normalized_subscores,
            raw_notes={"raw_response": data, "_vision_status": vision_status},
        )
