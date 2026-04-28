"""
Tests for Generic Reference Lock Gate.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from app.control.reference_lock_gate import ReferenceLockGate, GateDecision


class TestGenericReferenceLockGate:
    """Test ReferenceLockGate functionality with generic character registry."""
    
    @pytest.fixture
    def gate(self):
        """Create a gate with actual data directory."""
        return ReferenceLockGate(base_data_dir="data")
    
    @pytest.fixture
    def popadanka_project_dir(self):
        """Use actual Popadanka/Erdan project directory."""
        return Path("data/projects/popadanka_erdan")
    
    def test_gate_allows_generation_for_prompt_pack_containing_only_alya(
        self, gate, popadanka_project_dir
    ):
        """Test that gate allows generation for prompt_pack containing only Alya."""
        prompt_pack = {
            "character_id": "alya",
        }
        
        decision = gate.can_generate_prompt_pack(popadanka_project_dir, prompt_pack)
        
        assert decision.allowed is True
        assert "approved" in decision.reason.lower()
        assert "alya" in decision.checked_characters
    
    def test_gate_denies_generation_for_prompt_pack_containing_kael(
        self, gate, popadanka_project_dir
    ):
        """Test that gate denies generation for prompt_pack containing Kael."""
        prompt_pack = {
            "character_id": "kael",
        }
        
        decision = gate.can_generate_prompt_pack(popadanka_project_dir, prompt_pack)
        
        assert decision.allowed is False
        assert "kael" in decision.missing_references or "kael" in decision.reason.lower()
    
    def test_gate_denies_generation_for_prompt_pack_containing_alya_plus_kael(
        self, gate, popadanka_project_dir
    ):
        """Test that gate denies generation for prompt_pack containing Alya + Kael."""
        prompt_pack = {
            "characters": ["alya", "kael"],
        }
        
        decision = gate.can_generate_prompt_pack(popadanka_project_dir, prompt_pack)
        
        assert decision.allowed is False
        assert "kael" in decision.missing_references
    
    def test_gate_denies_unknown_character(self, gate, popadanka_project_dir):
        """Test that gate denies unknown character."""
        decision = gate.can_generate_character(popadanka_project_dir, "unknown_character")
        
        assert decision.allowed is False
        assert "not found in registry" in decision.reason.lower()
    
    def test_gate_is_not_hardcoded_to_alya_temp_project_hero_01_approved(
        self, tmp_path
    ):
        """Test that gate is not hardcoded to Alya: create temp project with character_id="hero_01" and approved lock, expect allow."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "test_project" / "output" / "control"
            project_dir.mkdir(parents=True)
            
            # Create character registry with hero_01
            character_registry = {
                "characters": [
                    {
                        "character_id": "hero_01",
                        "name": "Hero 01",
                        "role": "protagonist",
                        "reference_required": True,
                        "status": "approved"
                    }
                ]
            }
            (project_dir / "character_registry.json").write_text(
                json.dumps(character_registry), encoding='utf-8'
            )
            
            # Create reference lock directory
            reference_locks_dir = project_dir / "reference_locks"
            reference_locks_dir.mkdir()
            
            # Create approved reference lock for hero_01
            hero_lock = {
                "character_id": "hero_01",
                "reference_lock_status": "approved",
                "downstream_generation_allowed": True,
                "approved_references": ["ref_hero_01_main"],
                "primary_identity_reference": {
                    "reference_id": "ref_hero_01_main",
                    "filename": "hero01.png",
                    "type": "reference_sheet",
                    "approved_for": ["identity", "face"]
                },
                "prompt_anchor_en": "Hero character with distinctive features"
            }
            (reference_locks_dir / "hero_01_reference_lock.json").write_text(
                json.dumps(hero_lock), encoding='utf-8'
            )
            
            temp_gate = ReferenceLockGate(base_data_dir=str(tmp_path))
            decision = temp_gate.can_generate_character(tmp_path / "test_project", "hero_01")
            
            assert decision.allowed is True
            assert "approved" in decision.reason.lower()
            assert "hero_01" in decision.checked_characters
    
    def test_gate_denies_temp_project_hero_01_when_lock_missing(self, tmp_path):
        """Test that gate denies temp project hero_01 when lock missing."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "test_project" / "output" / "control"
            project_dir.mkdir(parents=True)
            
            # Create character registry with hero_01
            character_registry = {
                "characters": [
                    {
                        "character_id": "hero_01",
                        "name": "Hero 01",
                        "role": "protagonist",
                        "reference_required": True,
                        "status": "approved"
                    }
                ]
            }
            (project_dir / "character_registry.json").write_text(
                json.dumps(character_registry), encoding='utf-8'
            )
            
            # Create reference lock directory but do NOT create lock file
            reference_locks_dir = project_dir / "reference_locks"
            reference_locks_dir.mkdir()
            
            temp_gate = ReferenceLockGate(base_data_dir=str(tmp_path))
            decision = temp_gate.can_generate_character(tmp_path / "test_project", "hero_01")
            
            assert decision.allowed is False
            assert "missing" in decision.reason.lower() or "hero_01_reference_lock" in decision.reason.lower()
    
    def test_does_not_call_comfyui_or_subprocess(self, gate, popadanka_project_dir):
        """Test that no ComfyUI or subprocess is called."""
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")):
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Run gate checks
                decision = gate.can_generate_character(popadanka_project_dir, "alya")
                
                prompt_pack = {"character_id": "alya"}
                decision2 = gate.can_generate_prompt_pack(popadanka_project_dir, prompt_pack)
                
                # If we get here, no subprocess was called
                assert True  # No assertion needed, just reaching here means success
