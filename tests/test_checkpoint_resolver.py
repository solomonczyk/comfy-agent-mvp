"""RC-RUNTIME1 — Tests for CheckpointResolverLite."""
import pytest
from pathlib import Path
import tempfile

from app.runtime.checkpoint_resolver import CheckpointResolverLite


class TestCheckpointResolverLite:
    """Tests for CheckpointResolverLite."""
    
    def test_validate_checkpoint_valid(self, tmp_path):
        """Test validate_checkpoint when checkpoint exists."""
        resolver = CheckpointResolverLite(checkpoint_dir=tmp_path)
        
        # Create a dummy checkpoint file
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        result = resolver.validate_checkpoint("model.safetensors")
        assert result["valid"] is True
        assert result["checkpoint_name"] == "model.safetensors"
        assert result["exists"] is True
        assert result["error"] is None
    
    def test_validate_checkpoint_missing(self, tmp_path):
        """Test validate_checkpoint when checkpoint is missing."""
        resolver = CheckpointResolverLite(checkpoint_dir=tmp_path)
        
        result = resolver.validate_checkpoint("missing.safetensors")
        assert result["valid"] is False
        assert result["checkpoint_name"] == "missing.safetensors"
        assert result["exists"] is False
        assert result["error"] is not None
    
    def test_resolve_checkpoint_path_relative(self, tmp_path):
        """Test resolve_checkpoint_path with relative path."""
        resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        (tmp_path / "model.safetensors").write_bytes(b"fake checkpoint")
        
        path = resolver.resolve_checkpoint_path("model.safetensors")
        assert path.exists()
        assert path.name == "model.safetensors"
    
    def test_resolve_checkpoint_path_absolute(self, tmp_path):
        """Test resolve_checkpoint_path with absolute path."""
        resolver = CheckpointResolverLite()
        
        checkpoint_path = tmp_path / "model.safetensors"
        checkpoint_path.write_bytes(b"fake checkpoint")
        
        resolved = resolver.resolve_checkpoint_path(str(checkpoint_path))
        assert resolved == checkpoint_path.resolve()
    
    def test_resolve_checkpoint_path_raises_when_missing(self, tmp_path):
        """Test resolve_checkpoint_path raises when checkpoint is missing."""
        resolver = CheckpointResolverLite(checkpoint_dir=tmp_path)
        
        with pytest.raises(FileNotFoundError, match="Checkpoint not found"):
            resolver.resolve_checkpoint_path("missing.safetensors")
    
    def test_list_available_checkpoints(self, tmp_path):
        """Test list_available_checkpoints returns checkpoint files."""
        resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        (tmp_path / "model1.safetensors").write_bytes(b"fake")
        (tmp_path / "model2.ckpt").write_bytes(b"fake")
        (tmp_path / "model3.pth").write_bytes(b"fake")
        (tmp_path / "readme.txt").write_text("text")
        
        checkpoints = resolver.list_available_checkpoints()
        assert len(checkpoints) == 3
        assert "model1.safetensors" in checkpoints
        assert "model2.ckpt" in checkpoints
        assert "model3.pth" in checkpoints
        assert "readme.txt" not in checkpoints
    
    def test_list_available_checkpoints_empty_dir(self, tmp_path):
        """Test list_available_checkpoints returns empty list for empty dir."""
        resolver = CheckpointResolverLite(checkpoints_root=tmp_path)
        
        checkpoints = resolver.list_available_checkpoints()
        assert checkpoints == []
    
    def test_list_available_checkpoints_nonexistent_dir(self):
        """Test list_available_checkpoints returns empty list for nonexistent dir."""
        resolver = CheckpointResolverLite(checkpoints_root=Path("/nonexistent"))
        
        checkpoints = resolver.list_available_checkpoints()
        assert checkpoints == []
    
    def test_is_safe_path_blocks_appdata(self):
        """Test that is_safe_path blocks AppData paths."""
        resolver = CheckpointResolverLite()
        
        assert resolver.is_safe_path("C:\\Users\\test\\AppData\\model.safetensors") is False
        assert resolver.is_safe_path("/home/test/.appdata/model.safetensors") is False
    
    def test_is_safe_path_blocks_temp(self):
        """Test that is_safe_path blocks Temp paths."""
        resolver = CheckpointResolverLite()
        
        assert resolver.is_safe_path("C:\\Temp\\model.safetensors") is False
        assert resolver.is_safe_path("/tmp/model.safetensors") is False
    
    def test_is_safe_path_blocks_pytest_temp(self):
        """Test that is_safe_path blocks pytest temp paths."""
        resolver = CheckpointResolverLite()
        
        assert resolver.is_safe_path("C:\\Users\\test\\pytest-temp\\model.safetensors") is False
    
    def test_is_safe_path_allows_safe_paths(self):
        """Test that is_safe_path allows safe paths."""
        resolver = CheckpointResolverLite()
        
        assert resolver.is_safe_path("models/checkpoints/model.safetensors") is True
        assert resolver.is_safe_path("D:\\Projects\\model.safetensors") is True
