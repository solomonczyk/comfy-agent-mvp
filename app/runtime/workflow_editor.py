"""RC-RUNTIME1 — WorkflowGraphEditor-lite for graph operations."""
from __future__ import annotations

import copy
import logging
from typing import Any

log = logging.getLogger(__name__)


class WorkflowGraphEditorLite:
    """Lite workflow graph editor for ComfyUI workflow manipulation.
    
    RC-RUNTIME1 — Supports basic graph operations without full graph library:
    - find_nodes
    - set_input
    - connect
    - add_node
    - replace_node_type
    - remove_if_unreferenced
    - validate_no_dangling_links
    - validate_contract
    """
    
    def __init__(self, workflow: dict[str, Any]):
        """Initialize workflow editor.
        
        Args:
            workflow: ComfyUI workflow dict (will be copied)
        """
        self.workflow = copy.deepcopy(workflow)
    
    def find_nodes(self, class_type: str | None = None) -> list[str]:
        """Find all nodes matching a class type.
        
        Args:
            class_type: Node class type to find (e.g., "LoadImage")
                       If None, returns all node IDs
            
        Returns:
            List of node IDs matching the class type
        """
        if class_type is None:
            return list(self.workflow.keys())
        
        return [
            node_id
            for node_id, node in self.workflow.items()
            if isinstance(node, dict) and node.get("class_type") == class_type
        ]
    
    def set_input(self, node_id: str, input_key: str, value: Any) -> None:
        """Set an input value on a node.
        
        Args:
            node_id: Node ID
            input_key: Input key name
            value: Input value
        """
        if node_id not in self.workflow:
            raise ValueError(f"Node {node_id} not found in workflow")
        
        node = self.workflow[node_id]
        if not isinstance(node, dict):
            raise ValueError(f"Node {node_id} is not a dict")
        
        if "inputs" not in node:
            node["inputs"] = {}
        
        node["inputs"][input_key] = value
        log.debug(f"[EDITOR] Node {node_id}: set {input_key} = {value}")
    
    def connect(self, source_node_id: str, source_output: int, target_node_id: str, target_input: str) -> None:
        """Connect two nodes.
        
        Args:
            source_node_id: Source node ID
            source_output: Source output index
            target_node_id: Target node ID
            target_input: Target input key
        """
        if source_node_id not in self.workflow:
            raise ValueError(f"Source node {source_node_id} not found")
        
        if target_node_id not in self.workflow:
            raise ValueError(f"Target node {target_node_id} not found")
        
        target_node = self.workflow[target_node_id]
        if not isinstance(target_node, dict):
            raise ValueError(f"Target node {target_node_id} is not a dict")
        
        if "inputs" not in target_node:
            target_node["inputs"] = {}
        
        target_node["inputs"][target_input] = [source_node_id, source_output]
        log.debug(f"[EDITOR] Connected {source_node_id}[{source_output}] → {target_node_id}.{target_input}")
    
    def add_node(self, node_id: str, class_type: str, inputs: dict[str, Any] | None = None) -> None:
        """Add a new node to the workflow.
        
        Args:
            node_id: Node ID
            class_type: Node class type
            inputs: Input dict (optional)
        """
        if node_id in self.workflow:
            raise ValueError(f"Node {node_id} already exists in workflow")
        
        self.workflow[node_id] = {
            "class_type": class_type,
            "inputs": inputs or {},
        }
        log.debug(f"[EDITOR] Added node {node_id} ({class_type})")
    
    def replace_node_type(self, node_id: str, new_class_type: str) -> None:
        """Replace a node's class type.
        
        Args:
            node_id: Node ID
            new_class_type: New class type
        """
        if node_id not in self.workflow:
            raise ValueError(f"Node {node_id} not found in workflow")
        
        node = self.workflow[node_id]
        if not isinstance(node, dict):
            raise ValueError(f"Node {node_id} is not a dict")
        
        old_class_type = node.get("class_type")
        node["class_type"] = new_class_type
        log.debug(f"[EDITOR] Node {node_id}: {old_class_type} → {new_class_type}")
    
    def remove_if_unreferenced(self, node_id: str) -> bool:
        """Remove a node if it has no incoming connections.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if node was removed, False if still referenced
        """
        if node_id not in self.workflow:
            return False
        
        # Check if any node references this node
        for other_id, other_node in self.workflow.items():
            if other_id == node_id:
                continue
            
            if not isinstance(other_node, dict):
                continue
            
            inputs = other_node.get("inputs", {})
            for value in inputs.values():
                if isinstance(value, list) and len(value) >= 2 and str(value[0]) == node_id:
                    # This node is referenced
                    log.debug(f"[EDITOR] Node {node_id} is referenced by {other_id}, not removing")
                    return False
        
        # Node is unreferenced, remove it
        del self.workflow[node_id]
        log.debug(f"[EDITOR] Removed unreferenced node {node_id}")
        return True
    
    def validate_no_dangling_links(self) -> dict[str, Any]:
        """Validate that all node links point to existing nodes.
        
        Returns:
            Dict with "valid" (bool) and "errors" (list of error messages)
        """
        errors = []
        
        for node_id, node in self.workflow.items():
            if not isinstance(node, dict):
                continue
            
            inputs = node.get("inputs", {})
            for input_key, value in inputs.items():
                if isinstance(value, list) and len(value) >= 2:
                    source_node_id = str(value[0])
                    if source_node_id not in self.workflow:
                        errors.append(
                            f"Node {node_id}.{input_key} references missing node {source_node_id}"
                        )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    
    def validate_contract(
        self,
        required_nodes: dict[str, str] | None = None,
        required_connections: list[tuple[str, str, str]] | None = None,
    ) -> dict[str, Any]:
        """Validate workflow contract.
        
        Args:
            required_nodes: Dict mapping node IDs to required class types
                           (e.g., {"3": "KSampler", "4": "CheckpointLoaderSimple"})
            required_connections: List of (source_id, target_id, target_input) tuples
                                   (e.g., [("8", "3", "latent_image")])
        
        Returns:
            Dict with "valid" (bool), "missing_nodes" (list),
            "invalid_nodes" (list), "missing_connections" (list)
        """
        errors = []
        missing_nodes = []
        invalid_nodes = []
        missing_connections = []
        
        # Validate required nodes
        if required_nodes:
            for node_id, expected_class_type in required_nodes.items():
                if node_id not in self.workflow:
                    missing_nodes.append(f"{node_id} ({expected_class_type})")
                    continue
                
                node = self.workflow[node_id]
                if not isinstance(node, dict):
                    invalid_nodes.append(f"{node_id}: not a dict")
                    continue
                
                actual_class_type = node.get("class_type")
                if actual_class_type != expected_class_type:
                    invalid_nodes.append(
                        f"{node_id}: expected {expected_class_type}, got {actual_class_type}"
                    )
        
        # Validate required connections
        if required_connections:
            for source_id, target_id, target_input in required_connections:
                if source_id not in self.workflow:
                    missing_connections.append(
                        f"Connection source {source_id} not found"
                    )
                    continue
                
                if target_id not in self.workflow:
                    missing_connections.append(
                        f"Connection target {target_id} not found"
                    )
                    continue
                
                target_node = self.workflow[target_id]
                if not isinstance(target_node, dict):
                    continue
                
                inputs = target_node.get("inputs", {})
                actual_connection = inputs.get(target_input)
                
                expected_connection = [source_id, 0]
                if actual_connection != expected_connection:
                    missing_connections.append(
                        f"{target_id}.{target_input} should be {expected_connection}, "
                        f"got {actual_connection}"
                    )
        
        return {
            "valid": len(missing_nodes) == 0 and len(invalid_nodes) == 0 and len(missing_connections) == 0,
            "missing_nodes": missing_nodes,
            "invalid_nodes": invalid_nodes,
            "missing_connections": missing_connections,
            "errors": errors,
        }
    
    def get_workflow(self) -> dict[str, Any]:
        """Get the (possibly modified) workflow.
        
        Returns:
            Copy of the workflow dict
        """
        return copy.deepcopy(self.workflow)
