"""Tests for Tool Policy Gateway Layer"""

import pytest
from app.tool_policy.models import (
    ToolPolicy,
    ToolRequest,
    DecisionStatus,
    DecisionResult,
)
from app.tool_policy.decision_engine import DecisionEngine
from app.tool_policy.dangerous_tool_registry import DangerousToolRegistry
from app.tool_policy.agent_tool_access_matrix import AgentToolAccessMatrix


class TestDangerousToolRegistry:
    """Test dangerous tool registry"""

    def test_registry_initialization(self):
        registry = DangerousToolRegistry()
        assert len(registry.get_all_dangerous_tools()) > 0

    def test_is_dangerous(self):
        registry = DangerousToolRegistry()
        assert registry.is_dangerous("comfyui.submit")
        assert registry.is_dangerous("generation.run")
        assert registry.is_dangerous("production.accept")
        assert not registry.is_dangerous("tool_policy.validate")

    def test_get_dangerous_categories(self):
        registry = DangerousToolRegistry()
        categories = registry.get_dangerous_categories("comfyui.submit")
        assert "generation" in categories
        assert "comfyui" in categories

    def test_get_tools_by_category(self):
        registry = DangerousToolRegistry()
        tools = registry.get_tools_by_category("generation")
        assert "comfyui.submit" in tools
        assert "generation.run" in tools


class TestAgentToolAccessMatrix:
    """Test agent tool access matrix"""

    def test_matrix_initialization(self):
        matrix = AgentToolAccessMatrix()
        assert len(matrix.get_all_policies()) > 0

    def test_get_policy(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("orchestrator")
        assert policy is not None
        assert policy.role == "orchestrator"
        assert policy.runtime_execution_allowed is False

    def test_script_supervisor_cannot_submit_comfyui(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("script_supervisor_agent")
        assert "comfyui.submit" in policy.forbidden_tools

    def test_camera_operator_requires_generation_gate(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("camera_operator_agent")
        assert "generation_gate" in policy.required_gate_types
        assert "preview_gate" in policy.required_gate_types

    def test_state_audit_guard_cannot_mutate_production(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("state_audit_guard_agent")
        assert policy.can_mutate_production_acceptance is False
        assert "production.accept" in policy.forbidden_tools

    def test_editor_requires_preview_gate(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("editor_agent")
        assert "preview_gate" in policy.required_gate_types

    def test_sound_agent_requires_voice_gate(self):
        matrix = AgentToolAccessMatrix()
        policy = matrix.get_policy("sound_agent")
        assert "voice_gate" in policy.required_gate_types

    def test_all_agents_block_dangerous_tools(self):
        matrix = AgentToolAccessMatrix()
        registry = DangerousToolRegistry()
        dangerous_tools = registry.get_all_dangerous_tools()
        
        for agent_id, policy in matrix.get_all_policies().items():
            for tool in dangerous_tools:
                # All dangerous tools should be in forbidden list
                assert tool in policy.forbidden_tools, f"{agent_id} missing {tool} in forbidden"

    def test_no_runtime_execution_allowed(self):
        matrix = AgentToolAccessMatrix()
        for agent_id, policy in matrix.get_all_policies().items():
            assert policy.runtime_execution_allowed is False, f"{agent_id} has runtime_execution_allowed=True"

    def test_no_production_acceptance_mutation(self):
        matrix = AgentToolAccessMatrix()
        for agent_id, policy in matrix.get_all_policies().items():
            assert policy.can_mutate_production_acceptance is False, f"{agent_id} can mutate production acceptance"

    def test_no_force_push_allowed(self):
        matrix = AgentToolAccessMatrix()
        for agent_id, policy in matrix.get_all_policies().items():
            assert policy.can_force_push is False, f"{agent_id} can force push"


class TestDecisionEngine:
    """Test decision engine"""

    def test_script_supervisor_blocked_comfyui_submit(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="script_supervisor_agent",
            requested_tool="comfyui.submit",
            requested_action="execute",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status == DecisionStatus.BLOCKED_ROLE_FORBIDDEN

    def test_camera_operator_blocked_generation_without_gate(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="camera_operator_agent",
            requested_tool="generation.run",
            requested_action="execute",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status in [
            DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
            DecisionStatus.BLOCKED_MISSING_GATE,
        ]

    def test_state_audit_guard_blocked_production_acceptance(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="state_audit_guard_agent",
            requested_tool="production.accept",
            requested_action="accept",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status == DecisionStatus.BLOCKED_PRODUCTION_ACCEPTANCE_FORBIDDEN

    def test_editor_blocked_preview_render_without_gate(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="editor_agent",
            requested_tool="preview.render",
            requested_action="render",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status in [
            DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
            DecisionStatus.BLOCKED_MISSING_GATE,
        ]

    def test_sound_agent_blocked_voice_generation_without_gate(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="sound_agent",
            requested_tool="voice.generate",
            requested_action="generate",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status in [
            DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
            DecisionStatus.BLOCKED_MISSING_GATE,
        ]

    def test_production_acceptance_always_blocked(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        for agent_id in matrix.get_all_policies().keys():
            request = ToolRequest(
                requester_agent_id=agent_id,
                requested_tool="production.accept",
                requested_action="accept",
            )

            decision = engine.evaluate(request)
            assert decision.allowed is False
            assert decision.status == DecisionStatus.BLOCKED_PRODUCTION_ACCEPTANCE_FORBIDDEN

    def test_force_push_always_blocked(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        for agent_id in matrix.get_all_policies().keys():
            request = ToolRequest(
                requester_agent_id=agent_id,
                requested_tool="git.force_push",
                requested_action="push",
            )

            decision = engine.evaluate(request)
            assert decision.allowed is False
            assert decision.status == DecisionStatus.BLOCKED_FORCE_PUSH_FORBIDDEN

    def test_safe_read_operations_allowed(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="orchestrator",
            requested_tool="tool_policy.validate",
            requested_action="validate",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is True
        assert decision.status in [
            DecisionStatus.ALLOWED_SAFE_READ,
            DecisionStatus.ALLOWED_SAFE_VALIDATION,
        ]

    def test_hardcoded_reference_blocked(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="orchestrator",
            requested_tool="tool_policy.validate",
            requested_action="validate",
            additional_context={"project": "rc2_multishot1_ep01"},
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status == DecisionStatus.BLOCKED_HARDCODED_REFERENCE

    def test_unknown_agent_blocked(self):
        registry = DangerousToolRegistry()
        matrix = AgentToolAccessMatrix()
        engine = DecisionEngine(matrix, registry)

        request = ToolRequest(
            requester_agent_id="unknown_agent",
            requested_tool="tool_policy.validate",
            requested_action="validate",
        )

        decision = engine.evaluate(request)
        assert decision.allowed is False
        assert decision.status == DecisionStatus.BLOCKED_ROLE_FORBIDDEN


class TestToolPolicyModels:
    """Test tool policy models"""

    def test_tool_policy_creation(self):
        policy = ToolPolicy(
            agent_id="test_agent",
            role="test_role",
            allowed_tools=["tool1", "tool2"],
            forbidden_tools=["dangerous_tool"],
            runtime_execution_allowed=False,
        )
        assert policy.agent_id == "test_agent"
        assert policy.role == "test_role"
        assert policy.runtime_execution_allowed is False

    def test_tool_request_creation(self):
        request = ToolRequest(
            requester_agent_id="test_agent",
            requested_tool="test_tool",
            requested_action="test_action",
        )
        assert request.requester_agent_id == "test_agent"
        assert request.requested_tool == "test_tool"

    def test_decision_result_creation(self):
        result = DecisionResult(
            status=DecisionStatus.ALLOWED_SAFE_READ,
            allowed=True,
            reason="Test reason",
            policy_applied=ToolPolicy(
                agent_id="test",
                role="test",
            ),
        )
        assert result.allowed is True
        assert result.status == DecisionStatus.ALLOWED_SAFE_READ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
