"""Tool Policy Models

Defines the data models for tool policy and tool request evaluation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DecisionStatus(Enum):
    """Decision status for tool request evaluation"""
    ALLOWED_SAFE_READ = "allowed_safe_read"
    ALLOWED_SAFE_VALIDATION = "allowed_safe_validation"
    BLOCKED_ROLE_FORBIDDEN = "blocked_role_forbidden"
    BLOCKED_DANGEROUS_ACTION = "blocked_dangerous_action"
    BLOCKED_MISSING_GATE = "blocked_missing_gate"
    BLOCKED_GATE_NOT_AUTHORIZED = "blocked_gate_not_authorized"
    BLOCKED_PRODUCTION_ACCEPTANCE_FORBIDDEN = "blocked_production_acceptance_forbidden"
    BLOCKED_FORCE_PUSH_FORBIDDEN = "blocked_force_push_forbidden"
    BLOCKED_HARDCODED_REFERENCE = "blocked_hardcoded_reference"


@dataclass
class ToolPolicy:
    """Tool policy for an agent"""
    agent_id: str
    role: str
    allowed_tools: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    dangerous_actions: List[str] = field(default_factory=list)
    required_gate_types: List[str] = field(default_factory=list)
    runtime_execution_allowed: bool = False
    can_mutate_production_acceptance: bool = False
    can_force_push: bool = False
    description: Optional[str] = None


@dataclass
class ToolRequest:
    """Tool request for evaluation"""
    requester_agent_id: str
    requested_tool: str
    requested_action: str
    target_stage: Optional[str] = None
    gate_packet_reference: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResult:
    """Result of tool request evaluation"""
    status: DecisionStatus
    allowed: bool
    reason: str
    policy_applied: ToolPolicy
    missing_gates: List[str] = field(default_factory=list)
    dangerous_categories: List[str] = field(default_factory=list)
    evaluation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
