"""Runtime gate inspector.

Inspects gate packets and provides detailed information.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.runtime_gate.models import (
    AuthorizationPolicy,
    GateTypeRegistry,
    RuntimeGatePacket,
)


class RuntimeGateInspector:
    """Inspector for runtime gate packets."""

    def __init__(self, gate_root: Path):
        """Initialize inspector with gate root directory."""
        self.gate_root = Path(gate_root)

    def inspect_packet(self, packet: RuntimeGatePacket) -> dict[str, Any]:
        """Inspect a gate packet and return detailed information."""
        return {
            "gate_id": packet.gate_id,
            "gate_type": packet.gate_type.value,
            "target_action": packet.target_action,
            "authorization_status": packet.authorization_status.value,
            "operator_authorization_required": packet.operator_authorization_required,
            "execution_allowed": packet.execution_allowed,
            "generation_authorized": packet.generation_authorized,
            "production_accepted": packet.production_accepted,
            "max_executions": packet.max_executions,
            "current_execution_count": packet.current_execution_count,
            "readiness_report_reference": packet.readiness_report_reference,
            "corrective_plan_reference": packet.corrective_plan_reference,
            "force_push_used": packet.force_push_used,
            "project_specific_hardcoding_detected": packet.project_specific_hardcoding_detected,
            "safety_violations": packet.safety_violations,
            "created_at": packet.created_at,
            "updated_at": packet.updated_at,
            "metadata": packet.metadata,
        }

    def inspect_file(self, file_path: Path) -> dict[str, Any]:
        """Inspect a gate packet file."""
        if not file_path.exists():
            return {
                "error": f"File not found: {file_path}",
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            packet = RuntimeGatePacket.from_dict(data)
            return self.inspect_packet(packet)

        except Exception as e:
            return {
                "error": f"Failed to inspect file: {e}",
            }

    def inspect_manifest(self) -> dict[str, Any]:
        """Inspect runtime gate manifest."""
        manifest_path = self.gate_root / "runtime_gate_manifest.json"
        if not manifest_path.exists():
            return {
                "error": f"Manifest not found: {manifest_path}",
            }

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            return {
                "error": f"Failed to inspect manifest: {e}",
            }

    def inspect_registry(self) -> dict[str, Any]:
        """Inspect gate type registry."""
        registry_path = self.gate_root / "gate_type_registry.json"
        if not registry_path.exists():
            return {
                "error": f"Registry not found: {registry_path}",
            }

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            return {
                "error": f"Failed to inspect registry: {e}",
            }

    def inspect_policy(self) -> dict[str, Any]:
        """Inspect authorization policy."""
        policy_path = self.gate_root / "authorization_policy.json"
        if not policy_path.exists():
            return {
                "error": f"Policy not found: {policy_path}",
            }

        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            return {
                "error": f"Failed to inspect policy: {e}",
            }

    def inspect_all(self) -> dict[str, Any]:
        """Inspect all gate artifacts."""
        return {
            "manifest": self.inspect_manifest(),
            "registry": self.inspect_registry(),
            "policy": self.inspect_policy(),
            "packets": self._inspect_all_packets(),
        }

    def _inspect_all_packets(self) -> dict[str, Any]:
        """Inspect all packet files."""
        packets = {}
        packet_files = list(self.gate_root.glob("*_packet.json"))
        for packet_file in packet_files:
            packets[packet_file.name] = self.inspect_file(packet_file)
        return packets

    def generate_readiness_report(self) -> dict[str, Any]:
        """Generate readiness report for gate layer."""
        manifest = self.inspect_manifest()
        registry = self.inspect_registry()
        policy = self.inspect_policy()
        packets = self._inspect_all_packets()

        # Check if manifest is valid
        manifest_valid = "error" not in manifest
        registry_valid = "error" not in registry
        policy_valid = "error" not in policy

        # Check packet safety
        safe_packets = 0
        total_packets = len(packets)
        for packet_name, packet_data in packets.items():
            if "error" not in packet_data:
                if not packet_data.get("execution_allowed", True):
                    if not packet_data.get("generation_authorized", True):
                        if not packet_data.get("production_accepted", True):
                            if not packet_data.get("force_push_used", True):
                                safe_packets += 1

        overall_ready = manifest_valid and registry_valid and policy_valid

        return {
            "task_id": "RC-COMBINE-V2-RUNTIME-GATE-AUTHORIZATION-CONTROL-001",
            "overall_ready": overall_ready,
            "manifest_valid": manifest_valid,
            "registry_valid": registry_valid,
            "policy_valid": policy_valid,
            "total_packets": total_packets,
            "safe_packets": safe_packets,
            "all_packets_safe": safe_packets == total_packets if total_packets > 0 else True,
            "manifest": manifest,
            "registry": registry,
            "policy": policy,
            "packets": packets,
            "metadata": {
                "description": "Runtime gate layer readiness report",
            },
        }
