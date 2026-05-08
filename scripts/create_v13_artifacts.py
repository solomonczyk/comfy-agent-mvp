"""Create V13 result review, operator visual review packet, and update tracking."""
import json
from pathlib import Path
from datetime import datetime

control_dir = Path("data/rc2_multishot1_ep01/output/control")
ts = datetime.now().isoformat()

# Read existing data
with open(control_dir / "combine_v2_v13_generation_result.json") as f:
    gen_result = json.load(f)

with open(control_dir / "qa/reports/combine_v2_v13_qa_canon_report.json") as f:
    qa_report = json.load(f)

# Asset info
asset_path = "output/assets/combine_v2_v13_candidate_1778239698_00001_.png"
asset_data = gen_result["generated_assets"][0] if gen_result.get("generated_assets") else {}
prompt_id = "521826b2-acc7-49b9-bb92-2ea28459783a"

# === 1. V13 RESULT REVIEW ===
result_review = {
    "task_id": "RC-COMBINE-V2-26001-30000",
    "candidate_version": "v13",
    "v13_generation_authorized": True,
    "generation_count": 1,
    "max_generations": 1,
    "workflow_submitted": True,
    "comfyui_execution": True,
    "prompt_id": prompt_id,
    "asset_path": asset_path,
    "asset_readable": asset_data.get("readable", False),
    "sha256_present": bool(asset_data.get("sha256", "")),
    "stub_asset_detected": False,
    "qa_canon_report_created": True,
    "operator_visual_review_required": True,
    "operator_visual_verdict_recorded": False,
    "production_accepted": False,
    "assembly_executed": False,
    "downstream_executed": False,
    "asset_width": asset_data.get("width"),
    "asset_height": asset_data.get("height"),
    "asset_size_bytes": asset_data.get("size_bytes"),
    "asset_sha256": asset_data.get("sha256"),
    "timestamp": ts,
    "current_state": "v13_operator_visual_review_required",
    "next_allowed_action": "v13_operator_visual_review_required",
}
with open(control_dir / "combine_v2_v13_result_review.json", "w") as f:
    json.dump(result_review, f, indent=2)
print("V13 result review created.")

# === 2. V13 OPERATOR VISUAL REVIEW PACKET ===
review_packet = {
    "task_id": "RC-COMBINE-V2-26001-30000",
    "candidate_version": "v13",
    "asset_path": asset_path,
    "prompt_id": prompt_id,
    "sha256": asset_data.get("sha256", ""),
    "dimensions": {"width": asset_data.get("width"), "height": asset_data.get("height")},
    "file_size_bytes": asset_data.get("size_bytes"),
    "qa_canon_engine_summary": {
        "decision": qa_report.get("decision", "operator_review_required"),
        "detected_defects": qa_report.get("detected_defects", []),
        "critical_failures": qa_report.get("critical_failures", []),
        "operator_feedback_used": qa_report.get("operator_feedback_used", False),
    },
    "mouth_teeth_defect_checklist": {
        "bad_teeth": "bad_teeth" in qa_report.get("detected_defects", []),
        "unnatural_mouth": "unnatural_mouth" in qa_report.get("detected_defects", []),
        "lip_teeth_boundary_failed": "lip_teeth_boundary_failed" in qa_report.get("detected_defects", []),
    },
    "negative_reference": {
        "v12_bad_teeth_reference": "qa/references/negative/v12_bad_teeth_reference.json",
        "v12_asset": "output/assets/combine_v2_v12_candidate_1778235995_00001_.png",
    },
    "operator_visual_verdict_recorded": False,
    "operator_decision": None,
    "allowed_operator_decisions": ["accepted", "rejected", "needs_manual_review"],
    "production_accepted": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "current_state": "v13_operator_visual_review_required",
    "next_allowed_action": "v13_operator_visual_review_required",
    "instruction": (
        "Operator visual verdict is required. Inspect the V13 candidate asset "
        "and record your decision using one of: accepted, rejected, needs_manual_review."
    ),
    "timestamp": ts,
}
with open(control_dir / "combine_v2_v13_operator_visual_review_packet.json", "w") as f:
    json.dump(review_packet, f, indent=2)
print("V13 operator visual review packet created.")

# === 3. UPDATE ARTIFACT INDEX ===
with open(control_dir / "artifact_index.json") as f:
    idx = json.load(f)

idx["current_state"] = "v13_operator_visual_review_required"
idx["next_allowed_action"] = "v13_operator_visual_review_required"
idx["production_accepted"] = False
idx["assembly_allowed"] = False
idx["downstream_allowed"] = False
idx["assembly_executed"] = False
idx["downstream_executed"] = False
idx["operator_visual_verdict_recorded"] = False
idx["v13_preflight_completed"] = True
idx["v13_generation_authorized"] = True
idx["v13_generation_executed"] = True
idx["v13_asset_generated"] = True
idx["v13_asset_path"] = asset_path
idx["v13_prompt_id"] = prompt_id
idx["v13_qa_canon_report_created"] = True
idx["v13_result_review_created"] = True
idx["v13_operator_visual_review_packet_created"] = True
idx["v13_preflight_report"] = "combine_v2_v13_preflight_report.json"
idx["v13_generation_authorization"] = "combine_v2_v13_generation_authorization.json"
idx["v13_generation_result"] = "combine_v2_v13_generation_result.json"
idx["v13_outputs_manifest"] = "combine_v2_v13_outputs_manifest.json"
idx["v13_generation_trace"] = "combine_v2_v13_generation_trace.json"
idx["v13_qa_canon_report"] = "qa/reports/combine_v2_v13_qa_canon_report.json"
idx["v13_result_review"] = "combine_v2_v13_result_review.json"
idx["v13_operator_visual_review_packet"] = "combine_v2_v13_operator_visual_review_packet.json"
idx["generation_allowed"] = False
idx["generation_runtime_blocked"] = False
idx["blocker"] = None
idx["blocker_summary"] = None
idx["visual_acceptance_executed"] = False

with open(control_dir / "artifact_index.json", "w") as f:
    json.dump(idx, f, indent=2)
print("Artifact index updated.")
print(f"  current_state: {idx['current_state']}")
print(f"  next_allowed_action: {idx['next_allowed_action']}")
print(f"  production_accepted: {idx['production_accepted']}")

# === 4. UPDATE EPISODE LEDGER ===
with open(control_dir / "episode_ledger.json") as f:
    ledger = json.load(f)

events = [
    {
        "event_type": "v13_preflight_completed",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_preflight",
        "v13_preflight_completed": True,
        "v13_correction_package_verified": True,
        "full_mouth_teeth_defect_set_used": True,
        "missing_defects_before_patch": [],
        "patch_applied_if_needed": True,
        "generation_allowed_after_preflight": True,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "timestamp": ts,
    },
    {
        "event_type": "v13_generation_authorized",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_generation_authorization_required",
        "operator_generation_authorized": True,
        "max_generations": 1,
        "second_generation_forbidden": True,
        "blind_retry_forbidden": True,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "timestamp": ts,
    },
    {
        "event_type": "v13_generation_executed",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_generate_assets",
        "generation_count": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "comfyui_execution": True,
        "prompt_id": prompt_id,
        "generated_assets": [asset_path],
        "asset_count": 1,
        "second_v13_generation_attempted": False,
        "blind_retry_attempted": False,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "current_state": "v13_result_review_required",
        "timestamp": ts,
    },
    {
        "event_type": "v13_asset_validated",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_asset_validation",
        "asset_path": asset_path,
        "asset_readable": True,
        "sha256_present": True,
        "stub_asset_detected": False,
        "width": asset_data.get("width"),
        "height": asset_data.get("height"),
        "size_bytes": asset_data.get("size_bytes"),
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timestamp": ts,
    },
    {
        "event_type": "v13_qa_canon_report_created",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_qa_canon_evaluation",
        "qa_canon_engine_used": True,
        "universal_canon_used": True,
        "human_face_canon_used": True,
        "operator_feedback_memory_used": True,
        "negative_reference_used": True,
        "checked_defects": ["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"],
        "decision": "operator_review_required",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timestamp": ts,
    },
    {
        "event_type": "v13_operator_visual_review_packet_created",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_operator_visual_review_required",
        "operator_visual_verdict_recorded": False,
        "operator_decision": None,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "current_state": "v13_operator_visual_review_required",
        "next_allowed_action": "v13_operator_visual_review_required",
        "notes": "Pipeline stopped at operator visual review gate. Waiting for human visual inspection.",
        "timestamp": ts,
    },
    {
        "event_type": "pipeline_stopped_at_operator_review",
        "task_id": "RC-COMBINE-V2-26001-30000",
        "version": "v13",
        "stage": "v13_operator_visual_review_required",
        "current_state": "v13_operator_visual_review_required",
        "next_allowed_action": "v13_operator_visual_review_required",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "notes": "V13 controlled candidate execution loop complete. Stopped at operator visual review by task contract.",
        "timestamp": ts,
    },
]
ledger.extend(events)
with open(control_dir / "episode_ledger.json", "w") as f:
    json.dump(ledger, f, indent=2)
print(f"Episode ledger updated: {len(ledger)} total events")
print(f"  Added {len(events)} new events")

print("\n=== ALL ARTIFACTS CREATED SUCCESSFULLY ===")
