"""Data models for workflow registry and pipeline blueprints.

Project-agnostic models that can be reused across different projects/episodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowType(str, Enum):
    """Types of workflows supported by the registry."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    EDITORIAL = "editorial"
    QA = "qa"
    ASSEMBLY = "assembly"
    CUSTOM = "custom"


class ReferenceType(str, Enum):
    """Types of reference assets supported in reference packs."""
    STYLE = "style"
    CHARACTER = "character"
    LOCATION = "location"
    CAMERA = "camera"
    LIGHTING = "lighting"
    QUALITY = "quality"
    NEGATIVE = "negative"
    MOTION = "motion"
    VOICE = "voice"
    EDITORIAL = "editorial"


@dataclass
class WorkflowContract:
    """Contract defining a workflow's inputs, outputs, and constraints."""
    workflow_id: str
    workflow_type: WorkflowType
    project_agnostic: bool = True
    required_inputs: list[str] = field(default_factory=list)
    optional_inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    required_gates: list[str] = field(default_factory=list)
    execution_allowed_by_default: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "project_agnostic": self.project_agnostic,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "outputs": self.outputs,
            "forbidden_actions": self.forbidden_actions,
            "required_gates": self.required_gates,
            "execution_allowed_by_default": self.execution_allowed_by_default,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowContract":
        """Create from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            workflow_type=WorkflowType(data["workflow_type"]),
            project_agnostic=data.get("project_agnostic", True),
            required_inputs=data.get("required_inputs", []),
            optional_inputs=data.get("optional_inputs", []),
            outputs=data.get("outputs", []),
            forbidden_actions=data.get("forbidden_actions", []),
            required_gates=data.get("required_gates", []),
            execution_allowed_by_default=data.get("execution_allowed_by_default", False),
        )


@dataclass
class PipelineStage:
    """A stage in a pipeline blueprint."""
    stage_id: str
    stage_name: str
    stage_type: str
    required_artifacts: list[str] = field(default_factory=list)
    optional_artifacts: list[str] = field(default_factory=list)
    gate_required: bool = False
    operator_review_point: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "stage_type": self.stage_type,
            "required_artifacts": self.required_artifacts,
            "optional_artifacts": self.optional_artifacts,
            "gate_required": self.gate_required,
            "operator_review_point": self.operator_review_point,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineStage":
        """Create from dictionary."""
        return cls(
            stage_id=data["stage_id"],
            stage_name=data["stage_name"],
            stage_type=data["stage_type"],
            required_artifacts=data.get("required_artifacts", []),
            optional_artifacts=data.get("optional_artifacts", []),
            gate_required=data.get("gate_required", False),
            operator_review_point=data.get("operator_review_point", False),
        )


@dataclass
class StateTransition:
    """A state transition in a pipeline."""
    from_state: str
    to_state: str
    trigger_action: str
    gate_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "trigger_action": self.trigger_action,
            "gate_required": self.gate_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateTransition":
        """Create from dictionary."""
        return cls(
            from_state=data["from_state"],
            to_state=data["to_state"],
            trigger_action=data["trigger_action"],
            gate_required=data.get("gate_required", False),
        )


@dataclass
class PipelineBlueprint:
    """Blueprint defining pipeline stages, transitions, and review points."""
    blueprint_id: str
    stages: list[PipelineStage] = field(default_factory=list)
    stage_order: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    state_transitions: list[StateTransition] = field(default_factory=list)
    operator_review_points: list[str] = field(default_factory=list)
    dangerous_action_gates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "blueprint_id": self.blueprint_id,
            "stages": [s.to_dict() for s in self.stages],
            "stage_order": self.stage_order,
            "required_artifacts": self.required_artifacts,
            "state_transitions": [t.to_dict() for t in self.state_transitions],
            "operator_review_points": self.operator_review_points,
            "dangerous_action_gates": self.dangerous_action_gates,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineBlueprint":
        """Create from dictionary."""
        return cls(
            blueprint_id=data["blueprint_id"],
            stages=[PipelineStage.from_dict(s) for s in data.get("stages", [])],
            stage_order=data.get("stage_order", []),
            required_artifacts=data.get("required_artifacts", []),
            state_transitions=[StateTransition.from_dict(t) for t in data.get("state_transitions", [])],
            operator_review_points=data.get("operator_review_points", []),
            dangerous_action_gates=data.get("dangerous_action_gates", []),
        )


@dataclass
class ReferenceItem:
    """A reference item in a reference pack."""
    reference_id: str
    reference_type: ReferenceType
    description: str
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type.value,
            "description": self.description,
            "path": self.path,
            "metadata": self.metadata,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceItem":
        """Create from dictionary."""
        return cls(
            reference_id=data["reference_id"],
            reference_type=ReferenceType(data["reference_type"]),
            description=data["description"],
            path=data.get("path"),
            metadata=data.get("metadata", {}),
            required=data.get("required", True),
        )


@dataclass
class ReferencePack:
    """Collection of reference assets for a project/episode."""
    reference_pack_id: str
    project_binding_required: bool = False
    reference_types: list[ReferenceType] = field(default_factory=list)
    items: list[ReferenceItem] = field(default_factory=list)
    usage_policy: dict[str, Any] = field(default_factory=dict)
    operator_review_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reference_pack_id": self.reference_pack_id,
            "project_binding_required": self.project_binding_required,
            "reference_types": [rt.value for rt in self.reference_types],
            "items": [item.to_dict() for item in self.items],
            "usage_policy": self.usage_policy,
            "operator_review_required": self.operator_review_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferencePack":
        """Create from dictionary."""
        return cls(
            reference_pack_id=data["reference_pack_id"],
            project_binding_required=data.get("project_binding_required", False),
            reference_types=[ReferenceType(rt) for rt in data.get("reference_types", [])],
            items=[ReferenceItem.from_dict(item) for item in data.get("items", [])],
            usage_policy=data.get("usage_policy", {}),
            operator_review_required=data.get("operator_review_required", True),
        )


@dataclass
class GateContract:
    """Contract defining a gate's conditions and constraints."""
    gate_id: str
    gate_type: str
    required_state: str
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    operator_approval_required: bool = False
    max_attempts: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "required_state": self.required_state,
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
            "operator_approval_required": self.operator_approval_required,
            "max_attempts": self.max_attempts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateContract":
        """Create from dictionary."""
        return cls(
            gate_id=data["gate_id"],
            gate_type=data["gate_type"],
            required_state=data["required_state"],
            allowed_actions=data.get("allowed_actions", []),
            forbidden_actions=data.get("forbidden_actions", []),
            operator_approval_required=data.get("operator_approval_required", False),
            max_attempts=data.get("max_attempts"),
        )


@dataclass
class ExecutionContract:
    """Contract defining execution constraints for a workflow."""
    execution_id: str
    workflow_id: str
    blueprint_id: str
    max_generations: int = 1
    stop_after_generation: bool = True
    blind_retry_allowed: bool = False
    visual_qa_blocked: bool = True
    assembly_blocked: bool = True
    downstream_blocked: bool = True
    production_accepted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "blueprint_id": self.blueprint_id,
            "max_generations": self.max_generations,
            "stop_after_generation": self.stop_after_generation,
            "blind_retry_allowed": self.blind_retry_allowed,
            "visual_qa_blocked": self.visual_qa_blocked,
            "assembly_blocked": self.assembly_blocked,
            "downstream_blocked": self.downstream_blocked,
            "production_accepted": self.production_accepted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContract":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            blueprint_id=data["blueprint_id"],
            max_generations=data.get("max_generations", 1),
            stop_after_generation=data.get("stop_after_generation", True),
            blind_retry_allowed=data.get("blind_retry_allowed", False),
            visual_qa_blocked=data.get("visual_qa_blocked", True),
            assembly_blocked=data.get("assembly_blocked", True),
            downstream_blocked=data.get("downstream_blocked", True),
            production_accepted=data.get("production_accepted", False),
        )


@dataclass
class OperatorReviewPacket:
    """Packet for operator review at decision points."""
    packet_id: str
    review_point: str
    candidate_assets: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    decision_options: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    production_accepted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "packet_id": self.packet_id,
            "review_point": self.review_point,
            "candidate_assets": self.candidate_assets,
            "context": self.context,
            "decision_options": self.decision_options,
            "constraints": self.constraints,
            "production_accepted": self.production_accepted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperatorReviewPacket":
        """Create from dictionary."""
        return cls(
            packet_id=data["packet_id"],
            review_point=data["review_point"],
            candidate_assets=data.get("candidate_assets", []),
            context=data.get("context", {}),
            decision_options=data.get("decision_options", []),
            constraints=data.get("constraints", {}),
            production_accepted=data.get("production_accepted", False),
        )


@dataclass
class WorkflowRegistry:
    """Registry containing all workflow contracts, blueprints, and reference packs."""
    registry_id: str
    version: str
    workflow_contracts: dict[str, WorkflowContract] = field(default_factory=dict)
    pipeline_blueprints: dict[str, PipelineBlueprint] = field(default_factory=dict)
    reference_packs: dict[str, ReferencePack] = field(default_factory=dict)
    gate_contracts: dict[str, GateContract] = field(default_factory=dict)
    execution_contracts: dict[str, ExecutionContract] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "workflow_contracts": {
                k: v.to_dict() for k, v in self.workflow_contracts.items()
            },
            "pipeline_blueprints": {
                k: v.to_dict() for k, v in self.pipeline_blueprints.items()
            },
            "reference_packs": {
                k: v.to_dict() for k, v in self.reference_packs.items()
            },
            "gate_contracts": {
                k: v.to_dict() for k, v in self.gate_contracts.items()
            },
            "execution_contracts": {
                k: v.to_dict() for k, v in self.execution_contracts.items()
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowRegistry":
        """Create from dictionary."""
        return cls(
            registry_id=data["registry_id"],
            version=data["version"],
            workflow_contracts={
                k: WorkflowContract.from_dict(v)
                for k, v in data.get("workflow_contracts", {}).items()
            },
            pipeline_blueprints={
                k: PipelineBlueprint.from_dict(v)
                for k, v in data.get("pipeline_blueprints", {}).items()
            },
            reference_packs={
                k: ReferencePack.from_dict(v)
                for k, v in data.get("reference_packs", {}).items()
            },
            gate_contracts={
                k: GateContract.from_dict(v)
                for k, v in data.get("gate_contracts", {}).items()
            },
            execution_contracts={
                k: ExecutionContract.from_dict(v)
                for k, v in data.get("execution_contracts", {}).items()
            },
            metadata=data.get("metadata", {}),
        )
