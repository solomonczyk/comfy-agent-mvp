"""
Tests for reference lock gate integration in ActionPlanBuilder for generate_frames.
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
        current_state="ready_for_generation",
        next_action="generate_frames",
        is_done=False,
        existing_artifacts=ShotArtifacts(
            brief_path="data/briefs/ep01_shot01_brief.md",
        ),
        project_root=None,  # Will be set in tests
    )


def create_popadanka_project_structure(project_root: Path):
    """Create the Popadanka/Erdan project structure with required artifacts."""
    # Create directory structure
    control_dir = project_root / "output" / "control"
    reference_locks_dir = control_dir / "reference_locks"
    control_dir.mkdir(parents=True)
    reference_locks_dir.mkdir()
    
    # Create project_profile.json
    project_profile = {
        "project_id": "popadanka_erdan",
        "title": "Попаданка / Erdan",
        "source_root": "F:\\VideoProjects\\МИР\\Эрдан",
        "default_aspect_ratio": "9:16",
        "safe_resolution": {"width": 480, "height": 640},
        "generation_policy": {
            "require_kb_ready": True,
            "require_reference_lock_for_main_characters": True,
            "allow_prompt_only_for_background_characters": False
        }
    }
    (control_dir / "project_profile.json").write_text(json.dumps(project_profile), encoding='utf-8')
    
    # Create character_registry.json
    character_registry = {
        "characters": [
            {
                "character_id": "alya",
                "name": "Аля",
                "role": "protagonist",
                "reference_required": True,
                "status": "approved"
            },
            {
                "character_id": "kael",
                "name": "Kael",
                "role": "main_character",
                "reference_required": True,
                "status": "missing"
            }
        ]
    }
    (control_dir / "character_registry.json").write_text(json.dumps(character_registry), encoding='utf-8')
    
    # Create Alya reference lock
    alya_lock = {
        "character_id": "alya",
        "reference_lock_status": "approved",
        "downstream_generation_allowed": True,
        "approved_references": ["ref_alya_main"],
        "primary_identity_reference": {
            "reference_id": "ref_alya_main",
            "filename": "референсы/Аля.png",
            "type": "reference_sheet",
            "approved_for": ["identity", "face"]
        },
        "prompt_anchor_en": "24-year-old woman, dark brown hair in messy bun"
    }
    (reference_locks_dir / "alya_reference_lock.json").write_text(json.dumps(alya_lock), encoding='utf-8')


def test_generate_frames_allowed_for_prompt_pack_with_only_alya_and_approved_lock(builder, base_report, tmp_path):
    """Test 1: generate_frames allowed for prompt_pack with only Alya and approved Alya lock."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with only Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.allowed
    assert plan.action == "generate_frames"
    assert "reference lock gate" not in plan.reason.lower() or "approved" in plan.reason.lower()


def test_generate_frames_denied_for_prompt_pack_with_kael_missing_lock(builder, base_report, tmp_path):
    """Test 2: generate_frames denied for prompt_pack with Kael missing lock."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Kael (missing lock)
    prompt_pack = {
        "characters": ["kael"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "reference lock gate" in plan.reason.lower()
    assert "kael" in plan.reason.lower() or "missing" in plan.reason.lower()


def test_generate_frames_denied_for_prompt_pack_with_alya_plus_kael(builder, base_report, tmp_path):
    """Test 3: generate_frames denied for prompt_pack with Alya + Kael."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with both Alya and Kael
    prompt_pack = {
        "characters": ["alya", "kael"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "reference lock gate" in plan.reason.lower()
    assert "kael" in plan.reason.lower() or "missing" in plan.reason.lower()


def test_generate_frames_denied_when_prompt_pack_missing_characters(builder, base_report, tmp_path):
    """Test 4: generate_frames denied when prompt_pack missing characters."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json without characters field
    prompt_pack = {
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "prompt_pack missing characters" in plan.reason.lower()


def test_generate_frames_denied_when_character_not_found_in_registry(builder, base_report, tmp_path):
    """Test 5: generate_frames denied when character not found in registry."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with unknown character
    prompt_pack = {
        "characters": ["unknown_character"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "reference lock gate" in plan.reason.lower()
    assert "not found in registry" in plan.reason.lower() or "unknown" in plan.reason.lower()


def test_generate_frames_allowed_when_characters_specified_per_beat_and_all_approved(builder, base_report, tmp_path):
    """Test 6: generate_frames allowed when characters are specified per beat and all approved."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with beat-level characters
    prompt_pack = {
        "beats": [
            {
                "beat_id": "beat_001",
                "characters": ["alya"]
            }
        ]
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.allowed
    assert plan.action == "generate_frames"


def test_action_plan_reason_includes_reference_lock_denial_reason(builder, base_report, tmp_path):
    """Test 7: control-status or action-plan reason includes reference lock denial reason."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Kael (missing lock)
    prompt_pack = {
        "characters": ["kael"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "reference lock gate" in plan.reason.lower()
    # The specific denial reason from the gate should be included
    assert "kael" in plan.reason.lower() or "missing" in plan.reason.lower()


def test_does_not_call_comfyui_or_subprocess(builder, base_report, tmp_path):
    """Test 8: no ComfyUI or subprocess is called."""
    from unittest.mock import patch
    
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    # Mock subprocess to ensure it's not called
    with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")):
        with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
            # Run the gate check - should not trigger subprocess
            plan = builder.build(base_report, "generate_frames")
            
            # If we reach here, no subprocess was called during gate check
            assert plan is not None


def test_generate_frames_denied_when_prompt_pack_not_found(builder, base_report, tmp_path):
    """Test: generate_frames denied when prompt_pack.json not found."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Do NOT create prompt_pack.json
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert not plan.allowed
    assert "prompt_pack" in plan.reason.lower()


def test_reference_lock_gate_does_not_hardcode_alya(builder, base_report, tmp_path):
    """Test: reference lock gate does not hardcode Alya - works with any character."""
    project_root = tmp_path / "test_project"
    control_dir = project_root / "output" / "control"
    reference_locks_dir = control_dir / "reference_locks"
    control_dir.mkdir(parents=True)
    reference_locks_dir.mkdir()
    
    # Create project_profile.json
    project_profile = {
        "project_id": "test_project",
        "title": "Test Project",
        "source_root": "/path/to/source",
        "default_aspect_ratio": "16:9",
        "safe_resolution": {"width": 1920, "height": 1080},
        "generation_policy": {
            "require_kb_ready": False,
            "require_reference_lock_for_main_characters": True,
            "allow_prompt_only_for_background_characters": False
        }
    }
    (control_dir / "project_profile.json").write_text(json.dumps(project_profile), encoding='utf-8')
    
    # Create character_registry.json with hero_01
    character_registry = {
        "characters": [
            {
                "character_id": "hero_01",
                "name": "Hero 01",
                "role": "protagonist",
                "reference_required": True,
                "status": "approved"
            }
        ]
    }
    (control_dir / "character_registry.json").write_text(json.dumps(character_registry), encoding='utf-8')
    
    # Create hero_01 reference lock
    hero_lock = {
        "character_id": "hero_01",
        "reference_lock_status": "approved",
        "downstream_generation_allowed": True,
        "approved_references": ["ref_hero_01_main"],
        "primary_identity_reference": {
            "reference_id": "ref_hero_01_main",
            "filename": "hero01.png",
            "type": "reference_sheet",
            "approved_for": ["identity", "face"]
        },
        "prompt_anchor_en": "Hero character with distinctive features"
    }
    (reference_locks_dir / "hero_01_reference_lock.json").write_text(json.dumps(hero_lock), encoding='utf-8')
    
    # Create prompt_pack.json with hero_01
    prompt_pack = {
        "characters": ["hero_01"],
        "beats": []
    }
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    # Should be allowed - gate is not hardcoded to Alya
    assert plan.allowed
    assert plan.action == "generate_frames"


def test_prompt_pack_mode_allowed_action_plan_does_not_require_brief_path(builder, base_report, tmp_path):
    """MK-GEN2R Test 1: prompt-pack mode allowed action plan does not require brief_path."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.generation_mode == "prompt_pack"
    assert "brief_path" not in plan.required_inputs
    assert plan.prompt_pack_path is not None


def test_prompt_pack_mode_allowed_action_plan_requires_prompt_pack_path(builder, base_report, tmp_path):
    """MK-GEN2R Test 2: prompt-pack mode allowed action plan requires prompt_pack_path."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.generation_mode == "prompt_pack"
    assert "prompt_pack_path" in plan.required_inputs
    assert plan.prompt_pack_path is not None
    assert plan.prompt_pack_path.endswith("prompt_pack.json")


def test_prompt_pack_mode_executable_true_only_when_prompt_pack_exists(builder, base_report, tmp_path):
    """MK-GEN2R Test 3: prompt-pack mode executable=true only when prompt_pack exists."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.generation_mode == "prompt_pack"
    assert plan.executable is True
    assert "prompt_pack_path" not in plan.missing_inputs


def test_missing_prompt_pack_path_denies_generate_frames(builder, base_report, tmp_path):
    """MK-GEN2R Test 4: missing prompt_pack_path denies generate_frames."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Do NOT create prompt_pack.json
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.allowed is False
    assert plan.executable is False
    assert "prompt_pack" in plan.reason.lower()
    # MK-GEN2R-2 — Verify required_inputs and missing_inputs report prompt_pack_path
    assert "prompt_pack_path" in plan.required_inputs
    assert "prompt_pack_path" in plan.missing_inputs
    # MK-GEN2R-2 — Verify generation_mode is still prompt_pack
    assert plan.generation_mode == "prompt_pack"


def test_brief_path_null_cannot_produce_executable_true_if_brief_mode_used(builder, tmp_path):
    """MK-GEN2R Test 5: brief_path null cannot produce executable=true if brief mode is used."""
    project_root = tmp_path / "test_project"
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Create project_profile.json
    project_profile = {
        "project_id": "test_project",
        "title": "Test Project",
        "source_root": "/path/to/source",
        "default_aspect_ratio": "16:9",
    }
    (control_dir / "project_profile.json").write_text(json.dumps(project_profile), encoding='utf-8')
    
    # Create report with brief_path=None and no prompt_pack
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="ready_for_generation",
        next_action="generate_frames",
        is_done=False,
        existing_artifacts=ShotArtifacts(
            brief_path=None,  # No brief
        ),
        project_root=str(project_root),
    )
    
    plan = builder.build(report, "generate_frames")
    
    # Should be denied since no prompt_pack and no brief
    assert plan.allowed is False
    assert plan.executable is False


def test_command_preview_indicates_prompt_pack_mode(builder, base_report, tmp_path):
    """MK-GEN2R Test 6: command_preview indicates prompt-pack mode."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.generation_mode == "prompt_pack"
    assert plan.command_preview is not None
    assert "--prompt-pack" in plan.command_preview
    assert "prompt_pack.json" in plan.command_preview


def test_allowed_alya_action_plan_has_no_contradictory_required_missing_inputs(builder, base_report, tmp_path):
    """MK-GEN2R Test 7: allowed Alya action plan has no contradictory required/missing inputs."""
    project_root = tmp_path / "popadanka_erdan"
    create_popadanka_project_structure(project_root)
    
    # Create prompt_pack.json with Alya
    prompt_pack = {
        "characters": ["alya"],
        "beats": []
    }
    control_dir = project_root / "output" / "control"
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding='utf-8')
    
    base_report.project_root = str(project_root)
    
    plan = builder.build(base_report, "generate_frames")
    
    assert plan.allowed is True
    assert plan.executable is True
    # In prompt-pack mode, brief_path should not be in required_inputs
    assert "brief_path" not in plan.required_inputs
    # prompt_pack_path should be in required_inputs and not missing
    assert "prompt_pack_path" in plan.required_inputs
    assert "prompt_pack_path" not in plan.missing_inputs
    # missing_inputs should be empty since prompt_pack exists
    assert len(plan.missing_inputs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
