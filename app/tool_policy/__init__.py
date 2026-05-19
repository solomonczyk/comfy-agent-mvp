"""Tool Policy Gateway Layer - Project-Agnostic Permission System

This module provides a universal permission checking layer for tools/actions.
It does NOT execute tools - it only evaluates whether a request is allowed.
"""

from .models import (
    ToolPolicy,
    ToolRequest,
    DecisionStatus,
    DecisionResult,
)
from .decision_engine import DecisionEngine
from .dangerous_tool_registry import DangerousToolRegistry
from .agent_tool_access_matrix import AgentToolAccessMatrix

__all__ = [
    "ToolPolicy",
    "ToolRequest",
    "DecisionStatus",
    "DecisionResult",
    "DecisionEngine",
    "DangerousToolRegistry",
    "AgentToolAccessMatrix",
]
