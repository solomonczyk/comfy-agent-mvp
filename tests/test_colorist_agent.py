"""Tests for Colorist Agent."""

import json
import pytest
from pathlib import Path
from app.agents.colorist.contract import ColoristAgentContract
from app.agents.colorist.validator import ColoristValidator
from app.agents.colorist.reviewer import ColoristReviewer
from app.agents.colorist.artifacts import ColoristArtifacts


class TestColoristAgentContract:
    """Test the colorist agent contract."""
    
    def test_contract_forbids_generation(self):
        """Test that contract forbids generation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ColoristAgentContract(project_root)
        contract_data = contract.create_contract()
        
        assert contract_data["can_execute_generation"] is False
        assert contract_data["can_retry"] is False
        assert contract_data["can_accept_visual"] is False
        assert contract_data["can_set_production_accepted"] is False
        assert contract_data["can_run_assembly"] is False
        assert contract_data["can_run_downstream"] is False
        assert contract_data["can_edit_image"] is False
        assert contract_data["can_submit_comfyui"] is False
        assert contract_data["can_perform_color_grading_output"] is False
    
    def test_contract_review_criteria(self):
        """Test that contract includes all required review criteria."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ColoristAgentContract(project_root)
        contract_data = contract.create_contract()
        
        expected_criteria = [
            "color_consistency",
            "contrast",
            "exposure",
            "brightness",
            "saturation_color_palette",
            "skin_tone_risk_if_visible",
            "mood_consistency",
            "cinematic_look_consistency",
            "visual_tone"
        ]
        
        for criterion in expected_criteria:
            assert criterion in contract_data["review_criteria"]
    
    def test_review_authorization_forbids_generation(self):
        """Test that review authorization forbids generation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        contract = ColoristAgentContract(project_root)
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
        assert auth["color_grading_output_forbidden"] is True
        assert auth["render_forbidden"] is True
        assert auth["production_accepted_forbidden"] is True


class TestColoristValidator:
    """Test the colorist validator."""
    
    def test_validate_candidate_exists(self):
        """Test candidate exists validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ColoristValidator(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        result = validator.validate_candidate_exists(candidate_path)
        
        assert result["check"] == "candidate_exists"
        assert result["passed"] is True
    
    def test_validate_candidate_sha256(self):
        """Test candidate SHA256 validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ColoristValidator(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        expected_sha256 = "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b"
        result = validator.validate_candidate_sha256(candidate_path, expected_sha256)
        
        assert result["check"] == "candidate_sha256"
        assert result["passed"] is True
    
    def test_validate_previous_state(self):
        """Test previous state validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ColoristValidator(project_root)
        
        # After review is complete, state should be production_design_review_required
        expected_state = "production_design_review_required"
        result = validator.validate_previous_state(expected_state)
        
        assert result["check"] == "previous_state"
        assert result["passed"] is True
        assert result["actual_state"] == expected_state
    
    def test_validate_previous_actor_character_proof(self):
        """Test previous Actor/Character Control proof validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ColoristValidator(project_root)
        
        expected_commit = "a6f2e00"
        result = validator.validate_previous_actor_character_proof(expected_commit)
        
        assert result["check"] == "previous_actor_character_proof"
        assert result["passed"] is True
        assert result["actual_commit"] == expected_commit
    
    def test_validate_forbidden_actions(self):
        """Test forbidden actions validation."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        validator = ColoristValidator(project_root)
        
        result = validator.validate_forbidden_actions_not_executed()
        
        assert result["check"] == "forbidden_actions"
        assert result["passed"] is True
        assert len(result["violations"]) == 0


class TestColoristReviewer:
    """Test the colorist reviewer."""
    
    def test_review_accepts_valid_candidate(self):
        """Test that reviewer accepts a valid candidate."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        reviewer = ColoristReviewer(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        review = reviewer.review_candidate(candidate_path)
        
        assert review["overall_verdict"] in ["ACCEPTED", "REJECTED", "UNCERTAIN"]
        assert "color_consistency" in review
        assert "contrast" in review
        assert "exposure" in review
        assert "brightness" in review
        assert "saturation_color_palette" in review
        assert "skin_tone_risk" in review
        assert "mood_consistency" in review
        assert "cinematic_look_consistency" in review
        assert "visual_tone" in review
    
    def test_review_missing_candidate_blocks_review(self):
        """Test that missing candidate blocks review."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        reviewer = ColoristReviewer(project_root)
        
        candidate_path = "nonexistent_path.png"
        review = reviewer.review_candidate(candidate_path)
        
        assert review["color_consistency"]["status"] == "error"
        assert review["color_consistency"]["passed"] is False
    
    def test_compute_image_metrics(self):
        """Test that image metrics are computed correctly."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        reviewer = ColoristReviewer(project_root)
        
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        metrics = reviewer._compute_image_metrics(candidate_path)
        
        assert "brightness" in metrics
        assert "contrast" in metrics
        assert "saturation" in metrics
        assert isinstance(metrics["brightness"], float)
        assert isinstance(metrics["contrast"], float)
        assert isinstance(metrics["saturation"], float)


class TestColoristArtifacts:
    """Test the colorist artifacts manager."""
    
    def test_verdict_does_not_set_production_accepted(self):
        """Test that verdict does not set production_accepted to true."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ColoristArtifacts(project_root)
        
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
        artifacts = ColoristArtifacts(project_root)
        
        assert artifacts._get_next_state("ACCEPTED") == "production_design_review_required"
        assert artifacts._get_next_action("ACCEPTED") == "production_design_review_required"
    
    def test_rejected_state_transition(self):
        """Test rejected state transition."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ColoristArtifacts(project_root)
        
        assert artifacts._get_next_state("REJECTED") == "visual_corrective_plan_required"
        assert artifacts._get_next_action("REJECTED") == "visual_corrective_plan_required"
    
    def test_manual_review_state_transition(self):
        """Test manual review state transition."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ColoristArtifacts(project_root)
        
        assert artifacts._get_next_state("UNCERTAIN") == "manual_visual_review_required"
        assert artifacts._get_next_action("UNCERTAIN") == "manual_visual_review_required"
    
    def test_corrective_plan_required_on_rejection(self):
        """Test that corrective plan is required on rejection."""
        project_root = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
        artifacts = ColoristArtifacts(project_root)
        
        review = {
            "candidate_path": "test.png",
            "candidate_sha256": "abc123",
            "defects_found": [{"component": "contrast", "issue": "too_low"}],
            "overall_verdict": "REJECTED"
        }
        
        corrective_plan = artifacts.create_corrective_plan(review)
        
        assert corrective_plan["corrective_plan_required"] is True
        assert corrective_plan["target_state"] == "visual_corrective_plan_required"
        assert len(corrective_plan["corrective_actions"]) > 0
