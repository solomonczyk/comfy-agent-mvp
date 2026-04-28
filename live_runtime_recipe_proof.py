"""
Live Runtime Recipe Proof - Tests recipe parity through actual runtime path

This script uses the live runtime path (WorkflowAgentService) instead of
standalone SDXLAgent to prove recipe enforcement in production.
"""
import asyncio
from datetime import datetime
from pathlib import Path
import json
from app.agent_run import run_agent

PROJECT_ROOT = Path(__file__).resolve().parents[0]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "live_runtime_recipe_proof"

# CANONICAL RECIPE (fixed, not randomized)
CANONICAL_RECIPE = {
    "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
    "sampler_name": "euler",
    "scheduler": "karras",
    "steps": 30,
    "cfg": 6.0,
    "width": 1024,
    "height": 1024,
    "seed": 123456789,  # Fixed seed, not randomized
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, extra fingers, duplicate, distorted features, oversaturated",
}

CANONICAL_PROMPT = "realistic female portrait, natural skin texture, detailed eyes, soft natural light, high detail, professional photography"

async def main():
    print("=== Live Runtime Recipe Proof ===")
    print("Testing recipe parity through live runtime path (WorkflowAgentService)")
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Canonical Recipe Settings:")
    for key, value in CANONICAL_RECIPE.items():
        print(f"  {key}: {value}")
    print()
    
    print(f"Canonical Prompt: {CANONICAL_PROMPT}")
    print()
    
    # Run through live runtime path
    # Note: agent_run doesn't support direct setting of all recipe fields
    # We'll use mode=portrait and check what gets applied
    result = await run_agent(
        prompt=CANONICAL_PROMPT,
        mode="portrait",
        enable_judging=False,
        enable_retry_loop=False,
    )
    
    print("\n=== Live Runtime Result ===")
    print(f"Status: {result.get('status')}")
    print(f"Workflow ID: {result.get('execution_plan', {}).get('workflow_id')}")
    print(f"Task Type: {result.get('execution_plan', {}).get('task_type')}")
    print()
    
    # Check for recipe_validation in result
    if "recipe_validation" in result and result["recipe_validation"] is not None:
        print("✓ recipe_validation found in result")
        validation = result["recipe_validation"]
        print(f"  Passed: {validation.get('passed')}")
        print(f"  Failures: {validation.get('failures')}")
    else:
        print("✗ recipe_validation NOT found in result or is None")
        print("  This indicates the live runtime path lacks recipe enforcement")
    
    print()
    
    # Extract mutation report
    mutation_report = result.get("mutation_report")
    if mutation_report:
        print("=== Mutation Report ===")
        print(f"Workflow ID: {mutation_report.get('workflow_id')}")
        print(f"Mutated Nodes: {mutation_report.get('mutated_nodes')}")
        print(f"Applied Changes: {mutation_report.get('applied_changes')}")
        print()
    
    # Save full result for analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = OUTPUT_DIR / f"live_runtime_result_{timestamp}.json"
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Full result saved to: {result_path}")
    print()
    
    # Verdict
    if "recipe_validation" in result and result["recipe_validation"].get("passed"):
        print("=== FINAL VERDICT: PASS ===")
        print("Recipe enforcement is working in live runtime path")
    else:
        print("=== FINAL VERDICT: FAIL ===")
        print("Recipe enforcement is NOT working in live runtime path")
        print("Root cause: recipe_validation missing from live runtime result")

if __name__ == "__main__":
    asyncio.run(main())
