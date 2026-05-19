"""Engine for workflow readiness evaluation.

Project-agnostic preflight engine that evaluates workflow readiness
before any runtime action. This engine does NOT execute generation,
retry, or any downstream operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.reference_binding.binding_engine import ReferenceBindingEngine
from app.reference_binding.models import ReferenceBinding
from app.workflow_registry.loader import WorkflowRegistryLoader
from app.workflow_registry.models import (
    ExecutionContract,
    PipelineBlueprint,
    ReferencePack,
    WorkflowContract,
    WorkflowRegistry,
)
from app.workflow_readiness.models import (
    BlockerReport,
    CombinedReadinessReport,
    ComponentReadiness,
    GenerationGateRequirementReport,
    ReadinessStatus,
    WorkflowReadinessManifest,
)


class WorkflowReadinessEngine:
    """Engine for evaluating workflow readiness."""

    # Forbidden runtime actions that should block execution
    FORBIDDEN_ACTIONS = [
        "generation",
        "retry",
        "comfyui_submit",
        "preview_render",
        "image_editing",
        "upscale",
        "visual_qa_acceptance",
        "operator_visual_acceptance",
        "assembly",
        "downstream",
        "production_acceptance",
        "hidden_downloads",
        "api_calls",
        "force_push",
        "destructive_git",
        "runtime_state_mutation",
    ]

    # Hardcoded project-specific paths that should block execution
    HARDCODED_PROJECT_PATTERNS = [
        "rc2_multishot1_ep01",
        "rc2_",
        "/data/rc2/",
        "/data/episodes/",
    ]

    @staticmethod
    def evaluate_readiness(
        workflow_registry_path: Path,
        pipeline_blueprint_id: str,
        reference_pack_id: str,
        reference_binding_path: Path,
        reference_set_report_path: Path | None = None,
    ) -> CombinedReadinessReport:
        """Evaluate workflow readiness for all components.

        Args:
            workflow_registry_path: Path to workflow registry JSON
            pipeline_blueprint_id: ID of pipeline blueprint to evaluate
            reference_pack_id: ID of reference pack to evaluate
            reference_binding_path: Path to reference binding JSON
            reference_set_report_path: Optional path to reference set dropzone report

        Returns:
            CombinedReadinessReport with overall readiness status
        """
        report_id = f"readiness_{pipeline_blueprint_id}_{reference_pack_id}"
        component_readiness: dict[str, ComponentReadiness] = {}
        missing_references: list[str] = []
        invalid_bindings: list[str] = []
        forbidden_actions_detected: list[str] = []
        hardcoded_paths_detected: dict[str, list[str]] = {}

        # Load and evaluate workflow registry
        try:
            registry = WorkflowRegistryLoader.load_workflow_registry(workflow_registry_path)
            registry_readiness = ComponentReadiness(
                component_type="workflow_registry",
                component_id=registry.registry_id,
                is_valid=True,
                is_present=True,
                metadata={"version": registry.version},
            )
            component_readiness["workflow_registry"] = registry_readiness
        except Exception as e:
            registry_readiness = ComponentReadiness(
                component_type="workflow_registry",
                component_id="unknown",
                is_valid=False,
                is_present=False,
                errors=[str(e)],
            )
            component_readiness["workflow_registry"] = registry_readiness

        # Load and evaluate pipeline blueprint
        try:
            blueprint = WorkflowRegistryLoader.load_pipeline_blueprint(
                workflow_registry_path.parent / "pipeline_blueprints" / f"{pipeline_blueprint_id}.json"
            )
            blueprint_readiness = ComponentReadiness(
                component_type="pipeline_blueprint",
                component_id=blueprint.blueprint_id,
                is_valid=True,
                is_present=True,
                metadata={"stages": len(blueprint.stages)},
            )
            component_readiness["pipeline_blueprint"] = blueprint_readiness

            # Check for hardcoded project paths in blueprint
            blueprint_dict = blueprint.to_dict()
            blueprint_str = json.dumps(blueprint_dict, default=str)
            for pattern in WorkflowReadinessEngine.HARDCODED_PROJECT_PATTERNS:
                if pattern in blueprint_str:
                    if pattern not in hardcoded_paths_detected:
                        hardcoded_paths_detected[pattern] = []
                    hardcoded_paths_detected[pattern].append("pipeline_blueprint")
        except Exception as e:
            blueprint_readiness = ComponentReadiness(
                component_type="pipeline_blueprint",
                component_id=pipeline_blueprint_id,
                is_valid=False,
                is_present=False,
                errors=[str(e)],
            )
            component_readiness["pipeline_blueprint"] = blueprint_readiness

        # Load and evaluate reference pack
        try:
            reference_pack = WorkflowRegistryLoader.load_reference_pack(
                workflow_registry_path.parent / "reference_packs" / f"{reference_pack_id}.json"
            )
            pack_readiness = ComponentReadiness(
                component_type="reference_pack",
                component_id=reference_pack.reference_pack_id,
                is_valid=True,
                is_present=True,
                metadata={
                    "total_items": len(reference_pack.items),
                    "project_binding_required": reference_pack.project_binding_required,
                },
            )
            component_readiness["reference_pack"] = pack_readiness

            # Check for missing references
            for item in reference_pack.items:
                if item.required and not item.path:
                    missing_references.append(item.reference_id)

            # Check for hardcoded project paths in reference pack
            pack_dict = reference_pack.to_dict()
            pack_str = json.dumps(pack_dict, default=str)
            for pattern in WorkflowReadinessEngine.HARDCODED_PROJECT_PATTERNS:
                if pattern in pack_str:
                    if pattern not in hardcoded_paths_detected:
                        hardcoded_paths_detected[pattern] = []
                    hardcoded_paths_detected[pattern].append("reference_pack")
        except Exception as e:
            pack_readiness = ComponentReadiness(
                component_type="reference_pack",
                component_id=reference_pack_id,
                is_valid=False,
                is_present=False,
                errors=[str(e)],
            )
            component_readiness["reference_pack"] = pack_readiness

        # Load and evaluate reference binding
        try:
            binding_data = WorkflowRegistryLoader.load_json(reference_binding_path)
            binding = ReferenceBinding.from_dict(binding_data)
            binding_errors = ReferenceBindingEngine.validate_binding(binding)

            binding_readiness = ComponentReadiness(
                component_type="reference_binding",
                component_id=binding.binding_id,
                is_valid=len(binding_errors) == 0,
                is_present=True,
                errors=binding_errors,
                metadata={"blueprint_id": binding.blueprint_id},
            )
            component_readiness["reference_binding"] = binding_readiness

            if binding_errors:
                invalid_bindings.append(binding.binding_id)

            # Check for hardcoded project paths in binding
            binding_str = json.dumps(binding_data, default=str)
            for pattern in WorkflowReadinessEngine.HARDCODED_PROJECT_PATTERNS:
                if pattern in binding_str:
                    if pattern not in hardcoded_paths_detected:
                        hardcoded_paths_detected[pattern] = []
                    hardcoded_paths_detected[pattern].append("reference_binding")
        except Exception as e:
            binding_readiness = ComponentReadiness(
                component_type="reference_binding",
                component_id="unknown",
                is_valid=False,
                is_present=False,
                errors=[str(e)],
            )
            component_readiness["reference_binding"] = binding_readiness
            invalid_bindings.append("unknown")

        # Load and evaluate reference set report if provided
        if reference_set_report_path and reference_set_report_path.exists():
            try:
                reference_set_data = WorkflowRegistryLoader.load_json(reference_set_report_path)
                set_readiness = ComponentReadiness(
                    component_type="reference_set_report",
                    component_id=reference_set_report_path.stem,
                    is_valid=True,
                    is_present=True,
                    metadata={"report_type": reference_set_data.get("document_type", "unknown")},
                )
                component_readiness["reference_set_report"] = set_readiness

                # Check for hardcoded project paths in reference set report
                set_str = json.dumps(reference_set_data, default=str)
                for pattern in WorkflowReadinessEngine.HARDCODED_PROJECT_PATTERNS:
                    if pattern in set_str:
                        if pattern not in hardcoded_paths_detected:
                            hardcoded_paths_detected[pattern] = []
                        hardcoded_paths_detected[pattern].append("reference_set_report")
            except Exception as e:
                set_readiness = ComponentReadiness(
                    component_type="reference_set_report",
                    component_id=reference_set_report_path.stem,
                    is_valid=False,
                    is_present=False,
                    errors=[str(e)],
                )
                component_readiness["reference_set_report"] = set_readiness

        # Determine overall readiness status
        overall_status = WorkflowReadinessEngine._determine_overall_status(
            component_readiness,
            missing_references,
            invalid_bindings,
            forbidden_actions_detected,
            hardcoded_paths_detected,
        )

        # Generation is NEVER authorized by this layer
        generation_authorized = False
        generation_gate_required = True

        return CombinedReadinessReport(
            report_id=report_id,
            overall_status=overall_status,
            generation_authorized=generation_authorized,
            generation_gate_required=generation_gate_required,
            component_readiness=component_readiness,
            missing_references=missing_references,
            invalid_bindings=invalid_bindings,
            forbidden_actions_detected=forbidden_actions_detected,
            hardcoded_paths_detected=hardcoded_paths_detected,
            metadata={
                "pipeline_blueprint_id": pipeline_blueprint_id,
                "reference_pack_id": reference_pack_id,
            },
        )

    @staticmethod
    def _determine_overall_status(
        component_readiness: dict[str, ComponentReadiness],
        missing_references: list[str],
        invalid_bindings: list[str],
        forbidden_actions_detected: list[str],
        hardcoded_paths_detected: dict[str, list[str]],
    ) -> ReadinessStatus:
        """Determine overall readiness status from component status."""
        # Check for hardcoded project paths (highest priority blocker)
        if hardcoded_paths_detected:
            return ReadinessStatus.BLOCKED_PROJECT_SPECIFIC_HARDCODING

        # Check for forbidden actions
        if forbidden_actions_detected:
            return ReadinessStatus.BLOCKED_FORBIDDEN_RUNTIME_ACTION

        # Check for invalid bindings
        if invalid_bindings:
            return ReadinessStatus.BLOCKED_INVALID_REFERENCE_BINDING

        # Check for missing required references
        if missing_references:
            return ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE

        # Check if any component is invalid or missing
        for component_id, readiness in component_readiness.items():
            if not readiness.is_valid:
                if component_id == "workflow_registry":
                    return ReadinessStatus.BLOCKED_INVALID_WORKFLOW_CONTRACT
                elif component_id == "reference_binding":
                    return ReadinessStatus.BLOCKED_INVALID_REFERENCE_BINDING
                elif component_id in ["reference_pack", "reference_set_report"]:
                    return ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE

        # Check if any component is missing
        for component_id, readiness in component_readiness.items():
            if not readiness.is_present:
                if component_id in ["reference_pack", "reference_set_report"]:
                    return ReadinessStatus.PENDING_OPERATOR_REFERENCE_SUPPLY

        # All checks passed - ready for operator authorization
        return ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION

    @staticmethod
    def create_generation_gate_report(
        readiness_report: CombinedReadinessReport,
    ) -> GenerationGateRequirementReport:
        """Create generation gate requirement report from readiness report."""
        blocking_components: list[str] = []

        # Identify blocking components
        for component_id, readiness in readiness_report.component_readiness.items():
            if not readiness.is_valid or not readiness.is_present:
                blocking_components.append(component_id)

        # Add missing references to blocking components
        if readiness_report.missing_references:
            blocking_components.append("missing_references")

        # Add invalid bindings to blocking components
        if readiness_report.invalid_bindings:
            blocking_components.append("invalid_bindings")

        # Gate is always required and closed in this layer
        gate_required = True
        gate_status = "closed"
        gate_reason = "generation_requires_operator_authorization"

        # If technically ready, gate is still closed but for authorization
        if (
            readiness_report.overall_status
            == ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION
        ):
            gate_reason = "technically_ready_awaiting_operator_authorization"
            blocking_components = []

        return GenerationGateRequirementReport(
            report_id=f"gate_{readiness_report.report_id}",
            gate_required=gate_required,
            gate_status=gate_status,
            gate_reason=gate_reason,
            blocking_components=blocking_components,
            authorization_path=["operator_generation_authorization"],
            metadata={
                "readiness_report_id": readiness_report.report_id,
                "overall_status": readiness_report.overall_status.value,
            },
        )

    @staticmethod
    def create_blocker_report(
        readiness_report: CombinedReadinessReport,
    ) -> BlockerReport:
        """Create blocker report from readiness report."""
        has_blockers = False
        blocker_type: str | None = None
        blocker_details: dict[str, Any] = {}
        resolution_actions: list[str] = []

        if readiness_report.hardcoded_paths_detected:
            has_blockers = True
            blocker_type = "project_specific_hardcoding"
            blocker_details = {
                "hardcoded_patterns": readiness_report.hardcoded_paths_detected,
            }
            resolution_actions = [
                "Remove hardcoded project-specific paths",
                "Use project-agnostic references",
                "Validate with project-agnostic schema",
            ]
        elif readiness_report.forbidden_actions_detected:
            has_blockers = True
            blocker_type = "forbidden_runtime_action"
            blocker_details = {
                "forbidden_actions": readiness_report.forbidden_actions_detected,
            }
            resolution_actions = [
                "Remove forbidden action requests",
                "Ensure no generation/retry/assembly in preflight",
            ]
        elif readiness_report.invalid_bindings:
            has_blockers = True
            blocker_type = "invalid_reference_binding"
            blocker_details = {
                "invalid_bindings": readiness_report.invalid_bindings,
            }
            resolution_actions = [
                "Fix reference binding errors",
                "Validate binding against schema",
                "Ensure slot roles are correct",
            ]
        elif readiness_report.missing_references:
            has_blockers = True
            blocker_type = "missing_required_reference"
            blocker_details = {
                "missing_references": readiness_report.missing_references,
            }
            resolution_actions = [
                "Supply missing reference files",
                "Update reference pack with file paths",
                "Mark optional references if not required",
            ]
        elif readiness_report.overall_status in [
            ReadinessStatus.BLOCKED_INVALID_WORKFLOW_CONTRACT,
        ]:
            has_blockers = True
            blocker_type = "invalid_workflow_contract"
            blocker_details = {
                "status": readiness_report.overall_status.value,
            }
            resolution_actions = [
                "Fix workflow contract errors",
                "Validate contract against schema",
                "Ensure all required fields are present",
            ]

        return BlockerReport(
            report_id=f"blocker_{readiness_report.report_id}",
            has_blockers=has_blockers,
            blocker_type=blocker_type,
            blocker_details=blocker_details,
            resolution_actions=resolution_actions,
            metadata={
                "readiness_report_id": readiness_report.report_id,
                "overall_status": readiness_report.overall_status.value,
            },
        )

    @staticmethod
    def create_manifest(
        task_id: str,
        evaluation_scope: dict[str, Any],
    ) -> WorkflowReadinessManifest:
        """Create workflow readiness manifest."""
        return WorkflowReadinessManifest(
            task_id=task_id,
            evaluation_scope=evaluation_scope,
            metadata={
                "project_agnostic": True,
                "generation_blocked": True,
                "gate_required": True,
            },
        )
