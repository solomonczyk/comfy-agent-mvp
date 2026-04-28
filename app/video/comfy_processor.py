"""KT-7 ComfyUI-based frame processor.

Replaces the temporary KT-6 PIL processing path with real selected-frame
processing through the existing image-edit runtime (`run_agent(mode="edit")`
-> `TaskType.IMG2IMG` -> `img2img_v1` workflow).

Per-frame linkage (source frame, processed frame, run_id, prompt_id,
metadata/result paths) is recorded and surfaced in the video manifest.
"""
from __future__ import annotations

import asyncio
import io
import json
from datetime import datetime
import re
import shutil
from pathlib import Path
from typing import Any

from app.agent_run import run_agent
from app.comfy.workflow_patcher import WorkflowPatcher


_PROMPT_ID_LINE = re.compile(r"^prompt_id:\s*(?P<pid>\S+)\s*$", re.MULTILINE)


def _compute_frame_brightness(image_data: bytes) -> dict[str, float]:
    """Compute brightness and channel statistics for frame image data.

    Args:
        image_data: Raw image bytes (PNG format)

    Returns:
        Dict with mean_brightness, min_brightness, max_brightness, std_brightness,
        and RGB channel dominance ratios for blue-frame detection
    """
    try:
        from PIL import Image
        import math
        img = Image.open(io.BytesIO(image_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Convert to grayscale for brightness calculation
        gray = img.convert("L")
        pixels = list(gray.getdata())
        
        mean_brightness = sum(pixels) / len(pixels)
        min_brightness = min(pixels)
        max_brightness = max(pixels)
        
        # Calculate standard deviation
        variance = sum((x - mean_brightness) ** 2 for x in pixels) / len(pixels)
        std_brightness = math.sqrt(variance)
        
        # Calculate RGB channel statistics for blue-frame detection
        rgb_pixels = list(img.getdata())
        r_values = [p[0] for p in rgb_pixels]
        g_values = [p[1] for p in rgb_pixels]
        b_values = [p[2] for p in rgb_pixels]
        
        r_mean = sum(r_values) / len(r_values)
        g_mean = sum(g_values) / len(g_values)
        b_mean = sum(b_values) / len(b_values)
        
        total_mean = r_mean + g_mean + b_mean
        if total_mean > 0:
            red_dominance_ratio = r_mean / total_mean
            green_dominance_ratio = g_mean / total_mean
            blue_dominance_ratio = b_mean / total_mean
        else:
            red_dominance_ratio = 0.33
            green_dominance_ratio = 0.33
            blue_dominance_ratio = 0.33
        
        return {
            "mean_brightness": mean_brightness,
            "min_brightness": min_brightness,
            "max_brightness": max_brightness,
            "std_brightness": std_brightness,
            "red_dominance_ratio": red_dominance_ratio,
            "green_dominance_ratio": green_dominance_ratio,
            "blue_dominance_ratio": blue_dominance_ratio,
            "r_mean": r_mean,
            "g_mean": g_mean,
            "b_mean": b_mean,
        }
    except Exception as e:
        print(f"[MK-6K-R] Warning: Failed to compute brightness: {e}")
        return {
            "mean_brightness": 0.0,
            "min_brightness": 0.0,
            "max_brightness": 0.0,
            "std_brightness": 0.0,
            "red_dominance_ratio": 0.33,
            "green_dominance_ratio": 0.33,
            "blue_dominance_ratio": 0.33,
            "r_mean": 0.0,
            "g_mean": 0.0,
            "b_mean": 0.0,
        }


def _extract_prompt_id(summary_path: str | None) -> str | None:
    """Best-effort parse of prompt_id from a run summary.txt."""
    if not summary_path:
        return None
    p = Path(summary_path)
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return None
    match = _PROMPT_ID_LINE.search(text)
    if not match:
        return None
    pid = match.group("pid")
    if pid in ("-", "None", ""):
        return None
    return pid


async def process_frames_via_comfy(
    selected_paths: list[Path],
    processed_dir: Path,
    prompt: str,
    comfy_recipe: dict[str, Any] | None = None,
    reference_locked: bool = False,
    batch_mode: bool = False,
    bounded_mode: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run each selected frame through the existing edit (img2img) path.

    For every frame the generated image is copied into `processed_dir` as a
    contiguous `frame_NNNNNN.png` sequence so ffmpeg can assemble them
    directly. A linkage record is returned per frame.
    
    bounded_mode: MK-6J bounded generation - uses 2 keyframe submissions + seed variation
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    # The img2img_v1 workflow uses LoadImage at node 5 (not EmptyLatentImage), so
    # width/height overrides are rejected by the mutator. The frame's native
    # resolution dictates the output dimensions.
    safe_recipe = None
    if comfy_recipe:
        safe_recipe = {
            k: v for k, v in comfy_recipe.items()
            if k not in {"width", "height"} and v is not None
        } or None

    linkage: list[dict[str, Any]] = []
    generation_diagnostics = {
        "copy_fallback_used": False,
        "real_generation_used": False,
        "total_frames_requested": len(selected_paths),
        "real_generation_count": 0,
        "copy_fallback_count": 0,
        "comfy_submission_count": 0,
        "images_per_submission": [],
        "generation_strategy": "framewise",
    }

    # When reference_locked is True, bypass multi-candidate selection at workflow level
    # but still perform real frame generation through ComfyUI
    # The key is to skip the candidate selection loop, not to skip generation entirely
    if reference_locked:
        print("[REFERENCE_LOCKED] Bypassing multi-candidate selection, using real generation")

    # Determine generation strategy
    if bounded_mode:
        generation_diagnostics["generation_strategy"] = "bounded_batch"
        print(f"[BOUNDED_MODE] MK-6J-S: Using bounded batch strategy with integrity guards (2 submissions, 3 frames each)")
        
        # Bounded strategy: generate all frames in 2 submissions
        # Each submission uses the batch workflow to generate 3 frames
        num_frames = len(selected_paths)
        frames_per_submission = 3
        num_submissions = (num_frames + frames_per_submission - 1) // frames_per_submission
        
        print(f"[BOUNDED_MODE] Generating {num_frames} frames in {num_submissions} submissions ({frames_per_submission} frames per submission)")
        
        # Import ComfyClient for direct batch submission
        from app.comfy.comfy_client import ComfyClient
        
        comfy_client = ComfyClient()
        
        # MK-6J-S: Integrity guard - track active prompt_ids to prevent duplicate submissions
        active_prompt_ids: set[str] = set()
        
        # MK-6J-S: Bounded wait policy
        max_pending_wait_s = 60  # 1 minute max for pending
        max_running_wait_s = 600  # 10 minutes max for running (covers large 1024x1024 references)
        max_total_wait_s = 720  # 12 minutes max total per submission
        
        # MK-6J-CQ: Queue recovery gate - inspect and attempt to recover queue state before bounded probe
        print(f"[BOUNDED_MODE] MK-6J-CQ: Inspecting pre-recovery queue state...")
        queue_data = await comfy_client.get_queue()
        queue_pending = queue_data.get("queue_pending", [])
        queue_running = queue_data.get("queue_running", [])
        
        # MK-6J-XT: Execution trace diagnostics for running-state behavior classification
        execution_trace = {
            "clean_queue_confirmation": False,
            "probe_prompt_id": None,
            "running_trace": [],
            "node_execution_trace": [],
            "progress_heartbeat_count": 0,
            "last_progress_timestamp": None,
            "save_node_reached": False,
            "output_seen": False,
            "final_execution_classification": "unknown",
        }
        
        # Extract active prompt IDs
        active_pending_ids = []
        for item in queue_pending:
            if len(item) > 1:
                active_pending_ids.append(item[1])
        
        active_running_ids = []
        for item in queue_running:
            if len(item) > 1:
                active_running_ids.append(item[1])
        
        all_active_ids = set(active_pending_ids + active_running_ids)
        
        # MK-6J-CQ: Queue recovery diagnostics
        queue_recovery = {
            "pre_recovery_queue_state": "unknown",
            "stale_owned_prompt_ids": [],
            "foreign_external_prompt_ids": [],
            "recovery_action_used": "none",
            "recovery_action_result": "not_attempted",
            "post_recovery_queue_state": "unknown",
            "fresh_probe_prompt_id": None,
            "fresh_probe_lifecycle": {},
            "fresh_probe_final_state": "unknown",
            "root_cause_reclassification": "unknown",
        }
        
        # Classify queue state and prompts
        if not all_active_ids:
            queue_recovery["pre_recovery_queue_state"] = "queue_empty"
            queue_recovery["recovery_action_result"] = "no_action_needed"
            execution_trace["clean_queue_confirmation"] = True
            print(f"[BOUNDED_MODE] MK-6J-CQ: Queue is EMPTY - no recovery needed")
            print(f"[BOUNDED_MODE] MK-6J-XT: Clean queue confirmed for execution trace")
        else:
            queue_recovery["pre_recovery_queue_state"] = "queue_busy"
            # Since this is a new bounded run, all existing prompts are stale owned (from previous bounded attempts)
            # They are not external/foreign from other systems
            queue_recovery["stale_owned_prompt_ids"] = list(all_active_ids)
            queue_recovery["foreign_external_prompt_ids"] = []
            
            print(f"[BOUNDED_MODE] MK-6J-CQ: Queue has {len(all_active_ids)} STALE OWNED prompts from previous bounded attempts")
            print(f"[BOUNDED_MODE] MK-6J-CQ: Stale prompt IDs = {list(all_active_ids)}")
            
            # MK-6J-CQ: Attempt queue recovery
            # Check if ComfyClient supports queue recovery methods
            recovery_methods = []
            if hasattr(comfy_client, 'clear_queue'):
                recovery_methods.append('clear_queue')
            if hasattr(comfy_client, 'delete_queue'):
                recovery_methods.append('delete_queue')
            if hasattr(comfy_client, 'interrupt_queue'):
                recovery_methods.append('interrupt_queue')
            
            if recovery_methods:
                queue_recovery["recovery_action_used"] = recovery_methods[0]
                print(f"[BOUNDED_MODE] MK-6J-CQ: Attempting queue recovery using {recovery_methods[0]}...")
                try:
                    if recovery_methods[0] == 'clear_queue':
                        await comfy_client.clear_queue()
                    elif recovery_methods[0] == 'delete_queue':
                        await comfy_client.delete_queue()
                    elif recovery_methods[0] == 'interrupt_queue':
                        await comfy_client.interrupt_queue()
                    
                    queue_recovery["recovery_action_result"] = "success"
                    print(f"[BOUNDED_MODE] MK-6J-CQ: Queue recovery SUCCESS")
                except Exception as exc:
                    queue_recovery["recovery_action_result"] = f"failed: {exc}"
                    print(f"[BOUNDED_MODE] MK-6J-CQ: Queue recovery FAILED: {exc}")
            else:
                queue_recovery["recovery_action_used"] = "none"
                queue_recovery["recovery_action_result"] = "queue_recovery_not_supported"
                print(f"[BOUNDED_MODE] MK-6J-CQ: Queue recovery NOT SUPPORTED - ComfyClient has no clear/delete/interrupt methods")
                print(f"[BOUNDED_MODE] MK-6J-CQ: Manual queue cleanup required via ComfyUI UI")
            
            # Verify post-recovery queue state
            queue_data = await comfy_client.get_queue()
            queue_pending = queue_data.get("queue_pending", [])
            queue_running = queue_data.get("queue_running", [])
            
            post_pending_ids = []
            for item in queue_pending:
                if len(item) > 1:
                    post_pending_ids.append(item[1])
            
            post_running_ids = []
            for item in queue_running:
                if len(item) > 1:
                    post_running_ids.append(item[1])
            
            post_active_ids = set(post_pending_ids + post_running_ids)
            
            if not post_active_ids:
                queue_recovery["post_recovery_queue_state"] = "queue_empty"
                print(f"[BOUNDED_MODE] MK-6J-CQ: Post-recovery queue is CLEAN - proceeding with fresh bounded probe")
            else:
                queue_recovery["post_recovery_queue_state"] = "queue_busy_still"
                print(f"[BOUNDED_MODE] MK-6J-CQ: Post-recovery queue still has {len(post_active_ids)} prompts")
                print(f"[BOUNDED_MODE] MK-6J-CQ: Remaining prompt IDs = {list(post_active_ids)}")
                
                # Queue is not clean - cannot proceed with fresh probe
                generation_diagnostics["queue_recovery"] = queue_recovery
                generation_diagnostics["bounded_integrity_fail"] = True
                generation_diagnostics["bounded_integrity_reason"] = "queue_not_clean_after_recovery"
                
                raise RuntimeError(f"MK-6J-CQ: Queue not clean after recovery - {len(post_active_ids)} prompts remain: {list(post_active_ids)}. Manual cleanup required.")
        
        generation_diagnostics["queue_recovery"] = queue_recovery
        
        frames_generated_count = 0
        for submission_idx in range(num_submissions):
            start_frame = submission_idx * frames_per_submission
            end_frame = min(start_frame + frames_per_submission, num_frames)
            frames_in_this_batch = end_frame - start_frame
            
            # MK-6J-CQ: Track the first submission as a fresh probe for root cause reclassification
            is_fresh_probe = (submission_idx == 0)
            if is_fresh_probe:
                print(f"[BOUNDED_MODE] MK-6J-CQ: Submission {submission_idx} is FRESH PROBE for root cause reclassification")
            
            # MK-6J-S: Submission integrity diagnostics
            submission_integrity = {
                "bounded_submission_index": submission_idx,
                "prompt_id": None,
                "submit_attempt_count": 0,
                "duplicate_submit_blocked": False,
                "queue_state": "queued_not_started",
                "running_state": "not_running",
                "pending_wait_s": 0,
                "running_wait_s": 0,
                "total_wait_s": 0,
                "abort_reason": None,
                "output_fetch_count": 0,
                "images_observed_during_wait": 0,
                "single_prompt_integrity_status": "unknown",
                "is_fresh_probe": is_fresh_probe,
            }
            
            # Use the reference frame for this batch
            src_frame = selected_paths[start_frame]
            src_frame = Path(src_frame).resolve()
            
            # Upload the reference image
            try:
                upload_result = await comfy_client.upload_image(str(src_frame))
                image_name = upload_result.get("name", Path(src_frame).name)
            except Exception as exc:
                print(f"[BOUNDED_MODE] MK-6J-S: Failed to upload image: {exc}")
                submission_integrity["abort_reason"] = f"upload_failed: {exc}"
                submission_integrity["single_prompt_integrity_status"] = "aborted"
                generation_diagnostics["comfy_submission_count"] += 1
                generation_diagnostics["images_per_submission"].append(0)
                if "submission_integrities" not in generation_diagnostics:
                    generation_diagnostics["submission_integrities"] = []
                generation_diagnostics["submission_integrities"].append(submission_integrity)
                continue
            
            # Load the batch workflow directly as JSON (no mutator to avoid automatic overrides)
            import json
            from pathlib import Path as PPath
            
            workflow_path = PPath("data/workflows/img2img_batch_template.json")
            
            try:
                with open(workflow_path, 'r') as f:
                    workflow = json.load(f)
                
                # MK-6K-S: Trace batch template wiring
                print(f"[MK-6K-S] Analyzing batch template wiring for submission {submission_idx}...")
                ksampler_latent_sources = {}
                vaencode_sources = {}
                
                for node_id, node_data in workflow.items():
                    class_type = node_data.get("class_type")
                    inputs = node_data.get("inputs", {})
                    
                    if class_type == "KSampler":
                        latent_source = inputs.get("latent_image")
                        if latent_source:
                            ksampler_latent_sources[node_id] = latent_source
                            print(f"[MK-6K-S] KSampler {node_id}.latent_image = {latent_source}")
                    
                    elif class_type == "VAEEncode":
                        pixels_source = inputs.get("pixels")
                        if pixels_source:
                            vaencode_sources[node_id] = pixels_source
                            print(f"[MK-6K-S] VAEEncode {node_id}.pixels = {pixels_source}")
                
                # MK-6K-S: Prove VAEEncode -> KSampler linkage
                print(f"[MK-6K-S] VAEEncode -> KSampler linkage proof:")
                for ksampler_id, latent_source in ksampler_latent_sources.items():
                    source_node_id = latent_source[0] if isinstance(latent_source, list) else "unknown"
                    source_node = workflow.get(source_node_id, {})
                    source_type = source_node.get("class_type", "unknown")
                    print(f"[MK-6K-S]   KSampler {ksampler_id} <- {source_node_id} ({source_type})")
                
                # Apply recipe mutations to all KSampler nodes (3, 10, 13)
                base_seed = safe_recipe.get("seed", 123456789) if safe_recipe else 123456789
                
                for node_id in ["3", "10", "13"]:
                    if node_id in workflow:
                        node = workflow[node_id]
                        inputs = node.get("inputs", {})
                        
                        # Apply seed variation
                        # MK-6R2: Use tight seed offsets (+3) when reference_locked to preserve
                        # per-slot variation without diverging to unrelated scene categories.
                        # Non-reference-locked mode keeps wider offsets (*100) for diversity.
                        seed_offset = 0 if node_id == "3" else (1 if node_id == "10" else 2)
                        slot_offset = seed_offset * 3 if reference_locked else seed_offset * 100
                        inputs["seed"] = base_seed + (submission_idx * 10000) + slot_offset
                        
                        # Apply other recipe parameters
                        if safe_recipe:
                            if "steps" in safe_recipe:
                                inputs["steps"] = safe_recipe["steps"]
                            if "cfg" in safe_recipe:
                                inputs["cfg"] = safe_recipe["cfg"]
                            if "sampler_name" in safe_recipe:
                                inputs["sampler_name"] = safe_recipe["sampler_name"]
                            if "scheduler" in safe_recipe:
                                inputs["scheduler"] = safe_recipe["scheduler"]
                            # MK-6R2: Apply denoise override conditionally.
                            # reference_locked=True  -> enforce denoise=0.60 so the model stays
                            #   close to the portrait reference (FIX-1 from MK-6Q audit).
                            # reference_locked=False -> keep template default (0.8) to avoid
                            #   low_stddev_uniform_frames in free-generation mode (MK-6K intent).
                            if reference_locked:
                                recipe_denoise = safe_recipe.get("denoise", 0.60)
                                inputs["denoise"] = min(recipe_denoise, 0.65)
                            elif "denoise" in safe_recipe:
                                inputs["denoise"] = safe_recipe["denoise"]
                        
                        # Don't override latent_image - it's already linked to VAE Encode nodes
                        node["inputs"] = inputs
                
                # Set input image
                if "5" in workflow:
                    workflow["5"]["inputs"]["image"] = image_name
                
                # Set prompt
                for node_id in ["6"]:
                    if node_id in workflow:
                        workflow[node_id]["inputs"]["text"] = prompt
                
                # Debug: print latent_image links before submission
                print(f"[BOUNDED_MODE] DEBUG: Node 3 latent_image = {workflow['3']['inputs'].get('latent_image')}")
                print(f"[BOUNDED_MODE] DEBUG: Node 10 latent_image = {workflow['10']['inputs'].get('latent_image')}")
                print(f"[BOUNDED_MODE] DEBUG: Node 13 latent_image = {workflow['13']['inputs'].get('latent_image')}")
                
                # Apply workflow patcher to fix KSampler defects
                workflow = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3", "10", "13"])
                
                # MK-6K-PP: Dump workflow before submission for parity proof
                dump_dir = Path("data/outputs/mk6k_pp_payload_dumps")
                dump_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                dump_path = dump_dir / f"bounded_submission_{timestamp}.json"
                with open(dump_path, 'w') as f:
                    json.dump(workflow, f, indent=2)
                print(f"[MK-6K-PP] Dumped workflow to: {dump_path}")
                
                # Submit to ComfyUI
                submission_integrity["submit_attempt_count"] += 1
                prompt_id = await comfy_client.queue_prompt(workflow)
                submission_integrity["prompt_id"] = prompt_id
                
                # MK-6J-S: Duplicate submission guard - check if this prompt_id is already active
                if prompt_id in active_prompt_ids:
                    print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Duplicate prompt_id detected: {prompt_id}")
                    submission_integrity["duplicate_submit_blocked"] = True
                    submission_integrity["abort_reason"] = f"duplicate_prompt_id: {prompt_id}"
                    submission_integrity["single_prompt_integrity_status"] = "aborted"
                    raise RuntimeError(f"MK-6J-S: Duplicate submission blocked - prompt_id {prompt_id} already active")
                
                # Track this prompt_id as active
                active_prompt_ids.add(prompt_id)
                print(f"[BOUNDED_MODE] MK-6J-S: Queue prompt returned prompt_id = {prompt_id}")
                print(f"[BOUNDED_MODE] MK-6J-S: Active prompt_ids = {active_prompt_ids}")
                
                submission_integrity["queue_state"] = "queued_not_started"
                submission_integrity["single_prompt_integrity_status"] = "submitted"
                
                # MK-6J-XT: Set probe_prompt_id for execution trace
                if is_fresh_probe:
                    execution_trace["probe_prompt_id"] = prompt_id
                    print(f"[BOUNDED_MODE] MK-6J-XT: Probe prompt_id = {prompt_id}")
                
                # MK-6J-S: Wait for completion using bounded wait policy with MK-6J-XT progress tracking
                import time
                pending_wait_start = time.time()
                running_wait_start = None
                total_wait_start = time.time()
                images = []
                output_fetched = False
                
                # MK-6J-XT: Progress tracking variables
                last_progress_time = None
                progress_no_progress_duration = 0
                progress_heartbeat_active = False
                
                # MK-6J-XT: Use WebSocket progress watching for execution trace
                def status_callback(status: str, data: dict[str, Any] | None) -> None:
                    """Track execution progress for MK-6J-XT classification"""
                    nonlocal last_progress_time, progress_heartbeat_active
                    
                    import time
                    current_time = time.time()
                    last_progress_time = current_time
                    progress_heartbeat_active = True
                    execution_trace["progress_heartbeat_count"] += 1
                    execution_trace["last_progress_timestamp"] = current_time
                    
                    trace_entry = {
                        "timestamp": current_time,
                        "status": status,
                        "data": data,
                    }
                    execution_trace["running_trace"].append(trace_entry)
                    
                    # Track node execution
                    if status == "EXECUTING" and data:
                        node_id = data.get("node")
                        if node_id:
                            node_entry = {
                                "timestamp": current_time,
                                "node_id": node_id,
                            }
                            execution_trace["node_execution_trace"].append(node_entry)
                            print(f"[BOUNDED_MODE] MK-6J-XT: Executing node {node_id}")
                    
                    # Track save node reachability
                    if status == "EXECUTING" and data:
                        node_id = data.get("node")
                        if node_id in ["9", "12", "15"]:  # SaveImage nodes
                            execution_trace["save_node_reached"] = True
                            print(f"[BOUNDED_MODE] MK-6J-XT: Save node {node_id} reached")
                    
                    # Track output seen
                    if status == "OUTPUT":
                        execution_trace["output_seen"] = True
                        print(f"[BOUNDED_MODE] MK-6J-XT: Output seen")
                
                # Start WebSocket progress watching
                import asyncio
                progress_task = None
                if is_fresh_probe:
                    print(f"[BOUNDED_MODE] MK-6J-XT: Starting WebSocket progress watching for probe")
                    progress_task = asyncio.create_task(
                        comfy_client.watch_progress_websocket(prompt_id, status_callback=status_callback)
                    )
                
                while time.time() - total_wait_start < max_total_wait_s:
                    # Check queue state first
                    queue_data = await comfy_client.get_queue()
                    is_running = comfy_client._is_prompt_running(queue_data, prompt_id)
                    is_pending = comfy_client._is_prompt_pending(queue_data, prompt_id)
                    
                    # Update wait times
                    current_time = time.time()
                    submission_integrity["pending_wait_s"] = current_time - pending_wait_start
                    if is_running and running_wait_start is None:
                        running_wait_start = current_time
                    if running_wait_start is not None:
                        submission_integrity["running_wait_s"] = current_time - running_wait_start
                    submission_integrity["total_wait_s"] = current_time - total_wait_start
                    
                    # Update state tracking
                    if is_pending:
                        submission_integrity["queue_state"] = "pending"
                        submission_integrity["running_state"] = "not_running"
                        # Check for stall in pending
                        if submission_integrity["pending_wait_s"] > max_pending_wait_s:
                            print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Stalled pending state for {submission_integrity['pending_wait_s']:.1f}s")
                            submission_integrity["queue_state"] = "stalled_pending"
                            submission_integrity["abort_reason"] = f"stalled_pending: {submission_integrity['pending_wait_s']:.1f}s > {max_pending_wait_s}s"
                            submission_integrity["single_prompt_integrity_status"] = "aborted"
                            raise RuntimeError(f"MK-6J-S: Abort - stalled pending for {submission_integrity['pending_wait_s']:.1f}s")
                    elif is_running:
                        submission_integrity["queue_state"] = "not_pending"
                        submission_integrity["running_state"] = "running"
                        
                        # MK-6J-XT: Progress-aware timeout policy
                        # Check if progress heartbeat is active
                        if last_progress_time is not None:
                            progress_no_progress_duration = current_time - last_progress_time
                            
                            # If progress heartbeat continues, classify as slow execution (not hard stall)
                            if progress_no_progress_duration < 30:  # Progress within last 30 seconds
                                print(f"[BOUNDED_MODE] MK-6J-XT: Progress heartbeat active ({execution_trace['progress_heartbeat_count']} heartbeats, last progress {progress_no_progress_duration:.1f}s ago)")
                            else:
                                # No progress for 30+ seconds - potential stall
                                print(f"[BOUNDED_MODE] MK-6J-XT: No progress for {progress_no_progress_duration:.1f}s - checking stall condition")
                        
                        # Check for stall in running (MK-6J-S original check)
                        if submission_integrity["running_wait_s"] > max_running_wait_s:
                            # MK-6J-XT: Classify based on progress trace
                            if execution_trace["progress_heartbeat_count"] > 0:
                                # Progress heartbeats detected - slow valid execution
                                execution_trace["final_execution_classification"] = "slow_valid_execution"
                                print(f"[BOUNDED_MODE] MK-6J-XT: Execution classified as SLOW VALID - {execution_trace['progress_heartbeat_count']} progress heartbeats detected")
                                print(f"[BOUNDED_MODE] MK-6J-XT: Nodes executed: {[entry['node_id'] for entry in execution_trace['node_execution_trace']]}")
                                print(f"[BOUNDED_MODE] MK-6J-XT: Save node reached: {execution_trace['save_node_reached']}")
                                print(f"[BOUNDED_MODE] MK-6J-XT: Output seen: {execution_trace['output_seen']}")
                            else:
                                # No progress heartbeats - true stall
                                execution_trace["final_execution_classification"] = "stalled_execution_no_progress"
                                print(f"[BOUNDED_MODE] MK-6J-XT: Execution classified as STALLED NO PROGRESS - zero progress heartbeats")
                            
                            print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Stalled running state for {submission_integrity['running_wait_s']:.1f}s")
                            submission_integrity["running_state"] = "stalled_running"
                            submission_integrity["abort_reason"] = f"stalled_running: {submission_integrity['running_wait_s']:.1f}s > {max_running_wait_s}s (classification: {execution_trace['final_execution_classification']})"
                            submission_integrity["single_prompt_integrity_status"] = "aborted"
                            raise RuntimeError(f"MK-6J-S: Abort - stalled running for {submission_integrity['running_wait_s']:.1f}s (classification: {execution_trace['final_execution_classification']})")
                    else:
                        submission_integrity["queue_state"] = "not_pending"
                        submission_integrity["running_state"] = "not_running"
                        # Prompt completed, check history
                        history = await comfy_client.get_history(prompt_id)
                        submission_integrity["history_present"] = prompt_id in history
                        
                        if prompt_id in history:
                            outputs = history[prompt_id].get("outputs", {})
                            print(f"[BOUNDED_MODE] MK-6J-S: History outputs keys = {list(outputs.keys())}")
                            
                            # MK-6J-S: Guard - ensure output fetch happens exactly once
                            if output_fetched:
                                print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Output fetch attempted twice for prompt_id {prompt_id}")
                                submission_integrity["abort_reason"] = "duplicate_output_fetch"
                                submission_integrity["single_prompt_integrity_status"] = "aborted"
                                raise RuntimeError(f"MK-6J-S: Duplicate output fetch blocked for prompt_id {prompt_id}")
                            
                            output_fetched = True
                            submission_integrity["output_fetch_count"] += 1
                            
                            # Collect images from all SaveImage nodes (9, 12, 15)
                            for save_node_id in ["9", "12", "15"]:
                                if save_node_id in outputs:
                                    node_outputs = outputs[save_node_id].get("images", [])
                                    print(f"[BOUNDED_MODE] MK-6J-S: Node {save_node_id} has {len(node_outputs)} images")
                                    for img in node_outputs:
                                        images.append(img)
                            
                            submission_integrity["images_observed_during_wait"] = len(images)
                            print(f"[BOUNDED_MODE] MK-6J-S: Total images collected = {len(images)}")
                            
                            if images:
                                submission_integrity["queue_state"] = "completed"
                                submission_integrity["single_prompt_integrity_status"] = "completed"
                                
                                # MK-6J-XT: Classify successful execution
                                if is_fresh_probe:
                                    if execution_trace["save_node_reached"] and execution_trace["output_seen"]:
                                        execution_trace["final_execution_classification"] = "slow_valid_execution"
                                    elif execution_trace["save_node_reached"]:
                                        execution_trace["final_execution_classification"] = "save_node_reached_no_output"
                                    elif execution_trace["progress_heartbeat_count"] > 0:
                                        execution_trace["final_execution_classification"] = "slow_valid_execution_partial"
                                    else:
                                        execution_trace["final_execution_classification"] = "completed_no_trace"
                                    
                                    print(f"[BOUNDED_MODE] MK-6J-XT: Successful execution classification: {execution_trace['final_execution_classification']}")
                                
                                break
                        else:
                            print(f"[BOUNDED_MODE] MK-6J-S: prompt_id {prompt_id} not in history after queue cleared")
                            submission_integrity["abort_reason"] = "history_missing_after_queue_clear"
                            submission_integrity["single_prompt_integrity_status"] = "aborted"
                            break
                    
                    print(f"[BOUNDED_MODE] MK-6J-S: Queue state - pending={is_pending}, running={is_running}, wait={submission_integrity['total_wait_s']:.1f}s")
                    time.sleep(2)
                
                # Check for timeout
                if submission_integrity["total_wait_s"] >= max_total_wait_s:
                    print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Total wait timeout: {submission_integrity['total_wait_s']:.1f}s")
                    submission_integrity["abort_reason"] = f"total_wait_timeout: {submission_integrity['total_wait_s']:.1f}s"
                    submission_integrity["single_prompt_integrity_status"] = "aborted"
                    raise RuntimeError(f"MK-6J-S: Abort - total wait timeout after {submission_integrity['total_wait_s']:.1f}s")
                
                # Mark prompt_id as resolved
                active_prompt_ids.discard(prompt_id)
                print(f"[BOUNDED_MODE] MK-6J-S: Prompt {prompt_id} resolved, active_prompt_ids = {active_prompt_ids}")
                
                # MK-6J-XT: Clean up WebSocket progress watching task
                if progress_task and not progress_task.done():
                    progress_task.cancel()
                    print(f"[BOUNDED_MODE] MK-6J-XT: WebSocket progress task cancelled")
                
                # Download and save images
                downloaded_count = 0
                for img_idx, img_info in enumerate(images):
                    try:
                        img_response = await comfy_client.fetch_image(img_info["filename"], img_info["subfolder"], img_info["type"])
                        img_data = img_response.get("content")
                        if img_data is None:
                            raise ValueError(f"No content in fetch_image response: {img_response}")
                        
                        frame_idx = start_frame + img_idx
                        if frame_idx >= num_frames:
                            break
                        
                        dst = processed_dir / f"frame_{frame_idx + 1:06d}.png"
                        dst.write_bytes(img_data)
                        
                        # MK-6K-R: Stage B - Fetched image payload diagnostics
                        frame_brightness = _compute_frame_brightness(img_data)
                        # Match QC logic: black if mean < 10.0 OR std < 5.0
                        is_black_frame = (frame_brightness["mean_brightness"] < 10.0) or (frame_brightness["std_brightness"] < 5.0)
                        # Blue frame detection: blue dominance > 0.5
                        is_blue_frame = frame_brightness["blue_dominance_ratio"] > 0.5
                        is_invalid = is_black_frame or is_blue_frame
                        
                        print(f"[MK-6K-R] Stage B (fetched): Frame {frame_idx + 1}: mean={frame_brightness['mean_brightness']:.1f}, std={frame_brightness['std_brightness']:.1f}, blue_ratio={frame_brightness['blue_dominance_ratio']:.2f}, black={is_black_frame}, blue={is_blue_frame}")
                        
                        entry = {
                            "index": frame_idx + 1,
                            "source_frame": str(selected_paths[frame_idx]),
                            "processed_frame": str(dst),
                            "run_id": prompt_id,
                            "prompt_id": prompt_id,
                            "status": "completed",
                            "metadata_path": None,
                            "result_path": None,
                            "trace_path": None,
                            "source_generated_image": str(dst),
                            "error": None,
                            "batch_index": submission_idx,
                            "batch_offset": img_idx,
                            # MK-6K-S: Slot-level mapping and stage-based validity tracing
                            "frame_diagnostics": {
                                "frame_index": frame_idx + 1,
                                "source_submission_index": submission_idx,
                                "source_output_index": img_idx,
                                "output_filename": img_info["filename"],
                                "output_node": img_info.get("node", "unknown"),
                                "prompt_id": prompt_id,
                                # MK-6K-S: Slot wiring information
                                "slot_wiring": {
                                    "slot_index": img_idx,
                                    "ksampler_node_id": str(3 + img_idx * 7),  # 3, 10, 13
                                    "vadecode_node_id": str(8 + img_idx * 3),  # 8, 11, 14
                                    "saveimage_node_id": str(9 + img_idx * 3),  # 9, 12, 15
                                    "latent_source_node_id": str(16 + img_idx),  # 16, 17, 18
                                    "latent_source_type": "VAEEncode",
                                },
                                # Stage B: Fetched payload diagnostics
                                "stage_b_fetched": {
                                    "black_frame": is_black_frame,
                                    "blue_frame": is_blue_frame,
                                    "invalid": is_invalid,
                                    "mean_brightness": frame_brightness["mean_brightness"],
                                    "std_brightness": frame_brightness["std_brightness"],
                                    "min_brightness": frame_brightness["min_brightness"],
                                    "max_brightness": frame_brightness["max_brightness"],
                                    "blue_dominance_ratio": frame_brightness["blue_dominance_ratio"],
                                    "red_dominance_ratio": frame_brightness["red_dominance_ratio"],
                                    "green_dominance_ratio": frame_brightness["green_dominance_ratio"],
                                    "r_mean": frame_brightness["r_mean"],
                                    "g_mean": frame_brightness["g_mean"],
                                    "b_mean": frame_brightness["b_mean"],
                                },
                                # Stage C: Decoded/loaded object (after dst.write_bytes)
                                "stage_c_decoded": {
                                    "path": str(dst),
                                    "status": "written_to_disk",
                                },
                                # Stage D: Linked frame (passed to assembly)
                                "stage_d_linked": {
                                    "source_frame": str(selected_paths[frame_idx]),
                                    "linkage_source": "bounded_batch",
                                },
                            },
                        }
                        linkage.append(entry)
                        downloaded_count += 1
                        frames_generated_count += 1
                    except Exception as exc:
                        print(f"[BOUNDED_MODE] MK-6J-S: Failed to download image {img_idx}: {exc}")
                
                generation_diagnostics["real_generation_used"] = True
                generation_diagnostics["real_generation_count"] += downloaded_count
                generation_diagnostics["comfy_submission_count"] += 1
                generation_diagnostics["images_per_submission"].append(downloaded_count)
                
                # Add submission integrity diagnostics
                if "submission_integrities" not in generation_diagnostics:
                    generation_diagnostics["submission_integrities"] = []
                generation_diagnostics["submission_integrities"].append(submission_integrity)
                
                print(f"[BOUNDED_MODE] MK-6J-S: Submission {submission_idx + 1}: downloaded {downloaded_count} frames, integrity={submission_integrity['single_prompt_integrity_status']}")
                
                # MK-6J-CQ: Fresh probe lifecycle tracking for root cause reclassification
                if is_fresh_probe:
                    queue_recovery["fresh_probe_prompt_id"] = submission_integrity["prompt_id"]
                    queue_recovery["fresh_probe_lifecycle"] = {
                        "prompt_id": submission_integrity["prompt_id"],
                        "queue_state": submission_integrity["queue_state"],
                        "running_state": submission_integrity["running_state"],
                        "pending_wait_s": submission_integrity["pending_wait_s"],
                        "running_wait_s": submission_integrity["running_wait_s"],
                        "total_wait_s": submission_integrity["total_wait_s"],
                        "abort_reason": submission_integrity["abort_reason"],
                        "images_observed_during_wait": submission_integrity["images_observed_during_wait"],
                        "output_fetch_count": submission_integrity["output_fetch_count"],
                        "single_prompt_integrity_status": submission_integrity["single_prompt_integrity_status"],
                    }
                    queue_recovery["fresh_probe_final_state"] = submission_integrity["single_prompt_integrity_status"]
                    
                    # Reclassify root cause based on fresh probe behavior
                    if submission_integrity["single_prompt_integrity_status"] == "completed":
                        queue_recovery["root_cause_reclassification"] = "none_workflow_valid"
                        print(f"[BOUNDED_MODE] MK-6J-CQ: Fresh probe COMPLETED - bounded workflow is VALID on clean queue")
                    elif submission_integrity["abort_reason"] and "stalled_pending" in submission_integrity["abort_reason"]:
                        # Fresh probe stalled in pending even on clean queue
                        queue_recovery["root_cause_reclassification"] = "bounded_workflow_non_start_on_clean_queue"
                        print(f"[BOUNDED_MODE] MK-6J-CQ: Fresh probe STALLED PENDING on clean queue - ROOT CAUSE: bounded workflow non-start / route invalidity")
                    elif submission_integrity["abort_reason"] and "stalled_running" in submission_integrity["abort_reason"]:
                        queue_recovery["root_cause_reclassification"] = "bounded_workflow_stall_running"
                        print(f"[BOUNDED_MODE] MK-6J-CQ: Fresh probe STALLED RUNNING - ROOT CAUSE: bounded workflow execution stall")
                    else:
                        queue_recovery["root_cause_reclassification"] = f"unknown_abort: {submission_integrity.get('abort_reason')}"
                        print(f"[BOUNDED_MODE] MK-6J-CQ: Fresh probe aborted with unknown reason: {submission_integrity.get('abort_reason')}")
                    
                    # Update generation diagnostics with reclassification
                    generation_diagnostics["queue_recovery"] = queue_recovery
                    
                    # MK-6J-XT: Add execution trace to generation diagnostics
                    generation_diagnostics["execution_trace"] = execution_trace
                    print(f"[BOUNDED_MODE] MK-6J-XT: Execution trace added to diagnostics")
                    
                    # MK-6J-CQ: If fresh probe failed with workflow non-start, stop further submissions
                    if queue_recovery["root_cause_reclassification"] == "bounded_workflow_non_start_on_clean_queue":
                        print(f"[BOUNDED_MODE] MK-6J-CQ: Fresh probe classified as workflow non-start - stopping further submissions")
                        generation_diagnostics["bounded_integrity_fail"] = True
                        generation_diagnostics["bounded_integrity_reason"] = queue_recovery["root_cause_reclassification"]
                        raise RuntimeError(f"MK-6J-CQ: Bounded workflow non-start on clean queue - root cause reclassified: {queue_recovery['root_cause_reclassification']}")
                
            except Exception as exc:
                print(f"[BOUNDED_MODE] MK-6J-S: Failed to process batch {submission_idx + 1}: {exc}")
                
                # Clean up prompt_id from active set on failure
                if submission_integrity.get("prompt_id"):
                    active_prompt_ids.discard(submission_integrity["prompt_id"])
                
                submission_integrity["abort_reason"] = str(exc)
                submission_integrity["single_prompt_integrity_status"] = "aborted"
                
                generation_diagnostics["comfy_submission_count"] += 1
                generation_diagnostics["images_per_submission"].append(0)
                
                if "submission_integrities" not in generation_diagnostics:
                    generation_diagnostics["submission_integrities"] = []
                generation_diagnostics["submission_integrities"].append(submission_integrity)
        
        print(f"[BOUNDED_MODE] MK-6J-S: Generated {frames_generated_count} frames in {generation_diagnostics['comfy_submission_count']} submissions")
        
        # MK-6J-S: Ensure scene assembly is blocked unless all required bounded submission slots are completed
        all_completed = all(
            s.get("single_prompt_integrity_status") == "completed"
            for s in generation_diagnostics.get("submission_integrities", [])
        )
        
        if not all_completed:
            print(f"[BOUNDED_MODE] MK-6J-S: ERROR - Not all bounded submissions completed")
            submission_statuses = [s.get("single_prompt_integrity_status") for s in generation_diagnostics.get("submission_integrities", [])]
            print(f"[BOUNDED_MODE] MK-6J-S: Submission statuses = {submission_statuses}")
            generation_diagnostics["bounded_integrity_fail"] = True
            generation_diagnostics["bounded_integrity_reason"] = f"not_all_completed: {submission_statuses}"
            raise RuntimeError(f"MK-6J-S: Bounded integrity fail - not all submissions completed: {submission_statuses}")
        
        # Calculate frames generated
        frames_generated = sum(1 for e in linkage if e.get("processed_frame"))
        generation_diagnostics["frames_generated"] = frames_generated
        
        return linkage, generation_diagnostics
    
    if batch_mode:
        generation_diagnostics["generation_strategy"] = "batch"
        # Process frames in batches to reduce submission count
        # For now, use a simple strategy: process all frames in one batch if possible
        # This would require a workflow that supports batch generation
        # For this implementation, we'll use parallel processing to reduce wall time
        import asyncio as aio
        print(f"[BATCH_MODE] Processing {len(selected_paths)} frames in parallel to reduce wall time")
        
        async def process_single_frame(idx, src_frame):
            src_frame = Path(src_frame).resolve()
            entry = {
                "index": idx,
                "source_frame": str(src_frame),
                "processed_frame": None,
                "run_id": None,
                "prompt_id": None,
                "status": "pending",
                "metadata_path": None,
                "result_path": None,
                "trace_path": None,
                "source_generated_image": None,
                "error": None,
            }

            try:
                result = await run_agent(
                    prompt=prompt,
                    mode="edit",
                    input_image=str(src_frame),
                    canonical_recipe=safe_recipe,
                    status_callback=None,
                )
                
                entry["status"] = result.get("status", "unknown")
                entry["run_id"] = result.get("run_id")
                entry["trace_path"] = result.get("trace_path")

                asset_report = result.get("asset_report") or {}
                entry["metadata_path"] = asset_report.get("metadata_path") or result.get("metadata_path")
                entry["result_path"] = asset_report.get("result_path")
                entry["prompt_id"] = _extract_prompt_id(
                    asset_report.get("summary_path") or result.get("summary_path")
                )

                image_paths = asset_report.get("image_paths") or []
                if image_paths:
                    src_generated = Path(image_paths[0])
                    entry["source_generated_image"] = str(src_generated)

                    if src_generated.exists():
                        dst = processed_dir / f"frame_{idx:06d}.png"
                        try:
                            shutil.copy2(src_generated, dst)
                            entry["processed_frame"] = str(dst)
                        except Exception as exc:
                            entry["error"] = f"copy failed: {exc}"
                    else:
                        entry["error"] = f"generated image missing on disk: {src_generated}"
                else:
                    entry["error"] = entry["error"] or "no image produced by run_agent"

                return entry, len(image_paths)
            except Exception as exc:
                entry["status"] = "failed"
                entry["error"] = f"run_agent raised: {exc}"
                return entry, 0

        # Process all frames in parallel
        tasks = [process_single_frame(idx, frame) for idx, frame in enumerate(selected_paths, start=1)]
        results = await aio.gather(*tasks)
        
        for entry, image_count in results:
            linkage.append(entry)
            generation_diagnostics["real_generation_used"] = True
            generation_diagnostics["real_generation_count"] += 1
            generation_diagnostics["comfy_submission_count"] += 1
            generation_diagnostics["images_per_submission"].append(image_count)
    else:
        generation_diagnostics["generation_strategy"] = "framewise"
        for idx, src_frame in enumerate(selected_paths, start=1):
            src_frame = Path(src_frame).resolve()
            entry: dict[str, Any] = {
                "index": idx,
                "source_frame": str(src_frame),
                "processed_frame": None,
                "run_id": None,
                "prompt_id": None,
                "status": "pending",
                "metadata_path": None,
                "result_path": None,
                "trace_path": None,
                "source_generated_image": None,
                "error": None,
            }

            try:
                result = await run_agent(
                    prompt=prompt,
                    mode="edit",
                    input_image=str(src_frame),
                    canonical_recipe=safe_recipe,
                    status_callback=None,
                )
                generation_diagnostics["real_generation_used"] = True
                generation_diagnostics["real_generation_count"] += 1
                generation_diagnostics["comfy_submission_count"] += 1
                
                # Track images per submission
                asset_report = result.get("asset_report") or {}
                image_paths = asset_report.get("image_paths") or []
                generation_diagnostics["images_per_submission"].append(len(image_paths))
            except Exception as exc:
                entry["status"] = "failed"
                entry["error"] = f"run_agent raised: {exc}"
                linkage.append(entry)
                continue

            entry["status"] = result.get("status", "unknown")
            entry["run_id"] = result.get("run_id")
            entry["trace_path"] = result.get("trace_path")

            asset_report = result.get("asset_report") or {}
            entry["metadata_path"] = asset_report.get("metadata_path") or result.get("metadata_path")
            entry["result_path"] = asset_report.get("result_path")
            entry["prompt_id"] = _extract_prompt_id(
                asset_report.get("summary_path") or result.get("summary_path")
            )

            image_paths = asset_report.get("image_paths") or []
            if image_paths:
                src_generated = Path(image_paths[0])
                entry["source_generated_image"] = str(src_generated)

                if src_generated.exists():
                    dst = processed_dir / f"frame_{idx:06d}.png"
                    try:
                        shutil.copy2(src_generated, dst)
                        entry["processed_frame"] = str(dst)
                    except Exception as exc:
                        entry["error"] = f"copy failed: {exc}"
                else:
                    entry["error"] = f"generated image missing on disk: {src_generated}"
            else:
                entry["error"] = entry["error"] or "no image produced by run_agent"

            linkage.append(entry)

    # Calculate frames generated
    frames_generated = sum(1 for e in linkage if e.get("processed_frame"))
    generation_diagnostics["frames_generated"] = frames_generated

    return linkage, generation_diagnostics
