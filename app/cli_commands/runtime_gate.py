"""CLI commands for runtime gate authorization control.

Task: RC-COMBINE-V2-RUNTIME-GATE-AUTHORIZATION-CONTROL-001
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.runtime_gate.builder import RuntimeGateBuilder
from app.runtime_gate.inspector import RuntimeGateInspector
from app.runtime_gate.models import GateType
from app.runtime_gate.validator import RuntimeGateValidator


def runtime_gate_build(args: argparse.Namespace) -> int:
    """Build runtime gate artifacts."""
    gate_root = Path(args.gate_root)
    json_output = args.json
    gate_type = args.gate_type
    target_action = args.target_action or f"{gate_type}_action"
    readiness_report = Path(args.readiness_report) if args.readiness_report else None
    corrective_plan_ref = args.corrective_plan_reference

    timestamp = datetime.now().isoformat()

    try:
        builder = RuntimeGateBuilder(gate_root)

        # Write base artifacts
        artifacts = builder.write_artifacts()

        # Build gate packet if gate type specified
        if gate_type:
            try:
                gate_type_enum = GateType(gate_type)
                packet = builder.build_gate_packet(
                    gate_type_enum,
                    target_action,
                    readiness_report,
                    corrective_plan_ref,
                )

                # Write packet
                packet_path = gate_root / "pending_gate_packet.json"
                with open(packet_path, "w", encoding="utf-8") as f:
                    json.dump(packet.to_dict(), f, indent=2, default=str)
                artifacts["packet"] = packet_path

                # Build and write safety report
                safety_report = builder.build_safety_report(packet)
                safety_report_path = gate_root / "gate_safety_report.json"
                with open(safety_report_path, "w", encoding="utf-8") as f:
                    json.dump(safety_report.to_dict(), f, indent=2, default=str)
                artifacts["safety_report"] = safety_report_path

            except ValueError:
                result = {
                    "status": "error",
                    "action": "runtime_gate_build",
                    "error": f"Invalid gate type: {gate_type}",
                    "valid_gate_types": [gt.value for gt in GateType],
                    "timestamp": timestamp,
                }
                if json_output:
                    print(json.dumps(result, indent=2))
                else:
                    print(f"Error: Invalid gate type: {gate_type}")
                    print(f"Valid gate types: {', '.join([gt.value for gt in GateType])}")
                return 1

        result = {
            "status": "ok",
            "action": "runtime_gate_build",
            "gate_root": str(gate_root),
            "artifacts": {k: str(v) for k, v in artifacts.items()},
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Runtime gate artifacts built at: {gate_root}")
            for name, path in artifacts.items():
                print(f"  - {name}: {path}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "runtime_gate_build",
            "gate_root": str(gate_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def runtime_gate_validate(args: argparse.Namespace) -> int:
    """Validate runtime gate artifacts."""
    gate_root = Path(args.gate_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        validator = RuntimeGateValidator(gate_root)
        validation_result = validator.validate_all()

        result = {
            "status": "ok" if validation_result["overall_valid"] else "error",
            "action": "runtime_gate_validate",
            "gate_root": str(gate_root),
            "overall_valid": validation_result["overall_valid"],
            "results": validation_result["results"],
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            if validation_result["overall_valid"]:
                print(f"All gate artifacts valid at: {gate_root}")
            else:
                print(f"Validation failed at: {gate_root}")
                for name, res in validation_result["results"].items():
                    if not res["valid"]:
                        print(f"  - {name}: FAILED")
                        for err in res["errors"]:
                            print(f"      {err}")
                    else:
                        print(f"  - {name}: OK")

        return 0 if validation_result["overall_valid"] else 1

    except Exception as e:
        result = {
            "status": "error",
            "action": "runtime_gate_validate",
            "gate_root": str(gate_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def runtime_gate_inspect(args: argparse.Namespace) -> int:
    """Inspect runtime gate artifacts."""
    gate_root = Path(args.gate_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        inspector = RuntimeGateInspector(gate_root)
        inspection_data = inspector.inspect_all()

        result = {
            "status": "ok",
            "action": "runtime_gate_inspect",
            "gate_root": str(gate_root),
            "inspection": inspection_data,
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Runtime gate inspection for: {gate_root}")
            print(f"  Manifest: {'OK' if 'error' not in inspection_data['manifest'] else 'ERROR'}")
            print(f"  Registry: {'OK' if 'error' not in inspection_data['registry'] else 'ERROR'}")
            print(f"  Policy: {'OK' if 'error' not in inspection_data['policy'] else 'ERROR'}")
            print(f"  Packets: {len(inspection_data['packets'])}")
            for packet_name, packet_data in inspection_data["packets"].items():
                if "error" not in packet_data:
                    print(f"    - {packet_name}: {packet_data['gate_type']} ({packet_data['authorization_status']})")
                else:
                    print(f"    - {packet_name}: ERROR")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "runtime_gate_inspect",
            "gate_root": str(gate_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def runtime_gate_readiness_report(args: argparse.Namespace) -> int:
    """Generate readiness report for runtime gate layer."""
    gate_root = Path(args.gate_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        inspector = RuntimeGateInspector(gate_root)
        report = inspector.generate_readiness_report()

        result = {
            "status": "ok",
            "action": "runtime_gate_readiness_report",
            "gate_root": str(gate_root),
            "report": report,
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Runtime gate readiness report for: {gate_root}")
            print(f"  Overall Ready: {report['overall_ready']}")
            print(f"  Manifest Valid: {report['manifest_valid']}")
            print(f"  Registry Valid: {report['registry_valid']}")
            print(f"  Policy Valid: {report['policy_valid']}")
            print(f"  Total Packets: {report['total_packets']}")
            print(f"  Safe Packets: {report['safe_packets']}")
            print(f"  All Packets Safe: {report['all_packets_safe']}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "runtime_gate_readiness_report",
            "gate_root": str(gate_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1
