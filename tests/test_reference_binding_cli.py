"""Tests for reference binding CLI commands.

Task: RC-COMBINE-V2-BLUEPRINT-REFERENCE-BINDING-001
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from app.cli_commands.reference_binding import reference_binding
from app.reference_binding.binding_engine import ReferenceBindingEngine
from app.reference_binding.models import ReferenceRole, SlotRequirement


class TestReferenceBindingCLI:
    """Test reference binding CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = Path("temp_test_reference_binding")
        self.temp_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_validate_valid_binding(self):
        """Test validating a valid binding."""
        # Create a valid binding
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

        binding_file = self.temp_dir / "test_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding.to_dict(), f)

        # Test validation
        result = self.runner.invoke(reference_binding, ["validate", str(binding_file)])

        assert result.exit_code == 0
        assert "Validation PASSED" in result.output

    def test_validate_invalid_binding(self):
        """Test validating an invalid binding."""
        # Create an invalid binding (missing stage_bindings)
        binding_data = {
            "binding_id": "test_binding",
            "blueprint_id": "test_blueprint",
            "stage_bindings": [],
            "readiness_policy": {},
        }

        binding_file = self.temp_dir / "invalid_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding_data, f)

        # Test validation
        result = self.runner.invoke(reference_binding, ["validate", str(binding_file)])

        assert result.exit_code != 0
        assert "Validation FAILED" in result.output

    def test_inspect_binding(self):
        """Test inspecting a binding."""
        # Create a binding
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

        binding_file = self.temp_dir / "test_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding.to_dict(), f)

        # Test inspection
        result = self.runner.invoke(reference_binding, ["inspect", str(binding_file)])

        assert result.exit_code == 0
        inspection_data = json.loads(result.output)
        assert inspection_data["binding_id"] == "test_binding"
        assert inspection_data["total_stages"] == 1

    def test_readiness_report(self):
        """Test generating a readiness report."""
        # Create a binding
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

        binding_file = self.temp_dir / "test_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding.to_dict(), f)

        # Create available slots
        available_slots = {"character_front_full_body": {"path": "/path/to/image.jpg"}}
        slots_file = self.temp_dir / "available_slots.json"
        with slots_file.open("w") as f:
            json.dump(available_slots, f)

        # Test readiness report
        result = self.runner.invoke(
            reference_binding,
            ["readiness-report", str(binding_file), str(slots_file)],
        )

        assert result.exit_code == 0
        readiness_data = json.loads(result.output)
        assert readiness_data["binding_id"] == "test_binding"
        assert readiness_data["generation_gate_status"]["gate_open"] is True

    def test_get_required_slots(self):
        """Test getting required slots for a stage."""
        # Create a binding
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

        binding_file = self.temp_dir / "test_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding.to_dict(), f)

        # Test getting required slots
        result = self.runner.invoke(
            reference_binding, ["get-required-slots", str(binding_file), "test_stage"]
        )

        assert result.exit_code == 0
        assert "required_slot" in result.output
        assert "optional_slot" not in result.output

    def test_get_optional_slots(self):
        """Test getting optional slots for a stage."""
        # Create a binding
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

        binding_file = self.temp_dir / "test_binding.json"
        with binding_file.open("w") as f:
            json.dump(binding.to_dict(), f)

        # Test getting optional slots
        result = self.runner.invoke(
            reference_binding, ["get-optional-slots", str(binding_file), "test_stage"]
        )

        assert result.exit_code == 0
        assert "optional_slot" in result.output
        assert "required_slot" not in result.output
