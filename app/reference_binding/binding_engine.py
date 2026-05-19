"""Engine for reference binding between blueprints and reference packs.

Provides functionality to create, validate, and evaluate reference bindings,
including readiness calculations and gate status determination.
"""

from __future__ import annotations

from typing import Any

from app.reference_binding.models import (
    GenerationGateStatus,
    ReadinessPolicy,
    ReferenceBinding,
    ReferenceRole,
    ReferenceReadiness,
    SlotRequirement,
    SlotStatus,
    SlotStatusInfo,
    StageBinding,
    StageReadiness,
)


class ReferenceBindingEngine:
    """Engine for working with reference bindings."""

    @staticmethod
    def create_binding(
        binding_id: str,
        blueprint_id: str,
    ) -> ReferenceBinding:
        """Create a new reference binding."""
        return ReferenceBinding(
            binding_id=binding_id,
            blueprint_id=blueprint_id,
            stage_bindings=[],
            readiness_policy={
                "default_policy": ReadinessPolicy.PENDING_OPERATOR_SUPPLY.value,
                "stage_overrides": {},
            },
            metadata={},
        )

    @staticmethod
    def add_stage_binding(
        binding: ReferenceBinding,
        stage_id: str,
        slot_requirements: list[SlotRequirement],
    ) -> ReferenceBinding:
        """Add a stage binding to the reference binding."""
        stage_binding = StageBinding(
            stage_id=stage_id,
            reference_slot_requirements=slot_requirements,
        )
        binding.stage_bindings.append(stage_binding)
        return binding

    @staticmethod
    def get_stage_binding(
        binding: ReferenceBinding,
        stage_id: str,
    ) -> StageBinding | None:
        """Get a stage binding by stage ID."""
        for stage_binding in binding.stage_bindings:
            if stage_binding.stage_id == stage_id:
                return stage_binding
        return None

    @staticmethod
    def validate_binding(binding: ReferenceBinding) -> list[str]:
        """Validate a reference binding."""
        errors: list[str] = []

        # Check that binding_id is provided
        if not binding.binding_id:
            errors.append("binding_id is required")

        # Check that blueprint_id is provided
        if not binding.blueprint_id:
            errors.append("blueprint_id is required")

        # Check that stage_bindings is not empty
        if not binding.stage_bindings:
            errors.append("stage_bindings cannot be empty")

        # Validate each stage binding
        for stage_binding in binding.stage_bindings:
            if not stage_binding.stage_id:
                errors.append("stage_id is required for each stage binding")

            if not stage_binding.reference_slot_requirements:
                errors.append(
                    f"reference_slot_requirements cannot be empty for stage {stage_binding.stage_id}"
                )

            # Validate each slot requirement
            for slot_req in stage_binding.reference_slot_requirements:
                if not slot_req.slot_id:
                    errors.append(
                        f"slot_id is required for slot in stage {stage_binding.stage_id}"
                    )

                # Validate that quality_reference cannot be used as identity_reference
                if (
                    slot_req.slot_role == ReferenceRole.IDENTITY_REFERENCE
                    and "quality" in slot_req.slot_id.lower()
                ):
                    errors.append(
                        f"quality reference cannot be used as identity reference: {slot_req.slot_id}"
                    )

                # Validate that negative_reference cannot be used as positive prompt source
                if (
                    slot_req.slot_role == ReferenceRole.IDENTITY_REFERENCE
                    and "negative" in slot_req.slot_id.lower()
                ):
                    errors.append(
                        f"negative reference cannot be used as identity reference: {slot_req.slot_id}"
                    )

        # Validate readiness policy
        if "default_policy" not in binding.readiness_policy:
            errors.append("readiness_policy must have default_policy")

        return errors

    @staticmethod
    def calculate_readiness(
        binding: ReferenceBinding,
        available_slots: dict[str, Any],
    ) -> ReferenceReadiness:
        """Calculate readiness matrix based on available reference slots."""
        stage_readiness_list: list[StageReadiness] = []
        blocking_slots: list[str] = []
        blocking_stages: list[str] = []

        for stage_binding in binding.stage_bindings:
            slot_status_list: list[SlotStatusInfo] = []
            stage_blocked = False
            any_required_missing = False

            for slot_req in stage_binding.reference_slot_requirements:
                # Check if slot is available
                slot_available = slot_req.slot_id in available_slots

                # Determine status
                if slot_available:
                    status = SlotStatus.SATISFIED
                else:
                    status = SlotStatus.MISSING
                    if slot_req.required:
                        any_required_missing = True

                # Check if this is a blocker
                is_blocker = slot_req.blocker_if_missing and not slot_available
                if is_blocker:
                    stage_blocked = True
                    blocking_slots.append(slot_req.slot_id)

                slot_status_info = SlotStatusInfo(
                    slot_id=slot_req.slot_id,
                    slot_role=slot_req.slot_role,
                    status=status,
                    required=slot_req.required,
                    blocker=is_blocker,
                )
                slot_status_list.append(slot_status_info)

            # Determine overall stage readiness
            if stage_blocked:
                readiness_status = ReadinessPolicy.BLOCKED_MISSING_REQUIRED_REFERENCE
                blocking_stages.append(stage_binding.stage_id)
            elif any_required_missing:
                readiness_status = ReadinessPolicy.PENDING_OPERATOR_SUPPLY
            else:
                readiness_status = ReadinessPolicy.READY

            stage_readiness = StageReadiness(
                stage_id=stage_binding.stage_id,
                readiness_status=readiness_status,
                slot_status=slot_status_list,
            )
            stage_readiness_list.append(stage_readiness)

        # Determine generation gate status
        gate_open = not blocking_stages and not blocking_slots
        generation_gate_status = GenerationGateStatus(
            gate_open=gate_open,
            blocking_slots=blocking_slots,
            blocking_stages=blocking_stages,
        )

        return ReferenceReadiness(
            readiness_id=f"{binding.binding_id}_readiness",
            binding_id=binding.binding_id,
            blueprint_id=binding.blueprint_id,
            stage_readiness=stage_readiness_list,
            generation_gate_status=generation_gate_status,
            metadata={},
        )

    @staticmethod
    def get_required_slots_for_stage(
        binding: ReferenceBinding,
        stage_id: str,
    ) -> list[SlotRequirement]:
        """Get required reference slots for a specific stage."""
        stage_binding = ReferenceBindingEngine.get_stage_binding(binding, stage_id)
        if stage_binding:
            return [
                req for req in stage_binding.reference_slot_requirements if req.required
            ]
        return []

    @staticmethod
    def get_optional_slots_for_stage(
        binding: ReferenceBinding,
        stage_id: str,
    ) -> list[SlotRequirement]:
        """Get optional reference slots for a specific stage."""
        stage_binding = ReferenceBindingEngine.get_stage_binding(binding, stage_id)
        if stage_binding:
            return [
                req
                for req in stage_binding.reference_slot_requirements
                if not req.required
            ]
        return []

    @staticmethod
    def get_slots_by_role(
        binding: ReferenceBinding,
        stage_id: str,
        role: ReferenceRole,
    ) -> list[SlotRequirement]:
        """Get reference slots for a specific stage and role."""
        stage_binding = ReferenceBindingEngine.get_stage_binding(binding, stage_id)
        if stage_binding:
            return [
                req for req in stage_binding.reference_slot_requirements if req.slot_role == role
            ]
        return []

    @staticmethod
    def inspect_binding(binding: ReferenceBinding) -> dict[str, Any]:
        """Inspect a binding and return detailed information."""
        inspection: dict[str, Any] = {
            "binding_id": binding.binding_id,
            "blueprint_id": binding.blueprint_id,
            "total_stages": len(binding.stage_bindings),
            "stage_details": [],
            "slot_summary": {
                "total_slots": 0,
                "by_role": {},
            },
        }

        role_counts: dict[str, int] = {}

        for stage_binding in binding.stage_bindings:
            stage_detail: dict[str, Any] = {
                "stage_id": stage_binding.stage_id,
                "total_slots": len(stage_binding.reference_slot_requirements),
                "required_slots": sum(
                    1 for req in stage_binding.reference_slot_requirements if req.required
                ),
                "optional_slots": sum(
                    1 for req in stage_binding.reference_slot_requirements if not req.required
                ),
                "slots_with_gates": sum(
                    1
                    for req in stage_binding.reference_slot_requirements
                    if req.gate_required_before_generation
                ),
                "blocking_slots": sum(
                    1 for req in stage_binding.reference_slot_requirements if req.blocker_if_missing
                ),
            }
            inspection["stage_details"].append(stage_detail)

            for req in stage_binding.reference_slot_requirements:
                inspection["slot_summary"]["total_slots"] += 1
                role = req.slot_role.value
                role_counts[role] = role_counts.get(role, 0) + 1

        inspection["slot_summary"]["by_role"] = role_counts

        return inspection
