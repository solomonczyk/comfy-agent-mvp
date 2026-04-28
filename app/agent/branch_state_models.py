"""Typed branch state models for executor port hardening.

This module provides typed wrappers for load-bearing branch state,
reducing dict-heavy paths and schema drift risk.

Typed state models:
- BranchResult: Typed wrapper for generation result
- TypedCandidateHistory: Typed wrapper for candidate history
- TypedExecutedAction: Typed wrapper for executed action
- TypedBranchOutcome: Typed wrapper for branch outcome
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BranchResult:
    """Typed wrapper for generation result.
    
    Provides structured access to common result fields instead of raw dict.
    Reduces schema drift risk on load-bearing paths.
    """
    status: str
    images: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Optional fields that may be present
    corrective_action: dict[str, Any] | None = None
    executed_action: dict[str, Any] | None = None
    candidate_selection: dict[str, Any] | None = None
    mutation_report: dict[str, Any] = field(default_factory=dict)
    orchestrator_report: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BranchResult":
        """Create BranchResult from raw dict."""
        return cls(
            status=data.get("status", "unknown"),
            images=data.get("images", []),
            metadata=data.get("metadata", {}),
            corrective_action=data.get("corrective_action"),
            executed_action=data.get("executed_action"),
            candidate_selection=data.get("candidate_selection"),
            mutation_report=data.get("mutation_report", {}),
            orchestrator_report=data.get("orchestrator_report", {}),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to raw dict for external contract compatibility."""
        result = {
            "status": self.status,
            "images": self.images,
            "metadata": self.metadata,
            "mutation_report": self.mutation_report,
            "orchestrator_report": self.orchestrator_report,
        }
        if self.corrective_action:
            result["corrective_action"] = self.corrective_action
        if self.executed_action:
            result["executed_action"] = self.executed_action
        if self.candidate_selection:
            result["candidate_selection"] = self.candidate_selection
        return result


@dataclass
class TypedCandidateHistory:
    """Typed wrapper for candidate history.
    
    Provides structured access to candidate history state.
    Reduces schema drift risk on lineage tracking paths.
    """
    selected_candidate_id: str | None = None
    selected_attempt_index: int | None = None
    attempts: list[dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TypedCandidateHistory":
        """Create TypedCandidateHistory from raw dict."""
        if data is None:
            return cls()
        return cls(
            selected_candidate_id=data.get("selected_candidate_id"),
            selected_attempt_index=data.get("selected_attempt_index"),
            attempts=data.get("attempts", []),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to raw dict for external contract compatibility."""
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "selected_attempt_index": self.selected_attempt_index,
            "attempts": self.attempts,
        }


@dataclass
class TypedExecutedAction:
    """Typed wrapper for executed action.
    
    Provides structured access to executed action fields.
    Reduces schema drift risk on execution trace paths.
    """
    executed_action: str
    execution_status: str
    branch_taken: str
    target_workflow_id: str | None = None
    selected_candidate_id: str | None = None
    selected_attempt_index: int | None = None
    notes: list[str] = field(default_factory=list)
    error_type: str | None = None
    error_code: str | None = None
    error: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TypedExecutedAction":
        """Create TypedExecutedAction from raw dict."""
        return cls(
            executed_action=data.get("executed_action", "unknown"),
            execution_status=data.get("execution_status", "unknown"),
            branch_taken=data.get("branch_taken", "unknown"),
            target_workflow_id=data.get("target_workflow_id"),
            selected_candidate_id=data.get("selected_candidate_id"),
            selected_attempt_index=data.get("selected_attempt_index"),
            notes=data.get("notes", []),
            error_type=data.get("error_type"),
            error_code=data.get("error_code"),
            error=data.get("error"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to raw dict for external contract compatibility."""
        result = {
            "executed_action": self.executed_action,
            "execution_status": self.execution_status,
            "branch_taken": self.branch_taken,
            "notes": self.notes,
        }
        if self.target_workflow_id:
            result["target_workflow_id"] = self.target_workflow_id
        if self.selected_candidate_id:
            result["selected_candidate_id"] = self.selected_candidate_id
        if self.selected_attempt_index:
            result["selected_attempt_index"] = self.selected_attempt_index
        if self.error_type:
            result["error_type"] = self.error_type
        if self.error_code:
            result["error_code"] = self.error_code
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class TypedBranchOutcome:
    """Typed wrapper for branch outcome.
    
    Provides structured access to branch execution outcome.
    Reduces schema drift risk on branch orchestration paths.
    """
    executed_action: TypedExecutedAction
    updated_result: BranchResult | None = None
    updated_history: TypedCandidateHistory | None = None
    branch_completed: bool = False
    branch_failed: bool = False
    branch_blocked: bool = False
    
    @classmethod
    def from_branch_execution_outcome(
        cls, outcome: Any  # BranchExecutionOutcome from executor
    ) -> "TypedBranchOutcome":
        """Create TypedBranchOutcome from BranchExecutionOutcome."""
        return cls(
            executed_action=TypedExecutedAction.from_dict(outcome.executed_action),
            updated_result=BranchResult.from_dict(outcome.updated_result) if outcome.updated_result else None,
            updated_history=TypedCandidateHistory.from_dict(outcome.updated_candidate_history) if outcome.updated_candidate_history else None,
            branch_completed=outcome.branch_completed,
            branch_failed=outcome.branch_failed,
            branch_blocked=outcome.branch_blocked,
        )
