"""Runtime gate validator.

Validates gate packets against safety rules and authorization policies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.runtime_gate.models import (
    AuthorizationPolicy,
    GateSafetyReport,
    GateTypeRegistry,
    RuntimeGatePacket,
)


class RuntimeGateValidator:
    """Validator for runtime gate packets."""

    def __init__(self, gate_root: Path):
        """Initialize validator with gate root directory."""
        self.gate_root = Path(gate_root)

    def validate_packet(self, packet: RuntimeGatePacket, policy: AuthorizationPolicy) -> list[str]:
        """Validate a gate packet against authorization policy.
        
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Validate execution_allowed is false
        if packet.execution_allowed:
            errors.append("execution_allowed must be false")

        # Validate generation_authorized is false
        if packet.generation_authorized:
            errors.append("generation_authorized must be false")

        # Validate production_accepted is false
        if packet.production_accepted:
            errors.append("production_accepted must be false")

        # Validate force_push_used is false
        if packet.force_push_used:
            errors.append("force_push_used must be false")

        # Validate authorization status
        if packet.authorization_status.value not in [
            "draft",
            "pending_operator_authorization",
            "authorized_not_executed",
            "consumed",
            "revoked",
            "blocked",
        ]:
            errors.append(f"Invalid authorization_status: {packet.authorization_status.value}")

        # Validate no project-specific hardcoding
        if packet.project_specific_hardcoding_detected:
            errors.append("Project-specific hardcoding detected")

        # Validate against forbidden patterns
        packet_str = json.dumps(packet.to_dict())
        for pattern in policy.forbidden_patterns:
            if pattern in packet_str:
                errors.append(f"Forbidden pattern detected: {pattern}")

        # Validate max_executions
        if packet.max_executions < 1:
            errors.append("max_executions must be at least 1")

        # Validate current_execution_count
        if packet.current_execution_count < 0:
            errors.append("current_execution_count cannot be negative")
        if packet.current_execution_count > packet.max_executions:
            errors.append("current_execution_count exceeds max_executions")

        # Validate retry gate has corrective plan
        if packet.gate_type.value == "retry_gate" and not packet.corrective_plan_reference:
            errors.append("retry_gate requires corrective_plan_reference")

        return errors

    def validate_file(self, file_path: Path) -> dict[str, Any]:
        """Validate a gate packet file.
        
        Returns validation result with valid flag and errors list.
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
        }

        if not file_path.exists():
            result["errors"].append(f"File not found: {file_path}")
            return result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Try to parse as RuntimeGatePacket
            try:
                packet = RuntimeGatePacket.from_dict(data)
                
                # Load policy
                policy_path = self.gate_root / "authorization_policy.json"
                if policy_path.exists():
                    with open(policy_path, "r", encoding="utf-8") as f:
                        policy_data = json.load(f)
                    policy = AuthorizationPolicy.from_dict(policy_data)
                else:
                    policy = AuthorizationPolicy(
                        policy_id="default",
                        version="1.0.0",
                    )

                errors = self.validate_packet(packet, policy)
                result["errors"].extend(errors)
                result["valid"] = len(errors) == 0

            except Exception as e:
                result["errors"].append(f"Failed to parse gate packet: {e}")

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")

        return result

    def validate_manifest(self, manifest_path: Path) -> dict[str, Any]:
        """Validate runtime gate manifest."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
        }

        if not manifest_path.exists():
            result["errors"].append(f"Manifest not found: {manifest_path}")
            return result

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check required fields
            required_fields = ["task_id", "document_type", "version", "project_agnostic", "created", "gate_layer_active"]
            for field in required_fields:
                if field not in data:
                    result["errors"].append(f"Missing required field: {field}")

            # Check document_type
            if data.get("document_type") != "runtime_gate_manifest":
                result["errors"].append(f"Invalid document_type: {data.get('document_type')}")

            # Check project_agnostic
            if not data.get("project_agnostic"):
                result["errors"].append("project_agnostic must be true")

            # Check gate_layer_active
            if not data.get("gate_layer_active"):
                result["errors"].append("gate_layer_active must be true")

            result["valid"] = len(result["errors"]) == 0

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")

        return result

    def validate_registry(self, registry_path: Path) -> dict[str, Any]:
        """Validate gate type registry."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
        }

        if not registry_path.exists():
            result["errors"].append(f"Registry not found: {registry_path}")
            return result

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check required fields
            required_fields = ["registry_id", "version", "gate_types"]
            for field in required_fields:
                if field not in data:
                    result["errors"].append(f"Missing required field: {field}")

            # Check project_agnostic
            if not data.get("project_agnostic"):
                result["errors"].append("project_agnostic must be true")

            # Validate gate_types
            gate_types = data.get("gate_types", {})
            for gt_key, gt_config in gate_types.items():
                if "gate_type" not in gt_config:
                    result["errors"].append(f"Gate type {gt_key} missing gate_type field")
                if "default_max_executions" not in gt_config:
                    result["errors"].append(f"Gate type {gt_key} missing default_max_executions")
                if "operator_authorization_required" not in gt_config:
                    result["errors"].append(f"Gate type {gt_key} missing operator_authorization_required")

            result["valid"] = len(result["errors"]) == 0

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")

        return result

    def validate_all(self) -> dict[str, Any]:
        """Validate all gate artifacts."""
        results = {
            "manifest": self.validate_manifest(self.gate_root / "runtime_gate_manifest.json"),
            "registry": self.validate_registry(self.gate_root / "gate_type_registry.json"),
        }

        # Validate policy file separately (not as a packet)
        policy_path = self.gate_root / "authorization_policy.json"
        if policy_path.exists():
            try:
                with open(policy_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Check required fields
                required_fields = ["policy_id", "version", "core_rule", "safety_rules"]
                policy_errors = []
                for field in required_fields:
                    if field not in data:
                        policy_errors.append(f"Missing required field: {field}")
                results["policy"] = {
                    "valid": len(policy_errors) == 0,
                    "errors": policy_errors,
                    "warnings": [],
                }
            except Exception as e:
                results["policy"] = {
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": [],
                }
        else:
            results["policy"] = {
                "valid": False,
                "errors": ["Policy file not found"],
                "warnings": [],
            }

        # Validate any packet files
        packet_files = list(self.gate_root.glob("*_packet.json"))
        for packet_file in packet_files:
            results[packet_file.name] = self.validate_file(packet_file)

        overall_valid = all(r["valid"] for r in results.values())

        return {
            "overall_valid": overall_valid,
            "results": results,
        }
