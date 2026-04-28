"""Vision Defect Judge for detecting specific visual defects.

This judge uses vision models to detect:
- semantic_collapse
- multi_subject_unexpected
- eye_geometry_broken
- pupil_iris_artifact
- mouth_teeth_artifact
- plastic_skin
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.judges.base_types import JudgeInput, JudgeIssue, JudgeReport


class VisionDefectJudge:
    """Vision-based defect detection for critical visual artifacts."""
    
    # Defect codes that this judge can detect
    DETECTABLE_DEFECTS = {
        "semantic_collapse",
        "multi_subject_unexpected",
        "eye_geometry_broken",
        "pupil_iris_artifact",
        "mouth_teeth_artifact",
        "plastic_skin",
    }
    
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
You are VisionDefectJudge for image generation QA.

Your task is to detect specific visual defects in the generated image.

Focus ONLY on detecting these defects:
1. semantic_collapse - Image is a collage, nonsensical composition, or completely fails to represent coherent subject matter
2. multi_subject_unexpected - Multiple subjects/people when only one was expected, or wrong number of subjects
3. eye_geometry_broken - Severe eye deformation, missing eyes, extra eyes, or completely broken eye geometry
4. pupil_iris_artifact - Broken pupil, missing iris, deformed pupil/iris structure
5. mouth_teeth_artifact - Severe mouth deformation, missing mouth, broken teeth structure, or unnatural teeth
6. plastic_skin - Unnatural, waxy, or plastic-looking skin texture (especially on faces)

Return STRICT JSON only.

User Task:
{task_text}

Generation Prompt:
{final_prompt}

Required JSON schema:
{{
  "score": 0.0,
  "verdict": "pass|retry|reject",
  "blocking_issues": [
    {{
      "code": "semantic_collapse|multi_subject_unexpected|eye_geometry_broken|pupil_iris_artifact|mouth_teeth_artifact|plastic_skin",
      "message": "string",
      "severity": "critical"
    }}
  ],
  "issues": [],
  "strengths": [],
  "recommended_repairs": [],
  "subscores": {{
    "anatomy_integrity_score": 0.0,
    "semantic_coherence_score": 0.0
  }},
  "detected_defects": ["semantic_collapse", "plastic_skin"]
}}

Rules:
- Only use the exact defect codes listed above
- Set severity to "critical" for all detected defects
- If any defect is detected, verdict should be "reject" (for critical anatomy defects) or "retry" (for plastic skin)
- Score should reflect overall defect severity (0.0 = severe defects, 1.0 = no defects)
- detected_defects array should list all defects found
""".strip()
    
    def evaluate(self, judge_input: JudgeInput) -> JudgeReport:
        image_path = Path(judge_input.primary_image_path)
        if not image_path.exists():
            return JudgeReport(
                judge_name="vision_defect",
                score=0.0,
                verdict="reject",
                blocking_issues=[
                    JudgeIssue(
                        code="missing_image_for_vision_defect_judge",
                        message=f"Image not found: {image_path}",
                        severity="critical",
                    )
                ],
                recommended_repairs=["regenerate_output"],
            )
        
        raw = self.vision_client.judge_image(
            image_path=str(image_path),
            prompt=self._build_prompt(judge_input),
        )
        
        if isinstance(raw, str):
            if not raw or raw.strip() == "":
                return JudgeReport(
                    judge_name="vision_defect",
                    score=0.5,
                    verdict="retry",
                    blocking_issues=[
                        JudgeIssue(
                            code="empty_vision_response",
                            message="Vision model returned empty response",
                            severity="medium",
                        )
                    ],
                    recommended_repairs=["retry_with_different_model"],
                )
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                return JudgeReport(
                    judge_name="vision_defect",
                    score=0.5,
                    verdict="retry",
                    blocking_issues=[
                        JudgeIssue(
                            code="invalid_json_response",
                            message=f"Vision model returned invalid JSON: {str(exc)}",
                            severity="medium",
                        )
                    ],
                    recommended_repairs=["retry_with_different_model"],
                    raw_notes={"raw_response": raw},
                )
        else:
            data = raw
        
        # Extract subscores
        subscores = data.get("subscores", {})
        normalized_subscores = {
            "anatomy_integrity_score": self._safe_float(subscores.get("anatomy_integrity_score")),
            "semantic_coherence_score": self._safe_float(subscores.get("semantic_coherence_score")),
        }
        
        # Extract detected defects from raw response
        detected_defects = data.get("detected_defects", [])
        
        # Build blocking issues from detected defects
        blocking_issues = []
        for defect_code in detected_defects:
            if defect_code in self.DETECTABLE_DEFECTS:
                blocking_issues.append(
                    JudgeIssue(
                        code=defect_code,
                        message=f"Detected defect: {defect_code}",
                        severity="critical",
                    )
                )
        
        # Also add any blocking issues from the response
        for item in data.get("blocking_issues", []):
            if item.get("code") in self.DETECTABLE_DEFECTS:
                blocking_issues.append(JudgeIssue(**item))
        
        # Determine verdict based on defects
        verdict = data.get("verdict", "pass")
        
        # Override verdict based on detected defects if not set correctly
        critical_anatomy_defects = {
            "semantic_collapse",
            "eye_geometry_broken",
            "pupil_iris_artifact",
            "mouth_teeth_artifact",
        }
        
        has_critical_defect = any(d in critical_anatomy_defects for d in detected_defects)
        has_plastic_skin = "plastic_skin" in detected_defects
        
        if has_critical_defect:
            verdict = "reject"
        elif has_plastic_skin:
            verdict = "retry"
        
        return JudgeReport(
            judge_name="vision_defect",
            score=self._safe_float(data.get("score")),
            verdict=verdict,
            blocking_issues=blocking_issues,
            issues=[JudgeIssue(**item) for item in data.get("issues", [])],
            strengths=[str(x) for x in data.get("strengths", [])],
            recommended_repairs=[str(x) for x in data.get("recommended_repairs", [])],
            subscores=normalized_subscores,
            raw_notes={
                "raw_response": data,
                "detected_defects": detected_defects,
            },
        )
