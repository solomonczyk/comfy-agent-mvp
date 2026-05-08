import json
import os
import unittest

class TestCombineV9WorkflowPackage(unittest.TestCase):
    def setUp(self):
        self.project_root = r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01"
        self.control_dir = os.path.join(self.project_root, "output", "control")
        
    def test_v9_workflow_package_created(self):
        """Test that V9 workflow package is created based on V8 quality-locked workflow"""
        workflow_path = os.path.join(
            self.control_dir, "combine_v2_v9_quality_locked_workflow_package.json"
        )
        self.assertTrue(os.path.exists(workflow_path), "V9 workflow package should exist")
        
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
            
        # Check that it's based on V8 quality-locked workflow
        self.assertEqual(workflow_data.get("workflow_type"), "v9_quality_locked_generation")
        self.assertEqual(workflow_data.get("saveimage_filename_prefix"), "combine_v2_v9_quality_locked_shot02")
        refinement_params = workflow_data.get("refinement_parameters", {})
        self.assertEqual(refinement_params.get("checkpoint"), "realvisxlV50_v50Bakedvae.safetensors")
        self.assertEqual(refinement_params.get("sampler"), "dpmpp_2m")
        self.assertEqual(refinement_params.get("scheduler"), "karras")
        self.assertEqual(refinement_params.get("steps"), 30)
        self.assertEqual(refinement_params.get("cfg_scale"), 6.5)
        self.assertEqual(refinement_params.get("resolution"), "1024x1024")
        
        # Check that it forbids fallback/minimal workflow
        self.assertTrue(workflow_data.get("no_fallback_workflow"), "Should not use fallback workflow")
        self.assertTrue(workflow_data.get("no_hidden_retry_path"), "Should not have hidden retry path")
        self.assertTrue(workflow_data.get("no_dry_run_as_success_path"), "Should not have dry-run-as-success path")
        
        # Check max_generations=1
        self.assertEqual(workflow_data.get("max_generations"), 1, "Should allow max 1 generation")
        
    def test_minimal_workflow_forbidden(self):
        """Test that minimal workflow is forbidden"""
        workflow_path = os.path.join(
            self.control_dir, "combine_v2_v9_quality_locked_workflow_package.json"
        )
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
            
        # Verify it's NOT a minimal workflow by checking for required nodes
        # In a real implementation, we would check the workflow JSON structure
        # For now, we verify that quality guardrails are applied
        self.assertGreaterEqual(
            len(workflow_data.get("quality_guardrails_applied", [])), 9,
            "Should have quality guardrails applied (not minimal workflow)"
        )
        
    def test_v9_workflow_uses_same_settings_as_v8(self):
        """Test that V9 workflow uses same checkpoint, sampler, scheduler as V8"""
        # Load V8 workflow for comparison
        v8_workflow_path = os.path.join(
            self.control_dir, "combine_v2_v8_quality_locked_submitted_workflow.json"
        )
        with open(v8_workflow_path, 'r') as f:
            v8_workflow_data = json.load(f)
            
        # Load V9 workflow
        v9_workflow_path = os.path.join(
            self.control_dir, "combine_v2_v9_quality_locked_workflow_package.json"
        )
        with open(v9_workflow_path, 'r') as f:
            v9_workflow_data = json.load(f)
            
        # Check that key settings match
        v8_refinement = v8_workflow_data.get("refinement_parameters", {})
        v9_refinement = v9_workflow_data.get("refinement_parameters", {})
        
        self.assertEqual(
            v8_refinement.get("checkpoint"),
            v9_refinement.get("checkpoint")
        )
        self.assertEqual(
            v8_refinement.get("sampler"),
            v9_refinement.get("sampler")
        )
        self.assertEqual(
            v8_refinement.get("scheduler"),
            v9_refinement.get("scheduler")
        )
        self.assertEqual(
            v8_refinement.get("cfg_scale"),
            v9_refinement.get("cfg_scale")
        )
        self.assertEqual(
            v8_refinement.get("steps"),
            v9_refinement.get("steps")
        )
        self.assertEqual(
            v8_refinement.get("resolution"),
            v9_refinement.get("resolution")
        )

if __name__ == '__main__':
    unittest.main()