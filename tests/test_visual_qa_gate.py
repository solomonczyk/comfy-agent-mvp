"""
Tests for visual QA gate integration in ActionPlanBuilder.
"""
import json
import pytest
from pathlib import Path
from app.control.action_plan import ActionPlanBuilder
from app.control.models import ShotStateReport, ShotArtifacts


@pytest.fixture
def builder():
    """Return ActionPlanBuilder instance."""
    return ActionPlanBuilder()


@pytest.fixture
def base_report():
    """Return base ShotStateReport for testing."""
    return ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="frames_generated",
        next_action="assemble_scene",
        is_done=False,
        existing_artifacts=ShotArtifacts(
            brief_path="data/briefs/ep01_shot01_brief.md",
            generated_frames=["frame1.png"],
        ),
        frame_manifest_path="output/control/frames_manifest.json",
        project_root="data/test_project",
    )


def test_assemble_scene_denied_when_visual_qa_report_missing(builder, base_report, tmp_path):
    """Test 1: assemble_scene denied when visual_qa_report missing."""
    # Create project root without visual_qa_report.json
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / "output" / "control").mkdir(parents=True)
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "assemble_scene")
    
    assert not plan.allowed
    assert "visual qa report missing" in plan.reason.lower()


def test_assemble_scene_denied_when_needs_manual_review(builder, base_report, tmp_path):
    """Test 2: assemble_scene denied when visual_qa_report overall_verdict is needs_manual_review."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create visual_qa_report.json with needs_manual_review verdict
    qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "needs_manual_review",
        "total_frames": 3,
        "passed_frames": 0,
        "failed_frames": 0,
        "needs_review_frames": 3,
        "evaluations": []
    }
    
    with open(control_dir / "visual_qa_report.json", "w") as f:
        json.dump(qa_report, f)
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "assemble_scene")
    
    assert not plan.allowed
    assert "visual qa not passed" in plan.reason.lower()
    assert "needs_manual_review" in plan.reason.lower()


def test_assemble_scene_denied_when_fail(builder, base_report, tmp_path):
    """Test 3: assemble_scene denied when visual_qa_report overall_verdict is fail."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create visual_qa_report.json with fail verdict
    qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "fail",
        "total_frames": 3,
        "passed_frames": 0,
        "failed_frames": 3,
        "needs_review_frames": 0,
        "evaluations": []
    }
    
    with open(control_dir / "visual_qa_report.json", "w") as f:
        json.dump(qa_report, f)
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "assemble_scene")
    
    assert not plan.allowed
    assert "visual qa not passed" in plan.reason.lower()
    assert "fail" in plan.reason.lower()


def test_assemble_scene_allowed_when_pass(builder, base_report, tmp_path):
    """Test 4: assemble_scene allowed when visual_qa_report overall_verdict is pass."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create visual_qa_report.json with pass verdict
    qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "pass",
        "total_frames": 3,
        "passed_frames": 3,
        "failed_frames": 0,
        "needs_review_frames": 0,
        "evaluations": []
    }
    
    with open(control_dir / "visual_qa_report.json", "w") as f:
        json.dump(qa_report, f)
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "assemble_scene")
    
    assert plan.allowed
    assert plan.action == "assemble_scene"


def test_generate_frames_not_affected_by_visual_qa_gate(builder, base_report, tmp_path):
    """Test 5: generate_frames behavior is not affected by visual QA gate."""
    # Set current state to ready_for_generation
    base_report.current_state = "ready_for_generation"
    base_report.next_action = "generate_frames"
    
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create visual_qa_report.json with fail verdict (should not affect generate_frames)
    qa_report = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "overall_verdict": "fail",
        "total_frames": 3,
        "passed_frames": 0,
        "failed_frames": 3,
        "needs_review_frames": 0,
        "evaluations": []
    }
    
    with open(control_dir / "visual_qa_report.json", "w") as f:
        json.dump(qa_report, f)
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    # generate_frames should be allowed regardless of visual QA status
    assert plan.allowed
    assert plan.action == "generate_frames"


def test_prompt_pack_does_not_hardcode_euler_simple():
    """Test 6: prompt_pack does not hardcode euler/simple."""
    prompt_pack_path = Path("data/real_ep01_pilot_r6/output/control/prompt_pack.json")
    
    if not prompt_pack_path.exists():
        pytest.skip("prompt_pack.json not found")
    
    with open(prompt_pack_path, "r") as f:
        prompt_pack = json.load(f)
    
    for beat in prompt_pack.get("beats", []):
        sampler = beat.get("sampler")
        scheduler = beat.get("scheduler")
        
        assert sampler != "euler", f"Beat {beat.get('beat_id')} uses hardcoded euler sampler"
        assert scheduler != "simple", f"Beat {beat.get('beat_id')} uses hardcoded simple scheduler"


def test_prompt_pack_uses_deterministic_seed_policy():
    """Test 7: prompt_pack uses deterministic seed policy, not random."""
    prompt_pack_path = Path("data/real_ep01_pilot_r6/output/control/prompt_pack.json")
    
    if not prompt_pack_path.exists():
        pytest.skip("prompt_pack.json not found")
    
    with open(prompt_pack_path, "r") as f:
        prompt_pack = json.load(f)
    
    for beat in prompt_pack.get("beats", []):
        seed_policy = beat.get("seed_policy")
        
        # Should not be "random" string
        assert seed_policy != "random", f"Beat {beat.get('beat_id')} uses random seed policy"
        
        # Should be a dict with deterministic structure
        assert isinstance(seed_policy, dict), f"Beat {beat.get('beat_id')} seed_policy is not a dict"
        assert seed_policy.get("mode") == "deterministic_per_shot", f"Beat {beat.get('beat_id')} seed_policy mode is not deterministic_per_shot"
        assert "character_seed" in seed_policy, f"Beat {beat.get('beat_id')} seed_policy missing character_seed"
        assert "beat_seed_offset" in seed_policy, f"Beat {beat.get('beat_id')} seed_policy missing beat_seed_offset"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
