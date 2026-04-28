"""
Tests for GORYNYCH ep01 production artifacts.
"""

import pytest
import json
from pathlib import Path

from app.gorynych.contracts import (
    StoryContract,
    CharacterCanon,
    ReferenceLockContract,
    PromptPack,
)


class TestEp01Artifacts:
    """Test that ep01 artifacts are production-aligned for Alya."""
    
    @pytest.fixture
    def output_dir(self):
        """Get the output directory for ep01 artifacts."""
        return Path("data/gorynych_ep01/output/control")
    
    @pytest.fixture
    def story_contract(self, output_dir):
        """Load story contract."""
        with open(output_dir / "story_contract.json", 'r') as f:
            data = json.load(f)
        return StoryContract.from_dict(data)
    
    @pytest.fixture
    def character_canon(self, output_dir):
        """Load character canon."""
        with open(output_dir / "character_canon.json", 'r') as f:
            data = json.load(f)
        return CharacterCanon.from_dict(data)
    
    @pytest.fixture
    def reference_lock(self, output_dir):
        """Load reference lock contract."""
        with open(output_dir / "reference_lock_contract.json", 'r') as f:
            data = json.load(f)
        return ReferenceLockContract.from_dict(data)
    
    @pytest.fixture
    def beat_specs(self, output_dir):
        """Load beat specs."""
        with open(output_dir / "beat_specs.json", 'r') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def prompt_pack(self, output_dir):
        """Load prompt pack."""
        with open(output_dir / "prompt_pack.json", 'r') as f:
            data = json.load(f)
        return PromptPack.from_dict(data)
    
    def test_ep01_artifacts_are_about_alya_not_alex(self, story_contract, character_canon):
        """Test that ep01 artifacts are about Alya, not Alex."""
        assert story_contract.protagonist == "Alya"
        assert character_canon.name == "Alya"
        assert "Alex" not in story_contract.title
        assert "Alex" not in character_canon.name
    
    def test_character_canon_contains_all_required_immutable_anchors(self, character_canon):
        """Test that character_canon contains all required immutable anchors."""
        assert len(character_canon.immutable_anchors) > 0
        
        # Check for required distinctive features
        assert "dark brown hair in messy bun" in character_canon.distinctive_features
        assert "pale skin" in character_canon.distinctive_features
        assert "dark tired eyes" in character_canon.distinctive_features
        assert "tired worried sharp expression" in character_canon.distinctive_features
        
        # Check costume
        assert "gray oversized hoodie" in character_canon.costume_primary.lower()
        
        # Check forbidden drift
        assert len(character_canon.forbidden_drift) > 0
        
        # Check reference_required
        assert character_canon.reference_required is True
    
    def test_reference_lock_contract_blocks_downstream_and_has_approval_timestamp_null_when_not_approved(
        self, reference_lock
    ):
        """Test that reference_lock_contract blocks downstream and has approval_timestamp=null when not approved."""
        assert reference_lock.downstream_generation_allowed is False
        assert reference_lock.approval_timestamp is None
        assert reference_lock.approved_by is None
        assert reference_lock.lock_reason is not None
    
    def test_beat_specs_contains_exactly_3_required_beats(self, beat_specs):
        """Test that beat_specs contains exactly 3 required beats."""
        assert len(beat_specs) == 3
        
        beat_ids = [beat["beat_id"] for beat in beat_specs]
        assert "beat_01_reach_phone" in beat_ids
        assert "beat_02_alarm_screen" in beat_ids
        assert "beat_03_error_screen" in beat_ids
    
    def test_prompt_pack_is_beat_level_and_contains_exactly_3_beat_prompts(self, prompt_pack):
        """Test that prompt_pack is beat-level and contains exactly 3 beat prompts."""
        assert len(prompt_pack.beat_prompts) == 3
        
        beat_ids = [bp.beat_id for bp in prompt_pack.beat_prompts]
        assert "beat_01_reach_phone" in beat_ids
        assert "beat_02_alarm_screen" in beat_ids
        assert "beat_03_error_screen" in beat_ids
    
    def test_every_generation_prompt_is_english_only(self, prompt_pack):
        """Test that every generation prompt is English-only."""
        assert prompt_pack.validate_language() is True
        
        for bp in prompt_pack.beat_prompts:
            # Check ASCII encoding
            bp.positive_prompt.encode('ascii')
            bp.negative_prompt.encode('ascii')
            bp.continuity_prompt.encode('ascii')
    
    def test_prompt_pack_uses_deterministic_per_shot_seed_policy(self, prompt_pack):
        """Test that prompt_pack uses deterministic_per_shot seed policy."""
        assert prompt_pack.validate_seed_policy() is True
        assert prompt_pack.seed_policy["mode"] == "deterministic_per_shot"
        assert prompt_pack.seed_policy["character_seed"] == 747001
        assert prompt_pack.seed_policy["allow_random_seed"] is False
    
    def test_no_prompt_pack_uses_controlled_random(self, prompt_pack):
        """Test that no prompt_pack uses controlled_random."""
        # The seed policy should be a dict, not a string
        assert isinstance(prompt_pack.seed_policy, dict)
        assert prompt_pack.seed_policy.get("mode") != "controlled_random"
    
    def test_technical_params_do_not_exceed_safe_local_profile(self, prompt_pack):
        """Test that technical_params do not exceed safe local profile: width <= 640 and height <= 640."""
        assert prompt_pack.validate_safe_resolution() is True
        
        for bp in prompt_pack.beat_prompts:
            assert bp.width <= 640
            assert bp.height <= 640
    
    def test_each_beat_contains_camera_angle_focal_length_mm_lighting_scheme_color_grade(self, prompt_pack):
        """Test that each beat contains camera_angle, focal_length_mm, lighting_scheme, color_grade."""
        for bp in prompt_pack.beat_prompts:
            assert bp.camera_angle is not None
            assert bp.focal_length_mm is not None
            assert bp.lighting_scheme is not None
            assert bp.color_grade is not None
