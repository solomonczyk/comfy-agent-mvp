"""
Test Recipe Override Fix - Verify canonical recipe wins over preset defaults

This script tests the Workflow Recipe Override Repair v1 fix by:
1. Creating an ExecutionPlan with canonical_recipe
2. Calling WorkflowMutator.apply_plan()
3. Verifying that mutated settings match canonical recipe
4. Testing fail-fast when there's a mismatch
"""
import json
from pathlib import Path

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelectionResult
from app.workflows.workflow_mutator import WorkflowMutator
from app.workflows.workflow_types import TaskType

PROJECT_ROOT = Path(__file__).resolve().parents[0]
WORKFLOW_PATH = PROJECT_ROOT / "data" / "workflows" / "sdxl_txt2img_template.json"

# CANONICAL RECIPE (should win over preset defaults)
CANONICAL_RECIPE = {
    "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
    "sampler_name": "euler",
    "scheduler": "karras",
    "steps": 30,
    "cfg": 6.0,
    "width": 1024,
    "height": 1024,
    "seed": 123456789,
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, extra fingers, duplicate, distorted features, oversaturated",
    "filename_prefix": "portrait_comparison/test",
}

# PRESET DEFAULTS (from sdxl_presets.json - should be overridden)
PRESET_DEFAULTS = {
    "sampler_name": "dpmpp_2m",
    "scheduler": "karras",
    "steps": 30,
    "cfg": 6.0,
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting",
    "filename_prefix": "agent/portrait",
}

def test_canonical_recipe_precedence():
    """Test that canonical recipe wins over preset defaults."""
    print("=== Test 1: Canonical Recipe Precedence ===")
    
    mutator = WorkflowMutator()
    
    # Create task selection
    task_selection = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=1.0,
        reason="Test reason",
        routing_source="test",
    )
    
    # Create execution plan WITH canonical recipe
    builder = ExecutionPlanBuilder()
    execution_plan = builder.build(
        user_prompt="test prompt",
        task_selection=task_selection,
        workflow_id="portrait_sdxl_v1",
        workflow_path=str(WORKFLOW_PATH),
        preset_name="portrait",  # This has preset defaults
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={"prompt": "test prompt"},
        enable_judging=False,
        enable_retry_loop=False,
        canonical_recipe=CANONICAL_RECIPE,  # This should WIN
    )
    
    # Load and mutate workflow
    template_workflow = mutator.load_template(WORKFLOW_PATH)
    mutation_result = mutator.apply_plan(template_workflow, execution_plan)
    
    print(f"Mutated Nodes: {mutation_result.mutated_nodes}")
    print(f"Applied Changes: {mutation_result.applied_changes}")
    print()
    
    # Verify canonical recipe was applied
    failures = []
    for key, expected_value in CANONICAL_RECIPE.items():
        actual_value = mutation_result.applied_changes.get(key)
        if actual_value != expected_value:
            failures.append({
                "parameter": key,
                "expected": expected_value,
                "actual": actual_value
            })
    
    if failures:
        print("✗ FAIL: Canonical recipe was not applied correctly")
        print(f"Failures: {json.dumps(failures, indent=2)}")
        return False
    else:
        print("✓ PASS: Canonical recipe was applied correctly")
        return True

def test_fail_fast_on_mismatch():
    """Test that fail-fast triggers when canonical recipe is not applied."""
    print("\n=== Test 2: Fail-Fast on Mismatch ===")
    
    mutator = WorkflowMutator()
    
    # Create task selection
    task_selection = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=1.0,
        reason="Test reason",
        routing_source="test",
    )
    
    # Create execution plan with INCOMPLETE canonical recipe (missing sampler_name)
    incomplete_recipe = CANONICAL_RECIPE.copy()
    incomplete_recipe.pop("sampler_name")  # Remove sampler_name to test fail-fast
    
    builder = ExecutionPlanBuilder()
    execution_plan = builder.build(
        user_prompt="test prompt",
        task_selection=task_selection,
        workflow_id="portrait_sdxl_v1",
        workflow_path=str(WORKFLOW_PATH),
        preset_name="portrait",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={"prompt": "test prompt"},
        enable_judging=False,
        enable_retry_loop=False,
        canonical_recipe=incomplete_recipe,
    )
    
    # Load workflow
    template_workflow = mutator.load_template(WORKFLOW_PATH)
    
    # This should NOT fail-fast because sampler_name is not in canonical_recipe
    # So preset default (dpmpp_2m) should be applied
    try:
        mutation_result = mutator.apply_plan(template_workflow, execution_plan)
        actual_sampler = mutation_result.applied_changes.get("sampler_name")
        if actual_sampler == "dpmpp_2m":
            print("✓ PASS: Preset default applied when canonical recipe doesn't specify field")
            return True
        else:
            print(f"✗ FAIL: Unexpected sampler_name: {actual_sampler}")
            return False
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")
        return False

def test_explicit_mismatch_fail_fast():
    """Test fail-fast when we explicitly set a mismatch in overrides."""
    print("\n=== Test 3: Explicit Mismatch Fail-Fast ===")
    
    mutator = WorkflowMutator()
    
    # Create task selection
    task_selection = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=1.0,
        reason="Test reason",
        routing_source="test",
    )
    
    # Create execution plan with canonical recipe
    builder = ExecutionPlanBuilder()
    execution_plan = builder.build(
        user_prompt="test prompt",
        task_selection=task_selection,
        workflow_id="portrait_sdxl_v1",
        workflow_path=str(WORKFLOW_PATH),
        preset_name="portrait",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={
            "prompt": "test prompt",
            "sampler_name": "wrong_sampler",  # This should be overridden by canonical_recipe
        },
        enable_judging=False,
        enable_retry_loop=False,
        canonical_recipe=CANONICAL_RECIPE,
    )
    
    # Load workflow
    template_workflow = mutator.load_template(WORKFLOW_PATH)
    
    # Apply with overrides - canonical_recipe should still win
    try:
        mutation_result = mutator.apply_plan(
            template_workflow, 
            execution_plan,
            overrides={"sampler_name": "wrong_sampler"}  # This should be overridden
        )
        actual_sampler = mutation_result.applied_changes.get("sampler_name")
        if actual_sampler == "euler":  # Canonical recipe value
            print("✓ PASS: Canonical recipe won over overrides")
            return True
        else:
            print(f"✗ FAIL: Canonical recipe did not win. sampler_name={actual_sampler}")
            return False
    except Exception as e:
        print(f"✗ FAIL: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== Workflow Recipe Override Repair v1 - Test Suite ===")
    print()
    
    results = []
    results.append(("Canonical Recipe Precedence", test_canonical_recipe_precedence()))
    results.append(("Fail-Fast on Mismatch", test_fail_fast_on_mismatch()))
    results.append(("Explicit Mismatch Fail-Fast", test_explicit_mismatch_fail_fast()))
    
    print("\n=== Test Summary ===")
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\n=== FINAL VERDICT: {'PASS' if all_passed else 'FAIL'} ===")
