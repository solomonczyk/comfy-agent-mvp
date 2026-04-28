"""Executor ports for explicit dependency injection.

This module provides typed port interfaces for branch execution capabilities,
replacing callback soup with explicit, typed capability abstractions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from app.agent.execution_plan import ExecutionPlan
from app.agent.branch_state_models import BranchResult
from app.agent.branch_port_commands import (
    RetryBranchCommand,
    SwitchBranchCommand,
    SelectionCommand,
    HistoryAddAttemptCommand,
    HistoryMarkSelectedCommand,
)


class RetryBranchPort(ABC):
    """Port for retry branch execution.
    
    Provides explicit retry execution capability without exposing
    the concrete implementation to the executor.
    """
    
    @abstractmethod
    async def execute_retry(self, plan: ExecutionPlan, current: BranchResult, command: RetryBranchCommand) -> BranchResult:
        """Execute retry branch with typed command.
        
        Args:
            plan: Execution plan for retry
            current: Current generation result
            command: Typed retry command with execution parameters
            
        Returns:
            Retry generation result
        """
        pass


class SwitchBranchPort(ABC):
    """Port for switch branch execution.
    
    Provides explicit switch execution capability without exposing
    the concrete implementation to the executor.
    """
    
    @abstractmethod
    async def execute_switch(
        self,
        plan: ExecutionPlan,
        current: BranchResult,
        command: SwitchBranchCommand,
    ) -> BranchResult:
        """Execute switch branch with typed command.
        
        Args:
            plan: Execution plan for switch
            current: Current generation result
            command: Typed switch command with execution parameters
            
        Returns:
            Switched generation result
        """
        pass


class CandidateSelectionPort(ABC):
    """Port for candidate selection.
    
    Provides explicit candidate selection capability without exposing
    the concrete implementation to the executor.
    """
    
    @abstractmethod
    def choose_best_candidate(self, candidates: list[BranchResult]) -> BranchResult:
        """Choose best candidate from list."""
        pass


class CandidateHistoryPort(ABC):
    """Port for candidate history management.
    
    Provides explicit history update capability without exposing
    the concrete implementation to the executor.
    """
    
    @abstractmethod
    def add_attempt(self, command: HistoryAddAttemptCommand) -> None:
        """Add attempt to history with typed command."""
        pass
    
    @abstractmethod
    def mark_selected(self, command: HistoryMarkSelectedCommand) -> None:
        """Mark candidate as selected with typed command."""
        pass


@dataclass
class BranchExecutorPorts:
    """Consolidated executor ports.
    
    Replaces callback bundle with explicit typed ports.
    Reduces coupling and makes dependencies explicit.
    """
    retry_port: RetryBranchPort | None = None
    switch_port: SwitchBranchPort | None = None
    selection_port: CandidateSelectionPort | None = None
    history_port: CandidateHistoryPort | None = None


# Backward compatibility adapters for gradual migration
# These allow existing callback-based code to work with new ports

class CallbackRetryPort(RetryBranchPort):
    """Adapter for callback-based retry execution."""
    
    def __init__(
        self,
        callback: Callable[
            [ExecutionPlan, dict[str, Any], dict[str, Any]],
            Awaitable[dict[str, Any]]
        ]
    ):
        self._callback = callback
    
    async def execute_retry(
        self,
        plan: ExecutionPlan,
        current: BranchResult,
        command: RetryBranchCommand,
    ) -> BranchResult:
        """Execute retry via callback with typed command."""
        # Convert typed command to context dict for backward compatibility
        context = {
            "corrective_action": command.corrective_action,
            "save_metadata": command.save_metadata,
            "disable_internal_retry": command.disable_internal_retry,
            "retry_overrides": command.retry_overrides,
        }
        result_dict = await self._callback(
            plan,
            current.to_dict(),
            context,
        )
        return BranchResult.from_dict(result_dict)


class CallbackSwitchPort(SwitchBranchPort):
    """Adapter for callback-based switch execution."""
    
    def __init__(
        self,
        callback: Callable[
            [ExecutionPlan, dict[str, Any], dict[str, Any]],
            Awaitable[dict[str, Any]]
        ]
    ):
        self._callback = callback
    
    async def execute_switch(
        self,
        plan: ExecutionPlan,
        current: BranchResult,
        command: SwitchBranchCommand,
    ) -> BranchResult:
        """Execute switch via callback with typed command."""
        # Convert typed command to context dict for backward compatibility
        context = {
            "corrective_action": command.corrective_action,
            "save_metadata": command.save_metadata,
            "target_workflow_id": command.target_workflow_id,
            "execution_plan": command.execution_plan,
            "first_result": command.first_result,
            "task_selection": command.task_selection,
            "assets": command.assets,
            "switch_applied_this_run": command.switch_applied_this_run,
            "candidate_history": command.candidate_history,
        }
        result_dict = await self._callback(
            plan,
            current.to_dict(),
            context,
        )
        return BranchResult.from_dict(result_dict)


class CallbackSelectionPort(CandidateSelectionPort):
    """Adapter for callback-based candidate selection."""
    
    def __init__(
        self,
        callback: Callable[[list[dict[str, Any]]], dict[str, Any]]
    ):
        self._callback = callback
    
    def choose_best_candidate(self, candidates: list[BranchResult]) -> BranchResult:
        """Choose best candidate via callback."""
        candidates_dicts = [c.to_dict() for c in candidates]
        result_dict = self._callback(candidates_dicts)
        return BranchResult.from_dict(result_dict)


class CallbackHistoryPort(CandidateHistoryPort):
    """Adapter for callback-based history management."""
    
    def __init__(
        self,
        update_callback: Callable[[dict[str, Any], int, str, str | None], None],
        mark_callback: Callable[[str, int, str], None],
    ):
        self._update_callback = update_callback
        self._mark_callback = mark_callback
    
    def add_attempt(self, command: HistoryAddAttemptCommand) -> None:
        """Add attempt via callback with typed command."""
        self._update_callback(
            command.result.to_dict() if hasattr(command.result, 'to_dict') else command.result,
            command.attempt_index,
            command.attempt_kind,
            command.parent_candidate_id,
        )
    
    def mark_selected(self, command: HistoryMarkSelectedCommand) -> None:
        """Mark selected via callback with typed command."""
        self._mark_callback(command.candidate_id, command.attempt_index, command.selection_reason)
