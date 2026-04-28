"""
Tests for GORYNYCH planner functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.gorynych.planner import GorynychPlanner
from app.gorynych.contracts import (
    StoryContract,
    CharacterCanon,
    ReferenceLockContract,
    ShotContract,
    PromptPack,
)


class TestGorynychPlanner:
    """Test GorynychPlanner artifact generation."""
    
    def test_planner_creates_story_contract_from_raw_scenario(self):
        """Test that planner creates story_contract from raw scenario."""
        planner = GorynychPlanner()
        raw_scenario = "A character faces a difficult choice in a city setting."
        
        story_contract = planner.build_story_contract(raw_scenario)
        
        assert isinstance(story_contract, StoryContract)
        assert story_contract.scenario_id is not None
        assert story_contract.title is not None
        assert story_contract.logline is not None
        assert len(story_contract.scene_breakdown) > 0
        assert len(story_contract.themes) > 0
    
    def test_planner_creates_character_canon_with_anchors(self):
        """Test that planner creates character_canon with anchors."""
        planner = GorynychPlanner()
        raw_scenario = "Test scenario"
        story_contract = planner.build_story_contract(raw_scenario)
        
        character_canon = planner.build_character_canon(story_contract)
        
        assert isinstance(character_canon, CharacterCanon)
        assert character_canon.character_id is not None
        assert character_canon.name is not None
        assert len(character_canon.anchors) > 0
        # At least one portrait anchor should be required
        portrait_anchors = [
            a for a in character_canon.anchors 
            if a.anchor_type in ["portrait_full", "portrait_closeup"]
        ]
        assert len(portrait_anchors) > 0
    
    def test_planner_creates_reference_lock_contract_that_blocks_downstream_generation_by_default(self):
        """Test that planner creates reference_lock_contract that blocks downstream generation by default."""
        planner = GorynychPlanner()
        raw_scenario = "Test scenario"
        story_contract = planner.build_story_contract(raw_scenario)
        character_canon = planner.build_character_canon(story_contract)
        
        reference_lock = planner.build_reference_lock_contract(character_canon)
        
        assert isinstance(reference_lock, ReferenceLockContract)
        assert reference_lock.downstream_generation_allowed is False
        assert reference_lock.lock_reason is not None
        assert len(reference_lock.required_anchors) > 0
    
    def test_planner_creates_shot_contract_with_camera_lens_light_fields(self):
        """Test that planner creates shot_contract with camera/lens/light fields."""
        planner = GorynychPlanner()
        raw_scenario = "Test scenario"
        story_contract = planner.build_story_contract(raw_scenario)
        character_canon = planner.build_character_canon(story_contract)
        
        # Get a scene plan
        scene_plan = list(story_contract.scene_plans.values())[0]
        head_3_rules = planner.head_3_knowledge
        
        shot_contract = planner.build_shot_contract(scene_plan, character_canon, head_3_rules)
        
        assert isinstance(shot_contract, ShotContract)
        assert shot_contract.camera_angle is not None
        assert shot_contract.focal_length_mm is not None
        assert shot_contract.lighting_key is not None
        assert shot_contract.lighting_direction is not None
    
    def test_planner_creates_prompt_pack_with_english_prompts_only(self):
        """Test that planner creates prompt_pack with English prompts only."""
        planner = GorynychPlanner()
        raw_scenario = "Test scenario"
        story_contract = planner.build_story_contract(raw_scenario)
        character_canon = planner.build_character_canon(story_contract)
        scene_plan = list(story_contract.scene_plans.values())[0]
        
        prompt_pack = planner.build_prompt_pack(scene_plan, character_canon)
        
        assert isinstance(prompt_pack, PromptPack)
        assert prompt_pack.language_requirement == "en"
        assert len(prompt_pack.beat_prompts) > 0
        # Validate that prompts are English (ASCII)
        assert prompt_pack.validate_language() is True
    
    def test_planner_does_not_call_comfyui_or_subprocess(self):
        """Test that planner does not call ComfyUI or subprocess."""
        planner = GorynychPlanner()
        
        # Patch subprocess to detect any calls
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")) as mock_subprocess:
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Run planner methods
                raw_scenario = "Test scenario"
                story_contract = planner.build_story_contract(raw_scenario)
                character_canon = planner.build_character_canon(story_contract)
                reference_lock = planner.build_reference_lock_contract(character_canon)
                
                scene_plan = list(story_contract.scene_plans.values())[0]
                shot_contract = planner.build_shot_contract(
                    scene_plan, 
                    character_canon, 
                    planner.head_3_knowledge
                )
                prompt_pack = planner.build_prompt_pack(scene_plan, character_canon)
                
                # If we get here, no subprocess was called
                assert mock_subprocess.call_count == 0
        
        # Verify artifacts were created without subprocess
        assert isinstance(story_contract, StoryContract)
        assert isinstance(character_canon, CharacterCanon)
        assert isinstance(reference_lock, ReferenceLockContract)
        assert isinstance(shot_contract, ShotContract)
        assert isinstance(prompt_pack, PromptPack)
