"""RC-RUNTIME1 — Tests for WorkflowGraphEditorLite."""
import pytest

from app.runtime.workflow_editor import WorkflowGraphEditorLite


class TestWorkflowGraphEditorLite:
    """Tests for WorkflowGraphEditorLite."""
    
    def test_find_nodes_by_class_type(self):
        """Test find_nodes with class_type filter."""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
            "5": {"class_type": "LoadImage", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        
        ksampler_nodes = editor.find_nodes("KSampler")
        assert ksampler_nodes == ["3"]
        
        load_image_nodes = editor.find_nodes("LoadImage")
        assert load_image_nodes == ["5"]
    
    def test_find_nodes_without_filter(self):
        """Test find_nodes without class_type filter returns all."""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        
        all_nodes = editor.find_nodes()
        assert set(all_nodes) == {"3", "4"}
    
    def test_set_input(self):
        """Test set_input modifies node input."""
        workflow = {"3": {"class_type": "KSampler", "inputs": {"denoise": 0.5}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        editor.set_input("3", "denoise", 0.75)
        
        assert editor.workflow["3"]["inputs"]["denoise"] == 0.75
    
    def test_set_input_creates_inputs_dict(self):
        """Test set_input creates inputs dict if missing."""
        workflow = {"3": {"class_type": "KSampler"}}
        
        editor = WorkflowGraphEditorLite(workflow)
        editor.set_input("3", "denoise", 0.5)
        
        assert editor.workflow["3"]["inputs"]["denoise"] == 0.5
    
    def test_set_input_raises_for_missing_node(self):
        """Test set_input raises ValueError for missing node."""
        workflow = {}
        
        editor = WorkflowGraphEditorLite(workflow)
        
        with pytest.raises(ValueError, match="Node 999 not found"):
            editor.set_input("999", "denoise", 0.5)
    
    def test_connect(self):
        """Test connect creates link between nodes."""
        workflow = {
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        editor.connect("8", 0, "3", "latent_image")
        
        assert editor.workflow["3"]["inputs"]["latent_image"] == ["8", 0]
    
    def test_connect_raises_for_missing_source(self):
        """Test connect raises ValueError for missing source node."""
        workflow = {"3": {"class_type": "KSampler", "inputs": {}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        
        with pytest.raises(ValueError, match="Source node 999 not found"):
            editor.connect("999", 0, "3", "latent_image")
    
    def test_connect_raises_for_missing_target(self):
        """Test connect raises ValueError for missing target node."""
        workflow = {"8": {"class_type": "VAEEncode", "inputs": {}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        
        with pytest.raises(ValueError, match="Target node 999 not found"):
            editor.connect("8", 0, "999", "latent_image")
    
    def test_add_node(self):
        """Test add_node creates new node."""
        workflow = {}
        
        editor = WorkflowGraphEditorLite(workflow)
        editor.add_node("10", "SaveImage", {"filename_prefix": "test"})
        
        assert "10" in editor.workflow
        assert editor.workflow["10"]["class_type"] == "SaveImage"
        assert editor.workflow["10"]["inputs"]["filename_prefix"] == "test"
    
    def test_add_node_raises_for_duplicate(self):
        """Test add_node raises ValueError for duplicate node ID."""
        workflow = {"10": {"class_type": "SaveImage", "inputs": {}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        
        with pytest.raises(ValueError, match="Node 10 already exists"):
            editor.add_node("10", "KSampler", {})
    
    def test_replace_node_type(self):
        """Test replace_node_type changes class_type."""
        workflow = {"5": {"class_type": "ImageResize", "inputs": {}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        editor.replace_node_type("5", "ImageScale")
        
        assert editor.workflow["5"]["class_type"] == "ImageScale"
    
    def test_replace_node_type_raises_for_missing_node(self):
        """Test replace_node_type raises ValueError for missing node."""
        workflow = {}
        
        editor = WorkflowGraphEditorLite(workflow)
        
        with pytest.raises(ValueError, match="Node 999 not found"):
            editor.replace_node_type("999", "ImageScale")
    
    def test_remove_if_unreferenced_removes_unreferenced(self):
        """Test remove_if_unreferenced removes unreferenced node."""
        workflow = {
            "5": {"class_type": "EmptyLatentImage", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.remove_if_unreferenced("5")
        
        assert result is True
        assert "5" not in editor.workflow
        assert "3" in editor.workflow
    
    def test_remove_if_unreferenced_keeps_referenced(self):
        """Test remove_if_unreferenced keeps referenced node."""
        workflow = {
            "5": {"class_type": "EmptyLatentImage", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {"latent_image": ["5", 0]}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.remove_if_unreferenced("5")
        
        assert result is False
        assert "5" in editor.workflow
    
    def test_remove_if_unreferenced_returns_false_for_missing(self):
        """Test remove_if_unreferenced returns False for missing node."""
        workflow = {}
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.remove_if_unreferenced("999")
        
        assert result is False
    
    def test_validate_no_dangling_links_valid(self):
        """Test validate_no_dangling_links with valid workflow."""
        workflow = {
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {"latent_image": ["8", 0]}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_no_dangling_links()
        
        assert result["valid"] is True
        assert result["errors"] == []
    
    def test_validate_no_dangling_links_invalid(self):
        """Test validate_no_dangling_links detects dangling links."""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {"latent_image": ["999", 0]}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_no_dangling_links()
        
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "999" in result["errors"][0]
    
    def test_validate_contract_valid(self):
        """Test validate_contract with valid workflow."""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
            "8": {"class_type": "VAEEncode", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_contract(
            required_nodes={"3": "KSampler", "4": "CheckpointLoaderSimple"},
        )
        
        assert result["valid"] is True
        assert result["missing_nodes"] == []
        assert result["invalid_nodes"] == []
    
    def test_validate_contract_missing_node(self):
        """Test validate_contract detects missing node."""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_contract(
            required_nodes={"3": "KSampler", "4": "CheckpointLoaderSimple"},
        )
        
        assert result["valid"] is False
        assert len(result["missing_nodes"]) == 1
        assert "4 (CheckpointLoaderSimple)" in result["missing_nodes"][0]
    
    def test_validate_contract_invalid_node_type(self):
        """Test validate_contract detects invalid node type."""
        workflow = {
            "3": {"class_type": "EmptyLatentImage", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_contract(
            required_nodes={"3": "KSampler"},
        )
        
        assert result["valid"] is False
        assert len(result["invalid_nodes"]) == 1
        assert "expected KSampler, got EmptyLatentImage" in result["invalid_nodes"][0]
    
    def test_validate_contract_missing_connection(self):
        """Test validate_contract detects missing connection."""
        workflow = {
            "8": {"class_type": "VAEEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        }
        
        editor = WorkflowGraphEditorLite(workflow)
        result = editor.validate_contract(
            required_connections=[("8", "3", "latent_image")],
        )
        
        assert result["valid"] is False
        assert len(result["missing_connections"]) == 1
    
    def test_get_workflow_returns_copy(self):
        """Test get_workflow returns a copy, not reference."""
        workflow = {"3": {"class_type": "KSampler", "inputs": {}}}
        
        editor = WorkflowGraphEditorLite(workflow)
        returned = editor.get_workflow()
        
        returned["3"]["inputs"]["denoise"] = 0.5
        
        assert "denoise" not in editor.workflow["3"]["inputs"]
