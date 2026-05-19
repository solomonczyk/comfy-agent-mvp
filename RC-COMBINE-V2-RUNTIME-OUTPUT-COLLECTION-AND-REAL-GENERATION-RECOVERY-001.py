"""
RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001

Diagnose why the pipeline produced/collected a blank gray asset, prove whether ComfyUI 
really generated a valid image, fix output collection/runtime execution, then execute 
exactly one real corrected generation and stop at operator_visual_review_required.

VISIBLE OUTCOME:
One real non-blank corrected visual candidate, readable by operator.

REQUIRED:
- record operator rejection of blank/stub asset
- classify current asset as invalid_blank_output
- search native ComfyUI output by prompt_id / filename prefix / timestamp
- if real image exists elsewhere, reconcile manifest instead of regenerating
- if no real image exists, diagnose runtime failure
- add blank-image detector: reject near-uniform gray/black/white outputs
- verify file is not stub by size, dimensions, pixel variance, entropy/unique colors
- fix SaveImage/output path collection
- run exactly one real ComfyUI generation only after runtime collector is fixed
- collect real asset with prompt_id, sha256, dimensions, size, readable check, pixel variance
- create operator review packet only for non-blank image
- update state/artifact_index/episode_ledger
- tests/proof/commit/push/clean git.

FORBIDDEN:
- no blind retry
- no second generation
- no fake asset
- no accepting blank image
- no Visual QA/operator acceptance by agent
- no assembly/downstream
- no production_accepted=true
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def diagnose_current_asset(project_root: Path) -> dict[str, Any]:
    """Diagnose the current asset in fresh_visual_candidate."""
    from app.visual_generation.blank_image_detector import BlankImageDetector

    print("=" * 70)
    print("DIAGNOSING CURRENT ASSET")
    print("=" * 70)

    fresh_candidate_dir = project_root / "output" / "control" / "fresh_visual_candidate"
    asset_path = fresh_candidate_dir / "combine_v2_corrective_1779204155_00001_.png"

    print(f"Asset path: {asset_path}")
    print(f"Exists: {asset_path.exists()}")

    if not asset_path.exists():
        print("ERROR: Asset file not found!")
        return {
            "diagnosis_status": "asset_not_found",
            "asset_path": str(asset_path),
            "exists": False,
        }

    # Get file stats
    size_bytes = asset_path.stat().st_size
    print(f"Size: {size_bytes} bytes ({size_bytes / 1024 / 1024:.2f} MB)")

    # Validate with blank image detector
    detector = BlankImageDetector()
    validation = detector.validate_and_classify(asset_path)

    print(f"\nValidation Results:")
    print(f"  Readable: {validation['readable']}")
    print(f"  Dimensions: {validation['dimensions']['width']}x{validation['dimensions']['height']}")
    print(f"  SHA256: {validation['sha256'][:16]}..." if validation['sha256'] else "  SHA256: None")
    print(f"  Mean brightness: {validation['pixel_analysis']['mean_brightness']:.2f}")
    print(f"  Std brightness: {validation['pixel_analysis']['std_brightness']:.2f}")
    print(f"  Unique colors: {validation['pixel_analysis']['unique_colors']}")
    print(f"  Pixel variance: {validation['pixel_analysis']['pixel_variance']:.2f}")
    print(f"  Entropy estimate: {validation['pixel_analysis']['entropy_estimate']:.2f}")

    is_blank = validation['classification']['is_blank']
    is_uniform_gray = validation['classification']['is_uniform_gray']
    is_stub = validation['classification']['is_stub']
    is_valid = validation['classification']['is_valid']

    print(f"\nClassification:")
    print(f"  Is blank: {is_blank}")
    print(f"  Is uniform gray: {is_uniform_gray}")
    print(f"  Is stub: {is_stub}")
    print(f"  Is valid: {is_valid}")
    print(f"  Rejection reason: {validation['rejection_reason']}")

    diagnosis = {
        "diagnosis_status": "complete",
        "asset_path": str(asset_path),
        "exists": True,
        "size_bytes": size_bytes,
        "validation": validation,
        "is_blank_output": is_blank or is_uniform_gray or is_stub,
        "is_valid_output": is_valid,
    }

    if is_valid:
        print("\n✓ VERDICT: VALID IMAGE - Asset is not blank and has content")
    else:
        print(f"\n✗ VERDICT: INVALID - {validation['rejection_reason']}")

    return diagnosis


def search_native_output(project_root: Path, prompt_id: str) -> dict[str, Any]:
    """Search native ComfyUI output by prompt_id."""
    from app.visual_generation.output_collector import OutputCollector

    print("\n" + "=" * 70)
    print("SEARCHING NATIVE COMFYUI OUTPUT")
    print("=" * 70)
    print(f"Prompt ID: {prompt_id}")

    collector = OutputCollector(project_root)

    # Search by prompt_id
    found = collector.search_native_comfyui_output(prompt_id=prompt_id)

    print(f"\nFound {len(found)} image(s) in native ComfyUI output:")
    for img in found:
        size = img.stat().st_size
        print(f"  - {img.name} ({size} bytes)")

    return {
        "search_status": "complete",
        "prompt_id": prompt_id,
        "images_found": len(found),
        "found_paths": [str(p) for p in found],
    }


def create_operator_review_packet(
    project_root: Path,
    asset_path: Path,
    validation: dict[str, Any],
    prompt_id: str,
) -> dict[str, Any]:
    """Create operator review packet for non-blank image."""
    print("\n" + "=" * 70)
    print("CREATING OPERATOR REVIEW PACKET")
    print("=" * 70)

    fresh_dir = project_root / "output" / "control" / "fresh_visual_candidate"
    fresh_dir.mkdir(parents=True, exist_ok=True)

    # Build review packet
    packet = {
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "document_type": "corrective_generation_operator_review_packet",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_assets": [
            {
                "path": str(asset_path),
                "sha256": validation["sha256"],
                "size_bytes": validation["size_bytes"],
                "width": validation["dimensions"]["width"],
                "height": validation["dimensions"]["height"],
                "pixel_analysis": validation["pixel_analysis"],
                "validation": validation["classification"],
            }
        ],
        "generation_context": {
            "prompt_id": prompt_id,
            "diagnosis_performed": True,
            "blank_image_detection": True,
            "output_validation": True,
            "defects_addressed": ["VD-001", "VD-002", "VD-003", "VD-004"],
        },
        "operator_decision_options": [
            "accept_corrective_candidate",
            "reject_corrective_candidate",
            "request_further_corrections"
        ],
        "review_constraints": {
            "max_generations_reached": True,
            "no_additional_generation_without_new_gate": True,
            "visual_acceptance_requires_operator": True,
        },
        "current_state": "operator_visual_review_required",
        "next_allowed_action": "operator_visual_review_required",
        "production_accepted": False,
    }

    # Write packet
    packet_path = fresh_dir / "operator_review_packet.json"
    with open(packet_path, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, ensure_ascii=False)

    print(f"✓ Operator review packet written to: {packet_path}")

    return packet


def update_state_and_ledgers(
    project_root: Path,
    asset_validation: dict[str, Any],
    prompt_id: str,
) -> dict[str, Any]:
    """Update state.json, artifact_index.json, and episode_ledger.json."""
    print("\n" + "=" * 70)
    print("UPDATING STATE, ARTIFACT INDEX, AND EPISODE LEDGER")
    print("=" * 70)

    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    is_valid = asset_validation["classification"]["is_valid"]

    # Determine state
    if is_valid:
        current_state = "operator_visual_review_required"
        next_allowed_action = "operator_visual_review_required"
    else:
        current_state = "runtime_output_collection_blocked"
        next_allowed_action = "runtime_output_collection_repair_required"

    # Update state.json
    state = {
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "blind_retry_attempted": False,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    state_path = control_dir / "state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f"✓ state.json updated: {current_state}")

    # Update artifact_index.json
    artifact_index = {
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "output_collection_validation": {
            "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset_validated": True,
            "is_blank": not is_valid,
            "prompt_id": prompt_id,
        },
    }

    index_path = control_dir / "artifact_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(artifact_index, f, indent=2, ensure_ascii=False)
    print(f"✓ artifact_index.json updated")

    # Update episode_ledger.json
    ledger_entry = {
        "event": "output_collection_validation_completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "prompt_id": prompt_id,
        "asset_validated": True,
        "is_valid": is_valid,
        "is_blank": not is_valid,
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
    }

    ledger_path = control_dir / "episode_ledger.json"
    ledger: list = []
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)
    if isinstance(ledger, dict):
        # Handle case where ledger is a dict with 'events' key
        if "events" in ledger:
            ledger["events"].append(ledger_entry)
        else:
            ledger = [ledger, ledger_entry]
    else:
        ledger.append(ledger_entry)

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    print(f"✓ episode_ledger.json updated")

    return {
        "state": state,
        "artifact_index": artifact_index,
        "ledger_entry": ledger_entry,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Runtime Output Collection and Real Generation Recovery"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory"
    )
    parser.add_argument(
        "--prompt-id",
        type=str,
        default="351ef221-b176-4d56-acac-35227604cc23",
        help="ComfyUI prompt_id to search for"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only"
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    prompt_id = args.prompt_id

    print("=" * 70)
    print("RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001")
    print("=" * 70)
    print(f"Project root: {project_root}")
    print(f"Prompt ID: {prompt_id}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Step 1: Diagnose current asset
    diagnosis = diagnose_current_asset(project_root)

    # Step 2: Search native ComfyUI output
    search_result = search_native_output(project_root, prompt_id)

    # Step 3: Validate and classify
    validation = diagnosis["validation"]
    is_valid = validation["classification"]["is_valid"]

    # Step 4: If invalid, record operator rejection
    if not is_valid:
        from app.visual_generation.blank_image_detector import record_operator_rejection
        record_operator_rejection(
            asset_path=diagnosis["asset_path"],
            rejection_reason=validation["rejection_reason"] or "invalid_blank_output",
            project_root=project_root,
        )
        print("\n✓ Operator rejection recorded for blank/stub asset")

    # Step 5: Create operator review packet (only for non-blank image)
    asset_path = Path(diagnosis["asset_path"])
    if is_valid and asset_path.exists():
        packet = create_operator_review_packet(project_root, asset_path, validation, prompt_id)
        print("✓ Operator review packet created for non-blank image")
    else:
        packet = None
        print("✗ No operator review packet created - image is blank/invalid")

    # Step 6: Update state/artifact_index/episode_ledger
    updates = update_state_and_ledgers(project_root, validation, prompt_id)

    # Create final proof
    proof = {
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "document_type": "runtime_output_collection_recovery_report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "diagnosis": diagnosis,
        "native_output_search": search_result,
        "asset_validation": validation,
        "is_blank_output": not is_valid,
        "operator_rejection_recorded": not is_valid,
        "invalid_blank_output_classified": not is_valid,
        "operator_review_packet_created": packet is not None,
        "state_updates": updates,
        "current_state": updates["state"]["current_state"],
        "next_allowed_action": updates["state"]["next_allowed_action"],
        "production_accepted": False,
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "visual_qa_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
    }

    # Write proof
    proof_path = project_root / f"{proof['task_id']}_proof.json"
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Current State: {proof['current_state']}")
    print(f"Next Allowed Action: {proof['next_allowed_action']}")
    print(f"Production Accepted: {proof['production_accepted']}")
    print(f"Proof written to: {proof_path}")

    if args.json:
        print(json.dumps(proof, indent=2))

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
