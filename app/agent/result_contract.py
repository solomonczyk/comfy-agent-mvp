"""Unified agent result contract for all agent outcomes.

This module provides a stable, unified contract for agent results regardless of
whether the outcome is success, planning failure, execution failure, mutation failure,
or judge/retry enriched result.

All agent outcomes should return the same top-level schema with differences in
values, not in structure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agent.candidate_history import CandidateHistory


class FailedStage(str, Enum):
    """Normalized enumeration of failure stages in the agent pipeline."""
    
    PLANNING_GUARD = "planning_guard"
    WORKFLOW_LOOKUP = "workflow_lookup"
    EXECUTION_PLAN_BUILD = "execution_plan_build"
    WORKFLOW_MUTATION = "workflow_mutation"
    GENERATION = "generation"
    JUDGE_PIPELINE = "judge_pipeline"
    RETRY_LOOP = "retry_loop"


class ErrorCode(str, Enum):
    """Normalized enumeration of error codes in the agent pipeline."""
    
    MISSING_REQUIRED_INPUTS = "MISSING_REQUIRED_INPUTS"
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_NOT_IMPLEMENTED = "WORKFLOW_NOT_IMPLEMENTED"
    MUTATION_CONTRACT_ERROR = "MUTATION_CONTRACT_ERROR"
    GENERATION_FAILED = "GENERATION_FAILED"
    JUDGE_PIPELINE_FAILED = "JUDGE_PIPELINE_FAILED"
    RETRY_LOOP_FAILED = "RETRY_LOOP_FAILED"


@dataclass
class AgentResult:
    """Unified agent result contract.
    
    This dataclass represents the canonical result structure for all agent outcomes.
    Success and failure differ in field values, not in structure.
    
    Field hierarchy:
    - corrective_action: CANONICAL decision layer (source of truth)
    - retry_decision: DERIVED/COMPATIBILITY field (deprecated, for backward compatibility only)
    - workflow_switch: DERIVED/COMPATIBILITY field (deprecated, for backward compatibility only)
    """
    # Core status fields
    status: str  # "completed" | "failed"
    failed_stage: FailedStage | None = None
    error_type: str | None = None
    error_code: ErrorCode | None = None
    error: str | None = None
    
    # Input context
    user_prompt: str = ""
    
    # Agent pipeline fields
    task_selection: dict[str, Any] | None = None
    execution_plan: dict[str, Any] | None = None
    mutation_report: dict[str, Any] | None = None
    mutation_retry: dict[str, Any] | None = None
    
    # Judge/retry fields
    judge_status: str | None = None  # "pass" | "retry" | "reject"
    orchestrator_report: dict[str, Any] | None = None
    retry_decision: dict[str, Any] | None = None  # DERIVED/COMPATIBILITY: Use corrective_action instead (kept for backward compatibility only)
    retry_loop: dict[str, Any] | None = None
    workflow_switch: dict[str, Any] | None = None  # DERIVED/COMPATIBILITY: Use corrective_action instead (kept for backward compatibility only)
    
    # Workflow switch field
    # workflow_switch: dict[str, Any] | None = None
    
    # Corrective action field (canonical decision layer)
    corrective_action: dict[str, Any] | None = None  # CANONICAL: Corrective action decision from CorrectiveActionPolicy (source of truth)
    
    # Candidate history field
    candidate_history: dict[str, Any] | None = None
    
    # Candidate selection field
    candidate_selection: dict[str, Any] | None = None
    
    # Executed action field (execution layer)
    executed_action: dict[str, Any] | None = None  # EXECUTION: What actually happened when corrective_action was executed
    
    # Output fields
    images: list[dict[str, Any]] = field(default_factory=list)
    metadata_path: str | None = None
    summary_path: str | None = None
    recipe_validation: dict[str, Any] | None = None
    trace_path: str | None = None
    tool_chain: list[str] | None = None
    upscale_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the result with normalized field names
        """
        result = {
            "status": self.status,
            "failed_stage": self.failed_stage.value if self.failed_stage else None,
            "error_type": self.error_type,
            "error_code": self.error_code.value if self.error_code else None,
            "error": self.error,
            "user_prompt": self.user_prompt,
            "task_selection": self.task_selection,
            "execution_plan": self.execution_plan,
            "mutation_report": self.mutation_report,
            "mutation_retry": self.mutation_retry,
            "judge_status": self.judge_status,
            "orchestrator_report": self.orchestrator_report,
            "retry_decision": self.retry_decision,
            "retry_loop": self.retry_loop,
            "workflow_switch": self.workflow_switch,
            "corrective_action": self.corrective_action,
            "candidate_history": self.candidate_history,
            "candidate_selection": self.candidate_selection,
            "executed_action": self.executed_action,
            "images": self.images,
            "metadata_path": self.metadata_path,
            "summary_path": self.summary_path,
            "recipe_validation": self.recipe_validation,
            "trace_path": self.trace_path,
            "tool_chain": self.tool_chain,
            "upscale_result": self.upscale_result,
        }
        return result


class AgentResultBuilder:
    """Builder for creating unified agent results.
    
    This builder provides a fluent interface for constructing AgentResult instances
    for different outcome scenarios while maintaining schema consistency.
    """
    
    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._status = "completed"
        self._failed_stage: FailedStage | None = None
        self._error_type: str | None = None
        self._error_code: ErrorCode | None = None
        self._error: str | None = None
        self._user_prompt = ""
        self._task_selection: dict[str, Any] | None = None
        self._execution_plan: dict[str, Any] | None = None
        self._mutation_report: dict[str, Any] | None = None
        self._mutation_retry: dict[str, Any] | None = None
        self._judge_status: str | None = None
        self._orchestrator_report: dict[str, Any] | None = None
        self._retry_decision: dict[str, Any] | None = None
        self._retry_loop: dict[str, Any] | None = None
        self._workflow_switch: dict[str, Any] | None = None
        self._corrective_action: dict[str, Any] | None = None
        self._candidate_history: dict[str, Any] | None = None
        self._candidate_selection: dict[str, Any] | None = None
        self._executed_action: dict[str, Any] | None = None
        self._images: list[dict[str, Any]] = []
        self._metadata_path: str | None = None
        self._summary_path: str | None = None
    
    def with_status(self, status: str) -> "AgentResultBuilder":
        """Set the status field."""
        self._status = status
        return self
    
    def with_failed_stage(self, failed_stage: FailedStage) -> "AgentResultBuilder":
        """Set the failed_stage field."""
        self._failed_stage = failed_stage
        return self
    
    def with_error(
        self,
        error_type: str | None = None,
        error_code: ErrorCode | None = None,
        error: str | None = None,
    ) -> "AgentResultBuilder":
        """Set error-related fields."""
        self._error_type = error_type
        self._error_code = error_code
        self._error = error
        return self
    
    def with_user_prompt(self, user_prompt: str) -> "AgentResultBuilder":
        """Set the user_prompt field."""
        self._user_prompt = user_prompt
        return self
    
    def with_task_selection(self, task_selection: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the task_selection field."""
        self._task_selection = task_selection
        return self
    
    def with_execution_plan(self, execution_plan: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the execution_plan field."""
        self._execution_plan = execution_plan
        return self
    
    def with_mutation_report(self, mutation_report: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the mutation_report field."""
        self._mutation_report = mutation_report
        return self
    
    def with_mutation_retry(self, mutation_retry: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the mutation_retry field."""
        self._mutation_retry = mutation_retry
        return self
    
    def with_judge_status(self, judge_status: str | None) -> "AgentResultBuilder":
        """Set the judge_status field."""
        self._judge_status = judge_status
        return self
    
    def with_orchestrator_report(self, orchestrator_report: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the orchestrator_report field."""
        self._orchestrator_report = orchestrator_report
        return self
    
    def with_retry_decision(self, retry_decision: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the retry_decision field."""
        self._retry_decision = retry_decision
        return self
    
    def with_retry_loop(self, retry_loop: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the retry_loop field."""
        self._retry_loop = retry_loop
        return self
    
    def with_workflow_switch(self, workflow_switch: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the workflow_switch field."""
        self._workflow_switch = workflow_switch
        return self
    
    def with_corrective_action(self, corrective_action: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the corrective_action field."""
        self._corrective_action = corrective_action
        return self
    
    def with_candidate_history(self, candidate_history: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the candidate_history field."""
        self._candidate_history = candidate_history
        return self
    
    def with_candidate_selection(self, candidate_selection: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the candidate_selection field."""
        self._candidate_selection = candidate_selection
        return self
    
    def with_executed_action(self, executed_action: dict[str, Any] | None) -> "AgentResultBuilder":
        """Set the executed_action field."""
        self._executed_action = executed_action
        return self
    
    def with_images(self, images: list[dict[str, Any]]) -> "AgentResultBuilder":
        """Set the images field."""
        self._images = images
        return self
    
    def with_metadata_path(self, metadata_path: str | None) -> "AgentResultBuilder":
        """Set the metadata_path field."""
        self._metadata_path = metadata_path
        return self
    
    def with_summary_path(self, summary_path: str | None) -> "AgentResultBuilder":
        """Set the summary_path field."""
        self._summary_path = summary_path
        return self
    
    def build(self) -> AgentResult:
        """Build the AgentResult instance.
        
        Returns:
            AgentResult with all configured fields
        """
        return AgentResult(
            status=self._status,
            failed_stage=self._failed_stage,
            error_type=self._error_type,
            error_code=self._error_code,
            error=self._error,
            user_prompt=self._user_prompt,
            task_selection=self._task_selection,
            execution_plan=self._execution_plan,
            mutation_report=self._mutation_report,
            mutation_retry=self._mutation_retry,
            judge_status=self._judge_status,
            orchestrator_report=self._orchestrator_report,
            retry_decision=self._retry_decision,
            retry_loop=self._retry_loop,
            workflow_switch=self._workflow_switch,
            corrective_action=self._corrective_action,
            candidate_history=self._candidate_history,
            candidate_selection=self._candidate_selection,
            executed_action=self._executed_action,
            images=self._images,
            metadata_path=self._metadata_path,
            summary_path=self._summary_path,
        )


def build_agent_result(
    status: str = "completed",
    failed_stage: FailedStage | None = None,
    error_type: str | None = None,
    error_code: ErrorCode | None = None,
    error: str | None = None,
    user_prompt: str = "",
    task_selection: dict[str, Any] | None = None,
    execution_plan: dict[str, Any] | None = None,
    mutation_report: dict[str, Any] | None = None,
    mutation_retry: dict[str, Any] | None = None,
    judge_status: str | None = None,
    orchestrator_report: dict[str, Any] | None = None,
    retry_decision: dict[str, Any] | None = None,
    retry_loop: dict[str, Any] | None = None,
    workflow_switch: dict[str, Any] | None = None,
    corrective_action: dict[str, Any] | None = None,
    candidate_history: dict[str, Any] | None = None,
    candidate_selection: dict[str, Any] | None = None,
    executed_action: dict[str, Any] | None = None,
    images: list[dict[str, Any]] | None = None,
    metadata_path: str | None = None,
    summary_path: str | None = None,
    recipe_validation: dict[str, Any] | None = None,
    trace_path: str | None = None,
    tool_chain: list[str] | None = None,
    upscale_result: dict[str, Any] | None = None,
) -> AgentResult:
    """Convenience function to build an AgentResult.
    
    Args:
        status: Result status ("completed" or "failed")
        failed_stage: Stage where failure occurred (if any)
        error_type: Type of error (if any)
        error_code: Normalized error code (if any)
        error: Error message (if any)
        user_prompt: Original user prompt
        task_selection: Task selection result
        execution_plan: Execution plan
        mutation_report: Workflow mutation report
        mutation_retry: Mutation retry report
        judge_status: Judge pipeline status
        orchestrator_report: Judge orchestrator report
        retry_decision: Retry decision from judge
        retry_loop: Retry loop report
        workflow_switch: Workflow switch information
        corrective_action: Canonical corrective action decision
        candidate_history: Candidate history with attempt lineage
        candidate_selection: Candidate selection decision
        executed_action: Executed action result from CorrectiveActionExecutor
        images: Generated images
        metadata_path: Path to metadata file
        summary_path: Path to summary file
        
    Returns:
        AgentResult instance
    """
    return AgentResult(
        status=status,
        failed_stage=failed_stage,
        error_type=error_type,
        error_code=error_code,
        error=error,
        user_prompt=user_prompt,
        task_selection=task_selection,
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        mutation_retry=mutation_retry,
        judge_status=judge_status,
        orchestrator_report=orchestrator_report,
        retry_decision=retry_decision,
        retry_loop=retry_loop,
        workflow_switch=workflow_switch,
        corrective_action=corrective_action,
        candidate_history=candidate_history,
        candidate_selection=candidate_selection,
        executed_action=executed_action,
        images=images or [],
        metadata_path=metadata_path,
        summary_path=summary_path,
        recipe_validation=recipe_validation,
        trace_path=trace_path,
        tool_chain=tool_chain,
        upscale_result=upscale_result,
    )
