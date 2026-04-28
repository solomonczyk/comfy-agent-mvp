"""RC-RUNTIME1 — ResizeNodeSelector for choosing resize node type."""
from __future__ import annotations

from typing import Any


class ResizeNodeSelector:
    """Selector for choosing the appropriate resize node type.
    
    RC-RUNTIME1 — Chooses ImageResize if available, falls back to ImageScale.
    This ensures compatibility across different ComfyUI installations.
    """
    
    PREFERRED = "ImageResize"
    FALLBACK = "ImageScale"
    
    def __init__(self, object_info: dict[str, Any] | None = None):
        """Initialize resize node selector.
        
        Args:
            object_info: ComfyUI object_info dict (optional, can be set later)
        """
        self.object_info = object_info
    
    def set_object_info(self, object_info: dict[str, Any]) -> None:
        """Set object_info for node availability checking.
        
        Args:
            object_info: ComfyUI object_info dict
        """
        self.object_info = object_info
    
    def select_resize_node(self) -> str:
        """Select the best available resize node type.
        
        RC-RUNTIME1 — Prefers ImageResize, falls back to ImageScale.
        
        Returns:
            Selected node type ("ImageResize" or "ImageScale")
            
        Raises:
            ValueError: If no resize node is available
        """
        if self.object_info is None:
            # Default to preferred if no object_info available
            return self.PREFERRED
        
        if self.PREFERRED in self.object_info:
            return self.PREFERRED
        elif self.FALLBACK in self.object_info:
            return self.FALLBACK
        
        raise ValueError(
            f"No resize node available. "
            f"Tried: {self.PREFERRED}, {self.FALLBACK}"
        )
    
    def has_preferred(self) -> bool:
        """Check if preferred resize node (ImageResize) is available.
        
        Returns:
            True if ImageResize is available, False otherwise
        """
        if self.object_info is None:
            return False
        
        return self.PREFERRED in self.object_info
    
    def has_fallback(self) -> bool:
        """Check if fallback resize node (ImageScale) is available.
        
        Returns:
            True if ImageScale is available, False otherwise
        """
        if self.object_info is None:
            return False
        
        return self.FALLBACK in self.object_info
    
    def get_available_resize_nodes(self) -> list[str]:
        """Get list of available resize node types.
        
        Returns:
            List of available resize node types (ordered by preference)
        """
        if self.object_info is None:
            return []
        
        available = []
        if self.PREFERRED in self.object_info:
            available.append(self.PREFERRED)
        if self.FALLBACK in self.object_info:
            available.append(self.FALLBACK)
        
        return available
