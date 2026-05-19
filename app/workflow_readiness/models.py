"""Data models for workflow readiness orchestration.

Project-agnostic models for workflow readiness evaluation and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ReadinessStatus(str, Enum):
    """Overall readiness status for workflow execution."""
    READY_FOR_OPERATOR_GENERATION_AUTHORIZATION = "ready_for_operator_generation_authorization"
    PENDING_OPERATOR_REFERENCE_SUPPLY = "pending_operator_reference_supply"
    BLOCKED_MISSING_REQUIRED_REFERENCE = "blocked_missing_required_reference"
    BLOCKED_INVALID_REFERENCE_BINDING = "blocked_invalid_reference_binding"
    BLOCKED_INVALID_WORKFLOW_CONTRACT = "blocked_invalid_workflow_contract"
    BLOCKED_FORBIDDEN_RUNTIME_ACTION = "blocked_forbidden_runtime_action"
    BLOCKED_PROJECT_SPECIFIC_HARDCODING = "blocked_project_specific_hardcoding"


@dataclass
class WorkflowReadinessManifest:
    """Manifest for workflow readiness evaluation."""
    task_id: str
    document_type: str = "workflow_readiness_manifest"
    version: str = "1.0.0"
    project_agnostic: bool = True
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    evaluation_scope: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "document_type": self.document_type,
            "version": self.version,
            "project_agnostic": self.project_agnostic,
            "created": self.created,
            "evaluation_scope": self.evaluation_scope,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowReadinessManifest":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            document_type=data.get("document_type", "workflow_readiness_manifest"),
            version=data.get("version", "1.0.0"),
            project_agnostic=data.get("project_agnostic", True),
            created=data.get("created", datetime.utcnow().isoformat()),
            evaluation_scope=data.get("evaluation_scope", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ComponentReadiness:
    """Readiness status for a single component."""
    component_type: str
    component_id: str
    is_valid: bool
    is_present: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component_type": self.component_type,
            "component_id": self.component_id,
            "is_valid": self.is_valid,
            "is_present": self.is_present,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentReadiness":
        """Create from dictionary."""
        return cls(
            component_type=data["component_type"],
            component_id=data["component_id"],
            is_valid=data["is_valid"],
            is_present=data["is_present"],
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CombinedReadinessReport:
    """Combined readiness report for all workflow components."""
    report_id: str
    overall_status: ReadinessStatus
    generation_authorized: bool = False
    generation_gate_required: bool = True
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    component_readiness: dict[str, ComponentReadiness] = field(default_factory=dict)
    missing_references: list[str] = field(default_factory=list)
    invalid_bindings: list[str] = field(default_factory=list)
    forbidden_actions_detected: list[str] = field(default_factory=list)
    hardcoded_paths_detected: list[str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "overall_status": self.overall_status.value,
            "generation_authorized": self.generation_authorized,
            "generation_gate_required": self.generation_gate_required,
            "evaluated_at": self.evaluated_at,
            "component_readiness": {
                k: v.to_dict() for k, v in self.component_readiness.items()
            },
            "missing_references": self.missing_references,
            "invalid_bindings": self.invalid_bindings,
            "forbidden_actions_detected": self.forbidden_actions_detected,
            "hardcoded_paths_detected": self.hardcoded_paths_detected,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CombinedReadinessReport":
        """Create from dictionary."""
        return cls(
            report_id=data["report_id"],
            overall_status=ReadinessStatus(data["overall_status"]),
            generation_authorized=data.get("generation_authorized", False),
            generation_gate_required=data.get("generation_gate_required", True),
            evaluated_at=data.get("evaluated_at", datetime.utcnow().isoformat()),
            component_readiness={
                k: ComponentReadiness.from_dict(v)
                for k, v in data.get("component_readiness", {}).items()
            },
            missing_references=data.get("missing_references", []),
            invalid_bindings=data.get("invalid_bindings", []),
            forbidden_actions_detected=data.get("forbidden_actions_detected", []),
            hardcoded_paths_detected=data.get("hardcoded_paths_detected", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GenerationGateRequirementReport:
    """Report on generation gate requirements."""
    report_id: str
    gate_required: bool = True
    gate_status: str = "closed"
    gate_reason: str = "generation_requires_operator_authorization"
    blocking_components: list[str] = field(default_factory=list)
    authorization_path: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "gate_required": self.gate_required,
            "gate_status": self.gate_status,
            "gate_reason": self.gate_reason,
            "blocking_components": self.blocking_components,
            "authorization_path": self.authorization_path,
            "generated_at": self.generated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GenerationGateRequirementReport":
        """Create from dictionary."""
        return cls(
            report_id=data["report_id"],
            gate_required=data.get("gate_required", True),
            gate_status=data.get("gate_status", "closed"),
            gate_reason=data.get("gate_reason", "generation_requires_operator_authorization"),
            blocking_components=data.get("blocking_components", []),
            authorization_path=data.get("authorization_path", []),
            generated_at=data.get("generated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class BlockerReport:
    """Report on blockers preventing workflow execution."""
    report_id: str
    has_blockers: bool = False
    blocker_type: str | None = None
    blocker_details: dict[str, Any] = field(default_factory=dict)
    resolution_actions: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "has_blockers": self.has_blockers,
            "blocker_type": self.blocker_type,
            "blocker_details": self.blocker_details,
            "resolution_actions": self.resolution_actions,
            "generated_at": self.generated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlockerReport":
        """Create from dictionary."""
        return cls(
            report_id=data["report_id"],
            has_blockers=data.get("has_blockers", False),
            blocker_type=data.get("blocker_type"),
            blocker_details=data.get("blocker_details", {}),
            resolution_actions=data.get("resolution_actions", []),
            generated_at=data.get("generated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )
