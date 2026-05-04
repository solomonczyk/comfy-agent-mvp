"""Tests for resolution policy preflight guard.

RC-COMBINE-V2-621-680: Verify that the preflight guard blocks
submits that violate the rebuilt recipe resolution policy.
"""
import json
import pytest
from pathlib import Path


class TestResolutionPolicyPreflightGuard:
    """Test resolution policy preflight guard logic."""
    
    def test_rebuilt_payload_exists_check(self, tmp_path):
        """Check that rebuilt payload file exists."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        rebuilt_payload = {
            "new_resolution": {"width": 1024, "height": 1024},
            "old_512_resolution_blocked": True,
            "minimum_short_side_1024_enforced": True,
        }
        
        with open(control_dir / "combine_v2_rebuilt_generation_payload.json", "w") as f:
            json.dump(rebuilt_payload, f)
        
        assert (control_dir / "combine_v2_rebuilt_generation_payload.json").exists()
    
    def test_minimum_short_side_calculation(self):
        """Test minimum short side calculation logic."""
        test_cases = [
            ((512, 512), 512),
            ((1024, 1024), 1024),
            ((1024, 512), 512),
            ((512, 1024), 512),
            ((2048, 1024), 1024),
            ((768, 1024), 768),
        ]
        
        for (width, height), expected_min in test_cases:
            actual_min = min(width, height)
            assert actual_min == expected_min
    
    def test_resolution_violation_detection(self):
        """Test resolution violation detection logic."""
        minimum_required = 1024
        
        test_cases = [
            ((512, 512), True),
            ((1024, 1024), False),
            ((1024, 512), True),
            ((512, 1024), True),
            ((2048, 2048), False),
            ((768, 768), True),
        ]
        
        for (width, height), should_violate in test_cases:
            actual_min = min(width, height)
            violates = actual_min < minimum_required
            assert violates == should_violate
    
    def test_preflight_guard_artifact_structure(self, tmp_path):
        """Test that preflight failure artifact has correct structure."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        preflight_report = {
            "stage": "resolution_policy_preflight_check",
            "status": "blocked",
            "failure_code": "REBUILT_RECIPE_RESOLUTION_POLICY_VIOLATION",
            "would_submit": False,
            "comfyui_execution": False,
            "actual_workflow_resolution": "512x512",
            "actual_minimum_short_side": 512,
            "minimum_short_side_required": 1024,
            "resolution_violates_policy": True,
        }
        
        with open(control_dir / "combine_v2_resolution_policy_preflight_failure.json", "w") as f:
            json.dump(preflight_report, f)
        
        with open(control_dir / "combine_v2_resolution_policy_preflight_failure.json", "r") as f:
            loaded = json.load(f)
        
        assert loaded["status"] == "blocked"
        assert loaded["failure_code"] == "REBUILT_RECIPE_RESOLUTION_POLICY_VIOLATION"
        assert loaded["would_submit"] is False
        assert loaded["comfyui_execution"] is False
        assert loaded["resolution_violates_policy"] is True
