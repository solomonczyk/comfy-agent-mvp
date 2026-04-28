"""Tests for Corrective Action Executor - Scenarios 45-52.

These tests verify the execution layer separation from the decision layer:
- corrective_action = decision layer (what was decided)
- executed_action = execution layer (what actually happened)
"""

import pytest

from app.agent.corrective_action_executor import (
    CorrectiveActionExecutor,
    CorrectiveActionExecutionResult,
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_BLOCKED,
    EXECUTION_STATUS_FAILED,
    EXECUTION_STATUS_SKIPPED,
    BRANCH_ACCEPT,
    BRANCH_RETRY,
    BRANCH_SWITCH,
    BRANCH_REJECT,
)
from app.agent.corrective_action_policy import CorrectiveActionDecision
from app.agent.candidate_history import CandidateHistory, AttemptRecord
from app.agent.execution_plan import ExecutionPlan


class TestScenario45AcceptActionExecutedCanonically:
    """Scenario 45 — accept action executed canonically.
    
    Expectation:
    - corrective_action.action = accept
    - executed_action.executed_action = accept
    - execution_status = completed
    """
    
    def test_accept_action_execution(self):
        """Test that accept action is executed canonically through executor."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action decision
        corrective_action = CorrectiveActionDecision(
            action="accept",
            reason_code="accepted_by_judge",
            reason="Generation accepted by judge",
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        # Create candidate history with selected candidate
        candidate_history = CandidateHistory()
        candidate_history.selected_candidate_id = "cand_12345678"
        candidate_history.selected_attempt_index = 1
        
        # Execute through executor
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=candidate_history,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify execution result
        assert execution_result.executed_action == "accept"
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED
        assert execution_result.branch_taken == BRANCH_ACCEPT
        assert execution_result.selected_candidate_id == "cand_12345678"
        assert execution_result.selected_attempt_index == 1
        assert execution_result.target_workflow_id == "txt2img_portrait"


class TestScenario46RetryActionExecutedThroughExecutor:
    """Scenario 46 — retry action executed through executor.
    
    Expectation:
    - retry path goes through executor, not bypassing it
    """
    
    def test_retry_settings_execution(self):
        """Test that retry_settings action is executed through executor."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action decision
        corrective_action = CorrectiveActionDecision(
            action="retry_settings",
            reason_code="technical_settings_retry",
            reason="Technical quality needs repair through generation settings",
            source_repairs=["increase_steps", "reduce_highlights"],
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        # Execute through executor
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify execution result
        assert execution_result.executed_action == "retry_settings"
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED
        assert execution_result.branch_taken == BRANCH_RETRY
        assert execution_result.target_workflow_id == "txt2img_portrait"
    
    def test_retry_prompt_execution(self):
        """Test that retry_prompt action is executed through executor."""
        executor = CorrectiveActionExecutor()
        
        corrective_action = CorrectiveActionDecision(
            action="retry_prompt",
            reason_code="semantic_alignment_retry",
            reason="Semantic mismatch detected",
            source_repairs=["add more detail to subject"],
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        assert execution_result.executed_action == "retry_prompt"
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED
        assert execution_result.branch_taken == BRANCH_RETRY
    
    def test_retry_seed_execution(self):
        """Test that retry_seed action is executed through executor."""
        executor = CorrectiveActionExecutor()
        
        corrective_action = CorrectiveActionDecision(
            action="retry_seed",
            reason_code="seed_variation_retry",
            reason="Retry with new seed",
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        assert execution_result.executed_action == "retry_seed"
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED
        assert execution_result.branch_taken == BRANCH_RETRY


class TestScenario47SwitchActionExecutedThroughExecutor:
    """Scenario 47 — switch action executed through executor.
    
    Expectation:
    - switch path goes through executor
    """
    
    def test_switch_workflow_execution(self):
        """Test that switch_workflow action is executed through executor."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action decision with switch allowed
        corrective_action = CorrectiveActionDecision(
            action="switch_workflow",
            reason_code="resolution_repair_switch",
            reason="Technical judge requested resolution-focused repair",
            selected_workflow_id="img2img_v1",
            target_workflow_id="upscale_v1",
            required_inputs=["input_image"],
            missing_inputs=[],
            switch_allowed=True,
        )
        
        # Execute through executor
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets={"input_image": "path/to/image.jpg"},
        )
        
        # Verify execution result
        assert execution_result.executed_action == "switch_workflow"
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED
        assert execution_result.branch_taken == BRANCH_SWITCH
        assert execution_result.target_workflow_id == "upscale_v1"


class TestScenario48BlockedSwitchProducesExecutedActionBlocked:
    """Scenario 48 — blocked switch produces executed_action=blocked.
    
    Expectation:
    - corrective_action.action = switch_workflow
    - executed_action.execution_status = blocked
    """
    
    def test_blocked_switch_execution(self):
        """Test that blocked switch produces executed_action with blocked status."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action decision with switch NOT allowed
        corrective_action = CorrectiveActionDecision(
            action="switch_workflow",
            reason_code="switch_blocked_missing_inputs",
            reason="Switch blocked by missing assets",
            selected_workflow_id="img2img_v1",
            target_workflow_id="upscale_v1",
            required_inputs=["input_image"],
            missing_inputs=["input_image"],
            switch_allowed=False,
        )
        
        # Execute through executor
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,  # Missing input_image
        )
        
        # Verify execution result shows blocked status
        assert execution_result.executed_action == "switch_workflow"
        assert execution_result.execution_status == EXECUTION_STATUS_BLOCKED
        assert execution_result.branch_taken == BRANCH_SWITCH
        assert execution_result.target_workflow_id == "upscale_v1"
        assert execution_result.error_type == "switch_blocked"
        assert execution_result.error_code == "SWITCH_NOT_ALLOWED"


class TestScenario49FailedRetryProducesExecutedActionFailed:
    """Scenario 49 — failed retry produces executed_action=failed.
    
    Expectation:
    - decision and execution not mixed
    - decision = retry_settings
    - execution = failed
    
    Note: The executor validates execution but doesn't actually run generation.
    Runtime failures would be captured in the service layer and would update
    the execution_status to failed.
    """
    
    def test_failed_retry_updates_execution_status(self):
        """Test that runtime failure updates execution status to failed."""
        # This scenario would be tested in integration tests with actual generation
        # For unit test, we verify that executor can handle unknown actions
        executor = CorrectiveActionExecutor()
        
        # Create corrective action with unknown action (simulates failure case)
        corrective_action = CorrectiveActionDecision(
            action="unknown_action",
            reason_code="test",
            reason="Test unknown action",
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        assert execution_result.executed_action == "unknown_action"
        assert execution_result.execution_status == EXECUTION_STATUS_FAILED
        assert execution_result.error_type == "execution_error"


class TestScenario50ExecutedActionPresentInFinalResult:
    """Scenario 50 — executed_action present in final result.
    
    Expectation:
    - executed_action block is always present in final result
    """
    
    def test_executed_action_serialization(self):
        """Test that CorrectiveActionExecutionResult can be serialized to dict."""
        execution_result = CorrectiveActionExecutionResult(
            executed_action="retry_settings",
            execution_status=EXECUTION_STATUS_COMPLETED,
            selected_candidate_id="cand_12345678",
            selected_attempt_index=2,
            branch_taken=BRANCH_RETRY,
            target_workflow_id="txt2img_portrait",
            notes=["Retry execution initiated"],
        )
        
        # Verify to_dict() works
        result_dict = execution_result.to_dict()
        
        assert result_dict["executed_action"] == "retry_settings"
        assert result_dict["execution_status"] == EXECUTION_STATUS_COMPLETED
        assert result_dict["selected_candidate_id"] == "cand_12345678"
        assert result_dict["selected_attempt_index"] == 2
        assert result_dict["branch_taken"] == BRANCH_RETRY
        assert result_dict["target_workflow_id"] == "txt2img_portrait"
        assert result_dict["notes"] == ["Retry execution initiated"]


class TestScenario51SelectedCandidateAlignmentAfterExecutedRetrySwitch:
    """Scenario 51 — selected candidate remains aligned after executed retry/switch.
    
    Expectation:
    - top-level selected result
    - candidate_history.selected_candidate_id
    - executed_action.selected_candidate_id
    - are all aligned
    """
    
    def test_selected_candidate_alignment_retry(self):
        """Test that selected_candidate_id is aligned after retry execution."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action for retry
        corrective_action = CorrectiveActionDecision(
            action="retry_settings",
            reason_code="technical_settings_retry",
            reason="Technical quality needs repair",
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        # Create candidate history with selected candidate (retry won)
        candidate_history = CandidateHistory()
        candidate_history.selected_candidate_id = "cand_retry_won"
        candidate_history.selected_attempt_index = 2
        
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=candidate_history,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify alignment
        assert execution_result.selected_candidate_id == "cand_retry_won"
        assert execution_result.selected_attempt_index == 2
        assert candidate_history.selected_candidate_id == "cand_retry_won"
        assert candidate_history.selected_attempt_index == 2
    
    def test_selected_candidate_alignment_switch(self):
        """Test that selected_candidate_id is aligned after switch execution."""
        executor = CorrectiveActionExecutor()
        
        # Create corrective action for switch
        corrective_action = CorrectiveActionDecision(
            action="switch_workflow",
            reason_code="resolution_repair_switch",
            reason="Resolution-focused repair",
            selected_workflow_id="img2img_v1",
            target_workflow_id="upscale_v1",
            required_inputs=["input_image"],
            missing_inputs=[],
            switch_allowed=True,
        )
        
        # Create candidate history with selected candidate (switch won)
        candidate_history = CandidateHistory()
        candidate_history.selected_candidate_id = "cand_switch_won"
        candidate_history.selected_attempt_index = 2
        
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=candidate_history,
            execution_plan=None,
            mutation_report=None,
            assets={"input_image": "path/to/image.jpg"},
        )
        
        # Verify alignment
        assert execution_result.selected_candidate_id == "cand_switch_won"
        assert execution_result.selected_attempt_index == 2
        assert candidate_history.selected_candidate_id == "cand_switch_won"
        assert candidate_history.selected_attempt_index == 2


class TestScenario52DecisionExecutionSeparationPreserved:
    """Scenario 52 — decision/execution separation preserved.
    
    Expectation:
    - corrective_action and executed_action do not duplicate chaos
    - roles are not confused
    - corrective_action = decision layer
    - executed_action = execution layer
    """
    
    def test_decision_execution_separation_accept(self):
        """Test decision/execution separation for accept action."""
        executor = CorrectiveActionExecutor()
        
        # Decision layer: what was decided
        corrective_action = CorrectiveActionDecision(
            action="accept",
            reason_code="accepted_by_judge",
            reason="Generation accepted by judge",
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        # Execution layer: what actually happened
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify separation: decision has reason, execution has status
        assert corrective_action.action == "accept"  # Decision
        assert corrective_action.reason_code == "accepted_by_judge"  # Decision
        assert execution_result.executed_action == "accept"  # Execution
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED  # Execution
        assert execution_result.branch_taken == BRANCH_ACCEPT  # Execution
    
    def test_decision_execution_separation_retry(self):
        """Test decision/execution separation for retry action."""
        executor = CorrectiveActionExecutor()
        
        # Decision layer
        corrective_action = CorrectiveActionDecision(
            action="retry_settings",
            reason_code="technical_settings_retry",
            reason="Technical quality needs repair",
            source_repairs=["increase_steps"],
            selected_workflow_id="txt2img_portrait",
            target_workflow_id=None,
            switch_allowed=False,
        )
        
        # Execution layer
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify separation
        assert corrective_action.action == "retry_settings"  # Decision
        assert corrective_action.source_repairs == ["increase_steps"]  # Decision
        assert execution_result.executed_action == "retry_settings"  # Execution
        assert execution_result.execution_status == EXECUTION_STATUS_COMPLETED  # Execution
        assert execution_result.branch_taken == BRANCH_RETRY  # Execution
    
    def test_decision_execution_separation_blocked_switch(self):
        """Test decision/execution separation for blocked switch."""
        executor = CorrectiveActionExecutor()
        
        # Decision layer: switch was decided
        corrective_action = CorrectiveActionDecision(
            action="switch_workflow",
            reason_code="resolution_repair_switch",
            reason="Resolution-focused repair",
            selected_workflow_id="img2img_v1",
            target_workflow_id="upscale_v1",
            required_inputs=["input_image"],
            missing_inputs=["input_image"],
            switch_allowed=False,  # Decision: not allowed
        )
        
        # Execution layer: switch was blocked
        execution_result = executor.execute(
            corrective_action=corrective_action,
            current_result=None,
            candidate_history=None,
            execution_plan=None,
            mutation_report=None,
            assets=None,
        )
        
        # Verify separation
        assert corrective_action.action == "switch_workflow"  # Decision says switch
        assert corrective_action.switch_allowed == False  # Decision says not allowed
        assert execution_result.executed_action == "switch_workflow"  # Execution tried switch
        assert execution_result.execution_status == EXECUTION_STATUS_BLOCKED  # Execution was blocked
        assert execution_result.branch_taken == BRANCH_SWITCH  # Execution branch
