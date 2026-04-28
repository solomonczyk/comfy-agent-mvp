"""Tests for unified agent result contract (Agent Result Contract Hardening v0).

This test suite validates that all agent outcomes (success, planning failure,
execution failure, mutation failure, judge/retry enriched) return the same
top-level schema with differences in values, not in structure.
"""

import pytest

from app.agent.result_contract import (
    AgentResult,
    AgentResultBuilder,
    ErrorCode,
    FailedStage,
    build_agent_result,
)


class TestUnifiedResultContract:
    """Test suite for unified agent result contract."""

    def test_scenario_1_planning_failure_contract(self):
        """Scenario 1: Planning failure should return unified contract.

        Input: "upscale this image" without input_image
        Expected: status="failed", failed_stage="planning_guard", task_selection exists, execution_plan=null
        """
        # Build a planning failure result
        task_selection_dict = {
            "task_type": "img2img_upscale",
            "confidence": 0.95,
            "reason": "Detected upscale request",
            "routing_source": "rules",
            "required_inputs": ["input_image"],
            "missing_inputs": ["input_image"],
            "ambiguity_level": "low",
            "safe_fallback_used": False,
        }

        result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.PLANNING_GUARD,
            error_type="planning_failure",
            error_code=ErrorCode.MISSING_REQUIRED_INPUTS,
            error="Execution blocked: missing required inputs: input_image",
            user_prompt="upscale this image",
            task_selection=task_selection_dict,
            execution_plan=None,
            images=[],
            metadata_path=None,
            summary_path=None,
        )

        result_dict = result.to_dict()

        # Verify core fields
        assert result_dict["status"] == "failed"
        assert result_dict["failed_stage"] == "planning_guard"
        assert result_dict["error_type"] == "planning_failure"
        assert result_dict["error_code"] == "MISSING_REQUIRED_INPUTS"
        assert result_dict["error"] == "Execution blocked: missing required inputs: input_image"
        assert result_dict["user_prompt"] == "upscale this image"

        # Verify task_selection exists
        assert result_dict["task_selection"] is not None
        assert result_dict["task_selection"]["task_type"] == "img2img_upscale"
        assert result_dict["task_selection"]["missing_inputs"] == ["input_image"]

        # Verify execution_plan is null
        assert result_dict["execution_plan"] is None

        # Verify other fields are present (even if null)
        assert "mutation_report" in result_dict
        assert "mutation_retry" in result_dict
        assert "judge_status" in result_dict
        assert "orchestrator_report" in result_dict
        assert "retry_decision" in result_dict
        assert "retry_loop" in result_dict
        assert result_dict["images"] == []
        assert result_dict["metadata_path"] is None
        assert result_dict["summary_path"] is None

    def test_scenario_2_txt2img_success_contract(self):
        """Scenario 2: Normal txt2img success should return unified contract.

        Input: "portrait of a woman in soft light"
        Expected: status="completed", task_selection exists, execution_plan exists, images exist or success fragment
        """
        task_selection_dict = {
            "task_type": "portrait_txt2img",
            "confidence": 0.92,
            "reason": "Detected portrait request",
            "routing_source": "rules",
            "required_inputs": [],
            "missing_inputs": [],
            "ambiguity_level": "low",
            "safe_fallback_used": False,
        }

        execution_plan_dict = {
            "user_prompt": "portrait of a woman in soft light",
            "task_type": "portrait_txt2img",
            "workflow_id": "sdxl_portrait",
            "workflow_path": "/path/to/workflow.json",
            "preset_name": "portrait",
            "rewrite_mode": "fallback",
            "required_inputs": [],
            "resolved_inputs": {"prompt": "portrait of a woman in soft light"},
            "enable_judging": True,
            "enable_retry_loop": False,
            "notes": [],
        }

        mutation_report_dict = {
            "workflow_id": "sdxl_portrait",
            "mutated_nodes": ["6", "7"],
            "applied_changes": {
                "positive_prompt": "portrait of a woman in soft light",
                "negative_prompt": "blurry, low quality",
            },
            "notes": [],
        }

        images = [
            {
                "filename": "portrait_001.png",
                "subfolder": "",
                "type": "output",
                "node_id": "9",
            }
        ]

        result = build_agent_result(
            status="completed",
            user_prompt="portrait of a woman in soft light",
            task_selection=task_selection_dict,
            execution_plan=execution_plan_dict,
            mutation_report=mutation_report_dict,
            judge_status="pass",
            orchestrator_report={"final_score": 8.5, "final_verdict": "pass"},
            retry_decision=None,
            retry_loop=None,
            images=images,
            metadata_path="/path/to/metadata.json",
            summary_path="/path/to/summary.txt",
        )

        result_dict = result.to_dict()

        # Verify core fields
        assert result_dict["status"] == "completed"
        assert result_dict["failed_stage"] is None
        assert result_dict["error_type"] is None
        assert result_dict["error_code"] is None
        assert result_dict["error"] is None
        assert result_dict["user_prompt"] == "portrait of a woman in soft light"

        # Verify task_selection exists
        assert result_dict["task_selection"] is not None
        assert result_dict["task_selection"]["task_type"] == "portrait_txt2img"

        # Verify execution_plan exists
        assert result_dict["execution_plan"] is not None
        assert result_dict["execution_plan"]["workflow_id"] == "sdxl_portrait"

        # Verify mutation_report exists
        assert result_dict["mutation_report"] is not None
        assert result_dict["mutation_report"]["workflow_id"] == "sdxl_portrait"

        # Verify judge/retry fields in unified contract
        assert result_dict["judge_status"] == "pass"
        assert result_dict["orchestrator_report"] is not None
        assert result_dict["retry_decision"] is None
        assert result_dict["retry_loop"] is None

        # Verify images
        assert len(result_dict["images"]) == 1
        assert result_dict["images"][0]["filename"] == "portrait_001.png"

        # Verify metadata paths
        assert result_dict["metadata_path"] == "/path/to/metadata.json"
        assert result_dict["summary_path"] == "/path/to/summary.txt"

    def test_scenario_3_mutation_failure_contract(self):
        """Scenario 3: Workflow mutation failure should return unified contract.

        Input: Artificially broken template / contract mismatch
        Expected: status="failed", failed_stage="workflow_mutation", task_selection exists, execution_plan exists
        """
        task_selection_dict = {
            "task_type": "portrait_txt2img",
            "confidence": 0.92,
            "reason": "Detected portrait request",
            "routing_source": "rules",
            "required_inputs": [],
            "missing_inputs": [],
            "ambiguity_level": "low",
            "safe_fallback_used": False,
        }

        execution_plan_dict = {
            "user_prompt": "portrait of a woman",
            "task_type": "portrait_txt2img",
            "workflow_id": "broken_workflow",
            "workflow_path": "/path/to/broken.json",
            "preset_name": "portrait",
            "rewrite_mode": "fallback",
            "required_inputs": [],
            "resolved_inputs": {"prompt": "portrait of a woman"},
            "enable_judging": False,
            "enable_retry_loop": False,
            "notes": [],
        }

        result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.WORKFLOW_MUTATION,
            error_type="mutation_error",
            error_code=ErrorCode.MUTATION_CONTRACT_ERROR,
            error="Workflow mutation failed: Required node '6' not found (workflow_id=broken_workflow, node_id=6)",
            user_prompt="portrait of a woman",
            task_selection=task_selection_dict,
            execution_plan=execution_plan_dict,
            mutation_report=None,  # Mutation failed, no report
            images=[],
            metadata_path=None,
            summary_path=None,
        )

        result_dict = result.to_dict()

        # Verify core fields
        assert result_dict["status"] == "failed"
        assert result_dict["failed_stage"] == "workflow_mutation"
        assert result_dict["error_type"] == "mutation_error"
        assert result_dict["error_code"] == "MUTATION_CONTRACT_ERROR"
        assert result_dict["error"] is not None

        # Verify task_selection exists (selection succeeded before mutation)
        assert result_dict["task_selection"] is not None
        assert result_dict["task_selection"]["task_type"] == "portrait_txt2img"

        # Verify execution_plan exists (plan built before mutation)
        assert result_dict["execution_plan"] is not None
        assert result_dict["execution_plan"]["workflow_id"] == "broken_workflow"

        # Verify mutation_report is null or partial with notes
        assert result_dict["mutation_report"] is None

        # Verify other fields present
        assert result_dict["images"] == []
        assert result_dict["metadata_path"] is None
        assert result_dict["summary_path"] is None

    def test_scenario_4_generation_failure_contract(self):
        """Scenario 4: Generation failure should return unified contract.

        Input: Bad checkpoint / runtime generation failure
        Expected: status="failed", failed_stage="generation", same top-level schema
        """
        task_selection_dict = {
            "task_type": "portrait_txt2img",
            "confidence": 0.92,
            "reason": "Detected portrait request",
            "routing_source": "rules",
            "required_inputs": [],
            "missing_inputs": [],
            "ambiguity_level": "low",
            "safe_fallback_used": False,
        }

        execution_plan_dict = {
            "user_prompt": "portrait of a woman",
            "task_type": "portrait_txt2img",
            "workflow_id": "sdxl_portrait",
            "workflow_path": "/path/to/workflow.json",
            "preset_name": "portrait",
            "rewrite_mode": "fallback",
            "required_inputs": [],
            "resolved_inputs": {"prompt": "portrait of a woman"},
            "enable_judging": False,
            "enable_retry_loop": False,
            "notes": [],
        }

        mutation_report_dict = {
            "workflow_id": "sdxl_portrait",
            "mutated_nodes": ["6", "7"],
            "applied_changes": {
                "positive_prompt": "portrait of a woman",
                "negative_prompt": "blurry, low quality",
            },
            "notes": [],
        }

        result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.GENERATION,
            error_type="generation_error",
            error_code=ErrorCode.GENERATION_FAILED,
            error="Generation failed: Checkpoint not found: bad_checkpoint.safetensors",
            user_prompt="portrait of a woman",
            task_selection=task_selection_dict,
            execution_plan=execution_plan_dict,
            mutation_report=mutation_report_dict,  # Mutation succeeded before generation failed
            images=[],
            metadata_path=None,
            summary_path=None,
        )

        result_dict = result.to_dict()

        # Verify core fields
        assert result_dict["status"] == "failed"
        assert result_dict["failed_stage"] == "generation"
        assert result_dict["error_type"] == "generation_error"
        assert result_dict["error_code"] == "GENERATION_FAILED"
        assert result_dict["error"] is not None

        # Verify task_selection exists
        assert result_dict["task_selection"] is not None

        # Verify execution_plan exists
        assert result_dict["execution_plan"] is not None

        # Verify mutation_report exists (mutation succeeded before generation)
        assert result_dict["mutation_report"] is not None
        assert result_dict["mutation_report"]["workflow_id"] == "sdxl_portrait"

        # Verify other fields present
        assert result_dict["images"] == []
        assert result_dict["metadata_path"] is None
        assert result_dict["summary_path"] is None

    def test_scenario_5_judge_retry_enriched_contract(self):
        """Scenario 5: Judge/retry enriched completed result should return unified contract.

        Expected: status="completed", judge_status, orchestrator_report, retry_decision, retry_loop all present
        """
        task_selection_dict = {
            "task_type": "portrait_txt2img",
            "confidence": 0.92,
            "reason": "Detected portrait request",
            "routing_source": "rules",
            "required_inputs": [],
            "missing_inputs": [],
            "ambiguity_level": "low",
            "safe_fallback_used": False,
        }

        execution_plan_dict = {
            "user_prompt": "portrait of a woman",
            "task_type": "portrait_txt2img",
            "workflow_id": "sdxl_portrait",
            "workflow_path": "/path/to/workflow.json",
            "preset_name": "portrait",
            "rewrite_mode": "fallback",
            "required_inputs": [],
            "resolved_inputs": {"prompt": "portrait of a woman"},
            "enable_judging": True,
            "enable_retry_loop": False,
            "notes": [],
        }

        mutation_report_dict = {
            "workflow_id": "sdxl_portrait",
            "mutated_nodes": ["6", "7"],
            "applied_changes": {
                "positive_prompt": "portrait of a woman",
                "negative_prompt": "blurry, low quality",
            },
            "notes": [],
        }

        mutation_retry_dict = {
            "action": "retry_with_adjustments",
            "retry_overrides_applied": {
                "cfg": 7.0,
                "steps": 35,
            },
            "attempt_index": 2,
        }

        orchestrator_report_dict = {
            "final_score": 7.2,
            "final_verdict": "pass",
            "best_next_action": "accept",
            "technical": {
                "judge_name": "TechnicalJudge",
                "score": 8.0,
                "verdict": "pass",
                "issues": [],
                "strengths": ["Good resolution"],
                "recommended_repairs": [],
            },
            "semantic": {
                "judge_name": "SemanticJudge",
                "score": 7.0,
                "verdict": "pass",
                "issues": [],
                "strengths": ["Good prompt adherence"],
                "recommended_repairs": [],
            },
            "artistic": {
                "judge_name": "ArtisticJudge",
                "score": 6.5,
                "verdict": "retry",
                "issues": [{"code": "LOW_CONTRAST", "message": "Low contrast", "severity": "medium"}],
                "strengths": ["Good composition"],
                "recommended_repairs": ["Increase contrast"],
            },
        }

        retry_decision_dict = {
            "action": "retry",
            "max_retries": 3,
            "suggested_prompt_suffixes": ["high contrast"],
            "suggested_settings_updates": {"cfg": 7.0},
            "notes": ["Retry with higher contrast"],
        }

        retry_loop_dict = {
            "loop_status": "completed",
            "selected_attempt_index": 2,
            "selected_reason": "Best score after retry",
            "attempts": [
                {
                    "attempt_index": 1,
                    "prompt_id": "abc123",
                    "judge_status": "retry",
                    "final_verdict": "retry",
                    "final_score": 6.5,
                    "retry_action": "retry",
                    "seed": 12345,
                    "metadata_path": "/path/to/metadata1.json",
                    "summary_path": "/path/to/summary1.txt",
                },
                {
                    "attempt_index": 2,
                    "prompt_id": "def456",
                    "judge_status": "pass",
                    "final_verdict": "pass",
                    "final_score": 7.2,
                    "retry_action": "accept",
                    "seed": 67890,
                    "metadata_path": "/path/to/metadata2.json",
                    "summary_path": "/path/to/summary2.txt",
                },
            ],
        }

        images = [
            {
                "filename": "portrait_002.png",
                "subfolder": "",
                "type": "output",
                "node_id": "9",
            }
        ]

        result = build_agent_result(
            status="completed",
            user_prompt="portrait of a woman",
            task_selection=task_selection_dict,
            execution_plan=execution_plan_dict,
            mutation_report=mutation_report_dict,
            mutation_retry=mutation_retry_dict,
            judge_status="pass",
            orchestrator_report=orchestrator_report_dict,
            retry_decision=retry_decision_dict,
            retry_loop=retry_loop_dict,
            images=images,
            metadata_path="/path/to/metadata2.json",
            summary_path="/path/to/summary2.txt",
        )

        result_dict = result.to_dict()

        # Verify core fields
        assert result_dict["status"] == "completed"
        assert result_dict["failed_stage"] is None

        # Verify judge/retry enriched fields
        assert result_dict["judge_status"] == "pass"
        assert result_dict["orchestrator_report"] is not None
        assert result_dict["orchestrator_report"]["final_score"] == 7.2
        assert result_dict["retry_decision"] is not None
        assert result_dict["retry_decision"]["action"] == "retry"
        assert result_dict["retry_loop"] is not None
        assert result_dict["retry_loop"]["loop_status"] == "completed"

        # Verify mutation_retry exists
        assert result_dict["mutation_retry"] is not None
        assert result_dict["mutation_retry"]["attempt_index"] == 2

        # Verify other fields
        assert result_dict["task_selection"] is not None
        assert result_dict["execution_plan"] is not None
        assert result_dict["mutation_report"] is not None
        assert len(result_dict["images"]) == 1
        assert result_dict["metadata_path"] == "/path/to/metadata2.json"
        assert result_dict["summary_path"] == "/path/to/summary2.txt"

    def test_scenario_6_schema_equality_check(self):
        """Scenario 6: Schema equality check across different result types.

        Expected: top-level keys are identical for success, planning failure, and generation failure
        """
        # Build planning failure result
        planning_result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.PLANNING_GUARD,
            error_type="planning_failure",
            error_code=ErrorCode.MISSING_REQUIRED_INPUTS,
            error="Execution blocked: missing required inputs: input_image",
            user_prompt="upscale this image",
            task_selection={"task_type": "img2img_upscale"},
            execution_plan=None,
            images=[],
        )

        # Build success result
        success_result = build_agent_result(
            status="completed",
            user_prompt="portrait of a woman",
            task_selection={"task_type": "portrait_txt2img"},
            execution_plan={"workflow_id": "sdxl_portrait"},
            mutation_report={"workflow_id": "sdxl_portrait"},
            images=[{"filename": "portrait_001.png"}],
        )

        # Build generation failure result
        generation_failure_result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.GENERATION,
            error_type="generation_error",
            error_code=ErrorCode.GENERATION_FAILED,
            error="Generation failed",
            user_prompt="portrait of a woman",
            task_selection={"task_type": "portrait_txt2img"},
            execution_plan={"workflow_id": "sdxl_portrait"},
            mutation_report={"workflow_id": "sdxl_portrait"},
            images=[],
        )

        planning_dict = planning_result.to_dict()
        success_dict = success_result.to_dict()
        generation_failure_dict = generation_failure_result.to_dict()

        # Get top-level keys for each result
        planning_keys = set(planning_dict.keys())
        success_keys = set(success_dict.keys())
        generation_failure_keys = set(generation_failure_dict.keys())

        # Expected top-level keys (current AgentResult schema; KT-2 added trace_path + tool_chain)
        expected_keys = {
            "status",
            "failed_stage",
            "error_type",
            "error_code",
            "error",
            "user_prompt",
            "task_selection",
            "execution_plan",
            "mutation_report",
            "mutation_retry",
            "judge_status",
            "orchestrator_report",
            "retry_decision",
            "retry_loop",
            "workflow_switch",
            "corrective_action",
            "candidate_history",
            "candidate_selection",
            "executed_action",
            "images",
            "metadata_path",
            "summary_path",
            "recipe_validation",
            "trace_path",
            "tool_chain",
            "upscale_result",
        }

        # Verify all results have the same top-level keys
        assert planning_keys == expected_keys, f"Planning failure keys mismatch: {planning_keys - expected_keys} | {expected_keys - planning_keys}"
        assert success_keys == expected_keys, f"Success keys mismatch: {success_keys - expected_keys} | {expected_keys - success_keys}"
        assert generation_failure_keys == expected_keys, f"Generation failure keys mismatch: {generation_failure_keys - expected_keys} | {expected_keys - generation_failure_keys}"

        # Verify all three have identical keys
        assert planning_keys == success_keys == generation_failure_keys


class TestAgentResultBuilder:
    """Test suite for AgentResultBuilder fluent interface."""

    def test_builder_fluent_interface(self):
        """Test that builder provides fluent interface."""
        result = (
            AgentResultBuilder()
            .with_status("completed")
            .with_user_prompt("test prompt")
            .with_task_selection({"task_type": "portrait_txt2img"})
            .with_execution_plan({"workflow_id": "sdxl_portrait"})
            .with_images([{"filename": "test.png"}])
            .build()
        )

        assert result.status == "completed"
        assert result.user_prompt == "test prompt"
        assert result.task_selection == {"task_type": "portrait_txt2img"}
        assert result.execution_plan == {"workflow_id": "sdxl_portrait"}
        assert len(result.images) == 1

    def test_builder_with_error_fields(self):
        """Test builder with error-related fields."""
        result = (
            AgentResultBuilder()
            .with_status("failed")
            .with_failed_stage(FailedStage.GENERATION)
            .with_error(
                error_type="generation_error",
                error_code=ErrorCode.GENERATION_FAILED,
                error="Generation failed",
            )
            .with_user_prompt("test prompt")
            .build()
        )

        assert result.status == "failed"
        assert result.failed_stage == FailedStage.GENERATION
        assert result.error_type == "generation_error"
        assert result.error_code == ErrorCode.GENERATION_FAILED
        assert result.error == "Generation failed"


class TestEnums:
    """Test suite for FailedStage and ErrorCode enums."""

    def test_failed_stage_enum_values(self):
        """Test that FailedStage enum has expected values."""
        assert FailedStage.PLANNING_GUARD.value == "planning_guard"
        assert FailedStage.WORKFLOW_LOOKUP.value == "workflow_lookup"
        assert FailedStage.EXECUTION_PLAN_BUILD.value == "execution_plan_build"
        assert FailedStage.WORKFLOW_MUTATION.value == "workflow_mutation"
        assert FailedStage.GENERATION.value == "generation"
        assert FailedStage.JUDGE_PIPELINE.value == "judge_pipeline"
        assert FailedStage.RETRY_LOOP.value == "retry_loop"

    def test_error_code_enum_values(self):
        """Test that ErrorCode enum has expected values."""
        assert ErrorCode.MISSING_REQUIRED_INPUTS.value == "MISSING_REQUIRED_INPUTS"
        assert ErrorCode.WORKFLOW_NOT_FOUND.value == "WORKFLOW_NOT_FOUND"
        assert ErrorCode.WORKFLOW_NOT_IMPLEMENTED.value == "WORKFLOW_NOT_IMPLEMENTED"
        assert ErrorCode.MUTATION_CONTRACT_ERROR.value == "MUTATION_CONTRACT_ERROR"
        assert ErrorCode.GENERATION_FAILED.value == "GENERATION_FAILED"
        assert ErrorCode.JUDGE_PIPELINE_FAILED.value == "JUDGE_PIPELINE_FAILED"
        assert ErrorCode.RETRY_LOOP_FAILED.value == "RETRY_LOOP_FAILED"
