from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.judges.base_types import JudgeInput, JudgeIssue, JudgeReport


class SemanticJudge:
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

        return f"""
You are SemanticJudge for image generation QA.

Your task is to evaluate whether the generated image matches the user's task.

Return STRICT JSON only.

Scoring rubric:
- prompt_alignment_score
- subject_presence_score
- camera_angle_score
- mood_match_score
- meaning_preservation_score

Rules:
- Use scores from 0.0 to 1.0
- verdict must be one of: pass, retry, reject
- blocking_issues only for major semantic failure
- issues for non-catastrophic mismatch
- recommended_repairs must be short actionable phrases

USER_TASK:
{task_text}

FINAL_GENERATION_PROMPT:
{final_prompt}

Required JSON schema:
{{
  "score": 0.0,
  "verdict": "pass|retry|reject",
  "blocking_issues": [{{"code": "string", "message": "string", "severity": "low|medium|high|critical"}}],
  "issues": [{{"code": "string", "message": "string", "severity": "low|medium|high|critical"}}],
  "strengths": ["string"],
  "recommended_repairs": ["string"],
  "subscores": {{
    "prompt_alignment_score": 0.0,
    "subject_presence_score": 0.0,
    "camera_angle_score": 0.0,
    "mood_match_score": 0.0,
    "meaning_preservation_score": 0.0
  }}
}}
""".strip()

    def evaluate(self, judge_input: JudgeInput) -> JudgeReport:
        image_path = Path(judge_input.primary_image_path)
        if not image_path.exists():
            return JudgeReport(
                judge_name="semantic",
                score=None,  # None instead of 0.0 to indicate invalid
                verdict="retry",  # retry instead of reject for missing image
                blocking_issues=[
                    JudgeIssue(
                        code="missing_image_for_semantic_judge",
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
                judge_name="semantic",
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
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"_vision_status": "invalid_json", "_raw_response": raw}
        else:
            data = raw

        # Check if vision response is valid
        vision_status = data.get("_vision_status", "unknown")
        if vision_status in ["invalid_json", "api_failure", "unknown"]:
            # Return report with None score to indicate invalid vision response
            return JudgeReport(
                judge_name="semantic",
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
            "prompt_alignment_score": self._safe_float(subscores.get("prompt_alignment_score")),
            "subject_presence_score": self._safe_float(subscores.get("subject_presence_score")),
            "camera_angle_score": self._safe_float(subscores.get("camera_angle_score")),
            "mood_match_score": self._safe_float(subscores.get("mood_match_score")),
            "meaning_preservation_score": self._safe_float(subscores.get("meaning_preservation_score")),
        }

        # Only use score if it's not None
        score = data.get("score")
        if score is None:
            score = None  # Keep as None to indicate invalid
        else:
            score = self._safe_float(score)

        return JudgeReport(
            judge_name="semantic",
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
