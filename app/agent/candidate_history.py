"""Candidate history and attempt lineage tracking for multi-attempt agent runs.

This module provides data structures for tracking all attempts (initial, retry, switch)
and their relationships, enabling transparent lineage and candidate selection reasoning.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class AttemptRecord:
    """Record of a single generation attempt.
    
    Each attempt represents one candidate in the candidate history, with full
    context for debugging, lineage tracking, and selection reasoning.
    """
    attempt_index: int
    candidate_id: str
    parent_candidate_id: str | None = None
    attempt_kind: str = "initial"  # initial | retry_seed | retry_prompt | retry_settings | retry_mutation | workflow_switch
    workflow_id: str | None = None
    task_type: str | None = None
    judge_status: str | None = None
    final_verdict: str | None = None
    final_score: float | None = None
    selected: bool = False
    selection_reason: str | None = None
    source_trigger: str | None = None
    mutation_report: dict[str, Any] | None = None
    mutation_retry: dict[str, Any] | None = None
    workflow_switch: dict[str, Any] | None = None
    corrective_action: dict[str, Any] | None = None  # Canonical corrective action decision
    executed_action: dict[str, Any] | None = None  # Executed action result from CorrectiveActionExecutor
    images: list[dict[str, Any]] = field(default_factory=list)
    metadata_path: str | None = None
    summary_path: str | None = None
    error_type: str | None = None
    error_code: str | None = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "attempt_index": self.attempt_index,
            "candidate_id": self.candidate_id,
            "parent_candidate_id": self.parent_candidate_id,
            "attempt_kind": self.attempt_kind,
            "workflow_id": self.workflow_id,
            "task_type": self.task_type,
            "judge_status": self.judge_status,
            "final_verdict": self.final_verdict,
            "final_score": self.final_score,
            "selected": self.selected,
            "selection_reason": self.selection_reason,
            "source_trigger": self.source_trigger,
            "mutation_report": self.mutation_report,
            "mutation_retry": self.mutation_retry,
            "workflow_switch": self.workflow_switch,
            "corrective_action": self.corrective_action,
            "executed_action": self.executed_action,
            "images": self.images,
            "metadata_path": self.metadata_path,
            "summary_path": self.summary_path,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error": self.error,
        }


@dataclass
class CandidateHistory:
    """History of all candidates in a multi-attempt agent run.
    
    This tracks the complete lineage of attempts, including:
    - Which candidate was selected and why
    - Parent/child relationships between attempts
    - Failed attempts preserved for debugging
    - Full context for each candidate
    """
    selected_candidate_id: str | None = None
    selected_attempt_index: int | None = None
    selection_reason: str | None = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    
    def add_attempt(
        self,
        attempt_record: AttemptRecord,
    ) -> None:
        """Add an attempt record to the history."""
        self.attempts.append(attempt_record)
    
    def mark_selected(
        self,
        candidate_id: str,
        attempt_index: int,
        selection_reason: str,
    ) -> None:
        """Mark a candidate as selected."""
        self.selected_candidate_id = candidate_id
        self.selected_attempt_index = attempt_index
        self.selection_reason = selection_reason
        
        # Update the attempt record's selected flag
        for attempt in self.attempts:
            if attempt.candidate_id == candidate_id:
                attempt.selected = True
                attempt.selection_reason = selection_reason
            else:
                attempt.selected = False
    
    def get_attempt_by_id(self, candidate_id: str) -> AttemptRecord | None:
        """Get an attempt record by candidate ID."""
        for attempt in self.attempts:
            if attempt.candidate_id == candidate_id:
                return attempt
        return None
    
    def get_selected_attempt(self) -> AttemptRecord | None:
        """Get the selected attempt record."""
        if not self.selected_candidate_id:
            return None
        return self.get_attempt_by_id(self.selected_candidate_id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "selected_attempt_index": self.selected_attempt_index,
            "selection_reason": self.selection_reason,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


class AttemptRecordBuilder:
    """Builder for creating AttemptRecord instances."""
    
    def __init__(self) -> None:
        """Initialize builder."""
        self._attempt_index: int = 0
        self._candidate_id: str = ""
        self._parent_candidate_id: str | None = None
        self._attempt_kind: str = "initial"
        self._workflow_id: str | None = None
        self._task_type: str | None = None
        self._judge_status: str | None = None
        self._final_verdict: str | None = None
        self._final_score: float | None = None
        self._selected: bool = False
        self._selection_reason: str | None = None
        self._source_trigger: str | None = None
        self._mutation_report: dict[str, Any] | None = None
        self._mutation_retry: dict[str, Any] | None = None
        self._workflow_switch: dict[str, Any] | None = None
        self._corrective_action: dict[str, Any] | None = None
        self._executed_action: dict[str, Any] | None = None
        self._images: list[dict[str, Any]] = []
        self._metadata_path: str | None = None
        self._summary_path: str | None = None
        self._error_type: str | None = None
        self._error_code: str | None = None
        self._error: str | None = None
    
    def attempt_index(self, value: int) -> "AttemptRecordBuilder":
        """Set attempt index."""
        self._attempt_index = value
        return self
    
    def candidate_id(self, value: str) -> "AttemptRecordBuilder":
        """Set candidate ID."""
        self._candidate_id = value
        return self
    
    def parent_candidate_id(self, value: str | None) -> "AttemptRecordBuilder":
        """Set parent candidate ID."""
        self._parent_candidate_id = value
        return self
    
    def attempt_kind(self, value: str) -> "AttemptRecordBuilder":
        """Set attempt kind."""
        self._attempt_kind = value
        return self
    
    def workflow_id(self, value: str | None) -> "AttemptRecordBuilder":
        """Set workflow ID."""
        self._workflow_id = value
        return self
    
    def task_type(self, value: str | None) -> "AttemptRecordBuilder":
        """Set task type."""
        self._task_type = value
        return self
    
    def judge_status(self, value: str | None) -> "AttemptRecordBuilder":
        """Set judge status."""
        self._judge_status = value
        return self
    
    def final_verdict(self, value: str | None) -> "AttemptRecordBuilder":
        """Set final verdict."""
        self._final_verdict = value
        return self
    
    def final_score(self, value: float | None) -> "AttemptRecordBuilder":
        """Set final score."""
        self._final_score = value
        return self
    
    def selected(self, value: bool) -> "AttemptRecordBuilder":
        """Set selected flag."""
        self._selected = value
        return self
    
    def selection_reason(self, value: str | None) -> "AttemptRecordBuilder":
        """Set selection reason."""
        self._selection_reason = value
        return self
    
    def source_trigger(self, value: str | None) -> "AttemptRecordBuilder":
        """Set source trigger."""
        self._source_trigger = value
        return self
    
    def mutation_report(self, value: dict[str, Any] | None) -> "AttemptRecordBuilder":
        """Set mutation report."""
        self._mutation_report = value
        return self
    
    def mutation_retry(self, value: dict[str, Any] | None) -> "AttemptRecordBuilder":
        """Set mutation retry."""
        self._mutation_retry = value
        return self
    
    def workflow_switch(self, value: dict[str, Any] | None) -> "AttemptRecordBuilder":
        """Set workflow switch."""
        self._workflow_switch = value
        return self
    
    def corrective_action(self, value: dict[str, Any] | None) -> "AttemptRecordBuilder":
        """Set corrective action."""
        self._corrective_action = value
        return self
    
    def executed_action(self, value: dict[str, Any] | None) -> "AttemptRecordBuilder":
        """Set executed action."""
        self._executed_action = value
        return self
    
    def images(self, value: list[dict[str, Any]]) -> "AttemptRecordBuilder":
        """Set images."""
        self._images = value
        return self
    
    def metadata_path(self, value: str | None) -> "AttemptRecordBuilder":
        """Set metadata path."""
        self._metadata_path = value
        return self
    
    def summary_path(self, value: str | None) -> "AttemptRecordBuilder":
        """Set summary path."""
        self._summary_path = value
        return self
    
    def error_type(self, value: str | None) -> "AttemptRecordBuilder":
        """Set error type."""
        self._error_type = value
        return self
    
    def error_code(self, value: str | None) -> "AttemptRecordBuilder":
        """Set error code."""
        self._error_code = value
        return self
    
    def error(self, value: str | None) -> "AttemptRecordBuilder":
        """Set error."""
        self._error = value
        return self
    
    def build(self) -> AttemptRecord:
        """Build the AttemptRecord instance."""
        return AttemptRecord(
            attempt_index=self._attempt_index,
            candidate_id=self._candidate_id,
            parent_candidate_id=self._parent_candidate_id,
            attempt_kind=self._attempt_kind,
            workflow_id=self._workflow_id,
            task_type=self._task_type,
            judge_status=self._judge_status,
            final_verdict=self._final_verdict,
            final_score=self._final_score,
            selected=self._selected,
            selection_reason=self._selection_reason,
            source_trigger=self._source_trigger,
            mutation_report=self._mutation_report,
            mutation_retry=self._mutation_retry,
            workflow_switch=self._workflow_switch,
            corrective_action=self._corrective_action,
            executed_action=self._executed_action,
            images=self._images,
            metadata_path=self._metadata_path,
            summary_path=self._summary_path,
            error_type=self._error_type,
            error_code=self._error_code,
            error=self._error,
        )


def generate_candidate_id() -> str:
    """Generate a unique candidate ID."""
    return f"cand_{uuid.uuid4().hex[:8]}"
