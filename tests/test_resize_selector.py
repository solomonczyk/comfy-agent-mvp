"""RC-RUNTIME1 — Tests for ResizeNodeSelector."""
import pytest

from app.runtime.resize_selector import ResizeNodeSelector


class TestResizeNodeSelector:
    """Tests for ResizeNodeSelector."""
    
    def test_select_resize_node_prefers_imageresize(self):
        """Test that select_resize_node prefers ImageResize."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageResize": {},
            "ImageScale": {},
        })
        
        assert selector.select_resize_node() == "ImageResize"
    
    def test_select_resize_node_falls_back_to_imagescale(self):
        """Test that select_resize_node falls back to ImageScale."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageScale": {},
        })
        
        assert selector.select_resize_node() == "ImageScale"
    
    def test_select_resize_node_defaults_to_preferred_when_no_object_info(self):
        """Test that select_resize_node defaults to preferred when no object_info."""
        selector = ResizeNodeSelector()
        selector.object_info = None
        
        assert selector.select_resize_node() == "ImageResize"
    
    def test_select_resize_node_raises_when_none_available(self):
        """Test that select_resize_node raises ValueError when none available."""
        selector = ResizeNodeSelector()
        selector.set_object_info({})
        
        with pytest.raises(ValueError, match="No resize node available"):
            selector.select_resize_node()
    
    def test_has_preferred_returns_true_when_available(self):
        """Test that has_preferred returns True when ImageResize is available."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageResize": {},
        })
        
        assert selector.has_preferred() is True
    
    def test_has_preferred_returns_false_when_unavailable(self):
        """Test that has_preferred returns False when ImageResize is unavailable."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageScale": {},
        })
        
        assert selector.has_preferred() is False
    
    def test_has_fallback_returns_true_when_available(self):
        """Test that has_fallback returns True when ImageScale is available."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageScale": {},
        })
        
        assert selector.has_fallback() is True
    
    def test_has_fallback_returns_false_when_unavailable(self):
        """Test that has_fallback returns False when ImageScale is unavailable."""
        selector = ResizeNodeSelector()
        selector.set_object_info({})
        
        assert selector.has_fallback() is False
    
    def test_get_available_resize_nodes_returns_both(self):
        """Test that get_available_resize_nodes returns both when available."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageResize": {},
            "ImageScale": {},
        })
        
        available = selector.get_available_resize_nodes()
        assert available == ["ImageResize", "ImageScale"]
    
    def test_get_available_resize_nodes_returns_only_fallback(self):
        """Test that get_available_resize_nodes returns only fallback."""
        selector = ResizeNodeSelector()
        selector.set_object_info({
            "ImageScale": {},
        })
        
        available = selector.get_available_resize_nodes()
        assert available == ["ImageScale"]
    
    def test_get_available_resize_nodes_returns_empty_when_none(self):
        """Test that get_available_resize_nodes returns empty list when none."""
        selector = ResizeNodeSelector()
        selector.set_object_info({})
        
        available = selector.get_available_resize_nodes()
        assert available == []
