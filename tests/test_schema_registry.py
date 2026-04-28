"""RC-RUNTIME1 — Tests for ComfyNodeSchemaRegistry."""
from pathlib import Path
import pytest

from app.runtime.schema_registry import ComfyNodeSchemaRegistry


class TestComfyNodeSchemaRegistry:
    """Tests for ComfyNodeSchemaRegistry."""
    
    def test_has_node_type_returns_true_when_available(self):
        """Test that has_node_type returns True when node type is available."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "LoadImage": {"input": {}},
            "KSampler": {"input": {}},
        }
        
        assert registry.has_node_type("LoadImage") is True
        assert registry.has_node_type("KSampler") is True
    
    def test_has_node_type_returns_false_when_unavailable(self):
        """Test that has_node_type returns False when node type is unavailable."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "LoadImage": {"input": {}},
        }
        
        assert registry.has_node_type("KSampler") is False
        assert registry.has_node_type("NonExistent") is False
    
    def test_has_node_type_returns_false_when_no_object_info(self):
        """Test that has_node_type returns False when object_info is None."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = None
        
        assert registry.has_node_type("LoadImage") is False
    
    def test_get_available_resize_node_prefers_imageresize(self):
        """Test that get_available_resize_node prefers ImageResize."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "ImageResize": {"input": {}},
            "ImageScale": {"input": {}},
        }
        
        assert registry.get_available_resize_node() == "ImageResize"
    
    def test_get_available_resize_node_falls_back_to_imagescale(self):
        """Test that get_available_resize_node falls back to ImageScale."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "ImageScale": {"input": {}},
        }
        
        assert registry.get_available_resize_node() == "ImageScale"
    
    def test_get_available_resize_node_returns_none_when_unavailable(self):
        """Test that get_available_resize_node returns None when unavailable."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {}
        
        assert registry.get_available_resize_node() is None
    
    def test_validate_required_nodes_all_available(self):
        """Test validate_required_nodes when all required nodes are available."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "LoadImage": {},
            "VAEEncode": {},
            "VAEDecode": {},
            "KSampler": {},
            "CheckpointLoaderSimple": {},
        }
        
        result = registry.validate_required_nodes()
        assert result["valid"] is True
        assert result["missing"] == []
        assert len(result["available"]) == 5
    
    def test_validate_required_nodes_missing_some(self):
        """Test validate_required_nodes when some required nodes are missing."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "LoadImage": {},
            "KSampler": {},
        }
        
        result = registry.validate_required_nodes()
        assert result["valid"] is False
        assert len(result["missing"]) == 3
        assert "VAEEncode" in result["missing"]
    
    def test_validate_required_nodes_no_object_info(self):
        """Test validate_required_nodes when object_info is None."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = None
        
        result = registry.validate_required_nodes()
        assert result["valid"] is False
        assert result["error"] == "object_info not loaded"
    
    def test_get_node_schema_returns_schema_when_available(self):
        """Test that get_node_schema returns schema when available."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {
            "LoadImage": {"input": {"required": ["image"]}},
        }
        
        schema = registry.get_node_schema("LoadImage")
        assert schema is not None
        assert schema["input"]["required"] == ["image"]
    
    def test_get_node_schema_returns_none_when_unavailable(self):
        """Test that get_node_schema returns None when unavailable."""
        registry = ComfyNodeSchemaRegistry()
        registry._object_info = {}
        
        schema = registry.get_node_schema("LoadImage")
        assert schema is None
