"""Runtime gate packet builder.

Builds gate packets from readiness reports and gate type configurations.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.runtime_gate.models import (
    AuthorizationPolicy,
    AuthorizationStatus,
    GateSafetyReport,
    GateType,
    GateTypeConfig,
    GateTypeRegistry,
    RuntimeGateManifest,
    RuntimeGatePacket,
    SafetyCheck,
    SafetyRule,
)


class RuntimeGateBuilder:
    """Builder for runtime gate packets."""

    TASK_ID = "RC-COMBINE-V2-RUNTIME-GATE-AUTHORIZATION-CONTROL-001"

    def __init__(self, gate_root: Path):
        """Initialize builder with gate root directory."""
        self.gate_root = Path(gate_root)
        self.gate_root.mkdir(parents=True, exist_ok=True)

    def build_manifest(self) -> RuntimeGateManifest:
        """Build runtime gate manifest."""
        manifest = RuntimeGateManifest(
            task_id=self.TASK_ID,
            supported_gate_types=[gt.value for gt in GateType],
            authorization_policy="authorization_policy.json",
            metadata={
                "description": "Project-agnostic runtime gate authorization control layer",
            },
        )
        return manifest

    def build_gate_type_registry(self) -> GateTypeRegistry:
        """Build gate type registry with default configurations."""
        gate_types = {
            "generation_gate": GateTypeConfig(
                gate_type=GateType.GENERATION_GATE,
                default_max_executions=1,
                operator_authorization_required=True,
                dangerous_action=True,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "comfyui_submit",
                    "preview_render",
                    "voice_generation",
                    "assembly",
                    "downstream",
                ],
                description="Gate for visual generation actions",
            ),
            "retry_gate": GateTypeConfig(
                gate_type=GateType.RETRY_GATE,
                default_max_executions=3,
                operator_authorization_required=True,
                dangerous_action=True,
                required_inputs=["readiness_report", "corrective_plan"],
                forbidden_actions=[
                    "blind_retry",
                    "comfyui_submit",
                ],
                description="Gate for retry actions with corrective plan",
            ),
            "preview_render_gate": GateTypeConfig(
                gate_type=GateType.PREVIEW_RENDER_GATE,
                default_max_executions=5,
                operator_authorization_required=True,
                dangerous_action=False,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "production_acceptance",
                ],
                description="Gate for preview rendering",
            ),
            "voice_generation_gate": GateTypeConfig(
                gate_type=GateType.VOICE_GENERATION_GATE,
                default_max_executions=10,
                operator_authorization_required=True,
                dangerous_action=False,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "production_acceptance",
                ],
                description="Gate for voice generation",
            ),
            "assembly_gate": GateTypeConfig(
                gate_type=GateType.ASSEMBLY_GATE,
                default_max_executions=1,
                operator_authorization_required=True,
                dangerous_action=True,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "production_acceptance",
                ],
                description="Gate for assembly actions",
            ),
            "final_render_gate": GateTypeConfig(
                gate_type=GateType.FINAL_RENDER_GATE,
                default_max_executions=1,
                operator_authorization_required=True,
                dangerous_action=True,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "production_acceptance",
                ],
                description="Gate for final rendering",
            ),
            "asset_acquisition_gate": GateTypeConfig(
                gate_type=GateType.ASSET_ACQUISITION_GATE,
                default_max_executions=10,
                operator_authorization_required=True,
                dangerous_action=False,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "hidden_downloads",
                    "unauthorized_api_calls",
                ],
                description="Gate for asset acquisition",
            ),
            "external_api_call_gate": GateTypeConfig(
                gate_type=GateType.EXTERNAL_API_CALL_GATE,
                default_max_executions=100,
                operator_authorization_required=True,
                dangerous_action=False,
                required_inputs=["readiness_report"],
                forbidden_actions=[
                    "hidden_api_calls",
                ],
                description="Gate for external API calls",
            ),
        }

        registry = GateTypeRegistry(
            registry_id="default_gate_type_registry",
            version="1.0.0",
            gate_types=gate_types,
            metadata={
                "description": "Default gate type registry",
            },
        )
        return registry

    def build_authorization_policy(self) -> AuthorizationPolicy:
        """Build authorization policy."""
        safety_rules = [
            SafetyRule(
                rule_id="SR001",
                rule_description="generation_authorized must be false by default",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR002",
                rule_description="execution_allowed must be false by default",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR003",
                rule_description="production_accepted must always be false",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR004",
                rule_description="force_push_used must always be false",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR005",
                rule_description="operator authorization cannot be faked by CLI",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR006",
                rule_description="project-specific hardcoding is rejected",
                enforcement="strict",
            ),
            SafetyRule(
                rule_id="SR007",
                rule_description="rc2_multishot1_ep01 hardcoding is rejected",
                enforcement="strict",
            ),
        ]

        forbidden_patterns = [
            "rc2_multishot1_ep01",
            "production_accepted=true",
            "force_push_used=true",
        ]

        hardcoded_paths_blocked = [
            "rc2_multishot1_ep01",
            "/data/rc2/",
            "rc2_prodcards",
        ]

        policy = AuthorizationPolicy(
            policy_id="default_authorization_policy",
            version="1.0.0",
            safety_rules=safety_rules,
            forbidden_patterns=forbidden_patterns,
            hardcoded_paths_blocked=hardcoded_paths_blocked,
            metadata={
                "description": "Default authorization policy",
            },
        )
        return policy

    def build_gate_packet(
        self,
        gate_type: GateType,
        target_action: str,
        readiness_report_path: Path | None = None,
        corrective_plan_reference: str | None = None,
    ) -> RuntimeGatePacket:
        """Build a gate packet from readiness status.
        
        CRITICAL: This ALWAYS creates a pending_operator_authorization gate.
        Readiness=ready does NOT authorize execution.
        """
        # Load readiness report if provided
        readiness_status = "unknown"
        if readiness_report_path and readiness_report_path.exists():
            try:
                with open(readiness_report_path, "r", encoding="utf-8") as f:
                    readiness_data = json.load(f)
                    readiness_status = readiness_data.get("overall_status", "unknown")
            except (json.JSONDecodeError, OSError):
                readiness_status = "unknown"

        # Get gate type configuration
        registry = self.build_gate_type_registry()
        gate_config = registry.gate_types.get(gate_type.value)
        if gate_config is None:
            gate_config = GateTypeConfig(
                gate_type=gate_type,
                default_max_executions=1,
                operator_authorization_required=True,
                dangerous_action=True,
            )

        # Build gate packet
        # CRITICAL: authorization_status is ALWAYS pending_operator_authorization
        # CRITICAL: execution_allowed is ALWAYS false
        # CRITICAL: generation_authorized is ALWAYS false
        # CRITICAL: production_accepted is ALWAYS false
        packet = RuntimeGatePacket(
            gate_id=str(uuid.uuid4()),
            gate_type=gate_type,
            target_action=target_action,
            required_readiness_status="ready_for_operator_generation_authorization",
            authorization_status=AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION,
            operator_authorization_required=gate_config.operator_authorization_required,
            execution_allowed=False,  # NEVER true
            generation_authorized=False,  # NEVER true
            production_accepted=False,  # NEVER true
            required_inputs=gate_config.required_inputs,
            forbidden_actions=gate_config.forbidden_actions,
            max_executions=gate_config.default_max_executions,
            current_execution_count=0,
            readiness_report_reference=str(readiness_report_path) if readiness_report_path else None,
            corrective_plan_reference=corrective_plan_reference,
            force_push_used=False,  # NEVER true
            project_specific_hardcoding_detected={},
            safety_violations=[],
            metadata={
                "readiness_status": readiness_status,
                "task_id": self.TASK_ID,
            },
        )

        # Check for project-specific hardcoding
        self._check_hardcoding(packet, readiness_report_path)

        return packet

    def _check_hardcoding(
        self,
        packet: RuntimeGatePacket,
        readiness_report_path: Path | None = None,
    ) -> None:
        """Check for project-specific hardcoding."""
        hardcoded_patterns = ["rc2_multishot1_ep01", "/data/rc2/", "rc2_prodcards"]
        detected = {}

        if readiness_report_path and readiness_report_path.exists():
            try:
                with open(readiness_report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pattern in hardcoded_patterns:
                        if pattern in content:
                            if pattern not in detected:
                                detected[pattern] = []
                            detected[pattern].append(f"Found in {readiness_report_path}")
            except OSError:
                pass

        if detected:
            packet.project_specific_hardcoding_detected = detected
            packet.authorization_status = AuthorizationStatus.BLOCKED
            packet.safety_violations.append("Project-specific hardcoding detected")

    def build_safety_report(self, packet: RuntimeGatePacket) -> GateSafetyReport:
        """Build safety report for a gate packet."""
        checks = []
        violations = []
        warnings = []

        # Check 1: execution_allowed is false
        check1 = SafetyCheck(
            check_id="SC001",
            check_description="execution_allowed must be false",
            passed=not packet.execution_allowed,
            details="execution_allowed is false" if not packet.execution_allowed else "VIOLATION: execution_allowed is true",
        )
        checks.append(check1)
        if not check1.passed:
            violations.append("execution_allowed must be false")

        # Check 2: generation_authorized is false
        check2 = SafetyCheck(
            check_id="SC002",
            check_description="generation_authorized must be false",
            passed=not packet.generation_authorized,
            details="generation_authorized is false" if not packet.generation_authorized else "VIOLATION: generation_authorized is true",
        )
        checks.append(check2)
        if not check2.passed:
            violations.append("generation_authorized must be false")

        # Check 3: production_accepted is false
        check3 = SafetyCheck(
            check_id="SC003",
            check_description="production_accepted must be false",
            passed=not packet.production_accepted,
            details="production_accepted is false" if not packet.production_accepted else "VIOLATION: production_accepted is true",
        )
        checks.append(check3)
        if not check3.passed:
            violations.append("production_accepted must be false")

        # Check 4: force_push_used is false
        check4 = SafetyCheck(
            check_id="SC004",
            check_description="force_push_used must be false",
            passed=not packet.force_push_used,
            details="force_push_used is false" if not packet.force_push_used else "VIOLATION: force_push_used is true",
        )
        checks.append(check4)
        if not check4.passed:
            violations.append("force_push_used must be false")

        # Check 5: authorization status is pending or blocked
        check5 = SafetyCheck(
            check_id="SC005",
            check_description="authorization_status must be pending_operator_authorization or blocked",
            passed=packet.authorization_status in [
                AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION,
                AuthorizationStatus.BLOCKED,
            ],
            details=f"authorization_status is {packet.authorization_status.value}",
        )
        checks.append(check5)
        if not check5.passed:
            warnings.append("authorization_status should be pending_operator_authorization")

        # Check 6: no project-specific hardcoding
        check6 = SafetyCheck(
            check_id="SC006",
            check_description="no project-specific hardcoding",
            passed=len(packet.project_specific_hardcoding_detected) == 0,
            details=f"Found {len(packet.project_specific_hardcoding_detected)} hardcoded patterns" if packet.project_specific_hardcoding_detected else "No hardcoding detected",
        )
        checks.append(check6)
        if not check6.passed:
            violations.append("Project-specific hardcoding detected")

        safe = len(violations) == 0

        report = GateSafetyReport(
            report_id=str(uuid.uuid4()),
            gate_id=packet.gate_id,
            safe=safe,
            safety_checks=checks,
            violations=violations,
            warnings=warnings,
            metadata={
                "packet_target_action": packet.target_action,
                "packet_gate_type": packet.gate_type.value,
            },
        )
        return report

    def write_artifacts(self) -> dict[str, Path]:
        """Write all gate artifacts to disk."""
        artifacts = {}

        # Write manifest
        manifest = self.build_manifest()
        manifest_path = self.gate_root / "runtime_gate_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, default=str)
        artifacts["manifest"] = manifest_path

        # Write gate type registry
        registry = self.build_gate_type_registry()
        registry_path = self.gate_root / "gate_type_registry.json"
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry.to_dict(), f, indent=2, default=str)
        artifacts["registry"] = registry_path

        # Write authorization policy
        policy = self.build_authorization_policy()
        policy_path = self.gate_root / "authorization_policy.json"
        with open(policy_path, "w", encoding="utf-8") as f:
            json.dump(policy.to_dict(), f, indent=2, default=str)
        artifacts["policy"] = policy_path

        return artifacts
