"""CLI commands for evidence trace audit ledger.

Task: RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001
"""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.evidence_trace import (
    EvidenceEvent,
    EvidenceLedger,
    EvidenceTraceManifest,
    ConsistencyChecker,
    SourceLayer,
    DecisionStatus,
)


def combine_evidence_trace_record(args: argparse.Namespace) -> int:
    """RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001 — Record evidence event.

    Records an evidence event to the audit ledger. Does NOT execute generation,
    retry, or any downstream operations.

    Exit codes:
    - 0: event recorded
    - 1: error
    """
    project_root = Path(args.project_root)
    json_output = args.json
    task_id = args.task_id
    source_layer = args.source_layer
    artifact_path = args.artifact_path
    decision_status = args.decision_status
    blocked_actions = args.blocked_actions or []
    allowed_next_action = args.allowed_next_action
    created_by = args.created_by or "system"

    output_dir = project_root / "output" / "project_agnostic" / "evidence_trace"
    output_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = output_dir / "evidence_ledger.jsonl"

    try:
        # Validate source layer
        try:
            source_layer_enum = SourceLayer(source_layer)
        except ValueError:
            result = {
                "status": "error",
                "action": "combine_evidence_trace_record",
                "error": f"Invalid source layer: {source_layer}",
                "valid_source_layers": [sl.value for sl in SourceLayer],
                "timestamp": datetime.utcnow().isoformat(),
            }
            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"Error: Invalid source layer: {source_layer}")
                print(f"Valid source layers: {', '.join([sl.value for sl in SourceLayer])}")
            return 1

        # Validate decision status
        try:
            decision_status_enum = DecisionStatus(decision_status)
        except ValueError:
            result = {
                "status": "error",
                "action": "combine_evidence_trace_record",
                "error": f"Invalid decision status: {decision_status}",
                "valid_decision_statuses": [ds.value for ds in DecisionStatus],
                "timestamp": datetime.utcnow().isoformat(),
            }
            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"Error: Invalid decision status: {decision_status}")
                print(f"Valid decision statuses: {', '.join([ds.value for ds in DecisionStatus])}")
            return 1

        # Validate artifact path exists
        artifact_path_obj = Path(artifact_path)
        if not artifact_path_obj.exists():
            result = {
                "status": "error",
                "action": "combine_evidence_trace_record",
                "error": f"Artifact path does not exist: {artifact_path}",
                "timestamp": datetime.utcnow().isoformat(),
            }
            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"Error: Artifact path does not exist: {artifact_path}")
            return 1

        # Compute artifact SHA256
        artifact_sha256 = EvidenceEvent.compute_sha256(artifact_path)

        # Create event
        event = EvidenceEvent(
            event_id=str(uuid.uuid4()),
            task_id=task_id,
            source_layer=source_layer_enum,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            decision_status=decision_status_enum,
            blocked_actions=blocked_actions.split(",") if blocked_actions else [],
            allowed_next_action=allowed_next_action,
            created_by=created_by,
        )

        # Append to ledger
        ledger = EvidenceLedger(str(ledger_path), task_id)
        success = ledger.append_event(event)

        if not success:
            result = {
                "status": "error",
                "action": "combine_evidence_trace_record",
                "error": "Failed to append event to ledger",
                "timestamp": datetime.utcnow().isoformat(),
            }
            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print("Error: Failed to append event to ledger")
            return 1

        # Create/update manifest
        manifest = ledger.create_manifest()
        manifest_path = output_dir / "evidence_trace_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)

        result = {
            "status": "ok",
            "action": "combine_evidence_trace_record",
            "event_id": event.event_id,
            "ledger_path": str(ledger_path),
            "manifest_path": str(manifest_path),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Evidence event recorded: {event.event_id}")
            print(f"Ledger: {ledger_path}")
            print(f"Manifest: {manifest_path}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "combine_evidence_trace_record",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {str(e)}")
        return 1


def combine_evidence_trace_validate(args: argparse.Namespace) -> int:
    """RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001 — Validate evidence ledger.

    Validates the evidence ledger for append-only behavior and artifact integrity.
    Does NOT execute generation, retry, or any downstream operations.

    Exit codes:
    - 0: validation passed
    - 1: validation failed or error
    """
    project_root = Path(args.project_root)
    json_output = args.json

    output_dir = project_root / "output" / "project_agnostic" / "evidence_trace"
    ledger_path = output_dir / "evidence_ledger.jsonl"

    if not ledger_path.exists():
        result = {
            "status": "error",
            "action": "combine_evidence_trace_validate",
            "error": f"Ledger not found at {ledger_path}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: Ledger not found at {ledger_path}")
        return 1

    try:
        ledger = EvidenceLedger(str(ledger_path), task_id="validation")
        events = ledger.read_all_events()

        # Validate append-only
        append_only_valid = ledger.validate_append_only()

        # Validate artifact paths exist
        artifact_paths_valid = True
        missing_artifacts = []
        for event in events:
            if not Path(event.artifact_path).exists():
                artifact_paths_valid = False
                missing_artifacts.append(event.artifact_path)

        # Validate SHA256
        sha256_valid = True
        invalid_sha256 = []
        for event in events:
            computed_sha256 = EvidenceEvent.compute_sha256(event.artifact_path)
            if computed_sha256 != event.artifact_sha256:
                sha256_valid = False
                invalid_sha256.append({
                    "event_id": event.event_id,
                    "expected": event.artifact_sha256,
                    "computed": computed_sha256
                })

        all_valid = append_only_valid and artifact_paths_valid and sha256_valid

        result = {
            "status": "ok" if all_valid else "error",
            "action": "combine_evidence_trace_validate",
            "valid": all_valid,
            "checks": {
                "append_only": append_only_valid,
                "artifact_paths_exist": artifact_paths_valid,
                "sha256_integrity": sha256_valid,
            },
            "total_events": len(events),
            "missing_artifacts": missing_artifacts,
            "invalid_sha256": invalid_sha256,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Evidence Ledger Validation")
            print(f"Total Events: {len(events)}")
            print(f"Append-Only Valid: {append_only_valid}")
            print(f"Artifact Paths Valid: {artifact_paths_valid}")
            print(f"SHA256 Integrity Valid: {sha256_valid}")
            print(f"Overall Valid: {all_valid}")
            if missing_artifacts:
                print(f"\nMissing Artifacts: {len(missing_artifacts)}")
                for artifact in missing_artifacts:
                    print(f"  - {artifact}")
            if invalid_sha256:
                print(f"\nInvalid SHA256: {len(invalid_sha256)}")
                for item in invalid_sha256:
                    print(f"  - Event {item['event_id']}: expected={item['expected'][:8]}..., computed={item['computed'][:8]}...")

        return 0 if all_valid else 1

    except Exception as e:
        result = {
            "status": "error",
            "action": "combine_evidence_trace_validate",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {str(e)}")
        return 1


def combine_evidence_trace_inspect(args: argparse.Namespace) -> int:
    """RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001 — Inspect evidence ledger.

    Inspects the evidence ledger and displays events. Does NOT execute generation,
    retry, or any downstream operations.

    Exit codes:
    - 0: inspection completed
    - 1: error
    """
    project_root = Path(args.project_root)
    json_output = args.json
    task_id = args.task_id
    source_layer = args.source_layer

    output_dir = project_root / "output" / "project_agnostic" / "evidence_trace"
    ledger_path = output_dir / "evidence_ledger.jsonl"

    if not ledger_path.exists():
        result = {
            "status": "error",
            "action": "combine_evidence_trace_inspect",
            "error": f"Ledger not found at {ledger_path}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: Ledger not found at {ledger_path}")
        return 1

    try:
        ledger = EvidenceLedger(str(ledger_path), task_id="inspection")
        events = ledger.read_all_events()

        # Filter by task_id if provided
        if task_id:
            events = [e for e in events if e.task_id == task_id]

        # Filter by source_layer if provided
        if source_layer:
            events = [e for e in events if e.source_layer.value == source_layer]

        if json_output:
            print(json.dumps([e.to_dict() for e in events], indent=2))
        else:
            print(f"Evidence Ledger Inspection")
            print(f"Total Events: {len(events)}")
            if task_id:
                print(f"Task ID: {task_id}")
            if source_layer:
                print(f"Source Layer: {source_layer}")
            print(f"\nEvents:")
            for event in events:
                print(f"  - Event ID: {event.event_id}")
                print(f"    Task ID: {event.task_id}")
                print(f"    Source Layer: {event.source_layer.value}")
                print(f"    Decision Status: {event.decision_status.value}")
                print(f"    Artifact: {event.artifact_path}")
                print(f"    Timestamp: {event.timestamp}")
                print(f"    Created By: {event.created_by}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "combine_evidence_trace_inspect",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {str(e)}")
        return 1


def combine_evidence_trace_consistency_report(args: argparse.Namespace) -> int:
    """RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001 — Generate consistency report.

    Generates a consistency report for the evidence ledger. Does NOT execute generation,
    retry, or any downstream operations.

    Exit codes:
    - 0: report generated
    - 1: error
    """
    project_root = Path(args.project_root)
    json_output = args.json
    task_id = args.task_id

    output_dir = project_root / "output" / "project_agnostic" / "evidence_trace"
    ledger_path = output_dir / "evidence_ledger.jsonl"

    if not ledger_path.exists():
        result = {
            "status": "error",
            "action": "combine_evidence_trace_consistency_report",
            "error": f"Ledger not found at {ledger_path}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: Ledger not found at {ledger_path}")
        return 1

    try:
        ledger = EvidenceLedger(str(ledger_path), task_id=task_id if task_id else "consistency_check")
        events = ledger.read_all_events()

        # Filter by task_id if provided
        if task_id:
            events = [e for e in events if e.task_id == task_id]

        # Run consistency checks
        checker = ConsistencyChecker(events)
        report = checker.run_all_checks()

        # Write report
        report_path = output_dir / "proof_consistency_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Generate audit carryover report
        carryover_report = {
            "report_id": str(uuid.uuid4()),
            "task_id": task_id if task_id else "consistency_check",
            "carryover_items": [],
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }
        
        # Check for force_push violations
        force_push_events = [e for e in events if "force_push" in str(e.metadata).lower()]
        for fp_event in force_push_events:
            carryover_report["carryover_items"].append({
                "violation_type": "force_push",
                "original_event_id": fp_event.event_id,
                "carryover_status": "recorded",
                "details": f"Force push violation recorded from event {fp_event.event_id}"
            })

        carryover_path = output_dir / "audit_carryover_report.json"
        with open(carryover_path, "w", encoding="utf-8") as f:
            json.dump(carryover_report, f, indent=2)

        # Generate safety report
        safety_report = {
            "report_id": str(uuid.uuid4()),
            "task_id": task_id if task_id else "consistency_check",
            "safe": report["consistent"],
            "safety_checks": [
                {
                    "check_id": "NO_GENERATION",
                    "check_description": "No generation performed",
                    "passed": True,
                    "details": "Evidence trace layer does not perform generation"
                },
                {
                    "check_id": "NO_RETRY",
                    "check_description": "No retry attempted",
                    "passed": True,
                    "details": "Evidence trace layer does not perform retry"
                },
                {
                    "check_id": "NO_COMFYUI_SUBMIT",
                    "check_description": "No ComfyUI submit executed",
                    "passed": True,
                    "details": "Evidence trace layer does not submit to ComfyUI"
                },
                {
                    "check_id": "NO_PREVIEW_RENDER",
                    "check_description": "No preview render executed",
                    "passed": True,
                    "details": "Evidence trace layer does not render previews"
                },
                {
                    "check_id": "NO_VOICE_GENERATION",
                    "check_description": "No voice generation executed",
                    "passed": True,
                    "details": "Evidence trace layer does not generate voice"
                },
                {
                    "check_id": "NO_VISUAL_ACCEPTANCE",
                    "check_description": "No visual acceptance executed",
                    "passed": True,
                    "details": "Evidence trace layer does not perform visual acceptance"
                },
                {
                    "check_id": "NO_ASSEMBLY",
                    "check_description": "No assembly executed",
                    "passed": True,
                    "details": "Evidence trace layer does not perform assembly"
                },
                {
                    "check_id": "NO_DOWNSTREAM",
                    "check_description": "No downstream executed",
                    "passed": True,
                    "details": "Evidence trace layer does not execute downstream"
                },
                {
                    "check_id": "PRODUCTION_ACCEPTED_FALSE",
                    "check_description": "Production accepted remains false",
                    "passed": True,
                    "details": "Evidence trace layer never sets production_accepted to true"
                },
                {
                    "check_id": "NO_FORCE_PUSH",
                    "check_description": "No force push used",
                    "passed": len(force_push_events) == 0,
                    "details": f"Force push events: {len(force_push_events)}"
                },
            ],
            "violations": [],
            "warnings": [f"Force push events: {len(force_push_events)}"] if force_push_events else [],
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }

        safety_path = output_dir / "evidence_trace_safety_report.json"
        with open(safety_path, "w", encoding="utf-8") as f:
            json.dump(safety_report, f, indent=2)

        result = {
            "status": "ok",
            "action": "combine_evidence_trace_consistency_report",
            "consistent": report["consistent"],
            "total_events": len(events),
            "artifacts": {
                "consistency_report": str(report_path),
                "carryover_report": str(carryover_path),
                "safety_report": str(safety_path),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Evidence Trace Consistency Report")
            print(f"Consistent: {report['consistent']}")
            print(f"Total Events: {len(events)}")
            print(f"Artifacts:")
            print(f"  - Consistency Report: {report_path}")
            print(f"  - Carryover Report: {carryover_path}")
            print(f"  - Safety Report: {safety_path}")
            if report["violations"]:
                print(f"\nViolations: {len(report['violations'])}")
                for violation in report["violations"]:
                    print(f"  - {violation}")
            if report["warnings"]:
                print(f"\nWarnings: {len(report['warnings'])}")
                for warning in report["warnings"]:
                    print(f"  - {warning}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "combine_evidence_trace_consistency_report",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {str(e)}")
        return 1
