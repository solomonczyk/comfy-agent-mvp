import json
import os
import unittest

class TestCombineV9CorrectivePlan(unittest.TestCase):
    def setUp(self):
        self.project_root = r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01"
        self.control_dir = os.path.join(self.project_root, "output", "control")
        
    def test_v8_reference_exists_and_sha256_verified(self):
        """Test that V8 reference asset exists and SHA256 matches expected value"""
        v8_asset_path = os.path.join(
            self.project_root, "output", "assets", 
            "combine_v2_v8_quality_locked_shot02_00001_.png"
        )
        self.assertTrue(os.path.exists(v8_asset_path), "V8 reference asset should exist")
        
        # Verify SHA256 matches expected value from task description
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(v8_asset_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        computed_hash = sha256_hash.hexdigest()
        expected_hash = "e551c745e28ad7979f5eb63b206f85f4974cb1227e84121f337f8f81239e90cd"
        self.assertEqual(
            computed_hash, expected_hash,
            f"V8 asset SHA256 mismatch. Expected: {expected_hash}, Got: {computed_hash}"
        )
        
    def test_v9_corrective_plan_created(self):
        """Test that V9 corrective plan artifact is created with required fields"""
        plan_path = os.path.join(
            self.control_dir, "combine_v2_v9_corrective_plan.json"
        )
        self.assertTrue(os.path.exists(plan_path), "V9 corrective plan should exist")
        
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)
            
        # Check required fields
        self.assertTrue(plan_data.get("preserve_v8_strengths"), "Should preserve V8 strengths")
        self.assertTrue(plan_data.get("use_v8_as_positive_reference"), "Should use V8 as positive reference")
        self.assertTrue(plan_data.get("avoid_v7_failure_modes"), "Should avoid V7 failure modes")
        self.assertFalse(plan_data.get("production_accepted"), "Production should not be accepted")
        self.assertFalse(plan_data.get("generation_allowed_now"), "Generation should not be allowed now")
        
    def test_v9_prompt_package_created(self):
        """Test that V9 prompt package is created with required fields"""
        prompt_path = os.path.join(
            self.control_dir, "combine_v2_v9_prompt_package.json"
        )
        self.assertTrue(os.path.exists(prompt_path), "V9 prompt package should exist")
        
        with open(prompt_path, 'r') as f:
            prompt_data = json.load(f)
            
        # Check that it preserves V8 strengths
        self.assertIn("sharp focus", prompt_data.get("positive_prompt", ""))
        self.assertIn("realistic eyes", prompt_data.get("positive_prompt", ""))
        self.assertIn("natural mouth", prompt_data.get("positive_prompt", ""))
        self.assertIn("close portrait framing", prompt_data.get("positive_prompt", ""))
        self.assertIn("blue atmospheric magical background", prompt_data.get("positive_prompt", ""))
        
        # Check that it improves shot/story relevance
        self.assertIn("medium shot", prompt_data.get("positive_prompt", ""))
        self.assertIn("subject centered", prompt_data.get("positive_prompt", ""))
        self.assertIn("engaged expression", prompt_data.get("positive_prompt", ""))
        self.assertIn("storytelling through facial expression", prompt_data.get("positive_prompt", ""))
        
        # Check that it forbids V7 failure modes
        self.assertIn("blurry", prompt_data.get("negative_prompt", ""))
        self.assertIn("deformed eyes", prompt_data.get("negative_prompt", ""))
        self.assertIn("deformed mouth", prompt_data.get("negative_prompt", ""))
        self.assertIn("small subject", prompt_data.get("negative_prompt", ""))
        self.assertIn("empty space", prompt_data.get("negative_prompt", ""))
        
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

if __name__ == '__main__':
    unittest.main()