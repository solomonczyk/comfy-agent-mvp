"""Tests for execution plan."""

import pytest

from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.task_selector import TaskSelectionResult
from app.workflows.workflow_types import TaskType


@pytest.fixture
def task_selection():
    """Create a test task selection result."""
    return TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=0.8,
        reason="Matched keywords: portrait, woman",
        routing_source="rules",
    )


@pytest.fixture
def plan_builder():
    """Create a test execution plan builder."""
    return ExecutionPlanBuilder()


def test_build_execution_plan(plan_builder, task_selection):
    """Test building an execution plan."""
    plan = plan_builder.build(
        user_prompt="cinematic portrait of a woman",
        task_selection=task_selection,
        workflow_id="portrait_sdxl_v1",
        workflow_path="/path/to/workflow.json",
        preset_name="portrait",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={"prompt": "cinematic portrait of a woman"},
        enable_judging=True,
        enable_retry_loop=True,
    )

    assert plan.user_prompt == "cinematic portrait of a woman"
    assert plan.task_type == TaskType.PORTRAIT_TXT2IMG
    assert plan.workflow_id == "portrait_sdxl_v1"
    assert plan.workflow_path == "/path/to/workflow.json"
    assert plan.preset_name == "portrait"
    assert plan.rewrite_mode == "fallback"
    assert plan.required_inputs == ["prompt"]
    assert plan.resolved_inputs == {"prompt": "cinematic portrait of a woman"}
    assert plan.enable_judging is True
    assert plan.enable_retry_loop is True


def test_execution_plan_to_dict(plan_builder, task_selection):
    """Test converting execution plan to dictionary."""
    plan = plan_builder.build(
        user_prompt="test prompt",
        task_selection=task_selection,
        workflow_id="portrait_sdxl_v1",
        workflow_path="/path/to/workflow.json",
        preset_name="portrait",
        rewrite_mode="fallback",
        required_inputs=["prompt"],
        resolved_inputs={"prompt": "test prompt"},
        enable_judging=True,
        enable_retry_loop=True,
    )

    plan_dict = plan.to_dict()
    assert plan_dict["user_prompt"] == "test prompt"
    assert plan_dict["task_type"] == "portrait_txt2img"
    assert plan_dict["workflow_id"] == "portrait_sdxl_v1"
    assert plan_dict["enable_judging"] is True
    assert plan_dict["enable_retry_loop"] is True


def test_plan_builder_add_note(plan_builder):
    """Test adding notes to plan builder."""
    plan_builder.add_note("Note 1")
    plan_builder.add_note("Note 2")

    task_selection = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=0.8,
        reason="Test",
        routing_source="rules",
    )

    plan = plan_builder.build(
        user_prompt="test",
        task_selection=task_selection,
        workflow_id="test",
        workflow_path="/test.json",
        preset_name="test",
        rewrite_mode="raw",
        required_inputs=[],
        resolved_inputs={},
        enable_judging=False,
        enable_retry_loop=False,
    )

    assert len(plan.notes) == 2
    assert "Note 1" in plan.notes
    assert "Note 2" in plan.notes


def test_plan_builder_notes_cleared_after_build(plan_builder):
    """Test that notes are cleared after building a plan."""
    plan_builder.add_note("Note 1")

    task_selection = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=0.8,
        reason="Test",
        routing_source="rules",
    )

    plan1 = plan_builder.build(
        user_prompt="test1",
        task_selection=task_selection,
        workflow_id="test",
        workflow_path="/test.json",
        preset_name="test",
        rewrite_mode="raw",
        required_inputs=[],
        resolved_inputs={},
        enable_judging=False,
        enable_retry_loop=False,
    )

    assert len(plan1.notes) == 1

    # Build another plan without adding notes
    plan2 = plan_builder.build(
        user_prompt="test2",
        task_selection=task_selection,
        workflow_id="test",
        workflow_path="/test.json",
        preset_name="test",
        rewrite_mode="raw",
        required_inputs=[],
        resolved_inputs={},
        enable_judging=False,
        enable_retry_loop=False,
    )

    assert len(plan2.notes) == 0


def test_execution_plan_with_disabled_features(plan_builder, task_selection):
    """Test execution plan with judging and retry disabled."""
    plan = plan_builder.build(
        user_prompt="test",
        task_selection=task_selection,
        workflow_id="test",
        workflow_path="/test.json",
        preset_name="test",
        rewrite_mode="raw",
        required_inputs=[],
        resolved_inputs={},
        enable_judging=False,
        enable_retry_loop=False,
    )

    assert plan.enable_judging is False
    assert plan.enable_retry_loop is False
