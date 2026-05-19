"""Data models for runtime gate authorization control.

Project-agnostic models for gate packet creation and validation.
Core rule: readiness=ready does NOT mean execution_allowed=true.
Readiness only creates pending_operator_authorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GateType(str, Enum):
    """Types of runtime gates."""
    GENERATION_GATE = "generation_gate"
    RETRY_GATE = "retry_gate"
    PREVIEW_RENDER_GATE = "preview_render_gate"
    VOICE_GENERATION_GATE = "voice_generation_gate"
    ASSEMBLY_GATE = "assembly_gate"
    FINAL_RENDER_GATE = "final_render_gate"
    ASSET_ACQUISITION_GATE = "asset_acquisition_gate"
    EXTERNAL_API_CALL_GATE = "external_api_call_gate"


class AuthorizationStatus(str, Enum):
    """Authorization status for a gate."""
    DRAFT = "draft"
    PENDING_OPERATOR_AUTHORIZATION = "pending_operator_authorization"
    AUTHORIZED_NOT_EXECUTED = "authorized_not_executed"
    CONSUMED = "consumed"
    REVOKED = "revoked"
    BLOCKED = "blocked"


@dataclass
class RuntimeGatePacket:
    """Runtime gate packet for authorization control.
    
    CRITICAL: execution_allowed is ALWAYS false by default.
    Readiness only creates pending_operator_authorization, NOT authorization.
    """
    gate_id: str
    gate_type: GateType
    target_action: str
    required_readiness_status: str
    authorization_status: AuthorizationStatus = AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION
    operator_authorization_required: bool = True
    execution_allowed: bool = False  # NEVER true by this layer
    generation_authorized: bool = False  # NEVER true by this layer
    production_accepted: bool = False  # NEVER true by this layer
    required_inputs: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    max_executions: int = 1
    current_execution_count: int = 0
    readiness_report_reference: str | None = None
    corrective_plan_reference: str | None = None
    force_push_used: bool = False  # NEVER true
    project_specific_hardcoding_detected: dict[str, list[str]] = field(default_factory=dict)
    safety_violations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type.value,
            "target_action": self.target_action,
            "required_readiness_status": self.required_readiness_status,
            "authorization_status": self.authorization_status.value,
            "operator_authorization_required": self.operator_authorization_required,
            "execution_allowed": self.execution_allowed,
            "generation_authorized": self.generation_authorized,
            "production_accepted": self.production_accepted,
            "required_inputs": self.required_inputs,
            "forbidden_actions": self.forbidden_actions,
            "max_executions": self.max_executions,
            "current_execution_count": self.current_execution_count,
            "readiness_report_reference": self.readiness_report_reference,
            "corrective_plan_reference": self.corrective_plan_reference,
            "force_push_used": self.force_push_used,
            "project_specific_hardcoding_detected": self.project_specific_hardcoding_detected,
            "safety_violations": self.safety_violations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeGatePacket":
        """Create from dictionary."""
        return cls(
            gate_id=data["gate_id"],
            gate_type=GateType(data["gate_type"]),
            target_action=data["target_action"],
            required_readiness_status=data["required_readiness_status"],
            authorization_status=AuthorizationStatus(data.get("authorization_status", "pending_operator_authorization")),
            operator_authorization_required=data.get("operator_authorization_required", True),
            execution_allowed=data.get("execution_allowed", False),
            generation_authorized=data.get("generation_authorized", False),
            production_accepted=data.get("production_accepted", False),
            required_inputs=data.get("required_inputs", []),
            forbidden_actions=data.get("forbidden_actions", []),
            max_executions=data.get("max_executions", 1),
            current_execution_count=data.get("current_execution_count", 0),
            readiness_report_reference=data.get("readiness_report_reference"),
            corrective_plan_reference=data.get("corrective_plan_reference"),
            force_push_used=data.get("force_push_used", False),
            project_specific_hardcoding_detected=data.get("project_specific_hardcoding_detected", {}),
            safety_violations=data.get("safety_violations", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RuntimeGateManifest:
    """Manifest for runtime gate layer."""
    task_id: str
    document_type: str = "runtime_gate_manifest"
    version: str = "1.0.0"
    project_agnostic: bool = True
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    gate_layer_active: bool = True
    supported_gate_types: list[str] = field(default_factory=list)
    authorization_policy: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "document_type": self.document_type,
            "version": self.version,
            "project_agnostic": self.project_agnostic,
            "created": self.created,
            "gate_layer_active": self.gate_layer_active,
            "supported_gate_types": self.supported_gate_types,
            "authorization_policy": self.authorization_policy,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeGateManifest":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            document_type=data.get("document_type", "runtime_gate_manifest"),
            version=data.get("version", "1.0.0"),
            project_agnostic=data.get("project_agnostic", True),
            created=data.get("created", datetime.utcnow().isoformat()),
            gate_layer_active=data.get("gate_layer_active", True),
            supported_gate_types=data.get("supported_gate_types", []),
            authorization_policy=data.get("authorization_policy"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GateTypeConfig:
    """Configuration for a gate type."""
    gate_type: GateType
    default_max_executions: int
    operator_authorization_required: bool
    dangerous_action: bool
    required_inputs: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_type": self.gate_type.value,
            "default_max_executions": self.default_max_executions,
            "operator_authorization_required": self.operator_authorization_required,
            "dangerous_action": self.dangerous_action,
            "required_inputs": self.required_inputs,
            "forbidden_actions": self.forbidden_actions,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateTypeConfig":
        """Create from dictionary."""
        return cls(
            gate_type=GateType(data["gate_type"]),
            default_max_executions=data["default_max_executions"],
            operator_authorization_required=data["operator_authorization_required"],
            dangerous_action=data["dangerous_action"],
            required_inputs=data.get("required_inputs", []),
            forbidden_actions=data.get("forbidden_actions", []),
            description=data.get("description", ""),
        )


@dataclass
class GateTypeRegistry:
    """Registry of supported gate types."""
    registry_id: str
    version: str
    gate_types: dict[str, GateTypeConfig] = field(default_factory=dict)
    project_agnostic: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "project_agnostic": self.project_agnostic,
            "gate_types": {k: v.to_dict() for k, v in self.gate_types.items()},
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateTypeRegistry":
        """Create from dictionary."""
        return cls(
            registry_id=data["registry_id"],
            version=data["version"],
            gate_types={
                k: GateTypeConfig.from_dict(v)
                for k, v in data.get("gate_types", {}).items()
            },
            project_agnostic=data.get("project_agnostic", True),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SafetyRule:
    """A safety rule."""
    rule_id: str
    rule_description: str
    enforcement: str  # strict, warning, log

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_description": self.rule_description,
            "enforcement": self.enforcement,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SafetyRule":
        """Create from dictionary."""
        return cls(
            rule_id=data["rule_id"],
            rule_description=data["rule_description"],
            enforcement=data["enforcement"],
        )


@dataclass
class AuthorizationPolicy:
    """Authorization policy for runtime gate layer."""
    policy_id: str
    version: str
    core_rule: str = "readiness=ready does NOT mean execution_allowed=true. Readiness only creates pending_operator_authorization."
    safety_rules: list[SafetyRule] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)
    hardcoded_paths_blocked: list[str] = field(default_factory=list)
    project_agnostic: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "project_agnostic": self.project_agnostic,
            "core_rule": self.core_rule,
            "safety_rules": [r.to_dict() for r in self.safety_rules],
            "forbidden_patterns": self.forbidden_patterns,
            "hardcoded_paths_blocked": self.hardcoded_paths_blocked,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthorizationPolicy":
        """Create from dictionary."""
        return cls(
            policy_id=data["policy_id"],
            version=data["version"],
            core_rule=data.get("core_rule", "readiness=ready does NOT mean execution_allowed=true. Readiness only creates pending_operator_authorization."),
            safety_rules=[SafetyRule.from_dict(r) for r in data.get("safety_rules", [])],
            forbidden_patterns=data.get("forbidden_patterns", []),
            hardcoded_paths_blocked=data.get("hardcoded_paths_blocked", []),
            project_agnostic=data.get("project_agnostic", True),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SafetyCheck:
    """A safety check result."""
    check_id: str
    check_description: str
    passed: bool
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "check_description": self.check_description,
            "passed": self.passed,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SafetyCheck":
        """Create from dictionary."""
        return cls(
            check_id=data["check_id"],
            check_description=data["check_description"],
            passed=data["passed"],
            details=data.get("details"),
        )


@dataclass
class GateSafetyReport:
    """Safety report for a gate."""
    report_id: str
    safe: bool
    safety_checks: list[SafetyCheck] = field(default_factory=list)
    gate_id: str | None = None
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "gate_id": self.gate_id,
            "safe": self.safe,
            "safety_checks": [c.to_dict() for c in self.safety_checks],
            "violations": self.violations,
            "warnings": self.warnings,
            "generated_at": self.generated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateSafetyReport":
        """Create from dictionary."""
        return cls(
            report_id=data["report_id"],
            gate_id=data.get("gate_id"),
            safe=data["safe"],
            safety_checks=[SafetyCheck.from_dict(c) for c in data.get("safety_checks", [])],
            violations=data.get("violations", []),
            warnings=data.get("warnings", []),
            generated_at=data.get("generated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )
