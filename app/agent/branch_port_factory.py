"""Port factory for branch execution adapter composition.

This module provides a factory layer for creating concrete port adapters,
extracting port assembly logic from workflow_agent_service.py.
"""

from typing import Any

from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.execution_plan import ExecutionPlan
from app.agent.candidate_history import CandidateHistory
from app.agent.task_selector import TaskSelectionResult
from app.agent.branch_execution_ports import (
    RetryBranchPort,
    SwitchBranchPort,
    CandidateSelectionPort,
    CandidateHistoryPort,
)
from app.agent.branch_port_adapters import (
    ServiceRetryPort,
    ServiceSwitchPort,
    ServiceSelectionPort,
    ServiceHistoryPort,
)
from app.agent.branch_service_capabilities import BranchAdapterDependencies


class BranchPortFactory:
    """Factory for creating concrete branch port adapters.
    
    This factory extracts port assembly logic from the service,
    keeping the service as a thin orchestration shell.
    
    Now uses narrow capability dependencies instead of whole service.
    """
    
    def __init__(self, dependencies: BranchAdapterDependencies):
        """Initialize factory with capability dependencies.
        
        Args:
            dependencies: Narrow capability interfaces instead of whole service
        """
        self.dependencies = dependencies
    
    def create_retry_port(
        self,
        workflow_spec: dict[str, Any] | None,
        retry_overrides: dict[str, Any],
        disable_internal_retry: bool,
        save_metadata: bool,
        corrective_action: CorrectiveActionDecision,
    ) -> RetryBranchPort:
        """Create concrete retry port adapter."""
        return ServiceRetryPort(
            attempt_runner=self.dependencies.attempt_runner,
            workflow_spec=workflow_spec,
            retry_overrides=retry_overrides,
            disable_internal_retry=disable_internal_retry,
            save_metadata=save_metadata,
            corrective_action=corrective_action,
        )
    
    def create_switch_port(
        self,
        task_selection: TaskSelectionResult | None,
        assets: dict[str, Any] | None,
        save_metadata: bool,
        switch_applied_this_run: bool,
        candidate_history: CandidateHistory | None,
        corrective_action: CorrectiveActionDecision,
        execution_plan: ExecutionPlan | None,
        first_result: dict[str, Any] | None,
    ) -> SwitchBranchPort:
        """Create concrete switch port adapter."""
        return ServiceSwitchPort(
            switch_runner=self.dependencies.switch_runner,
            task_selection=task_selection,
            assets=assets,
            save_metadata=save_metadata,
            switch_applied_this_run=switch_applied_this_run,
            candidate_history=candidate_history,
            corrective_action=corrective_action,
            execution_plan=execution_plan,
            first_result=first_result,
        )
    
    def create_selection_port(self) -> CandidateSelectionPort:
        """Create concrete selection port adapter."""
        return ServiceSelectionPort(selection_reader=self.dependencies.selection_reader)
    
    def create_history_port(
        self,
        candidate_history: CandidateHistory | None,
    ) -> CandidateHistoryPort:
        """Create concrete history port adapter."""
        return ServiceHistoryPort(history_writer=self.dependencies.history_writer, candidate_history=candidate_history)
    
    def create_all_ports(
        self,
        workflow_spec: dict[str, Any] | None = None,
        retry_overrides: dict[str, Any] | None = None,
        disable_internal_retry: bool = False,
        save_metadata: bool = False,
        corrective_action: CorrectiveActionDecision | None = None,
        task_selection: TaskSelectionResult | None = None,
        assets: dict[str, Any] | None = None,
        switch_applied_this_run: bool = False,
        candidate_history: CandidateHistory | None = None,
        execution_plan: ExecutionPlan | None = None,
        first_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create all port adapters in one call.
        
        Returns:
            Dictionary with all created ports
        """
        ports = {}
        
        if corrective_action:
            ports["retry_port"] = self.create_retry_port(
                workflow_spec=workflow_spec,
                retry_overrides=retry_overrides or {},
                disable_internal_retry=disable_internal_retry,
                save_metadata=save_metadata,
                corrective_action=corrective_action,
            )
            
            ports["switch_port"] = self.create_switch_port(
                task_selection=task_selection,
                assets=assets,
                save_metadata=save_metadata,
                switch_applied_this_run=switch_applied_this_run,
                candidate_history=candidate_history,
                corrective_action=corrective_action,
                execution_plan=execution_plan,
                first_result=first_result,
            )
        
        ports["selection_port"] = self.create_selection_port()
        ports["history_port"] = self.create_history_port(candidate_history)
        
        return ports
