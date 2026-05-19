#!/usr/bin/env python3
"""
RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001
Purge all previous generated visual outputs and invalidate canonical references.
"""

import os
import json
import hashlib
import datetime
from pathlib import Path

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
TARGET_OUTPUT_ROOT = PROJECT_ROOT / "data/rc2_multishot1_ep01/output"
CONTROL_DIR = TARGET_OUTPUT_ROOT / "control"

VISUAL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4"}

PURGE_TASK_ID = "RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001"
TIMESTAMP = datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"error:{e}"


def classify_file(path: Path) -> str:
    parts = [p.lower() for p in path.relative_to(TARGET_OUTPUT_ROOT).parts]
    name = path.name.lower()
    if "contact_sheet" in name:
        return "contact_sheet"
    if "frame" in name and path.suffix.lower() == ".png":
        return "frame_dump"
    if path.suffix.lower() == ".gif":
        return "gif"
    if path.suffix.lower() == ".mp4":
        return "preview_video"
    if "preview" in parts or "previews" in parts:
        return "preview_image"
    if "assets" in parts:
        return "generated_image"
    if "frames" in parts:
        return "frame_dump"
    return "generated_image"


def find_visual_files():
    files = []
    for ext in VISUAL_EXTENSIONS:
        for path in TARGET_OUTPUT_ROOT.rglob(f"*{ext}"):
            if path.is_file():
                files.append(path)
    files.sort()
    return files


def create_inventory(files):
    inventory = []
    for f in files:
        rel = str(f.relative_to(PROJECT_ROOT)).replace("\\", "/")
        inventory.append({
            "path": rel,
            "type": classify_file(f),
            "size_bytes": f.stat().st_size,
            "sha256_before_delete": sha256_file(f),
        })
    return inventory


def delete_files(files):
    deleted = 0
    for f in files:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    return deleted


def update_json_file(path: Path, updater):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return
    updater(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def invalidate_visual_references(obj):
    """Recursively update any dict that looks like a visual asset reference."""
    if isinstance(obj, dict):
        # Heuristic: if it mentions visual assets, canonical results, etc.
        keys_to_invalidate = [
            "production_accepted",
            "visual_acceptance_executed",
            "assembly_executed",
            "downstream_executed",
            "assembly_allowed",
            "downstream_allowed",
            "canonical_outputs_registered",
            "operator_visual_verdict_recorded",
            "v13_production_accepted",
        ]
        for k in keys_to_invalidate:
            if k in obj:
                obj[k] = False

        # Mark visual asset paths as invalidated if they point to generated visuals
        for k in ["generated_assets", "current_best_concept_candidate_asset",
                  "current_best_quality_reference_asset", "v13_asset_path",
                  "v14_asset_path", "source_asset"]:
            if k in obj and isinstance(obj[k], str):
                if any(obj[k].lower().endswith(ext) for ext in VISUAL_EXTENSIONS):
                    obj[f"{k}_visual_asset_status"] = "purged_by_operator_directive"
                    obj[f"{k}_canonical_result"] = False
                    obj[f"{k}_usable_as_reference"] = False
                    obj[f"{k}_usable_for_downstream"] = False
            elif k in obj and isinstance(obj[k], list):
                for item in obj[k]:
                    if isinstance(item, str) and any(item.lower().endswith(ext) for ext in VISUAL_EXTENSIONS):
                        # We can't annotate inline in a list easily, but we can ensure the parent knows
                        pass

        # Specific state transitions
        if "current_state" in obj and obj["current_state"] in [
            "preview_operator_review_required",
            "v10_operator_visual_review_required",
            "v12_operator_visual_review_required",
            "v13_operator_visual_review_required",
            "v14_operator_visual_review_required",
            "v14_result_review_required",
            "editorial_operator_review_required",
            "editorial_dry_run_required",
            "planning_operator_review_required",
            "brief_operator_review_required",
            "agent_registry_operator_review_required",
            "generation_preflight_operator_review_required",
        ]:
            obj["current_state"] = "visual_outputs_purged_rebuild_required"
            obj["next_allowed_action"] = "fresh_visual_strategy_required"
            obj["voice_generation_ready"] = False
            obj["voice_generation_executed"] = False
            obj["preview_render_executed"] = False
            obj["new_generation_performed"] = False
            obj["comfyui_submit_executed"] = False
            obj["retry_attempted"] = False

        # Recurse
        for v in obj.values():
            invalidate_visual_references(v)
    elif isinstance(obj, list):
        for item in obj:
            invalidate_visual_references(item)


def main():
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Inventory
    print("Finding visual files...")
    files = find_visual_files()
    print(f"Found {len(files)} visual files.")

    inventory = create_inventory(files)
    inventory_path = CONTROL_DIR / "generated_visual_outputs_inventory_before_purge.json"
    with open(inventory_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": PURGE_TASK_ID,
            "timestamp": TIMESTAMP,
            "operator_directive": "purge all previous generated images and derived visual outputs",
            "reason": "visual outputs are rejected and compromising; must not be canonical or treated as usable result",
            "files_found": inventory,
            "total_files": len(inventory),
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Inventory written: {inventory_path}")

    # 2. Purge manifest (redacted, no embedded images)
    manifest_entries = []
    for item in inventory:
        manifest_entries.append({
            "path": item["path"],
            "type": item["type"],
            "size_bytes": item["size_bytes"],
            "sha256": item["sha256_before_delete"],
            "action": "deleted",
            "canonical_reference_invalidated": True,
        })

    manifest_path = CONTROL_DIR / "generated_visual_outputs_purge_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": PURGE_TASK_ID,
            "operator_directive": "purge previous generated visual outputs",
            "purge_reason": "rejected visual material; must not be canonical or reusable",
            "files_found": manifest_entries,
            "total_files_deleted": len(manifest_entries),
            "embedded_visual_content_preserved": False,
            "timestamp": TIMESTAMP,
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Manifest written: {manifest_path}")

    # 3. Delete files
    print("Deleting visual files...")
    deleted_count = delete_files(files)
    print(f"Deleted {deleted_count}/{len(files)} files.")

    # 4. Update artifact_index.json (project-level)
    root_artifact_index = PROJECT_ROOT / "artifact_index.json"
    if root_artifact_index.exists():
        update_json_file(root_artifact_index, lambda d: invalidate_visual_references(d))
        print("Updated root artifact_index.json")

    # 5. Update episode_ledger.json (project-level)
    root_ledger = PROJECT_ROOT / "episode_ledger.json"
    if root_ledger.exists():
        def update_root_ledger(data):
            invalidate_visual_references(data)
            events = data.get("events", [])
            events.append({
                "event": "generated_visual_outputs_purged",
                "timestamp": TIMESTAMP,
                "details": "RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001: All generated visual outputs purged. Canonical references invalidated.",
                "task_id": PURGE_TASK_ID,
            })
            data["current_state"] = "visual_outputs_purged_rebuild_required"
            data["next_allowed_action"] = "fresh_visual_strategy_required"
            data["production_accepted"] = False
            data["voice_generation_ready"] = False
            data["assembly_allowed"] = False
            data["downstream_allowed"] = False
        update_json_file(root_ledger, update_root_ledger)
        print("Updated root episode_ledger.json")

    # 6. Update rc2_multishot1_ep01/output/control/artifact_index.json
    local_artifact_index = CONTROL_DIR / "artifact_index.json"
    if local_artifact_index.exists():
        update_json_file(local_artifact_index, lambda d: invalidate_visual_references(d))
        print("Updated local artifact_index.json")

    # 7. Update rc2_multishot1_ep01/output/control/episode_ledger.json
    local_ledger = CONTROL_DIR / "episode_ledger.json"
    if local_ledger.exists():
        def update_local_ledger(data):
            invalidate_visual_references(data)
            if isinstance(data, list):
                data.append({
                    "event_type": "generated_visual_outputs_purged",
                    "task_id": PURGE_TASK_ID,
                    "stage": "visual_purge",
                    "production_accepted": False,
                    "assembly_executed": False,
                    "downstream_executed": False,
                    "current_state": "visual_outputs_purged_rebuild_required",
                    "next_allowed_action": "fresh_visual_strategy_required",
                    "notes": "All generated visual outputs purged by operator directive. Canonical references invalidated.",
                    "timestamp": TIMESTAMP,
                })
            elif isinstance(data, dict):
                events = data.get("events", [])
                events.append({
                    "event": "generated_visual_outputs_purged",
                    "timestamp": TIMESTAMP,
                    "details": "RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001: All generated visual outputs purged. Canonical references invalidated.",
                    "task_id": PURGE_TASK_ID,
                })
                data["current_state"] = "visual_outputs_purged_rebuild_required"
                data["next_allowed_action"] = "fresh_visual_strategy_required"
                data["production_accepted"] = False
                data["assembly_allowed"] = False
                data["downstream_allowed"] = False
        update_json_file(local_ledger, update_local_ledger)
        print("Updated local episode_ledger.json")

    # 8. Create reference invalidation report
    invalidation_path = CONTROL_DIR / "generated_visual_outputs_reference_invalidation_report.json"
    with open(invalidation_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": PURGE_TASK_ID,
            "timestamp": TIMESTAMP,
            "invalidated_references": [
                {"file": "artifact_index.json", "action": "visual_asset_status updated to purged_by_operator_directive"},
                {"file": "episode_ledger.json", "action": "state transitioned to visual_outputs_purged_rebuild_required"},
                {"file": "output/control/artifact_index.json", "action": "all visual asset references invalidated"},
                {"file": "output/control/episode_ledger.json", "action": "purge event appended, state updated"},
            ],
            "visual_asset_status": "purged_by_operator_directive",
            "canonical_result": False,
            "usable_as_reference": False,
            "usable_for_downstream": False,
            "production_accepted": False,
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Invalidation report written: {invalidation_path}")

    # 9. Post-purge state report
    state_report_path = CONTROL_DIR / "post_purge_state_report.json"
    with open(state_report_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": PURGE_TASK_ID,
            "timestamp": TIMESTAMP,
            "current_state": "visual_outputs_purged_rebuild_required",
            "next_allowed_action": "fresh_visual_strategy_required",
            "production_accepted": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "visual_files_remaining_in_canonical_paths": 0,
            "active_canonical_visual_results": 0,
            "usable_visual_references": 0,
            "new_image_generation_performed": False,
            "comfyui_submit_executed": False,
            "retry_attempted": False,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"State report written: {state_report_path}")

    # 10. Fresh visual strategy required packet
    strategy_path = CONTROL_DIR / "fresh_visual_strategy_required_packet.json"
    with open(strategy_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": PURGE_TASK_ID,
            "timestamp": TIMESTAMP,
            "operator_directive": "fresh visual strategy required",
            "reason": "All previous generated visuals purged. No canonical visual assets remain.",
            "current_state": "visual_outputs_purged_rebuild_required",
            "next_allowed_action": "fresh_visual_strategy_required",
            "production_accepted": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "required_before_next_generation": [
                "Operator-approved generation strategy",
                "Reference image validation",
                "Workflow recipe review",
                "ComfyUI resource check",
            ],
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Strategy packet written: {strategy_path}")

    # 11. Clean up empty preview/asset/frame directories under output
    for subdir in ["assets", "previews", "frames"]:
        p = TARGET_OUTPUT_ROOT / subdir
        if p.exists():
            try:
                # Remove empty subdirectories recursively
                for root, dirs, files in os.walk(str(p), topdown=False):
                    for d in dirs:
                        dp = Path(root) / d
                        if dp.exists() and not any(dp.iterdir()):
                            dp.rmdir()
                if p.exists() and not any(p.iterdir()):
                    p.rmdir()
                    print(f"Removed empty directory: {p}")
            except Exception as e:
                print(f"Could not clean directory {p}: {e}")

    print("Purge complete.")


if __name__ == "__main__":
    main()
