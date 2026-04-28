"""
GORYNYCH Contract Definitions
Data structures for the GORYNYCH-COMFY protocol.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class BeatSpec:
    """Atomic narrative unit specification with production-level detail."""
    beat_id: str
    parent_scene_id: str
    beat_type: str  # action, reaction, realization, decision, transition
    duration_seconds: float
    camera_intent: str
    character_focus: list[str]
    action_description: str
    emotional_valence: str  # positive, negative, neutral
    # Production-specific fields
    goal: str
    main_subject: str
    phone_required: bool = False
    phone_screen_required: bool = False
    composition: str = "center"
    required_screen_area_ratio_min: Optional[float] = None
    planned_overlay_text: Optional[str] = None
    visual_acceptance_criteria: list[str] = field(default_factory=list)
    fail_conditions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "beat_id": self.beat_id,
            "parent_scene_id": self.parent_scene_id,
            "beat_type": self.beat_type,
            "duration_seconds": self.duration_seconds,
            "camera_intent": self.camera_intent,
            "character_focus": self.character_focus,
            "action_description": self.action_description,
            "emotional_valence": self.emotional_valence,
            "goal": self.goal,
            "main_subject": self.main_subject,
            "phone_required": self.phone_required,
            "phone_screen_required": self.phone_screen_required,
            "composition": self.composition,
            "required_screen_area_ratio_min": self.required_screen_area_ratio_min,
            "planned_overlay_text": self.planned_overlay_text,
            "visual_acceptance_criteria": self.visual_acceptance_criteria,
            "fail_conditions": self.fail_conditions,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BeatSpec":
        return cls(**data)


@dataclass
class ScenePlan:
    """Scene-level planning specification."""
    scene_id: str
    sequence_number: int
    location: str
    time_of_day: str
    weather: str
    characters_present: list[str]
    action_summary: str
    emotional_beat: str
    dialogue_requirements: Optional[str] = None
    sound_design_notes: Optional[str] = None
    beats: list[BeatSpec] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "sequence_number": self.sequence_number,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "characters_present": self.characters_present,
            "action_summary": self.action_summary,
            "emotional_beat": self.emotional_beat,
            "dialogue_requirements": self.dialogue_requirements,
            "sound_design_notes": self.sound_design_notes,
            "beats": [beat.to_dict() for beat in self.beats],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ScenePlan":
        beats_data = data.pop("beats", [])
        beats = [BeatSpec.from_dict(b) for b in beats_data]
        return cls(beats=beats, **data)


@dataclass
class StoryContract:
    """Top-level story structure contract."""
    scenario_id: str
    title: str
    logline: str
    genre: str
    tone: str
    setting: str
    protagonist: str
    antagonist: str
    conflict_type: str
    arc_type: str
    scene_breakdown: list[str]
    themes: list[str]
    constraints: list[str]
    scene_plans: dict[str, ScenePlan] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre,
            "tone": self.tone,
            "setting": self.setting,
            "protagonist": self.protagonist,
            "antagonist": self.antagonist,
            "conflict_type": self.conflict_type,
            "arc_type": self.arc_type,
            "scene_breakdown": self.scene_breakdown,
            "themes": self.themes,
            "constraints": self.constraints,
            "scene_plans": {
                scene_id: plan.to_dict() 
                for scene_id, plan in self.scene_plans.items()
            },
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "StoryContract":
        scene_plans_data = data.pop("scene_plans", {})
        scene_plans = {
            scene_id: ScenePlan.from_dict(plan_data)
            for scene_id, plan_data in scene_plans_data.items()
        }
        return cls(scene_plans=scene_plans, **data)


@dataclass
class CharacterAnchor:
    """Reference specification for character consistency."""
    anchor_id: str
    character_id: str
    anchor_type: str  # portrait_full, portrait_closeup, body_reference, etc.
    view_angle: str
    lighting_condition: str
    emotion_state: str
    priority: str  # critical, high, medium, low
    status: str  # pending, generated, approved, locked
    reference_path: Optional[str] = None
    generation_notes: Optional[str] = None
    immutable: bool = False  # Whether this anchor cannot change
    
    def to_dict(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "character_id": self.character_id,
            "anchor_type": self.anchor_type,
            "view_angle": self.view_angle,
            "lighting_condition": self.lighting_condition,
            "emotion_state": self.emotion_state,
            "priority": self.priority,
            "status": self.status,
            "reference_path": self.reference_path,
            "generation_notes": self.generation_notes,
            "immutable": self.immutable,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CharacterAnchor":
        return cls(**data)


@dataclass
class CharacterCanon:
    """Character consistency and anchoring specification."""
    character_id: str
    name: str
    role: str
    age_approximate: str
    gender: str
    ethnicity: str
    build: str
    height_category: str
    distinctive_features: list[str]
    skin_tone: str
    hair_color: str
    hair_style: str
    eye_color: str
    facial_structure: str
    costume_primary: str
    costume_secondary: Optional[str] = None
    accessories: list[str] = field(default_factory=list)
    posture_default: Optional[str] = None
    expression_default: Optional[str] = None
    voice_characteristics: Optional[str] = None
    personality_traits: list[str] = field(default_factory=list)
    background_summary: Optional[str] = None
    anchors: list[CharacterAnchor] = field(default_factory=list)
    # Production-level fields
    immutable_anchors: list[str] = field(default_factory=list)
    forbidden_drift: list[str] = field(default_factory=list)
    reference_required: bool = True
    
    def to_dict(self) -> dict:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "role": self.role,
            "age_approximate": self.age_approximate,
            "gender": self.gender,
            "ethnicity": self.ethnicity,
            "build": self.build,
            "height_category": self.height_category,
            "distinctive_features": self.distinctive_features,
            "skin_tone": self.skin_tone,
            "hair_color": self.hair_color,
            "hair_style": self.hair_style,
            "eye_color": self.eye_color,
            "facial_structure": self.facial_structure,
            "costume_primary": self.costume_primary,
            "costume_secondary": self.costume_secondary,
            "accessories": self.accessories,
            "posture_default": self.posture_default,
            "expression_default": self.expression_default,
            "voice_characteristics": self.voice_characteristics,
            "personality_traits": self.personality_traits,
            "background_summary": self.background_summary,
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "immutable_anchors": self.immutable_anchors,
            "forbidden_drift": self.forbidden_drift,
            "reference_required": self.reference_required,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "CharacterCanon":
        anchors_data = data.pop("anchors", [])
        anchors = [CharacterAnchor.from_dict(a) for a in anchors_data]
        return cls(anchors=anchors, **data)


@dataclass
class ReferenceLockContract:
    """Controls downstream generation based on reference availability."""
    lock_id: str
    character_id: str
    required_anchors: list[str]
    downstream_generation_allowed: bool = False
    lock_reason: str = "Reference anchors not yet approved"
    unlock_conditions: Optional[str] = None
    approval_timestamp: Optional[str] = None
    approved_by: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "lock_id": self.lock_id,
            "character_id": self.character_id,
            "required_anchors": self.required_anchors,
            "downstream_generation_allowed": self.downstream_generation_allowed,
            "lock_reason": self.lock_reason,
            "unlock_conditions": self.unlock_conditions,
            "approval_timestamp": self.approval_timestamp,
            "approved_by": self.approved_by,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ReferenceLockContract":
        return cls(**data)


@dataclass
class ShotContract:
    """Visual execution parameters for a shot."""
    shot_id: str
    scene_id: str
    beat_id: Optional[str]
    shot_type: str  # wide, medium, closeup, etc.
    camera_angle: str
    focal_length_mm: int
    aperture: str
    depth_of_field: str
    camera_movement: str
    movement_speed: str
    framing: str
    composition_rule: str
    aspect_ratio: str
    lighting_setup: str
    lighting_key: str
    lighting_direction: str
    color_palette: str
    color_grading_intent: str
    focus_subject: str
    background_elements: list[str]
    atmosphere: str
    technical_notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "shot_id": self.shot_id,
            "scene_id": self.scene_id,
            "beat_id": self.beat_id,
            "shot_type": self.shot_type,
            "camera_angle": self.camera_angle,
            "focal_length_mm": self.focal_length_mm,
            "aperture": self.aperture,
            "depth_of_field": self.depth_of_field,
            "camera_movement": self.camera_movement,
            "movement_speed": self.movement_speed,
            "framing": self.framing,
            "composition_rule": self.composition_rule,
            "aspect_ratio": self.aspect_ratio,
            "lighting_setup": self.lighting_setup,
            "lighting_key": self.lighting_key,
            "lighting_direction": self.lighting_direction,
            "color_palette": self.color_palette,
            "color_grading_intent": self.color_grading_intent,
            "focus_subject": self.focus_subject,
            "background_elements": self.background_elements,
            "atmosphere": self.atmosphere,
            "technical_notes": self.technical_notes,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ShotContract":
        return cls(**data)


@dataclass
class BeatPromptPack:
    """Beat-level generation instructions."""
    beat_id: str
    positive_prompt: str
    negative_prompt: str
    continuity_prompt: str
    camera_angle: str
    focal_length_mm: int
    lighting_scheme: str
    color_grade: str
    depth_of_field: str
    texture: str
    checkpoint: str
    steps: int
    cfg: float
    sampler: str
    scheduler: str
    width: int
    height: int
    seed: int
    
    def to_dict(self) -> dict:
        return {
            "beat_id": self.beat_id,
            "positive_prompt": self.positive_prompt,
            "negative_prompt": self.negative_prompt,
            "continuity_prompt": self.continuity_prompt,
            "camera_angle": self.camera_angle,
            "focal_length_mm": self.focal_length_mm,
            "lighting_scheme": self.lighting_scheme,
            "color_grade": self.color_grade,
            "depth_of_field": self.depth_of_field,
            "texture": self.texture,
            "checkpoint": self.checkpoint,
            "steps": self.steps,
            "cfg": self.cfg,
            "sampler": self.sampler,
            "scheduler": self.scheduler,
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BeatPromptPack":
        return cls(**data)


@dataclass
class PromptPack:
    """Generation instructions container with beat-level prompts."""
    prompt_pack_id: str
    beat_prompts: list[BeatPromptPack]
    seed_policy: dict[str, Any]  # {"mode": "deterministic_per_shot", "character_seed": ..., "beat_seed_offset": {...}, "allow_random_seed": false}
    language_requirement: str = "en"
    prompt_validation_passed: bool = False
    
    def to_dict(self) -> dict:
        return {
            "prompt_pack_id": self.prompt_pack_id,
            "beat_prompts": [bp.to_dict() for bp in self.beat_prompts],
            "seed_policy": self.seed_policy,
            "language_requirement": self.language_requirement,
            "prompt_validation_passed": self.prompt_validation_passed,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def validate_language(self) -> bool:
        """Validate that all prompts are in English."""
        for bp in self.beat_prompts:
            try:
                bp.positive_prompt.encode('ascii')
                bp.negative_prompt.encode('ascii')
                bp.continuity_prompt.encode('ascii')
            except UnicodeEncodeError:
                return False
        return True
    
    def validate_seed_policy(self) -> bool:
        """Validate seed policy is deterministic_per_shot or random with explicit allow."""
        mode = self.seed_policy.get("mode")
        allow_random = self.seed_policy.get("allow_random_seed", False)
        
        if mode == "deterministic_per_shot":
            return not allow_random
        elif mode == "random":
            return allow_random
        else:
            return False
    
    def validate_safe_resolution(self) -> bool:
        """Validate that all beat prompts use safe resolution."""
        for bp in self.beat_prompts:
            if bp.width > 640 or bp.height > 640:
                return False
        return True
    
    @classmethod
    def from_dict(cls, data: dict) -> "PromptPack":
        beat_prompts_data = data.pop("beat_prompts", [])
        beat_prompts = [BeatPromptPack.from_dict(bp) for bp in beat_prompts_data]
        return cls(beat_prompts=beat_prompts, **data)
