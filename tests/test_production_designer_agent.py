"""Tests for Production Designer Agent."""

import json
import pytest
from pathlib import Path
from app.agents.production_designer.contract import ProductionDesignerAgentContract
from app.agents.production_designer.validator import ProductionDesignerValidator
from app.agents.production_designer.reviewer import ProductionDesignerReviewer
from app.agents.production_designer.artifacts import ProductionDesignerArtifacts


class TestProductionDesignerAgentContract:
    """Test the production designer agent contract."""
    
    def test_contract_forbids_generation(self):
        """Test that contract forbids generation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ProductionDesignerAgentContract(project_root)
        contract_data = contract.create_contract()
        
        assert contract_data["can_execute_generation"] is False
        assert contract_data["can_retry"] is False
        assert contract_data["can_accept_visual"] is False
        assert contract_data["can_set_production_accepted"] is False
        assert contract_data["can_run_assembly"] is False
        assert contract_data["can_run_downstream"] is False
        assert contract_data["can_edit_image"] is False
        assert contract_data["can_submit_comfyui"] is False
        assert contract_data["can_modify_set_background"] is False
    
    def test_contract_review_criteria(self):
        """Test that contract includes all required review criteria."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ProductionDesignerAgentContract(project_root)
        contract_data = contract.create_contract()
        
        expected_criteria = [
            "visual_world",
            "location_environment",
            "set_design",
            "decor_background_coherence",
            "genre_era_style_consistency",
            "atmosphere",
            "scene_support"
        ]
        
        for criterion in expected_criteria:
            assert criterion in contract_data["review_criteria"]
    
    def test_review_authorization_forbids_generation(self):
        """Test that review authorization forbids generation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ProductionDesignerAgentContract(project_root)
        auth = contract.create_review_authorization()
        
        assert auth["generation_authorized"] is False
        assert auth["retry_authorized"] is False
        assert auth["render_authorized"] is False
        assert auth["downstream_authorized"] is False
        assert auth["new_generation_forbidden"] is True
        assert auth["retry_forbidden"] is True
        assert auth["second_generation_forbidden"] is True
        assert auth["comfyui_submit_forbidden"] is True
        assert auth["image_editing_forbidden"] is True
        assert auth["set_background_modification_forbidden"] is True
        assert auth["render_forbidden"] is True
        assert auth["production_accepted_forbidden"] is True


class TestProductionDesignerValidator:
    """Test the production designer validator."""
    
    def test_validate_candidate_exists(self):
        """Test candidate exists validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ProductionDesignerValidator(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        result = validator.validate_candidate_exists(candidate_path)
        
        assert result["check"] == "candidate_exists"
        assert result["passed"] is True
    
    def test_validate_candidate_sha256(self):
        """Test candidate SHA256 validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ProductionDesignerValidator(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        expected_sha256 = "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b"
        result = validator.validate_candidate_sha256(candidate_path, expected_sha256)
        
        assert result["check"] == "candidate_sha256"
        assert result["passed"] is True
    
    def test_validate_previous_state(self):
        """Test previous state validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ProductionDesignerValidator(project_root)
        
        # After review is complete, state should be set_decorator_review_required
        expected_state = "set_decorator_review_required"
        result = validator.validate_previous_state(expected_state)
        
        assert result["check"] == "previous_state"
        assert result["passed"] is True
        assert result["actual_state"] == expected_state
    
    def test_validate_previous_colorist_proof(self):
        """Test previous Colorist proof validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ProductionDesignerValidator(project_root)
        
        expected_commit = "79c429f"
        result = validator.validate_previous_colorist_proof(expected_commit)
        
        assert result["check"] == "previous_colorist_proof"
        assert result["passed"] is True
        assert result["actual_commit"] == expected_commit
    
    def test_validate_forbidden_actions(self):
        """Test forbidden actions validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ProductionDesignerValidator(project_root)
        
        result = validator.validate_forbidden_actions_not_executed()
        
        assert result["check"] == "forbidden_actions"
        assert result["passed"] is True
        assert len(result["violations"]) == 0


class TestProductionDesignerReviewer:
    """Test the production designer reviewer."""
    
    def test_review_accepts_valid_candidate(self):
        """Test that reviewer accepts a valid candidate."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        reviewer = ProductionDesignerReviewer(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        review = reviewer.review_candidate(candidate_path)
        
        assert review["overall_verdict"] in ["ACCEPTED", "REJECTED", "UNCERTAIN"]
        assert "visual_world" in review
        assert "location_environment" in review
        assert "set_design" in review
        assert "decor_background_coherence" in review
        assert "genre_era_style_consistency" in review
        assert "atmosphere" in review
        assert "scene_support" in review
    
    def test_review_missing_candidate_blocks_review(self):
        """Test that missing candidate blocks review."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        reviewer = ProductionDesignerReviewer(project_root)
        
        candidate_path = "nonexistent_path.png"
        review = reviewer.review_candidate(candidate_path)
        
        assert review["visual_world"]["status"] == "error"
        assert review["visual_world"]["passed"] is False


class TestProductionDesignerArtifacts:
    """Test the production designer artifacts manager."""
    
    def test_verdict_does_not_set_production_accepted(self):
        """Test that verdict does not set production_accepted to true."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ProductionDesignerArtifacts(project_root)
        
        review = {
            "candidate_path": "test.png",
            "candidate_sha256": "abc123",
            "defects_found": [],
            "overall_verdict": "ACCEPTED"
        }
        
        verdict = artifacts.create_verdict("ACCEPTED", review)
        
        assert verdict["production_accepted"] is False
    
    def test_accepted_state_transition(self):
        """Test accepted state transition."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ProductionDesignerArtifacts(project_root)
        
        assert artifacts._get_next_state("ACCEPTED") == "set_decorator_review_required"
        assert artifacts._get_next_action("ACCEPTED") == "set_decorator_review_required"
    
    def test_rejected_state_transition(self):
        """Test rejected state transition."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ProductionDesignerArtifacts(project_root)
        
        assert artifacts._get_next_state("REJECTED") == "visual_corrective_plan_required"
        assert artifacts._get_next_action("REJECTED") == "visual_corrective_plan_required"
    
    def test_manual_review_state_transition(self):
        """Test manual review state transition."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ProductionDesignerArtifacts(project_root)
        
        assert artifacts._get_next_state("UNCERTAIN") == "manual_visual_review_required"
        assert artifacts._get_next_action("UNCERTAIN") == "manual_visual_review_required"
    
    def test_corrective_plan_required_on_rejection(self):
        """Test that corrective plan is required on rejection."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ProductionDesignerArtifacts(project_root)
        
        review = {
            "candidate_path": "test.png",
            "candidate_sha256": "abc123",
            "defects_found": [{"component": "set_design", "issue": "inappropriate"}],
            "overall_verdict": "REJECTED"
        }
        
        corrective_plan = artifacts.create_corrective_plan(review)
        
        assert corrective_plan["corrective_plan_required"] is True
        assert corrective_plan["target_state"] == "visual_corrective_plan_required"
        assert len(corrective_plan["corrective_actions"]) > 0
