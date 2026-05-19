"""Writer for workflow registry and related artifacts.

Provides functions to write workflow contracts, pipeline blueprints,
reference packs, and other registry artifacts to JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.workflow_registry.models import (
    ExecutionContract,
    GateContract,
    OperatorReviewPacket,
    PipelineBlueprint,
    ReferencePack,
    WorkflowContract,
    WorkflowRegistry,
)


class RegistryWriter:
    """Writer for workflow registry artifacts."""

    @staticmethod
    def write_json(
        file_path: Path,
        data: dict[str, Any],
        indent: int = 2,
    ) -> None:
        """Write data to a JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def write_workflow_contract(
        file_path: Path,
        contract: WorkflowContract,
    ) -> None:
        """Write a workflow contract to JSON file."""
        RegistryWriter.write_json(file_path, contract.to_dict())

    @staticmethod
    def write_pipeline_blueprint(
        file_path: Path,
        blueprint: PipelineBlueprint,
    ) -> None:
        """Write a pipeline blueprint to JSON file."""
        RegistryWriter.write_json(file_path, blueprint.to_dict())

    @staticmethod
    def write_reference_pack(
        file_path: Path,
        pack: ReferencePack,
    ) -> None:
        """Write a reference pack to JSON file."""
        RegistryWriter.write_json(file_path, pack.to_dict())

    @staticmethod
    def write_gate_contract(
        file_path: Path,
        gate: GateContract,
    ) -> None:
        """Write a gate contract to JSON file."""
        RegistryWriter.write_json(file_path, gate.to_dict())

    @staticmethod
    def write_execution_contract(
        file_path: Path,
        contract: ExecutionContract,
    ) -> None:
        """Write an execution contract to JSON file."""
        RegistryWriter.write_json(file_path, contract.to_dict())

    @staticmethod
    def write_operator_review_packet(
        file_path: Path,
        packet: OperatorReviewPacket,
    ) -> None:
        """Write an operator review packet to JSON file."""
        RegistryWriter.write_json(file_path, packet.to_dict())

    @staticmethod
    def write_workflow_registry(
        file_path: Path,
        registry: WorkflowRegistry,
    ) -> None:
        """Write a complete workflow registry to JSON file."""
        RegistryWriter.write_json(file_path, registry.to_dict())

    @staticmethod
    def write_registry_to_directory(
        registry_root: Path,
        registry: WorkflowRegistry,
        write_individual_artifacts: bool = True,
    ) -> None:
        """Write a workflow registry to a directory structure.

        Creates:
            registry_root/
                workflow_registry.json
                workflow_contracts/
                pipeline_blueprints/
                reference_packs/
                gate_contracts/
                execution_contracts/
        """
        registry_root.mkdir(parents=True, exist_ok=True)

        # Write main registry file
        registry_path = registry_root / "workflow_registry.json"
        RegistryWriter.write_workflow_registry(registry_path, registry)

        if write_individual_artifacts:
            # Write individual artifacts to subdirectories
            contracts_dir = registry_root / "workflow_contracts"
            contracts_dir.mkdir(exist_ok=True)

            for contract_id, contract in registry.workflow_contracts.items():
                contract_path = contracts_dir / f"{contract_id}.json"
                RegistryWriter.write_workflow_contract(contract_path, contract)

            blueprints_dir = registry_root / "pipeline_blueprints"
            blueprints_dir.mkdir(exist_ok=True)

            for blueprint_id, blueprint in registry.pipeline_blueprints.items():
                blueprint_path = blueprints_dir / f"{blueprint_id}.json"
                RegistryWriter.write_pipeline_blueprint(blueprint_path, blueprint)

            reference_packs_dir = registry_root / "reference_packs"
            reference_packs_dir.mkdir(exist_ok=True)

            for pack_id, pack in registry.reference_packs.items():
                pack_path = reference_packs_dir / f"{pack_id}.json"
                RegistryWriter.write_reference_pack(pack_path, pack)

            gate_contracts_dir = registry_root / "gate_contracts"
            gate_contracts_dir.mkdir(exist_ok=True)

            for gate_id, gate in registry.gate_contracts.items():
                gate_path = gate_contracts_dir / f"{gate_id}.json"
                RegistryWriter.write_gate_contract(gate_path, gate)

            execution_contracts_dir = registry_root / "execution_contracts"
            execution_contracts_dir.mkdir(exist_ok=True)

            for exec_id, contract in registry.execution_contracts.items():
                exec_path = execution_contracts_dir / f"{exec_id}.json"
                RegistryWriter.write_execution_contract(exec_path, contract)

    @staticmethod
    def write_validation_report(
        file_path: Path,
        validation_result: dict[str, Any],
    ) -> None:
        """Write a validation report to JSON file."""
        RegistryWriter.write_json(file_path, validation_result)

    @staticmethod
    def write_forbidden_actions_report(
        file_path: Path,
        forbidden_actions: list[str],
    ) -> None:
        """Write a forbidden actions report to JSON file."""
        report = {
            "task_id": "RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001",
            "document_type": "forbidden_actions_report",
            "forbidden_actions_checked": [
                "generation_performed",
                "retry_attempted",
                "comfyui_submit_executed",
                "preview_render_executed",
                "visual_qa_acceptance_executed",
                "operator_visual_acceptance_executed",
                "voice_generation_executed",
                "assembly_executed",
                "downstream_executed",
                "production_accepted",
            ],
            "forbidden_actions_found": forbidden_actions,
            "all_forbidden_actions_false": len(forbidden_actions) == 0,
        }
        RegistryWriter.write_json(file_path, report)
