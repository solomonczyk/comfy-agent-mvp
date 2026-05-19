"""Tests for project-agnostic workflow registry.

Task: RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from app.workflow_registry.models import (
    ExecutionContract,
    GateContract,
    PipelineBlueprint,
    PipelineStage,
    ReferenceItem,
    ReferencePack,
    ReferenceType,
    StateTransition,
    WorkflowContract,
    WorkflowRegistry,
    WorkflowType,
)
from app.workflow_registry.validator import WorkflowRegistryValidator


def test_workflow_contract_valid():
    """Test that a valid workflow contract is accepted."""
    contract = WorkflowContract(
        workflow_id="test_workflow",
        workflow_type=WorkflowType.IMAGE,
        project_agnostic=True,
        required_inputs=["prompt"],
        outputs=["image"],
        forbidden_actions=["generation_performed"],
    )
    errors = WorkflowRegistryValidator.validate_workflow_contract(contract)
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_workflow_contract_missing_required_field():
    """Test that missing required fields are rejected."""
    contract = WorkflowContract(
        workflow_id="",  # Missing workflow_id
        workflow_type=WorkflowType.IMAGE,
        project_agnostic=True,
    )
    errors = WorkflowRegistryValidator.validate_workflow_contract(contract)
    assert len(errors) > 0
    assert any("workflow_id" in err for err in errors)


def test_workflow_contract_not_project_agnostic():
    """Test that non-project-agnostic contracts are rejected."""
    contract = WorkflowContract(
        workflow_id="test_workflow",
        workflow_type=WorkflowType.IMAGE,
        project_agnostic=False,  # Should be True
    )
    errors = WorkflowRegistryValidator.validate_workflow_contract(contract)
    assert len(errors) > 0
    assert any("project_agnostic" in err for err in errors)


def test_workflow_contract_hardcoded_rc2_multishot1_ep01():
    """Test that hardcoded rc2_multishot1_ep01 references are rejected."""
    contract = WorkflowContract(
        workflow_id="test_workflow",
        workflow_type=WorkflowType.IMAGE,
        project_agnostic=True,
        required_inputs=["data/rc2_multishot1_ep01/prompt"],  # Forbidden pattern
    )
    errors = WorkflowRegistryValidator.validate_workflow_contract(contract)
    assert len(errors) > 0
    assert any("rc2_multishot1_ep01" in err.lower() for err in errors)


def test_pipeline_blueprint_valid():
    """Test that a valid pipeline blueprint is accepted."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            )
        ],
        stage_order=["stage1"],
    )
    errors = WorkflowRegistryValidator.validate_pipeline_blueprint(blueprint)
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_pipeline_blueprint_missing_blueprint_id():
    """Test that missing blueprint_id is rejected."""
    blueprint = PipelineBlueprint(
        blueprint_id="",  # Missing blueprint_id
        stages=[],
        stage_order=[],
    )
    errors = WorkflowRegistryValidator.validate_pipeline_blueprint(blueprint)
    assert len(errors) > 0
    assert any("blueprint_id" in err for err in errors)


def test_pipeline_blueprint_stage_order_mismatch():
    """Test that stage_order referencing unknown stages is rejected."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            )
        ],
        stage_order=["stage1", "stage2"],  # stage2 doesn't exist
    )
    errors = WorkflowRegistryValidator.validate_pipeline_blueprint(blueprint)
    assert len(errors) > 0
    assert any("stage_order" in err for err in errors)


def test_reference_pack_valid():
    """Test that a valid reference pack is accepted."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE, ReferenceType.CHARACTER],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
                path=None,  # No actual image required
            )
        ],
        usage_policy={
            "allow_slot_description": True,
            "require_actual_images": False,
        },
    )
    errors = WorkflowRegistryValidator.validate_reference_pack(pack)
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_reference_pack_requires_actual_images():
    """Test that reference packs requiring actual images are rejected."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE],
        items=[],
        usage_policy={
            "allow_slot_description": True,
            "require_actual_images": True,  # Should be False in project-agnostic context
        },
    )
    errors = WorkflowRegistryValidator.validate_reference_pack(pack)
    assert len(errors) > 0
    assert any("require_actual_images" in err for err in errors)


def test_reference_pack_hardcoded_path():
    """Test that reference items with hardcoded episode-specific paths are rejected."""
    pack = ReferencePack(
        reference_pack_id="test_pack",
        project_binding_required=False,
        reference_types=[ReferenceType.STYLE],
        items=[
            ReferenceItem(
                reference_id="style1",
                reference_type=ReferenceType.STYLE,
                description="Style reference",
                path="data/rc2_multishot1_ep01/style.png",  # Forbidden pattern
            )
        ],
    )
    errors = WorkflowRegistryValidator.validate_reference_pack(pack)
    assert len(errors) > 0
    assert any("rc2_multishot1_ep01" in err.lower() for err in errors)


def test_execution_contract_dangerous_actions_blocked():
    """Test that execution contracts with dangerous actions unblocked are rejected."""
    contract = ExecutionContract(
        execution_id="test_exec",
        workflow_id="test_workflow",
        blueprint_id="test_blueprint",
        visual_qa_blocked=False,  # Should be True in project-agnostic context
    )
    errors = WorkflowRegistryValidator.validate_execution_contract(contract)
    assert len(errors) > 0
    assert any("visual_qa_blocked" in err for err in errors)


def test_execution_contract_production_accepted():
    """Test that execution contracts with production_accepted=True are rejected."""
    contract = ExecutionContract(
        execution_id="test_exec",
        workflow_id="test_workflow",
        blueprint_id="test_blueprint",
        production_accepted=True,  # Should be False
    )
    errors = WorkflowRegistryValidator.validate_execution_contract(contract)
    assert len(errors) > 0
    assert any("production_accepted" in err for err in errors)


def test_execution_contract_blind_retry_allowed():
    """Test that execution contracts with blind_retry_allowed=True are rejected."""
    contract = ExecutionContract(
        execution_id="test_exec",
        workflow_id="test_workflow",
        blueprint_id="test_blueprint",
        blind_retry_allowed=True,  # Should be False
    )
    errors = WorkflowRegistryValidator.validate_execution_contract(contract)
    assert len(errors) > 0
    assert any("blind_retry_allowed" in err for err in errors)


def test_workflow_registry_valid():
    """Test that a valid workflow registry is accepted."""
    registry = WorkflowRegistry(
        registry_id="test_registry",
        version="1.0.0",
        workflow_contracts={
            "test_workflow": WorkflowContract(
                workflow_id="test_workflow",
                workflow_type=WorkflowType.IMAGE,
                project_agnostic=True,
            )
        },
    )
    errors = WorkflowRegistryValidator.validate_workflow_registry(registry)
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_workflow_registry_missing_registry_id():
    """Test that missing registry_id is rejected."""
    registry = WorkflowRegistry(
        registry_id="",  # Missing registry_id
        version="1.0.0",
    )
    errors = WorkflowRegistryValidator.validate_workflow_registry(registry)
    assert len(errors) > 0
    assert any("registry_id" in err for err in errors)


def test_forbidden_runtime_actions():
    """Test that forbidden runtime actions are detected."""
    data = {
        "generation_performed": True,  # Forbidden
        "retry_attempted": False,
        "comfyui_submit_executed": False,
    }
    violations = WorkflowRegistryValidator.check_forbidden_runtime_actions(data)
    assert len(violations) > 0
    assert any("generation_performed" in v for v in violations)


def test_forbidden_runtime_actions_all_false():
    """Test that all forbidden runtime actions being false is accepted."""
    data = {
        "generation_performed": False,
        "retry_attempted": False,
        "comfyui_submit_executed": False,
        "preview_render_executed": False,
        "visual_qa_acceptance_executed": False,
        "operator_visual_acceptance_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
    }
    violations = WorkflowRegistryValidator.check_forbidden_runtime_actions(data)
    assert len(violations) == 0


def test_forbidden_patterns_detection():
    """Test that forbidden patterns are detected in data."""
    data = {
        "path": "data/rc2_multishot1_ep01/assets",
        "description": "Episode-specific data",
    }
    violations = WorkflowRegistryValidator.check_forbidden_patterns(data)
    assert len(violations) > 0
    assert any("rc2_multishot1_ep01" in v.lower() for v in violations)


def test_forbidden_patterns_clean_data():
    """Test that clean data passes forbidden pattern check."""
    data = {
        "path": "data/project/assets",
        "description": "Generic project data",
    }
    violations = WorkflowRegistryValidator.check_forbidden_patterns(data)
    assert len(violations) == 0


def test_validate_file_not_found():
    """Test that missing files are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = Path(tmpdir) / "nonexistent.json"
        result = WorkflowRegistryValidator.validate_file(nonexistent)
        assert result["valid"] is False
        assert len(result["errors"]) > 0


def test_validate_file_invalid_json():
    """Test that invalid JSON is rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_json = Path(tmpdir) / "invalid.json"
        invalid_json.write_text("{ invalid json }")
        result = WorkflowRegistryValidator.validate_file(invalid_json)
        assert result["valid"] is False
        assert len(result["errors"]) > 0


def test_validate_file_with_forbidden_patterns():
    """Test that files with forbidden patterns are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_with_patterns = Path(tmpdir) / "bad.json"
        file_with_patterns.write_text(
            json.dumps({"path": "data/rc2_multishot1_ep01/test.png"})
        )
        result = WorkflowRegistryValidator.validate_file(file_with_patterns)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
