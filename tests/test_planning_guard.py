"""Tests for planning guard - fail-fast on missing required inputs."""

import pytest
from app.agent.task_selector import TaskSelector
from app.workflows.workflow_types import TaskType


@pytest.fixture
def task_selector():
    """Create task selector for testing."""
    return TaskSelector(llm_client=None)


def test_planning_guard_upscale_without_image(task_selector):
    """Scenario: upscale this image without image -> planning fail-fast."""
    task_selection = task_selector.select("upscale this image", assets=None)
    
    assert task_selection.task_type == TaskType.UPSCALE
    assert task_selection.missing_inputs == ["input_image"]
    assert task_selection.confidence >= 0.50  # Lower confidence due to missing image
    assert "input_image missing" in task_selection.reason.lower()


def test_planning_guard_fix_face_without_image(task_selector):
    """Scenario: fix face without image -> planning fail-fast."""
    task_selection = task_selector.select("fix face", assets=None)
    
    assert task_selection.task_type == TaskType.INPAINT_FACE
    assert task_selection.missing_inputs == ["input_image"]
    assert task_selection.confidence >= 0.50  # Lower confidence due to missing image
    assert "input_image missing" in task_selection.reason.lower()


def test_planning_guard_stylize_without_image(task_selector):
    """Scenario: stylize this image without image -> planning fail-fast."""
    task_selection = task_selector.select("stylize this image", assets=None)
    
    assert task_selection.task_type == TaskType.IMG2IMG
    assert task_selection.missing_inputs == ["input_image"]
    assert task_selection.confidence >= 0.50  # Lower confidence due to missing image
    assert "input_image missing" in task_selection.reason.lower()


def test_planning_guard_repair_eyes_without_mask(task_selector):
    """Scenario: repair eyes and skin with image but without mask -> task selector ok, planning may fail."""
    assets = {"input_image": "path/to/image.jpg"}  # Image present, no mask
    
    task_selection = task_selector.select("repair eyes and skin", assets=assets)
    
    # Task selector should identify inpaint_face with input_image present
    # Mask is optional for task selector, workflow spec may require it
    assert task_selection.task_type == TaskType.INPAINT_FACE
    assert "input_image" not in task_selection.missing_inputs  # Image is present
    # Task selector doesn't track mask as required (it's workflow-specific)


def test_planning_guard_make_better_without_image(task_selector):
    """Scenario: make this better without image -> selector unknown, no planning guard trigger."""
    task_selection = task_selector.select("make this better", assets=None)
    
    # Selector returns unknown with high ambiguity, no missing_inputs
    assert task_selection.task_type == TaskType.UNKNOWN
    assert task_selection.missing_inputs == []
    assert task_selection.ambiguity_level == "high"


def test_planning_guard_portrait_without_image(task_selector):
    """Scenario: portrait of a woman without image -> txt2img normal, no planning guard trigger."""
    task_selection = task_selector.select("portrait of a woman in soft light", assets=None)
    
    # txt2img doesn't require image, so no missing inputs
    assert task_selection.task_type in [TaskType.PORTRAIT_TXT2IMG, TaskType.CINEMATIC_TXT2IMG]
    assert task_selection.missing_inputs == []  # No missing inputs for txt2img


def test_planning_guard_upscale_with_image(task_selector):
    """Scenario: upscale this image with image present -> normal execution, no planning guard."""
    assets = {"input_image": "path/to/image.jpg"}
    
    task_selection = task_selector.select("upscale this image", assets=assets)
    
    # Should pass planning guard (no missing_inputs)
    assert task_selection.task_type == TaskType.UPSCALE
    assert task_selection.missing_inputs == []  # Image is present
    assert task_selection.confidence >= 0.85


def test_planning_guard_fix_face_with_image(task_selector):
    """Scenario: fix face with image present -> normal execution, no planning guard."""
    assets = {"input_image": "path/to/image.jpg"}
    
    task_selection = task_selector.select("fix face", assets=assets)
    
    # Should pass planning guard (no missing_inputs)
    assert task_selection.task_type == TaskType.INPAINT_FACE
    assert task_selection.missing_inputs == []  # Image is present
    assert task_selection.confidence >= 0.85


def test_planning_guard_with_mask_asset(task_selector):
    """Scenario: inpaint_face with both input_image and mask_image."""
    assets = {"input_image": "path/to/image.jpg", "mask_image": "path/to/mask.jpg"}
    
    task_selection = task_selector.select("repair eyes and skin", assets=assets)
    
    assert task_selection.task_type == TaskType.INPAINT_FACE
    assert task_selection.missing_inputs == []  # Both assets present
    assert task_selection.confidence >= 0.85


def test_planning_guard_result_structure():
    """Test that planning failure result has correct canonical contract format."""
    from app.agent.workflow_agent_service import WorkflowAgentService
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        workflows_dir = Path(tmp_dir) / "workflows"
        workflows_dir.mkdir()
        outputs_dir = Path(tmp_dir) / "outputs"
        outputs_dir.mkdir()
        presets_path = Path(tmp_dir) / "presets.json"
        presets_path.write_text("{}")
        
        agent_service = WorkflowAgentService(
            workflows_dir=workflows_dir,
            outputs_dir=outputs_dir,
            presets_path=presets_path,
            llm_client=None,
            enable_judging=False,
        )
        
        # Check task selection structure (selector layer)
        task_selection = agent_service.get_task_selection("upscale this image")
        assert task_selection.missing_inputs == ["input_image"]
        assert task_selection.required_inputs == ["input_image"]
        
        # Verify canonical contract fields would be present in failure result
        # (not testing actual execution since no workflow files)
        assert hasattr(task_selection, "task_type")
        assert hasattr(task_selection, "confidence")
        assert hasattr(task_selection, "reason")
        assert hasattr(task_selection, "routing_source")
        assert hasattr(task_selection, "required_inputs")
        assert hasattr(task_selection, "missing_inputs")
        assert hasattr(task_selection, "ambiguity_level")
        assert hasattr(task_selection, "safe_fallback_used")

