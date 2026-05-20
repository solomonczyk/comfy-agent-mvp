"""
Tests for Identity/Environment Idempotency Lock system.
"""

import os
import json
import pytest
from pathlib import Path


class TestIdempotencyLockSystem:
    """Test suite for identity/environment idempotency lock system."""
    
    @pytest.fixture
    def project_root(self):
        return Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
    
    @pytest.fixture
    def idempotency_lock_dir(self, project_root):
        return project_root / "output" / "control" / "identity_environment_lock"
    
    def test_character_lock_registry_exists(self, idempotency_lock_dir):
        """Test that character_lock_registry.json exists."""
        registry_path = idempotency_lock_dir / "character_lock_registry.json"
        assert registry_path.exists(), "Character lock registry must exist"
    
    def test_character_lock_registry_has_canonical_asset(self, idempotency_lock_dir):
        """Test that character lock registry has canonical character asset."""
        registry_path = idempotency_lock_dir / "character_lock_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        
        assert registry["canonical_character_asset"]["filename"] == "identity_lock__00001_.png"
        assert registry["character_lock_id"] == "char_lock_001"
        assert registry["lock_status"] == "active"
        assert registry["lock_enforced"] == True
    
    def test_character_lock_registry_blocks_random_identity(self, idempotency_lock_dir):
        """Test that character lock registry blocks random identity generation."""
        registry_path = idempotency_lock_dir / "character_lock_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        
        assert registry["random_identity_generation_blocked"] == True
        assert registry["generation_requirements"]["canonical_character_asset_required"] == True
    
    def test_environment_lock_registry_exists(self, idempotency_lock_dir):
        """Test that environment_lock_registry.json exists."""
        registry_path = idempotency_lock_dir / "environment_lock_registry.json"
        assert registry_path.exists(), "Environment lock registry must exist"
    
    def test_environment_lock_registry_has_canonical_asset(self, idempotency_lock_dir):
        """Test that environment lock registry has canonical environment asset."""
        registry_path = idempotency_lock_dir / "environment_lock_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        
        assert registry["canonical_environment_asset"]["filename"] == "corrective_visual_recovery__00001_.png"
        assert registry["environment_lock_id"] == "env_lock_001"
        assert registry["scene_id"] == "scene_rc2_multishot1_ep01"
        assert registry["lock_status"] == "active"
        assert registry["lock_enforced"] == True
    
    def test_environment_lock_registry_blocks_random_environment(self, idempotency_lock_dir):
        """Test that environment lock registry blocks random environment generation."""
        registry_path = idempotency_lock_dir / "environment_lock_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        
        assert registry["random_environment_generation_blocked"] == True
        assert registry["same_scene_idempotency_enforced"] == True
        assert registry["generation_requirements"]["canonical_environment_asset_required"] == True
    
    def test_scene_idempotency_policy_exists(self, idempotency_lock_dir):
        """Test that scene_idempotency_policy.json exists."""
        policy_path = idempotency_lock_dir / "scene_idempotency_policy.json"
        assert policy_path.exists(), "Scene idempotency policy must exist"
    
    def test_scene_idempotency_policy_requires_workflow_proof(self, idempotency_lock_dir):
        """Test that scene idempotency policy requires workflow proof."""
        policy_path = idempotency_lock_dir / "scene_idempotency_policy.json"
        with open(policy_path) as f:
            policy = json.load(f)
        
        proof = policy["workflow_proof_required"]
        assert proof["canonical_character_asset_used"] == True
        assert proof["character_lock_id"] == "char_lock_001"
        assert proof["environment_lock_id"] == "env_lock_001"
        assert proof["scene_id"] == "scene_rc2_multishot1_ep01"
        assert proof["same_scene_idempotency_enforced"] == True
        assert proof["random_identity_generation_blocked"] == True
        assert proof["random_environment_generation_blocked"] == True
    
    def test_scene_idempotency_policy_blocks_generation_without_locks(self, idempotency_lock_dir):
        """Test that policy blocks generation without canonical locks."""
        policy_path = idempotency_lock_dir / "scene_idempotency_policy.json"
        with open(policy_path) as f:
            policy = json.load(f)
        
        blocking = policy["blocking_conditions"]
        assert blocking["generation_without_canonical_character_blocked"] == True
        assert blocking["generation_without_canonical_environment_blocked"] == True
        assert blocking["generation_without_scene_id_blocked"] == True
    
    def test_canonical_reference_contact_sheet_exists(self, idempotency_lock_dir):
        """Test that canonical_reference_contact_sheet.jpg exists."""
        contact_sheet_path = idempotency_lock_dir / "canonical_reference_contact_sheet.jpg"
        assert contact_sheet_path.exists(), "Canonical reference contact sheet must exist"
        assert os.access(contact_sheet_path, os.R_OK), "Contact sheet must be readable"
    
    def test_generation_preflight_idempotency_gate_exists(self, idempotency_lock_dir):
        """Test that generation_preflight_idempotency_gate.json exists."""
        gate_path = idempotency_lock_dir / "generation_preflight_idempotency_gate.json"
        assert gate_path.exists(), "Generation preflight idempotency gate must exist"
    
    def test_generation_preflight_gate_blocks_invalid_generation(self, idempotency_lock_dir):
        """Test that preflight gate blocks generation without idempotency locks."""
        gate_path = idempotency_lock_dir / "generation_preflight_idempotency_gate.json"
        with open(gate_path) as f:
            gate = json.load(f)
        
        assert gate["gate_status"] == "active"
        assert gate["authorization"]["blocking_mode"] == True
        assert gate["authorization"]["gate_enabled"] == True
    
    def test_state_reflects_idempotency_lock_implementation(self, project_root):
        """Test that state.json reflects idempotency lock implementation."""
        state_path = project_root / "output" / "control" / "state.json"
        with open(state_path) as f:
            state = json.load(f)
        
        assert state["idempotency_lock_executed"] == True
        assert state["character_lock_registry_created"] == True
        assert state["environment_lock_registry_created"] == True
        assert state["scene_idempotency_policy_created"] == True
        assert state["canonical_reference_contact_sheet_created"] == True
        assert state["generation_preflight_idempotency_gate_created"] == True
        assert state["character_lock_id"] == "char_lock_001"
        assert state["environment_lock_id"] == "env_lock_001"
        assert state["scene_id"] == "scene_rc2_multishot1_ep01"
        assert state["canonical_character_asset_used"] == True
        assert state["same_scene_idempotency_enforced"] == True
        assert state["random_identity_generation_blocked"] == True
        assert state["random_environment_generation_blocked"] == True
    
    def test_no_generation_performed_in_idempotency_task(self, project_root):
        """Test that no generation was performed during idempotency lock task."""
        state_path = project_root / "output" / "control" / "state.json"
        with open(state_path) as f:
            state = json.load(f)
        
        # The idempotency lock task should not have performed any generation
        assert state.get("idempotency_lock_task_id") == "RC-COMBINE-V2-IDENTITY-ENVIRONMENT-IDEMPOTENCY-LOCK-001"
        # Verify production_accepted remains false
        assert state["production_accepted"] == False
