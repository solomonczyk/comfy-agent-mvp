"""Branch execution context and dependencies for executor interface hardening.

This module provides consolidated data structures for executor branch execution,
separating run-state context from operational dependencies.

BranchExecutionContext: Immutable-ish run-state data (no operations)
BranchExecutorDependencies: Callbacks and operations (no runtime data)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.execution_plan import ExecutionPlan
from app.agent.branch_execution_ports import BranchExecutorPorts
from app.agent.branch_state_models import TypedCandidateHistory


# Callback type definitions (kept for backward compatibility during migration)
RetryCallback = Callable[["ExecutionPlan", dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]
SwitchCallback = Callable[["ExecutionPlan", dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]
ChooseBestCandidateCallback = Callable[[list[dict[str, Any]]], dict[str, Any]]
UpdateHistoryCallback = Callable[[dict[str, Any], int, str, str | None], None]
MarkSelectedCallback = Callable[[str, int, str], None]


@dataclass(frozen=True)
class BranchExecutionContext:
    """Immutable context for branch execution.
    
    Contains run-state data only - no operations or callbacks.
    This is per-run immutable-ish context that should not be modified
    during execution.
    
    Principle: Context = run-state data, not operations.
    """
    corrective_action: CorrectiveActionDecision
    current_result: dict[str, Any]
    execution_plan: ExecutionPlan | None = None
    mutation_report: dict[str, Any] | None = None
    assets: dict[str, Any] | None = None
    candidate_history: TypedCandidateHistory | None = None


@dataclass
class BranchExecutorDependencies:
    """Dependencies for branch execution.
    
    Now uses only explicit typed ports - no legacy callbacks.
    Ports provide typed capabilities without exposing concrete implementation.
    
    Principle: Dependencies = operations/adapters, not run-state.
    """
    # Canonical: explicit typed ports only
    ports: BranchExecutorPorts
