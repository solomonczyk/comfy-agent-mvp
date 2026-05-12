"""
Tests for Fresh Visual Strategy repairability policy enforcement.
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Fixture for project root path."""
    return Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")


@pytest.fixture
def control_dir(project_root):
    """Fixture for control directory."""
    return project_root / "output" / "control"


@pytest.fixture
def strategy_dir(control_dir):
    """Fixture for strategy directory."""
    return control_dir / "fresh_visual_strategy"


class TestRepairabilityPolicyEnforcement:
    """Tests for repairability policy enforcement in fresh visual strategy."""
    
    def test_repairability_policy_exists(self, strategy_dir):
        """Test that repairability policy artifact exists."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        assert policy_path.exists(), "Repairability policy artifact does not exist"
    
    def test_repairability_policy_has_defect_classification(self, strategy_dir):
        """Test that repairability policy has defect classification."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert "defect_classification" in policy["repairability_aware_visual_policy"], "Defect classification missing from policy"
    
    def test_repairability_policy_blocks_unknown(self, strategy_dir):
        """Test that repairability policy blocks unknown repairability."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert policy["repairability_aware_visual_policy"]["unknown_repairability_blocks"] is True, "Policy does not block unknown repairability"
    
    def test_repairability_policy_requires_operator_review(self, strategy_dir):
        """Test that repairability policy requires operator review."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert policy["repairability_aware_visual_policy"]["visual_operator_review_required"] is True, "Policy does not require operator review"
    
    def test_repairability_policy_technical_pass_not_visual_pass(self, strategy_dir):
        """Test that technical pass is not visual pass."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert policy["repairability_aware_visual_policy"]["technical_pass_is_not_visual_pass"] is True, "Policy does not enforce technical pass != visual pass"
    
    def test_repairability_policy_production_accepted_must_remain_false(self, strategy_dir):
        """Test that production_accepted must remain false."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert policy["repairability_aware_visual_policy"]["production_accepted_must_remain_false"] is True, "Policy does not enforce production_accepted=false"
    
    def test_defect_classification_has_not_repairable_category(self, strategy_dir):
        """Test that defect classification has not_repairable_with_current_tools category."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        classification = policy["repairability_aware_visual_policy"]["defect_classification"]
        assert "not_repairable_with_current_tools" in classification, "Missing not_repairable_with_current_tools category"
    
    def test_defect_classification_has_unknown_repairability_category(self, strategy_dir):
        """Test that defect classification has unknown_repairability category."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        classification = policy["repairability_aware_visual_policy"]["defect_classification"]
        assert "unknown_repairability" in classification, "Missing unknown_repairability category"
    
    def test_not_repairable_category_blocks(self, strategy_dir):
        """Test that not_repairable_with_current_tools category has BLOCK action."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        classification = policy["repairability_aware_visual_policy"]["defect_classification"]["not_repairable_with_current_tools"]
        assert "BLOCK" in classification["action"].upper(), "not_repairable category does not block"
    
    def test_unknown_repairability_category_blocks(self, strategy_dir):
        """Test that unknown_repairability category has BLOCK action."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        classification = policy["repairability_aware_visual_policy"]["defect_classification"]["unknown_repairability"]
        assert "BLOCK" in classification["action"].upper(), "unknown_repairability category does not block"
    
    def test_repairability_assessment_workflow_defined(self, strategy_dir):
        """Test that repairability assessment workflow is defined."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert "repairability_assessment_workflow" in policy["repairability_aware_visual_policy"], "Repairability assessment workflow not defined"
    
    def test_repairability_assessment_workflow_has_six_steps(self, strategy_dir):
        """Test that repairability assessment workflow has 6 steps."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        workflow = policy["repairability_aware_visual_policy"]["repairability_assessment_workflow"]
        assert len(workflow) == 6, f"Expected 6 workflow steps, got {len(workflow)}"
    
    def test_repairability_policy_has_enforcement_points(self, strategy_dir):
        """Test that repairability policy has enforcement points."""
        policy_path = strategy_dir / "repairability_aware_visual_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert "enforcement_points" in policy["repairability_aware_visual_policy"], "Enforcement points not defined"
        assert len(policy["repairability_aware_visual_policy"]["enforcement_points"]) > 0, "No enforcement points defined"
    
    def test_negative_reference_policy_exists(self, strategy_dir):
        """Test that negative reference policy exists."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        assert policy_path.exists(), "Negative reference policy does not exist"
    
    def test_negative_reference_policy_has_documented_references(self, strategy_dir):
        """Test that negative reference policy has documented references."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        references = policy["negative_reference_policy"]["documented_negative_references"]
        assert len(references) > 0, "No negative references documented"
    
    def test_negative_reference_policy_enforces_loading(self, strategy_dir):
        """Test that negative reference policy enforces loading before generation."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        enforcement = policy["negative_reference_policy"]["negative_reference_enforcement"]
        assert enforcement["must_be_loaded_before_generation"] is True, "Policy does not enforce loading before generation"
    
    def test_negative_reference_policy_includes_bad_teeth(self, strategy_dir):
        """Test that negative reference policy includes bad teeth defect."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        references = policy["negative_reference_policy"]["documented_negative_references"]
        assert "v12_bad_teeth" in references, "Bad teeth defect not documented"
    
    def test_negative_reference_policy_includes_framing_defects(self, strategy_dir):
        """Test that negative reference policy includes framing defects."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        references = policy["negative_reference_policy"]["documented_negative_references"]
        assert "v13_framing_defects" in references, "Framing defects not documented"
    
    def test_negative_reference_policy_includes_identity_drift(self, strategy_dir):
        """Test that negative reference policy includes identity drift."""
        policy_path = strategy_dir / "negative_reference_policy.json"
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        references = policy["negative_reference_policy"]["documented_negative_references"]
        assert "identity_drift" in references, "Identity drift not documented"
