"""
Test script for real VisionJudgeClient.
Tests the multimodal vision judge with a real image.
"""
import json
from pathlib import Path

from app.judges.base_types import JudgeInput
from app.judges.technical_judge import TechnicalJudge
from app.judges.semantic_judge import SemanticJudge
from app.judges.artistic_judge import ArtisticJudge
from app.judges.judge_orchestrator import JudgeOrchestrator
from app.judges.retry_controller import RetryController
from app.judges.vision_judge_client import VisionJudgeClient


def test_real_vision_client():
    """Test the real vision client with a sample image."""
    print("=" * 80)
    print("Real VisionJudgeClient Test")
    print("=" * 80)

    # Create a test image
    from PIL import Image
    test_image_path = Path("f:/ComfyUI/comfy-agent-mvp/data/outputs/test_vision_judge.png")
    test_image_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple test image (1024x1024 gradient)
    img = Image.new("RGB", (1024, 1024), color=(128, 128, 128))
    img.save(test_image_path)

    # Initialize real vision client
    try:
        vision_client = VisionJudgeClient(model="openai/gpt-4o")
        print(f"✓ VisionJudgeClient initialized with model: openai/gpt-4o")
    except Exception as exc:
        print(f"✗ Failed to initialize VisionJudgeClient: {exc}")
        print("Note: This requires OPENROUTER_API_KEY to be set in .env")
        return

    # Test semantic judge
    print("\n" + "-" * 80)
    print("Testing SemanticJudge with real vision client...")
    print("-" * 80)

    semantic_judge = SemanticJudge(vision_client=vision_client)
    
    judge_input = JudgeInput(
        user_prompt="Realistic portrait of a woman standing by a rainy window at night",
        final_positive_prompt="cinematic portrait, woman by rainy window, night, moody lighting, realistic, 8k, detailed",
        preset_name="sdxl_realistic",
        rewrite_mode="enhance",
        seed=12345,
        images=[],
        primary_image_path=str(test_image_path),
        width=1024,
        height=1024,
    )

    try:
        semantic_report = semantic_judge.evaluate(judge_input)
        print("\n--- SemanticJudge Report ---")
        print(json.dumps({
            "judge_name": semantic_report.judge_name,
            "score": semantic_report.score,
            "verdict": semantic_report.verdict,
            "blocking_issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in semantic_report.blocking_issues
            ],
            "issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in semantic_report.issues
            ],
            "strengths": semantic_report.strengths,
            "recommended_repairs": semantic_report.recommended_repairs,
            "subscores": semantic_report.subscores,
        }, indent=2))
        print("\n✓ SemanticJudge completed successfully")
    except Exception as exc:
        print(f"\n✗ SemanticJudge failed: {exc}")
        import traceback
        traceback.print_exc()
        return

    # Test artistic judge
    print("\n" + "-" * 80)
    print("Testing ArtisticJudge with real vision client...")
    print("-" * 80)

    artistic_judge = ArtisticJudge(vision_client=vision_client)

    try:
        artistic_report = artistic_judge.evaluate(judge_input)
        print("\n--- ArtisticJudge Report ---")
        print(json.dumps({
            "judge_name": artistic_report.judge_name,
            "score": artistic_report.score,
            "verdict": artistic_report.verdict,
            "blocking_issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in artistic_report.blocking_issues
            ],
            "issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in artistic_report.issues
            ],
            "strengths": artistic_report.strengths,
            "recommended_repairs": artistic_report.recommended_repairs,
            "subscores": artistic_report.subscores,
        }, indent=2))
        print("\n✓ ArtisticJudge completed successfully")
    except Exception as exc:
        print(f"\n✗ ArtisticJudge failed: {exc}")
        import traceback
        traceback.print_exc()
        return

    # Test full orchestrator
    print("\n" + "-" * 80)
    print("Testing full JudgeOrchestrator with real vision client...")
    print("-" * 80)

    technical_judge = TechnicalJudge()
    orchestrator = JudgeOrchestrator(
        technical_judge=technical_judge,
        semantic_judge=semantic_judge,
        artistic_judge=artistic_judge,
    )
    retry_controller = RetryController(max_retries=3)

    try:
        orchestrator_report = orchestrator.evaluate(judge_input)
        retry_decision = retry_controller.build_decision(orchestrator_report)
        
        print("\n--- OrchestratorReport ---")
        print(json.dumps({
            "final_score": orchestrator_report.final_score,
            "final_verdict": orchestrator_report.final_verdict,
            "best_next_action": orchestrator_report.best_next_action,
            "technical_score": orchestrator_report.technical.score,
            "semantic_score": orchestrator_report.semantic.score,
            "artistic_score": orchestrator_report.artistic.score,
        }, indent=2))
        
        print("\n--- RetryDecision ---")
        print(json.dumps({
            "action": retry_decision.action,
            "max_retries": retry_decision.max_retries,
            "suggested_prompt_suffixes": retry_decision.suggested_prompt_suffixes,
            "suggested_settings_updates": retry_decision.suggested_settings_updates,
            "notes": retry_decision.notes,
        }, indent=2))
        
        print("\n✓ Full judge pipeline completed successfully")
        print(f"\njudge_status: {orchestrator_report.final_verdict}")
        print(f"best_next_action: {orchestrator_report.best_next_action}")
        
    except Exception as exc:
        print(f"\n✗ JudgeOrchestrator failed: {exc}")
        import traceback
        traceback.print_exc()
        return

    # Cleanup
    test_image_path.unlink(missing_ok=True)

    print("\n" + "=" * 80)
    print("Real VisionJudgeClient test completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_real_vision_client()
