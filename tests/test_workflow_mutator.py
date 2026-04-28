"""Tests for workflow mutation scenarios."""

import json
import pytest
from pathlib import Path

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelectionResult
from app.workflows.node_contracts import SDXL_CONTRACTS
from app.workflows.workflow_mutator import MutationError, WorkflowMutator
from app.workflows.workflow_types import TaskType


def load_template_workflow() -> dict:
    """Load the SDXL template workflow for testing."""
    template_path = Path(__file__).parent.parent / "data" / "workflows" / "sdxl_txt2img_template.json"
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
        routing_source="test",
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
        enable_judging=False,
        enable_retry_loop=False,
    )


# Scenario 1: Portrait mutation
def test_scenario_1_portrait_mutation():
    """Test portrait mutation with cinematic prompt."""
    mutator = WorkflowMutator()
    workflow = load_template_workflow()
    
    execution_plan = build_test_execution_plan(
        TaskType.PORTRAIT_TXT2IMG,
        user_prompt="cinematic portrait of a realistic woman",
        resolved_inputs={
            "prompt": "cinematic portrait of a realistic woman",
            "negative_prompt": None,
            "width": None,
            "height": None,
            "steps": None,
            "cfg": None,
            "seed": None,
            "checkpoint": None,
            "prefix": None,
        },
    )
    
    mutation_result = mutator.apply_plan(workflow, execution_plan)
    
    # Verify mutation
    assert mutation_result.workflow_id == "test_workflow"
    assert "6" in mutation_result.mutated_nodes  # positive prompt
    assert "7" in mutation_result.mutated_nodes  # negative prompt
    assert "5" in mutation_result.mutated_nodes  # resolution
    assert "3" in mutation_result.mutated_nodes  # sampler settings
    assert "9" in mutation_result.mutated_nodes  # filename prefix
    
    # Verify applied changes
    assert "positive_prompt" in mutation_result.applied_changes
    assert "negative_prompt" in mutation_result.applied_changes
    assert "width" in mutation_result.applied_changes
    assert "height" in mutation_result.applied_changes
    assert mutation_result.applied_changes["width"] == 1024
    assert mutation_result.applied_changes["height"] == 1024
    assert "filename_prefix" in mutation_result.applied_changes
    assert "portrait" in mutation_result.applied_changes["filename_prefix"]
    
    # Verify workflow was actually mutated
    assert workflow["6"]["inputs"]["text"] == "cinematic portrait of a realistic woman"
    assert "plastic skin" in workflow["7"]["inputs"]["text"]  # portrait-specific negative
    assert workflow["5"]["inputs"]["width"] == 1024
    assert workflow["5"]["inputs"]["height"] == 1024
    assert workflow["9"]["inputs"]["filename_prefix"] == "agent/portrait"
    
    print("Scenario 1 (portrait mutation): PASS")


# Scenario 2: Product mutation
def test_scenario_2_product_mutation():
    """Test product mutation with luxury product shot."""
    mutator = WorkflowMutator()
    workflow = load_template_workflow()
    
    execution_plan = build_test_execution_plan(
        TaskType.PRODUCT_TXT2IMG,
        user_prompt="luxury product shot",
        resolved_inputs={
            "prompt": "luxury product shot",
            "negative_prompt": None,
            "width": None,
            "height": None,
            "steps": None,
            "cfg": None,
            "seed": None,
            "checkpoint": None,
            "prefix": None,
        },
    )
    
    mutation_result = mutator.apply_plan(workflow, execution_plan)
    
    # Verify mutation
    assert mutation_result.workflow_id == "test_workflow"
    assert "6" in mutation_result.mutated_nodes
    assert "7" in mutation_result.mutated_nodes
    assert "5" in mutation_result.mutated_nodes
    assert "3" in mutation_result.mutated_nodes
    assert "9" in mutation_result.mutated_nodes
    
    # Verify product-specific settings
    assert mutation_result.applied_changes["width"] == 1024
    assert mutation_result.applied_changes["height"] == 1024
    assert mutation_result.applied_changes["steps"] == 25
    assert mutation_result.applied_changes["cfg"] == 7.0
    assert "product" in mutation_result.applied_changes["filename_prefix"]
    
    # Verify workflow was actually mutated
    assert workflow["6"]["inputs"]["text"] == "luxury product shot"
    assert "messy background" in workflow["7"]["inputs"]["text"]  # product-specific negative
    assert workflow["3"]["inputs"]["steps"] == 25
    assert workflow["3"]["inputs"]["cfg"] == 7.0
    assert workflow["9"]["inputs"]["filename_prefix"] == "agent/product"
    
    print("Scenario 2 (product mutation): PASS")


# Scenario 3: Fashion mutation
def test_scenario_3_fashion_mutation():
    """Test fashion mutation with editorial runway look."""
    mutator = WorkflowMutator()
    workflow = load_template_workflow()
    
    execution_plan = build_test_execution_plan(
        TaskType.FASHION_TXT2IMG,
        user_prompt="editorial runway premium studio look",
        resolved_inputs={
            "prompt": "editorial runway premium studio look",
            "negative_prompt": None,
            "width": None,
            "height": None,
            "steps": None,
            "cfg": None,
            "seed": None,
            "checkpoint": None,
            "prefix": None,
        },
    )
    
    mutation_result = mutator.apply_plan(workflow, execution_plan)
    
    # Verify mutation
    assert mutation_result.workflow_id == "test_workflow"
    assert "6" in mutation_result.mutated_nodes
    assert "7" in mutation_result.mutated_nodes
    assert "5" in mutation_result.mutated_nodes
    assert "3" in mutation_result.mutated_nodes
    assert "9" in mutation_result.mutated_nodes
    
    # Verify fashion-specific settings
    assert mutation_result.applied_changes["width"] == 1024
    assert mutation_result.applied_changes["height"] == 1536  # portrait orientation
    assert mutation_result.applied_changes["steps"] == 35
    assert mutation_result.applied_changes["cfg"] == 6.5
    assert "fashion" in mutation_result.applied_changes["filename_prefix"]
    
    # Verify workflow was actually mutated
    assert workflow["6"]["inputs"]["text"] == "editorial runway premium studio look"
    assert "cluttered" in workflow["7"]["inputs"]["text"]  # fashion-specific negative
    assert workflow["5"]["inputs"]["width"] == 1024
    assert workflow["5"]["inputs"]["height"] == 1536
    assert workflow["3"]["inputs"]["steps"] == 35
    assert workflow["9"]["inputs"]["filename_prefix"] == "agent/fashion"
    
    print("Scenario 3 (fashion mutation): PASS")


# Scenario 4: Missing mutable node (controlled failure)
def test_scenario_4_missing_mutable_node():
    """Test controlled failure when a required mutable node is missing."""
    mutator = WorkflowMutator()
    
    # Create a workflow missing node 3 (KSampler)
    workflow = load_template_workflow()
    del workflow["3"]
    
    execution_plan = build_test_execution_plan(
        TaskType.PORTRAIT_TXT2IMG,
        user_prompt="test prompt",
    )
    
    # Should raise MutationError with clear message
    try:
        mutator.apply_plan(workflow, execution_plan)
        assert False, "Expected MutationError to be raised"
    except MutationError as e:
        assert "Required mutable node '3' not found" in e.message
        assert e.workflow_id == "test_workflow"
        assert e.node_id == "3"
        print(f"Scenario 4 (missing mutable node): PASS - {e.message}")


# Scenario 4b: Class type mismatch (controlled failure)
def test_scenario_4b_class_type_mismatch():
    """Test controlled failure when node class_type doesn't match contract."""
    mutator = WorkflowMutator()
    
    # Create a workflow with wrong class_type for node 3
    workflow = load_template_workflow()
    workflow["3"]["class_type"] = "WrongNodeType"
    
    execution_plan = build_test_execution_plan(
        TaskType.PORTRAIT_TXT2IMG,
        user_prompt="test prompt",
    )
    
    # Should raise MutationError with clear message
    try:
        mutator.apply_plan(workflow, execution_plan)
        assert False, "Expected MutationError to be raised"
    except MutationError as e:
        assert "Expected class_type 'KSampler'" in e.message
        assert e.workflow_id == "test_workflow"
        assert e.node_id == "3"
        print(f"Scenario 4b (class type mismatch): PASS - {e.message}")


# Scenario 5: Full integration test (requires actual agent service)
def test_scenario_5_full_integration():
    """Test full integration with workflow agent service.
    
    This is a simplified integration test that verifies the mutation layer
    works correctly with the execution plan structure.
    """
    mutator = WorkflowMutator()
    workflow = load_template_workflow()
    
    # Build a realistic execution plan
    task_selection = TaskSelectionResult(
        task_type=TaskType.CINEMATIC_TXT2IMG,
        confidence=0.95,
        reason="Detected cinematic keywords",
        routing_source="rules",
    )
    
    builder = ExecutionPlanBuilder()
    execution_plan = builder.build(
        user_prompt="cinematic wide shot of a cityscape at sunset",
        task_selection=task_selection,
        workflow_id="cinematic_sdxl_v1",
        workflow_path="data/workflows/sdxl_txt2img_template.json",
        preset_name="cinematic",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={
            "prompt": "cinematic wide shot of a cityscape at sunset",
            "negative_prompt": None,
            "width": None,
            "height": None,
            "steps": None,
            "cfg": None,
            "seed": 12345,
            "checkpoint": None,
            "prefix": None,
        },
        enable_judging=True,
        enable_retry_loop=True,
    )
    
    # Apply mutation
    mutation_result = mutator.apply_plan(workflow, execution_plan)
    
    # Verify execution_plan structure
    assert execution_plan.task_type == TaskType.CINEMATIC_TXT2IMG
    assert execution_plan.workflow_id == "cinematic_sdxl_v1"
    assert execution_plan.enable_judging == True
    assert execution_plan.enable_retry_loop == True
    assert execution_plan.resolved_inputs["seed"] == 12345
    
    # Verify mutation_result structure
    assert mutation_result.workflow_id == "cinematic_sdxl_v1"
    assert len(mutation_result.mutated_nodes) > 0
    assert "positive_prompt" in mutation_result.applied_changes
    assert "negative_prompt" in mutation_result.applied_changes
    
    # Verify cinematic-specific settings were applied
    assert mutation_result.applied_changes["width"] == 1344
    assert mutation_result.applied_changes["height"] == 768
    assert mutation_result.applied_changes["cfg"] == 6.5
    assert "cinematic" in mutation_result.applied_changes["filename_prefix"]
    
    # Verify seed override was applied
    assert workflow["3"]["inputs"]["seed"] == 12345
    
    # Verify mutation_report structure matches expected format
    report_dict = mutation_result.to_dict()
    assert "workflow_id" in report_dict
    assert "mutated_nodes" in report_dict
    assert "applied_changes" in report_dict
    assert "notes" in report_dict
    
    print("Scenario 5 (full integration): PASS")


# Scenario 5c: Checkpoint mutation
def test_scenario_5c_checkpoint_mutation():
    """Test that checkpoint is included in mutation_report when set."""
    mutator = WorkflowMutator()
    workflow = load_template_workflow()
    
    execution_plan = build_test_execution_plan(
        TaskType.PORTRAIT_TXT2IMG,
        user_prompt="test prompt",
        resolved_inputs={
            "prompt": "test prompt",
            "negative_prompt": None,
            "width": None,
            "height": None,
            "steps": None,
            "cfg": None,
            "seed": None,
            "checkpoint": "custom_checkpoint.safetensors",  # Custom checkpoint
            "prefix": None,
        },
    )
    
    mutation_result = mutator.apply_plan(workflow, execution_plan)
    
    # Verify checkpoint is in applied_changes
    assert "checkpoint" in mutation_result.applied_changes
    assert mutation_result.applied_changes["checkpoint"] == "custom_checkpoint.safetensors"
    assert "4" in mutation_result.mutated_nodes
    
    # Verify workflow was actually mutated
    assert workflow["4"]["inputs"]["ckpt_name"] == "custom_checkpoint.safetensors"
    
    print("Scenario 5c (checkpoint mutation): PASS")


if __name__ == "__main__":
    print("Running workflow mutation scenarios...")
    print()
    
    try:
        test_scenario_1_portrait_mutation()
    except Exception as e:
        print(f"Scenario 1 (portrait mutation): FAIL - {e}")
    
    try:
        test_scenario_2_product_mutation()
    except Exception as e:
        print(f"Scenario 2 (product mutation): FAIL - {e}")
    
    try:
        test_scenario_3_fashion_mutation()
    except Exception as e:
        print(f"Scenario 3 (fashion mutation): FAIL - {e}")
    
    try:
        test_scenario_4_missing_mutable_node()
    except Exception as e:
        print(f"Scenario 4 (missing mutable node): FAIL - {e}")
    
    try:
        test_scenario_4b_class_type_mismatch()
    except Exception as e:
        print(f"Scenario 4b (class type mismatch): FAIL - {e}")
    
    try:
        test_scenario_5_full_integration()
    except Exception as e:
        print(f"Scenario 5 (full integration): FAIL - {e}")
    
    try:
        test_scenario_5c_checkpoint_mutation()
    except Exception as e:
        print(f"Scenario 5c (checkpoint mutation): FAIL - {e}")
    
    print()
    print("All mutation scenario tests completed.")
