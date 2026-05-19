"""Tests for reference binding between blueprints and reference packs.

Task: RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001
"""

import pytest

from app.reference_binding.binding_engine import ReferenceBindingEngine
from app.reference_binding.models import (
    ReferenceBinding,
    ReferenceRole,
    ReadinessPolicy,
    SlotRequirement,
    SlotStatus,
)


class TestReferenceBindingValidation:
    """Test reference binding validation."""

    def test_valid_binding_passes(self):
        """Test that a valid binding passes validation."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="character_front_full_body",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        errors = ReferenceBindingEngine.validate_binding(binding)
        assert len(errors) == 0, "Valid binding should have no errors"

    def test_missing_optional_slot_does_not_block(self):
        """Test that missing optional slots do not block execution."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="expression_variants",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=False,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        # No slots available
        available_slots = {}

        readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

        # Stage should be ready since slot is optional
        assert readiness.stage_readiness[0].readiness_status == ReadinessPolicy.READY

    def test_missing_required_slot_blocks(self):
        """Test that missing required slots block execution."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="character_front_full_body",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
            blocker_if_missing=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        # No slots available
        available_slots = {}

        readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

        # Stage should be blocked
        assert (
            readiness.stage_readiness[0].readiness_status
            == ReadinessPolicy.BLOCKED_MISSING_REQUIRED_REFERENCE
        )
        assert readiness.generation_gate_status.gate_open is False

    def test_quality_reference_cannot_be_used_as_identity_reference(self):
        """Test that quality reference cannot be used as identity reference."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="quality_reference",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        errors = ReferenceBindingEngine.validate_binding(binding)
        assert len(errors) > 0
        assert any("quality reference cannot be used as identity" in err for err in errors)

    def test_negative_reference_cannot_be_used_as_identity_reference(self):
        """Test that negative reference cannot be used as identity reference."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="negative_reference",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        errors = ReferenceBindingEngine.validate_binding(binding)
        assert len(errors) > 0
        assert any("negative reference cannot be used as identity" in err for err in errors)

    def test_no_generation_gate_opened(self):
        """Test that generation gate is not opened when required slots are missing."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="character_front_full_body",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
            gate_required_before_generation=True,
            blocker_if_missing=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        # No slots available
        available_slots = {}

        readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

        # Generation gate should be closed
        assert readiness.generation_gate_status.gate_open is False
        assert len(readiness.generation_gate_status.blocking_slots) > 0

    def test_generation_gate_opened_when_all_required_satisfied(self):
        """Test that generation gate is opened when all required slots are satisfied."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="character_front_full_body",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
            gate_required_before_generation=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="character_generation",
            slot_requirements=[slot_req],
        )

        # Slot available
        available_slots = {"character_front_full_body": {"path": "/path/to/image.jpg"}}

        readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

        # Generation gate should be open
        assert readiness.generation_gate_status.gate_open is True
        assert len(readiness.generation_gate_status.blocking_slots) == 0


class TestReferenceBindingModels:
    """Test reference binding data models."""

    def test_slot_requirement_serialization(self):
        """Test slot requirement serialization."""
        slot_req = SlotRequirement(
            slot_id="test_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        slot_dict = slot_req.to_dict()
        assert slot_dict["slot_id"] == "test_slot"
        assert slot_dict["slot_role"] == "identity_reference"
        assert slot_dict["required"] is True

        # Test deserialization
        restored = SlotRequirement.from_dict(slot_dict)
        assert restored.slot_id == "test_slot"
        assert restored.slot_role == ReferenceRole.IDENTITY_REFERENCE
        assert restored.required is True

    def test_reference_binding_serialization(self):
        """Test reference binding serialization."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="test_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="test_stage",
            slot_requirements=[slot_req],
        )

        binding_dict = binding.to_dict()
        assert binding_dict["binding_id"] == "test_binding"
        assert binding_dict["blueprint_id"] == "test_blueprint"
        assert len(binding_dict["stage_bindings"]) == 1

        # Test deserialization
        restored = ReferenceBinding.from_dict(binding_dict)
        assert restored.binding_id == "test_binding"
        assert restored.blueprint_id == "test_blueprint"
        assert len(restored.stage_bindings) == 1


class TestReferenceBindingEngine:
    """Test reference binding engine functionality."""

    def test_get_required_slots_for_stage(self):
        """Test getting required slots for a stage."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        required_slot = SlotRequirement(
            slot_id="required_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        optional_slot = SlotRequirement(
            slot_id="optional_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=False,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="test_stage",
            slot_requirements=[required_slot, optional_slot],
        )

        required_slots = ReferenceBindingEngine.get_required_slots_for_stage(
            binding, "test_stage"
        )

        assert len(required_slots) == 1
        assert required_slots[0].slot_id == "required_slot"

    def test_get_optional_slots_for_stage(self):
        """Test getting optional slots for a stage."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        required_slot = SlotRequirement(
            slot_id="required_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        optional_slot = SlotRequirement(
            slot_id="optional_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=False,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="test_stage",
            slot_requirements=[required_slot, optional_slot],
        )

        optional_slots = ReferenceBindingEngine.get_optional_slots_for_stage(
            binding, "test_stage"
        )

        assert len(optional_slots) == 1
        assert optional_slots[0].slot_id == "optional_slot"

    def test_get_slots_by_role(self):
        """Test getting slots by role."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        identity_slot = SlotRequirement(
            slot_id="identity_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        style_slot = SlotRequirement(
            slot_id="style_slot",
            slot_role=ReferenceRole.STYLE_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="test_stage",
            slot_requirements=[identity_slot, style_slot],
        )

        identity_slots = ReferenceBindingEngine.get_slots_by_role(
            binding, "test_stage", ReferenceRole.IDENTITY_REFERENCE
        )

        assert len(identity_slots) == 1
        assert identity_slots[0].slot_id == "identity_slot"

    def test_inspect_binding(self):
        """Test binding inspection."""
        binding = ReferenceBindingEngine.create_binding(
            binding_id="test_binding",
            blueprint_id="test_blueprint",
        )

        slot_req = SlotRequirement(
            slot_id="test_slot",
            slot_role=ReferenceRole.IDENTITY_REFERENCE,
            required=True,
        )

        ReferenceBindingEngine.add_stage_binding(
            binding,
            stage_id="test_stage",
            slot_requirements=[slot_req],
        )

        inspection = ReferenceBindingEngine.inspect_binding(binding)

        assert inspection["binding_id"] == "test_binding"
        assert inspection["blueprint_id"] == "test_blueprint"
        assert inspection["total_stages"] == 1
        assert inspection["slot_summary"]["total_slots"] == 1
