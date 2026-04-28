"""RC-RUNTIME1 — CheckpointResolver-lite for validating checkpoint existence."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class CheckpointResolverLite:
    """Lite checkpoint resolver for validating checkpoint existence.
    
    RC-RUNTIME1 — Validates checkpoint file existence without
    making real ComfyUI API calls. Blocks missing checkpoints
    before workflow submission.
    """
    
    DEFAULT_CHECKPOINT_DIR = Path("models/checkpoints")
    
    def __init__(
        self,
        checkpoint_dir: Path | str | None = None,
        checkpoints_root: Path | str | None = None,
    ):
        """Initialize checkpoint resolver.
        
        Args:
            checkpoint_dir: Directory containing checkpoint files
            checkpoints_root: Root checkpoints directory (for resolving relative paths)
        """
        if checkpoint_dir is None:
            self.checkpoint_dir = self.DEFAULT_CHECKPOINT_DIR
        else:
            self.checkpoint_dir = Path(checkpoint_dir)
        
        if checkpoints_root is None:
            self.checkpoints_root = self.DEFAULT_CHECKPOINT_DIR
        else:
            self.checkpoints_root = Path(checkpoints_root)
    
    def resolve_checkpoint_path(self, checkpoint_name: str) -> Path:
        """Resolve checkpoint name to absolute path.
        
        Args:
            checkpoint_name: Checkpoint filename (e.g., "model.safetensors")
            
        Returns:
            Absolute path to checkpoint file
            
        Raises:
            FileNotFoundError: If checkpoint file does not exist
        """
        # Try as relative to checkpoints_root
        relative_path = self.checkpoints_root / checkpoint_name
        if relative_path.exists():
            return relative_path.resolve()
        
        # Try as absolute path
        absolute_path = Path(checkpoint_name)
        if absolute_path.is_absolute() and absolute_path.exists():
            return absolute_path.resolve()
        
        # Try as relative to checkpoint_dir
        dir_path = self.checkpoint_dir / checkpoint_name
        if dir_path.exists():
            return dir_path.resolve()
        
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_name}. "
            f"Tried: {relative_path}, {absolute_path}, {dir_path}"
        )
    
    def validate_checkpoint(self, checkpoint_name: str) -> dict[str, Any]:
        """Validate that checkpoint file exists.
        
        Args:
            checkpoint_name: Checkpoint filename
            
        Returns:
            Dict with "valid" (bool), "path" (resolved Path if valid),
            "error" (str if invalid)
        """
        try:
            path = self.resolve_checkpoint_path(checkpoint_name)
            return {
                "valid": True,
                "path": str(path),
                "checkpoint_name": checkpoint_name,
                "exists": True,
                "error": None,
            }
        except FileNotFoundError as e:
            return {
                "valid": False,
                "path": None,
                "checkpoint_name": checkpoint_name,
                "exists": False,
                "error": str(e),
            }
    
    def list_available_checkpoints(self) -> list[str]:
        """List all available checkpoint files.
        
        Returns:
            List of checkpoint filenames
        """
        if not self.checkpoints_root.exists():
            return []
        
        checkpoints = []
        for file_path in self.checkpoints_root.iterdir():
            if file_path.is_file() and file_path.suffix in {".safetensors", ".ckpt", ".pth"}:
                checkpoints.append(file_path.name)
        
        return sorted(checkpoints)
    
    def is_safe_path(self, checkpoint_path: str | Path) -> bool:
        """Check if checkpoint path is safe (not in AppData/Temp/pytest).
        
        RC-RUNTIME1 — Blocks unsafe production paths.
        
        Args:
            checkpoint_path: Path to checkpoint
            
        Returns:
            True if path is safe, False otherwise
        """
        path_str = str(checkpoint_path).lower()
        
        # Block AppData paths
        if "appdata" in path_str:
            return False
        
        # Block Temp paths
        if "\\temp\\" in path_str or "/tmp/" in path_str or "\\tmp\\" in path_str:
            return False
        
        # Block pytest temp paths
        if "pytest" in path_str and "temp" in path_str:
            return False
        
        return True
