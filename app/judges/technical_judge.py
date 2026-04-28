from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageStat, ImageFilter

from app.judges.base_types import JudgeInput, JudgeIssue, JudgeReport


class TechnicalJudge:
    def __init__(
        self,
        *,
        expected_min_sharpness: float = 4.0,
        max_overexposed_ratio: float = 0.35,
        max_underexposed_ratio: float = 0.35,
    ) -> None:
        self.expected_min_sharpness = expected_min_sharpness
        self.max_overexposed_ratio = max_overexposed_ratio
        self.max_underexposed_ratio = max_underexposed_ratio

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _load_image(path: str) -> Image.Image:
        image_path = Path(path)
        if not image_path.exists():
            raise FileNotFoundError(f"Primary image not found: {image_path}")
        return Image.open(image_path).convert("RGB")

    @staticmethod
    def _brightness_stats(image: Image.Image) -> tuple[float, float, float]:
        gray = image.convert("L")
        hist = gray.histogram()
        total = sum(hist) or 1
        mean = sum(i * count for i, count in enumerate(hist)) / total
        over = sum(hist[245:]) / total
        under = sum(hist[:10]) / total
        return mean, over, under

    @staticmethod
    def _sharpness_score(image: Image.Image) -> float:
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(edges)
        mean_edge = stat.mean[0]
        return min(mean_edge / 12.0, 1.0)

    @staticmethod
    def _noise_score(image: Image.Image) -> float:
        gray = image.convert("L")
        small = gray.resize((128, 128))
        stat = ImageStat.Stat(small)
        std = stat.stddev[0]
        # очень грубая эвристика: слишком низкий std = flat/muddy, слишком высокий = noisy
        if std < 18:
            return max(0.0, std / 18.0)
        if std > 70:
            return max(0.0, 1.0 - ((std - 70) / 50.0))
        return 1.0

    def evaluate(self, judge_input: JudgeInput) -> JudgeReport:
        issues: list[JudgeIssue] = []
        blocking_issues: list[JudgeIssue] = []
        strengths: list[str] = []
        repairs: list[str] = []

        try:
            image = self._load_image(judge_input.primary_image_path)
        except Exception as exc:
            return JudgeReport(
                judge_name="technical",
                score=0.0,
                verdict="reject",
                blocking_issues=[
                    JudgeIssue(
                        code="image_unreadable",
                        message=str(exc),
                        severity="critical",
                    )
                ],
                recommended_repairs=["regenerate_output", "check_artifact_fetch_pipeline"],
                subscores={
                    "output_integrity_score": 0.0,
                    "artifact_score": 0.0,
                    "anatomy_score": 0.0,
                    "exposure_score": 0.0,
                    "sharpness_score": 0.0,
                    "noise_score": 0.0,
                    "text_rendering_score": 0.5,
                },
            )

        width, height = image.size
        expected_w = judge_input.width
        expected_h = judge_input.height

        # Hard reject: Black frame detection
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        mean_brightness = stat.mean[0]
        
        if mean_brightness < 10:
            blocking_issues.append(
                JudgeIssue(
                    code="black_frame",
                    message=f"Black frame detected: mean brightness {mean_brightness:.2f}",
                    severity="critical",
                )
            )
            repairs.append("immediate_reject")
        
        if expected_w and expected_h and (width != expected_w or height != expected_h):
            issues.append(
                JudgeIssue(
                    code="size_mismatch",
                    message=f"Expected {expected_w}x{expected_h}, got {width}x{height}",
                    severity="high",
                )
            )
            repairs.append("fix_output_resolution")

        mean_brightness, over_ratio, under_ratio = self._brightness_stats(image)
        sharpness = self._sharpness_score(image)
        noise = self._noise_score(image)

        exposure_score = 1.0
        if over_ratio > self.max_overexposed_ratio:
            exposure_score -= 0.4
            issues.append(
                JudgeIssue(
                    code="overexposed",
                    message=f"High overexposed pixel ratio: {over_ratio:.2f}",
                    severity="high",
                )
            )
            repairs.append("reduce_highlights_or_cfg")
        if under_ratio > self.max_underexposed_ratio:
            exposure_score -= 0.4
            issues.append(
                JudgeIssue(
                    code="underexposed",
                    message=f"High underexposed pixel ratio: {under_ratio:.2f}",
                    severity="high",
                )
            )
            repairs.append("lift_shadows_or_adjust_prompt_lighting")

        sharpness_score = self._clamp_score(sharpness)
        # Repair 1: stricter gate for sharpness - if < 0.10, minimum retry
        if sharpness_score < 0.10:
            issues.append(
                JudgeIssue(
                    code="critically_blurry_image",
                    message=f"Critical sharpness failure: {sharpness_score:.2f}",
                    severity="high",
                )
            )
            repairs.append("increase_steps_or_change_seed")
        elif sharpness_score < 0.35:
            issues.append(
                JudgeIssue(
                    code="blurry_image",
                    message=f"Low sharpness score: {sharpness_score:.2f}",
                    severity="high",
                )
            )
            repairs.append("increase_steps_or_change_seed")

        noise_score = self._clamp_score(noise)
        if noise_score < 0.4:
            issues.append(
                JudgeIssue(
                    code="excessive_noise_or_flatness",
                    message=f"Noise score out of target range: {noise_score:.2f}",
                    severity="medium",
                )
            )
            repairs.append("adjust_sampler_cfg_or_prompt")

        # v0: честно не умеем уверенно детектить руки/лицо/текст
        anatomy_score = 0.65
        text_rendering_score = 0.60
        artifact_score = 0.75
        output_integrity_score = 1.0

        if width < 256 or height < 256:
            blocking_issues.append(
                JudgeIssue(
                    code="too_small_output",
                    message=f"Output too small: {width}x{height}",
                    severity="critical",
                )
            )
            repairs.append("increase_output_resolution")

        if mean_brightness < 5 or mean_brightness > 250:
            blocking_issues.append(
                JudgeIssue(
                    code="near_blank_image",
                    message=f"Image appears nearly blank, mean brightness={mean_brightness:.2f}",
                    severity="critical",
                )
            )
            repairs.append("regenerate_with_new_seed")

        if not issues:
            strengths.append("output_is_readable")
        if sharpness_score >= 0.55:
            strengths.append("acceptable_sharpness")
        if exposure_score >= 0.7:
            strengths.append("exposure_within_reasonable_range")

        subscores = {
            "artifact_score": self._clamp_score(artifact_score),
            "anatomy_score": self._clamp_score(anatomy_score),
            "exposure_score": self._clamp_score(exposure_score),
            "sharpness_score": sharpness_score,
            "noise_score": noise_score,
            "text_rendering_score": self._clamp_score(text_rendering_score),
            "output_integrity_score": self._clamp_score(output_integrity_score),
        }

        score = sum(subscores.values()) / len(subscores)

        # Repair 1: stricter verdict logic
        has_blur_issue = any(i.code in ["blurry_image", "critically_blurry_image"] for i in issues)
        has_noise_issue = any(i.code == "excessive_noise_or_flatness" for i in issues)

        if blocking_issues:
            verdict = "reject"
            score = min(score, 0.35)
        # Critical sharpness failure → minimum retry
        elif sharpness_score < 0.10:
            verdict = "retry"
            score = min(score, 0.40)
        # Noise score == 0.0 and has blur issue → not pass
        elif noise_score == 0.0 and has_blur_issue:
            verdict = "retry"
            score = min(score, 0.45)
        # High blur issue and score < 0.65 → retry, not pass
        elif has_blur_issue and score < 0.65:
            verdict = "retry"
        elif score < 0.55:
            verdict = "retry"
        else:
            verdict = "pass"

        return JudgeReport(
            judge_name="technical",
            score=round(score, 4),
            verdict=verdict,
            blocking_issues=blocking_issues,
            issues=issues,
            strengths=strengths,
            recommended_repairs=sorted(set(repairs)),
            subscores={k: round(v, 4) for k, v in subscores.items()},
            raw_notes={
                "measured_width": width,
                "measured_height": height,
                "mean_brightness": round(mean_brightness, 2),
                "over_ratio": round(over_ratio, 4),
                "under_ratio": round(under_ratio, 4),
            },
        )
