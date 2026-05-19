"""Validator for workflow registry and related artifacts.

Provides validation functions to ensure workflow contracts,
pipeline blueprints, reference packs, and other registry artifacts
meet project-agnostic requirements and constraints.
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


class ValidationError(Exception):
    """Validation error with details."""

    def __init__(self, message: str, path: str | None = None):
        self.message = message
        self.path = path
        super().__init__(message)


class WorkflowRegistryValidator:
    """Validator for workflow registry artifacts."""

    # Forbidden patterns that indicate project-specific hardcoding
    FORBIDDEN_PATTERNS = [
        "rc2_multishot1_ep01",
        "rc2_multishot1",
        "data/rc2_multishot1",
        "output/rc2_multishot1",
        "/data/rc2",
        "\\data\\rc2",
    ]

    # Actions that must remain false in project-agnostic context
    FORBIDDEN_RUNTIME_ACTIONS = [
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
    ]

    @staticmethod
    def check_forbidden_patterns(data: Any, path: str = "") -> list[str]:
        """Check for forbidden patterns in data structure."""
        violations: list[str] = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                violations.extend(
                    WorkflowRegistryValidator.check_forbidden_patterns(value, current_path)
                )
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                violations.extend(
                    WorkflowRegistryValidator.check_forbidden_patterns(item, current_path)
                )
        elif isinstance(data, str):
            for pattern in WorkflowRegistryValidator.FORBIDDEN_PATTERNS:
                if pattern in data.lower():
                    violations.append(
                        f"Forbidden pattern '{pattern}' found at {path}: {data}"
                    )

        return violations

    @staticmethod
    def check_forbidden_runtime_actions(data: dict[str, Any]) -> list[str]:
        """Check that forbidden runtime actions are false or absent."""
        violations: list[str] = []

        for action in WorkflowRegistryValidator.FORBIDDEN_RUNTIME_ACTIONS:
            if action in data:
                value = data[action]
                if value is True:
                    violations.append(
                        f"Forbidden runtime action '{action}' is True at top level"
                    )

        return violations

    @staticmethod
    def validate_workflow_contract(
        contract: WorkflowContract,
    ) -> list[str]:
        """Validate a workflow contract."""
        errors: list[str] = []

        # Check required fields
        if not contract.workflow_id:
            errors.append("workflow_id is required")

        if not contract.workflow_type:
            errors.append("workflow_type is required")

        # Check project-agnostic flag
        if not contract.project_agnostic:
            errors.append("project_agnostic must be True for project-agnostic contracts")

        # Check for forbidden patterns
        contract_dict = contract.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            contract_dict
        )
        errors.extend(pattern_violations)

        return errors

    @staticmethod
    def validate_pipeline_blueprint(
        blueprint: PipelineBlueprint,
    ) -> list[str]:
        """Validate a pipeline blueprint."""
        errors: list[str] = []

        # Check required fields
        if not blueprint.blueprint_id:
            errors.append("blueprint_id is required")

        # Check for forbidden patterns
        blueprint_dict = blueprint.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            blueprint_dict
        )
        errors.extend(pattern_violations)

        # Validate stage order references
        stage_ids = {stage.stage_id for stage in blueprint.stages}
        for stage_id in blueprint.stage_order:
            if stage_id not in stage_ids:
                errors.append(
                    f"stage_order references unknown stage_id: {stage_id}"
                )

        return errors

    @staticmethod
    def validate_reference_pack(pack: ReferencePack) -> list[str]:
        """Validate a reference pack."""
        errors: list[str] = []

        # Check required fields
        if not pack.reference_pack_id:
            errors.append("reference_pack_id is required")

        # Check for forbidden patterns
        pack_dict = pack.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            pack_dict
        )
        errors.extend(pattern_violations)

        # Check usage policy - in project-agnostic context, should not require actual images
        if pack.usage_policy.get("require_actual_images", False):
            errors.append(
                "usage_policy.require_actual_images must be False in project-agnostic context"
            )

        # Reference pack should not require actual images in project-agnostic context
        # It should be able to describe image slots without requiring them
        for item in pack.items:
            if item.required and item.path is None:
                # This is OK - reference pack can describe slots without actual paths
                pass
            elif item.path:
                # Check that path is not absolute episode-specific path
                path_str = str(item.path)
                for pattern in WorkflowRegistryValidator.FORBIDDEN_PATTERNS:
                    if pattern in path_str.lower():
                        errors.append(
                            f"Reference item {item.reference_id} has forbidden path pattern: {path_str}"
                        )

        return errors

    @staticmethod
    def validate_gate_contract(gate: GateContract) -> list[str]:
        """Validate a gate contract."""
        errors: list[str] = []

        # Check required fields
        if not gate.gate_id:
            errors.append("gate_id is required")

        if not gate.gate_type:
            errors.append("gate_type is required")

        if not gate.required_state:
            errors.append("required_state is required")

        # Check for forbidden patterns
        gate_dict = gate.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            gate_dict
        )
        errors.extend(pattern_violations)

        return errors

    @staticmethod
    def validate_execution_contract(
        contract: ExecutionContract,
    ) -> list[str]:
        """Validate an execution contract."""
        errors: list[str] = []

        # Check required fields
        if not contract.execution_id:
            errors.append("execution_id is required")

        if not contract.workflow_id:
            errors.append("workflow_id is required")

        if not contract.blueprint_id:
            errors.append("blueprint_id is required")

        # Check dangerous actions are blocked
        if not contract.visual_qa_blocked:
            errors.append("visual_qa_blocked must be True in project-agnostic context")

        if not contract.assembly_blocked:
            errors.append("assembly_blocked must be True in project-agnostic context")

        if not contract.downstream_blocked:
            errors.append("downstream_blocked must be True in project-agnostic context")

        if contract.production_accepted:
            errors.append("production_accepted must be False in project-agnostic context")

        if contract.blind_retry_allowed:
            errors.append("blind_retry_allowed must be False in project-agnostic context")

        # Check for forbidden patterns
        contract_dict = contract.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            contract_dict
        )
        errors.extend(pattern_violations)

        return errors

    @staticmethod
    def validate_workflow_registry(
        registry: WorkflowRegistry,
    ) -> list[str]:
        """Validate a complete workflow registry."""
        errors: list[str] = []

        # Check required fields
        if not registry.registry_id:
            errors.append("registry_id is required")

        if not registry.version:
            errors.append("version is required")

        # Check for forbidden patterns
        registry_dict = registry.to_dict()
        pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(
            registry_dict
        )
        errors.extend(pattern_violations)

        # Validate all contained artifacts
        for contract_id, contract in registry.workflow_contracts.items():
            contract_errors = WorkflowRegistryValidator.validate_workflow_contract(
                contract
            )
            for err in contract_errors:
                errors.append(f"workflow_contract[{contract_id}]: {err}")

        for blueprint_id, blueprint in registry.pipeline_blueprints.items():
            blueprint_errors = WorkflowRegistryValidator.validate_pipeline_blueprint(
                blueprint
            )
            for err in blueprint_errors:
                errors.append(f"pipeline_blueprint[{blueprint_id}]: {err}")

        for pack_id, pack in registry.reference_packs.items():
            pack_errors = WorkflowRegistryValidator.validate_reference_pack(pack)
            for err in pack_errors:
                errors.append(f"reference_pack[{pack_id}]: {err}")

        for gate_id, gate in registry.gate_contracts.items():
            gate_errors = WorkflowRegistryValidator.validate_gate_contract(gate)
            for err in gate_errors:
                errors.append(f"gate_contract[{gate_id}]: {err}")

        for exec_id, contract in registry.execution_contracts.items():
            exec_errors = WorkflowRegistryValidator.validate_execution_contract(
                contract
            )
            for err in exec_errors:
                errors.append(f"execution_contract[{exec_id}]: {err}")

        return errors

    @staticmethod
    def validate_json_schema(
        data: dict[str, Any],
        schema_path: Path,
    ) -> list[str]:
        """Validate JSON data against a JSON schema file."""
        errors: list[str] = []

        if not schema_path.exists():
            errors.append(f"Schema file not found: {schema_path}")
            return errors

        try:
            schema = WorkflowRegistryLoader.load_json(schema_path)
            # Basic structural validation - in production would use jsonschema library
            # For now, we check that required fields exist based on schema
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
        except Exception as e:
            errors.append(f"Error loading schema: {e}")

        return errors

    @staticmethod
    def validate_file(
        file_path: Path,
        schema_path: Path | None = None,
    ) -> dict[str, Any]:
        """Validate a JSON file against optional schema and project-agnostic rules."""
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            data = WorkflowRegistryLoader.load_json(file_path)

            # Check for forbidden patterns
            pattern_violations = WorkflowRegistryValidator.check_forbidden_patterns(data)
            if pattern_violations:
                result["valid"] = False
                result["errors"].extend(pattern_violations)

            # Check for forbidden runtime actions
            action_violations = WorkflowRegistryValidator.check_forbidden_runtime_actions(
                data
            )
            if action_violations:
                result["valid"] = False
                result["errors"].extend(action_violations)

            # Validate against schema if provided
            if schema_path:
                schema_errors = WorkflowRegistryValidator.validate_json_schema(
                    data, schema_path
                )
                if schema_errors:
                    result["valid"] = False
                    result["errors"].extend(schema_errors)

        except FileNotFoundError as e:
            result["valid"] = False
            result["errors"].append(str(e))
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Validation error: {e}")

        return result


# Import loader for schema validation
from app.workflow_registry.loader import WorkflowRegistryLoader
