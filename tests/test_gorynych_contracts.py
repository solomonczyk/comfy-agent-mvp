"""
Tests for GORYNYCH contract definitions.
"""

import pytest
import json

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


class TestStoryContract:
    """Test StoryContract serialization and structure."""
    
    def test_story_contract_serializes_to_json(self):
        """Test that StoryContract can be serialized to JSON."""
        contract = StoryContract(
            scenario_id="test_scenario",
            title="Test Story",
            logline="A test logline",
            genre="drama",
            tone="serious",
            setting="urban",
            protagonist="Alex",
            antagonist="fate",
            conflict_type="internal",
            arc_type="linear",
            scene_breakdown=["scene_001"],
            themes=["identity"],
            constraints=["single_location"],
        )
        
        # Test to_dict
        data = contract.to_dict()
        assert isinstance(data, dict)
        assert data["scenario_id"] == "test_scenario"
        
        # Test to_json
        json_str = contract.to_json()
        assert isinstance(json_str, str)
        
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["scenario_id"] == "test_scenario"


class TestCharacterCanon:
    """Test CharacterCanon structure and anchors."""
    
    def test_character_canon_includes_character_anchors(self):
        """Test that CharacterCanon includes character anchors."""
        anchor = CharacterAnchor(
            anchor_id="anchor_001",
            character_id="char_001",
            anchor_type="portrait_full",
            view_angle="front",
            lighting_condition="three_point",
            emotion_state="neutral",
            priority="critical",
            status="pending",
        )
        
        canon = CharacterCanon(
            character_id="char_001",
            name="Alex",
            role="protagonist",
            age_approximate="adult",
            gender="unspecified",
            ethnicity="unspecified",
            build="average",
            height_category="average",
            distinctive_features=["determined"],
            skin_tone="medium",
            hair_color="dark",
            hair_style="natural",
            eye_color="brown",
            facial_structure="defined",
            costume_primary="casual",
            anchors=[anchor],
        )
        
        assert len(canon.anchors) == 1
        assert canon.anchors[0].anchor_id == "anchor_001"
        
        # Test serialization
        data = canon.to_dict()
        assert "anchors" in data
        assert len(data["anchors"]) == 1


class TestReferenceLockContract:
    """Test ReferenceLockContract defaults and structure."""
    
    def test_reference_lock_contract_defaults_downstream_generation_allowed_false(self):
        """Test that ReferenceLockContract defaults downstream_generation_allowed to False."""
        lock = ReferenceLockContract(
            lock_id="lock_001",
            character_id="char_001",
            required_anchors=["anchor_001", "anchor_002"],
        )
        
        assert lock.downstream_generation_allowed is False
        
        # Test serialization
        data = lock.to_dict()
        assert data["downstream_generation_allowed"] is False


class TestPromptPack:
    """Test PromptPack validation and structure."""
    
    def test_prompt_pack_requires_english_generation_prompts(self):
        """Test that PromptPack requires English generation prompts."""
        beat_prompt = BeatPromptPack(
            beat_id="beat_001",
            positive_prompt="A cinematic shot of a character",
            negative_prompt="blurry, low quality",
            continuity_prompt="Character continuity",
            camera_angle="eye_level",
            focal_length_mm=50,
            lighting_scheme="natural",
            color_grade="cinematic",
            depth_of_field="medium",
            texture="sharp",
            checkpoint="realvisxl_v4",
            steps=30,
            cfg=7.5,
            sampler="dpmpp_2m",
            scheduler="karras",
            width=480,
            height=640,
            seed=12345,
        )
        
        pack = PromptPack(
            prompt_pack_id="prompt_001",
            beat_prompts=[beat_prompt],
            seed_policy={
                "mode": "deterministic_per_shot",
                "character_seed": 747001,
                "beat_seed_offset": {"beat_001": 0},
                "allow_random_seed": False,
            },
        )
        
        assert pack.language_requirement == "en"
        
        # Test language validation
        assert pack.validate_language() is True
    
    def test_prompt_pack_rejects_random_seed_policy_unless_explicitly_allowed(self):
        """Test that PromptPack rejects random seed policy unless explicitly allowed."""
        beat_prompt = BeatPromptPack(
            beat_id="beat_001",
            positive_prompt="A cinematic shot",
            negative_prompt="blurry",
            continuity_prompt="Character continuity",
            camera_angle="eye_level",
            focal_length_mm=50,
            lighting_scheme="natural",
            color_grade="cinematic",
            depth_of_field="medium",
            texture="sharp",
            checkpoint="realvisxl_v4",
            steps=30,
            cfg=7.5,
            sampler="dpmpp_2m",
            scheduler="karras",
            width=480,
            height=640,
            seed=12345,
        )
        
        # Create pack with random seed policy but allow_random_seed=False
        pack = PromptPack(
            prompt_pack_id="prompt_001",
            beat_prompts=[beat_prompt],
            seed_policy={
                "mode": "random",
                "allow_random_seed": False,
            },
        )
        
        # Validation should fail
        assert pack.validate_seed_policy() is False
        
        # When explicitly allowed, validation should pass
        pack.seed_policy["allow_random_seed"] = True
        assert pack.validate_seed_policy() is True
    
    def test_prompt_pack_serializes_to_json(self):
        """Test that PromptPack can be serialized to JSON."""
        beat_prompt = BeatPromptPack(
            beat_id="beat_001",
            positive_prompt="A cinematic shot",
            negative_prompt="blurry",
            continuity_prompt="Character continuity",
            camera_angle="eye_level",
            focal_length_mm=50,
            lighting_scheme="natural",
            color_grade="cinematic",
            depth_of_field="medium",
            texture="sharp",
            checkpoint="realvisxl_v4",
            steps=30,
            cfg=7.5,
            sampler="dpmpp_2m",
            scheduler="karras",
            width=480,
            height=640,
            seed=12345,
        )
        
        pack = PromptPack(
            prompt_pack_id="prompt_001",
            beat_prompts=[beat_prompt],
            seed_policy={
                "mode": "deterministic_per_shot",
                "character_seed": 747001,
                "beat_seed_offset": {"beat_001": 0},
                "allow_random_seed": False,
            },
        )
        
        json_str = pack.to_json()
        assert isinstance(json_str, str)
        
        parsed = json.loads(json_str)
        assert parsed["prompt_pack_id"] == "prompt_001"
        assert parsed["language_requirement"] == "en"


class TestShotContract:
    """Test ShotContract structure and fields."""
    
    def test_shot_contract_has_camera_lens_light_fields(self):
        """Test that ShotContract has camera, lens, and lighting fields."""
        shot = ShotContract(
            shot_id="shot_001",
            scene_id="scene_001",
            beat_id=None,
            shot_type="medium",
            camera_angle="eye_level",
            focal_length_mm=50,
            aperture="f/2.8",
            depth_of_field="medium",
            camera_movement="static",
            movement_speed="static",
            framing="center",
            composition_rule="rule_of_thirds",
            aspect_ratio="16:9",
            lighting_setup="three_point",
            lighting_key="key_high",
            lighting_direction="front",
            color_palette="natural",
            color_grading_intent="cinematic",
            focus_subject="Alex",
            background_elements=["room"],
            atmosphere="tense",
        )
        
        assert shot.camera_angle == "eye_level"
        assert shot.focal_length_mm == 50
        assert shot.lighting_key == "key_high"
        assert shot.lighting_direction == "front"
        
        # Test serialization
        json_str = shot.to_json()
        parsed = json.loads(json_str)
        assert parsed["focal_length_mm"] == 50
