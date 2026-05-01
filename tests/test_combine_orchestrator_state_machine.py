"""
Tests for Combine V2 Orchestrator State Machine

Tests the universal state machine, route registry, and orchestrator skeleton.
"""

import pytest
from app.orchestrator.state_machine import CombineStateMachine
from app.orchestrator.routing import RouteFamilyRegistry
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.contracts import CombineStatus


class TestCombineStateMachine:
    """Test the universal state machine"""
    
    def test_all_declared_states_are_valid(self):
        """Test that all declared states are valid"""
        all_states = CombineStateMachine.get_all_states()
        for state in all_states:
            assert CombineStateMachine.is_valid_state(state), f"State {state} should be valid"
    
    def test_invalid_states_are_rejected(self):
        """Test that invalid states are rejected"""
        assert not CombineStateMachine.is_valid_state("invalid_state")
        assert not CombineStateMachine.is_valid_state("")
        assert not CombineStateMachine.is_valid_state("not_a_state")
    
    def test_allowed_transitions_work(self):
        """Test that allowed transitions work"""
        # Test some valid transitions
        assert CombineStateMachine.can_transition("initial", "brief_intake_required")
        assert CombineStateMachine.can_transition("brief_intake_required", "route_classification_required")
        assert CombineStateMachine.can_transition("route_classification_required", "production_plan_required")
        assert CombineStateMachine.can_transition("production_plan_required", "production_plan_review")
        assert CombineStateMachine.can_transition("generate_assets", "visual_qa_required")
        assert CombineStateMachine.can_transition("final_operator_acceptance", "completed")
    
    def test_forbidden_transitions_fail(self):
        """Test that forbidden transitions fail"""
        # Test some forbidden transitions
        assert not CombineStateMachine.can_transition("workflow_plan_required", "generate_assets")
        assert not CombineStateMachine.can_transition("workflow_preflight_required", "generate_assets")
        assert not CombineStateMachine.can_transition("brief_intake_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("generate_assets", "assembly_required")
        assert not CombineStateMachine.can_transition("visual_qa_required", "completed")
    
    def test_generation_cannot_happen_before_preflight_authorization(self):
        """Test that generation cannot happen before preflight/authorization"""
        # Generation cannot happen from early states
        assert not CombineStateMachine.can_transition("brief_intake_required", "generate_assets")
        assert not CombineStateMachine.can_transition("route_classification_required", "generate_assets")
        assert not CombineStateMachine.can_transition("production_plan_required", "generate_assets")
        assert not CombineStateMachine.can_transition("workflow_plan_required", "generate_assets")
        assert not CombineStateMachine.can_transition("workflow_preflight_required", "generate_assets")
        
        # Generation can only happen after authorization
        assert CombineStateMachine.can_transition("generation_authorization_required", "generate_assets")
    
    def test_qa_cannot_happen_before_generated_artifacts(self):
        """Test that QA cannot happen before generated artifacts"""
        # QA cannot happen from early states
        assert not CombineStateMachine.can_transition("brief_intake_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("route_classification_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("production_plan_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("workflow_plan_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("workflow_preflight_required", "visual_qa_required")
        assert not CombineStateMachine.can_transition("generation_authorization_required", "visual_qa_required")
        
        # QA can happen after generation
        assert CombineStateMachine.can_transition("generate_assets", "visual_qa_required")
    
    def test_assembly_cannot_happen_before_accepted_visuals_assets(self):
        """Test that assembly cannot happen before accepted visuals/assets"""
        # Assembly cannot happen from early states
        assert not CombineStateMachine.can_transition("brief_intake_required", "assembly_required")
        assert not CombineStateMachine.can_transition("route_classification_required", "assembly_required")
        assert not CombineStateMachine.can_transition("production_plan_required", "assembly_required")
        assert not CombineStateMachine.can_transition("workflow_plan_required", "assembly_required")
        assert not CombineStateMachine.can_transition("workflow_preflight_required", "assembly_required")
        assert not CombineStateMachine.can_transition("generation_authorization_required", "assembly_required")
        assert not CombineStateMachine.can_transition("generate_assets", "assembly_required")
        
        # Assembly can happen after QA and operator review
        assert CombineStateMachine.can_transition("operator_visual_review", "assembly_required")
    
    def test_terminal_states_are_terminal(self):
        """Test that terminal states are terminal"""
        terminal_states = CombineStateMachine.get_terminal_states()
        assert "completed" in terminal_states
        assert "blocked_manual_review" in terminal_states
        
        # Terminal states should have no allowed transitions
        assert CombineStateMachine.is_terminal_state("completed")
        assert CombineStateMachine.is_terminal_state("blocked_manual_review")
        assert len(CombineStateMachine.get_allowed_next_states("completed")) == 0


class TestRouteFamilyRegistry:
    """Test the route family registry"""
    
    def test_route_families_are_registered(self):
        """Test that route families are registered"""
        families = RouteFamilyRegistry.list_route_families()
        
        # Check that all expected families are present
        assert "portrait_character_identity" in families
        assert "product_visual" in families
        assert "ugc_testimonial" in families
        assert "platform_ad_creative" in families
        assert "social_short_vertical" in families
        assert "cinematic_scene" in families
        assert "educational_explainer" in families
        assert "image_to_video" in families
        assert "video_to_video" in families
        assert "batch_variations" in families
        assert "custom" in families
    
    def test_no_single_use_case_route_is_universal_default(self):
        """Test that no single-use-case route is treated as universal default"""
        families = RouteFamilyRegistry.list_route_families()
        
        # All families should be treated equally
        # No family should be marked as default in the registry
        for family in families:
            policy = RouteFamilyRegistry.get_route_family_policy(family)
            assert "default" not in policy or not policy["default"]
    
    def test_ugc_is_route_only(self):
        """Test that UGC is a route only, not a universal default"""
        assert RouteFamilyRegistry.is_supported_route_family("ugc_testimonial")
        policy = RouteFamilyRegistry.get_route_family_policy("ugc_testimonial")
        assert policy["description"] == "UGC and testimonial content generation"
        # UGC should not be marked as default
        assert "default" not in policy or not policy["default"]
    
    def test_meta_platform_ad_is_route_only(self):
        """Test that Meta/platform ad is a route only, not a universal default"""
        assert RouteFamilyRegistry.is_supported_route_family("platform_ad_creative")
        policy = RouteFamilyRegistry.get_route_family_policy("platform_ad_creative")
        assert policy["description"] == "Platform ad creative generation (Meta, TikTok, etc.)"
        # Platform ad should not be marked as default
        assert "default" not in policy or not policy["default"]
    
    def test_portrait_is_route_only(self):
        """Test that portrait is a route only, not a universal default"""
        assert RouteFamilyRegistry.is_supported_route_family("portrait_character_identity")
        policy = RouteFamilyRegistry.get_route_family_policy("portrait_character_identity")
        assert policy["description"] == "Portrait and character identity generation"
        # Portrait should not be marked as default
        assert "default" not in policy or not policy["default"]
    
    def test_product_is_route_only(self):
        """Test that product is a route only, not a universal default"""
        assert RouteFamilyRegistry.is_supported_route_family("product_visual")
        policy = RouteFamilyRegistry.get_route_family_policy("product_visual")
        assert policy["description"] == "Product image and product video generation"
        # Product should not be marked as default
        assert "default" not in policy or not policy["default"]
    
    def test_custom_route_is_supported(self):
        """Test that custom route is supported"""
        assert RouteFamilyRegistry.is_supported_route_family("custom")
        policy = RouteFamilyRegistry.get_route_family_policy("custom")
        assert policy["description"] == "Custom route for user-defined workflows"
    
    def test_classify_route_stub_returns_candidates(self):
        """Test that classify_route_stub returns candidates, not hardcoded default"""
        brief = {"content": "portrait of a character"}
        candidates = RouteFamilyRegistry.classify_route_stub(brief)
        
        # Should return multiple candidates
        assert len(candidates) > 0
        
        # Should include custom as fallback
        route_families = [c.route_family for c in candidates]
        assert "custom" in route_families
        
        # Should not hardcode a single default
        # The classifier should return candidates with confidence scores
        for candidate in candidates:
            assert hasattr(candidate, 'confidence')
            assert hasattr(candidate, 'route_family')
            assert hasattr(candidate, 'reason')


class TestCombineOrchestrator:
    """Test the Combine orchestrator"""
    
    def test_combine_status_can_instantiate_orchestrator_without_comfyui(self, tmp_path):
        """Test that combine-status can instantiate orchestrator without ComfyUI"""
        # This test should pass without requiring ComfyUI to be running
        orchestrator = CombineOrchestrator(str(tmp_path))
        status = orchestrator.get_status()
        
        # Verify status structure
        assert isinstance(status, CombineStatus)
        assert status.project_root == str(tmp_path)
        assert status.windsurf_runtime_dependency == False
        assert status.generation_performed == False
        assert status.comfyui_execution == False
        assert status.combine_v2 == True
    
    def test_combine_run_stage_dry_run_does_not_execute_generation(self, tmp_path):
        """Test that combine-run-stage dry-run does not execute generation"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Run first stage to reach a state where route_classification_required is allowed
        orchestrator.run_stage("brief_intake_required", dry_run=True)
        
        # Run a stage in dry-run mode
        result = orchestrator.run_stage("route_classification_required", dry_run=True)
        
        # Verify no generation was performed
        assert result.no_generation_performed == True
        assert result.success == True
        assert "dry run" in result.message.lower() or "stub" in result.message.lower()
