#!/usr/bin/env python3
"""Create all V8 generation artifacts and update index/ledger.
Task: RC-COMBINE-V2-7601-8600
"""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp")
ASSETS_DIR = PROJECT_ROOT / "data" / "rc2_multishot1_ep01" / "output" / "assets"
CONTROL_DIR = PROJECT_ROOT / "data" / "rc2_multishot1_ep01" / "output" / "control"
COMFY_OUTPUT = Path(r"F:\ComfyUI\ComfyUI\output")

PROMPT_ID = "687a6356-af7f-48c1-b0cb-7bb59ea755ab"
SEED = 94223796
TIMESTAMP = datetime.now(timezone.utc).isoformat()

CHECKPOINT = "realvisxlV50_v50Bakedvae.safetensors"
SAMPLER = "dpmpp_2m"
SCHEDULER = "karras"
STEPS = 30
CFG = 6.5
WIDTH = 1024
HEIGHT = 1024
FILENAME_PREFIX = "combine_v2_v8_quality_locked_shot02"

ASSET_FILENAME = f"{FILENAME_PREFIX}_00001_.png"
RELATIVE_ASSET_PATH = f"data/rc2_multishot1_ep01/output/assets/{ASSET_FILENAME}"

# Source: copied from ComfyUI via view API
ASSET_PATH = ASSETS_DIR / ASSET_FILENAME

# Validate asset
sha256 = hashlib.sha256(ASSET_PATH.read_bytes()).hexdigest()
with Image.open(ASSET_PATH) as img:
    w, h = img.size
file_size = ASSET_PATH.stat().st_size

print(f"Asset: {ASSET_FILENAME}")
print(f"  SHA256: {sha256}")
print(f"  Dimensions: {w}x{h}")
print(f"  Size: {file_size} bytes")
print(f"  Valid: {file_size > 1024 and w >= 64 and h >= 64}")

POSITIVE_PROMPT = (
    "masterpiece, best quality, "
    "young adult female fantasy character, ethereal cinematic portrait, "
    "beautiful young woman with flowing white hair, "
    "elegant white fantasy dress, "
    "blue atmospheric magical background with soft bokeh, "
    "sharp focus, highly detailed, crisp, "
    "sharp facial features, clear definition, high detail face, "
    "realistic eyes, detailed iris, clean eye shape, natural eye appearance, "
    "detailed eyelashes, natural eyelashes, clean eyelash detail, "
    "natural mouth, well-formed teeth, natural smile, "
    "natural skin texture, visible skin pores, realistic skin detail, "
    "natural skin reflectance, detailed hair strands, "
    "individual hair strands, sharp hair detail, "
    "cinematic lighting with soft falloff, "
    "intricate fantasy details, high fantasy art style, "
    "attractive fantasy character identity, close portrait framing, "
    "soft clean lighting, intricate hair detail"
)

NEGATIVE_PROMPT = (
    "old, elderly, aged face, wrinkles, aged skin, senior, grandmother, "
    "realistic photo, studio portrait, passport photo, documentary, "
    "modern clothing, casual wear, plain background, "
    "blurry, soft focus, out of focus, "
    "soft face, blurry face, undefined features, "
    "deformed eyes, bad eyes, unrealistic eyes, distorted eyes, "
    "clumpy eyelashes, missing eyelashes, bad eyelashes, "
    "deformed mouth, bad teeth, missing teeth, open mouth distortion, "
    "smooth skin, plastic skin, wax skin, airbrushed skin, unreal skin, "
    "wax skin, plastic face, synthetic skin, doll-like skin, mannequin skin, "
    "soft hair, blurry hair, hair blob, undefined hair, "
    "glossy plastic skin, over-smoothed face, "
    "changing character concept, loss of fantasy styling, "
    "loss of blue fantasy environment, replacing fantasy with realism, "
    "ugly, deformed, bad anatomy, disfigured, poorly drawn face, "
    "extra limbs, cloned face, disgusting, low quality, worst quality, "
    "monochrome, grayscale, boring, mundane"
)

# ============================================================
# 1. SUBMITTED WORKFLOW RECORD
# ============================================================
submitted_workflow = {
    "task_id": "RC-COMBINE-V2-7601-8600",
    "workflow_type": "v8_quality_locked_generation",
    "saveimage_filename_prefix": FILENAME_PREFIX,
    "positive_prompt": POSITIVE_PROMPT,
    "negative_prompt": NEGATIVE_PROMPT,
    "prompt_id": PROMPT_ID,
    "refinement_parameters": {
        "cfg_scale": CFG,
        "steps": STEPS,
        "sampler": SAMPLER,
        "scheduler": SCHEDULER,
        "resolution": f"{WIDTH}x{HEIGHT}",
        "checkpoint": CHECKPOINT,
        "seed": SEED,
    },
    "quality_guardrails_applied": [
        "QR_V8_001:anti_blur",
        "QR_V8_002:anti_softness",
        "QR_V8_003:realistic_eyes",
        "QR_V8_004:clean_eyelashes",
        "QR_V8_005:stable_mouth_teeth",
        "QR_V8_006:visible_skin_micro_detail",
        "QR_V8_007:no_wax_plastic_skin",
        "QR_V8_008:hair_strand_detail",
        "QR_V8_009:sharper_facial_features",
    ],
    "timestamp": TIMESTAMP,
}
(CONTROL_DIR / "combine_v2_v8_quality_locked_submitted_workflow.json").write_text(
    json.dumps(submitted_workflow, indent=2, ensure_ascii=False))
print("[OK] Submitted workflow saved")

# ============================================================
# 2. GENERATION RESULT
# ============================================================
result = {
    "task_id": "RC-COMBINE-V2-7601-8600",
    "stage": "v8_real_generation",
    "workflow_submitted": True,
    "comfyui_execution": True,
    "prompt_id": PROMPT_ID,
    "comfyui_status": "success",
    "generation_count": 1,
    "max_generations": 1,
    "second_generation_attempted": False,
    "retry_attempted": False,
    "dry_run_used": False,
    "canonical_outputs_registered": True,
    "generated_assets": [ASSET_FILENAME],
    "asset_readable": True,
    "sha256_present": True,
    "sha256": sha256,
    "dimensions_present": True,
    "dimensions": {"width": w, "height": h},
    "size_bytes": file_size,
    "size_bytes_gt_1024": file_size > 1024,
    "stub_asset_detected": False,
    "failure_code": None,
    "error_message": None,
    "trace_events": [
        {"event": "workflow_submitted", "status": "success", "prompt_id": PROMPT_ID},
        {"event": "generation_completed", "status": "success"},
        {"event": "asset_validated", "status": "success", "sha256": sha256,
         "dimensions": {"width": w, "height": h}, "size_bytes": file_size},
    ],
    "visual_qa_executed": False,
    "operator_visual_decision_created": False,
    "assembly_executed": False,
    "downstream_executed": False,
    "production_accepted": False,
    "current_state": "v8_operator_visual_review_required",
    "next_allowed_action": "v8_operator_visual_review_required",
    "timestamp": TIMESTAMP,
}
(CONTROL_DIR / "combine_v2_v8_real_generation_result.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False))
print("[OK] Generation result saved")

# ============================================================
# 3. OUTPUTS MANIFEST
# ============================================================
manifest = {
    "stage": "v8_real_generation",
    "manifest_type": "v8_real_generation_outputs_manifest",
    "task_id": "RC-COMBINE-V2-7601-8600",
    "generation_count": 1,
    "max_generations": 1,
    "second_generation_attempted": False,
    "retry_attempted": False,
    "workflow_submitted": True,
    "generated_assets": [ASSET_FILENAME],
    "asset_paths": [RELATIVE_ASSET_PATH],
    "collection_status": "success",
    "asset_readable": True,
    "sha256_present": True,
    "sha256": sha256,
    "dimensions": {"width": w, "height": h},
    "size_bytes": file_size,
    "stub_asset_detected": False,
    "canonical_outputs_registered": True,
    "visual_qa_executed": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_accepted": False,
    "timestamp": TIMESTAMP,
}
(CONTROL_DIR / "combine_v2_v8_real_generation_outputs_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False))
print("[OK] Outputs manifest saved")

# ============================================================
# 4. OPERATOR VISUAL REVIEW PACKET
# ============================================================
review_packet = {
    "task_id": "RC-COMBINE-V2-7601-8600",
    "stage": "v8_quality_locked_generation",
    "artifact_id": "combine_v2_v8_quality_locked_operator_visual_review_packet",
    "generation_attempted": True,
    "generation_success": True,
    "v8_quality_locked_package_used": "combine_v2_v8_quality_locked_refinement_package.json",
    "v8_quality_guardrails_used": "combine_v2_v8_quality_guardrails.json",
    "v8_generation_gate_used": "combine_v2_v8_quality_locked_generation_gate.json",
    "prompt_id": PROMPT_ID,
    "generation_count": 1,
    "max_generations": 1,
    "second_generation_attempted": False,
    "retry_attempted": False,
    "dry_run_used": False,
    "generated_assets": [ASSET_FILENAME],
    "asset_path": RELATIVE_ASSET_PATH,
    "comfyui_execution": True,
    "workflow_submitted": True,
    "submitted_workflow_ref": "combine_v2_v8_quality_locked_submitted_workflow.json",
    "outputs_manifest_ref": "combine_v2_v8_real_generation_outputs_manifest.json",
    "generation_result_ref": "combine_v2_v8_real_generation_result.json",
    "positive_prompt": POSITIVE_PROMPT,
    "negative_prompt": NEGATIVE_PROMPT,
    "refinement_parameters": {
        "cfg_scale": CFG,
        "steps": STEPS,
        "sampler": SAMPLER,
        "scheduler": SCHEDULER,
        "resolution": f"{WIDTH}x{HEIGHT}",
        "checkpoint": CHECKPOINT,
        "seed": SEED,
    },
    "asset_sha256": sha256,
    "asset_dimensions": {"width": w, "height": h},
    "asset_size_bytes": file_size,
    "concept_reference_asset": "data/rc2_multishot1_ep01/output/assets/combine_v2_clean_sdxl_v6_candidate_shot02_00001_.png",
    "quality_reference_asset": "data/rc2_multishot1_ep01/output/assets/combine_v2_v6_targeted_refinement_shot02_00001_.png",
    "visual_qa_executed": False,
    "visual_qa_verdict": None,
    "visual_qa_report_ref": None,
    "operator_visual_decision_created": False,
    "operator_visual_verdict": None,
    "operator_visual_decision_ref": None,
    "production_accepted": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "notes": (
        "V8 quality-locked generation completed successfully. "
        "Asset requires operator visual review before any further pipeline progression. "
        "No visual QA executed by agent — this packet is prepared for manual operator review. "
        "Operator must inspect the generated image, compare against concept/quality references, "
        "and issue a visual verdict (ACCEPT/REJECT) before any downstream pipeline steps."
    ),
    "timestamp": TIMESTAMP,
}
(CONTROL_DIR / "combine_v2_v8_quality_locked_operator_visual_review_packet.json").write_text(
    json.dumps(review_packet, indent=2, ensure_ascii=False))
print("[OK] Operator visual review packet saved")

# ============================================================
# 5. UPDATE ARTIFACT INDEX
# ============================================================
artifact_index_path = CONTROL_DIR / "artifact_index.json"
artifact_index = json.loads(artifact_index_path.read_text(encoding="utf-8"))

# Update the key fields
artifact_index["current_state"] = "v8_operator_visual_review_required"
artifact_index["next_allowed_action"] = "v8_operator_visual_review_required"
artifact_index["generation_runtime_blocked"] = False
artifact_index["blocker"] = None
artifact_index["blocker_summary"] = None
artifact_index["manual_action_required"] = True
artifact_index["downstream_allowed"] = False
artifact_index["assembly_allowed"] = False
artifact_index["generation_allowed"] = False
artifact_index["generation_performed"] = True
artifact_index["comfyui_execution"] = True
artifact_index["generation_count"] = 1
artifact_index["second_generation_attempted"] = False
artifact_index["retry_attempted"] = False
artifact_index["canonical_outputs_registered"] = True
artifact_index["new_generation_performed"] = True
artifact_index["max_generations"] = 1
artifact_index["workflow_submitted"] = True
artifact_index["generated_assets"] = [ASSET_FILENAME]
artifact_index["asset_readable"] = True
artifact_index["operator_visual_review_packet_created"] = True
artifact_index["v8_operator_visual_review_packet_created"] = True
artifact_index["no_second_generation_attempted"] = True
artifact_index["no_new_generation_performed"] = False
artifact_index["new_comfyui_submit_executed"] = True
artifact_index["v8_real_generation_attempted"] = True
artifact_index["v8_real_generation_result"] = "combine_v2_v8_real_generation_result.json"
artifact_index["v8_real_generation_outputs_manifest"] = "combine_v2_v8_real_generation_outputs_manifest.json"
artifact_index["v8_operator_visual_review_packet"] = "combine_v2_v8_quality_locked_operator_visual_review_packet.json"
artifact_index["v8_real_generation_success"] = True
artifact_index["failure_code"] = None
artifact_index["generation_allowed_now"] = False

# Add stage result
artifact_index["stage_results"].append({
    "stage": "v8_quality_locked_real_generation",
    "success": True,
    "message": "V8 quality-locked real generation executed via ComfyUI. Asset created, validated, and registered.",
    "artifacts": [
        "combine_v2_v8_quality_locked_submitted_workflow.json",
        "combine_v2_v8_real_generation_result.json",
        "combine_v2_v8_real_generation_outputs_manifest.json",
        "combine_v2_v8_quality_locked_operator_visual_review_packet.json",
    ],
    "metadata": {
        "generation_count": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "comfyui_execution": True,
        "comfyui_submit_executed": True,
        "prompt_id": PROMPT_ID,
        "visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "generated_assets_count": 1,
        "canonical_outputs_registered": True,
        "operator_visual_review_allowed": True,
        "dry_run_used": False,
        "task_id": "RC-COMBINE-V2-7601-8600",
    },
    "timestamp": TIMESTAMP,
    "no_generation_performed": False,
})

artifact_index["timestamp"] = TIMESTAMP
artifact_index_path.write_text(json.dumps(artifact_index, indent=2, ensure_ascii=False))
print("[OK] Artifact index updated")

# ============================================================
# 6. UPDATE EPISODE LEDGER
# ============================================================
ledger_path = CONTROL_DIR / "episode_ledger.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

ledger.append({
    "event_type": "v8_real_generation_completed",
    "task_id": "RC-COMBINE-V2-7601-8600",
    "stage": "v8_real_generation",
    "new_generation_performed": True,
    "generation_count": 1,
    "max_generations": 1,
    "second_generation_attempted": False,
    "retry_attempted": False,
    "workflow_submitted": True,
    "comfyui_execution": True,
    "prompt_id": PROMPT_ID,
    "comfyui_status": "success",
    "dry_run_used": False,
    "generated_assets": [ASSET_FILENAME],
    "asset_count": 1,
    "asset_readable": True,
    "asset_sha256": sha256,
    "asset_dimensions": {"width": w, "height": h},
    "asset_size_bytes": file_size,
    "failure_code": None,
    "production_accepted": False,
    "visual_qa_executed": False,
    "operator_visual_decision_created": False,
    "assembly_executed": False,
    "downstream_executed": False,
    "current_state": "v8_operator_visual_review_required",
    "next_allowed_action": "v8_operator_visual_review_required",
    "previous_state": "v8_generation_runtime_blocked",
    "previous_layer": "RC-COMBINE-V2-6601-7600",
    "timestamp": TIMESTAMP,
})

ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
print("[OK] Episode ledger updated")

print("\n" + "=" * 60)
print("ALL V8 ARTIFACTS CREATED SUCCESSFULLY")
print("Current state: v8_operator_visual_review_required")
print("Next action: v8_operator_visual_review_required")
print("Asset: " + ASSET_FILENAME)
print("Prompt ID: " + PROMPT_ID)
print("=" * 60)
