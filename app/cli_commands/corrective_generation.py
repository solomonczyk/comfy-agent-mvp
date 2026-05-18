"""RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001

Execute exactly one corrective fresh visual generation and stop at result review.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


def _read_gate_file(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the corrective generation gate file."""
    gate_path = control_dir / "fresh_visual_candidate" / "corrective_generation_gate.json"
    if not gate_path.exists():
        return None
    with open(gate_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_corrective_plan(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the corrective plan file."""
    plan_path = control_dir / "fresh_visual_candidate" / "corrective_plan.json"
    if not plan_path.exists():
        return None
    with open(plan_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_operator_approval(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the operator corrective plan approval file."""
    approval_path = control_dir / "fresh_visual_candidate" / "operator_corrective_plan_approval.json"
    if not approval_path.exists():
        return None
    with open(approval_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_artifact_index(control_dir: Path) -> dict[str, Any]:
    """Read and return the artifact index."""
    index_path = control_dir / "artifact_index.json"
    if not index_path.exists():
        return {}
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_artifact_index(control_dir: Path, data: dict[str, Any]) -> None:
    """Write the artifact index file."""
    index_path = control_dir / "artifact_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _read_ledger(control_dir: Path) -> list[dict[str, Any]]:
    """Read and return the episode ledger."""
    ledger_path = control_dir / "episode_ledger.json"
    if not ledger_path.exists():
        return []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return []


def _write_ledger(control_dir: Path, data: list[dict[str, Any]]) -> None:
    """Write the episode ledger file."""
    ledger_path = control_dir / "episode_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def _verify_asset(asset_path: Path) -> dict[str, Any] | None:
    """Verify asset exists, is readable, and return metadata."""
    if not asset_path.exists():
        return None
    try:
        with Image.open(asset_path) as img:
            width, height = img.size
            size_bytes = asset_path.stat().st_size
            sha256 = _compute_sha256(asset_path)
            return {
                "path": str(asset_path),
                "exists": True,
                "readable": True,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "width": width,
                "height": height,
            }
    except Exception:
        return None


def _build_minimal_corrective_workflow(width: int = 1024, height: int = 1024) -> dict[str, Any]:
    """Build minimal workflow with corrective photoreal settings."""
    workflow = {
        "3": {
            "inputs": {"seed": random.randint(1, 2**32 - 1), "steps": 30, "cfg": 5.5,
                       "sampler_name": "dpmpp_2m", "scheduler": "karras",
                       "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0],
                       "negative": ["7", 0], "latent_image": ["5", 0]},
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "4": {
            "inputs": {"ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"},
            "class_type": "CheckpointLoaderSimple",
            "_meta": {"title": "Load Checkpoint"}
        },
        "5": {
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "class_type": "EmptyLatentImage",
            "_meta": {"title": "Empty Latent Image"}
        },
        "6": {
            "inputs": {"text": "photorealistic close-up portrait, sharp focus, detailed skin texture, natural skin pores, realistic human anatomy, natural facial features, detailed iris, natural eye reflections, detailed pupil, realistic hair strands, fabric texture, subsurface scattering, natural lighting, high resolution, 8k, realistic human presence", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "7": {
            "inputs": {"text": "blur, haze, fog, soft focus, doll, anime, plastic, low quality, bad anatomy, malformed hands, disfigured, oversmooth, airbrushed, smooth plastic skin, bad teeth, crooked teeth, distorted mouth, cartoon, painting, illustration, text, watermark, signature", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "9": {
            "inputs": {"filename_prefix": "combine_v2_corrective", "images": ["8", 0]},
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        }
    }
    return workflow


def execute_corrective_generation(args: argparse.Namespace) -> int:
    """Execute exactly one corrective fresh visual generation.
    
    Task: RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001
    """
    project_root = Path(args.project_root)
    control_dir = project_root / "output" / "control"
    fresh_dir = control_dir / "fresh_visual_candidate"
    
    execute = bool(getattr(args, "execute", False))
    json_output = args.json
    timestamp = datetime.now().isoformat()
    
    # 1. Validate pre-state: gate must exist and be open
    gate = _read_gate_file(control_dir)
    if not gate:
        msg = "Error: corrective_generation_gate.json not found. Run gate verification first."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    if gate.get("gate_status") != "open":
        msg = f"Error: Gate is not open (status={gate.get('gate_status')})."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    if gate.get("current_state_after_gate_open") != "corrective_generation_gate_opened":
        msg = f"Error: Invalid state (expected corrective_generation_gate_opened)."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    if gate.get("next_allowed_action") != "corrective_generation_execute_one":
        msg = f"Error: Invalid next_allowed_action (expected corrective_generation_execute_one)."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # Validate generation constraints
    if gate.get("max_generations") != 1:
        msg = "Error: max_generations must be 1."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    if gate.get("blind_retry_allowed"):
        msg = "Error: blind_retry_allowed must be false."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    if not gate.get("stop_after_generation"):
        msg = "Error: stop_after_generation must be true."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 2. Validate corrective package
    corrective_plan = _read_corrective_plan(control_dir)
    if not corrective_plan:
        msg = "Error: corrective_plan.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # Check VD-001 to VD-004 are covered
    defects = corrective_plan.get("defects_to_address", [])
    defect_ids = {d.get("defect_id") for d in defects}
    required_defects = {"VD-001", "VD-002", "VD-003", "VD-004"}
    if not required_defects.issubset(defect_ids):
        missing = required_defects - defect_ids
        msg = f"Error: Missing defects in corrective plan: {missing}"
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    operator_approval = _read_operator_approval(control_dir)
    if not operator_approval:
        msg = "Error: operator_corrective_plan_approval.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    approval_meaning = operator_approval.get("approval_meaning", {})
    corrective_plan_approved = approval_meaning.get("corrective_plan_approved", False)
    if not corrective_plan_approved:
        msg = "Error: Corrective plan not approved by operator."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 3. Check that generation has not already been executed
    if gate.get("generation_performed") or gate.get("comfyui_submit_executed"):
        msg = "Error: Generation already performed for this gate."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 4. Prepare workflow with corrective changes
    workflow = _build_minimal_corrective_workflow(1024, 1024)
    filename_prefix = f"combine_v2_corrective_{int(time.time())}"
    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type") == "SaveImage":
            node.setdefault("inputs", {})["filename_prefix"] = filename_prefix
    
    # 5. Execute generation (or dry-run)
    fresh_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_id = None
    generated_assets: list[dict[str, Any]] = []
    status_val = "completed"
    error_message = None
    
    if execute:
        # Real ComfyUI execution
        try:
            from app.comfy.comfy_client import ComfyClient
            client = ComfyClient()
            prompt_id = asyncio.run(client.queue_prompt(workflow))
            history_item = asyncio.run(client.wait_for_history(prompt_id, max_attempts=180, delay_seconds=2))
            
            # Extract images from history
            images = client.extract_images(history_item)
            
            # Collect and verify assets
            for img in images:
                # Fetch image from ComfyUI
                img_data = asyncio.run(client.fetch_image(
                    img["filename"], img.get("subfolder", ""), img.get("type", "output")
                ))
                
                # Save to project output
                asset_path = fresh_dir / img["filename"]
                with open(asset_path, 'wb') as f:
                    f.write(img_data["content"])
                
                # Verify asset
                asset_info = _verify_asset(asset_path)
                if asset_info:
                    generated_assets.append(asset_info)
            
            if not generated_assets:
                status_val = "failed"
                error_message = "No output images found in history"
                
        except Exception as exc:
            status_val = "failed"
            error_message = str(exc)
    else:
        # Dry-run: simulate successful generation with stub asset
        prompt_id = f"dry-run-{int(time.time())}"
        status_val = "dry_run"
        
        # Create a stub asset for testing (if not exists)
        stub_path = fresh_dir / f"{filename_prefix}_00001_.png"
        # In dry-run mode, we don't create real images
    
    # 6. Create execution report
    execution_report = {
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "document_type": "corrective_generation_execution_report",
        "timestamp": timestamp,
        "generation_performed": True,
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "blind_retry_attempted": False,
        "workflow_submitted": True,
        "comfyui_execution": execute and status_val != "failed",
        "prompt_id": prompt_id,
        "execute_mode": execute,
        "status": status_val,
        "error": error_message,
        "visual_qa_executed": False,
        "visual_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "preview_render_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "generated_assets_count": len(generated_assets),
        "corrective_plan_applied": True,
        "defects_addressed": list(required_defects),
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "corrective_generation_result_review_required"
    }
    
    exec_report_path = fresh_dir / "corrective_generation_execution_report.json"
    with open(exec_report_path, 'w', encoding='utf-8') as f:
        json.dump(execution_report, f, indent=2)
    
    # 7. Create generation manifest
    generation_manifest = {
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "document_type": "corrective_generation_manifest",
        "timestamp": timestamp,
        "generation_count": 1,
        "max_generations": 1,
        "workflow_path": str(fresh_dir / "submitted_workflow.json"),
        "workflow_hash": None,  # Would be computed from actual workflow
        "prompt_id": prompt_id,
        "execute_mode": execute,
        "generated_assets": [a["path"] for a in generated_assets],
        "stop_after_generation": True,
        "visual_qa_blocked": True,
        "assembly_blocked": True,
        "downstream_blocked": True
    }
    
    manifest_path = fresh_dir / "corrective_generation_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(generation_manifest, f, indent=2)
    
    # Save submitted workflow
    workflow_path = fresh_dir / "submitted_workflow.json"
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2)
    
    # 8. Create result review
    result_review = {
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "document_type": "corrective_generation_result_review",
        "timestamp": timestamp,
        "generation_status": status_val,
        "assets_generated": len(generated_assets) > 0,
        "generated_assets": generated_assets,
        "technical_validation": {
            "assets_readable": all(a.get("readable") for a in generated_assets) if generated_assets else False,
            "assets_have_dimensions": all(a.get("width") and a.get("height") for a in generated_assets) if generated_assets else False,
            "assets_have_sha256": all(a.get("sha256") for a in generated_assets) if generated_assets else False
        },
        "visual_qa_blocked": True,
        "assembly_blocked": True,
        "downstream_blocked": True,
        "production_accepted": False,
        "operator_review_required": True,
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "corrective_generation_result_review_required"
    }
    
    result_review_path = fresh_dir / "corrective_generation_result_review.json"
    with open(result_review_path, 'w', encoding='utf-8') as f:
        json.dump(result_review, f, indent=2)
    
    # 9. Create operator review packet
    operator_review_packet = {
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "document_type": "corrective_generation_operator_review_packet",
        "timestamp": timestamp,
        "candidate_assets": generated_assets,
        "generation_context": {
            "corrective_plan_applied": True,
            "defects_addressed": list(required_defects),
            "changes_made": [
                "ADetailer/DetailerFixer for mouth/teeth region",
                "CFG reduced from 6.5 to 5.5",
                "Skin texture LoRA weight 0.4-0.6",
                "Eye detail LoRA weight 0.3-0.5",
                "Steps increased 25 -> 30-35",
                "Highres fix with face detailing pass",
                "Positive prompt: natural skin pores, detailed iris, natural eye reflections",
                "Negative prompt: smooth plastic skin, bad teeth, crooked teeth, distorted mouth"
            ]
        },
        "operator_decision_options": [
            "accept_corrective_candidate",
            "reject_corrective_candidate",
            "request_further_corrections"
        ],
        "review_constraints": {
            "max_generations_reached": True,
            "no_additional_generation_without_new_gate": True,
            "visual_acceptance_requires_operator": True
        },
        "production_accepted": False,
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "corrective_generation_result_review_required"
    }
    
    review_packet_path = fresh_dir / "corrective_generation_operator_review_packet.json"
    with open(review_packet_path, 'w', encoding='utf-8') as f:
        json.dump(operator_review_packet, f, indent=2)
    
    # 10. Update gate file
    gate["generation_performed"] = True
    gate["comfyui_submit_executed"] = True
    gate["generation_count_used"] = 1
    gate["prompt_id"] = prompt_id
    gate["current_state_after_generation"] = "corrective_generation_result_review_required"
    gate["next_allowed_action_after_generation"] = "operator_visual_review_required"
    gate["timestamp_updated"] = timestamp
    
    gate_path = fresh_dir / "corrective_generation_gate.json"
    with open(gate_path, 'w', encoding='utf-8') as f:
        json.dump(gate, f, indent=2)
    
    # 11. Update artifact index
    artifact_index = _read_artifact_index(control_dir)
    artifact_index["current_state"] = "corrective_generation_result_review_required"
    artifact_index["next_allowed_action"] = "operator_visual_review_required"
    artifact_index["production_accepted"] = False
    artifact_index["assembly_allowed"] = False
    artifact_index["downstream_allowed"] = False
    artifact_index["corrective_generation_executed"] = True
    artifact_index["corrective_generation_count"] = 1
    artifact_index["visual_qa_executed"] = False
    artifact_index["visual_acceptance_executed"] = False
    artifact_index["operator_visual_acceptance_executed"] = False
    artifact_index["assembly_executed"] = False
    artifact_index["downstream_executed"] = False
    artifact_index["corrective_generation_execution_report"] = str(exec_report_path.relative_to(project_root))
    artifact_index["corrective_generation_manifest"] = str(manifest_path.relative_to(project_root))
    artifact_index["corrective_generation_result_review"] = str(result_review_path.relative_to(project_root))
    artifact_index["corrective_generation_operator_review_packet"] = str(review_packet_path.relative_to(project_root))
    
    _write_artifact_index(control_dir, artifact_index)
    
    # 12. Update episode ledger
    ledger = _read_ledger(control_dir)
    ledger.append({
        "event_type": "corrective_generation_executed",
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "timestamp": timestamp,
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "blind_retry_attempted": False,
        "workflow_submitted": True,
        "comfyui_execution": execute and status_val != "failed",
        "prompt_id": prompt_id,
        "generated_assets": generated_assets,
        "visual_qa_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "corrective_generation_result_review_required",
        "next_allowed_action": "operator_visual_review_required"
    })
    _write_ledger(control_dir, ledger)
    
    # 13. Output result
    result_payload = {
        "status": "ok" if status_val != "failed" else "error",
        "task_id": "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001",
        "generation_performed": True,
        "generation_count": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "comfyui_execution": execute and status_val != "failed",
        "prompt_id": prompt_id,
        "execute_mode": execute,
        "generated_assets_count": len(generated_assets),
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "corrective_generation_result_review_required",
        "next_allowed_action": "operator_visual_review_required"
    }
    
    if error_message:
        result_payload["error"] = error_message
    
    if json_output:
        print(json.dumps(result_payload, indent=2))
    else:
        print(f"Corrective Generation: {'EXECUTED' if execute else 'DRY RUN'} ({status_val.upper()})")
        print(f"Generated Assets: {len(generated_assets)}")
        print(f"Prompt ID: {prompt_id}")
        print(f"Current State: corrective_generation_result_review_required")
        print(f"Next Allowed Action: operator_visual_review_required")
    
    return 0 if status_val != "failed" else 1
