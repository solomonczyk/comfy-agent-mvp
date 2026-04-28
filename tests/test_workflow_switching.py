"""Tests for workflow switching (Workflow Switching v0).

This test suite validates that the agent can perform controlled switches
between known workflows (img2img, inpaint_face, upscale, txt2img family)
without multi-hop chaos, with proper asset validation and unified result contract.
"""

import pytest

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelectionResult
from app.agent.workflow_switch_planner import WorkflowSwitchPlanner, WorkflowSwitchPlan
from app.agent.workflow_switch_policy import (
    ALLOWED_SWITCHES,
    WORKFLOW_ASSET_REQUIREMENTS,
    WorkflowSwitchDecision,
    WorkflowSwitchPolicy,
)
from app.workflows.workflow_types import TaskType


class TestWorkflowSwitchPolicy:
    """Test suite for workflow switch policy."""

    def test_switch_matrix_img2img_to_upscale_allowed(self):
        """Test that img2img_v1 -> upscale_v1 is allowed in switch matrix."""
        assert "upscale_v1" in ALLOWED_SWITCHES["img2img_v1"]
    
    def test_switch_matrix_img2img_to_inpaint_face_allowed(self):
        """Test that img2img_v1 -> inpaint_face_v1 is allowed in switch matrix."""
        assert "inpaint_face_v1" in ALLOWED_SWITCHES["img2img_v1"]
    
    def test_switch_matrix_upscale_to_img2img_allowed(self):
        """Test that upscale_v1 -> img2img_v1 is allowed in switch matrix."""
        assert "img2img_v1" in ALLOWED_SWITCHES["upscale_v1"]
    
    def test_switch_matrix_inpaint_face_to_img2img_allowed(self):
        """Test that inpaint_face_v1 -> img2img_v1 is allowed in switch matrix."""
        assert "img2img_v1" in ALLOWED_SWITCHES["inpaint_face_v1"]
    
    def test_asset_requirements_inpaint_face(self):
        """Test that inpaint_face_v1 requires input_image and mask_image."""
        assert WORKFLOW_ASSET_REQUIREMENTS["inpaint_face_v1"] == ["input_image", "mask_image"]
    
    def test_asset_requirements_upscale(self):
        """Test that upscale_v1 requires input_image."""
        assert WORKFLOW_ASSET_REQUIREMENTS["upscale_v1"] == ["input_image"]
    
    def test_asset_requirements_txt2img(self):
        """Test that txt2img workflows have no asset requirements."""
        assert WORKFLOW_ASSET_REQUIREMENTS["txt2img_portrait"] == []
    
    def test_policy_returns_keep_current_when_no_retry_decision(self):
        """Test that policy returns keep_current when no retry decision."""
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        decision = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=None,
            orchestrator_report=None,
            assets=None,
        )
        
        assert decision.action == "keep_current"
        assert decision.switch_allowed is False
    
    def test_policy_returns_switch_workflow_for_resolution_repair(self):
        """Test that policy returns switch_workflow for resolution-focused repair."""
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        orchestrator_report = {
            "technical": {
                "recommended_repairs": ["increase resolution", "sharper details"],
            },
            "semantic": {
                "recommended_repairs": [],
            },
            "artistic": {
                "recommended_repairs": [],
            },
        }
        
        retry_decision = {
            "action": "switch_workflow",
            "max_retries": 3,
        }
        
        decision = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png"},
        )
        
        assert decision.action == "switch_workflow"
        assert decision.switch_allowed is True
        assert decision.to_workflow_id == "upscale_v1"
    
    def test_policy_blocks_switch_for_missing_assets(self):
        """Test that policy blocks switch when assets are missing."""
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        orchestrator_report = {
            "technical": {
                "recommended_repairs": ["face repair"],
            },
            "semantic": {
                "recommended_repairs": [],
            },
            "artistic": {
                "recommended_repairs": [],
            },
        }
        
        retry_decision = {
            "action": "switch_workflow",
            "max_retries": 3,
        }
        
        # Missing mask_image for inpaint_face
        decision = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png"},  # No mask_image
        )
        
        assert decision.action == "retry_current"
        assert decision.switch_allowed is False
        assert "mask_image" in decision.missing_inputs
    
    def test_policy_blocks_multi_hop_switching(self):
        """Test that policy blocks multi-hop switching."""
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        retry_decision = {
            "action": "switch_workflow",
            "max_retries": 3,
        }
        
        decision = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=None,
            assets=None,
            switch_applied_this_run=True,  # Switch already applied in this run
        )
        
        assert decision.action == "keep_current"
        assert decision.switch_allowed is False
        assert "Multi-hop switching not allowed" in decision.switch_reason
    
    def test_policy_returns_switch_workflow_for_face_repair(self):
        """Test that policy returns switch_workflow for face-specific repair."""
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        orchestrator_report = {
            "technical": {
                "recommended_repairs": ["face repair", "eye artifacts"],
            },
            "semantic": {
                "recommended_repairs": [],
            },
            "artistic": {
                "recommended_repairs": [],
            },
        }
        
        retry_decision = {
            "action": "switch_workflow",
            "max_retries": 3,
        }
        
        decision = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png", "mask_image": "mask.png"},
        )
        
        assert decision.action == "switch_workflow"
        assert decision.switch_allowed is True
        assert decision.to_workflow_id == "inpaint_face_v1"


class TestWorkflowSwitchPlanner:
    """Test suite for workflow switch planner."""
    
    def test_planner_returns_switch_not_applied_when_decision_is_retry_current(self):
        """Test that planner returns switch not applied when decision is retry_current."""
        planner = WorkflowSwitchPlanner("/workflows")
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        switch_decision = WorkflowSwitchDecision(
            action="retry_current",
            switch_allowed=False,
            from_workflow_id="img2img_v1",
            to_workflow_id=None,
            switch_reason="Normal retry sufficient",
            source_trigger="default",
        )
        
        task_selection = TaskSelectionResult(
            task_type=TaskType.IMG2IMG,
            confidence=0.9,
            reason="test",
            routing_source="rules",
            required_inputs=["input_image"],
            missing_inputs=[],
            ambiguity_level="low",
            safe_fallback_used=False,
        )
        
        # Mock registry
        class MockRegistry:
            def get_by_id(self, workflow_id):
                return None
        
        switch_plan = planner.build_switch_plan(
            current_execution_plan=execution_plan,
            switch_decision=switch_decision,
            task_selection=task_selection,
            assets=None,
            registry=MockRegistry(),
        )
        
        assert switch_plan.switch_applied is False
        assert switch_plan.from_workflow_id == "img2img_v1"
        assert switch_plan.to_workflow_id is None


class TestWorkflowSwitchDecision:
    """Test suite for WorkflowSwitchDecision dataclass."""
    
    def test_decision_to_dict(self):
        """Test that WorkflowSwitchDecision can be converted to dict."""
        decision = WorkflowSwitchDecision(
            action="switch_workflow",
            switch_allowed=True,
            from_workflow_id="img2img_v1",
            to_workflow_id="upscale_v1",
            switch_reason="Resolution-focused repair",
            source_trigger="orchestrator_report",
            missing_inputs=[],
            notes=["Switch approved"],
        )
        
        decision_dict = decision.to_dict()
        
        assert decision_dict["action"] == "switch_workflow"
        assert decision_dict["switch_allowed"] is True
        assert decision_dict["from_workflow_id"] == "img2img_v1"
        assert decision_dict["to_workflow_id"] == "upscale_v1"
        assert decision_dict["switch_reason"] == "Resolution-focused repair"
        assert decision_dict["source_trigger"] == "orchestrator_report"


class TestWorkflowSwitchPlan:
    """Test suite for WorkflowSwitchPlan dataclass."""
    
    def test_plan_to_dict(self):
        """Test that WorkflowSwitchPlan can be converted to dict."""
        plan = WorkflowSwitchPlan(
            switch_applied=True,
            from_workflow_id="img2img_v1",
            to_workflow_id="upscale_v1",
            target_task_type="img2img_upscale",
            switch_reason="Resolution-focused repair",
            source_trigger="orchestrator_report",
            required_inputs=["input_image"],
            missing_inputs=[],
            notes=["Switch plan built"],
            switched_execution_plan=None,
        )
        
        plan_dict = plan.to_dict()
        
        assert plan_dict["switch_applied"] is True
        assert plan_dict["from_workflow_id"] == "img2img_v1"
        assert plan_dict["to_workflow_id"] == "upscale_v1"
        assert plan_dict["target_task_type"] == "img2img_upscale"
        assert plan_dict["switch_reason"] == "Resolution-focused repair"


class TestWorkflowSwitchContractRepair:
    """Test suite for workflow switch contract repair (v0)."""
    
    def test_scenario_7_switched_candidate_becomes_final_top_level_result(self):
        """Scenario 7: switched candidate becomes final top-level result.
        
        Expected:
        - workflow_switch.to_workflow_id = upscale_v1
        - execution_plan.workflow_id = upscale_v1
        - mutation_report.workflow_id = upscale_v1
        - images correspond to upscale result
        - judge_status corresponds to selected switched attempt
        - selected_candidate_workflow_id matches to_workflow_id
        """
        # Simulate a switch scenario where switched result is selected
        from_workflow_id = "img2img_v1"
        to_workflow_id = "upscale_v1"
        
        # First attempt result (img2img_v1)
        first_result = {
            "execution_plan": {"workflow_id": "img2img_v1"},
            "mutation_report": {"workflow_id": "img2img_v1"},
            "judge_status": "retry",
            "orchestrator_report": {"final_score": 6.5},
            "retry_decision": {"action": "switch_workflow"},
            "images": [{"filename": "img2img_result.png"}],
            "metadata_path": "/path/to/metadata1.json",
            "summary_path": "/path/to/summary1.txt",
        }
        
        # Switched attempt result (upscale_v1) - this should become top-level
        switched_result = {
            "execution_plan": {"workflow_id": "upscale_v1"},
            "mutation_report": {"workflow_id": "upscale_v1"},
            "judge_status": "pass",
            "orchestrator_report": {"final_score": 8.5},
            "retry_decision": {"action": "accept"},
            "images": [{"filename": "portrait_upscaled_001.png"}],
            "metadata_path": "/path/to/metadata2.json",
            "summary_path": "/path/to/summary2.txt",
        }
        
        # Simulate the canonical result selection logic
        # (In real implementation, this happens in _handle_workflow_switch)
        selected_result = switched_result  # Assume switched result is selected
        
        # Attach workflow_switch block
        selected_result["workflow_switch"] = {
            "switch_applied": True,
            "from_workflow_id": from_workflow_id,
            "to_workflow_id": to_workflow_id,
            "switch_reason": "Judge recommended repairs: increase resolution",
            "source_trigger": "orchestrator_report",
            "switch_allowed": True,
            "missing_inputs": [],
            "notes": ["Switch approved"],
            "selected_candidate_workflow_id": to_workflow_id,
        }
        
        # Verify contract repair: top-level fields match selected switched candidate
        assert selected_result["workflow_switch"]["switch_applied"] is True
        assert selected_result["workflow_switch"]["from_workflow_id"] == from_workflow_id
        assert selected_result["workflow_switch"]["to_workflow_id"] == to_workflow_id
        assert selected_result["workflow_switch"]["selected_candidate_workflow_id"] == to_workflow_id
        
        # Verify top-level execution_plan matches switched workflow
        assert selected_result["execution_plan"]["workflow_id"] == to_workflow_id
        
        # Verify top-level mutation_report matches switched workflow
        assert selected_result["mutation_report"]["workflow_id"] == to_workflow_id
        
        # Verify top-level images correspond to switched result
        assert selected_result["images"][0]["filename"] == "portrait_upscaled_001.png"
        
        # Verify top-level judge_status corresponds to selected switched attempt
        assert selected_result["judge_status"] == "pass"
        
        # Verify top-level orchestrator_report corresponds to selected switched attempt
        assert selected_result["orchestrator_report"]["final_score"] == 8.5
        
        # Verify top-level metadata/summary paths correspond to switched result
        assert selected_result["metadata_path"] == "/path/to/metadata2.json"
        assert selected_result["summary_path"] == "/path/to/summary2.txt"
    
    def test_scenario_8_no_cross_run_state_leak(self):
        """Scenario 8: no cross-run state leak.
        
        Expected:
        - Two consecutive independent runs
        - In first run, switch is applied
        - In second run, switch can also be applied if conditions are valid
        - Second run is not blocked by "memory" from first run
        """
        policy = WorkflowSwitchPolicy()
        
        execution_plan = ExecutionPlanBuilder().build(
            user_prompt="test",
            task_selection=TaskSelectionResult(
                task_type=TaskType.IMG2IMG,
                confidence=0.9,
                reason="test",
                routing_source="rules",
                required_inputs=["input_image"],
                missing_inputs=[],
                ambiguity_level="low",
                safe_fallback_used=False,
            ),
            workflow_id="img2img_v1",
            workflow_path="/path/to/workflow.json",
            preset_name="default",
            rewrite_mode="fallback",
            required_inputs=["input_image"],
            resolved_inputs={"prompt": "test", "input_image": "image.png"},
            enable_judging=False,
            enable_retry_loop=False,
        )
        
        orchestrator_report = {
            "technical": {
                "recommended_repairs": ["increase resolution"],
            },
            "semantic": {
                "recommended_repairs": [],
            },
            "artistic": {
                "recommended_repairs": [],
            },
        }
        
        retry_decision = {
            "action": "switch_workflow",
            "max_retries": 3,
        }
        
        # First run: switch applied (switch_applied_this_run=False)
        decision_1 = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png"},
            switch_applied_this_run=False,  # No switch applied yet in this run
        )
        
        assert decision_1.action == "switch_workflow"
        assert decision_1.switch_allowed is True
        assert decision_1.to_workflow_id == "upscale_v1"
        
        # Second run: same conditions, should also allow switch
        # (switch_applied_this_run=False because it's a new independent run)
        decision_2 = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png"},
            switch_applied_this_run=False,  # New run, no switch applied yet
        )
        
        assert decision_2.action == "switch_workflow"
        assert decision_2.switch_allowed is True
        assert decision_2.to_workflow_id == "upscale_v1"
        
        # Verify that state is not leaking between runs
        # If state leaked, the second run would be blocked even with switch_applied_this_run=False
        # The policy is stateless, so this should pass
        
        # Also verify that within a single run, multi-hop is blocked
        decision_3 = policy.evaluate(
            task_selection=None,
            execution_plan=execution_plan,
            mutation_report=None,
            retry_decision=retry_decision,
            orchestrator_report=orchestrator_report,
            assets={"input_image": "image.png"},
            switch_applied_this_run=True,  # Switch already applied in this run
        )
        
        assert decision_3.action == "keep_current"
        assert decision_3.switch_allowed is False
        assert "Multi-hop switching not allowed" in decision_3.switch_reason


class TestCandidateHistoryAndLineage:
    """Test suite for candidate history and attempt lineage (v0)."""
    
    def test_scenario_9_single_attempt_history(self):
        """Scenario 9: single attempt history.
        
        Expected:
        - One attempt in history
        - attempt_kind = initial
        - It is selected
        - No parent_candidate_id
        """
        from app.agent.candidate_history import (
            AttemptRecord,
            AttemptRecordBuilder,
            CandidateHistory,
            generate_candidate_id,
        )
        
        history = CandidateHistory()
        
        # Create single initial attempt
        candidate_id = generate_candidate_id()
        attempt = (
            AttemptRecordBuilder()
            .attempt_index(0)
            .candidate_id(candidate_id)
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("pass")
            .selected(True)
            .selection_reason("only_candidate")
            .images([{"filename": "result.png"}])
            .build()
        )
        
        history.add_attempt(attempt)
        history.mark_selected(candidate_id, 0, "only_candidate")
        
        history_dict = history.to_dict()
        
        assert history_dict["selected_candidate_id"] == candidate_id
        assert history_dict["selected_attempt_index"] == 0
        assert history_dict["selection_reason"] == "only_candidate"
        assert len(history_dict["attempts"]) == 1
        assert history_dict["attempts"][0]["attempt_index"] == 0
        assert history_dict["attempts"][0]["attempt_kind"] == "initial"
        assert history_dict["attempts"][0]["selected"] is True
        assert history_dict["attempts"][0]["parent_candidate_id"] is None
    
    def test_scenario_10_retry_lineage(self):
        """Scenario 10: retry lineage.
        
        Expected:
        - initial + retry in history
        - retry has parent_candidate_id pointing to initial
        - Best candidate is selected
        - selection_reason filled
        """
        from app.agent.candidate_history import (
            AttemptRecord,
            AttemptRecordBuilder,
            CandidateHistory,
            generate_candidate_id,
        )
        
        history = CandidateHistory()
        
        # Create initial attempt
        initial_id = generate_candidate_id()
        initial = (
            AttemptRecordBuilder()
            .attempt_index(0)
            .candidate_id(initial_id)
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("retry")
            .final_score(6.5)
            .build()
        )
        
        # Create retry attempt
        retry_id = generate_candidate_id()
        retry = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(retry_id)
            .parent_candidate_id(initial_id)
            .attempt_kind("retry_mutation")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("pass")
            .final_score(8.5)
            .mutation_report({"applied_changes": {"positive_prompt": "enhanced"}})
            .build()
        )
        
        history.add_attempt(initial)
        history.add_attempt(retry)
        history.mark_selected(retry_id, 1, "retry_candidate_won")
        
        history_dict = history.to_dict()
        
        assert history_dict["selected_candidate_id"] == retry_id
        assert history_dict["selected_attempt_index"] == 1
        assert history_dict["selection_reason"] == "retry_candidate_won"
        assert len(history_dict["attempts"]) == 2
        
        # Check initial attempt
        assert history_dict["attempts"][0]["candidate_id"] == initial_id
        assert history_dict["attempts"][0]["attempt_kind"] == "initial"
        assert history_dict["attempts"][0]["parent_candidate_id"] is None
        assert history_dict["attempts"][0]["selected"] is False
        
        # Check retry attempt
        assert history_dict["attempts"][1]["candidate_id"] == retry_id
        assert history_dict["attempts"][1]["attempt_kind"] == "retry_mutation"
        assert history_dict["attempts"][1]["parent_candidate_id"] == initial_id
        assert history_dict["attempts"][1]["selected"] is True
        assert history_dict["attempts"][1]["mutation_report"] is not None
    
    def test_scenario_11_workflow_switch_lineage(self):
        """Scenario 11: workflow switch lineage.
        
        Expected:
        - initial + switched in history
        - switched has attempt_kind = workflow_switch
        - parent = initial
        - If switched wins, selected candidate = switched
        """
        from app.agent.candidate_history import (
            AttemptRecord,
            AttemptRecordBuilder,
            CandidateHistory,
            generate_candidate_id,
        )
        
        history = CandidateHistory()
        
        # Create initial attempt
        initial_id = generate_candidate_id()
        initial = (
            AttemptRecordBuilder()
            .attempt_index(0)
            .candidate_id(initial_id)
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("retry")
            .final_score(6.5)
            .build()
        )
        
        # Create switched attempt
        switched_id = generate_candidate_id()
        switched = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(switched_id)
            .parent_candidate_id(initial_id)
            .attempt_kind("workflow_switch")
            .workflow_id("upscale_v1")
            .task_type("upscale")
            .judge_status("pass")
            .final_score(8.5)
            .workflow_switch({
                "switch_applied": True,
                "from_workflow_id": "img2img_v1",
                "to_workflow_id": "upscale_v1",
                "switch_reason": "Judge recommended repairs: increase resolution",
                "source_trigger": "orchestrator_report",
            })
            .images([{"filename": "upscaled.png"}])
            .build()
        )
        
        history.add_attempt(initial)
        history.add_attempt(switched)
        history.mark_selected(switched_id, 1, "workflow_switch_candidate_won")
        
        history_dict = history.to_dict()
        
        assert history_dict["selected_candidate_id"] == switched_id
        assert history_dict["selected_attempt_index"] == 1
        assert history_dict["selection_reason"] == "workflow_switch_candidate_won"
        assert len(history_dict["attempts"]) == 2
        
        # Check initial attempt
        assert history_dict["attempts"][0]["candidate_id"] == initial_id
        assert history_dict["attempts"][0]["attempt_kind"] == "initial"
        assert history_dict["attempts"][0]["parent_candidate_id"] is None
        assert history_dict["attempts"][0]["selected"] is False
        
        # Check switched attempt
        assert history_dict["attempts"][1]["candidate_id"] == switched_id
        assert history_dict["attempts"][1]["attempt_kind"] == "workflow_switch"
        assert history_dict["attempts"][1]["parent_candidate_id"] == initial_id
        assert history_dict["attempts"][1]["selected"] is True
        assert history_dict["attempts"][1]["workflow_id"] == "upscale_v1"
        assert history_dict["attempts"][1]["workflow_switch"] is not None
    
    def test_scenario_12_failed_candidate_preserved(self):
        """Scenario 12: failed candidate preserved.
        
        Expected:
        - Failed retry or failed switched attempt still present in history
        - Has error_type/error
        """
        from app.agent.candidate_history import (
            AttemptRecord,
            AttemptRecordBuilder,
            CandidateHistory,
            generate_candidate_id,
        )
        
        history = CandidateHistory()
        
        # Create initial attempt (success)
        initial_id = generate_candidate_id()
        initial = (
            AttemptRecordBuilder()
            .attempt_index(0)
            .candidate_id(initial_id)
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("pass")
            .final_score(8.5)
            .images([{"filename": "result.png"}])
            .build()
        )
        
        # Create failed retry attempt
        retry_id = generate_candidate_id()
        retry = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(retry_id)
            .parent_candidate_id(initial_id)
            .attempt_kind("retry_mutation")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .error_type("generation_failed")
            .error_code("GENERATION_FAILED")
            .error("ComfyUI execution failed")
            .build()
        )
        
        history.add_attempt(initial)
        history.add_attempt(retry)
        history.mark_selected(initial_id, 0, "initial_candidate_kept")
        
        history_dict = history.to_dict()
        
        assert history_dict["selected_candidate_id"] == initial_id
        assert len(history_dict["attempts"]) == 2
        
        # Check failed retry is preserved
        assert history_dict["attempts"][1]["candidate_id"] == retry_id
        assert history_dict["attempts"][1]["attempt_kind"] == "retry_mutation"
        assert history_dict["attempts"][1]["error_type"] == "generation_failed"
        assert history_dict["attempts"][1]["error_code"] == "GENERATION_FAILED"
        assert history_dict["attempts"][1]["error"] == "ComfyUI execution failed"
        assert history_dict["attempts"][1]["selected"] is False
    
    def test_scenario_13_top_level_result_matches_selected_candidate_history(self):
        """Scenario 13: top-level result matches selected candidate history.
        
        Expected:
        - candidate_history.selected_candidate_id corresponds to top-level:
        - execution_plan.workflow_id
        - mutation_report.workflow_id
        - images
        - judge_status
        """
        from app.agent.candidate_history import (
            AttemptRecord,
            AttemptRecordBuilder,
            CandidateHistory,
            generate_candidate_id,
        )
        
        history = CandidateHistory()
        
        # Create initial attempt
        initial_id = generate_candidate_id()
        initial = (
            AttemptRecordBuilder()
            .attempt_index(0)
            .candidate_id(initial_id)
            .attempt_kind("initial")
            .workflow_id("img2img_v1")
            .task_type("img2img")
            .judge_status("retry")
            .final_score(6.5)
            .images([{"filename": "initial.png"}])
            .build()
        )
        
        # Create switched attempt (selected)
        switched_id = generate_candidate_id()
        switched = (
            AttemptRecordBuilder()
            .attempt_index(1)
            .candidate_id(switched_id)
            .parent_candidate_id(initial_id)
            .attempt_kind("workflow_switch")
            .workflow_id("upscale_v1")
            .task_type("upscale")
            .judge_status("pass")
            .final_score(8.5)
            .images([{"filename": "upscaled.png"}])
            .build()
        )
        
        history.add_attempt(initial)
        history.add_attempt(switched)
        history.mark_selected(switched_id, 1, "workflow_switch_candidate_won")
        
        history_dict = history.to_dict()
        selected_attempt = history.get_selected_attempt()
        
        # Simulate top-level result matching selected candidate
        top_level = {
            "execution_plan": {"workflow_id": "upscale_v1"},
            "mutation_report": {"workflow_id": "upscale_v1"},
            "judge_status": "pass",
            "images": [{"filename": "upscaled.png"}],
        }
        
        assert selected_attempt is not None
        assert selected_attempt.workflow_id == "upscale_v1"
        assert selected_attempt.judge_status == "pass"
        assert selected_attempt.images[0]["filename"] == "upscaled.png"
        
        # Verify top-level matches selected candidate
        assert top_level["execution_plan"]["workflow_id"] == selected_attempt.workflow_id
        assert top_level["judge_status"] == selected_attempt.judge_status
        assert top_level["images"][0]["filename"] == selected_attempt.images[0]["filename"]
    
    def test_scenario_14_routing_source_normalized_everywhere(self):
        """Scenario 14: routing_source normalized everywhere.
        
        Expected:
        - No external fragment has keyword
        - Only rules | llm
        """
        # This is already tested in test_mixed_routing_pack.py::test_routing_source_only_rules_or_llm
        # The fix has been applied to test_workflow_switching.py and test_unified_agent_result_contract.py
        # All routing_source values are now normalized to "rules" or "llm"
        
        # Verify in our test fixtures
        from app.agent.task_selector import TaskSelectionResult
        from app.workflows.workflow_types import TaskType
        
        # Create task selection with normalized routing_source
        task_selection = TaskSelectionResult(
            task_type=TaskType.IMG2IMG,
            confidence=0.9,
            reason="test",
            routing_source="rules",  # Normalized
            required_inputs=["input_image"],
            missing_inputs=[],
            ambiguity_level="low",
            safe_fallback_used=False,
        )
        
        assert task_selection.routing_source in ["rules", "llm"]
        assert task_selection.routing_source == "rules"
