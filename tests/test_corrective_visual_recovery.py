import json
import pytest
from pathlib import Path


class TestCorrectiveVisualRecovery:
    """Tests for RC-COMBINE-V2-CORRECTIVE-VISUAL-RECOVERY-FULL-VERTICAL-001"""
    
    @pytest.fixture
    def project_root(self):
        return Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
    
    @pytest.fixture
    def state_path(self, project_root):
        return project_root / "output" / "control" / "state.json"
    
    @pytest.fixture
    def state(self, state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def agent_contract_path(self, project_root):
        return project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_agent_contract.json"
    
    @pytest.fixture
    def agent_contract(self, agent_contract_path):
        with open(agent_contract_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def tool_policy_path(self, project_root):
        return project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_tool_policy.json"
    
    @pytest.fixture
    def tool_policy(self, tool_policy_path):
        with open(tool_policy_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generation_gate_path(self, project_root):
        return project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_generation_gate.json"
    
    @pytest.fixture
    def generation_gate(self, generation_gate_path):
        with open(generation_gate_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generation_manifest_path(self, project_root):
        return project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_generation_manifest.json"
    
    @pytest.fixture
    def generation_manifest(self, generation_manifest_path):
        with open(generation_manifest_path, 'r') as f:
            return json.load(f)
    
    def test_agent_has_llm_brain_config(self, agent_contract):
        """Agent has LLM-brain config with deepseek-v4-flash as primary brain"""
        assert "llm_brain_config" in agent_contract
        assert agent_contract["llm_brain_config"]["primary_model"] == "deepseek-v4-flash"
    
    def test_agent_has_role_context(self, agent_contract):
        """Agent has role context for Corrective Visual Recovery"""
        assert "role_context" in agent_contract
        assert "Corrective Visual Recovery" in agent_contract["role_context"]["primary_role"]
    
    def test_tool_policy_blocks_retry(self, tool_policy):
        """Tool policy blocks retry attempts"""
        assert "forbidden_actions" in tool_policy
        forbidden_actions = [item["action"] for item in tool_policy["forbidden_actions"]]
        assert "retry" in forbidden_actions
        assert "second_generation" in forbidden_actions
    
    def test_tool_policy_blocks_assembly(self, tool_policy):
        """Tool policy blocks assembly and downstream"""
        forbidden_actions = [item["action"] for item in tool_policy["forbidden_actions"]]
        assert "assembly" in forbidden_actions
        assert "downstream" in forbidden_actions
    
    def test_tool_policy_blocks_production_acceptance(self, tool_policy):
        """Tool policy blocks production acceptance"""
        forbidden_actions = [item["action"] for item in tool_policy["forbidden_actions"]]
        assert "production_acceptance" in forbidden_actions
    
    def test_generation_gate_max_generations_one(self, generation_gate):
        """Generation gate allows max_generations=1 only"""
        assert generation_gate["generation_limits"]["max_generations"] == 1
    
    def test_generation_gate_one_shot_enforced(self, generation_gate):
        """Generation gate enforces one-shot generation"""
        gate_ids = [gate["gate_id"] for gate in generation_gate["gates"]]
        assert "one_shot_corrective_generation_gate" in gate_ids
    
    def test_workflow_patch_blocks_generic_portrait(self, project_root):
        """Workflow patch blocks generic portrait prompt terms"""
        workflow_patch_path = project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_workflow_patch.json"
        with open(workflow_patch_path, 'r') as f:
            patch = json.load(f)
        negative_additions = patch["prompt_patches"]["negative_prompt_additions"]
        assert "beauty portrait" in " ".join(negative_additions)
        assert "glamour shot" in " ".join(negative_additions)
    
    def test_workflow_patch_blocks_plain_background(self, project_root):
        """Workflow patch blocks plain background"""
        workflow_patch_path = project_root / "output" / "control" / "corrective_visual_recovery" / "corrective_visual_recovery_workflow_patch.json"
        with open(workflow_patch_path, 'r') as f:
            patch = json.load(f)
        negative_additions = patch["prompt_patches"]["negative_prompt_additions"]
        assert "plain background" in " ".join(negative_additions)
        assert "solid color background" in " ".join(negative_additions)
    
    def test_manifest_requires_real_readable_image(self, generation_manifest, project_root):
        """Manifest requires real readable image"""
        assert "generated_assets" in generation_manifest
        assert len(generation_manifest["generated_assets"]) == 1
        asset = generation_manifest["generated_assets"][0]
        asset_path = project_root / "output" / "assets" / asset["filename"]
        assert asset_path.exists()
        assert asset_path.stat().st_size > 0
        assert asset["sha256"] == "6aa2d486295184b41cf7c36a0433f8970da7876631b08eda8ee35f420d9b7314"
    
    def test_manifest_generation_count_one(self, generation_manifest):
        """Manifest shows generation_count=1"""
        assert generation_manifest["generation_count"] == 1
        assert generation_manifest["max_generations"] == 1
    
    def test_state_routes_to_operator_visual_review(self, state):
        """State routes to operator_visual_review_required after generation"""
        assert state["current_state"] == "operator_visual_review_required"
        assert state["next_allowed_action"] == "operator_visual_review_required"
    
    def test_production_accepted_remains_false(self, state):
        """production_accepted remains false"""
        assert state["production_accepted"] == False
    
    def test_corrective_visual_generation_performed(self, state):
        """Corrective visual generation performed"""
        assert state["corrective_visual_generation_performed"] == True
        assert state["comfyui_submit_executed"] == True
    
    def test_no_retry_attempted(self, state, generation_manifest):
        """No retry attempted"""
        assert state["retry_attempted"] == False
        assert generation_manifest["retry_attempted"] == False
    
    def test_no_second_generation_attempted(self, state, generation_manifest):
        """No second generation attempted"""
        assert state["second_generation_attempted"] == False
        assert generation_manifest["second_generation_attempted"] == False
    
    def test_prompt_id_real(self, generation_manifest):
        """Real prompt_id from ComfyUI generation"""
        assert generation_manifest["prompt_id"] == "e959a66a-4163-49c7-bd3c-e7318db2dd51"
        assert generation_manifest["prompt_id"] == "e959a66a-4163-49c7-bd3c-e7318db2dd51"
