"""MK-P1 — Brief/TZ data model.

Pydantic v2 models representing a structured production brief.
These are the canonical input types for all downstream pipeline layers:
  - Characters resolver  (character.visual_description → ComfyUI prompt)
  - Voice assignment     (character.voice_id → TTS call)
  - Keyframe planner     (scene.keyframe_hints, scene.duration_hint_sec)
  - Scene builder        (scene.* → ComfyUI workflow parameters)
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ProjectMeta(BaseModel):
    title: str
    aspect_ratio: str = "4:3"
    fps: int = 8
    target_duration_sec: float = Field(gt=0)
    style_hint: Optional[str] = None
    mood: Optional[str] = None
    episode_id: Optional[str] = None
    shot_id: Optional[str] = None


class CharacterDef(BaseModel):
    name: str
    visual_description: str          # → ComfyUI positive prompt fragment
    voice_id: Optional[str] = None   # → TTS engine ref
    lora_ref: Optional[str] = None   # → optional LoRA filename


class SceneDef(BaseModel):
    scene_id: str                    # "s01", "s02", …
    characters_in_scene: list[str] = Field(default_factory=list)   # names from CharacterDef
    location: Optional[str] = None
    action: str                      # what happens
    description: Optional[str] = None  # MK-REAL2R-2: detailed scene description for prompt
    dialogue: Optional[str] = None
    duration_hint_sec: float = 1.5
    keyframe_hints: list[str] = Field(default_factory=list)
    time: Optional[str] = None
    mood: Optional[str] = None
    continuity_out: Optional[str] = None
    subtitles: Optional[str] = None

    @model_validator(mode="after")
    def scene_id_format(self) -> "SceneDef":
        if not self.scene_id.startswith("s"):
            self.scene_id = f"s{self.scene_id.zfill(2)}"
        return self


class BriefModel(BaseModel):
    meta: ProjectMeta
    characters: list[CharacterDef] = Field(default_factory=list)
    scenes: list[SceneDef] = Field(min_length=1)

    def character_by_name(self, name: str) -> CharacterDef:
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        raise KeyError(f"Character '{name}' not in brief")

    def to_dict(self) -> dict:
        return self.model_dump()
