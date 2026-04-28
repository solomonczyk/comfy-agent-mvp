"""Tests for mutation-aware retry planning and integration."""

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.mutation_retry_planner import MutationRetryPlanner
from app.agent.task_selector import TaskSelectionResult
from app.workflows.workflow_types import TaskType


def build_test_execution_plan(
    task_type: TaskType,
    user_prompt: str = "test prompt",
    resolved_inputs: dict | None = None,
) -> ExecutionPlan:
    """Build a test execution plan."""
    task_selection = TaskSelectionResult(
        task_type=task_type,
        confidence=0.9,
        reason="Test reason",
        routing_source="rules",
    )
    
    builder = ExecutionPlanBuilder()
    return builder.build(
        user_prompt=user_prompt,
        task_selection=task_selection,
        workflow_id="test_workflow",
        workflow_path="test/path.json",
        preset_name="test",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs=resolved_inputs or {"prompt": user_prompt},
        enable_judging=True,
        enable_retry_loop=True,
    )


def build_test_mutation_report() -> dict:
    """Build a test mutation report."""
    return {
        "workflow_id": "portrait_sdxl_v1",
        "mutated_nodes": ["3", "4", "5", "6", "7", "9"],
        "applied_changes": {
            "positive_prompt": "cinematic portrait of a realistic woman",
            "negative_prompt": "blurry, low quality, bad anatomy",
            "width": 1024,
            "height": 1024,
            "steps": 30,
            "cfg": 6.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "filename_prefix": "agent/portrait",
            "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
        },
        "notes": ["Applied task-specific overrides for portrait_txt2img"],
    }


# Scenario 1: retry_seed mutation-aware
def test_scenario_1_retry_seed():
    """Test retry_seed mutation-aware - only seed should change."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.PORTRAIT_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "retry_seed",
        "max_retries": 3,
        "notes": ["Retry with new seed while keeping general workflow stable"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify
    assert retry_plan.action == "retry_seed"
    assert "seed" in retry_plan.retry_overrides
    assert retry_plan.retry_overrides["_keep_prompt"] == True
    assert retry_plan.retry_overrides["_keep_settings"] == True
    assert "positive_prompt" not in retry_plan.retry_overrides
    assert "steps" not in retry_plan.retry_overrides
    assert "cfg" not in retry_plan.retry_overrides
    
    print("Scenario 1 (retry_seed mutation-aware): PASS")


# Scenario 2: retry_prompt mutation-aware
def test_scenario_2_retry_prompt():
    """Test retry_prompt mutation-aware - prompt should change based on repairs."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.PORTRAIT_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "retry_prompt",
        "max_retries": 3,
        "suggested_prompt_suffixes": ["improve_prompt_alignment", "strengthen_cinematic_contrast"],
        "notes": ["Prompt/intent alignment needs correction"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify
    assert retry_plan.action == "retry_prompt"
    assert "positive_prompt" in retry_plan.retry_overrides
    assert "cinematic contrast" in retry_plan.retry_overrides["positive_prompt"]
    assert retry_plan.retry_overrides["_keep_settings"] == True
    assert "seed" not in retry_plan.retry_overrides
    assert "steps" not in retry_plan.retry_overrides
    
    print("Scenario 2 (retry_prompt mutation-aware): PASS")


# Scenario 3: retry_settings mutation-aware
def test_scenario_3_retry_settings():
    """Test retry_settings mutation-aware - settings should change based on repairs."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.PORTRAIT_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "retry_settings",
        "max_retries": 3,
        "suggested_settings_updates": {
            "steps": 36,
            "cfg": 5.5,
        },
        "suggested_negative_additions": ["reduce_highlights_or_cfg"],
        "notes": ["Technical quality needs repair through generation settings"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify
    assert retry_plan.action == "retry_settings"
    assert "steps" in retry_plan.retry_overrides or "cfg" in retry_plan.retry_overrides
    assert retry_plan.retry_overrides["_keep_prompt"] == True
    assert "positive_prompt" not in retry_plan.retry_overrides or retry_plan.retry_overrides.get("_keep_prompt")
    
    print("Scenario 3 (retry_settings mutation-aware): PASS")


# Scenario 4: reject path
def test_scenario_4_reject_path():
    """Test reject path - no second attempt should be made."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.PORTRAIT_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "reject",
        "max_retries": 3,
        "notes": ["Reject after judge aggregation"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify
    assert retry_plan.action == "reject"
    assert len(retry_plan.retry_overrides) == 0
    assert "No retry needed" in " ".join(retry_plan.retry_reasoning)
    
    print("Scenario 4 (reject path): PASS")


# Scenario 5: full integration (mock)
def test_scenario_5_full_integration():
    """Test full integration with all components."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.CINEMATIC_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "retry_prompt",
        "max_retries": 3,
        "suggested_prompt_suffixes": ["improve_prompt_alignment"],
        "notes": ["Prompt/intent alignment needs correction"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify plan structure
    assert retry_plan.action == "retry_prompt"
    assert "retry_overrides" in retry_plan.to_dict()
    assert "retry_reasoning" in retry_plan.to_dict()
    assert "source_repairs" in retry_plan.to_dict()
    
    # Verify reasoning includes repair context
    assert any("retry with refined prompt" in r.lower() for r in retry_plan.retry_reasoning)
    
    # Verify source repairs captured
    assert "improve_prompt_alignment" in retry_plan.source_repairs
    
    print("Scenario 5 (full integration): PASS")


# Scenario 6: accept path (no retry)
def test_scenario_6_accept_path():
    """Test accept path - no retry needed."""
    planner = MutationRetryPlanner()
    execution_plan = build_test_execution_plan(TaskType.PORTRAIT_TXT2IMG)
    mutation_report = build_test_mutation_report()
    
    retry_decision = {
        "action": "accept",
        "max_retries": 3,
        "notes": ["Generation accepted"],
    }
    
    retry_plan = planner.build_plan(
        execution_plan=execution_plan,
        mutation_report=mutation_report,
        retry_decision=retry_decision,
        orchestrator_report=None,
    )
    
    # Verify
    assert retry_plan.action == "accept"
    assert len(retry_plan.retry_overrides) == 0
    assert "No retry needed" in " ".join(retry_plan.retry_reasoning)
    
    print("Scenario 6 (accept path / no nested retry): PASS")


# Test candidate chooser logic
def test_candidate_chooser():
    """Test candidate chooser logic for selecting best result."""
    from app.agent.workflow_agent_service import WorkflowAgentService
    from app.agent.candidate_selection import CandidateSelectionPolicy
    
    # Mock service instance (just for the chooser method)
    service = WorkflowAgentService.__new__(WorkflowAgentService)
    service.selection_policy = CandidateSelectionPolicy()
    
    # Test cases
    candidates = [
        {
            "judge_status": "pass",
            "orchestrator_report": {"final_score": 0.85},
        },
        {
            "judge_status": "retry",
            "orchestrator_report": {"final_score": 0.75},
        },
        {
            "judge_status": "reject",
            "orchestrator_report": {"final_score": 0.60},
        },
    ]
    
    best = service._choose_best_candidate(candidates)
    
    # Pass should win
    assert best["judge_status"] == "pass"
    
    # Test with same verdict, higher score wins
    candidates = [
        {
            "judge_status": "retry",
            "orchestrator_report": {"final_score": 0.70},
        },
        {
            "judge_status": "retry",
            "orchestrator_report": {"final_score": 0.80},
        },
    ]
    
    best = service._choose_best_candidate(candidates)
    assert best["orchestrator_report"]["final_score"] == 0.80
    
    # Test with single candidate
    single = [{"judge_status": "pass", "orchestrator_report": {"final_score": 0.90}}]
    best = service._choose_best_candidate(single)
    assert best["judge_status"] == "pass"
    
    print("Candidate chooser test: PASS")


if __name__ == "__main__":
    print("Running mutation-aware retry scenarios...")
    print()
    
    try:
        test_scenario_1_retry_seed()
    except Exception as e:
        print(f"Scenario 1 (retry_seed mutation-aware): FAIL - {e}")
    
    try:
        test_scenario_2_retry_prompt()
    except Exception as e:
        print(f"Scenario 2 (retry_prompt mutation-aware): FAIL - {e}")
    
    try:
        test_scenario_3_retry_settings()
    except Exception as e:
        print(f"Scenario 3 (retry_settings mutation-aware): FAIL - {e}")
    
    try:
        test_scenario_4_reject_path()
    except Exception as e:
        print(f"Scenario 4 (reject path): FAIL - {e}")
    
    try:
        test_scenario_5_full_integration()
    except Exception as e:
        print(f"Scenario 5 (full integration): FAIL - {e}")
    
    try:
        test_scenario_6_accept_path()
    except Exception as e:
        print(f"Scenario 6 (accept path / no nested retry): FAIL - {e}")
    
    try:
        test_candidate_chooser()
    except Exception as e:
        print(f"Candidate chooser test: FAIL - {e}")
    
    print()
    print("All mutation-aware retry tests completed.")
