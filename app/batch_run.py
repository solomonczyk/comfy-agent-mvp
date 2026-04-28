"""Batch-run CLI entrypoint for KT-4 batch orchestration."""
import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.agent_run import run_agent
from app.assets.paths import ASSET_PATHS, ensure_asset_dirs
from app.batch.batch_orchestrator import BatchOrchestrator
from app.batch.spec_loader import SpecLoader


BATCH_SPECS_DIR = ASSET_PATHS.batch_specs
BATCHES_DIR = ASSET_PATHS.batches
MANIFESTS_DIR = ASSET_PATHS.manifests


async def job_executor(
    mode: str,
    prompt: str,
    settings: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Execute a single job using the existing agent_run logic.
    
    Args:
        mode: Generation mode
        prompt: User prompt
        settings: Job-specific settings (width, height, steps, etc.)
        output_dir: Output directory for this job
        
    Returns:
        Job result dictionary
    """
    # Pass settings as canonical_recipe overrides if provided
    canonical_recipe = settings if settings else None

    result = await run_agent(
        prompt=prompt,
        mode=mode,
        enable_judging=False,
        enable_retry_loop=False,
        canonical_recipe=canonical_recipe,
        status_callback=None,  # Headless - no status printing
    )
    return result


async def run_batch(spec_path: Path) -> dict[str, Any]:
    """Run a batch of jobs.
    
    Args:
        spec_path: Path to batch spec JSON file
        
    Returns:
        Batch result dictionary
    """
    # Ensure KT-5 asset dirs exist
    ensure_asset_dirs()

    # Load batch spec
    spec = SpecLoader.load(spec_path)
    print(f"Loaded batch spec: {spec.batch_id} with {len(spec.jobs)} jobs")
    
    # Create orchestrator
    orchestrator = BatchOrchestrator(
        batches_dir=BATCHES_DIR,
        manifests_dir=MANIFESTS_DIR,
        job_executor=job_executor,
    )
    
    # Execute batch
    print(f"Starting batch execution...")
    result = await orchestrator.run_batch(spec)
    
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Batch-run CLI for headless batch execution",
    )
    parser.add_argument(
        "--spec",
        required=False,
        help="Path to batch spec JSON file (auto-detects if not provided)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print final result as JSON",
    )
    return parser


async def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Seam-fix #7: Auto-detect batch spec if not provided
    if not args.spec:
        if BATCH_SPECS_DIR.exists():
            # List available specs
            spec_files = list(BATCH_SPECS_DIR.glob("*.json"))
            if spec_files:
                print("Available batch specs:")
                for i, spec_file in enumerate(spec_files, 1):
                    print(f"  {i}. {spec_file.name}")
                # Use the first spec (or could use latest by modification time)
                spec_path = spec_files[0]
                print(f"Auto-detected batch spec: {spec_path.name}")
            else:
                print(f"Error: no batch spec files found in {BATCH_SPECS_DIR}")
                raise SystemExit(1)
        else:
            print(f"Error: batch specs directory not found: {BATCH_SPECS_DIR}")
            raise SystemExit(1)
    else:
        spec_path = Path(args.spec)

    if not spec_path.exists():
        print(f"Error: Batch spec not found: {spec_path}")
        raise SystemExit(1)
    
    try:
        result = await run_batch(spec_path)
    except Exception as e:
        print(f"Error during batch execution: {e}")
        raise
    
    # Print results
    print("\n" + "="*60)
    print("BATCH EXECUTION RESULT")
    print("="*60)
    print(f"Batch ID: {result['batch_id']}")
    print(f"Status: {result['status'].upper()}")
    print(f"Total Jobs: {result['total_jobs']}")
    print(f"Completed: {result['completed_jobs']}")
    print(f"Failed: {result['failed_jobs']}")
    print(f"Output Directory: {result['output_dir']}")
    print(f"Manifest: {result['manifest_path']}")
    print("="*60 + "\n")
    
    if args.print_result_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with error code if any jobs failed
    if result["failed_jobs"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
