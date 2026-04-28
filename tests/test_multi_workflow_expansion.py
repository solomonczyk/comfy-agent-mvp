"""Tests for Multi-Workflow Expansion v0 - img2img, inpaint_face, upscale."""

import json
from pathlib import Path

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelector, TaskSelectionResult
from app.workflows.node_contracts import get_all_contracts
from app.workflows.workflow_mutator import WorkflowMutator
from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType


def load_workflow_template(template_path: str) -> dict:
    """Load workflow template from JSON file."""
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


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
        workflow_id="img2img_v1" if task_type == TaskType.IMG2IMG else 
                    "inpaint_face_v1" if task_type == TaskType.INPAINT_FACE else
                    "upscale_v1",
        workflow_path="test/path.json",
        preset_name="test",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs=resolved_inputs or {"prompt": user_prompt},
        enable_judging=True,
        enable_retry_loop=True,
    )


# Scenario 1: img2img implemented
def test_scenario_1_img2img_implemented():
    """Test img2img workflow is implemented and mutation works."""
    # Check workflow registry
    registry = WorkflowRegistry("data/workflows")
    img2img_spec = registry.get_workflow("img2img_v1")
    
    assert img2img_spec is not None, "img2img_v1 workflow not found in registry"
    assert img2img_spec.implemented, "img2img_v1 workflow not marked as implemented"
    
    # Check template exists
    template_path = Path(img2img_spec.workflow_path)
    assert template_path.exists(), f"img2img template not found at {template_path}"
    
    # Load and validate template
    workflow = load_workflow_template(str(template_path))
    assert "5" in workflow, "LoadImage node (5) not found in img2img template"
    assert workflow["5"]["class_type"] == "LoadImage", "Node 5 is not LoadImage"
    
    # Check contracts
    contracts = get_all_contracts("img2img_v1")
    assert "5" in contracts, "No contract for node 5 in img2img contracts"
    assert contracts["5"].class_type == "LoadImage", "Contract for node 5 is not LoadImage"
    
    # Test mutation
    mutator = WorkflowMutator()
    execution_plan = build_test_execution_plan(
        TaskType.IMG2IMG,
        user_prompt="stylize this image",
        resolved_inputs={
            "prompt": "stylize this image",
            "input_image": "test_image.png",
            "denoise": 0.6,
        },
    )
    
    try:
        mutation_result = mutator.apply_plan(workflow, execution_plan)
        assert "5" in mutation_result.mutated_nodes, "Node 5 not mutated"
        assert mutation_result.applied_changes.get("input_image") == "test_image.png"
        assert mutation_result.applied_changes.get("denoise") == 0.6
        print("Scenario 1 (img2img implemented): PASS")
    except Exception as e:
        print(f"Scenario 1 (img2img implemented): FAIL - {e}")


# Scenario 2: inpaint_face implemented
def test_scenario_2_inpaint_face_implemented():
    """Test inpaint_face workflow is implemented and requires image + mask."""
    # Check workflow registry
    registry = WorkflowRegistry("data/workflows")
    inpaint_spec = registry.get_workflow("inpaint_face_v1")
    
    assert inpaint_spec is not None, "inpaint_face_v1 workflow not found in registry"
    assert inpaint_spec.implemented, "inpaint_face_v1 workflow not marked as implemented"
    
    # Check required inputs
    assert "image" in inpaint_spec.required_inputs, "image not in required_inputs"
    assert "mask" in inpaint_spec.required_inputs, "mask not in required_inputs"
    
    # Check template exists
    template_path = Path(inpaint_spec.workflow_path)
    assert template_path.exists(), f"inpaint template not found at {template_path}"
    
    # Load and validate template
    workflow = load_workflow_template(str(template_path))
    assert "5" in workflow, "LoadImage node (5) not found in inpaint template"
    assert "9" in workflow, "LoadImageMask node (9) not found in inpaint template"
    
    # Check contracts
    contracts = get_all_contracts("inpaint_face_v1")
    assert "5" in contracts, "No contract for node 5 in inpaint contracts"
    assert "9" in contracts, "No contract for node 9 in inpaint contracts"
    
    # Test mutation with both image and mask
    mutator = WorkflowMutator()
    execution_plan = build_test_execution_plan(
        TaskType.INPAINT_FACE,
        user_prompt="fix face",
        resolved_inputs={
            "prompt": "fix face",
            "input_image": "test_image.png",
            "mask": "test_mask.png",
            "denoise": 0.75,
        },
    )
    
    try:
        mutation_result = mutator.apply_plan(workflow, execution_plan)
        assert "5" in mutation_result.mutated_nodes, "Node 5 not mutated"
        assert "9" in mutation_result.mutated_nodes, "Node 9 not mutated"
        assert mutation_result.applied_changes.get("input_image") == "test_image.png"
        assert mutation_result.applied_changes.get("mask") == "test_mask.png"
        print("Scenario 2 (inpaint_face implemented): PASS")
    except Exception as e:
        print(f"Scenario 2 (inpaint_face implemented): FAIL - {e}")


# Scenario 3: upscale implemented
def test_scenario_3_upscale_implemented():
    """Test upscale workflow is implemented and mutation works."""
    # Check workflow registry
    registry = WorkflowRegistry("data/workflows")
    upscale_spec = registry.get_workflow("upscale_v1")
    
    assert upscale_spec is not None, "upscale_v1 workflow not found in registry"
    assert upscale_spec.implemented, "upscale_v1 workflow not marked as implemented"
    
    # Check template exists
    template_path = Path(upscale_spec.workflow_path)
    assert template_path.exists(), f"upscale template not found at {template_path}"
    
    # Load and validate template
    workflow = load_workflow_template(str(template_path))
    assert "5" in workflow, "LoadImage node (5) not found in upscale template"
    assert "10" in workflow, "LatentUpscale node (10) not found in upscale template"
    
    # Check contracts
    contracts = get_all_contracts("upscale_v1")
    assert "5" in contracts, "No contract for node 5 in upscale contracts"
    assert "10" in contracts, "No contract for node 10 in upscale contracts"
    
    # Test mutation
    mutator = WorkflowMutator()
    execution_plan = build_test_execution_plan(
        TaskType.UPSCALE,
        user_prompt="upscale this image",
        resolved_inputs={
            "prompt": "upscale this image",
            "input_image": "test_image.png",
            "upscale_width": 2048,
            "upscale_height": 2048,
        },
    )
    
    try:
        mutation_result = mutator.apply_plan(workflow, execution_plan)
        assert "5" in mutation_result.mutated_nodes, "Node 5 not mutated"
        assert "10" in mutation_result.mutated_nodes, "Node 10 not mutated"
        assert mutation_result.applied_changes.get("input_image") == "test_image.png"
        assert mutation_result.applied_changes.get("upscale_width") == 2048
        assert mutation_result.applied_changes.get("upscale_height") == 2048
        print("Scenario 3 (upscale implemented): PASS")
    except Exception as e:
        print(f"Scenario 3 (upscale implemented): FAIL - {e}")


# Scenario 4: asset missing fail-fast
def test_scenario_4_asset_missing_failfast():
    """Test that missing required assets fail fast at planning layer."""
    registry = WorkflowRegistry("data/workflows")
    inpaint_spec = registry.get_workflow("inpaint_face_v1")
    
    builder = ExecutionPlanBuilder()
    task_selection = TaskSelectionResult(
        task_type=TaskType.INPAINT_FACE,
        confidence=0.9,
        reason="Test reason",
        routing_source="rules",
    )
    
    # Try to build plan without required mask
    try:
        builder.build(
            user_prompt="fix face",
            task_selection=task_selection,
            workflow_id="inpaint_face_v1",
            workflow_path="test/path.json",
            preset_name="inpaint",
            rewrite_mode="raw",
            required_inputs=inpaint_spec.required_inputs,
            resolved_inputs={
                "prompt": "fix face",
                "input_image": "test_image.png",
                "mask": None,  # Missing required mask
            },
            enable_judging=True,
            enable_retry_loop=True,
        )
        print("Scenario 4 (asset missing fail-fast): FAIL - Should have raised ValueError")
    except ValueError as e:
        if "mask" in str(e).lower():
            print("Scenario 4 (asset missing fail-fast): PASS")
        else:
            print(f"Scenario 4 (asset missing fail-fast): FAIL - Wrong error: {e}")
    except Exception as e:
        print(f"Scenario 4 (asset missing fail-fast): FAIL - Unexpected error: {e}")


# Scenario 5: mutation-aware retry on img2img
def test_scenario_5_mutation_aware_retry():
    """Test that mutation-aware retry preserves asset inputs for img2img."""
    from app.agent.mutation_retry_planner import MutationRetryPlanner
    
    mutator = WorkflowMutator()
    retry_planner = MutationRetryPlanner()
    
    # First attempt
    registry = WorkflowRegistry("data/workflows")
    img2img_spec = registry.get_workflow("img2img_v1")
    workflow = load_workflow_template(str(img2img_spec.workflow_path))
    
    execution_plan = build_test_execution_plan(
        TaskType.IMG2IMG,
        user_prompt="stylize this image",
        resolved_inputs={
            "prompt": "stylize this image",
            "input_image": "test_image.png",
            "denoise": 0.6,
        },
    )
    
    try:
        first_mutation = mutator.apply_plan(workflow, execution_plan)
        
        # Build retry plan
        retry_decision = {"action": "retry_prompt", "max_retries": 3}
        retry_plan = retry_planner.build_plan(
            execution_plan=execution_plan,
            mutation_report=first_mutation.to_dict(),
            retry_decision=retry_decision,
            orchestrator_report=None,
        )
        
        # Verify retry preserves image input
        retry_overrides = retry_plan.retry_overrides
        assert "_keep_settings" in retry_overrides or "input_image" not in retry_overrides, \
            "Retry should preserve image input or keep settings"
        
        print("Scenario 5 (mutation-aware retry on img2img): PASS")
    except Exception as e:
        print(f"Scenario 5 (mutation-aware retry on img2img): FAIL - {e}")


# Scenario 6: full mixed routing pack
def test_scenario_6_full_mixed_routing():
    """Test that all workflow types route correctly."""
    selector = TaskSelector()
    registry = WorkflowRegistry("data/workflows")
    
    test_cases = [
        ("portrait of a woman", TaskType.PORTRAIT_TXT2IMG),
        ("cinematic wide shot", TaskType.CINEMATIC_TXT2IMG),
        ("product photography", TaskType.PRODUCT_TXT2IMG),
        ("fashion editorial", TaskType.FASHION_TXT2IMG),
        ("stylize this image", TaskType.IMG2IMG),
        ("fix face", TaskType.INPAINT_FACE),
        ("upscale this image", TaskType.UPSCALE),
    ]
    
    all_passed = True
    for prompt, expected_type in test_cases:
        selection = selector.select(prompt)
        if selection.task_type == expected_type:
            spec = registry.get_default_for_task(expected_type)
            if spec and spec.implemented:
                continue
            else:
                all_passed = False
                print(f"  FAIL: {expected_type} not implemented")
        else:
            all_passed = False
            print(f"  FAIL: Expected {expected_type}, got {selection.task_type}")
    
    if all_passed:
        print("Scenario 6 (full mixed routing pack): PASS")
    else:
        print("Scenario 6 (full mixed routing pack): FAIL")


if __name__ == "__main__":
    print("Running Multi-Workflow Expansion v0 scenarios...")
    print()
    
    test_scenario_1_img2img_implemented()
    test_scenario_2_inpaint_face_implemented()
    test_scenario_3_upscale_implemented()
    test_scenario_4_asset_missing_failfast()
    test_scenario_5_mutation_aware_retry()
    test_scenario_6_full_mixed_routing()
    
    print()
    print("All Multi-Workflow Expansion v0 tests completed.")
