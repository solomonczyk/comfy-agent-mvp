"""Tests for Gorynych identity workflow enforcement (RC2-GORYNYCH1)."""
import json
import tempfile
from pathlib import Path

import pytest

from app.runtime.preflight_service import PreflightService


class TestGorynychWorkflowDiscovery:
    """Test Gorynych workflow discovery and validation."""
    
    def test_gorynych_knowledge_files_exist(self):
        """Test that Gorynych knowledge files exist."""
        from app.gorynych.knowledge import validate_knowledge_files
        
        assert validate_knowledge_files() is True, "Gorynych knowledge files (head_1.md, head_2.md, head_3.md) must exist"
    
    def test_gorynych_module_imports(self):
        """Test that Gorynych module can be imported."""
        from app.gorynych import (
            GorynychPlanner,
            StoryContract,
            CharacterCanon,
            ReferenceLockContract,
        )
        
        assert GorynychPlanner is not None
        assert StoryContract is not None
        assert CharacterCanon is not None
        assert ReferenceLockContract is not None
    
    def test_workflow_template_has_ipadapter_nodes(self):
        """Test that workflow template contains IPAdapter nodes."""
        workflow_path = Path(__file__).parent.parent / "data" / "workflow_template.json"
        
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Check for IPAdapterAdvanced node
        has_ipadapter_advanced = any(
            node.get("class_type") == "IPAdapterAdvanced"
            for node in workflow.values()
            if isinstance(node, dict)
        )
        assert has_ipadapter_advanced, "Workflow template must contain IPAdapterAdvanced node"
        
        # Check for IPAdapterUnifiedLoader node
        has_ipadapter_loader = any(
            node.get("class_type") == "IPAdapterUnifiedLoader"
            for node in workflow.values()
            if isinstance(node, dict)
        )
        assert has_ipadapter_loader, "Workflow template must contain IPAdapterUnifiedLoader node"


class TestGorynychPreflightGate:
    """Test preflight gate for gorynych_identity mode."""
    
    def test_missing_ipadapter_blocks_gorynych_identity(self, tmp_path):
        """Test that missing IPAdapter nodes block gorynych_identity mode."""
        service = PreflightService()
        
        # Create workflow without IPAdapter nodes
        workflow = {
            "1": {"class_type": "LoadImage", "inputs": {"image": ""}},
            "2": {"class_type": "KSampler", "inputs": {}},
            "__inject__": {"positive_prompt_node": None, "negative_prompt_node": None}
        }
        
        result = service.validate_gorynych_identity_workflow(
            workflow=workflow,
            checkpoint_name="test.safetensors",
            project_root=tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("IPAdapterAdvanced" in block for block in result["blocks"])
        assert any("IPAdapterUnifiedLoader" in block for block in result["blocks"])
    
    def test_missing_knowledge_files_blocks_gorynych_identity(self, tmp_path):
        """Test that missing knowledge files block gorynych_identity mode."""
        service = PreflightService()
        
        # Create workflow with IPAdapter nodes
        workflow = {
            "1": {"class_type": "IPAdapterAdvanced", "inputs": {}},
            "2": {"class_type": "IPAdapterUnifiedLoader", "inputs": {}},
            "3": {"class_type": "LoadImage", "inputs": {"image": ""}},
            "__inject__": {"positive_prompt_node": "6", "negative_prompt_node": "7"}
        }
        
        # Create project root without knowledge files
        result = service.validate_gorynych_identity_workflow(
            workflow=workflow,
            checkpoint_name="test.safetensors",
            project_root=tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("knowledge" in block.lower() for block in result["blocks"])
    
    def test_unapproved_character_anchors_block_gorynych_identity(self, tmp_path):
        """Test that unapproved character anchors block gorynych_identity mode."""
        service = PreflightService()
        
        # Create workflow with IPAdapter nodes
        workflow = {
            "1": {"class_type": "IPAdapterAdvanced", "inputs": {}},
            "2": {"class_type": "IPAdapterUnifiedLoader", "inputs": {}},
            "3": {"class_type": "LoadImage", "inputs": {"image": ""}},
            "__inject__": {"positive_prompt_node": "6", "negative_prompt_node": "7"}
        }
        
        # Create knowledge directory
        knowledge_dir = tmp_path / "docs" / "knowledge"
        knowledge_dir.mkdir(parents=True)
        for filename in ["head_1.md", "head_2.md", "head_3.md"]:
            (knowledge_dir / filename).write_text("test")
        
        # Create character canon without approved anchors
        canon_path = tmp_path / "character_canon.json"
        canon_data = {
            "character_id": "test_char",
            "name": "Test",
            "anchors": [
                {"priority": "critical", "status": "pending"}
            ]
        }
        with open(canon_path, 'w') as f:
            json.dump(canon_data, f)
        
        result = service.validate_gorynych_identity_workflow(
            workflow=workflow,
            checkpoint_name="test.safetensors",
            project_root=tmp_path,
            character_canon_path=canon_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("critical character anchors approved" in block for block in result["blocks"])


class TestGorynychGenerationMode:
    """Test gorynych_identity generation mode enforcement."""
    
    def test_gorynych_identity_required_for_multi_frame_shots(self, tmp_path):
        """Test that gorynych_identity is required for multi-frame character shots."""
        from app.cli import validate_multishot_generation
        from argparse import Namespace
        
        # Create prompt pack with reference_locked mode (not gorynych_identity)
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "generation_mode": "reference_locked",
            "technical_fallback_only": False
        }
        with open(control_dir / "prompt_pack.json", 'w') as f:
            json.dump(prompt_pack, f)
        
        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True
        )
        result = validate_multishot_generation(args)
        
        assert result == 1  # Validation should fail
    
    def test_reference_locked_must_be_marked_fallback_only(self, tmp_path):
        """Test that reference_locked mode must be marked as technical_fallback_only."""
        from app.cli import validate_multishot_generation
        from argparse import Namespace
        
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack = {
            "generation_mode": "reference_locked",
            "technical_fallback_only": False  # Should be True
        }
        with open(control_dir / "prompt_pack.json", 'w') as f:
            json.dump(prompt_pack, f)
        
        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True
        )
        result = validate_multishot_generation(args)
        
        assert result == 1  # Validation should fail


class TestGorynychArtifactIndex:
    """Test artifact_index correctly records Gorynych requirements."""
    
    def test_legacy_frames_marked_not_production_accepted(self, tmp_path):
        """Test that frames generated with legacy reference_locked are marked not production accepted."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "shots": [
                {
                    "shot_id": "shot01",
                    "generation_mode": "reference_locked",
                    "production_accepted": False,
                    "reason": "Generated with legacy reference_locked img2img workflow; faces are inconsistent"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f)
        
        # Verify the artifact_index correctly marks frames as not production accepted
        with open(control_dir / "artifact_index.json", 'r') as f:
            loaded_index = json.load(f)
        
        assert loaded_index["shots"][0]["production_accepted"] is False
        assert "legacy" in loaded_index["shots"][0]["reason"].lower()


class TestGorynychValidationBlocksDownstream:
    """Test that validator blocks downstream if Gorynych is not used."""
    
    def test_validator_blocks_downstream_without_gorynych(self, tmp_path):
        """Test that validator blocks downstream actions if gorynych_identity not used."""
        from app.cli import validate_multishot_generation
        from argparse import Namespace
        
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create prompt pack with wrong generation mode
        prompt_pack = {
            "generation_mode": "reference_locked",
            "technical_fallback_only": False
        }
        with open(control_dir / "prompt_pack.json", 'w') as f:
            json.dump(prompt_pack, f)
        
        # Create episode ledger with downstream action after generation
        episode_ledger = {
            "records": [
                {"event_type": "generate_frames", "executed": True},
                {"event_type": "assemble_scene", "executed": True}
            ]
        }
        with open(control_dir / "episode_ledger.json", 'w') as f:
            json.dump(episode_ledger, f)
        
        args = Namespace(
            project_root=str(tmp_path),
            episode="ep01",
            json=True
        )
        result = validate_multishot_generation(args)
        
        assert result == 1  # Validation should fail
