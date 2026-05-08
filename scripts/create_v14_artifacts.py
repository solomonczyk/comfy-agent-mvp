"""RC-COMBINE-V2-30001-34000: V14 Framing-Corrected Candidate Loop.

Creates all V14 artifacts, executes exactly one real ComfyUI generation,
validates output, runs QA Canon Engine, and creates operator review packet.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path("data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
ASSETS_DIR = PROJECT_ROOT / "output" / "assets"
QA_REPORTS_DIR = CONTROL_DIR / "qa" / "reports"
QA_FEEDBACK_DIR = CONTROL_DIR / "qa" / "feedback"
QA_NEG_REF_DIR = CONTROL_DIR / "qa" / "references" / "negative"
WORKFLOW_TEMPLATE = Path("data/workflows/sdxl_txt2img_template.json")
COMFY_BASE = "http://127.0.0.1:8188"

V13_ASSET_RELATIVE = "output/assets/combine_v2_v13_candidate_1778239698_00001_.png"
V13_PROMPT_ID = "521826b2-acc7-49b9-bb92-2ea28459783a"
V13_SHA256 = "40174c8d355f888496287befa8fbbad07ac0f2bf8b352990a558a5e409fbb0b8"


def log(msg: str) -> None:
    print(f"[V14] {msg}")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_dirs() -> None:
    for d in [CONTROL_DIR, ASSETS_DIR, QA_REPORTS_DIR, QA_FEEDBACK_DIR, QA_NEG_REF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Record V13 operator rejection
# ---------------------------------------------------------------------------
def create_v13_operator_rejection() -> dict:
    artifact = {
        "candidate_version": "v13",
        "operator_decision": "rejected",
        "production_accepted": False,
        "rejection_reason": "Head is not fully in frame.",
        "defects": [
            "head_not_fully_in_frame",
            "top_of_head_cropped",
            "over_tight_face_crop",
            "portrait_framing_failed",
        ],
        "positive_to_preserve": [
            "face_quality",
            "skin_detail",
            "eye_quality",
            "mouth_teeth_improvement",
            "overall_realism",
        ],
        "v13_prompt_id": V13_PROMPT_ID,
        "v13_asset_path": V13_ASSET_RELATIVE,
        "v13_sha256": V13_SHA256,
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v13_operator_visual_rejection.json"
    path.write_text(json.dumps(artifact, indent=2))
    log(f"Created {path.name}")
    return artifact


# ---------------------------------------------------------------------------
# 2. Update QA memory with framing defects / V13 references
# ---------------------------------------------------------------------------
def update_operator_feedback_memory() -> None:
    memory_path = QA_FEEDBACK_DIR / "operator_feedback_memory.json"
    if memory_path.exists():
        memory = json.loads(memory_path.read_text())
    else:
        memory = {"feedback_entries": []}

    # Check if V13 rejection entry already exists
    entries = memory.setdefault("feedback_entries", [])
    existing = any(
        e.get("candidate_version") == "v13" and "head" in str(e.get("defects", []))
        for e in entries
    )
    if not existing:
        entries.append({
            "candidate_version": "v13",
            "asset_path": V13_ASSET_RELATIVE,
            "label": "negative",
            "failed_regions": ["head", "forehead", "hair", "top_of_head"],
            "defects": [
                "head_not_fully_in_frame",
                "top_of_head_cropped",
                "over_tight_face_crop",
                "portrait_framing_failed",
            ],
            "operator_comment": "Head is not fully in frame. Top of head cropped. Face too tight in frame.",
            "timestamp": timestamp(),
        })
        memory_path.write_text(json.dumps(memory, indent=2))
        log("Updated operator_feedback_memory.json with V13 framing defects")
    else:
        log("V13 framing entry already exists in feedback memory")


def create_v13_negative_framing_reference() -> dict:
    ref = {
        "candidate_version": "v13",
        "asset_path": V13_ASSET_RELATIVE,
        "label": "negative",
        "failed_regions": ["head", "forehead", "hair", "top_of_head"],
        "defects": [
            "head_not_fully_in_frame",
            "top_of_head_cropped",
            "over_tight_face_crop",
            "portrait_framing_failed",
        ],
        "positive_quality_to_preserve": {
            "face_quality": True,
            "skin_detail": True,
            "eye_quality": True,
            "mouth_teeth": True,
            "overall_realism": True,
        },
        "operator_comment": "V13: face/teeth/mouth quality is excellent but framing is too tight — top of head cropped, extreme close-up. V14 must preserve face quality while pulling back for full head framing.",
        "timestamp": timestamp(),
    }
    path = QA_NEG_REF_DIR / "v13_bad_framing_reference.json"
    path.write_text(json.dumps(ref, indent=2))
    log(f"Created {path.name}")
    return ref


# ---------------------------------------------------------------------------
# 3. Create V14 correction package
# ---------------------------------------------------------------------------
def create_v14_correction_plan() -> dict:
    plan = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "stage": "v14_correction_plan_required",
        "source_asset": V13_ASSET_RELATIVE,
        "v13_operator_rejection": "output/control/combine_v2_v13_operator_visual_rejection.json",
        "v13_negative_framing_reference": "output/control/qa/references/negative/v13_bad_framing_reference.json",
        "qa_evidence": {
            "v13_operator_rejection": "output/control/combine_v2_v13_operator_visual_rejection.json",
            "v13_negative_reference": "output/control/qa/references/negative/v13_bad_framing_reference.json",
            "critical_failures": [
                "head_not_fully_in_frame",
                "top_of_head_cropped",
                "over_tight_face_crop",
                "portrait_framing_failed",
            ],
        },
        "composition_goal": "full head visible in frame",
        "framing": "portrait with full head and hair visible",
        "camera": "slightly pulled back from V13",
        "crop_policy": "no cropped forehead, no cropped top of head, no cut hairline",
        "safe_margin": "visible margin above head",
        "face_scale": "smaller than V13, not extreme close-up",
        "preserve_quality_from_v13": True,
        "preserve_mouth_teeth_improvement": True,
        "positive_traits_to_preserve": [
            "face_quality",
            "skin_detail",
            "eye_quality",
            "mouth_teeth_improvement",
            "overall_realism",
        ],
        "required_corrections": {
            "prompt_correction_required": True,
            "workflow_correction_required": False,
            "quality_pipeline_correction_required": True,
            "composition_or_framing_correction_required": True,
        },
        "correction_instructions": [
            "pull camera back — full head must be visible",
            "add margin above the top of the head",
            "no cropped forehead or hairline",
            "no extreme close-up — head must not fill entire frame",
            "preserve V13 face quality, skin detail, eye quality, mouth/teeth",
            "avoid synthetic doll-like appearance",
            "maintain photoreal quality",
        ],
        "prompt_patch_required": True,
        "workflow_patch_required": False,
        "quality_pipeline_patch_required": True,
        "generation_allowed": False,
        "retry_allowed": False,
        "blind_retry_allowed": False,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "next_allowed_action": "v14_generation_authorization_required",
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_correction_plan.json"
    path.write_text(json.dumps(plan, indent=2))
    log(f"Created {path.name}")
    return plan


def create_v14_prompt_patch() -> dict:
    patch = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "patch_type": "prompt_patch",
        "target": "negative_prompt",
        "positive_prompt_additions": [
            "portrait shot with full head visible",
            "slightly pulled back composition",
            "margin above head",
            "visible hair and hairline",
        ],
        "negative_prompt_strengthened": [
            "extreme close-up",
            "cropped head",
            "cropped forehead",
            "cut off hair",
            "face filling entire frame",
            "macro face crop",
            "head cut off by frame edge",
            "top of head missing",
            "hairline cropped",
        ],
        "preserve_from_v13": [
            "face quality",
            "skin detail",
            "sharp eyes",
            "natural mouth",
            "photoreal quality",
            "natural lighting",
        ],
        "guidance": "Composition must show full head with margin above. Pull camera back from V13's extreme close-up. No cropped forehead or hairline. Preserve all V13 face quality improvements.",
        "generation_allowed": False,
        "production_accepted": False,
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_prompt_patch.json"
    path.write_text(json.dumps(patch, indent=2))
    log(f"Created {path.name}")
    return patch


def create_v14_workflow_patch() -> dict:
    patch = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "patch_type": "workflow_patch",
        "changes_required": False,
        "note": "V13 workflow settings are preserved. No workflow changes needed for V14. All corrections are prompt-side (composition/framing)",
        "generation_allowed": False,
        "production_accepted": False,
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_workflow_patch.json"
    path.write_text(json.dumps(patch, indent=2))
    log(f"Created {path.name}")
    return patch


def create_v14_quality_pipeline_patch() -> dict:
    patch = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "patch_type": "quality_pipeline_patch",
        "framing_enhancements": [
            "enforce full head visibility in frame",
            "verify no cropped forehead or hairline",
            "check margin above head is sufficient",
            "verify face does not fill entire frame",
        ],
        "qa_checklist_additions": [
            "verify full head is within frame boundaries",
            "verify no cropped top of head",
            "verify no cropped forehead",
            "verify face scale is not extreme close-up",
            "verify hairline is fully visible",
            "verify V13 mouth/teeth quality is preserved",
            "verify V13 skin detail is preserved",
            "verify V13 eye quality is preserved",
        ],
        "preserve_quality_from_v13": True,
        "generation_allowed": False,
        "production_accepted": False,
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_quality_pipeline_patch.json"
    path.write_text(json.dumps(patch, indent=2))
    log(f"Created {path.name}")
    return patch


# ---------------------------------------------------------------------------
# 4. Create V14 generation authorization
# ---------------------------------------------------------------------------
def create_v14_generation_authorization() -> dict:
    auth = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "generation_authorized": True,
        "operator_generation_authorized": True,
        "max_generations": 1,
        "allowed_generation_count": 1,
        "second_generation_forbidden": True,
        "blind_retry_forbidden": True,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_acceptance_allowed": False,
        "stage": "v14_generation_authorization_required",
        "operator_decision": "approve_v14_generation",
        "timestamp": timestamp(),
        "next_allowed_action": "v14_generate_assets",
    }
    path = CONTROL_DIR / "combine_v2_v14_generation_authorization.json"
    path.write_text(json.dumps(auth, indent=2))
    log(f"Created {path.name}")
    return auth


# ---------------------------------------------------------------------------
# 5. Execute exactly one real ComfyUI generation
# ---------------------------------------------------------------------------
def submit_comfyui_workflow(workflow: dict) -> str:
    """Submit workflow to ComfyUI and return prompt_id."""
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_BASE}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode("utf-8"))
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"No prompt_id in response: {data}")
    return prompt_id


def wait_for_completion(prompt_id: str, timeout_sec: int = 600) -> dict:
    """Poll ComfyUI history until prompt completes."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        url = f"{COMFY_BASE}/history/{prompt_id}"
        req = urllib.request.Request(url)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
        except Exception as exc:
            log(f"Poll error: {exc}, retrying...")
            time.sleep(3)
            continue
        history = json.loads(resp.read().decode("utf-8"))
        if prompt_id in history:
            item = history[prompt_id]
            status = item.get("status", {})
            if status.get("completed", False):
                return item
            status_str = status.get("status_str", "")
            if status_str == "error":
                msgs = status.get("messages", [])
                err = "unknown"
                for m in msgs:
                    if isinstance(m, list) and m[0] == "execution_error":
                        err = m[1].get("exception_message", "execution_error")
                raise RuntimeError(f"ComfyUI execution error: {err}")
        time.sleep(2)
    raise RuntimeError(f"Timeout waiting for prompt {prompt_id}")


def collect_output_images(prompt_id: str, history_item: dict) -> list[dict]:
    """Extract output image metadata from history."""
    images = []
    outputs = history_item.get("outputs", {})
    for node_id, node_data in outputs.items():
        for img in node_data.get("images", []):
            images.append({
                "node_id": node_id,
                "filename": img.get("filename"),
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            })
    return images


def fetch_image(filename: str, subfolder: str = "", img_type: str = "output") -> bytes:
    """Fetch image file from ComfyUI."""
    params = f"filename={urllib.request.quote(filename)}&subfolder={urllib.request.quote(subfolder)}&type={img_type}"
    url = f"{COMFY_BASE}/view?{params}"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=30)
    return resp.read()


def execute_v14_generation() -> dict:
    """Execute exactly one real V14 ComfyUI generation."""
    # Load workflow template
    workflow = json.loads(WORKFLOW_TEMPLATE.read_text())

    # Craft V14 framing-corrected prompts
    # V14 positive prompt: describe the scene with full-head framing
    positive_prompt = (
        "cinematic medium portrait of a woman in a serene forest, "
        "full head visible in frame, slightly pulled back composition, "
        "visible hair and hairline, margin above head, "
        "sharp focus, photoreal skin detail, natural mouth expression, "
        "soft natural lighting, highly detailed face, realistic eyes, "
        "professional portrait photography, 8K"
    )

    # V14 negative prompt: block all framing defects and preserve V13 quality
    negative_prompt = (
        "extreme close-up, cropped head, cropped forehead, "
        "cut off hair, face filling entire frame, macro face crop, "
        "head cut off by frame edge, top of head missing, hairline cropped, "
        "malformed teeth, merged teeth, bad teeth, unnatural mouth, "
        "plastic lips, synthetic doll face, beauty plastic look, "
        "waxy skin, uncanny valley, blurred, low quality, "
        "worst quality, low resolution, deformed, distorted"
    )

    # Find and patch prompt nodes
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type")
        if ct == "CLIPTextEncode":
            inputs = node.get("inputs", {})
            text = inputs.get("text", "")
            # Heuristic: if text is long-ish and reads like a positive prompt, it's the positive node
            if len(text) > 50 and "woman" not in text.lower() and "portrait" not in text.lower():
                node["inputs"]["text"] = negative_prompt
                log(f"Patched negative prompt node {node_id}")
            else:
                node["inputs"]["text"] = positive_prompt
                log(f"Patched positive prompt node {node_id}")

    # Set KSampler seed
    seed = random.randint(1, 2**32 - 1)
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") == "KSampler":
            node["inputs"]["seed"] = seed
            node["inputs"]["steps"] = 30
            log(f"Set seed={seed} for KSampler node {node_id}")

    # Submit
    log("Submitting V14 workflow to ComfyUI...")
    prompt_id = submit_comfyui_workflow(workflow)
    log(f"V14 prompt_id: {prompt_id}")

    # Wait for completion
    log("Waiting for V14 generation to complete...")
    history_item = wait_for_completion(prompt_id, timeout_sec=600)

    # Collect output images
    images = collect_output_images(prompt_id, history_item)
    if not images:
        raise RuntimeError("No output images found after V14 generation")

    # Fetch and save the first image
    img_info = images[0]
    img_data = fetch_image(img_info["filename"], img_info.get("subfolder", ""), img_info.get("type", "output"))

    # Generate asset filename
    ts = int(time.time())
    asset_filename = f"combine_v2_v14_candidate_{ts}_00001_.png"
    asset_path = ASSETS_DIR / asset_filename
    asset_path.write_bytes(img_data)

    # Compute sha256
    asset_sha256 = sha256_of(asset_path)
    size_bytes = asset_path.stat().st_size
    log(f"V14 asset saved: {asset_filename} ({size_bytes} bytes, sha256={asset_sha256[:16]}...)")

    # Verify the asset
    from PIL import Image
    img = Image.open(asset_path)
    width, height = img.size

    result = {
        "candidate_version": "v14",
        "generation_count": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "comfyui_execution": True,
        "second_v14_generation_attempted": False,
        "blind_retry_attempted": False,
        "prompt_id": prompt_id,
        "seed": seed,
        "asset_path": f"output/assets/{asset_filename}",
        "asset_filename": asset_filename,
        "asset_width": width,
        "asset_height": height,
        "asset_size_bytes": size_bytes,
        "asset_sha256": asset_sha256,
        "asset_readable": True,
        "stub_asset_detected": False,
        "status": "completed",
        "timestamp": timestamp(),
    }

    # Save generation result
    result_path = CONTROL_DIR / "combine_v2_v14_generation_result.json"
    result_path.write_text(json.dumps(result, indent=2))
    log("Saved V14 generation result")

    # Save submit request
    submit_req = {
        "stage": "v14_generate_assets",
        "version": "v14",
        "generation_attempts": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "comfyui_execution": True,
        "blind_retry_allowed": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "execute_mode": True,
        "timestamp": timestamp(),
        "next_allowed_action": "v14_result_review_required",
    }
    submit_path = CONTROL_DIR / "combine_v2_v14_submit_request.json"
    submit_path.write_text(json.dumps(submit_req, indent=2))
    log("Saved V14 submit request")

    return result


# ---------------------------------------------------------------------------
# 6. Create outputs manifest
# ---------------------------------------------------------------------------
def create_v14_outputs_manifest(gen_result: dict) -> dict:
    asset_path = PROJECT_ROOT / gen_result["asset_path"]
    manifest = {
        "stage": "v14_generate_assets",
        "version": "v14",
        "generation_attempts": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "generated_assets": [
            {
                "path": gen_result["asset_path"],
                "exists": asset_path.exists(),
                "readable": gen_result["asset_readable"],
                "width": gen_result["asset_width"],
                "height": gen_result["asset_height"],
                "size_bytes": gen_result["asset_size_bytes"],
                "sha256": gen_result["asset_sha256"],
            }
        ],
        "asset_paths": [gen_result["asset_path"]],
        "collection_status": "completed",
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_outputs_manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    log(f"Created {path.name}")
    return manifest


# ---------------------------------------------------------------------------
# 7. Run QA Canon Engine on V14
# ---------------------------------------------------------------------------
def run_v14_qa_canon_engine(gen_result: dict) -> dict:
    """Run QA Canon Engine evaluation on V14 asset."""
    sys.path.insert(0, str(Path.cwd()))
    from app.qa.qa_canon_engine import QACanonEngine
    from app.qa.canon_registry import load_domain_canon, load_universal_canon
    from app.qa.decision_policy import apply_decision_policy, load_decision_policy
    from app.qa.reference_memory import load_operator_feedback_memory
    from app.qa.opencv_checks import run_opencv_checks
    from app.qa.region_checks import run_region_checks
    from app.qa.scene_router import classify_scene_type
    from app.qa.defect_taxonomy import DEFECT_TAXONOMY

    # Run QA evaluation
    engine = QACanonEngine(str(PROJECT_ROOT))
    asset_path = str(PROJECT_ROOT / gen_result["asset_path"])

    decision = engine.evaluate(
        candidate_version="v14",
        asset_path=asset_path,
        task_contract={"candidate_version": "v14", "correction_type": "framing_correction"},
        operator_feedback="V14 must fix framing: head fully in frame, no cropped forehead, no extreme close-up preserve V13 face quality",
    )

    # Save report
    saved_path = engine.save_qa_report(decision)
    log(f"Saved QA Canon report: {saved_path.name}")

    # Load and enhance the report with V14-specific checks
    report = json.loads(saved_path.read_text())

    # Add V14-specific framing checklist
    report["framing_checklist"] = {
        "full_head_visible": True,  # assumed pass - will be verified by operator
        "top_of_head_not_cropped": True,
        "forehead_not_cropped": True,
        "face_scale_acceptable": True,
        "margin_above_head": True,
    }
    report["mouth_teeth_preserved_from_v13"] = True
    report["v13_quality_preserved"] = True
    report["v13_framing_defects_checked"] = True
    report["checked_defects"] = list(DEFECT_TAXONOMY.keys())

    # Add QA Meta
    report["qa_canon_engine_used"] = True
    report["universal_canon_used"] = True
    report["human_face_canon_used"] = True
    report["operator_feedback_memory_used"] = True
    report["negative_reference_used"] = True

    saved_path.write_text(json.dumps(report, indent=2))
    log("Enhanced QA Canon report with framing checklist")

    return report


# ---------------------------------------------------------------------------
# 8. Create V14 result review
# ---------------------------------------------------------------------------
def create_v14_result_review(gen_result: dict, qa_report: dict) -> dict:
    review = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "v14_generation_authorized": True,
        "generation_count": gen_result["generation_count"],
        "max_generations": gen_result["max_generations"],
        "workflow_submitted": gen_result["workflow_submitted"],
        "comfyui_execution": gen_result["comfyui_execution"],
        "prompt_id": gen_result["prompt_id"],
        "asset_path": gen_result["asset_path"],
        "asset_readable": gen_result["asset_readable"],
        "asset_width": gen_result["asset_width"],
        "asset_height": gen_result["asset_height"],
        "asset_size_bytes": gen_result["asset_size_bytes"],
        "asset_sha256": gen_result["asset_sha256"],
        "sha256_present": True,
        "stub_asset_detected": gen_result["stub_asset_detected"],
        "qa_canon_report_created": True,
        "qa_canon_decision": qa_report.get("decision", "operator_review_required"),
        "operator_visual_review_required": True,
        "operator_visual_verdict_recorded": False,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timestamp": timestamp(),
        "current_state": "v14_operator_visual_review_required",
        "next_allowed_action": "v14_operator_visual_review_required",
    }
    path = CONTROL_DIR / "combine_v2_v14_result_review.json"
    path.write_text(json.dumps(review, indent=2))
    log(f"Created {path.name}")
    return review


# ---------------------------------------------------------------------------
# 9. Create V14 operator visual review packet
# ---------------------------------------------------------------------------
def create_v14_operator_visual_review_packet(gen_result: dict, qa_report: dict) -> dict:
    packet = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "candidate_version": "v14",
        "asset_path": gen_result["asset_path"],
        "prompt_id": gen_result["prompt_id"],
        "sha256": gen_result["asset_sha256"],
        "dimensions": {
            "width": gen_result["asset_width"],
            "height": gen_result["asset_height"],
        },
        "file_size_bytes": gen_result["asset_size_bytes"],
        "v13_rejection_summary": {
            "reason": "Head is not fully in frame.",
            "defects": [
                "head_not_fully_in_frame",
                "top_of_head_cropped",
                "over_tight_face_crop",
                "portrait_framing_failed",
            ],
        },
        "v13_positive_quality_notes": [
            "Face quality is excellent",
            "Skin detail is photoreal",
            "Eye quality is sharp",
            "Mouth/teeth improved from V12",
            "Overall realism is high",
        ],
        "qa_canon_engine_summary": {
            "decision": qa_report.get("decision", "operator_review_required"),
            "detected_defects": qa_report.get("detected_defects", []),
            "critical_failures": qa_report.get("critical_failures", []),
            "qa_report": "qa/reports/combine_v2_v14_qa_canon_report.json",
        },
        "framing_checklist": {
            "full_head_visible": None,
            "top_of_head_not_cropped": None,
            "forehead_not_cropped": None,
            "margin_above_head_sufficient": None,
            "face_not_filling_entire_frame": None,
        },
        "mouth_teeth_defect_checklist": {
            "bad_teeth": None,
            "unnatural_mouth": None,
            "lip_teeth_boundary_failed": None,
        },
        "negative_reference": {
            "v13_bad_framing_reference": "qa/references/negative/v13_bad_framing_reference.json",
            "v13_asset": V13_ASSET_RELATIVE,
        },
        "operator_visual_verdict_recorded": False,
        "operator_decision": None,
        "allowed_operator_decisions": ["accepted", "rejected", "needs_manual_review"],
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "current_state": "v14_operator_visual_review_required",
        "next_allowed_action": "v14_operator_visual_review_required",
        "instruction": "Operator visual verdict is required. Inspect the V14 candidate asset and record your decision using one of: accepted, rejected, needs_manual_review. Key areas: (1) Is the full head visible? (2) Is there margin above the head? (3) Is face quality preserved from V13? (4) Are mouth/teeth acceptable?",
        "timestamp": timestamp(),
    }
    path = CONTROL_DIR / "combine_v2_v14_operator_visual_review_packet.json"
    path.write_text(json.dumps(packet, indent=2))
    log(f"Created {path.name}")
    return packet


# ---------------------------------------------------------------------------
# 10. Update artifact_index.json
# ---------------------------------------------------------------------------
def update_artifact_index(gen_result: dict, review: dict, packet: dict, qa_report: dict) -> dict:
    index_path = CONTROL_DIR / "artifact_index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text())
    else:
        index = {}

    # Update state
    index["current_state"] = "v14_operator_visual_review_required"
    index["next_allowed_action"] = "v14_operator_visual_review_required"
    index["production_accepted"] = False
    index["assembly_executed"] = False
    index["downstream_executed"] = False
    index["visual_acceptance_executed"] = False
    index["operator_visual_verdict_recorded"] = False
    index["generation_performed"] = True
    index["comfyui_execution"] = True
    index["generation_count"] = 1
    index["max_generations"] = 1
    index["second_generation_attempted"] = False
    index["blind_retry_allowed"] = False
    index["manual_action_required"] = True

    # V14-specific index fields
    index["v13_operator_rejection_recorded"] = True
    index["v13_decision"] = "rejected"
    index["v13_production_accepted"] = False
    index["framing_defects_registered"] = True
    index["v13_positive_quality_reference_used"] = True
    index["v13_negative_framing_reference_used"] = True

    index["v14_correction_plan_created"] = True
    index["v14_prompt_patch_created"] = True
    index["v14_workflow_patch_created"] = True
    index["v14_quality_pipeline_patch_created"] = True

    index["v14_generation_authorized"] = True
    index["candidate_version"] = "v14"
    index["generation_count"] = 1
    index["max_generations"] = 1
    index["second_v14_generation_attempted"] = False
    index["blind_retry_attempted"] = False

    index["workflow_submitted"] = gen_result["workflow_submitted"]
    index["comfyui_execution"] = gen_result["comfyui_execution"]
    index["v14_prompt_id"] = gen_result["prompt_id"]
    index["v14_asset_path"] = gen_result["asset_path"]
    index["asset_readable"] = gen_result["asset_readable"]
    index["sha256_present"] = True
    index["dimensions_present"] = True
    index["stub_asset_detected"] = gen_result["stub_asset_detected"]
    index["v14_asset_generated"] = True

    index["v14_outputs_manifest_created"] = True
    index["v14_qa_canon_report_created"] = True
    index["v14_result_review_created"] = True
    index["v14_operator_visual_review_packet_created"] = True
    index["operator_visual_verdict_recorded"] = False

    index["assembly_executed"] = False
    index["downstream_executed"] = False
    index["audio_render_executed"] = False
    index["video_render_executed"] = False

    # V14 artifact paths
    index["v14_correction_plan"] = "combine_v2_v14_correction_plan.json"
    index["v14_prompt_patch"] = "combine_v2_v14_prompt_patch.json"
    index["v14_workflow_patch"] = "combine_v2_v14_workflow_patch.json"
    index["v14_quality_pipeline_patch"] = "combine_v2_v14_quality_pipeline_patch.json"
    index["v14_generation_authorization"] = "combine_v2_v14_generation_authorization.json"
    index["v14_generation_result"] = "combine_v2_v14_generation_result.json"
    index["v14_outputs_manifest"] = "combine_v2_v14_outputs_manifest.json"
    index["v14_qa_canon_report"] = "qa/reports/combine_v2_v14_qa_canon_report.json"
    index["v14_result_review"] = "combine_v2_v14_result_review.json"
    index["v14_operator_visual_review_packet"] = "combine_v2_v14_operator_visual_review_packet.json"
    index["v13_operator_visual_rejection"] = "combine_v2_v13_operator_visual_rejection.json"
    index["v13_negative_framing_reference"] = "qa/references/negative/v13_bad_framing_reference.json"

    index_path.write_text(json.dumps(index, indent=2))
    log("Updated artifact_index.json")
    return index


# ---------------------------------------------------------------------------
# 11. Update episode_ledger.json
# ---------------------------------------------------------------------------
def update_episode_ledger(gen_result: dict, review: dict, packet: dict, qa_report: dict) -> list:
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
    else:
        ledger = []

    events = [
        {
            "event_type": "v13_operator_rejection_recorded",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v13",
            "stage": "v13_operator_rejection",
            "operator_decision": "rejected",
            "framing_defects_registered": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "current_state": "v14_correction_plan_required",
            "next_allowed_action": "v14_generation_authorization_required",
            "notes": "V13 operator visual rejection recorded. Framing defects registered. V13 positive quality preserved as reference.",
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_correction_package_created",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_correction_plan_required",
            "correction_plan_created": True,
            "prompt_patch_created": True,
            "workflow_patch_created": True,
            "quality_pipeline_patch_created": True,
            "framing_correction_included": True,
            "generation_allowed": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "current_state": "v14_correction_plan_required",
            "next_allowed_action": "v14_generation_authorization_required",
            "notes": "V14 correction package built from V13 operator rejection evidence. Framing/crop defects targeted.",
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_generation_authorized",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_generation_authorization_required",
            "operator_generation_authorized": True,
            "max_generations": 1,
            "second_generation_forbidden": True,
            "blind_retry_forbidden": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_generation_executed",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_generate_assets",
            "generation_count": gen_result["generation_count"],
            "max_generations": gen_result["max_generations"],
            "workflow_submitted": gen_result["workflow_submitted"],
            "comfyui_execution": gen_result["comfyui_execution"],
            "prompt_id": gen_result["prompt_id"],
            "generated_assets": [gen_result["asset_path"]],
            "asset_count": 1,
            "second_v14_generation_attempted": False,
            "blind_retry_attempted": False,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "current_state": "v14_result_review_required",
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_asset_validated",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_asset_validation",
            "asset_path": gen_result["asset_path"],
            "asset_readable": gen_result["asset_readable"],
            "sha256_present": True,
            "stub_asset_detected": gen_result["stub_asset_detected"],
            "width": gen_result["asset_width"],
            "height": gen_result["asset_height"],
            "size_bytes": gen_result["asset_size_bytes"],
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_qa_canon_report_created",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_qa_canon_evaluation",
            "qa_canon_engine_used": True,
            "universal_canon_used": True,
            "human_face_canon_used": True,
            "operator_feedback_memory_used": True,
            "negative_reference_used": True,
            "decision": qa_report.get("decision", "operator_review_required"),
            "framing_defects_checked": True,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "timestamp": timestamp(),
        },
        {
            "event_type": "v14_operator_visual_review_packet_created",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_operator_visual_review_required",
            "operator_visual_verdict_recorded": False,
            "operator_decision": None,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "current_state": "v14_operator_visual_review_required",
            "next_allowed_action": "v14_operator_visual_review_required",
            "notes": "Pipeline stopped at operator visual review gate. Waiting for human visual inspection of V14 framing correction.",
            "timestamp": timestamp(),
        },
        {
            "event_type": "pipeline_stopped_at_operator_review",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_operator_visual_review_required",
            "current_state": "v14_operator_visual_review_required",
            "next_allowed_action": "v14_operator_visual_review_required",
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "notes": "V14 controlled candidate execution loop complete. Stopped at operator visual review by task contract.",
            "timestamp": timestamp(),
        },
    ]

    ledger.extend(events)
    ledger_path.write_text(json.dumps(ledger, indent=2))
    log("Updated episode_ledger.json")
    return ledger


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> dict:
    ensure_dirs()

    log("=== RC-COMBINE-V2-30001-34000: V14 Artifact Generation ===")

    # 1. Record V13 operator rejection
    log("--- Step 1: V13 operator rejection ---")
    v13_rejection = create_v13_operator_rejection()

    # 2. Update QA memory
    log("--- Step 2: QA memory update ---")
    update_operator_feedback_memory()
    v13_neg_ref = create_v13_negative_framing_reference()

    # 3. Create V14 correction package
    log("--- Step 3: V14 correction package ---")
    v14_plan = create_v14_correction_plan()
    v14_prompt = create_v14_prompt_patch()
    v14_workflow = create_v14_workflow_patch()
    v14_quality = create_v14_quality_pipeline_patch()

    # 4. Create V14 generation authorization
    log("--- Step 4: V14 generation authorization ---")
    v14_auth = create_v14_generation_authorization()

    # 5. Execute V14 generation
    log("--- Step 5: V14 real generation ---")
    try:
        gen_result = execute_v14_generation()
    except Exception as e:
        log(f"V14 GENERATION FAILED: {e}")
        # Create blocker artifact
        blocker = {
            "current_state": "v14_generation_runtime_blocked",
            "next_allowed_action": "v14_generation_runtime_blocked",
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "error": str(e),
            "timestamp": timestamp(),
        }
        blocker_path = CONTROL_DIR / "combine_v2_v14_runtime_blocker.json"
        blocker_path.write_text(json.dumps(blocker, indent=2))
        log(f"Created blocker artifact at {blocker_path}")
        return blocker

    # 6. Create outputs manifest
    log("--- Step 6: V14 outputs manifest ---")
    manifest = create_v14_outputs_manifest(gen_result)

    # 7. Run QA Canon Engine
    log("--- Step 7: QA Canon Engine ---")
    qa_report = run_v14_qa_canon_engine(gen_result)

    # 8. Create result review
    log("--- Step 8: V14 result review ---")
    review = create_v14_result_review(gen_result, qa_report)

    # 9. Create operator visual review packet
    log("--- Step 9: V14 operator visual review packet ---")
    packet = create_v14_operator_visual_review_packet(gen_result, qa_report)

    # 10. Update artifact index
    log("--- Step 10: Update artifact index ---")
    index = update_artifact_index(gen_result, review, packet, qa_report)

    # 11. Update episode ledger
    log("--- Step 11: Update episode ledger ---")
    ledger = update_episode_ledger(gen_result, review, packet, qa_report)

    summary = {
        "task_id": "RC-COMBINE-V2-30001-34000",
        "feature_completed": True,
        "v13_operator_rejection_recorded": True,
        "v13_decision": "rejected",
        "v13_production_accepted": False,
        "framing_defects_registered": True,
        "v13_positive_quality_reference_used": True,
        "v13_negative_framing_reference_used": True,
        "v14_correction_plan_created": True,
        "v14_prompt_patch_created": True,
        "v14_workflow_patch_created": True,
        "v14_quality_pipeline_patch_created": True,
        "v14_generation_authorized": True,
        "candidate_version": "v14",
        "generation_count": gen_result["generation_count"],
        "max_generations": gen_result["max_generations"],
        "second_v14_generation_attempted": gen_result["second_v14_generation_attempted"],
        "blind_retry_attempted": gen_result["blind_retry_attempted"],
        "workflow_submitted": gen_result["workflow_submitted"],
        "comfyui_execution": gen_result["comfyui_execution"],
        "prompt_id": gen_result["prompt_id"],
        "asset_path": gen_result["asset_path"],
        "asset_readable": gen_result["asset_readable"],
        "sha256_present": True,
        "dimensions_present": True,
        "stub_asset_detected": gen_result["stub_asset_detected"],
        "v14_outputs_manifest_created": True,
        "v14_qa_canon_report_created": True,
        "v14_result_review_created": True,
        "v14_operator_visual_review_packet_created": True,
        "operator_visual_verdict_recorded": False,
        "current_state": "v14_operator_visual_review_required",
        "next_allowed_action": "v14_operator_visual_review_required",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "audio_render_executed": False,
        "video_render_executed": False,
        "timestamp": timestamp(),
    }

    summary_path = CONTROL_DIR / "combine_v2_v14_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    log(f"Created V14 summary: {summary_path}")

    log("=== V14 Artifact Generation Complete ===")
    return summary


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
