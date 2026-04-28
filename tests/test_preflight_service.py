"""RC-RUNTIME1 — Tests for PreflightService."""
import pytest
import tempfile
from pathlib import Path

from app.runtime.checkpoint_resolver import CheckpointResolverLite
from app.runtime.preflight_service import PreflightService
from app.runtime.resize_selector import ResizeNodeSelector
from app.runtime.schema_registry import ComfyNodeSchemaRegistry


class TestPreflightService:
    """Tests for PreflightService."""
    
    def test_validate_reference_locked_workflow_ready(self, tmp_path):
        """Test validate_reference_locked_workflow returns READY for valid workflow."""
        # Create a safe checkpoints directory structure
        checkpoints_dir = tmp_path / "models" / "checkpoints"
        checkpoints_dir.mkdir(parents=True)
        
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {"image": "output/control/test.png"}},
            "6": {"class_type": "ImageScale", "inputs": {"image": ["5", 0]}},
            "8": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["4", 2]}},
            "3": {"class_type": "KSampler", "inputs": {"latent_image": ["8", 0]}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
        }
        
        # Create dummy checkpoint in safe location
        (checkpoints_dir / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "VAEDecode": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=checkpoints_dir)
        
        # Mock is_safe_path to return True for test
        checkpoint_resolver.is_safe_path = lambda x: True
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        # Use a safe project root that doesn't trigger pytest temp check
        project_root = Path("F:/ComfyUI/project")
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", project_root
        )
        
        if result["status"] != "READY":
            print(f"Blocks: {result['blocks']}")
        
        assert result["status"] == "READY"
        assert result["blocks"] == []
    
    def test_validate_reference_locked_workflow_blocks_missing_loadimage(self, tmp_path):
        """Test validate_reference_locked_workflow blocks missing LoadImage."""
        workflow = {
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "VAEEncode": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Missing LoadImage" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_missing_resize(self, tmp_path):
        """Test validate_reference_locked_workflow blocks missing resize."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "VAEEncode": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Missing resize" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_missing_vaeencode(self, tmp_path):
        """Test validate_reference_locked_workflow blocks missing VAEEncode."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Missing VAEEncode" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_ksampler_emptylatent(self, tmp_path):
        """Test validate_reference_locked_workflow blocks KSampler connected to EmptyLatentImage."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "2": {"class_type": "EmptyLatentImage", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {"latent_image": ["2", 0]}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "EmptyLatentImage": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("EmptyLatentImage" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_missing_checkpoint(self, tmp_path):
        """Test validate_reference_locked_workflow blocks missing checkpoint."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "missing.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Missing checkpoint" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_unsafe_checkpoint_path(self, tmp_path):
        """Test validate_reference_locked_workflow blocks unsafe checkpoint path."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        # Create checkpoint in temp directory
        temp_dir = tmp_path / "Temp"
        temp_dir.mkdir()
        (temp_dir / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=temp_dir)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Unsafe checkpoint path" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_unsafe_reference_path(self, tmp_path):
        """Test validate_reference_locked_workflow blocks unsafe reference image path."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {"image": "C:\\Temp\\test.png"}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Unsafe reference image path" in block for block in result["blocks"])
    
    def test_validate_reference_locked_workflow_blocks_invalid_chain(self, tmp_path):
        """Test validate_reference_locked_workflow blocks invalid chain."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},  # Not connected to LoadImage
            "8": {"class_type": "VAEEncode", "inputs": {}},  # Not connected to ImageScale
            "3": {"class_type": "KSampler", "inputs": {}},  # Not connected to VAEEncode
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert result["status"] == "BLOCKED"
        assert any("Invalid reference_locked chain" in block for block in result["blocks"])
    
    def test_write_preflight_artifact(self, tmp_path):
        """Test write_preflight_artifact writes JSON file."""
        preflight_result = {
            "status": "READY",
            "blocks": [],
            "warnings": [],
        }
        
        schema_registry = ComfyNodeSchemaRegistry()
        checkpoint_resolver = CheckpointResolverLite()
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        artifact_path = service.write_preflight_artifact(
            preflight_result, tmp_path, "ep01", "shot01"
        )
        
        assert artifact_path.exists()
        assert artifact_path.name == "ep01_shot01_preflight.json"
        
        import json
        with open(artifact_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        assert loaded["status"] == "READY"
    
    def test_validate_reference_locked_workflow_includes_workflow_info(self, tmp_path):
        """Test that result includes workflow_info with node IDs."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert "workflow_info" in result
        assert result["workflow_info"]["load_image_nodes"] == ["5"]
        assert result["workflow_info"]["resize_nodes"] == ["6"]
        assert result["workflow_info"]["vae_encode_nodes"] == ["8"]
        assert result["workflow_info"]["ksampler_nodes"] == ["3"]
    
    def test_validate_reference_locked_workflow_includes_resize_node_type(self, tmp_path):
        """Test that result includes selected resize node type."""
        workflow = {
            "5": {"class_type": "LoadImage", "inputs": {}},
            "6": {"class_type": "ImageScale", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        schema_registry = ComfyNodeSchemaRegistry()
        schema_registry._object_info = {
            "LoadImage": {},
            "ImageScale": {},
            "VAEEncode": {},
            "KSampler": {},
        }
        
        checkpoint_resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        service = PreflightService(schema_registry, checkpoint_resolver)
        
        result = service.validate_reference_locked_workflow(
            workflow, "model.safetensors", tmp_path
        )
        
        assert "resize_node_type" in result
        assert result["resize_node_type"] == "ImageScale"
