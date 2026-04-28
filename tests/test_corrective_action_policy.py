"""Tests for CorrectiveActionPolicy.

This module tests the canonical decision layer for corrective actions.
"""

import pytest

from app.agent.corrective_action_policy import (
    CorrectiveActionDecision,
    CorrectiveActionPolicy,
    REASON_CODE_ACCEPTED_BY_JUDGE,
    REASON_CODE_SEMANTIC_ALIGNMENT_RETRY,
    REASON_CODE_TECHNICAL_SETTINGS_RETRY,
    REASON_CODE_SEED_VARIATION_RETRY,
    REASON_CODE_RESOLUTION_REPAIR_SWITCH,
    REASON_CODE_FACE_REPAIR_SWITCH,
    REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS,
    REASON_CODE_REJECT_AFTER_JUDGE,
    REASON_CODE_NO_SAFE_CORRECTIVE_ACTION,
)
from app.agent.execution_plan import ExecutionPlan
from app.agent.task_selector import TaskSelectionResult


class TestCorrectiveActionDecision:
    """Tests for CorrectiveActionDecision dataclass."""
    
    def test_to_dict(self):
        """Test that CorrectiveActionDecision converts to dict correctly."""
        decision = CorrectiveActionDecision(
            action="accept",
            reason_code=REASON_CODE_ACCEPTED_BY_JUDGE,
            reason="Generation accepted",
            source_repairs=["repair1"],
            selected_workflow_id="img2img_v1",
            target_workflow_id=None,
            required_inputs=[],
            missing_inputs=[],
            switch_allowed=False,
            notes=["note1"],
        )
        
        result = decision.to_dict()
        
        assert result["action"] == "accept"
        assert result["reason_code"] == REASON_CODE_ACCEPTED_BY_JUDGE
        assert result["reason"] == "Generation accepted"
        assert result["source_repairs"] == ["repair1"]
        assert result["selected_workflow_id"] == "img2img_v1"
        assert result["target_workflow_id"] is None
        assert result["required_inputs"] == []
        assert result["missing_inputs"] == []
        assert result["switch_allowed"] is False
        assert result["notes"] == ["note1"]


class TestCorrectiveActionPolicy:
    """Tests for CorrectiveActionPolicy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.policy = CorrectiveActionPolicy()
    
    def test_scenario_29_pass_to_accept(self):
        """Scenario 29: pass -> accept."""
        orchestrator_report = {
            "final_verdict": "pass",
            "best_next_action": None,
            "global_repairs": [],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        assert decision.action == "accept"
        assert decision.reason_code == REASON_CODE_ACCEPTED_BY_JUDGE
        assert decision.switch_allowed is False
    
    def test_scenario_30_semantic_mismatch_to_retry_prompt(self):
        """Scenario 30: semantic mismatch -> retry_prompt."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["prompt needs adjustment", "wrong subject"],
            "semantic": {
                "final_verdict": "fail",
                "recommended_repairs": ["fix subject alignment"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        assert decision.action == "retry_prompt"
        assert decision.reason_code == REASON_CODE_SEMANTIC_ALIGNMENT_RETRY
    
    def test_scenario_31_technical_settings_to_retry_settings(self):
        """Scenario 31: technical settings issue -> retry_settings."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["increase_steps_or_change_seed", "reduce_highlights_or_cfg"],
            "technical": {
                "final_verdict": "fail",
                "recommended_repairs": ["fix_output_resolution"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        assert decision.action == "retry_settings"
        assert decision.reason_code == REASON_CODE_TECHNICAL_SETTINGS_RETRY
    
    def test_scenario_32_img2img_resolution_to_switch_upscale(self):
        """Scenario 32: img2img resolution repair -> switch_workflow upscale."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["increase resolution", "sharper details"],
            "technical": {
                "final_verdict": "fail",
                "recommended_repairs": ["low resolution", "blurry"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        assets = {"input_image": "/path/to/image.jpg"}
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=assets,
        )
        
        assert decision.action == "switch_workflow"
        assert decision.reason_code == REASON_CODE_RESOLUTION_REPAIR_SWITCH
        assert decision.target_workflow_id == "upscale_v1"
        assert decision.switch_allowed is True
    
    def test_scenario_33_img2img_face_to_switch_inpaint_face(self):
        """Scenario 33: img2img face repair -> switch_workflow inpaint_face."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["fix face artifacts", "cleanup skin"],
            "technical": {
                "final_verdict": "fail",
                "recommended_repairs": ["eye artifacts", "portrait cleanup"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        assets = {"input_image": "/path/to/image.jpg", "mask_image": "/path/to/mask.jpg"}
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=assets,
        )
        
        assert decision.action == "switch_workflow"
        assert decision.reason_code == REASON_CODE_FACE_REPAIR_SWITCH
        assert decision.target_workflow_id == "inpaint_face_v1"
        assert decision.switch_allowed is True
    
    def test_scenario_34_switch_blocked_missing_assets(self):
        """Scenario 34: switch blocked by missing assets -> deterministic fallback."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["increase resolution", "sharper details"],
            "technical": {
                "final_verdict": "fail",
                "recommended_repairs": ["low resolution", "blurry"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        assets = None  # Missing assets
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=assets,
        )
        
        # Deterministic fallback to retry_settings
        assert decision.action == "retry_settings"
        assert decision.reason_code == REASON_CODE_SWITCH_BLOCKED_MISSING_INPUTS
        assert decision.switch_allowed is False
        assert decision.missing_inputs == ["input_image"]
    
    def test_scenario_35_retry_and_switch_same_source(self):
        """Scenario 35: retry and switch paths use same source of truth."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["increase resolution"],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        assets = {"input_image": "/path/to/image.jpg"}
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=assets,
        )
        
        # Both retry and switch should come from the same decision
        assert decision.action in ["switch_workflow", "retry_settings"]
        assert decision.source_repairs == ["increase resolution"]
    
    def test_scenario_36_corrective_action_in_result(self):
        """Scenario 36: final result contains corrective_action block."""
        orchestrator_report = {
            "final_verdict": "pass",
            "best_next_action": None,
            "global_repairs": [],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        # Verify decision can be converted to dict for result
        decision_dict = decision.to_dict()
        assert "action" in decision_dict
        assert "reason_code" in decision_dict
        assert "reason" in decision_dict
        assert "source_repairs" in decision_dict
        assert "selected_workflow_id" in decision_dict
        assert "target_workflow_id" in decision_dict
        assert "required_inputs" in decision_dict
        assert "missing_inputs" in decision_dict
        assert "switch_allowed" in decision_dict
        assert "notes" in decision_dict
    
    def test_scenario_37_corrective_action_matches_executed_branch(self):
        """Scenario 37: corrective_action matches executed branch."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": "retry_seed",
            "global_repairs": ["try different composition"],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        # Decision should match what was requested
        assert decision.action == "retry_seed"
        assert decision.reason_code == REASON_CODE_SEED_VARIATION_RETRY
    
    def test_scenario_38_no_action_drift(self):
        """Scenario 38: no action drift between layers."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["fix output resolution"],
            "technical": {
                "final_verdict": "fail",
                "recommended_repairs": ["fix_output_resolution"],
            },
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        # Decision should be deterministic based on orchestrator report
        assert decision.action == "retry_settings"
        assert decision.reason_code == REASON_CODE_TECHNICAL_SETTINGS_RETRY
        # No drift - decision is based solely on orchestrator report content
    
    def test_reject_after_judge(self):
        """Test reject after judge when no safe corrective action identified."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": None,
            "global_repairs": ["unfixable issue"],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        assert decision.action == "reject"
        assert decision.reason_code == REASON_CODE_REJECT_AFTER_JUDGE
    
    def test_seed_variation_retry(self):
        """Test seed variation retry detection."""
        orchestrator_report = {
            "final_verdict": "fail",
            "best_next_action": "retry_seed",
            "global_repairs": ["try another variation"],
        }
        execution_plan = ExecutionPlan(
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            task_type="img2img",
            user_prompt="test prompt",
            preset_name="default",
            rewrite_mode="rewrite",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test"},
            enable_judging=True,
            enable_retry_loop=False,
        )
        
        decision = self.policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report={},
            orchestrator_report=orchestrator_report,
            assets=None,
        )
        
        assert decision.action == "retry_seed"
        assert decision.reason_code == REASON_CODE_SEED_VARIATION_RETRY


class TestCorrectiveActionTraceAndPersistence:
    """Tests for corrective action trace and persistence (Scenarios 39-44)."""
    
    def test_scenario_39_persisted_metadata_contains_corrective_action(self):
        """Scenario 39: persisted metadata contains corrective_action."""
        from app.services.run_metadata import RunMetadataService
        import tempfile
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            
            report = {
                "status": "completed",
                "prompt_id": "test-123",
                "user_prompt": "test prompt",
                "final_positive_prompt": "test prompt",
                "preset_name": "default",
                "rewrite_mode": "rewrite",
                "seed": 12345,
                "images": [{"filename": "test.png"}],
                "judge_status": "pass",
                "corrective_action": {
                    "action": "accept",
                    "reason_code": "accepted_by_judge",
                    "reason": "Generation accepted by judge",
                    "source_repairs": [],
                    "selected_workflow_id": "img2img_v1",
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": [],
                },
            }
            
            persisted = metadata_service.persist_terminal_report(report)
            
            # Verify corrective_action is in persisted metadata
            assert "corrective_action" in persisted
            assert persisted["corrective_action"]["action"] == "accept"
            assert persisted["corrective_action"]["reason_code"] == "accepted_by_judge"
    
    def test_scenario_40_summary_reflects_corrective_action(self):
        """Scenario 40: summary reflects corrective_action."""
        from app.services.run_metadata import RunMetadataService
        
        report = {
            "status": "completed",
            "prompt_id": "test-123",
            "user_prompt": "test prompt",
            "final_positive_prompt": "test prompt",
            "preset_name": "default",
            "rewrite_mode": "rewrite",
            "seed": 12345,
            "images": [{"filename": "test.png"}],
            "corrective_action": {
                "action": "switch_workflow",
                "reason_code": "resolution_repair_switch",
                "reason": "Technical judge requested resolution-focused repair",
                "source_repairs": ["increase resolution"],
                "selected_workflow_id": "img2img_v1",
                "target_workflow_id": "upscale_v1",
                "required_inputs": ["input_image"],
                "missing_inputs": [],
                "switch_allowed": True,
                "notes": [],
            },
        }
        
        summary_text = RunMetadataService._build_summary_text(report)
        
        # Verify summary includes corrective_action fields
        assert "corrective_action:" in summary_text
        assert "corrective_action_reason_code:" in summary_text
        assert "target_workflow_id:" in summary_text
        assert "switch_workflow" in summary_text
        assert "upscale_v1" in summary_text
    
    def test_scenario_41_candidate_history_stores_corrective_action_per_attempt(self):
        """Scenario 41: candidate_history stores corrective_action per attempt."""
        from app.agent.candidate_history import AttemptRecordBuilder, generate_candidate_id
        
        # Create attempt record with corrective_action
        attempt_record = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(generate_candidate_id())
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .corrective_action({
                "action": "accept",
                "reason_code": "accepted_by_judge",
                "reason": "Generation accepted",
            })
            .build()
        )
        
        # Verify corrective_action is stored
        assert attempt_record.corrective_action is not None
        assert attempt_record.corrective_action["action"] == "accept"
        
        # Verify it's included in to_dict
        attempt_dict = attempt_record.to_dict()
        assert "corrective_action" in attempt_dict
        assert attempt_dict["corrective_action"]["action"] == "accept"
    
    def test_scenario_42_top_level_corrective_action_matches_selected_candidate(self):
        """Scenario 42: top-level corrective_action matches selected candidate."""
        from app.agent.candidate_history import CandidateHistory, AttemptRecordBuilder, generate_candidate_id
        
        # Create candidate history with two attempts
        history = CandidateHistory()
        
        # First attempt with retry decision
        attempt1 = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(generate_candidate_id())
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .corrective_action({
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
                "reason": "Technical settings issue",
            })
            .build()
        )
        history.add_attempt(attempt1)
        
        # Second attempt (retry) with accept decision
        attempt2 = (
            AttemptRecordBuilder()
            .attempt_index(2)
            .candidate_id(generate_candidate_id())
            .parent_candidate_id(attempt1.candidate_id)
            .attempt_kind("retry_settings")
            .workflow_id("img2img_v1")
            .corrective_action({
                "action": "accept",
                "reason_code": "accepted_by_judge",
                "reason": "Generation accepted after retry",
            })
            .build()
        )
        history.add_attempt(attempt2)
        
        # Mark second attempt as selected
        history.mark_selected(
            candidate_id=attempt2.candidate_id,
            attempt_index=2,
            selection_reason="retry_candidate_won",
        )
        
        # Verify selected attempt has corrective_action
        selected_attempt = history.get_selected_attempt()
        assert selected_attempt is not None
        assert selected_attempt.corrective_action["action"] == "accept"
    
    def test_scenario_43_retry_decision_workflow_switch_remain_derived(self):
        """Scenario 43: retry_decision and workflow_switch remain derived, not canonical."""
        from app.agent.result_contract import AgentResult
        
        # Create result with corrective_action as canonical
        result = AgentResult(
            status="completed",
            user_prompt="test",
            corrective_action={
                "action": "retry_settings",
                "reason_code": "technical_settings_retry",
                "reason": "Technical settings issue",
            },
            retry_decision={
                "action": "retry_settings",
                "reason": "Retry with settings adjustment",
            },  # Derived/compatibility field
            workflow_switch=None,
        )
        
        result_dict = result.to_dict()
        
        # Verify both fields exist but corrective_action is canonical
        assert "corrective_action" in result_dict
        assert "retry_decision" in result_dict
        assert result_dict["corrective_action"]["reason_code"] == "technical_settings_retry"
        # The retry_decision is a derived field for compatibility
    
    def test_scenario_44_failed_result_preserves_corrective_action_trace(self):
        """Scenario 44: failed result still preserves corrective_action trace."""
        from app.agent.candidate_history import AttemptRecordBuilder, generate_candidate_id
        
        # Create failed attempt with corrective_action
        attempt_record = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(generate_candidate_id())
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .error_type("ComfyUIError")
            .error("ComfyUI execution failed")
            .corrective_action({
                "action": "reject",
                "reason_code": "reject_after_judge",
                "reason": "Reject after judge aggregation",
                "source_repairs": ["unfixable issue"],
            })
            .build()
        )
        
        # Verify corrective_action is preserved even on failure
        assert attempt_record.corrective_action is not None
        assert attempt_record.corrective_action["action"] == "reject"
        assert attempt_record.error is not None
        
        # Verify it's included in to_dict
        attempt_dict = attempt_record.to_dict()
        assert "corrective_action" in attempt_dict
        assert attempt_dict["corrective_action"]["action"] == "reject"
        assert attempt_dict["error"] is not None
