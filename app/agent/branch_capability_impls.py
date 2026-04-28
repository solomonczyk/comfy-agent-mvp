"""Concrete capability implementations for branch execution.

This module provides concrete implementations of capability interfaces,
extracted from workflow_agent_service.py to separate concerns.
"""

from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.agent.branch_service_capabilities import (
    AttemptRunnerCapability,
    SwitchRunnerCapability,
    CandidateSelectionCapability,
    HistoryManagementCapability,
)
from app.agent.branch_domain_types import WorkflowSpec, AssetBundle


class ServiceAttemptRunnerCapability(AttemptRunnerCapability):
    """Concrete implementation of attempt runner capability.
    
    Wraps WorkflowAgentService._run_single_attempt method.
    """
    
    def __init__(self, service: Any):
        self.service = service
    
    async def run_single_attempt(
        self,
        execution_plan: ExecutionPlan,
        workflow_spec: dict[str, Any] | None,
        mutation_overrides: dict[str, Any],
        disable_internal_retry: bool,
        save_metadata: bool,
    ) -> dict[str, Any]:
        return await self.service._run_single_attempt(
            execution_plan=execution_plan,
            workflow_spec=workflow_spec,
            mutation_overrides=mutation_overrides,
            disable_internal_retry=disable_internal_retry,
            save_metadata=save_metadata,
        )


class ServiceSwitchRunnerCapability(SwitchRunnerCapability):
    """Concrete implementation of switch runner capability.
    
    Wraps WorkflowAgentService._handle_workflow_switch method.
    """
    
    def __init__(self, service: Any):
        self.service = service
    
    async def handle_workflow_switch(
        self,
        execution_plan: ExecutionPlan | None,
        first_result: dict[str, Any] | None,
        task_selection: Any,
        assets: dict[str, Any] | None,
        save_metadata: bool,
        switch_applied_this_run: bool,
        candidate_history: Any,
        corrective_action: Any,
        execution_result: Any,
    ) -> dict[str, Any]:
        return await self.service._handle_workflow_switch(
            execution_plan=execution_plan,
            first_result=first_result,
            task_selection=task_selection,
            assets=assets,
            save_metadata=save_metadata,
            switch_applied_this_run=switch_applied_this_run,
            candidate_history=candidate_history,
            corrective_action=corrective_action,
            execution_result=execution_result,
        )


class ServiceCandidateSelectionCapability(CandidateSelectionCapability):
    """Concrete implementation of candidate selection capability.
    
    Wraps WorkflowAgentService._choose_best_candidate method.
    """
    
    def __init__(self, service: Any):
        self.service = service
    
    def choose_best_candidate(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        return self.service._choose_best_candidate(candidates)


class ServiceHistoryManagementCapability(HistoryManagementCapability):
    """Concrete implementation of history management capability.
    
    Wraps WorkflowAgentService._create_attempt_record method.
    """
    
    def __init__(self, service: Any):
        self.service = service
    
    def create_attempt_record(
        self,
        result: dict[str, Any],
        attempt_index: int,
        attempt_kind: str,
        parent_candidate_id: str | None,
    ) -> dict[str, Any]:
        return self.service._create_attempt_record(
            result=result,
            attempt_index=attempt_index,
            attempt_kind=attempt_kind,
            parent_candidate_id=parent_candidate_id,
        )
