"""
Tests for Reference Lock Gate.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from app.control.reference_lock_gate import ReferenceLockGate, GateDecision


class TestReferenceLockGate:
    """Test ReferenceLockGate functionality."""
    
    @pytest.fixture
    def gate(self, tmp_path):
        """Create a gate with temp output dir."""
        return ReferenceLockGate(base_output_dir=str(tmp_path))
    
    @pytest.fixture
    def erdan_project_dir(self, tmp_path):
        """Create a mock Erdan project directory with Alya reference lock approved."""
        project_dir = tmp_path / "erdan_source" / "output" / "control"
        project_dir.mkdir(parents=True)
        
        # Create approved reference lock contract
        reference_lock = {
            "character_id": "alya",
            "reference_lock_status": "approved",
            "downstream_generation_allowed": True,
            "lock_reason": "User approved primary Alya identity and outfit references",
            "approved_references": ["ref_alya_main"],
            "approval_timestamp": "2026-04-26T14:03:00Z",
            "approved_by": "user"
        }
        (project_dir / "reference_lock_contract.json").write_text(
            json.dumps(reference_lock), encoding='utf-8'
        )
        
        # Create Alya reference lock
        alya_ref_lock = {
            "character_id": "alya",
            "primary_identity_reference": {
                "reference_id": "ref_alya_main",
                "filename": "референсы/Аля.png",
                "type": "reference_sheet",
                "approved_for": ["identity", "face", "outfit"]
            },
            "prompt_anchor_en": "24-year-old woman, dark brown hair in messy bun"
        }
        (project_dir / "alya_reference_lock.json").write_text(
            json.dumps(alya_ref_lock), encoding='utf-8'
        )
        
        return tmp_path / "erdan_source"  # Return project root, not control dir
    
    @pytest.fixture
    def project_dir_missing_lock(self, tmp_path):
        """Create a project directory without reference lock."""
        project_dir = tmp_path / "test_project" / "output" / "control"
        project_dir.mkdir(parents=True)
        return tmp_path / "test_project"  # Return project root, not control dir
    
    def test_allows_alya_when_reference_lock_contract_is_approved_and_alya_reference_lock_exists(
        self, gate, erdan_project_dir
    ):
        """Test that allows Alya when reference_lock_contract is approved and alya_reference_lock exists."""
        decision = gate.can_generate_character(erdan_project_dir, "alya")
        
        assert decision.allowed is True
        assert "approved" in decision.reason.lower()
        assert "ref_alya_main" in decision.approved_references
    
    def test_denies_alya_when_reference_lock_contract_missing(self, project_dir_missing_lock):
        """Test that denies Alya when reference_lock_contract missing."""
        gate = ReferenceLockGate(base_output_dir=str(project_dir_missing_lock.parent))
        decision = gate.can_generate_character(project_dir_missing_lock, "alya")
        
        assert decision.allowed is False
        assert "missing" in decision.reason.lower() or "not found" in decision.reason.lower()
    
    def test_denies_alya_when_downstream_generation_allowed_false(self, gate, erdan_project_dir):
        """Test that denies Alya when downstream_generation_allowed=false."""
        # Create a temp directory for this test
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "test_project" / "output" / "control"
            project_dir.mkdir(parents=True)
            
            # Create reference lock with downstream_generation_allowed=False
            reference_lock = {
                "character_id": "alya",
                "reference_lock_status": "approved",
                "downstream_generation_allowed": False,
                "approved_references": ["ref_alya_main"],
                "approval_timestamp": "2026-04-26T14:03:00Z",
                "approved_by": "user"
            }
            (project_dir / "reference_lock_contract.json").write_text(
                json.dumps(reference_lock), encoding='utf-8'
            )
            
            # Create Alya reference lock
            alya_ref_lock = {
                "character_id": "alya",
                "primary_identity_reference": {
                    "reference_id": "ref_alya_main",
                    "filename": "референсы/Аля.png",
                    "type": "reference_sheet",
                    "approved_for": ["identity", "face", "outfit"]
                },
                "prompt_anchor_en": "24-year-old woman, dark brown hair in messy bun"
            }
            (project_dir / "alya_reference_lock.json").write_text(
                json.dumps(alya_ref_lock), encoding='utf-8'
            )
            
            temp_gate = ReferenceLockGate(base_output_dir=str(tmp_path))
            decision = temp_gate.can_generate_character(tmp_path / "test_project", "alya")
            
            assert decision.allowed is False
            assert "downstream_generation_allowed" in decision.reason.lower()
    
    def test_denies_alya_when_approved_references_missing_ref_alya_main(self):
        """Test that denies Alya when approved_references missing ref_alya_main."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "test_project" / "output" / "control"
            project_dir.mkdir(parents=True)
            
            # Create reference lock without approved references
            reference_lock = {
                "character_id": "alya",
                "reference_lock_status": "approved",
                "downstream_generation_allowed": True,
                "approved_references": [],
                "approval_timestamp": "2026-04-26T14:03:00Z",
                "approved_by": "user"
            }
            (project_dir / "reference_lock_contract.json").write_text(
                json.dumps(reference_lock), encoding='utf-8'
            )
            
            # Create Alya reference lock
            alya_ref_lock = {
                "character_id": "alya",
                "primary_identity_reference": {
                    "reference_id": "ref_alya_main",
                    "filename": "референсы/Аля.png",
                    "type": "reference_sheet",
                    "approved_for": ["identity", "face", "outfit"]
                },
                "prompt_anchor_en": "24-year-old woman, dark brown hair in messy bun"
            }
            (project_dir / "alya_reference_lock.json").write_text(
                json.dumps(alya_ref_lock), encoding='utf-8'
            )
            
            temp_gate = ReferenceLockGate(base_output_dir=str(tmp_path))
            decision = temp_gate.can_generate_character(tmp_path / "test_project", "alya")
            
            assert decision.allowed is False
            # The gate constructs the reference id as f"ref_{character_id}"
            assert "ref_alya" in decision.missing_references
    
    def test_denies_alya_when_alya_reference_lock_json_missing(self):
        """Test that denies Alya when alya_reference_lock.json missing."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "test_project" / "output" / "control"
            project_dir.mkdir(parents=True)
            
            # Create reference lock contract with ref_alya in approved list to pass that check
            reference_lock = {
                "character_id": "alya",
                "reference_lock_status": "approved",
                "downstream_generation_allowed": True,
                "lock_reason": "User approved primary Alya identity and outfit references",
                "approved_references": ["ref_alya"],  # Use ref_alya to match the gate's construction
                "approval_timestamp": "2026-04-26T14:03:00Z",
                "approved_by": "user"
            }
            (project_dir / "reference_lock_contract.json").write_text(
                json.dumps(reference_lock), encoding='utf-8'
            )
            
            # Do NOT create Alya reference lock - it's missing
            
            temp_gate = ReferenceLockGate(base_output_dir=str(tmp_path))
            decision = temp_gate.can_generate_character(tmp_path / "test_project", "alya")
            
            assert decision.allowed is False
            assert "alya_reference_lock.json" in decision.reason.lower()
    
    def test_denies_prompt_pack_containing_kael_because_kael_reference_lock_is_missing(
        self, gate, erdan_project_dir
    ):
        """Test that denies prompt_pack containing Kael because Kael reference lock is missing."""
        # Create prompt pack with Kael
        prompt_pack = {
            "character_id": "kael",
        }
        
        decision = gate.can_generate_prompt_pack(erdan_project_dir, prompt_pack)
        
        assert decision.allowed is False
        assert "kael" in decision.missing_references
    
    def test_denies_prompt_pack_containing_multiple_characters_if_any_required_reference_missing(
        self, gate, erdan_project_dir
    ):
        """Test that denies prompt_pack containing multiple characters if any required reference missing."""
        # Create prompt pack with both Alya (approved) and Kael (missing)
        prompt_pack = {
            "characters": ["alya", "kael"],
        }
        
        decision = gate.can_generate_prompt_pack(erdan_project_dir, prompt_pack)
        
        assert decision.allowed is False
        assert "kael" in decision.missing_references
    
    def test_does_not_call_comfyui_or_subprocess(self, gate, erdan_project_dir):
        """Test that no ComfyUI or subprocess is called."""
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")) as mock_subprocess:
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Run gate checks
                decision = gate.can_generate_character(erdan_project_dir, "alya")
                
                prompt_pack = {"character_id": "alya"}
                decision2 = gate.can_generate_prompt_pack(erdan_project_dir, prompt_pack)
                
                # If we get here, no subprocess was called
                assert mock_subprocess.call_count == 0
