"""Tests for task selector."""

import pytest

from app.agent.task_selector import TaskSelector, TaskSelectionResult
from app.workflows.workflow_types import TaskType


@pytest.fixture
def selector():
    """Create a test task selector without LLM."""
    return TaskSelector(llm_client=None)


def test_select_portrait_prompt(selector):
    """Test selecting task type for portrait prompt."""
    result = selector.select("cinematic portrait of a woman in soft window light")
    assert result.task_type in [TaskType.PORTRAIT_TXT2IMG, TaskType.CINEMATIC_TXT2IMG]
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"
    assert result.required_inputs == []
    assert result.ambiguity_level == "low"


def test_select_product_prompt(selector):
    """Test selecting task type for product prompt."""
    result = selector.select("luxury product shot of a perfume bottle on reflective black surface")
    assert result.task_type == TaskType.PRODUCT_TXT2IMG
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"
    assert result.required_inputs == []


def test_select_fashion_prompt(selector):
    """Test selecting task type for fashion prompt."""
    result = selector.select("high fashion editorial model, premium studio look")
    assert result.task_type == TaskType.FASHION_TXT2IMG
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"
    assert result.required_inputs == []


def test_select_upscale_prompt_with_image(selector):
    """Test selecting task type for upscale prompt with image."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("upscale this image to high detail", assets)
    assert result.task_type == TaskType.UPSCALE
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "upscale" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == []


def test_select_upscale_prompt_without_image(selector):
    """Test selecting task type for upscale prompt without image."""
    result = selector.select("upscale this image to high detail")
    assert result.task_type == TaskType.UPSCALE
    assert result.confidence < 0.85  # Should be penalized for missing image
    assert "input_image missing" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == ["input_image"]


def test_select_inpaint_face_prompt_with_image(selector):
    """Test selecting task type for inpaint face prompt with image."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("repair face and fix eye artifacts", assets)
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "face-repair" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == []


def test_select_inpaint_face_prompt_without_image(selector):
    """Test selecting task type for inpaint face prompt without image."""
    result = selector.select("repair face and fix eye artifacts")
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.50  # Should still route with strong intent
    assert "input_image missing" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == ["input_image"]


def test_select_img2img_prompt_with_image(selector):
    """Test selecting task type for img2img prompt with image."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("stylize this image", assets)
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "image-edit" in result.reason.lower()
    assert result.required_inputs == ["input_image"]


def test_select_img2img_prompt_without_image(selector):
    """Test selecting task type for img2img prompt without image."""
    result = selector.select("stylize this image")
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.50  # Should still route with strong intent
    assert "input_image missing" in result.reason.lower()


def test_select_vague_prompt_with_image(selector):
    """Test selecting task type for vague prompt with image (safe fallback)."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("make this better", assets)
    # Should safe fallback to img2img
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.45
    assert result.ambiguity_level == "medium"
    assert result.safe_fallback_used == True
    assert "safe fallback" in result.reason.lower()


def test_select_vague_prompt_without_image(selector):
    """Test selecting task type for vague prompt without image (controlled failure)."""
    result = selector.select("make this better")
    assert result.task_type == TaskType.UNKNOWN
    assert result.confidence < 0.45
    assert result.ambiguity_level == "high"
    # Should have either "without input image" or "controlled failure" in reason
    reason_lower = result.reason.lower()
    assert "without input image" in reason_lower or "controlled failure" in reason_lower


def test_select_vague_prompt_with_image_and_upscale_signal(selector):
    """Test vague prompt with image and explicit upscale signal."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("make this better, upscale it", assets)
    assert result.task_type == TaskType.UPSCALE
    assert result.ambiguity_level == "low"
    assert "detected upscale intent" in result.reason.lower()


def test_select_vague_prompt_with_image_and_face_signal(selector):
    """Test vague prompt with image and explicit face repair signal."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("make this better, fix face", assets)
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.ambiguity_level == "low"
    assert "detected face-repair intent" in result.reason.lower()


def test_select_cinematic_prompt(selector):
    """Test selecting task type for cinematic prompt."""
    result = selector.select("epic cinematic scene with dramatic lighting")
    assert result.task_type == TaskType.CINEMATIC_TXT2IMG
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"


def test_select_unknown_prompt(selector):
    """Test selecting task type for unknown/unclear prompt."""
    result = selector.select("generate something nice")
    assert result.task_type == TaskType.UNKNOWN
    assert result.confidence <= 0.2  # Can be 0.0 or 0.2 depending on path
    assert result.routing_source == "rules"


def test_select_case_insensitive(selector):
    """Test that selection is case insensitive."""
    result1 = selector.select("PORTRAIT of a person")
    result2 = selector.select("portrait of a person")
    assert result1.task_type == result2.task_type


def test_select_multiple_keywords(selector):
    """Test selection with multiple matching keywords."""
    result = selector.select("cinematic portrait of a woman")
    # Should select one of the matching types based on priority
    assert result.task_type in [TaskType.PORTRAIT_TXT2IMG, TaskType.CINEMATIC_TXT2IMG]
    assert result.confidence >= 0.6


def test_priority_order_upscale_vs_img2img(selector):
    """Test that upscale has higher priority than img2img."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("upscale and stylize this image", assets)
    # Upscale should win due to priority
    assert result.task_type == TaskType.UPSCALE
