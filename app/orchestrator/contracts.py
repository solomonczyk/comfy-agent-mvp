"""
Combine Orchestrator Contracts

Typed contracts for the internal multi-agent orchestrator.
These contracts define the data structures used throughout the orchestrator.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class StageExecutionDecision(Enum):
    """Decision for stage execution"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


@dataclass
class CombineRouteCandidate:
    """Candidate route family for a brief"""
    route_family: str
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CombineStageResult:
    """Result of a stage execution"""
    stage: str
    success: bool
    message: str
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    no_generation_performed: bool = True


@dataclass
class CombineStatus:
    """Current status of a Combine project"""
    project_root: str
    current_state: str
    next_allowed_action: str
    route_family: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    ledger_events: List[Dict[str, Any]] = field(default_factory=list)
    windsurf_runtime_dependency: bool = False
    generation_performed: bool = False
    comfyui_execution: bool = False
    combine_v2: bool = True


@dataclass
class CombineRunContext:
    """Context for running a Combine stage"""
    project_root: str
    current_state: str
    stage: str
    route_family: Optional[str] = None
    dry_run: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageTransitionRequest:
    """Request to transition to a new stage"""
    from_state: str
    to_state: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageTransitionResult:
    """Result of a stage transition"""
    allowed: bool
    from_state: str
    to_state: str
    blocked_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
