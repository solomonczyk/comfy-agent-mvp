"""
Tests for Editorial Preview Agent workflow.
"""

import os
import json
import pytest
from pathlib import Path


class TestEditorialPreviewWorkflow:
    """Test suite for editorial preview workflow from accepted visual."""
    
    @pytest.fixture
    def project_root(self):
        return Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
    
    @pytest.fixture
    def accepted_visual_path(self, project_root):
        return project_root / "output" / "assets" / "corrective_visual_recovery__00001_.png"
    
    @pytest.fixture
    def editorial_preview_dir(self, project_root):
        return project_root / "output" / "control" / "editorial_preview"
    
    @pytest.fixture
    def preview_dir(self, project_root):
        return project_root / "output" / "preview"
    
    def test_accepted_visual_candidate_is_real_and_readable(self, accepted_visual_path):
        """Test that accepted visual candidate exists and is readable."""
        assert accepted_visual_path.exists(), "Accepted visual candidate must exist"
        assert accepted_visual_path.is_file(), "Accepted visual must be a file"
        assert os.access(accepted_visual_path, os.R_OK), "Accepted visual must be readable"
    
    def test_accepted_visual_dimensions(self, accepted_visual_path):
        """Test that accepted visual has correct dimensions (1344x768)."""
        from PIL import Image
        img = Image.open(accepted_visual_path)
        width, height = img.size
        assert width == 1344, f"Width must be 1344, got {width}"
        assert height == 768, f"Height must be 768, got {height}"
    
    def test_agent_has_llm_brain_config(self, editorial_preview_dir):
        """Test that agent has LLM-brain config with deepseek-v4-flash."""
        brain_config_path = editorial_preview_dir / "editorial_preview_brain_config.json"
        assert brain_config_path.exists(), "Brain config must exist"
        
        with open(brain_config_path) as f:
            config = json.load(f)
        
        assert config["model_name"] == "deepseek-v4-flash", "Model must be deepseek-v4-flash"
        assert config["model_provider"] == "deepseek", "Provider must be deepseek"
        assert config["brain_restrictions"]["no_hidden_api_calls"] == True, "No hidden API calls must be enforced"
    
    def test_agent_has_role_context(self, editorial_preview_dir):
        """Test that agent has role context as Editor / Editorial Preview Agent."""
        brain_config_path = editorial_preview_dir / "editorial_preview_brain_config.json"
        with open(brain_config_path) as f:
            config = json.load(f)
        
        role_context = config["role_context"]
        assert role_context["agent_role"] == "Editor / Editorial Preview Agent"
        assert "preview_render_only" in role_context["decision_scope"]
    
    def test_agent_has_tool_policy(self, editorial_preview_dir):
        """Test that agent has tool policy blocking generation/retry/voice/assembly/downstream."""
        tool_policy_path = editorial_preview_dir / "editorial_preview_tool_policy.json"
        assert tool_policy_path.exists(), "Tool policy must exist"
        
        with open(tool_policy_path) as f:
            policy = json.load(f)
        
        # Check allowed tools
        assert "filesystem" in policy["allowed_tools"]
        assert "image_metadata" in policy["allowed_tools"]
        assert "preview_render" in policy["allowed_tools"]
        
        # Check forbidden tools
        forbidden = policy["forbidden_tools"]
        assert forbidden["comfyui_generation"]["allowed"] == False
        assert forbidden["retry"]["allowed"] == False
        assert forbidden["assembly"]["allowed"] == False
        assert forbidden["voice"]["allowed"] == False
        assert forbidden["downstream"]["allowed"] == False
    
    def test_agent_has_decision_layer(self, editorial_preview_dir):
        """Test that agent has decision layer for motion treatment and static prevention."""
        decision_path = editorial_preview_dir / "editorial_preview_decision.json"
        assert decision_path.exists(), "Decision layer must exist"
        
        with open(decision_path) as f:
            decision = json.load(f)
        
        assert "motion_treatment_decision" in decision
        assert "static_duplicate_prevention" in decision
        assert decision["render_count_limit"] == 1
    
    def test_agent_has_gates(self, editorial_preview_dir):
        """Test that agent has gates: accepted visual intake, preview render, operator preview review."""
        contract_path = editorial_preview_dir / "editorial_preview_agent_contract.json"
        assert contract_path.exists(), "Agent contract must exist"
        
        with open(contract_path) as f:
            contract = json.load(f)
        
        gates = contract["gates"]
        assert len(gates) == 3
        gate_names = [g["gate_name"] for g in gates]
        assert "accepted_visual_intake_gate" in gate_names
        assert "preview_render_gate" in gate_names
        assert "operator_preview_review_gate" in gate_names
    
    def test_preview_render_gate_allows_exactly_one_preview(self, editorial_preview_dir):
        """Test that preview render gate allows exactly one preview render."""
        render_gate_path = editorial_preview_dir / "editorial_preview_render_gate.json"
        assert render_gate_path.exists(), "Render gate must exist"
        
        with open(render_gate_path) as f:
            gate = json.load(f)
        
        assert gate["authorization"]["max_renders"] == 1
        assert gate["authorization"]["current_render_count"] == 0
        assert gate["render_constraints"]["single_render_limit"] == True
    
    def test_preview_artifacts_exist_and_are_readable(self, preview_dir):
        """Test that preview artifacts (mp4, gif, contact sheet) exist and are readable."""
        mp4_path = preview_dir / "preview_lowres.mp4"
        gif_path = preview_dir / "preview.gif"
        contact_sheet_path = preview_dir / "contact_sheet.jpg"
        
        assert mp4_path.exists(), "MP4 preview must exist"
        assert gif_path.exists(), "GIF preview must exist"
        assert contact_sheet_path.exists(), "Contact sheet must exist"
        
        assert os.access(mp4_path, os.R_OK), "MP4 must be readable"
        assert os.access(gif_path, os.R_OK), "GIF must be readable"
        assert os.access(contact_sheet_path, os.R_OK), "Contact sheet must be readable"
    
    def test_state_routes_to_operator_preview_review_required(self, project_root):
        """Test that state routes to operator_preview_review_required."""
        state_path = project_root / "output" / "control" / "state.json"
        with open(state_path) as f:
            state = json.load(f)
        
        assert state["current_state"] == "operator_preview_review_required"
        assert state["next_allowed_action"] == "operator_preview_review_required"
    
    def test_production_accepted_remains_false(self, project_root):
        """Test that production_accepted remains false."""
        state_path = project_root / "output" / "control" / "state.json"
        with open(state_path) as f:
            state = json.load(f)
        
        assert state["production_accepted"] == False
        
        # Also check in operator preview review packet
        packet_path = project_root / "output" / "control" / "editorial_preview" / "operator_preview_review_packet.json"
        with open(packet_path) as f:
            packet = json.load(f)
        
        assert packet["production_accepted"] == False
