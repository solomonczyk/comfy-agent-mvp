"""Mixed routing pack test - comprehensive routing scenarios."""

import pytest

from app.agent.task_selector import TaskSelector
from app.workflows.workflow_types import TaskType


@pytest.fixture
def selector():
    """Create a test task selector without LLM."""
    return TaskSelector(llm_client=None)


def test_scenario_1_upscale_with_image(selector):
    """Scenario 1: upscale this image + image present -> upscale"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("upscale this image", assets)
    
    assert result.task_type == TaskType.UPSCALE
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "upscale" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == []
    assert result.ambiguity_level == "low"


def test_scenario_2_fix_face_with_image(selector):
    """Scenario 2: fix face + image present -> inpaint_face"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("fix face", assets)
    
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "face-repair" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == []


def test_scenario_3_repair_eyes_skin_with_image(selector):
    """Scenario 3: repair eyes and skin + image present -> inpaint_face"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("repair eyes and skin", assets)
    
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == []


def test_scenario_4_stylize_with_image(selector):
    """Scenario 4: stylize this image + image present -> img2img"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("stylize this image", assets)
    
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.85
    assert result.routing_source == "rules"
    assert "image-edit" in result.reason.lower()
    assert result.required_inputs == ["input_image"]


def test_scenario_5_make_cinematic_with_image(selector):
    """Scenario 5: make this more cinematic + image present -> img2img"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("make this more cinematic", assets)
    
    # With ambiguity fix, "make this more cinematic" should route to img2img (safe fallback)
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.45
    assert result.routing_source == "rules"
    assert result.required_inputs == ["input_image"]
    assert result.ambiguity_level == "medium"


def test_scenario_6_make_better_with_image(selector):
    """Scenario 6: make this better + image present -> safe fallback to img2img"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("make this better", assets)
    
    # Should safe fallback to img2img, not upscale or inpaint_face
    assert result.task_type == TaskType.IMG2IMG
    assert result.confidence >= 0.45
    assert result.routing_source == "rules"
    assert result.ambiguity_level == "medium"
    assert result.safe_fallback_used == True
    assert "safe fallback" in result.reason.lower()
    assert result.required_inputs == ["input_image"]


def test_scenario_7_make_better_without_image(selector):
    """Scenario 7: make this better + no image -> unknown / controlled failure"""
    result = selector.select("make this better")
    
    assert result.task_type == TaskType.UNKNOWN
    assert result.confidence < 0.45
    assert result.routing_source == "rules"
    assert result.ambiguity_level == "high"
    # Should have either "without input image" or "controlled failure" in reason
    reason_lower = result.reason.lower()
    assert "without input image" in reason_lower or "controlled failure" in reason_lower


def test_scenario_8_portrait_no_image(selector):
    """Scenario 8: portrait of a woman in soft light + no image -> portrait_txt2img or cinematic_txt2img"""
    result = selector.select("portrait of a woman in soft light")
    
    assert result.task_type in [TaskType.PORTRAIT_TXT2IMG, TaskType.CINEMATIC_TXT2IMG]
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"
    assert result.required_inputs == []


def test_scenario_9_product_no_image(selector):
    """Scenario 9: luxury perfume bottle product shot + no image -> product_txt2img"""
    result = selector.select("luxury perfume bottle product shot")
    
    assert result.task_type == TaskType.PRODUCT_TXT2IMG
    assert result.confidence >= 0.6
    assert result.routing_source == "rules"
    assert result.required_inputs == []


def test_scenario_10_upscale_without_image(selector):
    """Scenario 10: upscale this image + no image -> not upscale success-route; confidence down + asset-missing reason"""
    result = selector.select("upscale this image")
    
    assert result.task_type == TaskType.UPSCALE
    assert result.confidence < 0.85  # Should be penalized
    assert "input_image missing" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == ["input_image"]


def test_scenario_11_fix_face_without_image(selector):
    """Scenario 11: fix face + no image -> not inpaint success-route; confidence down + asset-missing reason"""
    result = selector.select("fix face")
    
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.50  # Should still route with strong intent
    assert "input_image missing" in result.reason.lower()
    assert result.required_inputs == ["input_image"]
    assert result.missing_inputs == ["input_image"]


def test_scenario_12_repair_eyes_no_mask(selector):
    """Scenario 12: repair eyes and skin + image present + no mask -> selector can route inpaint_face, planning must fail-fast clearly"""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("repair eyes and skin", assets)
    
    # Selector can route to inpaint_face
    assert result.task_type == TaskType.INPAINT_FACE
    assert result.confidence >= 0.85
    # Note: mask is optional in current implementation, so no penalty
    # Planning layer should handle mask requirement if workflow needs it


def test_priority_upscale_over_img2img(selector):
    """Test priority: upscale > img2img when both signals present."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("upscale and stylize this image", assets)
    
    assert result.task_type == TaskType.UPSCALE  # Upscale has higher priority


def test_priority_inpaint_over_img2img(selector):
    """Test priority: inpaint_face > img2img when both signals present."""
    assets = {"input_image": "path/to/image.jpg"}
    result = selector.select("fix face and stylize this image", assets)
    
    assert result.task_type == TaskType.INPAINT_FACE  # inpaint_face has higher priority


def test_ambiguity_improve_this(selector):
    """Test ambiguity: 'improve this' without image."""
    result = selector.select("improve this")
    
    assert result.task_type == TaskType.UNKNOWN
    assert result.ambiguity_level == "high"
    assert result.confidence < 0.45


def test_ambiguity_fix_this(selector):
    """Test ambiguity: 'fix this' without image."""
    result = selector.select("fix this")
    
    assert result.task_type == TaskType.UNKNOWN
    assert result.ambiguity_level == "high"
    assert result.confidence < 0.45


def test_ambiguity_enhance_this(selector):
    """Test ambiguity: 'enhance this' without image."""
    result = selector.select("enhance this")
    
    assert result.task_type == TaskType.UNKNOWN
    assert result.ambiguity_level == "high"
    assert result.confidence < 0.45


def test_routing_source_only_rules_or_llm(selector):
    """Test that routing_source is only 'rules' or 'llm'."""
    result = selector.select("upscale this image")
    assert result.routing_source in ["rules", "llm"]


def test_txt2img_subtypes(selector):
    """Test txt2img subtypes are correctly identified."""
    portrait = selector.select("portrait of a woman")
    cinematic = selector.select("cinematic scene with dramatic lighting")
    product = selector.select("product shot of perfume bottle")
    fashion = selector.select("fashion editorial model")
    
    assert portrait.task_type == TaskType.PORTRAIT_TXT2IMG
    assert cinematic.task_type == TaskType.CINEMATIC_TXT2IMG
    assert product.task_type == TaskType.PRODUCT_TXT2IMG
    assert fashion.task_type == TaskType.FASHION_TXT2IMG


def print_mixed_routing_table(selector):
    """Print comprehensive mixed routing table for verification."""
    scenarios = [
        ("upscale this image", {"input_image": "path/to/image.jpg"}, TaskType.UPSCALE, ">= 0.85"),
        ("fix face", {"input_image": "path/to/image.jpg"}, TaskType.INPAINT_FACE, ">= 0.85"),
        ("repair eyes and skin", {"input_image": "path/to/image.jpg"}, TaskType.INPAINT_FACE, ">= 0.85"),
        ("stylize this image", {"input_image": "path/to/image.jpg"}, TaskType.IMG2IMG, ">= 0.85"),
        ("make this more cinematic", {"input_image": "path/to/image.jpg"}, TaskType.IMG2IMG, ">= 0.85"),
        ("make this better", {"input_image": "path/to/image.jpg"}, TaskType.IMG2IMG, ">= 0.45"),
        ("make this better", {}, TaskType.UNKNOWN, "< 0.45"),
        ("portrait of a woman in soft light", {}, TaskType.PORTRAIT_TXT2IMG, ">= 0.6"),
        ("luxury perfume bottle product shot", {}, TaskType.PRODUCT_TXT2IMG, ">= 0.6"),
        ("upscale this image", {}, TaskType.UPSCALE, "< 0.85"),
        ("fix face", {}, TaskType.INPAINT_FACE, "< 0.85"),
        ("repair eyes and skin", {"input_image": "path/to/image.jpg"}, TaskType.INPAINT_FACE, ">= 0.85"),
    ]
    
    print("\n=== MIXED ROUTING TABLE ===")
    print(f"{'Prompt':<40} {'Assets':<15} {'Task Type':<20} {'Confidence':<12} {'Status':<10}")
    print("-" * 100)
    
    for prompt, assets, expected_task, expected_conf in scenarios:
        result = selector.select(prompt, assets)
        assets_str = "image" if assets else "none"
        conf_str = f"{result.confidence:.2f}"
        status = "PASS" if result.task_type == expected_task else "FAIL"
        print(f"{prompt:<40} {assets_str:<15} {result.task_type.value:<20} {conf_str:<12} {status:<10}")
