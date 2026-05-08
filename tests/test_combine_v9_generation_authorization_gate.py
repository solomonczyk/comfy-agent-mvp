import json
import os
import unittest

class TestCombineV9GenerationAuthorizationGate(unittest.TestCase):
    def setUp(self):
        self.project_root = r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01"
        self.control_dir = os.path.join(self.project_root, "output", "control")
        
    def test_v9_generation_gate_created(self):
        """Test that V9 generation authorization gate is created with required fields"""
        gate_path = os.path.join(
            self.control_dir, "combine_v2_v9_generation_authorization_required.json"
        )
        self.assertTrue(os.path.exists(gate_path), "V9 generation authorization gate should exist")
        
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
            
        # Check required fields from task description
        self.assertFalse(gate_data.get("v9_generation_allowed_now"), "V9 generation should not be allowed now")
        self.assertTrue(gate_data.get("requires_separate_operator_generation_gate"), "Should require separate operator generation gate")
        self.assertEqual(gate_data.get("max_generations"), 1, "Should allow max 1 generation")
        self.assertFalse(gate_data.get("second_generation_allowed"), "Second generation should not be allowed")
        self.assertFalse(gate_data.get("retry_allowed"), "Retry should not be allowed")
        self.assertFalse(gate_data.get("visual_qa_allowed"), "Visual QA should not be allowed")
        self.assertFalse(gate_data.get("assembly_allowed"), "Assembly should not be allowed")
        self.assertFalse(gate_data.get("downstream_allowed"), "Downstream should not be allowed")
        self.assertFalse(gate_data.get("production_accepted"), "Production should not be accepted")
        
    def test_generation_gate_closed(self):
        """Test that generation gate is in closed state"""
        gate_path = os.path.join(
            self.control_dir, "combine_v2_v9_generation_authorization_required.json"
        )
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
            
        # Verify gate is closed
        self.assertFalse(gate_data.get("v9_generation_allowed_now"), "Generation gate should be closed")
        
    def test_max_generations_one_enforced(self):
        """Test that max_generations=1 is enforced"""
        gate_path = os.path.join(
            self.control_dir, "combine_v2_v9_generation_authorization_required.json"
        )
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
            
        self.assertEqual(gate_data.get("max_generations"), 1, "Max generations should be exactly 1")
        
    def test_production_accepted_false(self):
        """Test that production_accepted is false"""
        gate_path = os.path.join(
            self.control_dir, "combine_v2_v9_generation_authorization_required.json"
        )
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
            
        self.assertFalse(gate_data.get("production_accepted"), "Production should not be accepted")
        
    def test_assembly_downstream_blocked(self):
        """Test that assembly and downstream are blocked"""
        gate_path = os.path.join(
            self.control_dir, "combine_v2_v9_generation_authorization_required.json"
        )
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
            
        self.assertFalse(gate_data.get("assembly_allowed"), "Assembly should be blocked")
        self.assertFalse(gate_data.get("downstream_allowed"), "Downstream should be blocked")
        
    def test_no_generation_performed(self):
        """Test that no generation has been performed yet"""
        # Check artifact index for confirmation
        artifact_index_path = os.path.join(
            self.control_dir, "artifact_index.json"
        )
        with open(artifact_index_path, 'r') as f:
            artifact_data = json.load(f)
    
        # The latest stage should show no generation performed
        stage_results = artifact_data.get("stage_results", [])
        if stage_results:
            latest_stage = stage_results[-1]
            self.assertTrue(
                latest_stage.get("no_generation_performed", False),
                "Latest stage should show no generation performed"
            )

if __name__ == '__main__':
    unittest.main()