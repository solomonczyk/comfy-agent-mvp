"""Test scenarios for workflow agent integration."""

import json
from pathlib import Path

from app.agent.execution_plan import ExecutionPlanBuilder
from app.agent.task_selector import TaskSelector
from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType


def test_scenario_1_portrait_prompt():
    """Scenario 1: portrait prompt should select portrait_txt2img."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("cinematic portrait of a woman in soft window light")
    
    assert result.task_type in [TaskType.PORTRAIT_TXT2IMG, TaskType.CINEMATIC_TXT2IMG], \
        f"Expected portrait or cinematic, got {result.task_type}"
    assert result.confidence >= 0.7, f"Confidence too low: {result.confidence}"
    assert result.routing_source == "rules"
    print("✓ Scenario 1 PASS: portrait prompt routing")


def test_scenario_2_product_prompt():
    """Scenario 2: product prompt should select product_txt2img."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("luxury product shot of a perfume bottle on reflective black surface")
    
    assert result.task_type == TaskType.PRODUCT_TXT2IMG, \
        f"Expected product_txt2img, got {result.task_type}"
    assert result.confidence >= 0.7, f"Confidence too low: {result.confidence}"
    assert result.routing_source == "rules"
    print("✓ Scenario 2 PASS: product prompt routing")


def test_scenario_3_fashion_prompt():
    """Scenario 3: fashion prompt should select fashion_txt2img."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("high fashion editorial model, premium studio look")
    
    assert result.task_type == TaskType.FASHION_TXT2IMG, \
        f"Expected fashion_txt2img, got {result.task_type}"
    assert result.confidence >= 0.7, f"Confidence too low: {result.confidence}"
    assert result.routing_source == "rules"
    print("✓ Scenario 3 PASS: fashion prompt routing")


def test_scenario_4_upscale_prompt():
    """Scenario 4: upscale prompt should select upscale."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("upscale this image to high detail")
    
    assert result.task_type == TaskType.UPSCALE, \
        f"Expected upscale, got {result.task_type}"
    assert result.confidence >= 0.7, f"Confidence too low: {result.confidence}"
    assert result.routing_source == "rules"
    print("✓ Scenario 4 PASS: upscale prompt routing")


def test_scenario_5_inpaint_face_prompt():
    """Scenario 5: inpaint face prompt should select inpaint_face."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("repair face and fix eye artifacts")
    
    assert result.task_type == TaskType.INPAINT_FACE, \
        f"Expected inpaint_face, got {result.task_type}"
    assert result.confidence >= 0.7, f"Confidence too low: {result.confidence}"
    assert result.routing_source == "rules"
    print("✓ Scenario 5 PASS: inpaint face prompt routing")


def test_scenario_6_ambiguous_prompt():
    """Scenario 6: ambiguous prompt should not crash."""
    selector = TaskSelector(llm_client=None)
    result = selector.select("make this better and more cinematic")
    
    # Should not crash
    assert result is not None
    assert result.routing_source in ["rules", "llm"]
    assert result.confidence is not None
    assert result.reason is not None
    print(f"✓ Scenario 6 PASS: ambiguous prompt handled (task_type={result.task_type}, confidence={result.confidence})")


def test_scenario_7_full_integration():
    """Scenario 7: full integration test - build execution plan."""
    workflows_dir = Path(__file__).parent.parent / "data" / "workflows"
    registry = WorkflowRegistry(workflows_dir)
    selector = TaskSelector(llm_client=None)
    plan_builder = ExecutionPlanBuilder()
    
    user_prompt = "cinematic portrait of a woman"
    
    # Step 1: Select task
    task_selection = selector.select(user_prompt)
    
    # Step 2: Get workflow from registry
    workflow_spec = registry.get_default_for_task(task_selection.task_type)
    
    assert workflow_spec is not None, "No workflow found for task type"
    assert workflow_spec.implemented, "Selected workflow is not implemented"
    
    # Step 3: Build execution plan
    execution_plan = plan_builder.build(
        user_prompt=user_prompt,
        task_selection=task_selection,
        workflow_id=workflow_spec.workflow_id,
        workflow_path=workflow_spec.workflow_path,
        preset_name=workflow_spec.preset_name,
        rewrite_mode=workflow_spec.default_rewrite_mode,
        required_inputs=workflow_spec.required_inputs,
        resolved_inputs={"prompt": user_prompt},
        enable_judging=workflow_spec.supports_judging,
        enable_retry_loop=workflow_spec.supports_retry,
    )
    
    # Verify plan structure
    assert execution_plan.user_prompt == user_prompt
    assert execution_plan.task_type == task_selection.task_type
    assert execution_plan.workflow_id == workflow_spec.workflow_id
    assert execution_plan.preset_name == workflow_spec.preset_name
    assert execution_plan.enable_judging == workflow_spec.supports_judging
    assert execution_plan.enable_retry_loop == workflow_spec.supports_retry
    
    # Verify plan serialization
    plan_dict = execution_plan.to_dict()
    assert "user_prompt" in plan_dict
    assert "task_type" in plan_dict
    assert "workflow_id" in plan_dict
    assert "preset_name" in plan_dict
    assert "enable_judging" in plan_dict
    assert "enable_retry_loop" in plan_dict
    
    print("✓ Scenario 7 PASS: full integration - execution plan built successfully")
    print(f"  Task type: {execution_plan.task_type}")
    print(f"  Workflow ID: {execution_plan.workflow_id}")
    print(f"  Preset: {execution_plan.preset_name}")
    print(f"  Enable judging: {execution_plan.enable_judging}")
    print(f"  Enable retry: {execution_plan.enable_retry_loop}")


def run_all_scenarios():
    """Run all test scenarios and report results."""
    print("\n" + "="*60)
    print("RUNNING WORKFLOW AGENT TEST SCENARIOS")
    print("="*60 + "\n")
    
    scenarios = [
        ("Scenario 1: portrait prompt", test_scenario_1_portrait_prompt),
        ("Scenario 2: product prompt", test_scenario_2_product_prompt),
        ("Scenario 3: fashion prompt", test_scenario_3_fashion_prompt),
        ("Scenario 4: upscale prompt", test_scenario_4_upscale_prompt),
        ("Scenario 5: inpaint face prompt", test_scenario_5_inpaint_face_prompt),
        ("Scenario 6: ambiguous prompt", test_scenario_6_ambiguous_prompt),
        ("Scenario 7: full integration", test_scenario_7_full_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in scenarios:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {name} FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_scenarios()
    exit(0 if success else 1)
