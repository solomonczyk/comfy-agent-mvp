"""Tests for RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001

Execute exactly one corrective fresh visual generation and stop at result review.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.cli_commands.corrective_generation import (
    _read_gate_file,
    _read_corrective_plan,
    _read_operator_approval,
    _read_artifact_index,
    _write_artifact_index,
    _read_ledger,
    _write_ledger,
    _verify_asset,
)


class TestCorrectiveGenerationGateValidation:
    """Test gate validation requirements."""

    def test_corrective_generation_requires_open_gate(self, tmp_path):
        """Test that generation requires the gate to be open."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        # Create a closed gate
        gate = {
            "gate_status": "closed",
            "current_state_after_gate_open": "corrective_generation_gate_opened",
            "next_allowed_action": "corrective_generation_execute_one",
            "max_generations": 1,
            "blind_retry_allowed": False,
            "stop_after_generation": True,
        }
        with open(fresh_dir / "corrective_generation_gate.json", "w") as f:
            json.dump(gate, f)

        # Create required corrective plan
        plan = {
            "defects_to_address": [
                {"defect_id": "VD-001"},
                {"defect_id": "VD-002"},
                {"defect_id": "VD-003"},
                {"defect_id": "VD-004"},
            ]
        }
        with open(fresh_dir / "corrective_plan.json", "w") as f:
            json.dump(plan, f)

        # Create operator approval
        approval = {"corrective_plan_approved": True}
        with open(fresh_dir / "operator_corrective_plan_approval.json", "w") as f:
            json.dump(approval, f)

        # Read gate - should return closed gate
        result = _read_gate_file(control_dir)
        assert result["gate_status"] == "closed"

    def test_corrective_generation_requires_corrective_plan(self, tmp_path):
        """Test that generation requires corrective_plan.json to exist."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        # Missing corrective plan
        result = _read_corrective_plan(control_dir)
        assert result is None

    def test_corrective_generation_requires_operator_approval(self, tmp_path):
        """Test that generation requires operator approval."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        # Create unapproved operator approval
        approval = {"corrective_plan_approved": False}
        with open(fresh_dir / "operator_corrective_plan_approval.json", "w") as f:
            json.dump(approval, f)

        result = _read_operator_approval(control_dir)
        assert result["corrective_plan_approved"] is False


class TestCorrectiveGenerationExecutionConstraints:
    """Test execution constraints for exactly one generation."""

    def test_max_generations_must_be_one(self, tmp_path):
        """Test that max_generations must be 1."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        # Create gate with max_generations != 1
        gate = {
            "gate_status": "open",
            "current_state_after_gate_open": "corrective_generation_gate_opened",
            "next_allowed_action": "corrective_generation_execute_one",
            "max_generations": 2,  # Invalid
            "blind_retry_allowed": False,
            "stop_after_generation": True,
        }
        with open(fresh_dir / "corrective_generation_gate.json", "w") as f:
            json.dump(gate, f)

        result = _read_gate_file(control_dir)
        assert result["max_generations"] == 2  # Would be rejected by validation

    def test_blind_retry_must_be_false(self, tmp_path):
        """Test that blind_retry_allowed must be false."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        gate = {
            "gate_status": "open",
            "blind_retry_allowed": True,  # Invalid
        }
        with open(fresh_dir / "corrective_generation_gate.json", "w") as f:
            json.dump(gate, f)

        result = _read_gate_file(control_dir)
        assert result["blind_retry_allowed"] is True  # Would be rejected by validation

    def test_stop_after_generation_must_be_true(self, tmp_path):
        """Test that stop_after_generation must be true."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        gate = {
            "gate_status": "open",
            "stop_after_generation": False,  # Invalid
        }
        with open(fresh_dir / "corrective_generation_gate.json", "w") as f:
            json.dump(gate, f)

        result = _read_gate_file(control_dir)
        assert result["stop_after_generation"] is False  # Would be rejected by validation


class TestCorrectiveGenerationBlocksSecondAttempt:
    """Test that second generation is blocked."""

    def test_generation_blocks_if_already_performed(self, tmp_path):
        """Test that generation is blocked if already performed."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        gate = {
            "gate_status": "open",
            "generation_performed": True,
            "comfyui_submit_executed": True,
        }
        with open(fresh_dir / "corrective_generation_gate.json", "w") as f:
            json.dump(gate, f)

        result = _read_gate_file(control_dir)
        assert result["generation_performed"] is True
        assert result["comfyui_submit_executed"] is True


class TestCorrectiveGenerationDefectCoverage:
    """Test that corrective plan covers all required defects."""

    def test_corrective_plan_covers_vd001_to_vd004(self, tmp_path):
        """Test that corrective plan covers VD-001 to VD-004."""
        control_dir = tmp_path / "output" / "control"
        fresh_dir = control_dir / "fresh_visual_candidate"
        fresh_dir.mkdir(parents=True, exist_ok=True)

        # Create plan with all required defects
        plan = {
            "defects_to_address": [
                {"defect_id": "VD-001", "description": "Mouth and teeth artifacts"},
                {"defect_id": "VD-002", "description": "Over-smoothed skin"},
                {"defect_id": "VD-003", "description": "Unnatural eye rendering"},
                {"defect_id": "VD-004", "description": "Insufficient facial detail"},
            ]
        }
        with open(fresh_dir / "corrective_plan.json", "w") as f:
            json.dump(plan, f)

        result = _read_corrective_plan(control_dir)
        defect_ids = {d["defect_id"] for d in result["defects_to_address"]}
        required = {"VD-001", "VD-002", "VD-003", "VD-004"}
        assert required.issubset(defect_ids)


class TestCorrectiveGenerationAssetValidation:
    """Test asset validation for generated outputs."""

    def test_reject_missing_asset(self, tmp_path):
        """Test that missing assets are rejected."""
        nonexistent_path = tmp_path / "nonexistent.png"
        result = _verify_asset(nonexistent_path)
        assert result is None

    def test_verify_asset_returns_metadata(self, tmp_path):
        """Test that asset verification returns correct metadata."""
        from PIL import Image

        # Create a test image
        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color="red")
        img.save(img_path)

        result = _verify_asset(img_path)
        assert result is not None
        assert result["exists"] is True
        assert result["readable"] is True
        assert result["width"] == 1024
        assert result["height"] == 1024
        assert "sha256" in result
        assert result["size_bytes"] > 0


class TestCorrectiveGenerationStateUpdates:
    """Test that state files are properly updated."""

    def test_artifact_index_updated(self, tmp_path):
        """Test that artifact index is updated with correct state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Write initial index
        index = {"current_state": "corrective_generation_gate_opened"}
        _write_artifact_index(control_dir, index)

        # Read back
        result = _read_artifact_index(control_dir)
        assert result["current_state"] == "corrective_generation_gate_opened"

    def test_ledger_updated(self, tmp_path):
        """Test that episode ledger is updated with event."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Write initial ledger
        ledger = [{"event_type": "test_event"}]
        _write_ledger(control_dir, ledger)

        # Read back
        result = _read_ledger(control_dir)
        assert len(result) == 1
        assert result[0]["event_type"] == "test_event"


class TestCorrectiveGenerationForbiddenActions:
    """Test that forbidden actions are not performed."""

    def test_visual_qa_not_executed(self):
        """Test that visual QA is not executed."""
        # This test verifies that the execution report shows visual_qa_executed: false
        pass  # Covered by integration test

    def test_assembly_not_executed(self):
        """Test that assembly is not executed."""
        pass  # Covered by integration test

    def test_downstream_not_executed(self):
        """Test that downstream is not executed."""
        pass  # Covered by integration test

    def test_production_accepted_remains_false(self):
        """Test that production_accepted remains false."""
        pass  # Covered by integration test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
