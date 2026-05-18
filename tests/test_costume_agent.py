"""Tests for Costume Agent."""

import pytest
import json
from pathlib import Path
from datetime import datetime

from app.agents.costume.contract import CostumeAgentContract
from app.agents.costume.validator import CostumeValidator
from app.agents.costume.reviewer import CostumeReviewer
from app.agents.costume.artifacts import CostumeArtifacts
from app.agents.costume.runner import CostumeRunner


class TestCostumeAgentContract:
    """Tests for Costume Agent Contract."""
    
    def test_contract_exists(self):
        """Test that costume contract exists and forbids generation/retry/render/downstream."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        contract = CostumeAgentContract(project_root)
        contract_data = contract.create_contract()
        
        assert contract_data is not None
        assert contract_data["agent_id"] == "costume_agent"
        assert contract_data["can_execute_generation"] == False
        assert contract_data["can_retry"] == False
        assert contract_data["can_accept_visual"] == False
        assert contract_data["can_set_production_accepted"] == False
        assert contract_data["can_run_assembly"] == False
        assert contract_data["can_run_downstream"] == False
        assert contract_data["can_edit_image"] == False
        assert contract_data["can_submit_comfyui"] == False
        assert contract_data["can_modify_costume"] == False
        assert contract_data["can_modify_actor_body"] == False
        assert contract_data["can_perform_visual_qa_final_acceptance"] == False
        assert contract_data["can_perform_operator_acceptance"] == False
        assert contract_data["can_run_preview_render"] == False
        assert contract_data["can_run_final_render"] == False
        assert contract_data["can_generate_voice"] == False
        assert contract_data["can_generate_audio"] == False
    
    def test_review_authorization_forbids_generation(self):
        """Test that review authorization does not authorize generation."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        contract = CostumeAgentContract(project_root)
        auth = contract.create_review_authorization()
        
        assert auth["generation_authorized"] == False
        assert auth["retry_authorized"] == False
        assert auth["render_authorized"] == False
        assert auth["downstream_authorized"] == False
        assert auth["new_generation_forbidden"] == True
        assert auth["retry_forbidden"] == True
        assert auth["second_generation_forbidden"] == True
        assert auth["comfyui_submit_forbidden"] == True
        assert auth["image_editing_forbidden"] == True
        assert auth["costume_modification_forbidden"] == True
        assert auth["actor_body_modification_forbidden"] == True
        assert auth["render_forbidden"] == True
        assert auth["visual_qa_final_acceptance_forbidden"] == True
        assert auth["operator_acceptance_by_agent_forbidden"] == True
        assert auth["assembly_forbidden"] == True
        assert auth["preview_render_forbidden"] == True
        assert auth["final_render_forbidden"] == True
        assert auth["voice_audio_forbidden"] == True
        assert auth["downstream_forbidden"] == True
        assert auth["production_accepted_forbidden"] == True


class TestCostumeValidator:
    """Tests for Costume Validator."""
    
    def test_review_accepts_valid_candidate_path(self):
        """Test that review accepts valid candidate path."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        validator = CostumeValidator(project_root)
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        
        validation = validator.validate_candidate_exists(candidate_path)
        assert validation["passed"] == True
    
    def test_missing_candidate_blocks_review(self):
        """Test that missing candidate blocks review."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        validator = CostumeValidator(project_root)
        
        validation = validator.validate_candidate_exists("nonexistent.png")
        assert validation["passed"] == False
        assert "not found" in validation["message"].lower()
    
    def test_sha_mismatch_blocks_or_reports_blocker(self):
        """Test that SHA mismatch blocks or reports blocker."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        validator = CostumeValidator(project_root)
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        
        # Test with wrong SHA
        validation = validator.validate_candidate_sha256(candidate_path, "wrongsha256")
        assert validation["passed"] == False
        assert "mismatch" in validation["message"].lower()
        
        # Test with correct SHA
        validation = validator.validate_candidate_sha256(
            candidate_path, 
            "53f46d3dd50da408bfcf65e764fa9ca14630d568d96b1731a5bc0ad16ea4f68b"
        )
        assert validation["passed"] == True


class TestCostumeReviewer:
    """Tests for Costume Reviewer."""
    
    def test_visible_costume_reviewed_properly(self):
        """Test that visible costume is reviewed properly."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        reviewer = CostumeReviewer(project_root)
        candidate_path = "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\assets\\camera_operator_full_frame_corrective\\camera_operator_full_frame_20260518_183835_757e09a9_.png"
        
        review = reviewer.review_candidate(candidate_path)
        
        # Check that visible costume review is performed
        assert review["visible_costume_clothing"]["status"] == "reviewed"
        assert review["visible_costume_clothing"]["costume_visible"] == True
        assert review["visible_costume_clothing"]["passed"] == True
        
        # Check that other reviews are also performed
        assert review["outfit_consistency_with_character"]["status"] == "reviewed"
        assert review["costume_style_coherence"]["status"] == "reviewed"
        assert review["genre_era_style_consistency"]["status"] == "reviewed"
        assert review["clothing_artifacts"]["status"] == "reviewed"
        assert review["costume_continuity_risk"]["status"] == "reviewed"


class TestCostumeArtifacts:
    """Tests for Costume Artifacts."""
    
    def test_verdict_does_not_set_production_accepted_true(self):
        """Test that verdict does not set production_accepted=true."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        artifacts = CostumeArtifacts(project_root)
        
        review = {
            "candidate_path": "test.png",
            "candidate_sha256": "abc123",
            "defects_found": []
        }
        
        verdict_data = artifacts.create_verdict("ACCEPTED", review)
        assert verdict_data["production_accepted"] == False
        
        verdict_data = artifacts.create_verdict("REJECTED", review)
        assert verdict_data["production_accepted"] == False
        
        verdict_data = artifacts.create_verdict("UNCERTAIN", review)
        assert verdict_data["production_accepted"] == False


class TestCostumeStateTransitions:
    """Tests for Costume state transitions."""
    
    def test_accepted_state_transition(self):
        """Test accepted state transition."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        artifacts = CostumeArtifacts(project_root)
        
        next_state = artifacts._get_next_state("ACCEPTED")
        next_action = artifacts._get_next_action("ACCEPTED")
        
        assert next_state == "script_supervisor_continuity_review_required"
        assert next_action == "script_supervisor_continuity_review_required"
    
    def test_rejected_state_transition(self):
        """Test rejected state transition."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        artifacts = CostumeArtifacts(project_root)
        
        next_state = artifacts._get_next_state("REJECTED")
        next_action = artifacts._get_next_action("REJECTED")
        
        assert next_state == "visual_corrective_plan_required"
        assert next_action == "visual_corrective_plan_required"
    
    def test_uncertain_state_transition(self):
        """Test uncertain state transition."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        artifacts = CostumeArtifacts(project_root)
        
        next_state = artifacts._get_next_state("UNCERTAIN")
        next_action = artifacts._get_next_action("UNCERTAIN")
        
        assert next_state == "manual_visual_review_required"
        assert next_action == "manual_visual_review_required"


class TestCostumeCorrectivePlan:
    """Tests for Costume corrective plan."""
    
    def test_corrective_plan_required_on_rejection(self):
        """Test that corrective plan is required on rejection."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        artifacts = CostumeArtifacts(project_root)
        
        review = {
            "defects_found": [
                {"component": "visible_costume_clothing", "issue": "Costume defect"}
            ]
        }
        
        plan = artifacts.create_corrective_plan(review)
        assert plan["corrective_plan_required"] == True
        assert plan["target_state"] == "visual_corrective_plan_required"
        assert plan["production_accepted"] == False
    


class TestCostumeRunnerIntegration:
    """Integration tests for Costume Runner."""
    
    def test_artifact_index_and_episode_ledger_updated(self):
        """Test that artifact_index and episode_ledger are updated."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        runner = CostumeRunner(project_root)
        
        # Check that artifact_index exists and has costume-related fields
        artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
        assert artifact_index_path.exists()
        
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        assert "costume_review_executed" in artifact_index
        assert "costume_verdict" in artifact_index
        assert "costume_contract_created" in artifact_index
        assert "costume_review_authorization_created" in artifact_index
        assert "costume_review_report_created" in artifact_index
        assert "costume_verdict_created" in artifact_index
        
        # Check that episode_ledger exists and has costume event
        episode_ledger_path = Path(project_root) / "output" / "control" / "episode_ledger.json"
        assert episode_ledger_path.exists()
        
        with open(episode_ledger_path, 'r') as f:
            episode_ledger = json.load(f)
        
        # Find the costume review event
        costume_events = [e for e in episode_ledger if e.get("event_type") == "costume_review"]
        assert len(costume_events) > 0
        
        costume_event = costume_events[-1]
        assert costume_event["task_id"] == "RC-COMBINE-V2-COSTUME-VERTICAL-SLICE-001"
        assert costume_event["generation_performed"] == False
        assert costume_event["retry_attempted"] == False
        assert costume_event["comfyui_submit_executed"] == False
        assert costume_event["image_editing_executed"] == False
        assert costume_event["costume_modification_executed"] == False
        assert costume_event["actor_body_modification_executed"] == False
        assert costume_event["render_executed"] == False
        assert costume_event["assembly_executed"] == False
        assert costume_event["downstream_executed"] == False
        assert costume_event["production_accepted"] == False
    
    def test_props_proof_tracking_check(self):
        """Test Props proof tracking check."""
        project_root = "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01"
        validator = CostumeValidator(project_root)
        
        validation = validator.validate_previous_props_proof("f248d8e")
        assert validation["passed"] == True
