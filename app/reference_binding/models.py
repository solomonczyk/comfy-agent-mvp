"""Data models for reference binding between blueprints and reference packs.

Project-agnostic models for binding pipeline stages to reference slots
with roles and readiness policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReferenceRole(str, Enum):
    """Roles that reference slots can play in the generation pipeline."""
    IDENTITY_REFERENCE = "identity_reference"
    STYLE_REFERENCE = "style_reference"
    CAMERA_REFERENCE = "camera_reference"
    LIGHTING_REFERENCE = "lighting_reference"
    ANATOMY_REFERENCE = "anatomy_reference"
    QUALITY_REFERENCE = "quality_reference"
    NEGATIVE_REFERENCE = "negative_reference"


class ReadinessPolicy(str, Enum):
    """Readiness policies for stages based on reference availability."""
    READY = "ready"
    PENDING_OPERATOR_SUPPLY = "pending_operator_supply"
    BLOCKED_MISSING_REQUIRED_REFERENCE = "blocked_missing_required_reference"
    BLOCKED_INVALID_REFERENCE_ROLE = "blocked_invalid_reference_role"


class SlotStatus(str, Enum):
    """Status of a reference slot."""
    SATISFIED = "satisfied"
    MISSING = "missing"
    INVALID_ROLE = "invalid_role"


@dataclass
class SlotRequirement:
    """Requirement for a reference slot in a stage."""
    slot_id: str
    slot_role: ReferenceRole
    required: bool = True
    gate_required_before_generation: bool = False
    blocker_if_missing: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slot_id": self.slot_id,
            "slot_role": self.slot_role.value,
            "required": self.required,
            "gate_required_before_generation": self.gate_required_before_generation,
            "blocker_if_missing": self.blocker_if_missing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SlotRequirement":
        """Create from dictionary."""
        return cls(
            slot_id=data["slot_id"],
            slot_role=ReferenceRole(data["slot_role"]),
            required=data.get("required", True),
            gate_required_before_generation=data.get("gate_required_before_generation", False),
            blocker_if_missing=data.get("blocker_if_missing", False),
        )


@dataclass
class StageBinding:
    """Binding of reference slots to a blueprint stage."""
    stage_id: str
    reference_slot_requirements: list[SlotRequirement] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_id": self.stage_id,
            "reference_slot_requirements": [
                req.to_dict() for req in self.reference_slot_requirements
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageBinding":
        """Create from dictionary."""
        return cls(
            stage_id=data["stage_id"],
            reference_slot_requirements=[
                SlotRequirement.from_dict(req)
                for req in data.get("reference_slot_requirements", [])
            ],
        )


@dataclass
class ReferenceBinding:
    """Binding between a pipeline blueprint and reference pack slots."""
    binding_id: str
    blueprint_id: str
    stage_bindings: list[StageBinding] = field(default_factory=list)
    readiness_policy: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "binding_id": self.binding_id,
            "blueprint_id": self.blueprint_id,
            "stage_bindings": [binding.to_dict() for binding in self.stage_bindings],
            "readiness_policy": self.readiness_policy,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceBinding":
        """Create from dictionary."""
        return cls(
            binding_id=data["binding_id"],
            blueprint_id=data["blueprint_id"],
            stage_bindings=[
                StageBinding.from_dict(b) for b in data.get("stage_bindings", [])
            ],
            readiness_policy=data.get("readiness_policy", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SlotStatusInfo:
    """Status information for a reference slot."""
    slot_id: str
    slot_role: ReferenceRole
    status: SlotStatus
    required: bool = True
    blocker: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slot_id": self.slot_id,
            "slot_role": self.slot_role.value,
            "status": self.status.value,
            "required": self.required,
            "blocker": self.blocker,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SlotStatusInfo":
        """Create from dictionary."""
        return cls(
            slot_id=data["slot_id"],
            slot_role=ReferenceRole(data["slot_role"]),
            status=SlotStatus(data["status"]),
            required=data.get("required", True),
            blocker=data.get("blocker", False),
        )


@dataclass
class StageReadiness:
    """Readiness information for a stage."""
    stage_id: str
    readiness_status: ReadinessPolicy
    slot_status: list[SlotStatusInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_id": self.stage_id,
            "readiness_status": self.readiness_status.value,
            "slot_status": [status.to_dict() for status in self.slot_status],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageReadiness":
        """Create from dictionary."""
        return cls(
            stage_id=data["stage_id"],
            readiness_status=ReadinessPolicy(data["readiness_status"]),
            slot_status=[
                SlotStatusInfo.from_dict(s) for s in data.get("slot_status", [])
            ],
        )


@dataclass
class GenerationGateStatus:
    """Status of the generation gate."""
    gate_open: bool = False
    blocking_slots: list[str] = field(default_factory=list)
    blocking_stages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_open": self.gate_open,
            "blocking_slots": self.blocking_slots,
            "blocking_stages": self.blocking_stages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GenerationGateStatus":
        """Create from dictionary."""
        return cls(
            gate_open=data.get("gate_open", False),
            blocking_slots=data.get("blocking_slots", []),
            blocking_stages=data.get("blocking_stages", []),
        )


@dataclass
class ReferenceReadiness:
    """Readiness matrix for reference binding."""
    readiness_id: str
    binding_id: str
    blueprint_id: str
    stage_readiness: list[StageReadiness] = field(default_factory=list)
    generation_gate_status: GenerationGateStatus = field(default_factory=GenerationGateStatus)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "readiness_id": self.readiness_id,
            "binding_id": self.binding_id,
            "blueprint_id": self.blueprint_id,
            "stage_readiness": [r.to_dict() for r in self.stage_readiness],
            "generation_gate_status": self.generation_gate_status.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceReadiness":
        """Create from dictionary."""
        return cls(
            readiness_id=data["readiness_id"],
            binding_id=data["binding_id"],
            blueprint_id=data["blueprint_id"],
            stage_readiness=[
                StageReadiness.from_dict(r) for r in data.get("stage_readiness", [])
            ],
            generation_gate_status=GenerationGateStatus.from_dict(
                data.get("generation_gate_status", {})
            ),
            metadata=data.get("metadata", {}),
        )
