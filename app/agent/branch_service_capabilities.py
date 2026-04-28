"""Narrow capability interfaces for branch adapter dependencies.

This module provides capability interfaces that adapters depend on instead of
the entire WorkflowAgentService, reducing coupling and making dependencies explicit.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.agent.branch_domain_types import WorkflowSpec, AssetBundle


class AttemptRunnerCapability(ABC):
    """Capability for running single retry attempts."""
    
    @abstractmethod
    async def run_single_attempt(
        self,
        execution_plan: ExecutionPlan,
        workflow_spec: dict[str, Any] | None,  # TODO: migrate to WorkflowSpec | None
        mutation_overrides: dict[str, Any],
        disable_internal_retry: bool,
        save_metadata: bool,
    ) -> dict[str, Any]:
        """Run a single attempt with given parameters."""
        pass


class SwitchRunnerCapability(ABC):
    """Capability for handling workflow switches."""
    
    @abstractmethod
    async def handle_workflow_switch(
        self,
        execution_plan: ExecutionPlan | None,
        first_result: dict[str, Any] | None,
        task_selection: Any,
        assets: dict[str, Any] | None,  # TODO: migrate to AssetBundle | None
        save_metadata: bool,
        switch_applied_this_run: bool,
        candidate_history: Any,
        corrective_action: Any,
        execution_result: Any,
    ) -> dict[str, Any]:
        """Handle workflow switch with given parameters."""
        pass


class CandidateSelectionCapability(ABC):
    """Capability for selecting best candidate from results."""
    
    @abstractmethod
    def choose_best_candidate(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        """Choose best candidate from given results."""
        pass


class HistoryManagementCapability(ABC):
    """Capability for managing candidate history."""
    
    @abstractmethod
    def create_attempt_record(
        self,
        result: dict[str, Any],
        attempt_index: int,
        attempt_kind: str,
        parent_candidate_id: str | None,
    ) -> dict[str, Any]:
        """Create attempt record for history."""
        pass


@dataclass(frozen=True)
class BranchAdapterDependencies:
    """Dependency container for branch adapters.
    
    This bundle provides narrow capability interfaces instead of
    the entire WorkflowAgentService, reducing coupling.
    """
    attempt_runner: AttemptRunnerCapability
    switch_runner: SwitchRunnerCapability
    selection_reader: CandidateSelectionCapability
    history_writer: HistoryManagementCapability
