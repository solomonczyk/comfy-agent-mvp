"""Writer for reference binding artifacts."""

import json
from pathlib import Path

from app.reference_binding.binding_engine import ReferenceBindingEngine
from app.reference_binding.models import (
    ReferenceBinding,
    ReferenceReadiness,
    ReferenceRole,
    SlotRequirement,
)


class ReferenceBindingArtifactWriter:
    """Writer for reference binding artifacts."""

    @staticmethod
    def write_binding_manifest(
        output_dir: Path,
        binding: ReferenceBinding,
    ) -> Path:
        """Write reference binding manifest."""
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "reference_binding_manifest.json"

        manifest = {
            "document_type": "reference_binding_manifest",
            "version": "1.0",
            "task_id": "RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001",
            "project_agnostic": True,
            "binding_id": binding.binding_id,
            "blueprint_id": binding.blueprint_id,
            "total_stages": len(binding.stage_bindings),
            "total_slot_requirements": sum(
                len(sb.reference_slot_requirements) for sb in binding.stage_bindings
            ),
            "readiness_policy": binding.readiness_policy,
        }

        with manifest_path.open("w") as f:
            json.dump(manifest, f, indent=2)

        return manifest_path

    @staticmethod
    def write_stage_reference_requirements(
        output_dir: Path,
        binding: ReferenceBinding,
    ) -> Path:
        """Write stage reference requirements."""
        output_dir.mkdir(parents=True, exist_ok=True)
        requirements_path = output_dir / "stage_reference_requirements.json"

        requirements = {
            "document_type": "stage_reference_requirements",
            "version": "1.0",
            "task_id": "RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001",
            "project_agnostic": True,
            "binding_id": binding.binding_id,
            "blueprint_id": binding.blueprint_id,
            "stages": [],
        }

        for stage_binding in binding.stage_bindings:
            stage_info = {
                "stage_id": stage_binding.stage_id,
                "required_slots": [
                    req.slot_id
                    for req in stage_binding.reference_slot_requirements
                    if req.required
                ],
                "optional_slots": [
                    req.slot_id
                    for req in stage_binding.reference_slot_requirements
                    if not req.required
                ],
                "blocking_slots": [
                    req.slot_id
                    for req in stage_binding.reference_slot_requirements
                    if req.blocker_if_missing
                ],
                "gated_slots": [
                    req.slot_id
                    for req in stage_binding.reference_slot_requirements
                    if req.gate_required_before_generation
                ],
            }
            requirements["stages"].append(stage_info)

        with requirements_path.open("w") as f:
            json.dump(requirements, f, indent=2)

        return requirements_path

    @staticmethod
    def write_reference_role_policy(
        output_dir: Path,
        binding: ReferenceBinding,
    ) -> Path:
        """Write reference role policy."""
        output_dir.mkdir(parents=True, exist_ok=True)
        policy_path = output_dir / "reference_role_policy.json"

        policy = {
            "document_type": "reference_role_policy",
            "version": "1.0",
            "task_id": "RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001",
            "project_agnostic": True,
            "binding_id": binding.binding_id,
            "blueprint_id": binding.blueprint_id,
            "supported_roles": [role.value for role in ReferenceRole],
            "role_restrictions": {
                "identity_reference": {
                    "allowed_slot_categories": [
                        "character_pose",
                        "character_expression",
                        "character_detail",
                    ],
                    "forbidden_slots": ["quality_reference", "negative_reference"],
                },
                "style_reference": {
                    "allowed_slot_categories": ["technical_reference"],
                    "forbidden_slots": ["negative_reference"],
                },
                "quality_reference": {
                    "allowed_slot_categories": ["technical_reference"],
                    "forbidden_slots": [],
                    "calibration_only": True,
                },
                "negative_reference": {
                    "allowed_slot_categories": ["technical_reference"],
                    "forbidden_slots": [],
                    "calibration_only": True,
                },
            },
        }

        with policy_path.open("w") as f:
            json.dump(policy, f, indent=2)

        return policy_path

    @staticmethod
    def write_reference_readiness_matrix(
        output_dir: Path,
        readiness: ReferenceReadiness,
    ) -> Path:
        """Write reference readiness matrix."""
        output_dir.mkdir(parents=True, exist_ok=True)
        matrix_path = output_dir / "reference_readiness_matrix.json"

        matrix = readiness.to_dict()
        matrix["document_type"] = "reference_readiness_matrix"
        matrix["version"] = "1.0"
        matrix["task_id"] = "RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001"
        matrix["project_agnostic"] = True

        with matrix_path.open("w") as f:
            json.dump(matrix, f, indent=2)

        return matrix_path

    @staticmethod
    def write_all_artifacts(
        output_dir: Path,
        binding: ReferenceBinding,
        available_slots: dict[str, Any],
    ) -> dict[str, Path]:
        """Write all reference binding artifacts."""
        artifacts: dict[str, Path] = {}

        # Calculate readiness
        readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

        # Write all artifacts
        artifacts["manifest"] = ReferenceBindingArtifactWriter.write_binding_manifest(
            output_dir, binding
        )
        artifacts["stage_requirements"] = (
            ReferenceBindingArtifactWriter.write_stage_reference_requirements(
                output_dir, binding
            )
        )
        artifacts["role_policy"] = ReferenceBindingArtifactWriter.write_reference_role_policy(
            output_dir, binding
        )
        artifacts["readiness_matrix"] = (
            ReferenceBindingArtifactWriter.write_reference_readiness_matrix(
                output_dir, readiness
            )
        )

        return artifacts
