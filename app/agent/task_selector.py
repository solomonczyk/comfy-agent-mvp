"""Task selector for determining task type from user prompts."""

import re
from dataclasses import dataclass
from typing import Any

from app.services.openrouter_client import OpenRouterClient
from app.workflows.workflow_types import TaskType


@dataclass
class TaskSelectionResult:
    """Result of task selection."""
    task_type: TaskType
    confidence: float
    reason: str
    routing_source: str  # "rules" | "llm"
    required_inputs: list[str] = None
    missing_inputs: list[str] = None
    ambiguity_level: str = "low"  # low | medium | high
    safe_fallback_used: bool = False

    def __post_init__(self):
        if self.required_inputs is None:
            self.required_inputs = []
        if self.missing_inputs is None:
            self.missing_inputs = []


class TaskSelector:
    """Selector for determining task type from user prompts."""

    def __init__(self, llm_client: OpenRouterClient | None = None) -> None:
        """Initialize task selector with optional LLM client for fallback."""
        self.llm_client = llm_client

    def select(self, user_prompt: str, assets: dict[str, Any] | None = None) -> TaskSelectionResult:
        """Select task type from user prompt using rule-based + LLM fallback.

        Args:
            user_prompt: User's prompt text
            assets: Dictionary of available assets (e.g., {"input_image": "...", "mask_image": "..."})

        Returns:
            TaskSelectionResult with task type, confidence, and routing reason
        """
        prompt_lower = user_prompt.lower()
        if assets is None:
            assets = {}

        # Rule-based fast path with asset awareness
        rule_result = self._select_by_rules(prompt_lower, user_prompt, assets)
        
        # High confidence with all required assets: direct route
        if rule_result.confidence >= 0.85 and not rule_result.missing_inputs:
            return rule_result

        # Strong intent but missing assets: allow routing with note
        if rule_result.confidence >= 0.50 and rule_result.missing_inputs:
            return rule_result

        # Mid-confidence: check if we should use LLM fallback or controlled failure
        if 0.65 <= rule_result.confidence < 0.85:
            # Allow routing but with reason explaining confidence
            return rule_result

        # Low-confidence: LLM fallback or controlled failure
        if 0.45 <= rule_result.confidence < 0.65:
            if self.llm_client and rule_result.ambiguity_level in ["medium", "high"]:
                return self._select_by_llm(user_prompt, assets)
            # Otherwise safe fallback or controlled failure
            return self._apply_safe_fallback(rule_result, assets)

        # Very low confidence: unknown / controlled failure
        if rule_result.confidence < 0.45:
            return self._apply_controlled_failure(rule_result, assets)

        return rule_result

    def _select_by_rules(self, prompt_lower: str, original_prompt: str, assets: dict[str, Any]) -> TaskSelectionResult:
        """Select task type using priority-based rule engine with asset awareness."""
        # Priority order: upscale > inpaint_face > img2img > txt2img > unknown
        candidates = []

        # Score each task type with priority-based rules
        candidates.append(self._score_upscale(prompt_lower, assets))
        candidates.append(self._score_inpaint_face(prompt_lower, assets))
        candidates.append(self._score_img2img(prompt_lower, assets))
        candidates.append(self._score_txt2img(prompt_lower, assets))

        # Filter out zero-confidence candidates
        candidates = [c for c in candidates if c["confidence"] > 0]

        if not candidates:
            return self._create_unknown_result("No matching task type rules", assets)

        # Sort by confidence (highest first)
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        # Get best candidate
        best = candidates[0]

        # Apply ambiguity handling
        ambiguity_level = self._detect_ambiguity(prompt_lower, assets)
        best["ambiguity_level"] = ambiguity_level

        # Apply ambiguity penalties
        if ambiguity_level == "high":
            best["confidence"] -= 0.25
        elif ambiguity_level == "medium":
            best["confidence"] -= 0.10

        # Ensure confidence doesn't go below 0
        best["confidence"] = max(0.0, best["confidence"])

        # Apply ambiguity policy for vague prompts
        result = self._apply_ambiguity_policy(prompt_lower, assets, best, ambiguity_level)

        return result

    async def _select_by_llm(self, user_prompt: str, assets: dict[str, Any]) -> TaskSelectionResult:
        """Select task type using LLM classification."""
        if not self.llm_client:
            return TaskSelectionResult(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                reason="LLM client not available",
                routing_source="llm",
            )

        task_types_list = [
            "portrait_txt2img",
            "cinematic_txt2img",
            "product_txt2img",
            "fashion_txt2img",
            "img2img",
            "inpaint_face",
            "upscale",
            "unknown",
        ]

        system_prompt = f"""You are a task classifier for an image generation system.
Classify the user's request into one of these task types:
{', '.join(task_types_list)}

Respond with ONLY the task type name, nothing else."""

        try:
            response = await self.llm_client.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            )

            task_type_str = response.strip().lower()
            task_type = TaskType.UNKNOWN

            for tt in TaskType:
                if tt.value == task_type_str:
                    task_type = tt
                    break

            return TaskSelectionResult(
                task_type=task_type,
                confidence=0.6,
                reason=f"LLM classified as {task_type_str}",
                routing_source="llm",
                required_inputs=self._get_required_inputs_for_task(task_type),
                missing_inputs=self._get_missing_inputs(task_type, assets),
            )
        except Exception as e:
            return TaskSelectionResult(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                reason=f"LLM classification failed: {str(e)}",
                routing_source="llm",
            )

    def _score_upscale(self, prompt_lower: str, assets: dict[str, Any]) -> dict[str, Any]:
        """Score upscale task type."""
        confidence = 0.0
        reason = ""
        required_inputs = ["input_image"]
        missing_inputs = []

        # Strong intent phrases
        strong_phrases = ["upscale", "enlarge", "increase resolution", "make bigger", "scale up"]
        for phrase in strong_phrases:
            if phrase in prompt_lower:
                confidence += 0.55
                reason = f"Detected upscale intent with phrase '{phrase}'"
                break

        # Supporting keywords
        supporting = ["high resolution", "hi-res", "4k", "8k", "high detail", "sharpen", "enhance resolution"]
        for kw in supporting:
            if kw in prompt_lower:
                confidence += 0.20
                reason += f" and supporting keyword '{kw}'"
                break

        # Specific wording bonus
        if "this image" in prompt_lower or "this" in prompt_lower:
            confidence += 0.10
            reason += " with specific image reference"

        # Asset check
        has_image = bool(assets.get("input_image") or assets.get("image"))
        if has_image:
            confidence += 0.20
        else:
            confidence -= 0.15  # Reduced penalty to allow routing with strong intent
            missing_inputs.append("input_image")
            reason += " but input_image missing"

        return {
            "task_type": TaskType.UPSCALE,
            "confidence": max(0.0, confidence),
            "reason": reason,
            "required_inputs": required_inputs,
            "missing_inputs": missing_inputs,
        }

    def _score_inpaint_face(self, prompt_lower: str, assets: dict[str, Any]) -> dict[str, Any]:
        """Score inpaint_face task type."""
        confidence = 0.0
        reason = ""
        required_inputs = ["input_image"]
        missing_inputs = []

        # Strong intent phrases
        strong_phrases = ["fix face", "repair face", "fix eye", "repair eye", "fix artifact", "repair artifact"]
        for phrase in strong_phrases:
            if phrase in prompt_lower:
                confidence += 0.75
                reason = f"Detected face-repair intent with phrase '{phrase}'"
                break

        # Supporting keywords
        supporting = ["inpaint", "face fix", "repair portrait", "fix skin", "repair skin"]
        for kw in supporting:
            if kw in prompt_lower:
                confidence += 0.20
                reason += f" and supporting keyword '{kw}'"
                break

        # Specific wording bonus
        if "face" in prompt_lower or "eyes" in prompt_lower or "skin" in prompt_lower:
            confidence += 0.10
            reason += " with specific face reference"

        # Asset check
        has_image = bool(assets.get("input_image") or assets.get("image"))
        if has_image:
            confidence += 0.20
        else:
            confidence -= 0.15  # Reduced penalty to allow routing with strong intent
            missing_inputs.append("input_image")
            reason += " but input_image missing"

        # Mask check (optional for some workflows)
        has_mask = bool(assets.get("mask_image") or assets.get("mask"))
        # Note: mask is optional for some inpaint workflows, so we don't penalize heavily

        return {
            "task_type": TaskType.INPAINT_FACE,
            "confidence": max(0.0, confidence),
            "reason": reason,
            "required_inputs": required_inputs,
            "missing_inputs": missing_inputs,
        }

    def _score_img2img(self, prompt_lower: str, assets: dict[str, Any]) -> dict[str, Any]:
        """Score img2img task type."""
        confidence = 0.0
        reason = ""
        required_inputs = ["input_image"]
        missing_inputs = []

        # Strong intent phrases
        strong_phrases = ["stylize", "transform", "restyle", "modify image", "change style"]
        for phrase in strong_phrases:
            if phrase in prompt_lower:
                confidence += 0.55
                reason = f"Detected image-edit intent with phrase '{phrase}'"
                break

        # Supporting keywords
        supporting = ["make cinematic", "make dramatic", "change look", "image to image", "img2img"]
        for kw in supporting:
            if kw in prompt_lower:
                confidence += 0.20
                reason += f" and supporting keyword '{kw}'"
                break

        # Specific wording bonus
        if "this image" in prompt_lower or "this" in prompt_lower:
            confidence += 0.10
            reason += " with specific image reference"

        # Asset check
        has_image = bool(assets.get("input_image") or assets.get("image"))
        if has_image:
            confidence += 0.20
        else:
            confidence -= 0.15  # Reduced penalty to allow routing with strong intent
            missing_inputs.append("input_image")
            reason += " but input_image missing"

        return {
            "task_type": TaskType.IMG2IMG,
            "confidence": max(0.0, confidence),
            "reason": reason,
            "required_inputs": required_inputs,
            "missing_inputs": missing_inputs,
        }

    def _score_txt2img(self, prompt_lower: str, assets: dict[str, Any]) -> dict[str, Any]:
        """Score txt2img task types (portrait, cinematic, product, fashion)."""
        # Check for specific txt2img subtypes
        # Note: exclude "face" from portrait keywords to avoid conflict with inpaint_face
        portrait_keywords = ["portrait", "person", "woman", "man", "character", "headshot", "selfie"]
        cinematic_keywords = ["cinematic", "movie", "film", "scene", "wide shot", "establishing shot", "epic", "dramatic", "moody", "atmospheric"]
        product_keywords = ["product", "bottle", "packshot", "commercial", "advertisement", "studio product", "isolated", "white background", "perfume"]
        fashion_keywords = ["fashion", "editorial", "runway", "model", "couture", "high fashion", "style", "outfit", "clothing"]

        confidence = 0.0
        reason = ""
        task_type = TaskType.UNKNOWN

        # Score each subtype
        scores = {
            TaskType.PORTRAIT_TXT2IMG: sum(1 for kw in portrait_keywords if kw in prompt_lower),
            TaskType.CINEMATIC_TXT2IMG: sum(1 for kw in cinematic_keywords if kw in prompt_lower),
            TaskType.PRODUCT_TXT2IMG: sum(1 for kw in product_keywords if kw in prompt_lower),
            TaskType.FASHION_TXT2IMG: sum(1 for kw in fashion_keywords if kw in prompt_lower),
        }

        # Get best scoring subtype
        best_subtype = max(scores, key=scores.get)
        best_score = scores[best_subtype]

        if best_score > 0:
            task_type = best_subtype
            confidence = 0.45 + (best_score * 0.15)
            matched_keywords = [kw for kw_list in [portrait_keywords, cinematic_keywords, product_keywords, fashion_keywords]
                              for kw in kw_list if kw in prompt_lower]
            reason = f"Detected txt2img intent ({task_type.value}) with keywords: {', '.join(matched_keywords[:3])}"

        # No image is expected for txt2img, so no asset penalty
        return {
            "task_type": task_type,
            "confidence": min(0.85, confidence),
            "reason": reason,
            "required_inputs": [],
            "missing_inputs": [],
        }

    def _detect_ambiguity(self, prompt_lower: str, assets: dict[str, Any]) -> str:
        """Detect ambiguity level in prompt."""
        vague_phrases = ["make this better", "improve this", "fix this", "make it nicer", "enhance this", "improve image", "make this more"]

        for phrase in vague_phrases:
            if phrase in prompt_lower:
                has_image = bool(assets.get("input_image") or assets.get("image"))
                if not has_image:
                    return "high"  # vague + no image = high ambiguity
                else:
                    # Check if there are strong signals that override vagueness
                    # But exclude cinematic/dramatic when part of "make this more" transformation
                    has_strong_signal = any(p in prompt_lower for p in ["upscale", "enlarge", "fix face", "repair face"])
                    if has_strong_signal:
                        return "low"  # Strong signal overrides vagueness
                    return "medium"  # vague + image = medium ambiguity

        # Check if prompt is very short or generic (but only if it has no keywords)
        if len(prompt_lower.split()) < 3:
            has_image = bool(assets.get("input_image") or assets.get("image"))
            if not has_image:
                # Check if it has any valid keywords
                has_keywords = any(kw in prompt_lower for kw in ["portrait", "cinematic", "product", "fashion", "upscale", "stylize", "fix face", "repair face"])
                if not has_keywords:
                    return "high"

        return "low"

    def _apply_ambiguity_policy(self, prompt_lower: str, assets: dict[str, Any], candidate: dict[str, Any], ambiguity_level: str) -> TaskSelectionResult:
        """Apply ambiguity handling policy."""
        has_image = bool(assets.get("input_image") or assets.get("image"))

        # Case A: vague prompt + no image -> unknown
        if ambiguity_level == "high":
            # Check if it's a vague phrase specifically
            vague_phrases = ["make this better", "improve this", "fix this", "make it nicer", "enhance this", "make this more", "improve image"]
            is_vague_phrase = any(phrase in prompt_lower for phrase in vague_phrases)
            
            if is_vague_phrase:
                return TaskSelectionResult(
                    task_type=TaskType.UNKNOWN,
                    confidence=0.3,
                    reason="Vague image-edit request without input image",
                    routing_source="rules",
                    required_inputs=[],
                    missing_inputs=[],
                    ambiguity_level=ambiguity_level,
                )
            else:
                # Generic high ambiguity (e.g., very short prompt)
                return TaskSelectionResult(
                    task_type=TaskType.UNKNOWN,
                    confidence=0.0,
                    reason="No matching task type rules",
                    routing_source="rules",
                    required_inputs=[],
                    missing_inputs=[],
                    ambiguity_level=ambiguity_level,
                )

        # Case B: vague prompt + image present -> safe fallback to img2img
        if ambiguity_level == "medium" and has_image:
            # Check if there are strong signals for upscale or inpaint_face
            has_upscale_signal = any(p in prompt_lower for p in ["upscale", "enlarge", "increase resolution"])
            has_face_signal = any(p in prompt_lower for p in ["fix face", "repair face", "fix eye", "repair eye"])

            if has_upscale_signal:
                candidate["task_type"] = TaskType.UPSCALE
                candidate["reason"] = "Vague prompt with explicit upscale wording and input_image present"
            elif has_face_signal:
                candidate["task_type"] = TaskType.INPAINT_FACE
                candidate["reason"] = "Vague prompt with explicit face-repair wording and input_image present"
            else:
                # Safe fallback to img2img (even if txt2img keywords like cinematic are present)
                candidate["task_type"] = TaskType.IMG2IMG
                candidate["confidence"] = 0.55
                candidate["reason"] = "Vague improve-image wording with input_image present; safe fallback to img2img"
                candidate["required_inputs"] = ["input_image"]
                candidate["missing_inputs"] = []
                candidate["safe_fallback_used"] = True

        return TaskSelectionResult(
            task_type=candidate["task_type"],
            confidence=candidate["confidence"],
            reason=candidate["reason"],
            routing_source="rules",
            required_inputs=candidate["required_inputs"],
            missing_inputs=candidate["missing_inputs"],
            ambiguity_level=ambiguity_level,
            safe_fallback_used=candidate.get("safe_fallback_used", False),
        )

    def _create_unknown_result(self, reason: str, assets: dict[str, Any]) -> TaskSelectionResult:
        """Create unknown task result."""
        return TaskSelectionResult(
            task_type=TaskType.UNKNOWN,
            confidence=0.0,
            reason=reason,
            routing_source="rules",
            required_inputs=[],
            missing_inputs=[],
            ambiguity_level="low",
        )

    def _apply_safe_fallback(self, rule_result: TaskSelectionResult, assets: dict[str, Any]) -> TaskSelectionResult:
        """Apply safe fallback for mid-confidence cases."""
        # If image-based task but image missing, controlled failure
        if rule_result.task_type in [TaskType.UPSCALE, TaskType.IMG2IMG, TaskType.INPAINT_FACE]:
            has_image = bool(assets.get("input_image") or assets.get("image"))
            if not has_image:
                return TaskSelectionResult(
                    task_type=TaskType.UNKNOWN,
                    confidence=0.35,
                    reason=f"Image-based request detected but input_image missing; cannot route to {rule_result.task_type.value}",
                    routing_source="rules",
                    required_inputs=rule_result.required_inputs,
                    missing_inputs=rule_result.missing_inputs or ["input_image"],
                    ambiguity_level="medium",
                )

        # Otherwise, return original result with note
        rule_result.reason += " (mid-confidence routing)"
        return rule_result

    def _apply_controlled_failure(self, rule_result: TaskSelectionResult, assets: dict[str, Any]) -> TaskSelectionResult:
        """Apply controlled failure for very low confidence cases."""
        return TaskSelectionResult(
            task_type=TaskType.UNKNOWN,
            confidence=0.0,
            reason=f"Very low confidence routing ({rule_result.confidence:.2f}); controlled failure to prevent incorrect route",
            routing_source="rules",
            required_inputs=[],
            missing_inputs=[],
            ambiguity_level="high",
        )

    def _get_required_inputs_for_task(self, task_type: TaskType) -> list[str]:
        """Get required inputs for a task type."""
        if task_type in [TaskType.UPSCALE, TaskType.IMG2IMG, TaskType.INPAINT_FACE]:
            return ["input_image"]
        return []

    def _get_missing_inputs(self, task_type: TaskType, assets: dict[str, Any]) -> list[str]:
        """Get missing inputs for a task type."""
        required = self._get_required_inputs_for_task(task_type)
        missing = []
        for req in required:
            if req == "input_image":
                if not (assets.get("input_image") or assets.get("image")):
                    missing.append(req)
        return missing
