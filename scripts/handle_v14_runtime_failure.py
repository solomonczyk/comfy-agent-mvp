"""Handle V14 runtime failure — update state, artifacts, and ledger.

ComfyUI generation failed with OOM. Per task contract: no retry, block and stop.
This supersedes all prior V14 ledger updates — replaces the V14 event section
with the complete set of events from V13 rejection through runtime block.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

CONTROL_DIR = Path("data/rc2_multishot1_ep01/output/control")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_artifact_index() -> dict:
    path = CONTROL_DIR / "artifact_index.json"
    if path.exists():
        index = json.loads(path.read_text())
    else:
        index = {}

    # State
    index["current_state"] = "v14_generation_runtime_blocked"
    index["next_allowed_action"] = "v14_generation_runtime_blocked"
    index["production_accepted"] = False
    index["assembly_executed"] = False
    index["downstream_executed"] = False
    index["generation_runtime_blocked"] = True
    index["blocker"] = "ComfyUI OOM: DefaultCPUAllocator out of memory"
    index["blocker_summary"] = "V14 ComfyUI generation failed with CPU memory allocation error. No retry per task contract."
    index["manual_action_required"] = True

    # V13 rejection
    index["v13_operator_rejection_recorded"] = True
    index["v13_decision"] = "rejected"
    index["v13_production_accepted"] = False
    index["framing_defects_registered"] = True
    index["v13_positive_quality_reference_used"] = True
    index["v13_negative_framing_reference_used"] = True

    # V14 correction package
    index["v14_correction_plan_created"] = True
    index["v14_prompt_patch_created"] = True
    index["v14_workflow_patch_created"] = True
    index["v14_quality_pipeline_patch_created"] = True

    # V14 generation
    index["v14_generation_authorized"] = True
    index["candidate_version"] = "v14"
    index["v14_generation_attempted"] = True
    index["v14_generation_succeeded"] = False
    index["comfyui_execution"] = False
    index["second_v14_generation_attempted"] = False
    index["blind_retry_attempted"] = False
    index["v14_generation_runtime_blocked"] = True

    # QA Canon
    index["v14_qa_canon_report_created"] = False  # No asset to evaluate
    index["v14_result_review_created"] = False    # No asset to review
    index["v14_operator_visual_review_packet_created"] = False  # No packet without asset

    # Guards
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
    index["v14_runtime_blocker"] = "combine_v2_v14_runtime_blocker.json"
    index["v13_operator_visual_rejection"] = "combine_v2_v13_operator_visual_rejection.json"
    index["v13_negative_framing_reference"] = "qa/references/negative/v13_bad_framing_reference.json"

    path.write_text(json.dumps(index, indent=2))
    print(f"[V14] Updated artifact_index.json to runtime_blocked state")
    return index


def update_episode_ledger() -> list:
    path = CONTROL_DIR / "episode_ledger.json"
    if path.exists():
        ledger = json.loads(path.read_text())
    else:
        ledger = []

    events = [
        {
            "event_type": "v13_operator_rejection_recorded",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v13",
            "stage": "v13_operator_rejection",
            "operator_decision": "rejected",
            "defects": [
                "head_not_fully_in_frame",
                "top_of_head_cropped",
                "over_tight_face_crop",
                "portrait_framing_failed",
            ],
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
            "event_type": "v14_generation_runtime_blocked",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_generate_assets",
            "generation_attempted": True,
            "generation_success": False,
            "failure_code": "COMFYUI_OOM_CPU_ALLOC",
            "failure_detail": "DefaultCPUAllocator: not enough memory to allocate 12582912 bytes",
            "blind_retry_attempted": False,
            "second_generation_attempted": False,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "current_state": "v14_generation_runtime_blocked",
            "next_allowed_action": "v14_generation_runtime_blocked",
            "notes": "V14 ComfyUI generation failed with CPU OOM. No retry per task contract. Pipeline blocked at runtime.",
            "timestamp": timestamp(),
        },
        {
            "event_type": "pipeline_stopped_at_runtime_blocker",
            "task_id": "RC-COMBINE-V2-30001-34000",
            "version": "v14",
            "stage": "v14_generation_runtime_blocked",
            "current_state": "v14_generation_runtime_blocked",
            "next_allowed_action": "v14_generation_runtime_blocked",
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "notes": "V14 pipeline blocked at runtime. ComfyUI OOM. Manual intervention required to resolve memory and retry.",
            "timestamp": timestamp(),
        },
    ]

    # Remove any existing V14 events to avoid duplicates
    ledger = [e for e in ledger if e.get("version") != "v14" and "v14" not in e.get("event_type", "")]
    # Also remove old v13 rejection event if present (we're re-recording it)
    ledger = [e for e in ledger if e.get("event_type") != "v13_operator_rejection_recorded"]

    ledger.extend(events)
    path.write_text(json.dumps(ledger, indent=2))
    print(f"[V14] Updated episode_ledger.json with {len(events)} V14 events")
    return ledger


def main():
    print("=== V14 Runtime Failure Handler (Complete) ===")
    update_artifact_index()
    update_episode_ledger()
    print("=== Complete ===")
    print(json.dumps({
        "current_state": "v14_generation_runtime_blocked",
        "next_allowed_action": "v14_generation_runtime_blocked",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "generation_runtime_blocked": True,
    }, indent=2))


if __name__ == "__main__":
    main()
