"""Loader for workflow registry and related artifacts.

Provides functions to load workflow contracts, pipeline blueprints,
reference packs, and other registry artifacts from JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.workflow_registry.models import (
    ExecutionContract,
    GateContract,
    PipelineBlueprint,
    ReferencePack,
    WorkflowContract,
    WorkflowRegistry,
)


class WorkflowRegistryLoader:
    """Loader for workflow registry artifacts."""

    @staticmethod
    def load_json(file_path: Path) -> dict[str, Any]:
        """Load a JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_workflow_contract(file_path: Path) -> WorkflowContract:
        """Load a workflow contract from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return WorkflowContract.from_dict(data)

    @staticmethod
    def load_pipeline_blueprint(file_path: Path) -> PipelineBlueprint:
        """Load a pipeline blueprint from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return PipelineBlueprint.from_dict(data)

    @staticmethod
    def load_reference_pack(file_path: Path) -> ReferencePack:
        """Load a reference pack from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return ReferencePack.from_dict(data)

    @staticmethod
    def load_gate_contract(file_path: Path) -> GateContract:
        """Load a gate contract from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return GateContract.from_dict(data)

    @staticmethod
    def load_execution_contract(file_path: Path) -> ExecutionContract:
        """Load an execution contract from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return ExecutionContract.from_dict(data)

    @staticmethod
    def load_workflow_registry(file_path: Path) -> WorkflowRegistry:
        """Load a complete workflow registry from JSON file."""
        data = WorkflowRegistryLoader.load_json(file_path)
        return WorkflowRegistry.from_dict(data)

    @staticmethod
    def load_registry_from_directory(
        registry_root: Path,
    ) -> WorkflowRegistry:
        """Load a workflow registry from a directory structure.

        Expected structure:
            registry_root/
                workflow_registry.json
                workflow_contracts/
                pipeline_blueprints/
                reference_packs/
                gate_contracts/
                execution_contracts/
        """
        registry_path = registry_root / "workflow_registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(
                f"Workflow registry not found: {registry_path}"
            )

        registry_data = WorkflowRegistryLoader.load_json(registry_path)
        registry = WorkflowRegistry.from_dict(registry_data)

        # Load individual artifacts from subdirectories
        contracts_dir = registry_root / "workflow_contracts"
        if contracts_dir.exists():
            for contract_file in contracts_dir.glob("*.json"):
                contract = WorkflowRegistryLoader.load_workflow_contract(contract_file)
                registry.workflow_contracts[contract.workflow_id] = contract

        blueprints_dir = registry_root / "pipeline_blueprints"
        if blueprints_dir.exists():
            for blueprint_file in blueprints_dir.glob("*.json"):
                blueprint = WorkflowRegistryLoader.load_pipeline_blueprint(blueprint_file)
                registry.pipeline_blueprints[blueprint.blueprint_id] = blueprint

        reference_packs_dir = registry_root / "reference_packs"
        if reference_packs_dir.exists():
            for pack_file in reference_packs_dir.glob("*.json"):
                pack = WorkflowRegistryLoader.load_reference_pack(pack_file)
                registry.reference_packs[pack.reference_pack_id] = pack

        gate_contracts_dir = registry_root / "gate_contracts"
        if gate_contracts_dir.exists():
            for gate_file in gate_contracts_dir.glob("*.json"):
                gate = WorkflowRegistryLoader.load_gate_contract(gate_file)
                registry.gate_contracts[gate.gate_id] = gate

        execution_contracts_dir = registry_root / "execution_contracts"
        if execution_contracts_dir.exists():
            for exec_file in execution_contracts_dir.glob("*.json"):
                exec_contract = WorkflowRegistryLoader.load_execution_contract(exec_file)
                registry.execution_contracts[exec_contract.execution_id] = exec_contract

        return registry
