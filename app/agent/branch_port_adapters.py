"""Concrete port adapter implementations for WorkflowAgentService.

This module provides concrete port implementations that wrap service logic,
extracted from workflow_agent_service.py to keep the service thin.
"""

from typing import Any

from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.branch_execution_ports import (
    RetryBranchPort,
    SwitchBranchPort,
    CandidateSelectionPort,
    CandidateHistoryPort,
)
from app.agent.branch_state_models import BranchResult
from app.agent.branch_port_commands import (
    RetryBranchCommand,
    SwitchBranchCommand,
    HistoryAddAttemptCommand,
    HistoryMarkSelectedCommand,
)
from app.agent.execution_plan import ExecutionPlan
from app.agent.candidate_history import CandidateHistory
from app.agent.task_selector import TaskSelectionResult
from app.agent.branch_service_capabilities import (
    AttemptRunnerCapability,
    SwitchRunnerCapability,
    CandidateSelectionCapability,
    HistoryManagementCapability,
)


class ServiceRetryPort(RetryBranchPort):
    """Concrete retry port using narrow AttemptRunnerCapability."""
    
    def __init__(
        self,
        attempt_runner: AttemptRunnerCapability,
        workflow_spec: dict[str, Any] | None,
        retry_overrides: dict[str, Any],
        disable_internal_retry: bool,
        save_metadata: bool,
        corrective_action: CorrectiveActionDecision,
    ):
        self.attempt_runner = attempt_runner
        self.workflow_spec = workflow_spec
        self.retry_overrides = retry_overrides
        self.disable_internal_retry = disable_internal_retry
        self.save_metadata = save_metadata
        self.corrective_action = corrective_action
    
    async def execute_retry(
        self,
        plan: ExecutionPlan,
        current: BranchResult,
        command: RetryBranchCommand,
    ) -> BranchResult:
        """Execute retry via capability with typed command."""
        # Use command.workflow_spec if available, otherwise use self.workflow_spec
        workflow_spec_to_use = self.workflow_spec
        if command.workflow_spec:
            workflow_spec_to_use = command.workflow_spec.to_dict()
        
        retry_result = await self.attempt_runner.run_single_attempt(
            execution_plan=plan,
            workflow_spec=workflow_spec_to_use,
            mutation_overrides=self.retry_overrides,
            disable_internal_retry=self.disable_internal_retry,
            save_metadata=self.save_metadata,
        )
        
        # Attach corrective_action and executed_action
        retry_result["corrective_action"] = self.corrective_action.to_dict()
        retry_result["mutation_retry"] = {
            "action": self.corrective_action.action,
            "reason_code": self.corrective_action.reason_code,
            "retry_overrides_applied": {k: v for k, v in self.retry_overrides.items() if not k.startswith("_")},
            "attempt_index": 2,
        }
        
        return BranchResult.from_dict(retry_result)


class ServiceSwitchPort(SwitchBranchPort):
    """Concrete switch port using narrow SwitchRunnerCapability."""
    
    def __init__(
        self,
        switch_runner: SwitchRunnerCapability,
        task_selection: TaskSelectionResult | None,
        assets: dict[str, Any] | None,
        save_metadata: bool,
        switch_applied_this_run: bool,
        candidate_history: CandidateHistory | None,
        corrective_action: CorrectiveActionDecision,
        execution_plan: ExecutionPlan | None,
        first_result: dict[str, Any] | None,
    ):
        self.switch_runner = switch_runner
        self.task_selection = task_selection
        self.assets = assets
        self.save_metadata = save_metadata
        self.switch_applied_this_run = switch_applied_this_run
        self.candidate_history = candidate_history
        self.corrective_action = corrective_action
        self.execution_plan = execution_plan
        self.first_result = first_result
    
    async def execute_switch(
        self,
        plan: ExecutionPlan,
        current: BranchResult,
        command: SwitchBranchCommand,
    ) -> BranchResult:
        """Execute switch via capability with typed command."""
        result = await self.switch_runner.handle_workflow_switch(
            execution_plan=self.execution_plan or command.execution_plan,
            first_result=self.first_result or (command.first_result.to_dict() if command.first_result else None),
            task_selection=self.task_selection or command.task_selection,
            assets=self.assets or (command.assets.to_dict() if command.assets else None),
            save_metadata=self.save_metadata,
            switch_applied_this_run=self.switch_applied_this_run,
            candidate_history=self.candidate_history or command.candidate_history,
            corrective_action=self.corrective_action,
            execution_result=None,
        )
        return BranchResult.from_dict(result)


class ServiceSelectionPort(CandidateSelectionPort):
    """Concrete selection port using narrow CandidateSelectionCapability."""
    
    def __init__(self, selection_reader: CandidateSelectionCapability):
        self.selection_reader = selection_reader
    
    def choose_best_candidate(self, candidates: list[BranchResult]) -> BranchResult:
        """Choose best candidate via capability logic."""
        candidates_dicts = [c.to_dict() for c in candidates]
        best_dict = self.selection_reader.choose_best_candidate(candidates_dicts)
        return BranchResult.from_dict(best_dict)


class ServiceHistoryPort(CandidateHistoryPort):
    """Concrete history port using narrow HistoryManagementCapability."""
    
    def __init__(self, history_writer: HistoryManagementCapability, candidate_history: CandidateHistory | None):
        self.history_writer = history_writer
        self.candidate_history = candidate_history
    
    def add_attempt(self, command: HistoryAddAttemptCommand) -> None:
        """Add attempt via capability logic with typed command."""
        if self.candidate_history:
            attempt_record = self.history_writer.create_attempt_record(
                result=command.result.to_dict(),
                attempt_index=command.attempt_index,
                attempt_kind=command.attempt_kind,
                parent_candidate_id=command.parent_candidate_id,
            )
            self.candidate_history.add_attempt(attempt_record)
    
    def mark_selected(self, command: HistoryMarkSelectedCommand) -> None:
        """Mark selected via capability logic with typed command."""
        if self.candidate_history:
            self.candidate_history.mark_selected(
                candidate_id=command.candidate_id,
                attempt_index=command.attempt_index,
                selection_reason=command.selection_reason,
            )
