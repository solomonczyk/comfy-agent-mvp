"""Project-agnostic workflow registry and pipeline blueprint layer.

This module provides a universal, project-agnostic layer for describing
workflow contracts, pipeline blueprints, and reference pack schemas.
Future projects/episodes can connect via formal contracts instead of
hardcoded data.

Architecture:
    brief → blueprint → workflow registry → reference pack → gates → execution contract
"""

from app.workflow_registry.models import (
    WorkflowContract,
    PipelineBlueprint,
    WorkflowRegistry,
    ReferencePack,
    GateContract,
    ExecutionContract,
    OperatorReviewPacket,
)
from app.workflow_registry.loader import WorkflowRegistryLoader
from app.workflow_registry.validator import WorkflowRegistryValidator
from app.workflow_registry.blueprint_engine import BlueprintEngine
from app.workflow_registry.reference_pack_schema import ReferencePackSchema
from app.workflow_registry.registry_writer import RegistryWriter

__all__ = [
    "WorkflowContract",
    "PipelineBlueprint",
    "WorkflowRegistry",
    "ReferencePack",
    "GateContract",
    "ExecutionContract",
    "OperatorReviewPacket",
    "WorkflowRegistryLoader",
    "WorkflowRegistryValidator",
    "BlueprintEngine",
    "ReferencePackSchema",
    "RegistryWriter",
]
