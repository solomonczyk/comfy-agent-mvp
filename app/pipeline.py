"""MK-P7 — Full pipeline from BriefModel to Episode.

Wires together all previous layers:
  - BriefParser
  - CharacterResolver
  - VoiceResolver
  - KeyframePlanner
  - SceneBuilder
  - EpisodeAssembler
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

from app.brief.parser import BriefParser
from app.brief.models import BriefModel
from app.characters.resolver import CharacterResolver, CharacterResolveWarning
from app.characters.models import ResolvedCharacter
from app.voice.resolver import VoiceResolver
from app.voice.models import ResolvedVoice
from app.keyframes.planner import KeyframePlanner
from app.keyframes.models import SceneKeyframePlan
from app.reference.grid_generator import ReferenceGridGenerator
from app.scenes.builder import SceneBuilder
from app.scenes.models import BuiltScene
from app.episode.assembler import EpisodeAssembler
from app.episode.models import Episode


@dataclass
class PipelineConfig:
    lora_dir: str | Path
    voice_map: dict[str, dict]
    fallback_voice_id: str
    default_negative: str = (
        "blurry, deformed, bad anatomy, extra limbs, watermark"
    )
    fps: int = 8
    min_keyframes: int = 2
    max_scene_duration_sec: float = 5.0
    use_reference_grid: bool = False
    allow_live_reference_generation: bool = False
    reference_grid_size: int = 4
    reference_weight: float = 0.6


class Pipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def run(
        self,
        brief_source: str | dict,
        output_dir: Path | str = "output",
        comfy_host: str = "127.0.0.1",
        comfy_port: int = 8188,
        checkpoint: str | None = None,
    ) -> Episode:
        brief = BriefParser().parse(brief_source)
        output_dir = Path(output_dir)

        # Resolve characters
        char_resolver = CharacterResolver(
            lora_dir=self.config.lora_dir,
            default_negative=self.config.default_negative,
        )
        resolved_chars = char_resolver.resolve(brief)

        # Resolve voices for each character
        voice_resolver = VoiceResolver(
            voice_map=self.config.voice_map,
            fallback_voice_id=self.config.fallback_voice_id,
        )
        for char in resolved_chars:
            voice_resolver.resolve(char.voice_id)

        # Generate reference grids (one per character)
        reference_paths: dict[str, Path] = {}
        if self.config.use_reference_grid:
            if not self.config.allow_live_reference_generation:
                warnings.warn(
                    "[REFERENCE] skipped: live reference generation disabled "
                    "(set allow_live_reference_generation=True to enable)",
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                grid_generator = ReferenceGridGenerator(
                    host=comfy_host,
                    port=comfy_port,
                    checkpoint=checkpoint,
                    allow_live_submit=True,
                )
                ref_dir = output_dir / "reference"
                for char_def in brief.characters:
                    try:
                        grid_generator.generate(
                            character=char_def,
                            meta=brief.meta,
                            output_dir=ref_dir,
                            grid_size=self.config.reference_grid_size,
                        )
                        reference_paths[char_def.name] = grid_generator.get_best_frame(
                            ref_dir, char_def.name
                        )
                    except Exception as exc:
                        warnings.warn(
                            f"Reference grid generation failed for '{char_def.name}': {exc}",
                            RuntimeWarning,
                            stacklevel=2,
                        )

        # Plan keyframes
        keyframe_planner = KeyframePlanner(
            fps=self.config.fps or brief.meta.fps,
            min_keyframes=self.config.min_keyframes,
            max_scene_duration_sec=self.config.max_scene_duration_sec,
        )
        scene_plan_pairs = keyframe_planner.plan_with_scenes(brief)

        # Build scenes
        scene_builder = SceneBuilder(default_negative=self.config.default_negative)
        built_scenes: list[BuiltScene] = []
        aspect_ratio = brief.meta.aspect_ratio
        for scene_def, plan in scene_plan_pairs:
            built_scenes.append(scene_builder.build(scene_def, plan, resolved_chars, aspect_ratio=aspect_ratio))

        # Assemble episode
        episode = EpisodeAssembler().assemble(brief, built_scenes)
        episode.reference_paths = reference_paths
        return episode
