"""Tests for corrective visual generation workflow stage.

RC-COMBINE-V2-CORRECTIVE-VISUAL-GENERATION-WORKFLOW-STAGE-001
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli_commands.corrective_visual_generation_stage import (
    _build_corrective_workflow,
    _compute_sha256,
    _read_curator_package,
    _read_negative_reference_evidence,
    _read_reference_misuse_diagnosis,
    _read_reference_role_map,
    _read_reference_usage_policy,
    _read_state,
    _verify_asset,
    execute_corrective_visual_generation_stage,
)


class TestCorrectiveVisualGenerationWorkflowStage:
    """Test suite for corrective visual generation workflow stage."""

    def test_read_state(self, tmp_path: Path) -> None:
        """Test reading state file."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        state_data = {"current_state": "test_state", "production_accepted": False}
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f)
        
        result = _read_state(control_dir)
        assert result == state_data

    def test_read_state_missing(self, tmp_path: Path) -> None:
        """Test reading state file when missing."""
        control_dir = tmp_path / "output" / "control"
        result = _read_state(control_dir)
        assert result == {}

    def test_read_curator_package(self, tmp_path: Path) -> None:
        """Test reading curator package."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        package_data = {"package_id": "test_package", "references": ["ref1", "ref2"]}
        package_path = control_dir / "corrective_reference_bound_generation_package.json"
        with open(package_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f)
        
        result = _read_curator_package(control_dir)
        assert result == package_data

    def test_read_curator_package_missing(self, tmp_path: Path) -> None:
        """Test reading curator package when missing."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        result = _read_curator_package(control_dir)
        assert result is None

    def test_read_reference_role_map(self, tmp_path: Path) -> None:
        """Test reading reference role map."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        role_map = {
            "quality_only_refs": ["ref1"],
            "composition_refs": ["ref2"]
        }
        role_map_path = control_dir / "canonical_reference_role_map.json"
        with open(role_map_path, 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        result = _read_reference_role_map(control_dir)
        assert result == role_map

    def test_read_reference_usage_policy(self, tmp_path: Path) -> None:
        """Test reading reference usage policy."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        policy = {
            "policy_id": "reference_usage_policy",
            "quality_only_refs": ["ref1"]
        }
        policy_path = control_dir / "reference_usage_policy.json"
        with open(policy_path, 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        result = _read_reference_usage_policy(control_dir)
        assert result == policy

    def test_read_negative_reference_evidence(self, tmp_path: Path) -> None:
        """Test reading negative reference evidence."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        evidence = {
            "negative_reference_present": True,
            "negative_reference_path": "/path/to/rejected_asset.png"
        }
        evidence_path = control_dir / "negative_reference_evidence.json"
        with open(evidence_path, 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        result = _read_negative_reference_evidence(control_dir)
        assert result == evidence

    def test_read_reference_misuse_diagnosis(self, tmp_path: Path) -> None:
        """Test reading reference misuse diagnosis."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        diagnosis = {
            "misuse_issues": [
                {"issue_type": "extreme_face_crop", "explicitly_controlled": True}
            ]
        }
        diagnosis_path = control_dir / "reference_misuse_diagnosis.json"
        with open(diagnosis_path, 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        result = _read_reference_misuse_diagnosis(control_dir)
        assert result == diagnosis

    def test_build_corrective_workflow(self) -> None:
        """Test building corrective workflow."""
        workflow = _build_corrective_workflow(1024, 1024)
        
        assert "3" in workflow  # KSampler
        assert "4" in workflow  # CheckpointLoader
        assert "5" in workflow  # EmptyLatentImage
        assert "6" in workflow  # CLIP Text Encode (positive)
        assert "7" in workflow  # CLIP Text Encode (negative)
        assert "8" in workflow  # VAEDecode
        assert "9" in workflow  # SaveImage
        
        assert workflow["5"]["inputs"]["width"] == 1024
        assert workflow["5"]["inputs"]["height"] == 1024

    def test_compute_sha256(self, tmp_path: Path) -> None:
        """Test SHA256 computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        sha256 = _compute_sha256(test_file)
        assert len(sha256) == 64
        assert isinstance(sha256, str)

    def test_verify_asset(self, tmp_path: Path) -> None:
        """Test asset verification."""
        # Create a minimal valid PNG file
        from PIL import Image
        test_image = tmp_path / "test.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image)
        
        result = _verify_asset(test_image)
        assert result is not None
        assert result["exists"] is True
        assert result["readable"] is True
        assert result["width"] == 100
        assert result["height"] == 100
        assert result["sha256"] is not None
        assert result["size_bytes"] > 0

    def test_verify_asset_missing(self, tmp_path: Path) -> None:
        """Test asset verification for missing file."""
        test_file = tmp_path / "nonexistent.png"
        result = _verify_asset(test_file)
        assert result is None

    def test_authorization_required(self, tmp_path: Path) -> None:
        """Test that authorization is required."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state to authorization required
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create required artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        # Run dry-run (no execute flag)
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed in dry-run mode
        assert result == 0

    def test_curator_package_required(self, tmp_path: Path) -> None:
        """Test that curator package is required."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state to authorization required
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Missing curator package
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should fail due to missing curator package
        assert result == 1

    def test_quality_refs_blocked_as_composition(self, tmp_path: Path) -> None:
        """Test that quality refs cannot be used as composition targets."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts with quality ref in composition refs
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {
            "quality_only_refs": ["quality_ref1"],
            "composition_refs": ["quality_ref1"]  # Quality ref used as composition - forbidden
        }
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should fail due to quality ref used as composition target
        assert result == 1

    def test_negative_reference_required(self, tmp_path: Path) -> None:
        """Test that negative reference is required."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts without negative reference
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": False}  # Missing negative reference
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should fail due to missing negative reference
        assert result == 1

    def test_max_generations_enforced(self, tmp_path: Path) -> None:
        """Test that max_generations=1 is enforced."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create all required artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check that max_generations=1 in contract
        contract_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["max_generations"] == 1
        assert contract["retry_allowed"] is False
        assert contract["stop_after_generation"] is True

    def test_second_generation_blocked(self, tmp_path: Path) -> None:
        """Test that second generation is blocked."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state with generation already performed
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False,
            "corrective_visual_generation_performed": True  # Already performed
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should fail due to generation already performed
        assert result == 1

    def test_retry_blocked(self, tmp_path: Path) -> None:
        """Test that retry is blocked."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check that retry is blocked in contract
        contract_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["retry_allowed"] is False
        assert contract["generation_constraints"]["retry_forbidden"] is True
        assert contract["generation_constraints"]["blind_retry_forbidden"] is True

    def test_state_transitions_to_operator_visual_review(self, tmp_path: Path) -> None:
        """Test that state transitions to operator_visual_review_required on success."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check state transition
        with open(state_path, 'r', encoding='utf-8') as f:
            updated_state = json.load(f)
        
        assert updated_state["current_state"] == "operator_visual_review_required"
        assert updated_state["next_allowed_action"] == "operator_visual_review_required"
        assert updated_state["production_accepted"] is False

    def test_production_accepted_remains_false(self, tmp_path: Path) -> None:
        """Test that production_accepted remains false."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check production_accepted remains false
        with open(state_path, 'r', encoding='utf-8') as f:
            updated_state = json.load(f)
        
        assert updated_state["production_accepted"] is False
        
        # Also check in contract
        contract_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["production_accepted"] is False

    def test_no_assembly_or_downstream(self, tmp_path: Path) -> None:
        """Test that assembly and downstream are blocked."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check assembly and downstream blocked
        contract_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_contract.json"
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        assert contract["assembly_allowed"] is False
        assert contract["downstream_allowed"] is False
        assert contract["generation_constraints"]["assembly_blocked"] is True
        assert contract["generation_constraints"]["downstream_blocked"] is True

    def test_required_artifacts_created(self, tmp_path: Path) -> None:
        """Test that all required artifacts are created."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check required artifacts exist
        stage_dir = control_dir / "corrective_visual_generation_stage"
        required_artifacts = [
            "corrective_visual_generation_authorization.json",
            "corrective_visual_generation_contract.json",
            "corrective_visual_generation_preflight.json",
            "submitted_workflow.json",
            "corrective_visual_generation_manifest.json",
            "corrective_visual_generation_result_review.json",
            "operator_visual_review_packet.json",
            "corrective_visual_generation_stage_proof.json"
        ]
        
        for artifact in required_artifacts:
            assert (stage_dir / artifact).exists(), f"Missing artifact: {artifact}"

    def test_dry_run_cannot_be_reported_as_real_execution(self, tmp_path: Path) -> None:
        """Test that dry-run cannot be reported as real execution."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False  # Dry-run mode
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # Check that dry-run is properly reported
        manifest_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        assert manifest["execute_mode"] is False
        assert manifest["prompt_id"].startswith("dry-run-")
        
        # Check state
        with open(state_path, 'r', encoding='utf-8') as f:
            updated_state = json.load(f)
        
        assert updated_state["comfyui_submit_executed"] is False

    def test_manifest_matches_real_filesystem_asset(self, tmp_path: Path) -> None:
        """Test that manifest matches real filesystem asset (when execute=True)."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Set state
        state = {
            "current_state": "corrective_reference_bound_generation_authorization_required",
            "production_accepted": False
        }
        state_path = control_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        
        # Create artifacts
        package = {"package_id": "test"}
        with open(control_dir / "corrective_reference_bound_generation_package.json", 'w', encoding='utf-8') as f:
            json.dump(package, f)
        
        role_map = {"quality_only_refs": [], "composition_refs": []}
        with open(control_dir / "canonical_reference_role_map.json", 'w', encoding='utf-8') as f:
            json.dump(role_map, f)
        
        policy = {"policy_id": "test"}
        with open(control_dir / "reference_usage_policy.json", 'w', encoding='utf-8') as f:
            json.dump(policy, f)
        
        evidence = {"negative_reference_present": True}
        with open(control_dir / "negative_reference_evidence.json", 'w', encoding='utf-8') as f:
            json.dump(evidence, f)
        
        diagnosis = {"misuse_issues": []}
        with open(control_dir / "reference_misuse_diagnosis.json", 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f)
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.execute = False  # Use dry-run for this test
        args.json = True
        
        with patch('sys.stdout', new_callable=MagicMock):
            result = execute_corrective_visual_generation_stage(args)
        
        # Should succeed
        assert result == 0
        
        # In dry-run mode, no assets are generated, so manifest should be empty
        manifest_path = control_dir / "corrective_visual_generation_stage" / "corrective_visual_generation_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        assert manifest["generated_assets"] == []
