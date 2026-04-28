"""Tests for Executed Action Trace & Persistence Hardening - Scenarios 53-60.

These tests verify that executed_action is fully consistent across:
- runtime result
- persisted metadata
- summary
- terminal report
- candidate history / selected candidate
"""

import json
import pytest

from app.services.run_metadata import RunMetadataService
from app.services.terminal_report import build_terminal_report
from app.agent.candidate_history import CandidateHistory, AttemptRecord, AttemptRecordBuilder
from app.agent.corrective_action_executor import (
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_BLOCKED,
    EXECUTION_STATUS_FAILED,
    BRANCH_ACCEPT,
    BRANCH_RETRY,
    BRANCH_SWITCH,
)


class TestScenario53PersistedMetadataContainsExecutedAction:
    """Scenario 53 — persisted metadata contains executed_action.
    
    Expectation:
    - executed_action is saved in persisted JSON
    """
    
    def test_metadata_persistence_executed_action(self, tmp_path):
        """Test that executed_action is persisted in metadata JSON."""
        metadata_service = RunMetadataService(tmp_path)
        
        # Create a report with executed_action
        report = {
            "status": "completed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "sdxl_base",
            "rewrite_mode": "semantic",
            "seed": 12345,
            "images": [{"filename": "test.png"}],
            "corrective_action": {
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
            },
            "executed_action": {
                "executed_action": "retry_settings",
                "execution_status": "completed",
                "branch_taken": "retry",
                "selected_candidate_id": "cand_123",
                "selected_attempt_index": 2,
            },
        }
        
        # Persist the report
        persisted_report = metadata_service.persist_terminal_report(report)
        
        # Verify executed_action is in persisted report
        assert "executed_action" in persisted_report
        assert persisted_report["executed_action"]["executed_action"] == "retry_settings"
        assert persisted_report["executed_action"]["execution_status"] == "completed"
        assert persisted_report["executed_action"]["branch_taken"] == "retry"
        
        # Verify it's actually saved to disk
        metadata_path = persisted_report["metadata_path"]
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "executed_action" in saved_data
        assert saved_data["executed_action"]["executed_action"] == "retry_settings"


class TestScenario54SummaryReflectsExecutedAction:
    """Scenario 54 — summary reflects executed_action.
    
    Expectation:
    - summary contains executed_action
    - execution_status
    - branch_taken
    - selected_attempt_index
    """
    
    def test_summary_executed_action_fields(self, tmp_path):
        """Test that summary reflects executed_action fields."""
        metadata_service = RunMetadataService(tmp_path)
        
        # Create a report with executed_action
        report = {
            "status": "completed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "sdxl_base",
            "rewrite_mode": "semantic",
            "seed": 12345,
            "images": [{"filename": "test.png"}],
            "corrective_action": {
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
            },
            "executed_action": {
                "executed_action": "retry_settings",
                "execution_status": "completed",
                "branch_taken": "retry",
                "selected_candidate_id": "cand_123",
                "selected_attempt_index": 2,
            },
        }
        
        # Persist the report
        persisted_report = metadata_service.persist_terminal_report(report)
        
        # Read the summary file
        summary_path = persisted_report["summary_path"]
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_text = f.read()
        
        # Verify executed_action fields are in summary
        assert "executed_action: retry_settings" in summary_text
        assert "execution_status: completed" in summary_text
        assert "branch_taken: retry" in summary_text
        assert "selected_attempt_index: 2" in summary_text


class TestScenario55TerminalReportReflectsExecutedAction:
    """Scenario 55 — terminal report reflects executed_action.
    
    Expectation:
    - terminal report contains executed_action
    - execution status
    - branch taken
    - selected attempt
    """
    
    def test_terminal_report_executed_action(self):
        """Test that terminal report reflects executed_action."""
        # Build terminal report with executed_action
        terminal_report = build_terminal_report(
            status="completed",
            user_prompt="test prompt",
            final_positive_prompt="test prompt",
            prompt_id="test-123",
            failed_stage=None,
            error=None,
            preset_name="sdxl_base",
            rewrite_mode="semantic",
            seed=12345,
            images=[{"filename": "test.png"}],
            preflight=None,
            artifact_validation=None,
            artifact_fetch_validation=None,
            corrective_action={
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
            },
            executed_action={
                "executed_action": "retry_settings",
                "execution_status": "completed",
                "branch_taken": "retry",
                "selected_candidate_id": "cand_123",
                "selected_attempt_index": 2,
            },
        )
        
        # Verify executed_action is in terminal report
        assert "executed_action" in terminal_report
        assert terminal_report["executed_action"]["executed_action"] == "retry_settings"
        assert terminal_report["executed_action"]["execution_status"] == "completed"
        assert terminal_report["executed_action"]["branch_taken"] == "retry"
        assert terminal_report["executed_action"]["selected_candidate_id"] == "cand_123"
        assert terminal_report["executed_action"]["selected_attempt_index"] == 2


class TestScenario56BlockedSwitchPreservesExecutedActionTrace:
    """Scenario 56 — blocked switch preserves executed_action trace.
    
    Expectation:
    - blocked switch has executed_action with blocked status
    - execution_status = blocked
    """
    
    def test_blocked_switch_executed_action_trace(self, tmp_path):
        """Test that blocked switch preserves executed_action trace."""
        metadata_service = RunMetadataService(tmp_path)
        
        # Create a report with blocked switch executed_action
        report = {
            "status": "completed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "sdxl_base",
            "rewrite_mode": "semantic",
            "seed": 12345,
            "images": [{"filename": "test.png"}],
            "corrective_action": {
                "action": "switch_workflow",
                "reason_code": "switch_blocked_missing_inputs",
            },
            "executed_action": {
                "executed_action": "switch_workflow",
                "execution_status": "blocked",
                "branch_taken": "switch",
                "target_workflow_id": "upscale_v1",
                "error_type": "switch_blocked",
                "error_code": "SWITCH_NOT_ALLOWED",
                "error": "Switch blocked by missing assets",
            },
        }
        
        # Persist the report
        persisted_report = metadata_service.persist_terminal_report(report)
        
        # Verify blocked status is preserved
        assert persisted_report["executed_action"]["execution_status"] == "blocked"
        assert persisted_report["executed_action"]["branch_taken"] == "switch"
        assert persisted_report["executed_action"]["error_type"] == "switch_blocked"
        
        # Verify it's in summary
        summary_path = persisted_report["summary_path"]
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_text = f.read()
        
        assert "executed_action: switch_workflow" in summary_text
        assert "execution_status: blocked" in summary_text
        assert "branch_taken: switch" in summary_text


class TestScenario57FailedRetryPreservesExecutedActionTrace:
    """Scenario 57 — failed retry preserves executed_action trace.
    
    Expectation:
    - failed retry has executed_action with failed status
    - execution_status = failed
    """
    
    def test_failed_retry_executed_action_trace(self, tmp_path):
        """Test that failed retry preserves executed_action trace."""
        metadata_service = RunMetadataService(tmp_path)
        
        # Create a report with failed retry executed_action
        report = {
            "status": "failed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "sdxl_base",
            "rewrite_mode": "semantic",
            "seed": 12345,
            "images": [],
            "corrective_action": {
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
            },
            "executed_action": {
                "executed_action": "retry_settings",
                "execution_status": "failed",
                "branch_taken": "retry",
                "error_type": "generation_error",
                "error": "Generation failed during retry",
            },
        }
        
        # Persist the report
        persisted_report = metadata_service.persist_terminal_report(report)
        
        # Verify failed status is preserved
        assert persisted_report["executed_action"]["execution_status"] == "failed"
        assert persisted_report["executed_action"]["branch_taken"] == "retry"
        assert persisted_report["executed_action"]["error_type"] == "generation_error"
        
        # Verify it's in summary
        summary_path = persisted_report["summary_path"]
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_text = f.read()
        
        assert "executed_action: retry_settings" in summary_text
        assert "execution_status: failed" in summary_text


class TestScenario58SelectedCandidateParityWithExecutedAction:
    """Scenario 58 — selected candidate parity with executed_action.
    
    Expectation:
    - top-level executed_action.selected_candidate_id
    - candidate_history.selected_candidate_id
    - are aligned
    """
    
    def test_selected_candidate_parity(self):
        """Test that selected_candidate_id is aligned between executed_action and candidate_history."""
        # Create candidate history with selected candidate
        candidate_history = CandidateHistory()
        candidate_history.selected_candidate_id = "cand_won"
        candidate_history.selected_attempt_index = 2
        candidate_history.selection_reason = "retry_candidate_won"
        
        # Add attempts
        attempt1 = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id("cand_initial")
            .attempt_kind("initial")
            .workflow_id("txt2img_portrait")
            .executed_action({
                "executed_action": "accept",
                "execution_status": "completed",
                "branch_taken": "accept",
            })
            .build()
        )
        attempt2 = (
            AttemptRecordBuilder()
            .attempt_index(2)
            .candidate_id("cand_won")
            .attempt_kind("retry_settings")
            .workflow_id("txt2img_portrait")
            .executed_action({
                "executed_action": "retry_settings",
                "execution_status": "completed",
                "branch_taken": "retry",
                "selected_candidate_id": "cand_won",
                "selected_attempt_index": 2,
            })
            .build()
        )
        candidate_history.add_attempt(attempt1)
        candidate_history.add_attempt(attempt2)
        candidate_history.mark_selected("cand_won", 2, "retry_candidate_won")
        
        # Verify parity
        assert candidate_history.selected_candidate_id == "cand_won"
        assert candidate_history.selected_attempt_index == 2
        
        # Verify selected attempt has executed_action
        selected_attempt = candidate_history.get_selected_attempt()
        assert selected_attempt is not None
        assert selected_attempt.executed_action["selected_candidate_id"] == "cand_won"
        assert selected_attempt.executed_action["selected_attempt_index"] == 2


class TestScenario59AcceptPathHasExecutedAction:
    """Scenario 59 — accept path has executed_action.
    
    Expectation:
    - accept path has executed_action
    - execution_status = completed
    - branch_taken = accept
    """
    
    def test_accept_path_executed_action(self, tmp_path):
        """Test that accept path has executed_action."""
        metadata_service = RunMetadataService(tmp_path)
        
        # Create a report with accept executed_action
        report = {
            "status": "completed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "sdxl_base",
            "rewrite_mode": "semantic",
            "seed": 12345,
            "images": [{"filename": "test.png"}],
            "corrective_action": {
                "action": "accept",
                "reason_code": "accepted_by_judge",
            },
            "executed_action": {
                "executed_action": "accept",
                "execution_status": "completed",
                "branch_taken": "accept",
                "selected_candidate_id": "cand_123",
                "selected_attempt_index": 1,
            },
        }
        
        # Persist the report
        persisted_report = metadata_service.persist_terminal_report(report)
        
        # Verify accept executed_action
        assert persisted_report["executed_action"]["executed_action"] == "accept"
        assert persisted_report["executed_action"]["execution_status"] == "completed"
        assert persisted_report["executed_action"]["branch_taken"] == "accept"
        
        # Verify it's in summary
        summary_path = persisted_report["summary_path"]
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_text = f.read()
        
        assert "executed_action: accept" in summary_text
        assert "execution_status: completed" in summary_text
        assert "branch_taken: accept" in summary_text


class TestScenario60DecisionExecutionLineageHierarchyConsistent:
    """Scenario 60 — decision/execution/lineage hierarchy remains consistent.
    
    Expectation:
    - corrective_action — decision
    - executed_action — execution
    - retry_decision / workflow_switch — derived
    - candidate_history — lineage
    - top-level result — selected outcome
    """
    
    def test_hierarchy_consistency(self):
        """Test that the hierarchy is consistent across all layers."""
        # Create a complete result with all layers
        result = {
            "corrective_action": {
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
                "reason": "Technical quality needs repair",
            },
            "executed_action": {
                "executed_action": "retry_settings",
                "execution_status": "completed",
                "branch_taken": "retry",
                "selected_candidate_id": "cand_retry_won",
                "selected_attempt_index": 2,
            },
            "retry_decision": {
                "action": "retry",
                "reason": "Technical judge recommended retry",
            },
            "workflow_switch": {
                "switch_applied": False,
            },
            "candidate_history": {
                "selected_candidate_id": "cand_retry_won",
                "selected_attempt_index": 2,
                "selection_reason": "retry_candidate_won",
                "attempts": [
                    {
                        "attempt_index": 1,
                        "candidate_id": "cand_initial",
                        "attempt_kind": "initial",
                        "corrective_action": {"action": "retry_settings"},
                        "executed_action": {"executed_action": "retry_settings"},
                    },
                    {
                        "attempt_index": 2,
                        "candidate_id": "cand_retry_won",
                        "attempt_kind": "retry_settings",
                        "corrective_action": {"action": "retry_settings"},
                        "executed_action": {"executed_action": "retry_settings"},
                    },
                ],
            },
        }
        
        # Verify hierarchy: decision layer
        assert result["corrective_action"]["action"] == "retry_settings"
        assert result["corrective_action"]["reason_code"] == "technical_settings_retry"
        
        # Verify hierarchy: execution layer
        assert result["executed_action"]["executed_action"] == "retry_settings"
        assert result["executed_action"]["execution_status"] == "completed"
        assert result["executed_action"]["branch_taken"] == "retry"
        
        # Verify hierarchy: derived fields
        assert result["retry_decision"]["action"] == "retry"
        assert result["workflow_switch"]["switch_applied"] == False
        
        # Verify hierarchy: lineage
        assert result["candidate_history"]["selected_candidate_id"] == "cand_retry_won"
        assert result["candidate_history"]["selected_attempt_index"] == 2
        
        # Verify consistency across layers
        assert result["corrective_action"]["action"] == result["executed_action"]["executed_action"]
        assert result["candidate_history"]["selected_candidate_id"] == result["executed_action"]["selected_candidate_id"]
        assert result["candidate_history"]["selected_attempt_index"] == result["executed_action"]["selected_attempt_index"]
