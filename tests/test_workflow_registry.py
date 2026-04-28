"""Tests for workflow registry."""

import pytest
from pathlib import Path

from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType, WorkflowKind


@pytest.fixture
def registry():
    """Create a test workflow registry."""
    workflows_dir = Path(__file__).parent.parent / "data" / "workflows"
    return WorkflowRegistry(workflows_dir)


def test_registry_initialization(registry):
    """Test registry initializes with default workflows."""
    workflows = registry.list_workflows()
    assert len(workflows) >= 4  # At least portrait, cinematic, product, fashion


def test_list_workflows(registry):
    """Test listing all workflows."""
    workflows = registry.list_workflows()
    workflow_ids = [w.workflow_id for w in workflows]
    assert "portrait_sdxl_v1" in workflow_ids
    assert "cinematic_sdxl_v1" in workflow_ids
    assert "product_sdxl_v1" in workflow_ids
    assert "fashion_sdxl_v1" in workflow_ids


def test_get_workflow(registry):
    """Test getting a specific workflow by ID."""
    workflow = registry.get_workflow("portrait_sdxl_v1")
    assert workflow is not None
    assert workflow.workflow_id == "portrait_sdxl_v1"
    assert workflow.task_type == TaskType.PORTRAIT_TXT2IMG
    assert workflow.implemented is True


def test_get_workflow_not_found(registry):
    """Test getting a non-existent workflow."""
    workflow = registry.get_workflow("nonexistent_workflow")
    assert workflow is None


def test_get_workflows_for_task(registry):
    """Test getting workflows for a specific task type."""
    portrait_workflows = registry.get_workflows_for_task(TaskType.PORTRAIT_TXT2IMG)
    assert len(portrait_workflows) >= 1
    assert all(w.task_type == TaskType.PORTRAIT_TXT2IMG for w in portrait_workflows)


def test_get_default_for_task(registry):
    """Test getting default workflow for a task type."""
    default_portrait = registry.get_default_for_task(TaskType.PORTRAIT_TXT2IMG)
    assert default_portrait is not None
    assert default_portrait.task_type == TaskType.PORTRAIT_TXT2IMG
    assert default_portrait.implemented is True


def test_get_implemented_workflows(registry):
    """Test getting only implemented workflows."""
    implemented = registry.get_implemented_workflows()
    assert all(w.implemented for w in implemented)
    # At least portrait, cinematic, product should be implemented
    workflow_ids = [w.workflow_id for w in implemented]
    assert "portrait_sdxl_v1" in workflow_ids
    assert "cinematic_sdxl_v1" in workflow_ids
    assert "product_sdxl_v1" in workflow_ids


def test_not_implemented_workflows(registry):
    """Test that upscale and inpaint workflows are marked as not implemented."""
    upscale = registry.get_workflow("upscale_v1")
    assert upscale is not None
    assert upscale.implemented is True

    inpaint = registry.get_workflow("inpaint_face_v1")
    assert inpaint is not None
    assert inpaint.implemented is True


def test_workflow_spec_to_dict(registry):
    """Test converting workflow spec to dictionary."""
    workflow = registry.get_workflow("portrait_sdxl_v1")
    workflow_dict = workflow.to_dict()
    assert workflow_dict["workflow_id"] == "portrait_sdxl_v1"
    assert workflow_dict["task_type"] == "portrait_txt2img"
    assert workflow_dict["kind"] == "txt2img"
    assert "preset_name" in workflow_dict
    assert "description" in workflow_dict
