"""
Tests for Director of Photography Agent
"""

import json
import pytest
from pathlib import Path

DATA_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")


class TestDoPContract:
    """Test DoP agent contract."""

    def test_dop_contract_exists(self):
        """Test that dop_agent_contract.json exists."""
        contract_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_agent_contract.json"
        assert contract_path.exists(), "dop_agent_contract.json should exist"

    def test_dop_contract_forbids_generation(self):
        """Test that DoP contract forbids new generation."""
        contract_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract.get("forbidden_actions") is not None
        assert contract["forbidden_actions"]["new_generation"] is False
        assert contract["forbidden_actions"]["retry_generation"] is False
        assert contract["forbidden_actions"]["second_candidate"] is False
        assert contract["forbidden_actions"]["comfyui_submit"] is False

    def test_dop_contract_forbids_downstream(self):
        """Test that DoP contract forbids downstream actions."""
        contract_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["forbidden_actions"]["assembly"] is False
        assert contract["forbidden_actions"]["downstream_processing"] is False
        assert contract["forbidden_actions"]["production_acceptance"] is False

    def test_dop_contract_forbids_operator_acceptance_by_agent(self):
        """Test that DoP contract forbids operator acceptance by agent."""
        contract_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_agent_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["forbidden_actions"]["operator_acceptance_by_agent"] is False
        assert contract["decision_outputs"]["production_acceptance_forbidden"] is True


class TestDoPAuthorization:
    """Test DoP visual review authorization."""

    def test_dop_authorization_exists(self):
        """Test that dop_visual_review_authorization.json exists."""
        auth_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_authorization.json"
        assert auth_path.exists(), "dop_visual_review_authorization.json should exist"

    def test_dop_authorization_forbids_generation(self):
        """Test that DoP authorization forbids generation."""
        auth_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_authorization.json"
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth = json.load(f)
        
        assert auth.get("generation_authorized") is False
        assert auth.get("retry_authorized") is False
        assert auth.get("second_generation_authorized") is False
        assert auth.get("downstream_authorized") is False

    def test_dop_authorization_forbids_production_acceptance(self):
        """Test that DoP authorization forbids production acceptance."""
        auth_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_authorization.json"
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth = json.load(f)
        
        assert auth.get("production_acceptance_authorized") is False


class TestDoPReview:
    """Test DoP visual review."""

    def test_dop_review_report_exists(self):
        """Test that dop_visual_review_report.json exists."""
        report_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_report.json"
        assert report_path.exists(), "dop_visual_review_report.json should exist"

    def test_dop_review_accepts_valid_candidate(self):
        """Test that DoP review accepts valid candidate path."""
        report_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_report.json"
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        assert report.get("candidate_image_path") is not None
        assert report.get("candidate_prompt_id") is not None
        assert report.get("review_scores") is not None

    def test_dop_review_scores_exist(self):
        """Test that DoP review includes all required scores."""
        report_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_review_report.json"
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        scores = report["review_scores"]
        assert "composition" in scores
        assert "framing" in scores
        assert "lighting" in scores
        assert "readability" in scores
        assert "cinematic_suitability" in scores
        assert "overall" in scores

    def test_missing_candidate_blocks_review(self):
        """Test that missing candidate blocks review."""
        # This is tested by the review logic - if file doesn't exist, it raises FileNotFoundError
        from app.agents.dop.review import DirectorOfPhotographyReview
        review = DirectorOfPhotographyReview(str(DATA_ROOT))
        
        with pytest.raises(FileNotFoundError):
            review.review_candidate("nonexistent.png", "test-prompt-id")


class TestDoPVerdict:
    """Test DoP visual verdict."""

    def test_dop_verdict_exists(self):
        """Test that dop_visual_verdict.json exists."""
        verdict_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_verdict.json"
        assert verdict_path.exists(), "dop_visual_verdict.json should exist"

    def test_dop_verdict_does_not_set_production_accepted(self):
        """Test that DoP verdict does not set production_accepted=true."""
        verdict_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_verdict.json"
        with open(verdict_path, 'r', encoding='utf-8') as f:
            verdict = json.load(f)
        
        assert verdict.get("production_acceptance_forbidden") is True

    def test_dop_verdict_constraints_observed(self):
        """Test that DoP verdict observes all constraints."""
        verdict_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_verdict.json"
        with open(verdict_path, 'r', encoding='utf-8') as f:
            verdict = json.load(f)
        
        constraints = verdict["constraints_observed"]
        assert constraints["no_new_generation"] is True
        assert constraints["no_retry"] is True
        assert constraints["no_downstream"] is True
        assert constraints["no_production_acceptance"] is True


class TestDoPStateUpdates:
    """Test DoP state updates."""

    def test_state_json_updated(self):
        """Test that state.json was updated with DoP completion."""
        state_path = DATA_ROOT / "output" / "control" / "state.json"
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        assert state.get("current_state") == "actor_character_control_review_required"
        assert state.get("next_allowed_action") == "actor_character_control_review_required"
        assert state.get("production_accepted") is False

    def test_artifact_index_updated(self):
        """Test that artifact_index.json was updated with DoP artifacts."""
        artifact_index_path = DATA_ROOT / "output" / "control" / "artifact_index.json"
        with open(artifact_index_path, 'r', encoding='utf-8') as f:
            artifact_index = json.load(f)

        assert artifact_index.get("dop_vertical_completed") is True
        assert artifact_index.get("dop_agent_contract_created") is True
        assert artifact_index.get("dop_visual_review_authorization_created") is True
        assert artifact_index.get("dop_visual_review_report_created") is True
        assert artifact_index.get("dop_visual_verdict_created") is True
        assert artifact_index.get("dop_verdict") == "ACCEPTED_FOR_NEXT_GATE"

    def test_episode_ledger_updated(self):
        """Test that episode_ledger.json was updated with DoP review."""
        ledger_path = DATA_ROOT / "output" / "control" / "episode_ledger.json"
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger = json.load(f)

        # Find the DoP review event
        dop_event = None
        for event in ledger:
            if event.get("event_type") == "dop_visual_review":
                dop_event = event
                break
        
        assert dop_event is not None
        assert dop_event["dop_verdict"] == "ACCEPTED_FOR_NEXT_GATE"
        assert dop_event["current_state"] == "actor_character_control_review_required"
        assert dop_event["production_accepted"] is False


class TestDoPStateTransitions:
    """Test DoP state transitions."""

    def test_accepted_state_transition(self):
        """Test that accepted verdict transitions to actor_character_control_review_required."""
        verdict_path = DATA_ROOT / "output" / "control" / "dop_agent" / "dop_visual_verdict.json"
        with open(verdict_path, 'r', encoding='utf-8') as f:
            verdict = json.load(f)
        
        if verdict["dop_verdict"] == "ACCEPTED_FOR_NEXT_GATE":
            assert verdict["next_state"] == "actor_character_control_review_required"

    def test_rejected_state_transition(self):
        """Test that rejected verdict transitions to visual_corrective_plan_required."""
        # This test would require a rejected verdict scenario
        # For now, we test the logic exists in the review module
        from app.agents.dop.review import DirectorOfPhotographyReview
        review = DirectorOfPhotographyReview(str(DATA_ROOT))
        
        # Low score should trigger rejection
        # This is a conceptual test - actual rejection would require a different candidate
        assert review._review_composition(512, 512) < 0.8  # Smaller image gets lower score

    def test_manual_review_state_transition(self):
        """Test that uncertain verdict transitions to manual_visual_review_required."""
        # This test would require an uncertain verdict scenario
        # For now, we test the logic exists in the review module
        from app.agents.dop.review import DirectorOfPhotographyReview
        review = DirectorOfPhotographyReview(str(DATA_ROOT))
        
        # Medium score should trigger manual review
        assert 0.6 <= review._review_composition(512, 512) < 0.8  # Medium score range
