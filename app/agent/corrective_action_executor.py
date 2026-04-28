"""Corrective Action Executor for centralized execution layer.

This module provides the canonical executor for corrective actions, centralizing
the execution logic that was previously drifted between workflow_agent_service.py,
retry path, and switch path.

The executor is responsible for HOW the canonical corrective action is executed,
while CorrectiveActionPolicy is responsible for WHAT action to take.

Execution flow:
corrective_action (decision) -> executor.execute() -> executed_action (execution result)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.execution_plan import ExecutionPlan
from app.agent.candidate_history import CandidateHistory
from app.agent.branch_execution_context import (
    BranchExecutionContext,
    BranchExecutorDependencies,
)
from app.agent.branch_state_models import BranchResult, TypedCandidateHistory
from app.agent.branch_execution_ports import BranchExecutorPorts
from app.agent.branch_port_commands import (
    RetryBranchCommand,
    SwitchBranchCommand,
    HistoryAddAttemptCommand,
    HistoryMarkSelectedCommand,
)
from app.agent.branch_domain_types import WorkflowSpec, AssetBundle


# Callback type definitions for branch execution
RetryCallback = Callable[
    [ExecutionPlan, dict[str, Any], dict[str, Any]],
    Awaitable[dict[str, Any]]
]
SwitchCallback = Callable[
    [ExecutionPlan, dict[str, Any], dict[str, Any]],
    Awaitable[dict[str, Any]]
]
ChooseBestCandidateCallback = Callable[
    [list[dict[str, Any]]],
    dict[str, Any]
]
UpdateHistoryCallback = Callable[
    [dict[str, Any], int, str, str | None],
    None
]
MarkSelectedCallback = Callable[
    [str, int, str],
    None
]


# Normalized execution statuses
EXECUTION_STATUS_COMPLETED = "completed"
EXECUTION_STATUS_BLOCKED = "blocked"
EXECUTION_STATUS_FAILED = "failed"
EXECUTION_STATUS_SKIPPED = "skipped"

# Normalized branch types
BRANCH_ACCEPT = "accept"
BRANCH_RETRY = "retry"
BRANCH_SWITCH = "switch"
BRANCH_REJECT = "reject"


@dataclass
class BranchExecutionOutcome:
    """Canonical outcome of executing a corrective action branch.
    
    This dataclass represents the complete result of branch execution,
    including the execution result, updated state, and branch completion status.
    
    This is the return type for executor-owned branch orchestration.
    The executor not only validates the branch but actually runs it and
    returns the final outcome.
    
    Field hierarchy:
    - executed_action: Execution layer (what happened)
    - updated_result: Updated generation result after branch execution
    - updated_candidate_history: Updated candidate history with new attempts
    - selected_candidate_id: ID of selected candidate (parity across layers)
    - selected_attempt_index: Index of selected attempt (parity across layers)
    - branch_completed: Whether branch execution completed successfully
    - branch_failed: Whether branch execution failed
    - branch_blocked: Whether branch was blocked before execution
    - notes: Additional context about branch execution
    """
    executed_action: dict[str, Any]
    updated_result: dict[str, Any] | None = None
    updated_candidate_history: dict[str, Any] | None = None
    selected_candidate_id: str | None = None
    selected_attempt_index: int | None = None
    branch_completed: bool = False
    branch_failed: bool = False
    branch_blocked: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class CorrectiveActionExecutionResult:
    """Result of executing a corrective action.
    
    This dataclass represents the execution layer - what actually happened
    when the canonical corrective action was executed.
    
    Separation of concerns:
    - corrective_action: decision layer (what was decided)
    - executed_action: execution layer (what actually happened)
    """
    executed_action: str  # The action that was actually executed
    execution_status: str  # completed | blocked | failed | skipped
    selected_candidate_id: str | None = None
    selected_attempt_index: int | None = None
    branch_taken: str | None = None  # accept | retry | switch | reject
    target_workflow_id: str | None = None
    notes: list[str] = field(default_factory=list)
    error_type: str | None = None
    error_code: str | None = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "executed_action": self.executed_action,
            "execution_status": self.execution_status,
            "selected_candidate_id": self.selected_candidate_id,
            "selected_attempt_index": self.selected_attempt_index,
            "branch_taken": self.branch_taken,
            "target_workflow_id": self.target_workflow_id,
            "notes": self.notes,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error": self.error,
        }


class CorrectiveActionExecutor:
    """Canonical executor for corrective actions.
    
    This executor centralizes the execution logic for all corrective action branches:
    - accept: accept the current result
    - retry_seed: retry with new seed
    - retry_prompt: retry with prompt repairs
    - retry_settings: retry with settings repairs
    - switch_workflow: switch to a different workflow
    - reject: reject the current result
    
    The executor does NOT make decisions - it only executes the decision
    made by CorrectiveActionPolicy.
    
    Responsibility separation:
    - CorrectiveActionPolicy: decides WHAT to do
    - CorrectiveActionExecutor: executes HOW to do it (including branch orchestration)
    - WorkflowSwitchPolicy: validates IF switch is safe
    
    The executor now owns the full branch orchestration flow:
    - validates the branch
    - executes the branch (retry/switch/accept/reject)
    - manages candidate selection
    - returns final BranchExecutionOutcome
    """
    
    def __init__(self) -> None:
        """Initialize corrective action executor."""
        pass
    
    async def execute_branch(
        self,
        context: BranchExecutionContext,
        deps: BranchExecutorDependencies,
    ) -> BranchExecutionOutcome:
        """Execute a corrective action branch with full orchestration.
        
        This method owns the complete branch execution flow:
        - validates the branch
        - executes retry/switch/accept/reject
        - manages candidate selection
        - returns final outcome with updated state
        
        Args:
            context: BranchExecutionContext with run-state data (corrective_action, current_result, etc.)
            deps: BranchExecutorDependencies with callbacks and operations
            
        Returns:
            BranchExecutionOutcome with final result, updated history, and branch status
        """
        action = context.corrective_action.action
        
        # Get execution validation result
        execution_result = self.execute(
            corrective_action=context.corrective_action,
            current_result=context.current_result,
            candidate_history=None,  # Not used for validation
            execution_plan=context.execution_plan,
            mutation_report=context.mutation_report,
            assets=context.assets,
        )
        
        # Route based on branch type and execution status
        if action == "accept":
            return await self._orchestrate_accept_branch(
                execution_result=execution_result,
                current_result=context.current_result,
                candidate_history=context.candidate_history,
            )
        
        elif action == "reject":
            return await self._orchestrate_reject_branch(
                execution_result=execution_result,
                current_result=context.current_result,
                candidate_history=context.candidate_history,
            )
        
        elif action == "switch_workflow":
            return await self._orchestrate_switch_branch(
                execution_result=execution_result,
                corrective_action=context.corrective_action,
                current_result=context.current_result,
                execution_plan=context.execution_plan,
                mutation_report=context.mutation_report,
                assets=context.assets,
                deps=deps,
                candidate_history=context.candidate_history,
            )
        
        elif action in ("retry_seed", "retry_prompt", "retry_settings"):
            return await self._orchestrate_retry_branch(
                execution_result=execution_result,
                corrective_action=context.corrective_action,
                current_result=context.current_result,
                execution_plan=context.execution_plan,
                mutation_report=context.mutation_report,
                deps=deps,
                candidate_history=context.candidate_history,
            )
        
        else:
            # Unknown action - return failed outcome
            history_dict = context.candidate_history.to_dict() if context.candidate_history else None
            return BranchExecutionOutcome(
                executed_action=execution_result.to_dict(),
                updated_result=context.current_result,
                updated_candidate_history=history_dict,
                branch_completed=False,
                branch_failed=True,
                branch_blocked=False,
                notes=[f"Unknown corrective action: {action}"],
            )
    
    async def _orchestrate_accept_branch(
        self,
        execution_result: CorrectiveActionExecutionResult,
        current_result: dict[str, Any],
        candidate_history: TypedCandidateHistory | None,
    ) -> BranchExecutionOutcome:
        """Orchestrate accept branch execution.
        
        Args:
            execution_result: Execution validation result
            current_result: Current generation result
            candidate_history: Current candidate history
            
        Returns:
            BranchExecutionOutcome with accept branch result
        """
        history_dict = candidate_history.to_dict() if candidate_history else None
        return BranchExecutionOutcome(
            executed_action=execution_result.to_dict(),
            updated_result=current_result,
            updated_candidate_history=history_dict,
            selected_candidate_id=execution_result.selected_candidate_id,
            selected_attempt_index=execution_result.selected_attempt_index,
            branch_completed=True,
            branch_failed=False,
            branch_blocked=False,
            notes=execution_result.notes,
        )
    
    async def _orchestrate_reject_branch(
        self,
        execution_result: CorrectiveActionExecutionResult,
        current_result: dict[str, Any],
        candidate_history: TypedCandidateHistory | None,
    ) -> BranchExecutionOutcome:
        """Orchestrate reject branch execution.
        
        Args:
            execution_result: Execution validation result
            current_result: Current generation result
            candidate_history: Current candidate history
            
        Returns:
            BranchExecutionOutcome with reject branch result
        """
        history_dict = candidate_history.to_dict() if candidate_history else None
        return BranchExecutionOutcome(
            executed_action=execution_result.to_dict(),
            updated_result=current_result,
            updated_candidate_history=history_dict,
            selected_candidate_id=execution_result.selected_candidate_id,
            selected_attempt_index=execution_result.selected_attempt_index,
            branch_completed=True,
            branch_failed=False,
            branch_blocked=False,
            notes=execution_result.notes,
        )
    
    async def _orchestrate_switch_branch(
        self,
        execution_result: CorrectiveActionExecutionResult,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any],
        execution_plan: ExecutionPlan,
        mutation_report: dict[str, Any],
        assets: dict[str, Any] | None,
        deps: BranchExecutorDependencies,
        candidate_history: TypedCandidateHistory | None,
    ) -> BranchExecutionOutcome:
        """Orchestrate switch branch execution using ports only.
        
        Args:
            execution_result: Execution validation result
            corrective_action: Canonical decision
            current_result: Current generation result
            execution_plan: Current execution plan
            mutation_report: Mutation report
            assets: Available assets
            deps: BranchExecutorDependencies with ports only
            candidate_history: Current candidate history
            
        Returns:
            BranchExecutionOutcome with switch branch result
        """
        # Extract ports
        ports = deps.ports
        switch_port = ports.switch_port if ports else None
        selection_port = ports.selection_port if ports else None
        history_port = ports.history_port if ports else None
        
        # Convert to dict for outcome
        history_dict = candidate_history.to_dict() if candidate_history else None
        
        # If switch is blocked, return current result with blocked status
        if execution_result.execution_status == EXECUTION_STATUS_BLOCKED:
            return BranchExecutionOutcome(
                executed_action=execution_result.to_dict(),
                updated_result=current_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=execution_result.selected_candidate_id,
                selected_attempt_index=execution_result.selected_attempt_index,
                branch_completed=False,
                branch_failed=False,
                branch_blocked=True,
                notes=execution_result.notes,
            )
        
        # If no switch port provided, return completed without execution
        if not switch_port:
            return BranchExecutionOutcome(
                executed_action=execution_result.to_dict(),
                updated_result=current_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=execution_result.selected_candidate_id,
                selected_attempt_index=execution_result.selected_attempt_index,
                branch_completed=True,
                branch_failed=False,
                branch_blocked=False,
                notes=execution_result.notes + ["No switch port provided - validation only"],
            )
        
        # Get parent candidate ID safely
        parent_candidate_id = None
        if candidate_history and candidate_history.attempts:
            if candidate_history.attempts and len(candidate_history.attempts) > 0:
                parent_candidate_id = candidate_history.attempts[0].get("candidate_id")
        
        # Execute switch branch via port with typed command
        try:
            # Use typed state for current result
            current_typed = BranchResult.from_dict(current_result)
            
            # Normalize attempt kind for switch
            attempt_kind = "workflow_switch"
            
            # Build typed switch command with strongly-typed corrective_action and AssetBundle
            asset_bundle = AssetBundle.from_dict(assets) if assets else None
            switch_command = SwitchBranchCommand(
                corrective_action=corrective_action,  # Now typed object, not dict
                save_metadata=True,  # TODO: extract from context if needed
                target_workflow_id=corrective_action.target_workflow_id or "",
                execution_plan=execution_plan,
                first_result=current_typed,  # Now BranchResult instead of dict
                task_selection=None,  # TODO: extract from context if needed
                assets=asset_bundle,  # Now typed domain object
                switch_applied_this_run=False,  # TODO: extract from context if needed
                candidate_history=None,  # TODO: extract from context if needed
            )
            
            switch_typed = await switch_port.execute_switch(
                execution_plan,
                current_typed,
                switch_command,
            )
            switch_result = switch_typed.to_dict()
            
            # Update history via port with typed command
            if history_port:
                history_command = HistoryAddAttemptCommand(
                    result=switch_typed,
                    attempt_index=len(candidate_history.attempts) + 1 if candidate_history else 2,
                    attempt_kind=attempt_kind,
                    parent_candidate_id=parent_candidate_id,
                )
                history_port.add_attempt(history_command)
            
            # Choose best candidate via port
            best_result = current_result
            selected_index = 0
            if selection_port:
                candidates_typed = [current_typed, switch_typed]
                best_typed = selection_port.choose_best_candidate(candidates_typed)
                best_result = best_typed.to_dict()
                selected_index = 1 if best_typed == switch_typed else 0
            
            # Mark selected candidate via port with typed command
            selected_candidate_id = None
            selected_attempt_index = None
            if history_port:
                # Get candidate ID from attempts after update
                attempts = candidate_history.attempts if candidate_history else []
                if attempts and selected_index < len(attempts):
                    selected_candidate_id = attempts[selected_index].get("candidate_id")
                    selection_reason = "switch_candidate_won" if selected_index == 1 else "initial_candidate_kept"
                    history_command = HistoryMarkSelectedCommand(
                        candidate_id=selected_candidate_id,
                        attempt_index=selected_index + 1,
                        selection_reason=selection_reason,
                    )
                    history_port.mark_selected(history_command)
                    selected_attempt_index = selected_index + 1
            
            # Update executed_action with selected candidate info
            executed_action_dict = execution_result.to_dict()
            executed_action_dict["selected_candidate_id"] = selected_candidate_id
            executed_action_dict["selected_attempt_index"] = selected_attempt_index
            
            return BranchExecutionOutcome(
                executed_action=executed_action_dict,
                updated_result=best_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=selected_candidate_id,
                selected_attempt_index=selected_attempt_index,
                branch_completed=True,
                branch_failed=False,
                branch_blocked=False,
                notes=execution_result.notes + ["Switch branch executed successfully"],
            )
        
        except Exception as e:
            # Switch failed
            failed_executed_action = execution_result.to_dict()
            failed_executed_action["execution_status"] = EXECUTION_STATUS_FAILED
            failed_executed_action["error_type"] = "switch_execution_error"
            failed_executed_action["error"] = str(e)
            
            return BranchExecutionOutcome(
                executed_action=failed_executed_action,
                updated_result=current_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=execution_result.selected_candidate_id,
                selected_attempt_index=execution_result.selected_attempt_index,
                branch_completed=False,
                branch_failed=True,
                branch_blocked=False,
                notes=execution_result.notes + [f"Switch branch failed: {str(e)}"],
            )
    
    async def _orchestrate_retry_branch(
        self,
        execution_result: CorrectiveActionExecutionResult,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any],
        execution_plan: ExecutionPlan,
        mutation_report: dict[str, Any],
        deps: BranchExecutorDependencies,
        candidate_history: TypedCandidateHistory | None,
    ) -> BranchExecutionOutcome:
        """Orchestrate retry branch execution using ports only.
        
        Args:
            execution_result: Execution validation result
            corrective_action: Canonical decision
            current_result: Current generation result
            execution_plan: Current execution plan
            mutation_report: Mutation report
            deps: BranchExecutorDependencies with ports only
            candidate_history: Current candidate history
            
        Returns:
            BranchExecutionOutcome with retry branch result
        """
        # Extract ports
        ports = deps.ports
        retry_port = ports.retry_port if ports else None
        selection_port = ports.selection_port if ports else None
        history_port = ports.history_port if ports else None
        
        # Convert to dict for outcome
        history_dict = candidate_history.to_dict() if candidate_history else None
        
        # If no retry port provided, return completed without execution
        if not retry_port:
            return BranchExecutionOutcome(
                executed_action=execution_result.to_dict(),
                updated_result=current_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=execution_result.selected_candidate_id,
                selected_attempt_index=execution_result.selected_attempt_index,
                branch_completed=True,
                branch_failed=False,
                branch_blocked=False,
                notes=execution_result.notes + ["No retry port provided - validation only"],
            )
        
        # Get parent candidate ID safely
        parent_candidate_id = None
        if candidate_history and candidate_history.attempts:
            if candidate_history.attempts and len(candidate_history.attempts) > 0:
                parent_candidate_id = candidate_history.attempts[0].get("candidate_id")
        
        # Execute retry branch via port with typed command
        try:
            # Use typed state for current result
            current_typed = BranchResult.from_dict(current_result)
            
            # Normalize attempt kind from corrective action
            attempt_kind = corrective_action.action  # e.g., retry_seed, retry_prompt, retry_settings
            
            # Build typed retry command with strongly-typed corrective_action and WorkflowSpec
            workflow_spec = WorkflowSpec.from_dict(mutation_report.get("workflow_spec", {})) if mutation_report else None
            retry_command = RetryBranchCommand(
                corrective_action=corrective_action,  # Now typed object, not dict
                save_metadata=True,  # TODO: extract from context if needed
                disable_internal_retry=True,  # TODO: extract from context if needed
                retry_overrides=mutation_report.get("retry_overrides", {}) if mutation_report else {},
                workflow_spec=workflow_spec,  # Now typed domain object
            )
            
            retry_typed = await retry_port.execute_retry(
                execution_plan,
                current_typed,
                retry_command,
            )
            retry_result = retry_typed.to_dict()
            
            # Update history via port with typed command
            if history_port:
                history_command = HistoryAddAttemptCommand(
                    result=retry_typed,
                    attempt_index=len(candidate_history.attempts) + 1 if candidate_history else 2,
                    attempt_kind=attempt_kind,
                    parent_candidate_id=parent_candidate_id,
                )
                history_port.add_attempt(history_command)
            
            # Choose best candidate via port
            best_result = current_result
            selected_index = 0
            if selection_port:
                candidates_typed = [current_typed, retry_typed]
                best_typed = selection_port.choose_best_candidate(candidates_typed)
                best_result = best_typed.to_dict()
                selected_index = 1 if best_typed == retry_typed else 0
            
            # Mark selected candidate via port with typed command
            selected_candidate_id = None
            selected_attempt_index = None
            if history_port:
                # Get candidate ID from attempts after update
                attempts = candidate_history.attempts if candidate_history else []
                if attempts and selected_index < len(attempts):
                    selected_candidate_id = attempts[selected_index].get("candidate_id")
                    selection_reason = "retry_candidate_won" if selected_index == 1 else "initial_candidate_kept"
                    history_command = HistoryMarkSelectedCommand(
                        candidate_id=selected_candidate_id,
                        attempt_index=selected_index + 1,
                        selection_reason=selection_reason,
                    )
                    history_port.mark_selected(history_command)
                    selected_attempt_index = selected_index + 1
            
            # Update executed_action with selected candidate info
            executed_action_dict = execution_result.to_dict()
            executed_action_dict["selected_candidate_id"] = selected_candidate_id
            executed_action_dict["selected_attempt_index"] = selected_attempt_index
            
            return BranchExecutionOutcome(
                executed_action=executed_action_dict,
                updated_result=best_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=selected_candidate_id,
                selected_attempt_index=selected_attempt_index,
                branch_completed=True,
                branch_failed=False,
                branch_blocked=False,
                notes=execution_result.notes + ["Retry branch executed successfully"],
            )
        
        except Exception as e:
            # Retry failed
            failed_executed_action = execution_result.to_dict()
            failed_executed_action["execution_status"] = EXECUTION_STATUS_FAILED
            failed_executed_action["error_type"] = "retry_execution_error"
            failed_executed_action["error"] = str(e)
            
            return BranchExecutionOutcome(
                executed_action=failed_executed_action,
                updated_result=current_result,
                updated_candidate_history=history_dict,
                selected_candidate_id=execution_result.selected_candidate_id,
                selected_attempt_index=execution_result.selected_attempt_index,
                branch_completed=False,
                branch_failed=True,
                branch_blocked=False,
                notes=execution_result.notes + [f"Retry branch failed: {str(e)}"],
            )
    
    def execute(
        self,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any] | None,
        candidate_history: CandidateHistory | None,
        execution_plan: ExecutionPlan | None,
        mutation_report: dict[str, Any] | None,
        assets: dict[str, Any] | None,
    ) -> CorrectiveActionExecutionResult:
        """Execute a corrective action and return execution result.
        
        This method routes to the appropriate execution path based on the
        canonical corrective action decision.
        
        Args:
            corrective_action: Canonical decision from CorrectiveActionPolicy
            current_result: Current generation result
            candidate_history: Candidate history tracking attempts
            execution_plan: Current execution plan
            mutation_report: Mutation report from current attempt
            assets: Available assets
            
        Returns:
            CorrectiveActionExecutionResult with execution details
        """
        action = corrective_action.action
        
        # Route based on canonical action
        if action == "accept":
            return self._execute_accept(
                corrective_action=corrective_action,
                current_result=current_result,
                candidate_history=candidate_history,
            )
        
        elif action == "reject":
            return self._execute_reject(
                corrective_action=corrective_action,
                current_result=current_result,
                candidate_history=candidate_history,
            )
        
        elif action == "switch_workflow":
            return self._execute_switch_workflow(
                corrective_action=corrective_action,
                current_result=current_result,
                candidate_history=candidate_history,
                execution_plan=execution_plan,
                mutation_report=mutation_report,
                assets=assets,
            )
        
        elif action in ("retry_seed", "retry_prompt", "retry_settings"):
            return self._execute_retry(
                corrective_action=corrective_action,
                current_result=current_result,
                candidate_history=candidate_history,
                execution_plan=execution_plan,
                mutation_report=mutation_report,
            )
        
        else:
            # Unknown action - treat as failed
            return CorrectiveActionExecutionResult(
                executed_action=action,
                execution_status=EXECUTION_STATUS_FAILED,
                branch_taken=None,
                notes=[f"Unknown corrective action: {action}"],
                error_type="execution_error",
                error="Unknown corrective action type",
            )
    
    def _execute_accept(
        self,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any] | None,
        candidate_history: CandidateHistory | None,
    ) -> CorrectiveActionExecutionResult:
        """Execute accept action.
        
        Args:
            corrective_action: Canonical decision
            current_result: Current generation result
            candidate_history: Candidate history
            
        Returns:
            Execution result with completed status
        """
        # Get selected candidate info from history if available
        selected_candidate_id = None
        selected_attempt_index = None
        
        if candidate_history:
            selected_candidate_id = candidate_history.selected_candidate_id
            selected_attempt_index = candidate_history.selected_attempt_index
        
        return CorrectiveActionExecutionResult(
            executed_action=corrective_action.action,
            execution_status=EXECUTION_STATUS_COMPLETED,
            selected_candidate_id=selected_candidate_id,
            selected_attempt_index=selected_attempt_index,
            branch_taken=BRANCH_ACCEPT,
            target_workflow_id=corrective_action.selected_workflow_id,
            notes=["Accepted current result without further action"],
        )
    
    def _execute_reject(
        self,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any] | None,
        candidate_history: CandidateHistory | None,
    ) -> CorrectiveActionExecutionResult:
        """Execute reject action.
        
        Args:
            corrective_action: Canonical decision
            current_result: Current generation result
            candidate_history: Candidate history
            
        Returns:
            Execution result with completed or skipped status
        """
        # Get selected candidate info from history if available
        selected_candidate_id = None
        selected_attempt_index = None
        
        if candidate_history:
            selected_candidate_id = candidate_history.selected_candidate_id
            selected_attempt_index = candidate_history.selected_attempt_index
        
        return CorrectiveActionExecutionResult(
            executed_action=corrective_action.action,
            execution_status=EXECUTION_STATUS_COMPLETED,  # or SKIPPED depending on contract
            selected_candidate_id=selected_candidate_id,
            selected_attempt_index=selected_attempt_index,
            branch_taken=BRANCH_REJECT,
            target_workflow_id=corrective_action.selected_workflow_id,
            notes=["Rejected current result without further action"],
        )
    
    def _execute_switch_workflow(
        self,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any] | None,
        candidate_history: CandidateHistory | None,
        execution_plan: ExecutionPlan | None,
        mutation_report: dict[str, Any] | None,
        assets: dict[str, Any] | None,
    ) -> CorrectiveActionExecutionResult:
        """Execute switch_workflow action.
        
        This method validates if the switch is allowed and returns the appropriate
        execution status (completed if switched, blocked if not allowed).
        
        Args:
            corrective_action: Canonical decision
            current_result: Current generation result
            candidate_history: Candidate history
            execution_plan: Current execution plan
            mutation_report: Mutation report
            assets: Available assets
            
        Returns:
            Execution result with completed or blocked status
        """
        # Get selected candidate info from history if available
        selected_candidate_id = None
        selected_attempt_index = None
        
        if candidate_history:
            selected_candidate_id = candidate_history.selected_candidate_id
            selected_attempt_index = candidate_history.selected_attempt_index
        
        # Check if switch is allowed by the decision
        if not corrective_action.switch_allowed:
            return CorrectiveActionExecutionResult(
                executed_action=corrective_action.action,
                execution_status=EXECUTION_STATUS_BLOCKED,
                selected_candidate_id=selected_candidate_id,
                selected_attempt_index=selected_attempt_index,
                branch_taken=BRANCH_SWITCH,
                target_workflow_id=corrective_action.target_workflow_id,
                notes=corrective_action.notes + ["Switch blocked by decision"],
                error_type="switch_blocked",
                error_code="SWITCH_NOT_ALLOWED",
                error=corrective_action.reason,
            )
        
        # Switch is allowed - execution proceeds
        # Note: The actual switch execution happens in the service layer
        # This executor only validates and returns the execution result
        
        return CorrectiveActionExecutionResult(
            executed_action=corrective_action.action,
            execution_status=EXECUTION_STATUS_COMPLETED,
            selected_candidate_id=selected_candidate_id,
            selected_attempt_index=selected_attempt_index,
            branch_taken=BRANCH_SWITCH,
            target_workflow_id=corrective_action.target_workflow_id,
            notes=corrective_action.notes + ["Switch workflow execution initiated"],
        )
    
    def _execute_retry(
        self,
        corrective_action: CorrectiveActionDecision,
        current_result: dict[str, Any] | None,
        candidate_history: CandidateHistory | None,
        execution_plan: ExecutionPlan | None,
        mutation_report: dict[str, Any] | None,
    ) -> CorrectiveActionExecutionResult:
        """Execute retry action (retry_seed, retry_prompt, retry_settings).
        
        Args:
            corrective_action: Canonical decision
            current_result: Current generation result
            candidate_history: Candidate history
            execution_plan: Current execution plan
            mutation_report: Mutation report
            
        Returns:
            Execution result with completed status
        """
        # Get selected candidate info from history if available
        selected_candidate_id = None
        selected_attempt_index = None
        
        if candidate_history:
            selected_candidate_id = candidate_history.selected_candidate_id
            selected_attempt_index = candidate_history.selected_attempt_index
        
        # Note: The actual retry execution happens in the service layer
        # This executor only validates and returns the execution result
        
        return CorrectiveActionExecutionResult(
            executed_action=corrective_action.action,
            execution_status=EXECUTION_STATUS_COMPLETED,
            selected_candidate_id=selected_candidate_id,
            selected_attempt_index=selected_attempt_index,
            branch_taken=BRANCH_RETRY,
            target_workflow_id=corrective_action.selected_workflow_id,
            notes=corrective_action.notes + [f"Retry execution initiated: {corrective_action.action}"],
        )
