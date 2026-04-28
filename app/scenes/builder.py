"""MK-P5 — Scene builder.

Takes one SceneDef + its SceneKeyframePlan + list[ResolvedCharacter] and
produces a BuiltScene — a ready-to-submit ComfyUI workflow parameter package.

Merge rules:
- positive_prompt: join non-empty unique fragments with ", "
- negative_prompt: tokenise by comma, deduplicate tokens, rejoin
- lora_stack: deduplicate by lora_name, preserve first-seen order
- voice_ids: only non-None values, preserving order
"""
from __future__ import annotations

from app.brief.models import SceneDef
from app.characters.models import ResolvedCharacter
from app.keyframes.models import SceneKeyframePlan

from .models import BuiltScene

_DEFAULT_NEGATIVE = (
    "blurry, deformed, bad anatomy, extra limbs, "
    "watermark, signature, text, low quality"
)


class SceneBuilder:
    def __init__(self, default_negative: str = _DEFAULT_NEGATIVE) -> None:
        self.default_negative = default_negative

    def build(
        self,
        scene: SceneDef,
        plan: SceneKeyframePlan,
        characters: list[ResolvedCharacter],
        aspect_ratio: str = "4:3",
    ) -> BuiltScene:
        scene_chars = {n.lower() for n in scene.characters_in_scene}
        included = [c for c in characters if c.name.lower() in scene_chars]

        # Character-driven prompts
        prompt_parts = [c.positive_prompt for c in included]

        # MK-REAL2R-2: Use description if available, otherwise fall back to action
        # Description provides detailed visual description, action provides what happens
        if getattr(scene, "description", None):
            prompt_parts.append(scene.description)
        elif scene.action:
            prompt_parts.append(scene.action)
        
        # Scene context (location, time, mood) — always included
        if scene.location:
            prompt_parts.append(scene.location)
        if getattr(scene, "time", None):
            prompt_parts.append(scene.time)
        if getattr(scene, "mood", None):
            prompt_parts.append(scene.mood)

        positive_prompt = self._merge_positive(prompt_parts)
        # Ensure prompt is never empty
        if not positive_prompt:
            positive_prompt = getattr(scene, "description", None) or scene.action or "cinematic scene"

        negative_prompt = self._merge_negative(
            [c.negative_prompt for c in included] + [self.default_negative]
        )
        
        # MK-REAL2R-2: Add literal-frame blockers to prevent decorative frame generation
        frame_blockers = "picture frame, photo frame, decorative frame, empty frame, border, wall frame, ornate frame, frame object"
        negative_prompt = self._merge_negative([negative_prompt, frame_blockers])
        lora_stack = self._merge_loras(included)
        voice_ids = [c.voice_id for c in included if c.voice_id is not None]
        keyframe_hints = [kf.hint for kf in plan.keyframes]

        return BuiltScene(
            scene_id=scene.scene_id,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            lora_stack=lora_stack,
            voice_ids=voice_ids,
            total_frames=plan.total_frames,
            duration_sec=plan.duration_sec,
            fps=plan.fps,
            aspect_ratio=aspect_ratio,
            keyframe_hints=keyframe_hints,
            location=scene.location,
            dialogue=scene.dialogue,
        )

    # ── merge helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _merge_positive(prompts: list[str]) -> str:
        seen: list[str] = []
        for p in prompts:
            fragment = p.strip()
            if fragment and fragment not in seen:
                seen.append(fragment)
        return ", ".join(seen)

    @staticmethod
    def _merge_negative(negatives: list[str]) -> str:
        seen_tokens: list[str] = []
        seen_set: set[str] = set()
        for neg in negatives:
            for token in neg.split(","):
                t = token.strip()
                if t and t not in seen_set:
                    seen_set.add(t)
                    seen_tokens.append(t)
        return ", ".join(seen_tokens)

    @staticmethod
    def _merge_loras(characters: list[ResolvedCharacter]) -> list[dict]:
        seen_names: set[str] = set()
        stack: list[dict] = []
        for char in characters:
            for entry in char.to_comfy_lora_stack():
                name = entry["lora_name"]
                if name not in seen_names:
                    seen_names.add(name)
                    stack.append(entry)
        return stack
