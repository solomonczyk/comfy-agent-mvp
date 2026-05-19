"""Tool Policy Decision Engine

Evaluates tool requests against policies and returns decision results.
"""

from typing import List, Optional
from .models import (
    ToolPolicy,
    ToolRequest,
    DecisionResult,
    DecisionStatus,
)
from .dangerous_tool_registry import DangerousToolRegistry
from .agent_tool_access_matrix import AgentToolAccessMatrix


class DecisionEngine:
    """Evaluates tool requests against policies"""

    def __init__(
        self,
        access_matrix: AgentToolAccessMatrix,
        dangerous_registry: DangerousToolRegistry,
    ):
        self.access_matrix = access_matrix
        self.dangerous_registry = dangerous_registry

    def evaluate(self, request: ToolRequest) -> DecisionResult:
        """Evaluate a tool request and return decision"""
        policy = self.access_matrix.get_policy(request.requester_agent_id)
        
        if not policy:
            return DecisionResult(
                status=DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
                allowed=False,
                reason=f"No policy found for agent: {request.requester_agent_id}",
                policy_applied=ToolPolicy(
                    agent_id="unknown",
                    role="unknown",
                ),
            )

        # Check for hardcoded references (rc2_multishot1_ep01)
        if self._has_hardcoded_reference(request):
            return DecisionResult(
                status=DecisionStatus.BLOCKED_HARDCODED_REFERENCE,
                allowed=False,
                reason="Request contains hardcoded project reference (rc2_multishot1_ep01)",
                policy_applied=policy,
            )

        # Production acceptance is always blocked (check before general forbidden)
        if request.requested_tool == "production.accept":
            dangerous_categories = self.dangerous_registry.get_dangerous_categories(request.requested_tool)
            return DecisionResult(
                status=DecisionStatus.BLOCKED_PRODUCTION_ACCEPTANCE_FORBIDDEN,
                allowed=False,
                reason="Production acceptance is always forbidden",
                policy_applied=policy,
                dangerous_categories=dangerous_categories,
            )
        
        # Force push is always blocked (check before general forbidden)
        if request.requested_tool == "git.force_push":
            dangerous_categories = self.dangerous_registry.get_dangerous_categories(request.requested_tool)
            return DecisionResult(
                status=DecisionStatus.BLOCKED_FORCE_PUSH_FORBIDDEN,
                allowed=False,
                reason="Force push is always forbidden without manual destructive git gate",
                policy_applied=policy,
                dangerous_categories=dangerous_categories,
            )

        # Check if tool is explicitly forbidden
        if request.requested_tool in policy.forbidden_tools:
            return DecisionResult(
                status=DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
                allowed=False,
                reason=f"Tool '{request.requested_tool}' is forbidden for role '{policy.role}'",
                policy_applied=policy,
            )

        # Check if tool is dangerous
        dangerous_categories = self.dangerous_registry.get_dangerous_categories(request.requested_tool)
        if dangerous_categories:
            # Check if dangerous action is allowed
            if not policy.runtime_execution_allowed:
                return DecisionResult(
                    status=DecisionStatus.BLOCKED_DANGEROUS_ACTION,
                    allowed=False,
                    reason=f"Tool '{request.requested_tool}' is dangerous and runtime execution is not allowed for role '{policy.role}'",
                    policy_applied=policy,
                    dangerous_categories=dangerous_categories,
                )

        # Check if tool is in allowed list
        if request.requested_tool not in policy.allowed_tools:
            return DecisionResult(
                status=DecisionStatus.BLOCKED_ROLE_FORBIDDEN,
                allowed=False,
                reason=f"Tool '{request.requested_tool}' is not in allowed list for role '{policy.role}'",
                policy_applied=policy,
            )

        # Check for required gates
        missing_gates = []
        if policy.required_gate_types:
            if not request.gate_packet_reference:
                missing_gates = policy.required_gate_types
            else:
                # In a real implementation, we would validate the gate packet
                # For this project-agnostic layer, we assume any reference is valid
                pass

        if missing_gates:
            return DecisionResult(
                status=DecisionStatus.BLOCKED_MISSING_GATE,
                allowed=False,
                reason=f"Missing required gates: {', '.join(missing_gates)}",
                policy_applied=policy,
                missing_gates=missing_gates,
            )

        # Determine if it's a safe read or validation operation
        if self._is_safe_read_operation(request.requested_tool):
            return DecisionResult(
                status=DecisionStatus.ALLOWED_SAFE_READ,
                allowed=True,
                reason="Tool is a safe read operation",
                policy_applied=policy,
            )

        if self._is_safe_validation_operation(request.requested_tool):
            return DecisionResult(
                status=DecisionStatus.ALLOWED_SAFE_VALIDATION,
                allowed=True,
                reason="Tool is a safe validation operation",
                policy_applied=policy,
            )

        # Default to allowed if it passed all checks
        return DecisionResult(
            status=DecisionStatus.ALLOWED_SAFE_READ,
            allowed=True,
            reason="Tool request passed all policy checks",
            policy_applied=policy,
        )

    def _has_hardcoded_reference(self, request: ToolRequest) -> bool:
        """Check if request contains hardcoded project references"""
        forbidden_refs = ["rc2_multishot1_ep01"]
        context_str = str(request.additional_context) + " " + str(request.reason) + " " + str(request.target_stage)
        return any(ref in context_str.lower() for ref in forbidden_refs)

    def _is_safe_read_operation(self, tool: str) -> bool:
        """Check if tool is a safe read operation"""
        safe_read_patterns = [
            "read",
            "inspect",
            "get",
            "list",
            "validate",
            "check",
            "audit",
        ]
        return any(pattern in tool.lower() for pattern in safe_read_patterns)

    def _is_safe_validation_operation(self, tool: str) -> bool:
        """Check if tool is a safe validation operation"""
        safe_validation_patterns = [
            "validate",
            "verify",
            "check",
            "audit",
            "inspect",
        ]
        return any(pattern in tool.lower() for pattern in safe_validation_patterns)
