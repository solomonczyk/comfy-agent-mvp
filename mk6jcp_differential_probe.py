"""
MK-6J-CP: Control Baseline vs Batch Template Differential Probe v1

This script runs a differential probe to determine whether the execution pathology
is specific to the bounded batch template, rather than a generic ComfyUI running-state artifact.

Probes:
- Control probe: known-good single-image img2img route (img2img_v1)
- Batch probe: current bounded batch template route (img2img_batch_v1)

Both probes use identical conditions:
- Same clean queue conditions
- Same execution tracing
- Same reference input
- Same prompt family
- Same checkpoint / canonical recipe
- Same tracing / timeout instrumentation
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from app.comfy.comfy_client import ComfyClient
from app.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[0]
WORKFLOWS_DIR = PROJECT_ROOT / "data" / "workflows"
INPUT_IMAGE = PROJECT_ROOT / "test_input_image.png"


class ProbeDiagnostics:
    """Container for probe diagnostics."""
    
    def __init__(self, probe_name: str):
        self.probe_name = probe_name
        self.prompt_id: str | None = None
        self.entered_running: bool = False
        self.node_execution_trace: list[dict[str, Any]] = []
        self.progress_heartbeat_count: int = 0
        self.save_node_reached: bool = False
        self.output_seen: bool = False
        self.final_state: str = "unknown"
        self.abort_reason: str | None = None
        self.execution_time_seconds: float = 0
        self.queue_state_at_admission: dict[str, Any] = {}
        self.queue_state_at_completion: dict[str, Any] = {}
        self.history_data: dict[str, Any] = {}
        self.images_found: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "probe_name": self.probe_name,
            "prompt_id": self.prompt_id,
            "entered_running": self.entered_running,
            "node_execution_trace": self.node_execution_trace,
            "progress_heartbeat_count": self.progress_heartbeat_count,
            "save_node_reached": self.save_node_reached,
            "output_seen": self.output_seen,
            "final_state": self.final_state,
            "abort_reason": self.abort_reason,
            "execution_time_seconds": self.execution_time_seconds,
            "queue_state_at_admission": self.queue_state_at_admission,
            "queue_state_at_completion": self.queue_state_at_completion,
            "history_data": self.history_data,
            "images_found": self.images_found,
        }


async def clear_queue() -> dict[str, Any]:
    """Clear ComfyUI queue by interrupting running tasks."""
    print("\n=== CLEARING QUEUE ===")
    
    import httpx
    
    # Interrupt any running tasks
    url = f"{settings.comfy_base_url}/interrupt"
    
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(url)
        print(f"Interrupt response: {response.status_code}")
    
    # Check queue status after interrupt
    comfy_client = ComfyClient()
    queue = await comfy_client.get_queue()
    
    print(f"Queue after interrupt:")
    print(f"  Queue running: {len(queue.get('queue_running', []))} items")
    print(f"  Queue pending: {len(queue.get('queue_pending', []))} items")
    
    # If still stuck, try to clear via DELETE to /queue
    if queue.get('queue_running') or queue.get('queue_pending'):
        print("\nQueue still has items, attempting to clear...")
        clear_url = f"{settings.comfy_base_url}/queue"
        async with httpx.AsyncClient(timeout=settings.request_timeout) as http_client:
            try:
                response = await http_client.delete(clear_url)
                print(f"Clear queue response: {response.status_code}")
            except Exception as e:
                print(f"Clear queue failed: {e}")
        
        # Check queue again
        queue = await comfy_client.get_queue()
        print(f"\nQueue after clear attempt:")
        print(f"  Queue running: {len(queue.get('queue_running', []))} items")
        print(f"  Queue pending: {len(queue.get('queue_pending', []))} items")
    
    return queue


async def check_queue_clean() -> bool:
    """Check if queue is clean (no running or pending items)."""
    comfy_client = ComfyClient()
    queue = await comfy_client.get_queue()
    
    running_count = len(queue.get('queue_running', []))
    pending_count = len(queue.get('queue_pending', []))
    
    is_clean = running_count == 0 and pending_count == 0
    
    print(f"\nQueue clean check:")
    print(f"  Running: {running_count}")
    print(f"  Pending: {pending_count}")
    print(f"  Clean: {is_clean}")
    
    return is_clean


async def upload_input_image(image_path: Path) -> str:
    """Upload input image to ComfyUI."""
    print(f"\nUploading input image: {image_path}")
    
    comfy_client = ComfyClient()
    upload_result = await comfy_client.upload_image(image_path)
    
    image_name = upload_result.get("name", image_path.name)
    print(f"Uploaded as: {image_name}")
    
    return image_name


async def run_probe(
    workflow_path: Path,
    probe_name: str,
    input_image_name: str,
    timeout_seconds: int = 180,
) -> ProbeDiagnostics:
    """Run a single probe with full diagnostics."""
    print(f"\n{'='*60}")
    print(f"RUNNING PROBE: {probe_name}")
    print(f"{'='*60}")
    
    diagnostics = ProbeDiagnostics(probe_name)
    comfy_client = ComfyClient()
    
    # Load workflow
    print(f"Loading workflow: {workflow_path}")
    workflow = await comfy_client.load_workflow(workflow_path)
    
    # Update input image in workflow
    for node_id, node_data in workflow.items():
        if node_data.get("class_type") == "LoadImage":
            node_data["inputs"]["image"] = input_image_name
            print(f"Updated node {node_id} with input image: {input_image_name}")
    
    # Record queue state at admission
    queue_at_admission = await comfy_client.get_queue()
    diagnostics.queue_state_at_admission = {
        "queue_running": queue_at_admission.get("queue_running", []),
        "queue_pending": queue_at_admission.get("queue_pending", []),
    }
    
    # Queue the workflow
    print("Queuing workflow...")
    start_time = time.time()
    
    try:
        prompt_id = await comfy_client.queue_prompt(workflow)
        diagnostics.prompt_id = prompt_id
        print(f"Queued with prompt_id: {prompt_id}")
    except Exception as e:
        diagnostics.final_state = "failed"
        diagnostics.abort_reason = f"queue_prompt_failed: {str(e)}"
        diagnostics.execution_time_seconds = time.time() - start_time
        return diagnostics
    
    # Watch execution with WebSocket for progress tracking (with polling fallback)
    print("Watching execution progress...")
    
    def status_callback(status: str, payload: dict[str, Any] | None = None) -> None:
        """Status callback for tracking execution."""
        payload = payload or {}
        
        if status == "RUNNING":
            diagnostics.entered_running = True
            node_id = payload.get("node")
            diagnostics.progress_heartbeat_count += 1
            diagnostics.node_execution_trace.append({
                "event": "executing",
                "node_id": node_id,
                "timestamp": time.time() - start_time,
            })
            print(f"  [{diagnostics.progress_heartbeat_count}] Executing node: {node_id}")
            
            # Check if this is a SaveImage node
            if node_id:
                node_data = workflow.get(str(node_id), {})
                if node_data.get("class_type") == "SaveImage":
                    diagnostics.save_node_reached = True
                    print(f"  ✓ SaveImage node reached: {node_id}")
        
        elif status == "COMPLETED":
            images_found = payload.get("images_found", 0)
            diagnostics.images_found = images_found
            diagnostics.output_seen = images_found > 0
            print(f"  ✓ Images found: {images_found}")
        
        elif status == "FAILED":
            error = payload.get("error", "Unknown error")
            print(f"  ✗ Execution error: {error}")
        
        elif status == "RETRYING":
            reason = payload.get("reason", "Unknown reason")
            print(f"  ! Retrying: {reason}")
    
    try:
        history_item = await comfy_client.watch_progress_websocket(
            prompt_id=prompt_id,
            status_callback=status_callback,
        )
        
        # Execution completed successfully
        diagnostics.history_data = {"prompt_id": prompt_id, "status": "success"}
        
        # Extract images from history
        images = comfy_client.extract_images(history_item)
        diagnostics.images_found = len(images)
        diagnostics.output_seen = diagnostics.images_found > 0
        
        diagnostics.final_state = "completed"
        diagnostics.execution_time_seconds = time.time() - start_time
        
        print(f"  ✓ Execution completed successfully")
    
    except RuntimeError as e:
        diagnostics.final_state = "execution_error"
        diagnostics.abort_reason = str(e)
        diagnostics.execution_time_seconds = time.time() - start_time
        print(f"  ✗ Execution error: {e}")
    
    except Exception as e:
        diagnostics.final_state = "exception"
        diagnostics.abort_reason = f"probe_exception: {str(e)}"
        diagnostics.execution_time_seconds = time.time() - start_time
        import traceback
        print(f"Exception during probe: {e}")
        traceback.print_exc()
    
    # Record queue state at completion
    queue_at_completion = await comfy_client.get_queue()
    diagnostics.queue_state_at_completion = {
        "queue_running": queue_at_completion.get("queue_running", []),
        "queue_pending": queue_at_completion.get("queue_pending", []),
    }
    
    print(f"\nProbe completed: {probe_name}")
    print(f"  Final state: {diagnostics.final_state}")
    print(f"  Entered running: {diagnostics.entered_running}")
    print(f"  Progress heartbeats: {diagnostics.progress_heartbeat_count}")
    print(f"  Save node reached: {diagnostics.save_node_reached}")
    print(f"  Output seen: {diagnostics.output_seen}")
    print(f"  Images found: {diagnostics.images_found}")
    print(f"  Execution time: {diagnostics.execution_time_seconds:.2f}s")
    
    return diagnostics


def compare_diagnostics(
    control: ProbeDiagnostics,
    batch: ProbeDiagnostics,
) -> dict[str, Any]:
    """Compare control and batch probe diagnostics."""
    print(f"\n{'='*60}")
    print("DIFFERENTIAL COMPARISON")
    print(f"{'='*60}")
    
    comparison = {
        "control": control.to_dict(),
        "batch": batch.to_dict(),
        "comparison": {},
    }
    
    # Compare key metrics
    comparison["comparison"]["entered_running"] = {
        "control": control.entered_running,
        "batch": batch.entered_running,
        "match": control.entered_running == batch.entered_running,
    }
    
    comparison["comparison"]["save_node_reached"] = {
        "control": control.save_node_reached,
        "batch": batch.save_node_reached,
        "match": control.save_node_reached == batch.save_node_reached,
    }
    
    comparison["comparison"]["output_seen"] = {
        "control": control.output_seen,
        "batch": batch.output_seen,
        "match": control.output_seen == batch.output_seen,
    }
    
    comparison["comparison"]["final_state"] = {
        "control": control.final_state,
        "batch": batch.final_state,
        "match": control.final_state == batch.final_state,
    }
    
    comparison["comparison"]["progress_heartbeat_count"] = {
        "control": control.progress_heartbeat_count,
        "batch": batch.progress_heartbeat_count,
        "delta": batch.progress_heartbeat_count - control.progress_heartbeat_count,
    }
    
    # Print comparison
    print("\nKey Metrics Comparison:")
    print(f"  Entered Running:")
    print(f"    Control: {control.entered_running}")
    print(f"    Batch:   {batch.entered_running}")
    print(f"    Match:   {comparison['comparison']['entered_running']['match']}")
    
    print(f"\n  Save Node Reached:")
    print(f"    Control: {control.save_node_reached}")
    print(f"    Batch:   {batch.save_node_reached}")
    print(f"    Match:   {comparison['comparison']['save_node_reached']['match']}")
    
    print(f"\n  Output Seen:")
    print(f"    Control: {control.output_seen}")
    print(f"    Batch:   {batch.output_seen}")
    print(f"    Match:   {comparison['comparison']['output_seen']['match']}")
    
    print(f"\n  Final State:")
    print(f"    Control: {control.final_state}")
    print(f"    Batch:   {batch.final_state}")
    print(f"    Match:   {comparison['comparison']['final_state']['match']}")
    
    print(f"\n  Progress Heartbeat Count:")
    print(f"    Control: {control.progress_heartbeat_count}")
    print(f"    Batch:   {batch.progress_heartbeat_count}")
    print(f"    Delta:   {comparison['comparison']['progress_heartbeat_count']['delta']}")
    
    # Classify root cause
    print(f"\n{'='*60}")
    print("ROOT CAUSE CLASSIFICATION")
    print(f"{'='*60}")
    
    # Primary check: both probes completed with output
    if control.final_state == "completed" and batch.final_state == "completed":
        if control.output_seen and batch.output_seen:
            root_cause = "batch_template_functional_under_clean_conditions"
            reasoning = "Both control and batch probes completed successfully with output under clean queue conditions. The batch template is functional. Previous failures were likely due to queue contamination or transient conditions, not a batch-template-specific pathology."
        elif control.output_seen and not batch.output_seen:
            root_cause = "batch_template_specific_execution_pathology"
            reasoning = "Control probe produced output but batch probe did not, despite both completing. This indicates the batch template has a specific execution pathology in the save/output pipeline."
        elif not control.output_seen and batch.output_seen:
            root_cause = "inconclusive"
            reasoning = "Batch probe produced output but control probe did not. This is unexpected and may indicate an issue with the control baseline configuration."
        else:
            root_cause = "runtime_trace_or_comfy_execution_layer_defect"
            reasoning = "Both probes completed but neither produced output. This indicates a broader runtime/Comfy execution layer defect affecting the save pipeline."
    # Differential failure modes
    elif control.entered_running and not batch.entered_running:
        root_cause = "batch_template_specific_execution_pathology"
        reasoning = "Control probe entered running state but batch probe did not. This indicates the batch template has a specific execution pathology."
    elif control.save_node_reached and not batch.save_node_reached:
        root_cause = "batch_template_specific_execution_pathology"
        reasoning = "Control probe reached save node but batch probe did not. This indicates the batch template has a specific execution pathology."
    elif control.output_seen and not batch.output_seen:
        root_cause = "batch_template_specific_execution_pathology"
        reasoning = "Control probe produced output but batch probe did not. This indicates the batch template has a specific execution pathology."
    # Both failed in the same way
    elif not control.entered_running and not batch.entered_running:
        root_cause = "runtime_trace_or_comfy_execution_layer_defect"
        reasoning = "Neither probe entered running state. This indicates a broader runtime/Comfy execution layer defect."
    elif not control.output_seen and not batch.output_seen:
        root_cause = "runtime_trace_or_comfy_execution_layer_defect"
        reasoning = "Neither probe produced output. This indicates a broader runtime/Comfy execution layer defect."
    else:
        root_cause = "inconclusive"
        reasoning = "Unable to classify based on observed behavior. More investigation needed."
    
    comparison["root_cause_classification"] = {
        "classification": root_cause,
        "reasoning": reasoning,
    }
    
    print(f"\nClassification: {root_cause}")
    print(f"Reasoning: {reasoning}")
    
    return comparison


async def main():
    """Main entry point for differential probe."""
    print("="*60)
    print("MK-6J-CP: Control Baseline vs Batch Template Differential Probe")
    print("="*60)
    
    # Step 1: Clear queue
    await clear_queue()
    
    # Step 2: Verify queue is clean
    is_clean = await check_queue_clean()
    if not is_clean:
        print("\nERROR: Queue is not clean. Aborting probe.")
        return
    
    # Step 3: Upload input image
    if not INPUT_IMAGE.exists():
        print(f"\nERROR: Input image not found: {INPUT_IMAGE}")
        print("Please place a test image at test_input_image.png")
        return
    
    input_image_name = await upload_input_image(INPUT_IMAGE)
    
    # Step 4: Run control probe (img2img_simple_template.json)
    control_workflow = WORKFLOWS_DIR / "img2img_simple_template.json"
    control_diagnostics = await run_probe(
        workflow_path=control_workflow,
        probe_name="control_img2img_v1",
        input_image_name=input_image_name,
        timeout_seconds=180,
    )
    
    # Step 5: Clear queue between probes
    await clear_queue()
    is_clean = await check_queue_clean()
    if not is_clean:
        print("\nWARNING: Queue not clean between probes. Proceeding anyway.")
    
    # Step 6: Run batch probe (img2img_batch_template.json)
    batch_workflow = WORKFLOWS_DIR / "img2img_batch_template.json"
    batch_diagnostics = await run_probe(
        workflow_path=batch_workflow,
        probe_name="batch_img2img_batch_v1",
        input_image_name=input_image_name,
        timeout_seconds=180,
    )
    
    # Step 7: Compare diagnostics
    comparison = compare_diagnostics(control_diagnostics, batch_diagnostics)
    
    # Step 8: Save results
    results_path = PROJECT_ROOT / "mk6jcp_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Results saved to: {results_path}")
    print(f"{'='*60}")
    
    # Step 9: Final decision
    print(f"\n{'='*60}")
    print("FINAL DECISION")
    print(f"{'='*60}")
    
    classification = comparison["root_cause_classification"]["classification"]
    
    if classification in [
        "batch_template_specific_execution_pathology",
        "runtime_trace_or_comfy_execution_layer_defect",
    ]:
        print(f"\nMK-6J-CP: PASS")
        print(f"Root cause classified as: {classification}")
    elif classification == "batch_template_functional_under_clean_conditions":
        print(f"\nMK-6J-CP: PASS (with reclassification)")
        print(f"Batch template is functional. Previous failure was likely transient.")
    else:
        print(f"\nMK-6J-CP: FAIL")
        print(f"Classification inconclusive: {classification}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
