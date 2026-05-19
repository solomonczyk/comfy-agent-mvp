"""Tests for workflow registry CLI commands.

Task: RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import pytest

from app.cli_commands.workflow_registry import (
    init_workflow_registry,
    validate_workflow_registry,
    inspect_workflow_registry,
    validate_pipeline_blueprint,
    validate_reference_pack,
)


def test_cli_init_workflow_registry():
    """Test initializing a workflow registry via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_root = Path(tmpdir) / "registry"
        
        args = argparse.Namespace(
            registry_root=str(registry_root),
            registry_id="test_registry",
            json=True,
        )
        
        result_code = init_workflow_registry(args)
        assert result_code == 0
        
        # Check that registry was created
        assert registry_root.exists()
        assert (registry_root / "workflow_registry.json").exists()
        assert (registry_root / "workflow_contracts").exists()
        assert (registry_root / "pipeline_blueprints").exists()
        assert (registry_root / "reference_packs").exists()
        assert (registry_root / "gate_contracts").exists()
        assert (registry_root / "execution_contracts").exists()


def test_cli_validate_workflow_registry():
    """Test validating a workflow registry via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_root = Path(tmpdir) / "registry"
        
        # First initialize
        init_args = argparse.Namespace(
            registry_root=str(registry_root),
            registry_id="test_registry",
            json=True,
        )
        init_workflow_registry(init_args)
        
        # Then validate
        validate_args = argparse.Namespace(
            registry_root=str(registry_root),
            json=True,
        )
        result_code = validate_workflow_registry(validate_args)
        assert result_code == 0


def test_cli_inspect_workflow_registry():
    """Test inspecting a workflow registry via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_root = Path(tmpdir) / "registry"
        
        # First initialize
        init_args = argparse.Namespace(
            registry_root=str(registry_root),
            registry_id="test_registry",
            json=True,
        )
        init_workflow_registry(init_args)
        
        # Then inspect
        inspect_args = argparse.Namespace(
            registry_root=str(registry_root),
            json=True,
        )
        result_code = inspect_workflow_registry(inspect_args)
        assert result_code == 0


def test_cli_validate_pipeline_blueprint():
    """Test validating a pipeline blueprint via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        blueprint_path = Path(tmpdir) / "blueprint.json"
        
        # Create a valid blueprint
        blueprint_data = {
            "blueprint_id": "test_blueprint",
            "stages": [
                {
                    "stage_id": "stage1",
                    "stage_name": "Generation",
                    "stage_type": "generation",
                    "required_artifacts": [],
                    "optional_artifacts": [],
                    "gate_required": False,
                    "operator_review_point": False,
                }
            ],
            "stage_order": ["stage1"],
            "required_artifacts": [],
            "state_transitions": [],
            "operator_review_points": [],
            "dangerous_action_gates": [],
        }
        
        with open(blueprint_path, "w") as f:
            json.dump(blueprint_data, f)
        
        args = argparse.Namespace(
            blueprint=str(blueprint_path),
            json=True,
        )
        result_code = validate_pipeline_blueprint(args)
        assert result_code == 0


def test_cli_validate_pipeline_blueprint_with_forbidden_pattern():
    """Test that blueprints with forbidden patterns are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        blueprint_path = Path(tmpdir) / "blueprint.json"
        
        # Create a blueprint with forbidden pattern
        blueprint_data = {
            "blueprint_id": "test_blueprint",
            "stages": [
                {
                    "stage_id": "stage1",
                    "stage_name": "Generation",
                    "stage_type": "generation",
                    "required_artifacts": ["data/rc2_multishot1_ep01/prompt"],  # Forbidden
                    "optional_artifacts": [],
                    "gate_required": False,
                    "operator_review_point": False,
                }
            ],
            "stage_order": ["stage1"],
            "required_artifacts": [],
            "state_transitions": [],
            "operator_review_points": [],
            "dangerous_action_gates": [],
        }
        
        with open(blueprint_path, "w") as f:
            json.dump(blueprint_data, f)
        
        args = argparse.Namespace(
            blueprint=str(blueprint_path),
            json=True,
        )
        result_code = validate_pipeline_blueprint(args)
        assert result_code == 1  # Should fail


def test_cli_validate_reference_pack():
    """Test validating a reference pack via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_path = Path(tmpdir) / "pack.json"
        
        # Create a valid reference pack
        pack_data = {
            "reference_pack_id": "test_pack",
            "project_binding_required": False,
            "reference_types": ["style", "character"],
            "items": [
                {
                    "reference_id": "style1",
                    "reference_type": "style",
                    "description": "Style reference",
                    "path": None,  # No actual image required
                    "required": True,
                    "metadata": {},
                }
            ],
            "usage_policy": {
                "allow_slot_description": True,
                "require_actual_images": False,
            },
            "operator_review_required": True,
        }
        
        with open(pack_path, "w") as f:
            json.dump(pack_data, f)
        
        args = argparse.Namespace(
            reference_pack=str(pack_path),
            json=True,
        )
        result_code = validate_reference_pack(args)
        assert result_code == 0


def test_cli_validate_reference_pack_requires_actual_images():
    """Test that reference packs requiring actual images are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_path = Path(tmpdir) / "pack.json"
        
        # Create a pack that requires actual images
        pack_data = {
            "reference_pack_id": "test_pack",
            "project_binding_required": False,
            "reference_types": ["style"],
            "items": [],
            "usage_policy": {
                "allow_slot_description": True,
                "require_actual_images": True,  # Should be False
            },
            "operator_review_required": True,
        }
        
        with open(pack_path, "w") as f:
            json.dump(pack_data, f)
        
        args = argparse.Namespace(
            reference_pack=str(pack_path),
            json=True,
        )
        result_code = validate_reference_pack(args)
        assert result_code == 1  # Should fail


def test_cli_validate_reference_pack_with_hardcoded_path():
    """Test that reference packs with hardcoded episode-specific paths are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_path = Path(tmpdir) / "pack.json"
        
        # Create a pack with hardcoded path
        pack_data = {
            "reference_pack_id": "test_pack",
            "project_binding_required": False,
            "reference_types": ["style"],
            "items": [
                {
                    "reference_id": "style1",
                    "reference_type": "style",
                    "description": "Style reference",
                    "path": "data/rc2_multishot1_ep01/style.png",  # Forbidden
                    "required": True,
                    "metadata": {},
                }
            ],
            "usage_policy": {
                "allow_slot_description": True,
                "require_actual_images": False,
            },
            "operator_review_required": True,
        }
        
        with open(pack_path, "w") as f:
            json.dump(pack_data, f)
        
        args = argparse.Namespace(
            reference_pack=str(pack_path),
            json=True,
        )
        result_code = validate_reference_pack(args)
        assert result_code == 1  # Should fail


def test_cli_json_output_deterministic():
    """Test that CLI JSON output is deterministic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_root = Path(tmpdir) / "registry"
        
        args = argparse.Namespace(
            registry_root=str(registry_root),
            registry_id="test_registry",
            json=True,
        )
        
        # Run twice and compare output
        import sys
        from io import StringIO
        
        # First run
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        init_workflow_registry(args)
        output1 = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Second run
        sys.stdout = StringIO()
        init_workflow_registry(args)
        output2 = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Parse and compare
        data1 = json.loads(output1)
        data2 = json.loads(output2)
        
        # Same registry_id should produce same output
        assert data1["registry_id"] == data2["registry_id"]
        assert data1["status"] == data2["status"]
