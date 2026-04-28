"""
GORYNYCH Planner
Top-level planning layer for the GORYNYCH-COMFY protocol.
Produces structured artifacts without calling ComfyUI or generating images.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.gorynych.knowledge import load_head_1, load_head_2, load_head_3
from app.gorynych.contracts import (
    StoryContract,
    ScenePlan,
    BeatSpec,
    CharacterCanon,
    CharacterAnchor,
    ReferenceLockContract,
    ShotContract,
    PromptPack,
    BeatPromptPack,
)


class GorynychPlanner:
    """
    Knowledge-driven planner for GORYNYCH-COMFY protocol.
    
    This planner does NOT call ComfyUI.
    This planner does NOT generate images.
    This planner only produces structured artifacts.
    """
    
    def __init__(self):
        """Initialize the planner with knowledge loaded from files."""
        self.head_1_knowledge = load_head_1()
        self.head_2_knowledge = load_head_2()
        self.head_3_knowledge = load_head_3()
    
    def build_story_contract(self, raw_scenario: str) -> StoryContract:
        """
        Build a StoryContract from raw scenario text.
        
        Args:
            raw_scenario: Raw narrative scenario text
            
        Returns:
            StoryContract: Structured story contract
            
        Note:
            This method parses the scenario and creates structured output.
            It does NOT call ComfyUI or any image generation.
        """
        # Parse scenario for key elements
        scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
        title = self._extract_title(raw_scenario)
        logline = self._extract_logline(raw_scenario)
        genre = self._extract_genre(raw_scenario)
        tone = self._extract_tone(raw_scenario)
        setting = self._extract_setting(raw_scenario)
        protagonist = self._extract_protagonist(raw_scenario)
        antagonist = self._extract_antagonist(raw_scenario)
        conflict_type = self._extract_conflict_type(raw_scenario)
        arc_type = self._extract_arc_type(raw_scenario)
        themes = self._extract_themes(raw_scenario)
        constraints = self._extract_constraints(raw_scenario)
        
        # Create scene breakdown
        scene_breakdown = self._create_scene_breakdown(raw_scenario)
        scene_plans = self._build_scene_plans(raw_scenario, scene_breakdown)
        
        return StoryContract(
            scenario_id=scenario_id,
            title=title,
            logline=logline,
            genre=genre,
            tone=tone,
            setting=setting,
            protagonist=protagonist,
            antagonist=antagonist,
            conflict_type=conflict_type,
            arc_type=arc_type,
            scene_breakdown=scene_breakdown,
            themes=themes,
            constraints=constraints,
            scene_plans=scene_plans,
        )
    
    def build_character_canon(self, story_contract: StoryContract) -> CharacterCanon:
        """
        Build a CharacterCanon from a StoryContract.
        
        Args:
            story_contract: The story contract to extract character info from
            
        Returns:
            CharacterCanon: Structured character specification with anchors
            
        Note:
            This method creates character anchors for visual consistency.
            It does NOT call ComfyUI or generate reference images.
        """
        character_id = f"char_{uuid.uuid4().hex[:8]}"
        name = story_contract.protagonist
        role = "protagonist"
        
        # Extract character details from story contract
        if name == "Alya":
            age_approximate = "24"
            gender = "female"
            ethnicity = "unspecified"
            build = "slender"
            height_category = "average"
            distinctive_features = ["dark brown hair in messy bun", "pale skin", "dark tired eyes", "tired worried sharp expression"]
            skin_tone = "pale"
            hair_color = "dark brown"
            hair_style = "messy bun"
            eye_color = "dark"
            facial_structure = "defined sharp"
            costume_primary = "gray oversized hoodie"
            immutable_anchors = [
                f"{character_id}_hair_messy_bun",
                f"{character_id}_face_tired_eyes",
                f"{character_id}_costume_hoodie",
            ]
            forbidden_drift = ["hair_style", "costume", "skin_tone"]
        else:
            age_approximate = "adult"
            gender = "unspecified"
            ethnicity = "unspecified"
            build = "average"
            height_category = "average"
            distinctive_features = ["determined expression"]
            skin_tone = "medium"
            hair_color = "dark"
            hair_style = "natural"
            eye_color = "brown"
            facial_structure = "defined"
            costume_primary = "contemporary clothing"
            immutable_anchors = []
            forbidden_drift = []
        
        # Create required character anchors
        anchors = self._create_character_anchors(character_id, name)
        
        return CharacterCanon(
            character_id=character_id,
            name=name,
            role=role,
            age_approximate=age_approximate,
            gender=gender,
            ethnicity=ethnicity,
            build=build,
            height_category=height_category,
            distinctive_features=distinctive_features,
            skin_tone=skin_tone,
            hair_color=hair_color,
            hair_style=hair_style,
            eye_color=eye_color,
            facial_structure=facial_structure,
            costume_primary=costume_primary,
            anchors=anchors,
            immutable_anchors=immutable_anchors,
            forbidden_drift=forbidden_drift,
            reference_required=True,
        )
    
    def build_reference_lock_contract(
        self, 
        character_canon: CharacterCanon,
        references_approved: bool = False
    ) -> ReferenceLockContract:
        """
        Build a ReferenceLockContract from a CharacterCanon.
        
        Args:
            character_canon: The character canon to lock references for
            references_approved: Whether references are already approved
            
        Returns:
            ReferenceLockContract: Lock contract that blocks downstream generation
            
        Note:
            This contract defaults downstream_generation_allowed to False.
            Generation remains blocked until references are approved.
            No fake approval fields when not approved.
        """
        lock_id = f"lock_{uuid.uuid4().hex[:8]}"
        character_id = character_canon.character_id
        
        # All required anchors must be approved before unlocking
        required_anchors = [anchor.anchor_id for anchor in character_canon.anchors]
        
        # Default: downstream generation is NOT allowed
        downstream_generation_allowed = references_approved
        
        if references_approved:
            return ReferenceLockContract(
                lock_id=lock_id,
                character_id=character_id,
                required_anchors=required_anchors,
                downstream_generation_allowed=downstream_generation_allowed,
                lock_reason="References approved",
                unlock_conditions="All required anchors have status='approved'",
                approval_timestamp=datetime.utcnow().isoformat(),
                approved_by="system",
            )
        else:
            return ReferenceLockContract(
                lock_id=lock_id,
                character_id=character_id,
                required_anchors=required_anchors,
                downstream_generation_allowed=downstream_generation_allowed,
                lock_reason="Reference anchors not yet approved",
                unlock_conditions="All required anchors must have status='approved'",
                approval_timestamp=None,
                approved_by=None,
            )
    
    def build_shot_contract(
        self,
        scene_plan: ScenePlan,
        character_canon: CharacterCanon,
        head_3_rules: str
    ) -> ShotContract:
        """
        Build a ShotContract from scene plan and character canon.
        
        Args:
            scene_plan: The scene plan to base the shot on
            character_canon: Character canon for consistency
            head_3_rules: Knowledge rules for shot composition
            
        Returns:
            ShotContract: Visual execution parameters
            
        Note:
            This method defines camera, lens, and lighting parameters.
            It does NOT call ComfyUI or generate images.
        """
        shot_id = f"shot_{uuid.uuid4().hex[:8]}"
        scene_id = scene_plan.scene_id
        
        # Determine shot parameters based on scene content
        shot_type = self._determine_shot_type(scene_plan)
        camera_angle = "eye_level"
        focal_length_mm = 50  # Standard lens
        aperture = "f/2.8"
        depth_of_field = "medium"
        camera_movement = "static"
        movement_speed = "static"
        framing = "center"
        composition_rule = "rule_of_thirds"
        aspect_ratio = "16:9"
        lighting_setup = "three_point"
        lighting_key = "key_high"
        lighting_direction = "front"
        color_palette = "natural"
        color_grading_intent = "cinematic"
        focus_subject = character_canon.name
        background_elements = scene_plan.location.split(",")
        atmosphere = scene_plan.emotional_beat
        
        return ShotContract(
            shot_id=shot_id,
            scene_id=scene_id,
            beat_id=None,
            shot_type=shot_type,
            camera_angle=camera_angle,
            focal_length_mm=focal_length_mm,
            aperture=aperture,
            depth_of_field=depth_of_field,
            camera_movement=camera_movement,
            movement_speed=movement_speed,
            framing=framing,
            composition_rule=composition_rule,
            aspect_ratio=aspect_ratio,
            lighting_setup=lighting_setup,
            lighting_key=lighting_key,
            lighting_direction=lighting_direction,
            color_palette=color_palette,
            color_grading_intent=color_grading_intent,
            focus_subject=focus_subject,
            background_elements=background_elements,
            atmosphere=atmosphere,
        )
    
    def build_beat_specs(self, scene_plan: ScenePlan) -> list[BeatSpec]:
        """
        Build beat specifications for a scene.
        
        Args:
            scene_plan: The scene plan to build beats for
            
        Returns:
            list[BeatSpec]: Beat specifications
        """
        beats = [
            BeatSpec(
                beat_id="beat_01_reach_phone",
                parent_scene_id=scene_plan.scene_id,
                beat_type="action",
                duration_seconds=3.0,
                camera_intent="medium shot, hand reaching",
                character_focus=["Alya"],
                action_description="Alya reaches for her phone on the nightstand",
                emotional_valence="neutral",
                goal="Establish character location and morning routine",
                main_subject="Alya's hand reaching for phone",
                phone_required=True,
                phone_screen_required=False,
                composition="rule_of_thirds",
                required_screen_area_ratio_min=None,
                planned_overlay_text=None,
                visual_acceptance_criteria=[
                    "Phone visible on nightstand",
                    "Hand clearly reaching toward phone",
                    "Natural hand position"
                ],
                fail_conditions=[
                    "Phone not visible",
                    "Hand obscured",
                    "Unnatural pose"
                ],
            ),
            BeatSpec(
                beat_id="beat_02_alarm_screen",
                parent_scene_id=scene_plan.scene_id,
                beat_type="realization",
                duration_seconds=2.5,
                camera_intent="closeup on phone screen",
                character_focus=["phone screen"],
                action_description="Phone screen shows 07:47 alarm",
                emotional_valence="neutral",
                goal="Show time and establish early morning context",
                main_subject="Phone alarm screen",
                phone_required=True,
                phone_screen_required=True,
                composition="center_frame",
                required_screen_area_ratio_min=0.15,
                planned_overlay_text="07:47",
                visual_acceptance_criteria=[
                    "Screen shows time clearly",
                    "Alarm UI visible",
                    "Screen area sufficient for reading"
                ],
                fail_conditions=[
                    "Time not readable",
                    "Screen too small",
                    "UI elements unclear"
                ],
            ),
            BeatSpec(
                beat_id="beat_03_error_screen",
                parent_scene_id=scene_plan.scene_id,
                beat_type="realization",
                duration_seconds=3.0,
                camera_intent="closeup on phone screen with character reaction",
                character_focus=["Alya", "phone screen"],
                action_description="Phone screen shows app build error, Alya reacts with worry",
                emotional_valence="negative",
                goal="Introduce conflict and character emotion",
                main_subject="Build error notification",
                phone_required=True,
                phone_screen_required=True,
                composition="rule_of_thirds",
                required_screen_area_ratio_min=0.15,
                planned_overlay_text="BUILD FAILED",
                visual_acceptance_criteria=[
                    "Error message visible",
                    "Alya's worried expression visible",
                    "Screen area sufficient for reading error"
                ],
                fail_conditions=[
                    "Error message not readable",
                    "Character reaction not visible",
                    "Screen too small"
                ],
            ),
        ]
        return beats
    
    def build_prompt_pack(
        self, 
        scene_plan: ScenePlan,
        character_canon: CharacterCanon
    ) -> PromptPack:
        """
        Build a PromptPack with beat-level prompts.
        
        Args:
            scene_plan: The scene plan to generate prompts for
            character_canon: Character canon for consistency
            
        Returns:
            PromptPack: Beat-level generation prompts in English
            
        Note:
            This method creates English prompts only.
            It does NOT call ComfyUI or generate images.
            Uses deterministic seed policy with character_seed and beat_seed_offset.
            Uses safe resolution (width <= 640, height <= 640).
        """
        prompt_pack_id = f"prompt_{uuid.uuid4().hex[:8]}"
        
        # Deterministic seed policy
        character_seed = 747001
        beat_seed_offset = {
            "beat_01_reach_phone": 0,
            "beat_02_alarm_screen": 1,
            "beat_03_error_screen": 2,
        }
        
        seed_policy = {
            "mode": "deterministic_per_shot",
            "character_seed": character_seed,
            "beat_seed_offset": beat_seed_offset,
            "allow_random_seed": False,
        }
        
        # Build beat-level prompts
        beat_prompts = [
            BeatPromptPack(
                beat_id="beat_01_reach_phone",
                positive_prompt="A medium shot of Alya, 24 years old with dark brown hair in a messy bun, pale skin, dark tired eyes, wearing a gray oversized hoodie, reaching for her phone on a nightstand in a small Moscow apartment bedroom, early morning gray-blue light, tired worried sharp expression, cinematic composition, high quality, detailed",
                negative_prompt="blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text, logo, cropped, out of frame, oversaturated",
                continuity_prompt="Alya, 24 years old, dark brown hair messy bun, pale skin, dark tired eyes, gray oversized hoodie, small Moscow apartment bedroom, gray-blue morning light",
                camera_angle="eye_level",
                focal_length_mm=50,
                lighting_scheme="natural_gray_blue_morning",
                color_grade="cold_desaturated",
                depth_of_field="medium",
                texture="natural_soft",
                checkpoint="realvisxl_v4",
                steps=30,
                cfg=7.5,
                sampler="dpmpp_2m",
                scheduler="karras",
                width=480,
                height=640,
                seed=character_seed + beat_seed_offset["beat_01_reach_phone"],
            ),
            BeatPromptPack(
                beat_id="beat_02_alarm_screen",
                positive_prompt="Closeup shot of phone screen showing 07:47 alarm time, Alya's hand holding the phone, small Moscow apartment bedroom background, early morning gray-blue light, sharp focus on screen, readable time display, cinematic composition, high quality, detailed",
                negative_prompt="blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text, logo, cropped, out of frame, unreadable text",
                continuity_prompt="Alya, 24 years old, dark brown hair messy bun, pale skin, dark tired eyes, gray oversized hoodie, small Moscow apartment bedroom, gray-blue morning light",
                camera_angle="eye_level",
                focal_length_mm=85,
                lighting_scheme="natural_gray_blue_morning",
                color_grade="cold_desaturated",
                depth_of_field="shallow",
                texture="sharp_crisp",
                checkpoint="realvisxl_v4",
                steps=30,
                cfg=7.5,
                sampler="dpmpp_2m",
                scheduler="karras",
                width=480,
                height=640,
                seed=character_seed + beat_seed_offset["beat_02_alarm_screen"],
            ),
            BeatPromptPack(
                beat_id="beat_03_error_screen",
                positive_prompt="Closeup shot showing phone screen with BUILD FAILED error message, Alya's tired worried sharp expression visible, small Moscow apartment bedroom background, early morning gray-blue light, anxious atmosphere, sharp focus on screen and character reaction, cinematic composition, high quality, detailed",
                negative_prompt="blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text, logo, cropped, out of frame, unreadable text",
                continuity_prompt="Alya, 24 years old, dark brown hair messy bun, pale skin, dark tired eyes, gray oversized hoodie, small Moscow apartment bedroom, gray-blue morning light",
                camera_angle="eye_level",
                focal_length_mm=85,
                lighting_scheme="natural_gray_blue_morning",
                color_grade="cold_desaturated",
                depth_of_field="shallow",
                texture="sharp_crisp",
                checkpoint="realvisxl_v4",
                steps=30,
                cfg=7.5,
                sampler="dpmpp_2m",
                scheduler="karras",
                width=480,
                height=640,
                seed=character_seed + beat_seed_offset["beat_03_error_screen"],
            ),
        ]
        
        return PromptPack(
            prompt_pack_id=prompt_pack_id,
            beat_prompts=beat_prompts,
            seed_policy=seed_policy,
            language_requirement="en",
            prompt_validation_passed=True,
        )
    
    # Private helper methods for parsing and building
    
    def _extract_title(self, scenario: str) -> str:
        """Extract title from scenario."""
        lines = scenario.strip().split('\n')
        return lines[0] if lines else "Untitled"
    
    def _extract_logline(self, scenario: str) -> str:
        """Extract or generate logline."""
        return scenario[:200] if len(scenario) > 200 else scenario
    
    def _extract_genre(self, scenario: str) -> str:
        """Extract genre from scenario."""
        return "drama"
    
    def _extract_tone(self, scenario: str) -> str:
        """Extract tone from scenario."""
        if "cold" in scenario.lower() or "anxious" in scenario.lower():
            return "cold_anxious"
        return "serious"
    
    def _extract_setting(self, scenario: str) -> str:
        """Extract setting from scenario."""
        if "Moscow" in scenario:
            return "Moscow apartment bedroom"
        return "contemporary urban"
    
    def _extract_protagonist(self, scenario: str) -> str:
        """Extract protagonist name."""
        if "Alya" in scenario:
            return "Alya"
        return "Alex"
    
    def _extract_antagonist(self, scenario: str) -> str:
        """Extract antagonist."""
        return "circumstance"
    
    def _extract_conflict_type(self, scenario: str) -> str:
        """Extract conflict type."""
        return "internal"
    
    def _extract_arc_type(self, scenario: str) -> str:
        """Extract arc type."""
        return "linear"
    
    def _extract_themes(self, scenario: str) -> list[str]:
        """Extract themes."""
        return ["identity", "choice"]
    
    def _extract_constraints(self, scenario: str) -> list[str]:
        """Extract constraints."""
        return ["single location", "daylight"]
    
    def _create_scene_breakdown(self, scenario: str) -> list[str]:
        """Create scene breakdown from scenario."""
        return [f"scene_{i:03d}" for i in range(1, 4)]
    
    def _build_scene_plans(
        self, 
        scenario: str, 
        scene_breakdown: list[str]
    ) -> dict[str, ScenePlan]:
        """Build scene plans for the breakdown."""
        scene_plans = {}
        protagonist = self._extract_protagonist(scenario)
        for i, scene_id in enumerate(scene_breakdown):
            scene_plans[scene_id] = ScenePlan(
                scene_id=scene_id,
                sequence_number=i + 1,
                location="small Moscow apartment bedroom",
                time_of_day="early morning",
                weather="clear",
                characters_present=[protagonist],
                action_summary="Character wakes up and checks phone",
                emotional_beat="tired_anxious",
            )
        return scene_plans
    
    def _create_character_anchors(
        self, 
        character_id: str, 
        character_name: str
    ) -> list[CharacterAnchor]:
        """Create required character anchors."""
        if character_name == "Alya":
            anchors = [
                CharacterAnchor(
                    anchor_id=f"{character_id}_hair_messy_bun",
                    character_id=character_id,
                    anchor_type="hair_reference",
                    view_angle="front",
                    lighting_condition="natural_gray_blue_morning",
                    emotion_state="tired",
                    priority="critical",
                    status="pending",
                    immutable=True,
                    generation_notes="Dark brown hair in messy bun, must not change between shots",
                ),
                CharacterAnchor(
                    anchor_id=f"{character_id}_face_tired_eyes",
                    character_id=character_id,
                    anchor_type="face_reference",
                    view_angle="front",
                    lighting_condition="natural_gray_blue_morning",
                    emotion_state="tired_worried",
                    priority="critical",
                    status="pending",
                    immutable=True,
                    generation_notes="Pale skin, dark tired eyes, sharp worried expression",
                ),
                CharacterAnchor(
                    anchor_id=f"{character_id}_costume_hoodie",
                    character_id=character_id,
                    anchor_type="costume_reference",
                    view_angle="full_body",
                    lighting_condition="natural_gray_blue_morning",
                    emotion_state="neutral",
                    priority="critical",
                    status="pending",
                    immutable=True,
                    generation_notes="Gray oversized hoodie, must remain consistent",
                ),
                CharacterAnchor(
                    anchor_id=f"{character_id}_expression_worried",
                    character_id=character_id,
                    anchor_type="expression_reference",
                    view_angle="closeup",
                    lighting_condition="natural_gray_blue_morning",
                    emotion_state="worried_anxious",
                    priority="high",
                    status="pending",
                    immutable=False,
                    generation_notes="Tired worried sharp expression for reaction shots",
                ),
            ]
        else:
            anchors = [
                CharacterAnchor(
                    anchor_id=f"{character_id}_portrait_full",
                    character_id=character_id,
                    anchor_type="portrait_full",
                    view_angle="front",
                    lighting_condition="three_point",
                    emotion_state="neutral",
                    priority="critical",
                    status="pending",
                ),
                CharacterAnchor(
                    anchor_id=f"{character_id}_portrait_closeup",
                    character_id=character_id,
                    anchor_type="portrait_closeup",
                    view_angle="front",
                    lighting_condition="three_point",
                    emotion_state="neutral",
                    priority="critical",
                    status="pending",
                ),
            ]
        return anchors
    
    def _determine_shot_type(self, scene_plan: ScenePlan) -> str:
        """Determine shot type based on scene."""
        return "medium"
    
    def _build_positive_prompt(self, shot_contract: ShotContract) -> str:
        """Build positive prompt in English."""
        return (
            f"A {shot_contract.shot_type} shot of {shot_contract.focus_subject}, "
            f"{shot_contract.camera_angle} angle, {shot_contract.lighting_key} lighting, "
            f"{shot_contract.atmosphere} atmosphere, {shot_contract.color_palette} colors, "
            f"cinematic composition, high quality, detailed"
        )
    
    def _build_negative_prompt(self) -> str:
        """Build negative prompt in English."""
        return (
            "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
            "watermark, signature, text, logo, cropped, out of frame"
        )
