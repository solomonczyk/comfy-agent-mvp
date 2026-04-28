"""RC-RUNTIME1 — ComfyNodeSchemaRegistry for reading/caching object_info."""
from __future__ import annotations

import asyncio
import httpx
import logging
from pathlib import Path
from typing import Any

from app.config import settings

log = logging.getLogger(__name__)


class ComfyNodeSchemaRegistry:
    """Registry for ComfyUI node schemas from object_info.
    
    RC-RUNTIME1 — Reads and caches ComfyUI object_info to confirm
    available node types and their capabilities.
    """
    
    REQUIRED_NODES = {
        "LoadImage",
        "VAEEncode",
        "VAEDecode",
        "KSampler",
        "CheckpointLoaderSimple",
    }
    
    RESIZE_NODES = {
        "ImageScale",
        "ImageResize",
    }
    
    def __init__(self, comfy_base_url: str | None = None):
        """Initialize schema registry.
        
        Args:
            comfy_base_url: ComfyUI base URL (defaults to settings.comfy_base_url)
        """
        self.comfy_base_url = comfy_base_url or settings.comfy_base_url
        self._object_info: dict[str, Any] | None = None
        self._cache_timestamp: float | None = None
    
    async def fetch_object_info(self) -> dict[str, Any]:
        """Fetch object_info from ComfyUI.
        
        Returns:
            object_info dict mapping node class types to their schema
            
        Raises:
            httpx.HTTPError: If fetch fails
        """
        url = f"{self.comfy_base_url}/object_info"
        
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        self._object_info = data
        self._cache_timestamp = asyncio.get_event_loop().time()
        log.info(f"[SCHEMA] Fetched object_info with {len(data)} node types")
        
        return data
    
    async def get_object_info(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get object_info, using cache if available.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            object_info dict
        """
        if force_refresh or self._object_info is None:
            return await self.fetch_object_info()
        
        return self._object_info
    
    def has_node_type(self, node_class_type: str) -> bool:
        """Check if a node type is available in ComfyUI.
        
        Args:
            node_class_type: Node class type (e.g., "LoadImage", "ImageScale")
            
        Returns:
            True if node type is available, False otherwise
        """
        if self._object_info is None:
            return False
        
        return node_class_type in self._object_info
    
    def get_available_resize_node(self) -> str | None:
        """Get the best available resize node type.
        
        RC-RUNTIME1 — Prefers ImageResize, falls back to ImageScale.
        
        Returns:
            "ImageResize" if available, "ImageScale" if available, None otherwise
        """
        if self._object_info is None:
            return None
        
        if "ImageResize" in self._object_info:
            return "ImageResize"
        elif "ImageScale" in self._object_info:
            return "ImageScale"
        
        return None
    
    def validate_required_nodes(self) -> dict[str, Any]:
        """Validate that all required nodes are available.
        
        Returns:
            Dict with "valid" (bool), "missing" (list of missing node types),
            "available" (list of available required node types)
        """
        if self._object_info is None:
            return {
                "valid": False,
                "missing": sorted(self.REQUIRED_NODES),
                "available": [],
                "error": "object_info not loaded",
            }
        
        available = sorted(self.REQUIRED_NODES.intersection(self._object_info.keys()))
        missing = sorted(self.REQUIRED_NODES - self._object_info.keys())
        
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "available": available,
        }
    
    def get_node_schema(self, node_class_type: str) -> dict[str, Any] | None:
        """Get schema for a specific node type.
        
        Args:
            node_class_type: Node class type
            
        Returns:
            Node schema dict if available, None otherwise
        """
        if self._object_info is None:
            return None
        
        return self._object_info.get(node_class_type)
