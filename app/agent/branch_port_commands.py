"""Typed port command models for branch execution.

This module provides typed command objects for port interfaces,
replacing raw dict context with structured, type-safe command payloads.
"""

from dataclasses import dataclass, field
from typing import Any

from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.execution_plan import ExecutionPlan
from app.agent.branch_state_models import BranchResult
from app.agent.candidate_history import CandidateHistory
from app.agent.task_selector import TaskSelectionResult
from app.agent.branch_domain_types import WorkflowSpec, AssetBundle


@dataclass(frozen=True)
class RetryBranchCommand:
    """Typed command for retry branch execution."""
    corrective_action: CorrectiveActionDecision
    save_metadata: bool
    disable_internal_retry: bool
    retry_overrides: dict[str, Any]
    workflow_spec: WorkflowSpec | None = None  # Now typed domain object


@dataclass(frozen=True)
class SwitchBranchCommand:
    """Typed command for switch branch execution."""
    corrective_action: CorrectiveActionDecision
    save_metadata: bool
    target_workflow_id: str
    execution_plan: ExecutionPlan | None = None
    first_result: BranchResult | None = None
    task_selection: TaskSelectionResult | None = None
    assets: AssetBundle | None = None  # Now typed domain object
    switch_applied_this_run: bool = False
    candidate_history: CandidateHistory | None = None


@dataclass(frozen=True)
class SelectionCommand:
    """Typed command for candidate selection."""
    candidates: list[BranchResult]


@dataclass(frozen=True)
class HistoryAddAttemptCommand:
    """Typed command for adding attempt to history."""
    result: BranchResult
    attempt_index: int
    attempt_kind: str
    parent_candidate_id: str | None


@dataclass(frozen=True)
class HistoryMarkSelectedCommand:
    """Typed command for marking selected candidate."""
    candidate_id: str
    attempt_index: int
    selection_reason: str
