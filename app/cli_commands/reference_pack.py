"""CLI commands for reference pack intake and canonicalization.

Task: RC-COMBINE-V2-REFERENCE-PACK-INTAKE-CANONICALIZATION-001
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.reference_pack.canonicalizer import ReferenceCanonicalizer
from app.reference_pack.intake import ReferencePackIntake
from app.reference_pack.validator import ReferencePackValidator


def init_reference_pack(args: argparse.Namespace) -> int:
    """Initialize a new project-agnostic reference pack.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    reference_root = Path(args.reference_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    # Create directory structure
    reference_root.mkdir(parents=True, exist_ok=True)

    # Create default reference pack
    pack_id = args.pack_id or "default_reference_pack"
    pack = ReferencePackIntake.create_default_pack(pack_id)

    # Save pack
    pack_path = reference_root / "reference_pack_manifest.json"
    ReferencePackIntake.save_pack_to_file(pack, pack_path)

    # Create usage policy
    policy = ReferencePackIntake.create_default_usage_policy()
    policy_path = reference_root / "reference_usage_policy.json"
    with open(policy_path, 'w', encoding='utf-8') as f:
        json.dump({
            "document_type": policy.document_type,
            "version": policy.version,
            "task_id": policy.task_id,
            "project_agnostic": policy.project_agnostic,
            "usage_policy": policy.usage_policy,
            "constraints": policy.constraints,
            "metadata": policy.metadata,
        }, f, indent=2)

    # Copy taxonomy definition
    taxonomy_source = Path("app/reference_pack/reference_slot_taxonomy.json")
    taxonomy_dest = reference_root / "reference_slot_taxonomy.json"
    if taxonomy_source.exists():
        if not taxonomy_dest.exists():
            import shutil
            shutil.copy(taxonomy_source, taxonomy_dest)

    result = {
        "status": "ok",
        "action": "reference_pack_initialized",
        "reference_root": str(reference_root),
        "pack_id": pack_id,
        "timestamp": timestamp,
        "project_agnostic": True,
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Reference pack initialized at: {reference_root}")
        print(f"Pack ID: {pack_id}")
        print(f"Project-agnostic: True")

    return 0


def validate_reference_pack(args: argparse.Namespace) -> int:
    """Validate a reference pack.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for validation failure)
    """
    reference_root = Path(args.reference_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    pack_path = reference_root / "reference_pack_manifest.json"

    if not pack_path.exists():
        result = {
            "status": "error",
            "action": "reference_pack_validated",
            "error": "reference_pack_manifest.json not found",
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: reference_pack_manifest.json not found")
        return 1

    # Load pack
    pack = ReferencePackIntake.load_pack_from_file(pack_path)

    # Validate
    is_valid, errors = ReferencePackIntake.validate_pack(pack)

    # Additional validation checks
    additional_errors: list[str] = []

    # Check for hardcoded project paths
    for slot_id, slot in pack.slots.items():
        for asset in slot.assets:
            if asset.file_path:
                path_errors = ReferencePackValidator.validate_file_path(asset.file_path)
                additional_errors.extend(path_errors)

    # Check no visual acceptance
    pack_dict = {
        "reference_pack_id": pack.reference_pack_id,
        "project_agnostic": pack.project_agnostic,
        "slots": {sid: {"status": s.status.value} for sid, s in pack.slots.items()},
    }
    visual_errors = ReferencePackValidator.validate_no_visual_acceptance(pack_dict)
    additional_errors.extend(visual_errors)

    all_errors = errors + additional_errors

    result = {
        "status": "ok" if not all_errors else "error",
        "action": "reference_pack_validated",
        "reference_root": str(reference_root),
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "timestamp": timestamp,
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if all_errors:
            print(f"Validation failed with {len(all_errors)} error(s):")
            for err in all_errors:
                print(f"  - {err}")
        else:
            print(f"Reference pack valid: {reference_root}")

    return 0 if not all_errors else 1


def inspect_reference_pack(args: argparse.Namespace) -> int:
    """Inspect a reference pack and print its contents.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    reference_root = Path(args.reference_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    pack_path = reference_root / "reference_pack_manifest.json"

    if not pack_path.exists():
        result = {
            "status": "error",
            "action": "reference_pack_inspected",
            "error": "reference_pack_manifest.json not found",
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: reference_pack_manifest.json not found")
        return 1

    # Load pack
    pack = ReferencePackIntake.load_pack_from_file(pack_path)

    # Build inspection result
    slots_summary = {}
    for slot_id, slot in pack.slots.items():
        slots_summary[slot_id] = {
            "category": slot.category.value,
            "status": slot.status.value,
            "assets_count": len(slot.assets),
            "required": slot.required,
        }

    result = {
        "status": "ok",
        "action": "reference_pack_inspected",
        "reference_root": str(reference_root),
        "pack_id": pack.reference_pack_id,
        "project_agnostic": pack.project_agnostic,
        "total_slots": len(pack.slots),
        "slots": slots_summary,
        "metadata": pack.metadata,
        "timestamp": timestamp,
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Reference Pack: {pack.reference_pack_id}")
        print(f"  Project-agnostic: {pack.project_agnostic}")
        print(f"  Total Slots: {len(pack.slots)}")
        for slot_id, summary in slots_summary.items():
            print(f"    - {slot_id}: {summary['status']} ({summary['assets_count']} assets)")

    return 0


def readiness_report(args: argparse.Namespace) -> int:
    """Generate readiness report for reference pack.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    reference_root = Path(args.reference_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    pack_path = reference_root / "reference_pack_manifest.json"

    if not pack_path.exists():
        result = {
            "status": "error",
            "action": "readiness_report_generated",
            "error": "reference_pack_manifest.json not found",
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: reference_pack_manifest.json not found")
        return 1

    # Load pack
    pack = ReferencePackIntake.load_pack_from_file(pack_path)

    # Generate canonicalization report
    report = ReferenceCanonicalizer.canonicalize_pack(pack)

    # Save report
    report_path = reference_root / "reference_readiness_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "document_type": report.document_type,
            "version": report.version,
            "task_id": report.task_id,
            "project_agnostic": report.project_agnostic,
            "reference_pack_id": report.reference_pack_id,
            "canonicalization_status": report.canonicalization_status,
            "slot_report": report.slot_report,
            "validation_results": report.validation_results,
            "readiness_assessment": report.readiness_assessment,
            "metadata": report.metadata,
        }, f, indent=2)

    result = {
        "status": "ok",
        "action": "readiness_report_generated",
        "reference_root": str(reference_root),
        "pack_id": pack.reference_pack_id,
        "canonicalization_status": report.canonicalization_status,
        "ready_for_generation": report.readiness_assessment["ready_for_generation"],
        "pending_operator_supply_count": report.readiness_assessment["pending_operator_supply_count"],
        "report_path": str(report_path),
        "timestamp": timestamp,
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Readiness Report Generated: {report_path}")
        print(f"  Canonicalization Status: {report.canonicalization_status}")
        print(f"  Ready for Generation: {report.readiness_assessment['ready_for_generation']}")
        print(f"  Pending Operator Supply: {report.readiness_assessment['pending_operator_supply_count']}")

    return 0
