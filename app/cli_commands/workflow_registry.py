"""CLI commands for workflow registry and pipeline blueprint validation.

Task: RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.workflow_registry.models import (
    ExecutionContract,
    GateContract,
    PipelineBlueprint,
    ReferencePack,
    ReferenceType,
    WorkflowContract,
    WorkflowRegistry,
    WorkflowType,
)
from app.workflow_registry.reference_pack_schema import ReferencePackSchema
from app.workflow_registry.registry_writer import RegistryWriter
from app.workflow_registry.validator import WorkflowRegistryValidator
from app.workflow_registry.loader import WorkflowRegistryLoader


def init_workflow_registry(args: argparse.Namespace) -> int:
    """Initialize a new workflow registry."""
    registry_root = Path(args.registry_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    # Create registry structure
    registry_root.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (registry_root / "workflow_contracts").mkdir(exist_ok=True)
    (registry_root / "pipeline_blueprints").mkdir(exist_ok=True)
    (registry_root / "reference_packs").mkdir(exist_ok=True)
    (registry_root / "gate_contracts").mkdir(exist_ok=True)
    (registry_root / "execution_contracts").mkdir(exist_ok=True)

    # Create empty registry
    registry = WorkflowRegistry(
        registry_id=args.registry_id or "default_registry",
        version="1.0.0",
        metadata={
            "created": timestamp,
            "description": "Project-agnostic workflow registry",
            "project_binding_required": False,
        },
    )

    # Write registry
    RegistryWriter.write_registry_to_directory(registry_root, registry)

    result = {
        "status": "ok",
        "action": "workflow_registry_initialized",
        "registry_root": str(registry_root),
        "registry_id": registry.registry_id,
        "version": registry.version,
        "timestamp": timestamp,
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Workflow registry initialized at: {registry_root}")
        print(f"Registry ID: {registry.registry_id}")
        print(f"Version: {registry.version}")

    return 0


def validate_workflow_registry(args: argparse.Namespace) -> int:
    """Validate a workflow registry."""
    registry_root = Path(args.registry_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        registry = WorkflowRegistryLoader.load_registry_from_directory(registry_root)
        errors = WorkflowRegistryValidator.validate_workflow_registry(registry)

        result = {
            "status": "ok" if not errors else "error",
            "action": "workflow_registry_validated",
            "registry_root": str(registry_root),
            "registry_id": registry.registry_id,
            "version": registry.version,
            "valid": len(errors) == 0,
            "errors": errors,
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            if errors:
                print(f"Validation failed with {len(errors)} error(s):")
                for err in errors:
                    print(f"  - {err}")
            else:
                print(f"Registry valid: {registry.registry_id} v{registry.version}")

        return 0 if not errors else 1

    except Exception as e:
        result = {
            "status": "error",
            "action": "workflow_registry_validated",
            "registry_root": str(registry_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def inspect_workflow_registry(args: argparse.Namespace) -> int:
    """Inspect a workflow registry and print its contents."""
    registry_root = Path(args.registry_root)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        registry = WorkflowRegistryLoader.load_registry_from_directory(registry_root)

        result = {
            "status": "ok",
            "action": "workflow_registry_inspected",
            "registry_root": str(registry_root),
            "registry_id": registry.registry_id,
            "version": registry.version,
            "workflow_contracts_count": len(registry.workflow_contracts),
            "pipeline_blueprints_count": len(registry.pipeline_blueprints),
            "reference_packs_count": len(registry.reference_packs),
            "gate_contracts_count": len(registry.gate_contracts),
            "execution_contracts_count": len(registry.execution_contracts),
            "workflow_contracts": list(registry.workflow_contracts.keys()),
            "pipeline_blueprints": list(registry.pipeline_blueprints.keys()),
            "reference_packs": list(registry.reference_packs.keys()),
            "gate_contracts": list(registry.gate_contracts.keys()),
            "execution_contracts": list(registry.execution_contracts.keys()),
            "metadata": registry.metadata,
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Registry: {registry.registry_id} v{registry.version}")
            print(f"  Workflow Contracts: {len(registry.workflow_contracts)}")
            for wc_id in registry.workflow_contracts:
                print(f"    - {wc_id}")
            print(f"  Pipeline Blueprints: {len(registry.pipeline_blueprints)}")
            for pb_id in registry.pipeline_blueprints:
                print(f"    - {pb_id}")
            print(f"  Reference Packs: {len(registry.reference_packs)}")
            for rp_id in registry.reference_packs:
                print(f"    - {rp_id}")
            print(f"  Gate Contracts: {len(registry.gate_contracts)}")
            for gc_id in registry.gate_contracts:
                print(f"    - {gc_id}")
            print(f"  Execution Contracts: {len(registry.execution_contracts)}")
            for ec_id in registry.execution_contracts:
                print(f"    - {ec_id}")

        return 0

    except Exception as e:
        result = {
            "status": "error",
            "action": "workflow_registry_inspected",
            "registry_root": str(registry_root),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def validate_pipeline_blueprint(args: argparse.Namespace) -> int:
    """Validate a pipeline blueprint file."""
    blueprint_path = Path(args.blueprint)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        validation_result = WorkflowRegistryValidator.validate_file(blueprint_path)

        # Additional blueprint-specific validation
        if validation_result["valid"]:
            blueprint = WorkflowRegistryLoader.load_pipeline_blueprint(blueprint_path)
            blueprint_errors = WorkflowRegistryValidator.validate_pipeline_blueprint(blueprint)
            if blueprint_errors:
                validation_result["valid"] = False
                validation_result["errors"].extend(blueprint_errors)

        result = {
            "status": "ok" if validation_result["valid"] else "error",
            "action": "pipeline_blueprint_validated",
            "blueprint_path": str(blueprint_path),
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            if validation_result["errors"]:
                print(f"Validation failed:")
                for err in validation_result["errors"]:
                    print(f"  - {err}")
            else:
                print(f"Blueprint valid: {blueprint_path}")

        return 0 if validation_result["valid"] else 1

    except Exception as e:
        result = {
            "status": "error",
            "action": "pipeline_blueprint_validated",
            "blueprint_path": str(blueprint_path),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1


def validate_reference_pack(args: argparse.Namespace) -> int:
    """Validate a reference pack file."""
    reference_pack_path = Path(args.reference_pack)
    json_output = args.json
    timestamp = datetime.now().isoformat()

    try:
        validation_result = WorkflowRegistryValidator.validate_file(reference_pack_path)

        # Additional reference pack-specific validation
        if validation_result["valid"]:
            pack = WorkflowRegistryLoader.load_reference_pack(reference_pack_path)
            pack_errors = WorkflowRegistryValidator.validate_reference_pack(pack)
            if pack_errors:
                validation_result["valid"] = False
                validation_result["errors"].extend(pack_errors)

            # Check slot compatibility
            slot_errors = ReferencePackSchema.validate_pack_slot_compatibility(pack)
            if slot_errors:
                validation_result["valid"] = False
                validation_result["errors"].extend(slot_errors)

        result = {
            "status": "ok" if validation_result["valid"] else "error",
            "action": "reference_pack_validated",
            "reference_pack_path": str(reference_pack_path),
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "timestamp": timestamp,
        }

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            if validation_result["errors"]:
                print(f"Validation failed:")
                for err in validation_result["errors"]:
                    print(f"  - {err}")
            else:
                print(f"Reference pack valid: {reference_pack_path}")

        return 0 if validation_result["valid"] else 1

    except Exception as e:
        result = {
            "status": "error",
            "action": "reference_pack_validated",
            "reference_pack_path": str(reference_pack_path),
            "error": str(e),
            "timestamp": timestamp,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {e}")
        return 1
