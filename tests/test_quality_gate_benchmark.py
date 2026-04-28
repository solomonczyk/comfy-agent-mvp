"""Quality Gate Benchmark Tests.

Tests for quality gate functionality including:
- Hard reject rules (black frames, semantic collapse, facial defects)
- Quality scorecard with 4 axes
- Acceptance thresholds
- Defect taxonomy
- Defect → corrective action mapping
- Quality report persistence
"""

from app.judges.judge_orchestrator import QualityScorecard, QualityReport, PortraitQualityProfile


def test_quality_scorecard_weighted_score():
    """Test quality scorecard weighted score calculation."""
    scorecard = QualityScorecard(
        technical_score=8,
        anatomy_score=9,
        semantic_score=8,
        aesthetic_score=7,
    )
    # Expected: (8*0.2) + (9*0.3) + (8*0.3) + (7*0.2) = 1.6 + 2.7 + 2.4 + 1.4 = 8.1
    assert abs(scorecard.weighted_score - 8.1) < 0.01
    print("PASS: Quality scorecard weighted score calculation")


def test_portrait_quality_profile_thresholds():
    """Test portrait quality profile thresholds."""
    profile = PortraitQualityProfile()
    
    # Check hard reject codes
    assert "black_frame" in profile.HARD_REJECT_CODES
    assert "eye_geometry_broken" in profile.HARD_REJECT_CODES
    
    # Check score thresholds
    assert profile.MIN_TECHNICAL_SCORE == 7
    assert profile.MIN_ANATOMY_SCORE == 8
    assert profile.MIN_SEMANTIC_SCORE == 8
    assert profile.MIN_AESTHETIC_SCORE == 7
    assert profile.MIN_WEIGHTED_SCORE == 7.5
    
    print("PASS: Portrait quality profile thresholds")


def test_quality_report_serialization():
    """Test quality report serialization to dict."""
    scorecard = QualityScorecard(
        technical_score=8,
        anatomy_score=9,
        semantic_score=8,
        aesthetic_score=7,
    )
    
    report = QualityReport(
        quality_profile="portrait_premium_v1",
        verdict="accept",
        scorecard=scorecard,
        hard_fail_reasons=[],
        soft_fail_reasons=["weak_aesthetic"],
        recommended_corrective_action="retry_seed",
    )
    
    report_dict = report.to_dict()
    assert report_dict["quality_profile"] == "portrait_premium_v1"
    assert report_dict["verdict"] == "accept"
    assert report_dict["scorecard"]["technical_score"] == 8
    assert report_dict["scorecard"]["weighted_score"] == 8.1
    assert report_dict["soft_fail_reasons"] == ["weak_aesthetic"]
    assert report_dict["recommended_corrective_action"] == "retry_seed"
    
    print("PASS: Quality report serialization")


def test_defect_to_action_mapping():
    """Test defect to corrective action mapping."""
    from app.judges.judge_orchestrator import JudgeOrchestrator
    
    orchestrator = JudgeOrchestrator(
        technical_judge=None,
        semantic_judge=None,
        artistic_judge=None,
        quality_profile="portrait_premium_v1",
    )
    
    # Test critical defects
    assert orchestrator._map_defect_to_action("black_frame") == "reject"
    assert orchestrator._map_defect_to_action("semantic_collapse") == "retry_prompt"
    assert orchestrator._map_defect_to_action("eye_geometry_broken") == "reject"
    
    # Test soft defects
    assert orchestrator._map_defect_to_action("plastic_skin") == "retry_settings"
    assert orchestrator._map_defect_to_action("weak_aesthetic") == "retry_seed"
    
    print("PASS: Defect to action mapping")


def test_hard_reject_detection():
    """Test black frame detection in technical judge."""
    from app.judges.technical_judge import TechnicalJudge
    from app.judges.base_types import JudgeInput
    from PIL import Image
    
    # Create a black image for testing
    black_image = Image.new("RGB", (512, 512), (0, 0, 0))
    
    # Save to temp file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        black_image.save(f.name)
        black_image_path = f.name
    
    try:
        judge = TechnicalJudge()
        judge_input = JudgeInput(
            user_prompt="test",
            final_positive_prompt="test",
            preset_name=None,
            rewrite_mode=None,
            seed=123,
            images=[],
            primary_image_path=black_image_path,
            width=512,
            height=512,
        )
        
        report = judge.evaluate(judge_input)
        
        # Check that black_frame was detected as blocking issue
        blocking_codes = [issue.code for issue in report.blocking_issues]
        assert "black_frame" in blocking_codes
        assert report.verdict == "reject"
        
        print("PASS: Black frame detection")
    finally:
        import os
        if os.path.exists(black_image_path):
            os.remove(black_image_path)


if __name__ == "__main__":
    print("Running Quality Gate Benchmark Tests...")
    print()
    
    test_quality_scorecard_weighted_score()
    test_portrait_quality_profile_thresholds()
    test_quality_report_serialization()
    test_defect_to_action_mapping()
    test_hard_reject_detection()
    
    print()
    print("="*60)
    print("All benchmark tests PASSED")
    print("="*60)
