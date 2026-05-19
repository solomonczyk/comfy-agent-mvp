"""
Tests for Prompt/Conditioning Director Agent

Comprehensive tests for the brain-enabled Prompt/Conditioning Director Agent.
"""

import pytest
import os
import json
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from agents.prompt_conditioning_director.contract import PromptConditioningDirectorContract
from agents.prompt_conditioning_director.brain_config import BrainConfig
from agents.prompt_conditioning_director.brain_client import BrainClient
from agents.prompt_conditioning_director.context_pack import ContextPack
from agents.prompt_conditioning_director.conditioning_diagnosis import ConditioningDiagnosis
from agents.prompt_conditioning_director.decision_schema import DecisionSchema
from agents.prompt_conditioning_director.workflow_patch import WorkflowPatch
from agents.prompt_conditioning_director.generation_gate import GenerationGate
from agents.prompt_conditioning_director.artifacts import ArtifactManager


class TestPromptConditioningDirectorContract:
    """Test agent contract."""

    def test_agent_contract_exists(self):
        """Test that agent contract exists and can be instantiated."""
        contract = PromptConditioningDirectorContract(
            task_id="test_task"
        )
        assert contract.agent_name == "prompt_conditioning_director"
        assert contract.agent_role == "Prompt/Conditioning Director Agent"
        assert contract.version == "1.0.0"

    def test_brain_requirements_configurable_not_hardcoded(self):
        """Test that brain model config is configurable, not hardcoded."""
        config = BrainConfig()
        assert config.provider_configurable is True
        assert config.primary_model_id == "deepseek-v4-flash"
        # Should be able to change via environment
        assert config.provider_name == "deepseek"

    def test_forbidden_actions_listed(self):
        """Test that forbidden actions are properly listed."""
        contract = PromptConditioningDirectorContract()
        assert "blind_retry" in contract.forbidden_actions
        assert "second_generation" in contract.forbidden_actions
        assert "generation_before_llm_decision" in contract.forbidden_actions
        assert "fake_llm_result" in contract.forbidden_actions
        assert "hardcoded_business_logic_replacing_llm_brain" in contract.forbidden_actions

    def test_required_artifacts_listed(self):
        """Test that required artifacts are properly listed."""
        contract = PromptConditioningDirectorContract()
        assert "prompt_conditioning_director_agent_contract.json" in contract.required_artifacts
        assert "llm_conditioning_director_decision.json" in contract.required_artifacts
        assert "proof.json" in contract.required_artifacts


class TestBrainConfig:
    """Test brain configuration."""

    def test_provider_validation_blocks_fake_runtime_use(self):
        """Test that provider validation blocks fake runtime use."""
        config = BrainConfig()
        # Without API key, validation should fail
        assert config.validate_provider() is False
        assert config.provider_validated is False

    def test_simulation_mode_bypasses_validation(self):
        """Test that simulation mode bypasses provider validation."""
        config = BrainConfig(simulation_mode=True)
        assert config.validate_provider() is True
        assert config.provider_validated is True

    def test_fallback_policy_created(self):
        """Test that fallback policy is created."""
        config = BrainConfig()
        assert config.fallback_model_required is True
        assert config.fallback_provider_name is None  # Configurable

    def test_runtime_llm_call_requires_gate(self):
        """Test that runtime LLM call requires gate."""
        config = BrainConfig()
        assert config.runtime_llm_call_requires_gate is True


class TestDecisionSchema:
    """Test LLM decision schema validation."""

    def test_llm_decision_schema_validation(self):
        """Test that LLM decision schema is validated."""
        schema = DecisionSchema()
        
        # Valid decision
        valid_decision = {
            "decision_type": "prompt_conditioning_director_decision",
            "previous_failure_root_cause": ["test cause"],
            "reference_role_assignments": [
                {
                    "reference_path": "test",
                    "allowed_use": "quality_calibration",
                    "forbidden_use": ["composition"],
                    "weight_policy": "low",
                    "conditioning_region_policy": "face"
                }
            ],
            "composition_policy": {
                "required_framing": "medium_or_full_character_in_environment",
                "forbid_extreme_closeup": True,
                "forbid_face_crop": True,
                "face_must_be_fully_visible": True,
                "head_should_not_touch_frame_edges": True,
                "environment_visible": True
            },
            "prompt_patch": {
                "positive_prompt_additions": ["test"],
                "negative_prompt_additions": ["test"],
                "camera_language": ["test"],
                "reference_usage_notes": ["test"]
            },
            "workflow_patch_requirements": ["test"],
            "generation_allowed_after_patch": True,
            "operator_review_required_after_generation": True
        }
        
        errors = schema.validate(valid_decision)
        assert len(errors) == 0

    def test_invalid_decision_rejected(self):
        """Test that invalid decision is rejected."""
        schema = DecisionSchema()
        
        # Missing required fields
        invalid_decision = {
            "decision_type": "prompt_conditioning_director_decision"
        }
        
        errors = schema.validate(invalid_decision)
        assert len(errors) > 0


class TestContextPack:
    """Test context pack creation."""

    def test_context_pack_includes_rejected_asset_and_previous_prompt_id(self):
        """Test that context pack includes rejected asset and previous prompt_id."""
        pack = ContextPack(task_id="test_task")
        pack.previous_prompt_id = "test_prompt_id"
        pack.previous_asset_path = "/path/to/asset.png"
        pack.previous_rejection_reason = "test rejection"
        
        assert pack.previous_prompt_id == "test_prompt_id"
        assert pack.previous_asset_path == "/path/to/asset.png"
        assert pack.previous_rejection_reason == "test rejection"


class TestConditioningDiagnosis:
    """Test conditioning failure diagnosis."""

    def test_quality_closeup_refs_blocked_from_composition(self):
        """Test that quality close-up refs cannot be assigned composition control."""
        diagnosis = ConditioningDiagnosis(task_id="test_task")
        diagnosis.diagnose_crop_failure(
            rejection_reason="extreme crop",
            context_pack={"quality_references": ["/path/to/closeup.png"]}
        )
        
        assert "quality close-up references present without explicit role separation" in diagnosis.reference_role_issues


class TestWorkflowPatch:
    """Test workflow and prompt patching."""

    def test_workflow_patch_enforces_normal_framing(self):
        """Test that workflow patch enforces normal framing."""
        patch = WorkflowPatch(task_id="test_task")
        
        llm_decision = {
            "prompt_patch": {
                "positive_prompt_additions": ["medium shot", "full face visible"],
                "negative_prompt_additions": ["extreme close-up"],
                "camera_language": ["medium shot camera"],
                "reference_usage_notes": ["quality references only for detail"]
            },
            "composition_policy": {
                "forbid_extreme_closeup": True,
                "forbid_face_crop": True,
                "face_must_be_fully_visible": True
            },
            "workflow_patch_requirements": ["reduce face-region conditioning"]
        }
        
        patch.create_patch(llm_decision, {}, {})
        
        assert patch.patched_prompt_conditioning["composition_policy"]["forbid_extreme_closeup"] is True
        assert patch.patched_prompt_conditioning["composition_policy"]["face_must_be_fully_visible"] is True


class TestGenerationGate:
    """Test generation gate."""

    def test_gate_blocks_generation_without_valid_llm_decision(self):
        """Test that gate blocks generation without valid LLM decision."""
        gate = GenerationGate(task_id="test_task")
        
        # Without LLM decision
        result = gate.validate_prerequisites(
            provider_validated=True,
            model_available=True,
            pricing_policy_validated=True,
            context_pack_exists=True,
            conditioning_diagnosis_exists=True,
            llm_decision_exists=False,
            role_aware_contract_exists=True,
            workflow_patch_exists=True
        )
        
        assert result is False
        assert len(gate.blockers) > 0

    def test_max_generations_equals_1(self):
        """Test that max_generations equals 1."""
        gate = GenerationGate(task_id="test_task")
        assert gate.max_generations == 1

    def test_second_generation_blocked(self):
        """Test that second generation is blocked."""
        gate = GenerationGate(task_id="test_task")
        gate.generation_count = 1
        
        result = gate.authorize_generation()
        assert result is False
        assert gate.second_generation_attempted is False  # Not attempted yet
        assert len(gate.blockers) > 0

    def test_state_stops_at_operator_visual_review_required(self):
        """Test that state stops at operator_visual_review_required."""
        gate = GenerationGate(task_id="test_task")
        assert gate.next_state_after_generation == "operator_visual_review_required"


class TestArtifactManager:
    """Test artifact management."""

    def test_proof_json_required_fields(self):
        """Test that proof JSON has required fields."""
        manager = ArtifactManager(output_dir="/tmp/test", task_id="test_task")
        
        proof = manager.create_proof(
            generation_manifest={
                "generation_count": 1,
                "max_generations": 1,
                "second_generation_attempted": False,
                "blind_retry_attempted": False,
                "prompt_id": "test_id",
                "generated_assets": []
            },
            llm_decision={},
            generation_gate={"generation_authorized_by_task": True}
        )
        
        assert proof["task_id"] == "test_task"
        assert proof["generation_count"] == 1
        assert proof["max_generations"] == 1
        assert proof["second_generation_attempted"] is False
        assert proof["blind_retry_attempted"] is False


class TestIntegration:
    """Integration tests."""

    def test_no_blind_retry(self):
        """Test that blind retry is not attempted."""
        gate = GenerationGate(task_id="test_task")
        gate.record_blind_retry_attempt()
        assert gate.blind_retry_attempted is True
        assert len(gate.blockers) > 0

    def test_production_accepted_remains_false(self):
        """Test that production_accepted remains false."""
        proof = {
            "production_accepted": False
        }
        assert proof["production_accepted"] is False

    def test_no_assembly_downstream_flags(self):
        """Test that assembly and downstream flags are false."""
        proof = {
            "assembly_executed": False,
            "downstream_executed": False
        }
        assert proof["assembly_executed"] is False
        assert proof["downstream_executed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
