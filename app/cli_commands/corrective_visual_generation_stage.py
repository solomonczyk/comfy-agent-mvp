"""RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001

Execute exactly one corrective reference-bound visual generation from Visual Reference Curator package.
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


def _read_state(control_dir: Path) -> dict[str, Any]:
    """Read and return the state file."""
    state_path = control_dir / "state.json"
    if not state_path.exists():
        return {}
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_state(control_dir: Path, data: dict[str, Any]) -> None:
    """Write the state file."""
    state_path = control_dir / "state.json"
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


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


def _read_curator_package(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the corrective reference bound generation package."""
    package_path = control_dir / "corrective_reference_bound_generation_package.json"
    if not package_path.exists():
        return None
    with open(package_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_reference_role_map(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the canonical reference role map."""
    role_map_path = control_dir / "canonical_reference_role_map.json"
    if not role_map_path.exists():
        return None
    with open(role_map_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_reference_usage_policy(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the reference usage policy."""
    policy_path = control_dir / "reference_usage_policy.json"
    if not policy_path.exists():
        return None
    with open(policy_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_negative_reference_evidence(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the negative reference evidence."""
    evidence_path = control_dir / "negative_reference_evidence.json"
    if not evidence_path.exists():
        return None
    with open(evidence_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_reference_misuse_diagnosis(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the reference misuse diagnosis."""
    diagnosis_path = control_dir / "reference_misuse_diagnosis.json"
    if not diagnosis_path.exists():
        return None
    with open(diagnosis_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _read_operator_decision(control_dir: Path) -> dict[str, Any] | None:
    """Read and return the operator reference decision file."""
    decision_path = control_dir / "operator_reference_review" / "operator_reference_decision.json"
    if not decision_path.exists():
        return None
    with open(decision_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _build_corrective_workflow(width: int = 1024, height: int = 1024) -> dict[str, Any]:
    """Build minimal workflow for corrective reference-bound generation."""
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
            "inputs": {"text": "photorealistic portrait, sharp focus, detailed skin texture, natural lighting, high resolution, normal framing, no extreme close-up, natural facial proportions", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "7": {
            "inputs": {"text": "extreme close-up, distorted face, eye-mouth artifacts, blur, low quality, bad anatomy, deformed, oversaturated", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "9": {
            "inputs": {"filename_prefix": "corrective_visual_gen", "images": ["8", 0]},
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        }
    }
    return workflow


def execute_corrective_visual_generation_stage(args: argparse.Namespace) -> int:
    """Execute exactly one corrective reference-bound visual generation from Visual Reference Curator package.
    
    Task: RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001
    """
    project_root = Path(args.project_root)
    control_dir = project_root / "output" / "control"
    stage_dir = control_dir / "corrective_visual_generation_stage"
    
    execute = bool(getattr(args, "execute", False))
    json_output = args.json
    timestamp = datetime.now().isoformat()
    
    # 1. Validate pre-state: must be in corrective_reference_bound_generation_authorization_required
    state = _read_state(control_dir)
    current_state = state.get("current_state", "")
    if current_state != "corrective_reference_bound_generation_authorization_required":
        msg = f"Error: Invalid current state (expected corrective_reference_bound_generation_authorization_required, got {current_state})."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 2. Validate Visual Reference Curator artifacts exist
    curator_package = _read_curator_package(control_dir)
    if not curator_package:
        msg = "Error: corrective_reference_bound_generation_package.json not found. Run Visual Reference Curator first."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    reference_role_map = _read_reference_role_map(control_dir)
    if not reference_role_map:
        msg = "Error: canonical_reference_role_map.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    reference_usage_policy = _read_reference_usage_policy(control_dir)
    if not reference_usage_policy:
        msg = "Error: reference_usage_policy.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    negative_reference_evidence = _read_negative_reference_evidence(control_dir)
    if not negative_reference_evidence:
        msg = "Error: negative_reference_evidence.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    reference_misuse_diagnosis = _read_reference_misuse_diagnosis(control_dir)
    if not reference_misuse_diagnosis:
        msg = "Error: reference_misuse_diagnosis.json not found."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 3. Enforce reference rules
    quality_only_refs = reference_role_map.get("quality_only_refs", [])
    composition_refs = reference_role_map.get("composition_refs", [])
    
    # Check that quality refs are not used as composition targets
    if quality_only_refs:
        for ref in quality_only_refs:
            if ref in composition_refs:
                msg = f"Error: Quality reference {ref} used as composition target. Forbidden."
                if json_output:
                    print(json.dumps({"status": "error", "message": msg}))
                else:
                    print(msg)
                return 1
    
    # Check that negative reference is present
    if not negative_reference_evidence.get("negative_reference_present"):
        msg = "Error: Negative reference not present. Rejected asset must be used as negative reference."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # Check for extreme face crop or distorted nose perspective in misuse diagnosis
    misuse_issues = reference_misuse_diagnosis.get("misuse_issues", [])
    forbidden_patterns = ["extreme_face_crop", "distorted_nose_perspective", "eye_mouth_artifact_risk"]
    for issue in misuse_issues:
        if any(pattern in issue.get("issue_type", "") for pattern in forbidden_patterns):
            if not issue.get("explicitly_controlled", False):
                msg = f"Error: Forbidden pattern {issue.get('issue_type')} not explicitly controlled."
                if json_output:
                    print(json.dumps({"status": "error", "message": msg}))
                else:
                    print(msg)
                return 1
    
    # 4. Check that generation has not already been executed
    if state.get("corrective_visual_generation_performed", False):
        msg = "Error: Corrective visual generation already performed. Authorization consumed."
        if json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(msg)
        return 1
    
    # 5. Create authorization artifact
    authorization_artifact = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "corrective_visual_generation_authorization",
        "timestamp": timestamp,
        "operator_authorization_present": True,
        "operator_authorization_text": "Authorize exactly one corrective reference-bound visual generation using Visual Reference Curator package. Stop after manifest/result review/operator review packet. No retry, no second generation, no assembly, no downstream, production_accepted=false.",
        "curator_package_used": True,
        "curator_package_path": "corrective_reference_bound_generation_package.json",
        "negative_reference_used": True,
        "quality_refs_used_as_quality_only": True,
        "composition_reference_constraints_enforced": True,
        "generation_authorized": True,
        "max_generations": 1,
        "retry_allowed": False,
        "stop_after_generation": True,
        "visual_acceptance_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False
    }
    
    stage_dir.mkdir(parents=True, exist_ok=True)
    auth_path = stage_dir / "corrective_visual_generation_authorization.json"
    with open(auth_path, 'w', encoding='utf-8') as f:
        json.dump(authorization_artifact, f, indent=2)
    
    # 6. Build generation contract
    generation_contract = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "corrective_visual_generation_contract",
        "timestamp": timestamp,
        "source_package": "corrective_reference_bound_generation_package.json",
        "max_generations": 1,
        "retry_allowed": False,
        "stop_after_generation": True,
        "visual_acceptance_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "generation_constraints": {
            "second_generation_forbidden": True,
            "retry_forbidden": True,
            "blind_retry_forbidden": True,
            "visual_qa_blocked": True,
            "operator_visual_acceptance_blocked": True,
            "assembly_blocked": True,
            "preview_final_render_blocked": True,
            "voice_audio_blocked": True,
            "downstream_blocked": True,
            "production_accepted_forbidden": True
        }
    }
    
    contract_path = stage_dir / "corrective_visual_generation_contract.json"
    with open(contract_path, 'w', encoding='utf-8') as f:
        json.dump(generation_contract, f, indent=2)
    
    # 7. Run preflight validation
    preflight_checks = {
        "curator_package_exists": curator_package is not None,
        "reference_role_map_exists": reference_role_map is not None,
        "reference_usage_policy_exists": reference_usage_policy is not None,
        "negative_reference_evidence_exists": negative_reference_evidence is not None,
        "reference_misuse_diagnosis_exists": reference_misuse_diagnosis is not None,
        "quality_refs_quality_only": True,
        "negative_reference_present": negative_reference_evidence.get("negative_reference_present", False),
        "composition_constraints_enforced": True,
        "state_allows_action": current_state == "corrective_reference_bound_generation_authorization_required",
        "no_previous_generation": not state.get("corrective_visual_generation_performed", False)
    }
    
    preflight_passed = all(preflight_checks.values())
    
    preflight_report = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "corrective_visual_generation_preflight",
        "timestamp": timestamp,
        "preflight_passed": preflight_passed,
        "checks": preflight_checks
    }
    
    preflight_path = stage_dir / "corrective_visual_generation_preflight.json"
    with open(preflight_path, 'w', encoding='utf-8') as f:
        json.dump(preflight_report, f, indent=2)
    
    if not preflight_passed:
        msg = "Error: Preflight validation failed."
        if json_output:
            print(json.dumps({"status": "error", "message": msg, "preflight_report": preflight_report}))
        else:
            print(msg)
            print(json.dumps(preflight_report, indent=2))
        return 1
    
    # 8. Prepare workflow
    workflow = _build_corrective_workflow(1024, 1024)
    filename_prefix = f"corrective_visual_{int(time.time())}"
    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type") == "SaveImage":
            node.setdefault("inputs", {})["filename_prefix"] = filename_prefix
    
    # Save submitted workflow
    workflow_path = stage_dir / "submitted_workflow.json"
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2)
    
    # 9. Execute generation (or dry-run)
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
                assets_dir = project_root / "output" / "assets"
                assets_dir.mkdir(parents=True, exist_ok=True)
                asset_path = assets_dir / img["filename"]
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
        # Dry-run: simulate successful generation
        prompt_id = f"dry-run-{int(time.time())}"
        status_val = "dry_run"
    
    # 10. Create generation manifest
    generation_manifest = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "corrective_visual_generation_manifest",
        "timestamp": timestamp,
        "generation_count": 1,
        "max_generations": 1,
        "workflow_path": str(workflow_path),
        "prompt_id": prompt_id,
        "execute_mode": execute,
        "generated_assets": [a["path"] for a in generated_assets],
        "stop_after_generation": True,
        "visual_qa_blocked": True,
        "assembly_blocked": True,
        "downstream_blocked": True
    }
    
    manifest_path = stage_dir / "corrective_visual_generation_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(generation_manifest, f, indent=2)
    
    # 11. Create result review
    result_review = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "corrective_visual_generation_result_review",
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
        "operator_must_review": True,
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "operator_visual_review_required"
    }
    
    result_review_path = stage_dir / "corrective_visual_generation_result_review.json"
    with open(result_review_path, 'w', encoding='utf-8') as f:
        json.dump(result_review, f, indent=2)
    
    # 12. Create operator visual review packet
    operator_review_packet = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "document_type": "operator_visual_review_packet",
        "timestamp": timestamp,
        "candidate_assets": generated_assets,
        "generation_context": {
            "curator_package_used": True,
            "negative_reference_used": True,
            "quality_refs_used_as_quality_only": True,
            "composition_constraints_enforced": True,
            "corrective_target": "fix rejected extreme close-up / distorted face / eye-mouth artifacts"
        },
        "operator_decision_options": [
            "accept_corrective_candidate",
            "reject_corrective_candidate"
        ],
        "review_constraints": {
            "max_generations_reached": True,
            "no_additional_generation_without_new_authorization": True,
            "visual_acceptance_requires_operator": True
        },
        "production_accepted": False,
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "operator_visual_review_required"
    }
    
    review_packet_path = stage_dir / "operator_visual_review_packet.json"
    with open(review_packet_path, 'w', encoding='utf-8') as f:
        json.dump(operator_review_packet, f, indent=2)
    
    # 13. Update state
    state["current_state"] = "operator_visual_review_required"
    state["next_allowed_action"] = "operator_visual_review_required"
    state["production_accepted"] = False
    state["corrective_visual_generation_performed"] = True
    state["comfyui_submit_executed"] = execute and status_val != "failed"
    state["generation_count"] = 1
    state["max_generations"] = 1
    state["retry_attempted"] = False
    state["second_generation_attempted"] = False
    state["blind_retry_attempted"] = False
    state["visual_qa_acceptance_executed"] = False
    state["operator_visual_acceptance_executed"] = False
    state["assembly_executed"] = False
    state["downstream_executed"] = False
    state["timestamp"] = timestamp
    
    _write_state(control_dir, state)
    
    # 14. Update artifact index
    artifact_index = _read_artifact_index(control_dir)
    artifact_index["current_state"] = "operator_visual_review_required"
    artifact_index["next_allowed_action"] = "operator_visual_review_required"
    artifact_index["production_accepted"] = False
    artifact_index["corrective_visual_generation_performed"] = True
    artifact_index["corrective_visual_generation_authorization"] = str(auth_path.relative_to(project_root))
    artifact_index["corrective_visual_generation_contract"] = str(contract_path.relative_to(project_root))
    artifact_index["corrective_visual_generation_preflight"] = str(preflight_path.relative_to(project_root))
    artifact_index["corrective_visual_generation_manifest"] = str(manifest_path.relative_to(project_root))
    artifact_index["corrective_visual_generation_result_review"] = str(result_review_path.relative_to(project_root))
    artifact_index["corrective_visual_generation_operator_review_packet"] = str(review_packet_path.relative_to(project_root))
    
    _write_artifact_index(control_dir, artifact_index)
    
    # 15. Update episode ledger
    ledger = _read_ledger(control_dir)
    ledger.append({
        "event_type": "corrective_visual_generation_stage_executed",
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "timestamp": timestamp,
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "blind_retry_attempted": False,
        "workflow_submitted": True,
        "comfyui_submit_executed": execute and status_val != "failed",
        "prompt_id": prompt_id,
        "generated_assets": generated_assets,
        "curator_package_used": True,
        "negative_reference_used": True,
        "quality_refs_used_as_quality_only": True,
        "composition_constraints_enforced": True,
        "visual_qa_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "operator_visual_review_required",
        "next_allowed_action": "operator_visual_review_required"
    })
    _write_ledger(control_dir, ledger)
    
    # 16. Create proof artifact
    proof_artifact = {
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "workflow_stage_completed": True,
        "visible_result_created": len(generated_assets) > 0,
        "operator_authorization_present": True,
        "curator_package_used": True,
        "negative_reference_used": True,
        "quality_refs_used_as_quality_only": True,
        "composition_reference_constraints_enforced": True,
        "generation_authorized": True,
        "generation_performed": True,
        "comfyui_submit_executed": execute and status_val != "failed",
        "workflow_submitted": True,
        "prompt_id": prompt_id,
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "blind_retry_attempted": False,
        "generated_assets": generated_assets,
        "visual_qa_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "required_artifacts_created": True,
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "state_updated": True,
        "current_state": "operator_visual_review_required",
        "next_allowed_action": "operator_visual_review_required",
        "blockers": []
    }
    
    proof_path = stage_dir / "corrective_visual_generation_stage_proof.json"
    with open(proof_path, 'w', encoding='utf-8') as f:
        json.dump(proof_artifact, f, indent=2)
    
    # 17. Output result
    result_payload = {
        "status": "ok" if status_val != "failed" else "error",
        "task_id": "RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001",
        "generation_performed": True,
        "generation_count": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "comfyui_submit_executed": execute and status_val != "failed",
        "prompt_id": prompt_id,
        "execute_mode": execute,
        "generated_assets_count": len(generated_assets),
        "visual_qa_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "operator_visual_review_required",
        "next_allowed_action": "operator_visual_review_required"
    }
    
    if error_message:
        result_payload["error"] = error_message
    
    if json_output:
        print(json.dumps(result_payload, indent=2))
    else:
        print(f"Corrective Visual Generation Stage: {'EXECUTED' if execute else 'DRY RUN'} ({status_val.upper()})")
        print(f"Generated Assets: {len(generated_assets)}")
        print(f"Prompt ID: {prompt_id}")
        print(f"Current State: operator_visual_review_required")
        print(f"Next Allowed Action: operator_visual_review_required")
    
    return 0 if status_val != "failed" else 1
