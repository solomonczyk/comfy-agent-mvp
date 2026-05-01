"""
Tests for Combine V2 Universal Role Agent Protocol

Tests the role agent stubs, their contracts, and the orchestrator integration.
Verifies that:
- All role agents exist and implement the base protocol
- Agents return proper structured results
- No generation or ComfyUI execution occurs
- No UGC/Meta/portrait/product core anchoring
- Route-specific behavior is optional
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.base import BaseRoleAgent, AgentResult
from app.agents.brief_intake_agent import BriefIntakeAgent
from app.agents.route_classifier_agent import RouteClassifierAgent
from app.agents.strategy_intent_agent import StrategyIntentAgent
from app.agents.script_scenario_agent import ScriptScenarioAgent
from app.agents.creative_director_agent import CreativeDirectorAgent
from app.agents.character_director_agent import CharacterDirectorAgent
from app.agents.prompt_composition_agent import PromptCompositionAgent
from app.agents.workflow_td_agent import WorkflowTDAgent
from app.agents.asset_resolver_agent import AssetResolverAgent
from app.agents.generation_agent import GenerationAgent
from app.agents.artifact_evidence_agent import ArtifactEvidenceAgent
from app.agents.visual_qa_agent import VisualQAAgent
from app.agents.retry_policy_agent import RetryPolicyAgent
from app.agents.assembly_agent import AssemblyAgent
from app.agents.final_qa_agent import FinalQAAgent
from app.orchestrator.contracts import CombineRunContext


# ------------------------------------------------------------------
# Agent Registry - all required agents
# ------------------------------------------------------------------
ALL_AGENTS = [
    ("BriefIntakeAgent", BriefIntakeAgent),
    ("RouteClassifierAgent", RouteClassifierAgent),
    ("StrategyIntentAgent", StrategyIntentAgent),
    ("ScriptScenarioAgent", ScriptScenarioAgent),
    ("CreativeDirectorAgent", CreativeDirectorAgent),
    ("CharacterDirectorAgent", CharacterDirectorAgent),
    ("PromptCompositionAgent", PromptCompositionAgent),
    ("WorkflowTDAgent", WorkflowTDAgent),
    ("AssetResolverAgent", AssetResolverAgent),
    ("GenerationAgent", GenerationAgent),
    ("ArtifactEvidenceAgent", ArtifactEvidenceAgent),
    ("VisualQAAgent", VisualQAAgent),
    ("RetryPolicyAgent", RetryPolicyAgent),
    ("AssemblyAgent", AssemblyAgent),
    ("FinalQAAgent", FinalQAAgent),
]


class TestBaseRoleAgentProtocol:
    """Test the base protocol requirements."""
    
    def test_all_agents_implement_base_protocol(self):
        """All agents must inherit from BaseRoleAgent."""
        for name, agent_class in ALL_AGENTS:
            assert issubclass(agent_class, BaseRoleAgent), \
                f"{name} must inherit from BaseRoleAgent"
    
    def test_all_agents_have_required_properties(self):
        """All agents must implement required properties."""
        for name, agent_class in ALL_AGENTS:
            agent = agent_class()
            assert hasattr(agent, 'role_name')
            assert hasattr(agent, 'supported_stages')
            assert hasattr(agent, 'required_inputs')
            assert hasattr(agent, 'output_contract_type')
    
    def test_all_agents_have_required_methods(self):
        """All agents must implement required methods."""
        for name, agent_class in ALL_AGENTS:
            agent = agent_class()
            assert hasattr(agent, 'validate_inputs')
            assert hasattr(agent, 'create_stub_result')
            assert hasattr(agent, 'run')
    
    def test_all_agents_return_agent_result(self):
        """All agents' create_stub_result must return AgentResult."""
        context = CombineRunContext(
            project_root="/test/project",
            current_state="test",
            stage="test",
            dry_run=True
        )
        for name, agent_class in ALL_AGENTS:
            agent = agent_class()
            # Provide minimal required metadata
            context.metadata = {"project_root": "/test/project"}
            if "route_family" in agent.required_inputs:
                context.metadata["route_family"] = "custom"
            if hasattr(agent, 'route_family'):
                context.route_family = "custom"
            
            result = agent.create_stub_result(context)
            assert isinstance(result, AgentResult), \
                f"{name}.create_stub_result must return AgentResult"


class TestAgentResultStructure:
    """Test the AgentResult structured format."""
    
    def test_agent_result_has_all_required_fields(self):
        """AgentResult must have all required fields."""
        result = AgentResult(
            agent="TestAgent",
            stage="test",
            status="stubbed"
        )
        
        assert hasattr(result, 'agent')
        assert hasattr(result, 'stage')
        assert hasattr(result, 'status')
        assert hasattr(result, 'dry_run')
        assert hasattr(result, 'generation_performed')
        assert hasattr(result, 'comfyui_execution')
        assert hasattr(result, 'downstream_executed')
        assert hasattr(result, 'artifacts')
        assert hasattr(result, 'next_recommended_stage')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'not_required_for_route')
    
    def test_default_values_are_correct(self):
        """AgentResult defaults must enforce no-generation policy."""
        result = AgentResult(
            agent="TestAgent",
            stage="test",
            status="stubbed"
        )
        
        assert result.status == "stubbed"
        assert result.dry_run == True
        assert result.generation_performed == False
        assert result.comfyui_execution == False
        assert result.downstream_executed == False
        assert result.artifacts == []


class TestGenerationAgent:
    """Test the GenerationAgent - must refuse real generation."""
    
    def test_generation_agent_exists(self):
        """GenerationAgent must exist as a role."""
        agent = GenerationAgent()
        assert agent.role_name == "GenerationAgent"
    
    def test_generation_agent_refuses_generation(self):
        """GenerationAgent must refuse generation and return stub only."""
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root="/test/project",
            current_state="generate_assets",
            stage="generate_assets",
            dry_run=True,
            metadata={"project_root": "/test/project", "route_family": "custom"}
        )
        
        result = agent.run(context, dry_run=True)
        
        # Must refuse generation
        assert result.generation_performed == False
        assert result.comfyui_execution == False
        assert result.downstream_executed == False
        assert result.dry_run == True
        assert result.status == "stubbed"
    
    def test_generation_agent_run_always_dry_run(self):
        """GenerationAgent.run() must always enforce dry_run=True."""
        agent = GenerationAgent()
        context = CombineRunContext(
            project_root="/test/project",
            current_state="generate_assets",
            stage="generate_assets",
            dry_run=False,  # Try to pass False
            metadata={"project_root": "/test/project", "route_family": "custom"}
        )
        
        result = agent.run(context, dry_run=False)
        
        # Still must be dry run
        assert result.dry_run == True
        assert result.generation_performed == False


class TestRouteAwareOptionality:
    """Test that agents support not_required_for_route optionality."""
    
    def test_character_director_optional_for_non_character_routes(self):
        """CharacterDirectorAgent should be optional for routes without characters."""
        agent = CharacterDirectorAgent()
        
        # Product route - no characters needed
        context = CombineRunContext(
            project_root="/test/project",
            current_state="production_plan_review",
            stage="production_plan_review",
            dry_run=True,
            route_family="product_visual",
            metadata={"project_root": "/test/project", "route_family": "product_visual"}
        )
        
        result = agent.create_stub_result(context)
        # Product visual doesn't need character director
        assert result.not_required_for_route == True
    
    def test_character_director_required_for_character_routes(self):
        """CharacterDirectorAgent should be required for character routes."""
        agent = CharacterDirectorAgent()
        
        # Portrait route - needs characters
        context = CombineRunContext(
            project_root="/test/project",
            current_state="production_plan_review",
            stage="production_plan_review",
            dry_run=True,
            route_family="portrait_character_identity",
            metadata={"project_root": "/test/project", "route_family": "portrait_character_identity"}
        )
        
        result = agent.create_stub_result(context)
        # Portrait route needs character director
        assert result.not_required_for_route == False
    
    def test_script_scenario_optional_for_still_images(self):
        """ScriptScenarioAgent should be optional for still-image routes."""
        agent = ScriptScenarioAgent()
        
        # Product route - still image, no script needed
        context = CombineRunContext(
            project_root="/test/project",
            current_state="production_plan_required",
            stage="production_plan_required",
            dry_run=True,
            route_family="product_visual",
            metadata={"project_root": "/test/project", "route_family": "product_visual"}
        )
        
        result = agent.create_stub_result(context)
        assert result.not_required_for_route == True
    
    def test_assembly_optional_for_single_image_routes(self):
        """AssemblyAgent should be optional for single-image output routes."""
        agent = AssemblyAgent()
        
        # Product route - single image, no assembly needed
        context = CombineRunContext(
            project_root="/test/project",
            current_state="assembly_required",
            stage="assembly_required",
            dry_run=True,
            route_family="product_visual",
            metadata={"project_root": "/test/project", "route_family": "product_visual"}
        )
        
        result = agent.create_stub_result(context)
        assert result.not_required_for_route == True


class TestNoCoreAnchoring:
    """Test that no agent assumes UGC/Meta/portrait/product as core default."""
    
    def test_agents_do_not_assume_ugc_default(self):
        """No agent should assume UGC is the default route."""
        from app.orchestrator.routing import RouteFamilyRegistry
        
        # UGC is just one of many routes
        families = RouteFamilyRegistry.list_route_families()
        assert "ugc_testimonial" in families
        
        # But it's not marked as default in policy
        policy = RouteFamilyRegistry.get_route_family_policy("ugc_testimonial")
        assert "default" not in policy or not policy["default"]
    
    def test_agents_do_not_assume_meta_default(self):
        """No agent should assume Meta/ads is the default route."""
        from app.orchestrator.routing import RouteFamilyRegistry
        
        families = RouteFamilyRegistry.list_route_families()
        assert "platform_ad_creative" in families
        
        policy = RouteFamilyRegistry.get_route_family_policy("platform_ad_creative")
        assert "default" not in policy or not policy["default"]
    
    def test_agents_do_not_assume_portrait_default(self):
        """No agent should assume portrait is the default route."""
        from app.orchestrator.routing import RouteFamilyRegistry
        
        families = RouteFamilyRegistry.list_route_families()
        assert "portrait_character_identity" in families
        
        policy = RouteFamilyRegistry.get_route_family_policy("portrait_character_identity")
        assert "default" not in policy or not policy["default"]
    
    def test_agents_do_not_assume_product_default(self):
        """No agent should assume product is the default route."""
        from app.orchestrator.routing import RouteFamilyRegistry
        
        families = RouteFamilyRegistry.list_route_families()
        assert "product_visual" in families
        
        policy = RouteFamilyRegistry.get_route_family_policy("product_visual")
        assert "default" not in policy or not policy["default"]
    
    def test_route_policy_descriptions_are_factual(self):
        """Route policies should describe, not prescribe defaults."""
        from app.orchestrator.routing import RouteFamilyRegistry
        
        families = RouteFamilyRegistry.list_route_families()
        for family in families:
            policy = RouteFamilyRegistry.get_route_family_policy(family)
            # Policy should have description, not default=True
            assert "description" in policy
            # No route should be marked as universal default
            assert policy.get("default", False) == False


class TestOrchestratorAgentDispatch:
    """Test orchestrator dispatches to role agents correctly."""
    
    def test_orchestrator_maps_stages_to_agents(self):
        """Orchestrator should map stages to agent names."""
        from app.orchestrator.orchestrator import CombineOrchestrator
        
        orchestrator = CombineOrchestrator("/test/project")
        
        # Check key stage mappings
        assert "brief_intake_required" in orchestrator._stage_agent_map
        assert "route_classification_required" in orchestrator._stage_agent_map
        assert "generation_authorization_required" in orchestrator._stage_agent_map
        assert "visual_qa_required" in orchestrator._stage_agent_map
    
    def test_orchestrator_can_load_all_agents(self):
        """Orchestrator should be able to load all mapped agents."""
        from app.orchestrator.orchestrator import CombineOrchestrator
        
        orchestrator = CombineOrchestrator("/test/project")
        
        # Try loading each agent
        for stage, agent_name in orchestrator._stage_agent_map.items():
            agent = orchestrator._load_agent(agent_name)
            assert agent is not None
            assert agent.role_name == agent_name
    
    def test_run_stage_dispatches_to_agent(self):
        """run_stage should dispatch to role agent and return structured result."""
        import tempfile
        from app.orchestrator.orchestrator import CombineOrchestrator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal project structure
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            
            orchestrator = CombineOrchestrator(str(project_root))
            
            # Run a stage
            result = orchestrator.run_stage("route_classification_required", dry_run=True)
            
            # Verify result structure
            assert result.success == True
            assert result.no_generation_performed == True
            assert "RouteClassifierAgent" in result.message or "agent" in result.metadata
    
    def test_run_stage_returns_agent_result_fragment(self):
        """run_stage should return result with agent information."""
        import tempfile
        import json
        from app.orchestrator.orchestrator import CombineOrchestrator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            
            # Create artifact index with route family
            artifact_index = project_root / "artifact_index.json"
            artifact_index.write_text(json.dumps({"route_family": "custom"}))
            
            orchestrator = CombineOrchestrator(str(project_root))
            result = orchestrator.run_stage("brief_intake_required", dry_run=True)
            
            # Verify agent info in metadata
            assert "agent" in result.metadata
            assert result.metadata["agent"] == "BriefIntakeAgent"
            assert result.no_generation_performed == True
            assert result.metadata.get("generation_performed") == False
            assert result.metadata.get("comfyui_execution") == False


class TestContractFiles:
    """Test that contract files exist and are importable."""
    
    def test_brief_contract_exists(self):
        from app.contracts.brief_contract import BriefIntakeContract
        contract = BriefIntakeContract()
        assert contract.brief_id is None
    
    def test_route_contract_exists(self):
        from app.contracts.route_contract import RouteClassificationContract
        contract = RouteClassificationContract()
        assert contract.route_family is None
        assert contract.confidence == 0.0
    
    def test_production_plan_contract_exists(self):
        from app.contracts.production_plan_contract import ProductionPlanContract
        contract = ProductionPlanContract()
        assert contract.strategy is None
    
    def test_prompt_contract_exists(self):
        from app.contracts.prompt_contract import PromptCompositionContract
        contract = PromptCompositionContract()
        assert contract.positive_prompt is None
    
    def test_workflow_contract_exists(self):
        from app.contracts.workflow_contract import WorkflowTDContract
        contract = WorkflowTDContract()
        assert contract.workflow_type is None
    
    def test_visual_qa_contract_exists(self):
        from app.contracts.visual_qa_contract import VisualQAContract
        contract = VisualQAContract()
        assert contract.verdict is None
    
    def test_retry_contract_exists(self):
        from app.contracts.retry_contract import RetryContract
        contract = RetryContract()
        assert contract.retry_allowed == False
    
    def test_final_pack_contract_exists(self):
        from app.contracts.final_pack_contract import FinalPackContract
        contract = FinalPackContract()
        assert contract.acceptance_status is None


class TestAgentStateTransitions:
    """Test specific agent state transition recommendations."""
    
    def test_strategy_intent_recommends_production_plan_review(self):
        """StrategyIntentAgent must recommend production_plan_review."""
        agent = StrategyIntentAgent()
        context = CombineRunContext(
            project_root="/test/project",
            current_state="production_plan_required",
            stage="production_plan_required",
            route_family="custom",
            metadata={"project_root": "/test/project", "route_family": "custom"}
        )
        result = agent.create_stub_result(context)
        assert result.next_recommended_stage == "production_plan_review"

    def test_creative_director_recommends_asset_resolution(self):
        """CreativeDirectorAgent must recommend asset_resolution_required, NOT generation_authorization."""
        agent = CreativeDirectorAgent()
        context = CombineRunContext(
            project_root="/test/project",
            current_state="production_plan_review",
            stage="production_plan_review",
            route_family="custom",
            metadata={"project_root": "/test/project", "route_family": "custom"}
        )
        result = agent.create_stub_result(context)
        assert result.next_recommended_stage == "asset_resolution_required"
        assert result.next_recommended_stage != "generation_authorization_required"

    def test_no_generation_performed_by_stubs(self):
        """Verify no generation is executed by any stub agent."""
        context = CombineRunContext(
            project_root="/test/project",
            current_state="any",
            stage="any",
            route_family="custom",
            metadata={"project_root": "/test/project", "route_family": "custom"}
        )
        for name, agent_class in ALL_AGENTS:
            agent = agent_class()
            result = agent.create_stub_result(context)
            assert result.generation_performed == False
            assert result.comfyui_execution == False
            assert result.downstream_executed == False

