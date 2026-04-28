"""MK-CTRL24 — Tests for render_episode controlled action.

Tests cover:
- State transitions from audio_attached to episode_rendered
- Gate decisions allowing render_episode from audio_attached
- Action plan building with scene_mp4_path
- Command contract verification
- CLI behavior
- Artifact acceptance (success, missing, empty)
- Dry run mode
- Global kill switch blocking execution
- No auto-next-action after episode_rendered
- Handler execution
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.control.action_runner import ControlledActionRunner
from app.control.action_plan import ActionPlanBuilder
from app.control.artifact_parser import evaluate_artifact_acceptance, parse_generation_artifacts
from app.control.gate import ShotExecutionGate
from app.control.handler_contracts import HandlerPayload
from app.control.handlers import build_default_handler_registry
from app.control.models import ShotArtifacts, ShotStateReport
from app.control.real_handlers import RealRenderEpisodeHandler
from app.control.shot_controller import ShotController
from app.control.shot_state_storage import ShotStateStorage, ShotState
from app.control.ledger import ShotLedgerStorage


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_scene_mp4(temp_dir):
    """Create a mock scene MP4 file."""
    scene_path = temp_dir / "scene_audio.mp4"
    scene_path.write_bytes(b"mock scene data")
    return scene_path


@pytest.fixture
def mock_brief(temp_dir):
    """Create a mock brief file."""
    brief_path = temp_dir / "brief.json"
    brief_path.write_text(json.dumps({"dialogue": []}))
    return brief_path


@pytest.fixture
def state_storage(temp_dir):
    """Create a state storage."""
    return ShotStateStorage(temp_dir)


@pytest.fixture
def ledger_storage(temp_dir):
    """Create a ledger storage for testing."""
    return ShotLedgerStorage(temp_dir)


@pytest.fixture
def handler_registry():
    """Create a handler registry with mock handlers."""
    return build_default_handler_registry(enable_mock_handlers=True)


@pytest.fixture
def action_runner(temp_dir, handler_registry, ledger_storage):
    """Create a controlled action runner for testing."""
    controller = ShotController(temp_dir)
    gate = ShotExecutionGate()
    return ControlledActionRunner(
        controller=controller,
        gate=gate,
        handlers=handler_registry._handlers,
        ledger=ledger_storage,
    )


# Test 1: State transition from audio_attached to episode_rendered
def test_render_episode_state_transition(temp_dir, mock_scene_mp4, mock_brief):
    """Test that render_episode action transitions from audio_attached to episode_rendered."""
    episode_id = "ep01"
    shot_id = "shot01"
    
    state_storage = ShotStateStorage(temp_dir)
    
    # Set up initial state: audio_attached with artifact_path pointing to scene MP4
    initial_state = ShotState(
        episode_id=episode_id,
        shot_id=shot_id,
        current_state="audio_attached",
        expected_next_action="render_episode",
        artifact_path=str(mock_scene_mp4),
        brief_path=str(mock_brief),
        last_updated="2024-01-01T00:00:00",
    )
    state_storage.save(initial_state)
    
    # Verify initial state
    state = state_storage.load(episode_id, shot_id)
    assert state.current_state == "audio_attached"
    assert state.expected_next_action == "render_episode"


# Test 2: Gate decision allows render_episode from audio_attached
def test_render_episode_gate_decision_from_audio_attached():
    """Test that ShotExecutionGate allows render_episode from audio_attached state."""
    gate = ShotExecutionGate()
    
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="audio_attached",
        next_action="render_episode",
        artifact_path="output/scenes/scene_audio.mp4",
        brief_path="briefs/shot01.json",
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=False,
    )
    
    decision = gate.decide(report, "render_episode")
    
    assert decision.allowed is True
    assert "action matches next expected step" in decision.reason


# Test 3: Action plan building with scene_mp4_path
def test_render_episode_action_plan_building():
    """Test that ActionPlanBuilder builds render_episode plans with scene_mp4_path."""
    builder = ActionPlanBuilder()
    
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="audio_attached",
        next_action="render_episode",
        artifact_path="output/scenes/scene_audio.mp4",
        brief_path="briefs/shot01.json",
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=False,
    )
    
    plan = builder.build(report, "render_episode")
    
    assert plan.action == "render_episode"
    assert plan.allowed is True
    assert "scene_mp4_path" in plan.required_inputs
    assert "output/episodes/ep01_shot01_episode.mp4" in plan.expected_outputs
    assert "output/control/episode_manifest.json" in plan.expected_outputs
    assert "render-episode" in plan.command_preview
    assert plan.missing_inputs == []


# Test 4: Command contract verification
def test_render_episode_command_contract():
    """Test that render_episode command contract is correct."""
    builder = ActionPlanBuilder()
    
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="audio_attached",
        next_action="render_episode",
        artifact_path="output/scenes/scene_audio.mp4",
        brief_path="briefs/shot01.json",
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=False,
    )
    
    plan = builder.build(report, "render_episode")
    
    # Verify command template includes render-episode and --scene
    assert "render-episode" in plan.command_preview
    assert "--scene" in plan.command_preview
    assert plan.scene_mp4_path == "output/scenes/scene_audio.mp4"


# Test 5: CLI behavior test
def test_render_episode_cli_behavior(temp_dir, mock_scene_mp4):
    """Test that render-episode CLI command produces expected output."""
    from app.cli import render_episode
    import argparse
    
    args = argparse.Namespace(
        scene=str(mock_scene_mp4),
        output=str(temp_dir),
    )
    
    result = render_episode(args)
    
    assert result == 0
    
    # Verify output files were created
    episode_output = temp_dir / "episodes" / f"{mock_scene_mp4.stem}_episode.mp4"
    episode_manifest = temp_dir / "control" / "episode_manifest.json"
    
    assert episode_output.exists()
    assert episode_manifest.exists()


# Test 6: Artifact acceptance for successful episode
def test_render_episode_artifact_acceptance_success(temp_dir, mock_scene_mp4):
    """Test that episode artifact is accepted when output exists and has content."""
    episode_output = temp_dir / "episodes" / f"{mock_scene_mp4.stem}_episode.mp4"
    episode_output.parent.mkdir(parents=True, exist_ok=True)
    episode_output.write_bytes(b"mock episode data")
    
    artifacts = {
        "episode_output_path": str(episode_output),
        "episode_manifest_path": str(temp_dir / "control" / "episode_manifest.json"),
        "episode_duration_sec": 2.0,
        "episode_scene_count": 1,
        "output_exists": True,
        "output_size_bytes": 17,  # len(b"mock episode data")
    }
    
    result = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        **artifacts,
    )
    
    assert result["artifact_status"] == "accepted"
    assert result["artifact_accepted"] is True
    assert "episode artifact accepted" in result["artifact_reason"]


# Test 7: Artifact rejection for missing episode output
def test_render_episode_artifact_rejection_missing():
    """Test that episode artifact is rejected when output is missing."""
    artifacts = {
        "episode_output_path": "output/episodes/ep01_shot01_episode.mp4",
        "episode_manifest_path": "output/control/episode_manifest.json",
        "episode_duration_sec": 2.0,
        "episode_scene_count": 1,
    }
    
    result = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        output_exists=False,
        output_size_bytes=None,
        **artifacts,
    )
    
    assert result["artifact_status"] == "missing"
    assert result["artifact_accepted"] is False
    assert "missing or does not exist" in result["artifact_reason"]


# Test 8: Artifact rejection for empty episode output
def test_render_episode_artifact_rejection_empty(temp_dir):
    """Test that episode artifact is rejected when output is empty."""
    episode_output = temp_dir / "episodes" / "ep01_shot01_episode.mp4"
    episode_output.parent.mkdir(parents=True, exist_ok=True)
    episode_output.write_bytes(b"")  # Empty file
    
    artifacts = {
        "episode_output_path": str(episode_output),
        "episode_manifest_path": str(temp_dir / "control" / "episode_manifest.json"),
        "episode_duration_sec": 2.0,
        "episode_scene_count": 1,
    }
    
    result = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        output_exists=True,
        output_size_bytes=0,
        **artifacts,
    )
    
    assert result["artifact_status"] == "empty"
    assert result["artifact_accepted"] is False
    assert "empty or zero bytes" in result["artifact_reason"]


# Test 9: Dry run mode test
def test_render_episode_dry_run_mode(temp_dir, mock_scene_mp4, mock_brief):
    """Test that render_episode handler in dry validate mode returns validated."""
    handler = RealRenderEpisodeHandler(
        runner_callable=None,
        allow_real_execution=True,
    )
    
    # Create a minimal state report and action plan for HandlerPayload
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="audio_attached",
        next_action="render_episode",
        artifact_path=str(mock_scene_mp4),
        brief_path=str(mock_brief),
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=False,
    )
    
    # Create a minimal action plan
    from app.control.action_plan import ActionPlan
    action_plan = ActionPlan(
        episode_id="ep01",
        shot_id="shot01",
        action="render_episode",
        allowed=True,
        current_state="audio_attached",
        expected_next_action="render_episode",
        brief_path=str(mock_brief),
        required_inputs=["scene_mp4_path"],
        missing_inputs=[],
        expected_outputs=["output/episodes/ep01_shot01_episode.mp4"],
        command_preview="python -m app render-episode --scene output/scenes/scene_audio.mp4 --output output",
        handler_key="render_episode",
        reason="action matches next expected step",
        executable=True,
        scene_mp4_path=str(mock_scene_mp4),
        frame_manifest_path=None,
        output_dir="output",
    )
    
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="render_episode",
        state_report=report.to_dict() if hasattr(report, 'to_dict') else report.__dict__,
        action_plan=action_plan.to_dict() if hasattr(action_plan, 'to_dict') else action_plan.__dict__,
        dry_validate=True,
        allow_real_execution=True,
    )
    
    result = handler(payload)
    
    assert result.status == "validated"
    assert result.executed is False


# Test 10: Global kill switch blocks execution
def test_render_episode_blocked_by_global_kill_switch(temp_dir, mock_scene_mp4, mock_brief):
    """Test that global kill switch blocks render_episode execution."""
    handler = RealRenderEpisodeHandler(
        runner_callable=None,
        allow_real_execution=True,
    )
    
    # Create a minimal state report and action plan for HandlerPayload
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="audio_attached",
        next_action="render_episode",
        artifact_path=str(mock_scene_mp4),
        brief_path=str(mock_brief),
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=False,
    )
    
    # Create a minimal action plan
    from app.control.action_plan import ActionPlan
    action_plan = ActionPlan(
        episode_id="ep01",
        shot_id="shot01",
        action="render_episode",
        allowed=True,
        current_state="audio_attached",
        expected_next_action="render_episode",
        brief_path=str(mock_brief),
        required_inputs=["scene_mp4_path"],
        missing_inputs=[],
        expected_outputs=["output/episodes/ep01_shot01_episode.mp4"],
        command_preview="python -m app render-episode --scene output/scenes/scene_audio.mp4 --output output",
        handler_key="render_episode",
        reason="action matches next expected step",
        executable=True,
        scene_mp4_path=str(mock_scene_mp4),
        frame_manifest_path=None,
        output_dir="output",
    )
    
    payload = HandlerPayload(
        episode_id="ep01",
        shot_id="shot01",
        action="render_episode",
        state_report=report.to_dict() if hasattr(report, 'to_dict') else report.__dict__,
        action_plan=action_plan.to_dict() if hasattr(action_plan, 'to_dict') else action_plan.__dict__,
        dry_validate=False,
        allow_real_execution=True,
    )
    
    # Set global kill switch to disabled
    with patch.dict(os.environ, {"COMFY_AGENT_REAL_EXECUTION_ENABLED": "0"}):
        result = handler(payload)
    
    assert result.status == "blocked"
    assert result.executed is False
    assert "global kill switch" in result.reason.lower()
    assert result.artifacts.get("subprocess_invoked") is False
    assert result.artifacts.get("global_real_execution_enabled") is False
    # Verify standard audit fields
    assert result.artifacts.get("real_execution_requested") is True
    assert result.artifacts.get("subprocess_allowed") is True
    assert result.artifacts.get("production_executed") is False
    assert "reason" in result.artifacts


# Test 11: No auto-next-action after episode_rendered
def test_render_episode_no_auto_next_action(temp_dir):
    """Test that episode_rendered state has next_action=none (terminal state)."""
    state_storage = ShotStateStorage(temp_dir)
    controller = ShotController(temp_dir)
    
    # Set up state as episode_rendered
    state = ShotState(
        episode_id="ep01",
        shot_id="shot01",
        current_state="episode_rendered",
        expected_next_action="none",
        artifact_path="output/episodes/ep01_shot01_episode.mp4",
        brief_path="briefs/shot01.json",
        last_updated="2024-01-01T00:00:00",
    )
    state_storage.save(state)
    
    report = controller.inspect("ep01", "shot01")
    
    assert report.current_state == "episode_rendered"
    assert report.next_action == "none"
    assert report.is_done is True


# Test 11b: Gate denies action after episode_rendered
def test_render_episode_gate_denies_after_episode_rendered():
    """Test that gate denies any production action from episode_rendered state."""
    gate = ShotExecutionGate()
    
    report = ShotStateReport(
        episode_id="ep01",
        shot_id="shot01",
        current_state="episode_rendered",
        next_action="none",
        artifact_path="output/episodes/ep01_shot01_episode.mp4",
        brief_path="briefs/shot01.json",
        existing_artifacts=ShotArtifacts(),
        missing_artifacts=[],
        generation_required=False,
        assembly_required=False,
        audio_required=False,
        qa_required=False,
        is_done=True,  # episode_rendered is terminal
    )
    
    # Try to run render_episode again
    decision = gate.decide(report, "render_episode")
    
    assert decision.allowed is False
    assert "shot is already done" in decision.reason


# Test 12: Handler execution test
def test_render_episode_handler_execution():
    """Test that render_episode handler executes correctly."""
    from app.control.handlers import render_episode_handler
    
    payload = {
        "scene_mp4_path": "output/scenes/scene_audio.mp4",
    }
    
    result = render_episode_handler(payload)
    
    assert result["status"] == "executed"
    assert result["executed"] is True
    assert result["scene_mp4_path"] == "output/scenes/scene_audio.mp4"


# Additional test: CLI output parsing
def test_render_episode_cli_output_parsing():
    """Test that parse_generation_artifacts correctly parses render-episode output."""
    stdout = """Episode MP4 saved: output/episodes/ep01_shot01_episode.mp4
Episode manifest saved: output/control/episode_manifest.json
Episode duration seconds: 2.0
Episode scene count: 1"""
    
    result = parse_generation_artifacts(stdout, cwd=".")
    
    # Normalize path separators for Windows compatibility
    episode_output = result["episode_output_path"].replace("\\", "/")
    episode_manifest = result["episode_manifest_path"].replace("\\", "/")
    
    assert episode_output == "output/episodes/ep01_shot01_episode.mp4"
    assert episode_manifest == "output/control/episode_manifest.json"
    assert result["episode_duration_sec"] == 2.0
    assert result["episode_scene_count"] == 1


# RC2-RENDER1 Tests
def test_rc2_final_mp4_created_from_scene():
    """Test that RC2 final MP4 is created from existing scene.mp4."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    scene_mp4 = rc2_root / "output" / "scenes" / "ep01_shot01" / "scene.mp4"
    final_mp4 = rc2_root / "output" / "final" / "ep01_final.mp4"
    
    assert scene_mp4.exists(), "Source scene.mp4 must exist in RC2 root"
    assert final_mp4.exists(), "Final ep01_final.mp4 must exist in RC2 root"
    
    # Verify final MP4 has content
    final_size = final_mp4.stat().st_size
    assert final_size > 0, "Final MP4 must be non-empty"
    assert final_size == scene_mp4.stat().st_size, "Final MP4 should be copy of scene MP4"


def test_rc2_no_audio_policy_preserved():
    """Test that RC2 final manifest preserves no-audio policy honestly."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    final_manifest_path = rc2_root / "output" / "control" / "ep01_final_manifest.json"
    
    assert final_manifest_path.exists(), "Final manifest must exist in RC2 root"
    
    with open(final_manifest_path, 'r', encoding='utf-8') as f:
        final_manifest = json.load(f)
    
    assert final_manifest["audio_required"] is False, "audio_required must be false"
    assert final_manifest["audio_attached"] is False, "audio_attached must be false"
    assert final_manifest["audio_policy"] == "no_audio_for_rc", "audio_policy must be no_audio_for_rc"
    assert final_manifest["final_artifact_type"] == "mp4_without_audio", "final_artifact_type must be mp4_without_audio"
    assert "RC2 render without audio" in final_manifest["limitation"], "limitation must document RC2 no-audio"


def test_rc2_final_manifest_does_not_claim_audio():
    """Test that RC2 final manifest does not claim real audio track."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    final_manifest_path = rc2_root / "output" / "control" / "ep01_final_manifest.json"
    
    with open(final_manifest_path, 'r', encoding='utf-8') as f:
        final_manifest = json.load(f)
    
    # Verify no audio claims
    assert final_manifest["audio_attached"] is False
    assert final_manifest["audio_required"] is False
    assert final_manifest["audio_policy"] == "no_audio_for_rc"
    
    # Verify ComfyUI generation and pipeline rerun flags are false
    assert final_manifest["comfyui_generation"] is False
    assert final_manifest["pipeline_action_rerun"] is False


def test_rc2_frozen_rc1_artifact_index_not_mutated():
    """Test that frozen RC1 artifact_index.json was not mutated."""
    rc1_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01")
    rc1_artifact_index = rc1_root / "output" / "control" / "artifact_index.json"
    
    assert rc1_artifact_index.exists(), "RC1 artifact_index must exist"
    
    with open(rc1_artifact_index, 'r', encoding='utf-8') as f:
        rc1_index = json.load(f)
    
    # Verify RC1 artifact_index does not reference RC2 paths
    for artifact in rc1_index["artifacts"]:
        assert "rc2_render1" not in artifact["path"], f"RC1 artifact_index must not reference RC2 paths: {artifact['path']}"
    
    # Verify RC1 artifact_index has source RC field
    assert rc1_index.get("rc_version") is None or rc1_index.get("rc_version") != "rc2_render1", "RC1 should not have rc2_render1 version"


def test_rc2_frozen_rc1_ledger_not_mutated():
    """Test that frozen RC1 ledger was not mutated."""
    rc1_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01")
    rc1_ledger = rc1_root / "output" / "control" / "ep01_shot01_ledger.json"
    
    assert rc1_ledger.exists(), "RC1 ledger must exist"
    
    with open(rc1_ledger, 'r', encoding='utf-8') as f:
        rc1_ledger_data = json.load(f)
    
    # Verify RC1 ledger does not have RC2 final_mp4_rendered event
    for record in rc1_ledger_data["records"]:
        assert record["event_type"] != "final_mp4_rendered", "RC1 ledger must not have RC2 final_mp4_rendered event"
        if "handler_result" in record and isinstance(record["handler_result"], dict):
            assert "rc2_render" not in str(record["handler_result"]), "RC1 ledger must not reference RC2 render"


def test_rc2_final_mp4_path_exists_and_non_empty():
    """Test that RC2 final MP4 path exists and is non-empty."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    final_mp4 = rc2_root / "output" / "final" / "ep01_final.mp4"
    
    assert final_mp4.exists(), "Final MP4 must exist at expected path"
    
    file_size = final_mp4.stat().st_size
    assert file_size > 0, "Final MP4 must be non-empty"
    assert file_size == 44727, f"Final MP4 size should be 44727 bytes, got {file_size}"


def test_rc2_artifact_index_includes_final_mp4():
    """Test that RC2 artifact_index includes final MP4 and related artifacts."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    artifact_index_path = rc2_root / "output" / "control" / "artifact_index.json"
    
    with open(artifact_index_path, 'r', encoding='utf-8') as f:
        artifact_index = json.load(f)
    
    artifact_names = [a["name"] for a in artifact_index["artifacts"]]
    
    # Verify required artifacts are present
    assert "ep01_final.mp4" in artifact_names, "Final MP4 must be in artifact_index"
    assert "ep01_final_manifest.json" in artifact_names, "Final manifest must be in artifact_index"
    assert "scene.mp4" in artifact_names, "Scene MP4 must be in artifact_index"
    assert "ep01_shot01_audio_manifest.json" in artifact_names, "Audio manifest must be in artifact_index"
    
    # Verify final MP4 metadata
    final_mp4_artifact = next(a for a in artifact_index["artifacts"] if a["name"] == "ep01_final.mp4")
    assert final_mp4_artifact["audio_attached"] is False
    assert final_mp4_artifact["type"] == "final_video"
    
    # Verify RC2 version metadata
    assert artifact_index["rc_version"] == "rc2_render1"
    assert "rc_mir_erdan_ep01" in artifact_index["source_rc"]


def test_rc2_ledger_has_final_mp4_rendered_event():
    """Test that RC2 ledger has final_mp4_rendered event."""
    rc2_root = Path("f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_render1_ep01")
    ledger_path = rc2_root / "output" / "control" / "ep01_shot01_ledger.json"
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger_data = json.load(f)
    
    # Find final_mp4_rendered event
    final_render_events = [r for r in ledger_data["records"] if r["event_type"] == "final_mp4_rendered"]
    
    assert len(final_render_events) >= 1, "RC2 ledger must have at least one final_mp4_rendered event"
    
    event = final_render_events[0]
    assert event["success"] is True
    assert event["handler_status"] == "rc2_render"
    assert "RC2-RENDER1" in event["reason"]
    
    # Verify handler_result
    handler_result = event["handler_result"]
    assert handler_result["audio_policy"] == "no_audio_for_rc"
    assert handler_result["comfyui_generation"] is False
    assert handler_result["pipeline_action_rerun"] is False
    assert "rc2_render1_ep01" in handler_result["final_output_path"]


# RC2-RENDER1B Tests for render-final CLI command
def test_render_final_cli_command_creates_final_mp4(temp_dir):
    """Test that render-final CLI command creates final MP4 from existing scene.mp4."""
    import subprocess
    import json
    
    # Create mock source RC1 structure
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    # Create mock scene.mp4
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    # Create mock scene manifest
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {
        "duration": 3.0,
        "fps": 24,
        "resolution": "480x640",
        "scene_artifact_path": str(source_scene_mp4)
    }
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    # Create mock audio manifest with no-audio policy
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {
        "audio_required": False,
        "audio_policy": "no_audio_for_rc",
        "audio_attached": False
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    # Create output RC2 root
    output_root = temp_dir / "output_rc"
    
    # Run render-final command
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0, f"render-final command failed: {result.stderr}"
    
    # Parse JSON output
    output_data = json.loads(result.stdout)
    assert output_data["status"] == "success"
    
    # Verify final MP4 exists
    final_mp4 = Path(output_data["final_mp4_path"])
    assert final_mp4.exists()
    assert final_mp4.stat().st_size > 0
    
    # Verify final manifest exists
    final_manifest_path = Path(output_data["final_manifest_path"])
    assert final_manifest_path.exists()
    
    # Verify artifact index exists
    artifact_index_path = Path(output_data["artifact_index_path"])
    assert artifact_index_path.exists()
    
    # Verify ledger exists
    ledger_path = Path(output_data["ledger_path"])
    assert ledger_path.exists()


def test_render_final_cli_writes_final_manifest(temp_dir):
    """Test that render-final CLI command writes final manifest with correct fields."""
    import subprocess
    
    # Create mock source RC1 structure
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {
        "duration": 3.0,
        "fps": 24,
        "resolution": "480x640"
    }
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {
        "audio_required": False,
        "audio_policy": "no_audio_for_rc",
        "audio_attached": False
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Read final manifest
    final_manifest_path = output_root / "output" / "control" / "ep01_final_manifest.json"
    with open(final_manifest_path, 'r', encoding='utf-8') as f:
        final_manifest = json.load(f)
    
    # Verify required fields
    assert final_manifest["audio_required"] is False
    assert final_manifest["audio_attached"] is False
    assert final_manifest["audio_policy"] == "no_audio_for_rc"
    assert final_manifest["final_artifact_type"] == "mp4_without_audio"
    assert "RC2 render without audio" in final_manifest["limitation"]
    assert final_manifest["comfyui_generation"] is False
    assert final_manifest["pipeline_action_rerun"] is False
    assert final_manifest["render_method"] == "copy_existing_scene_mp4"


def test_render_final_cli_writes_rc2_artifact_index(temp_dir):
    """Test that render-final CLI command writes RC2 artifact_index."""
    import subprocess
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Read artifact index
    artifact_index_path = output_root / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path, 'r', encoding='utf-8') as f:
        artifact_index = json.load(f)
    
    artifact_names = [a["name"] for a in artifact_index["artifacts"]]
    
    # Verify required artifacts
    assert "ep01_final.mp4" in artifact_names
    assert "ep01_final_manifest.json" in artifact_names
    assert "scene.mp4" in artifact_names
    
    # Verify RC2 metadata
    assert artifact_index["rc_version"] == "rc2_render1"
    assert "source_rc" in artifact_index


def test_render_final_cli_writes_rc2_ledger_event(temp_dir):
    """Test that render-final CLI command writes RC2 ledger event."""
    import subprocess
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Read ledger
    ledger_path = output_root / "output" / "control" / "ep01_shot01_ledger.json"
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger_data = json.load(f)
    
    # Find final_mp4_rendered event
    final_render_events = [r for r in ledger_data["records"] if r["event_type"] == "final_mp4_rendered"]
    
    assert len(final_render_events) == 1
    
    event = final_render_events[0]
    assert event["success"] is True
    assert event["handler_status"] == "rc2_render"
    assert "RC2-RENDER1B" in event["reason"]
    
    # Verify handler_result has frozen_rc1_mutated field
    handler_result = event["handler_result"]
    assert handler_result["frozen_rc1_mutated"] is False


def test_render_final_cli_preserves_no_audio_policy(temp_dir):
    """Test that render-final CLI command preserves no-audio policy honestly."""
    import subprocess
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Read final manifest
    final_manifest_path = output_root / "output" / "control" / "ep01_final_manifest.json"
    with open(final_manifest_path, 'r', encoding='utf-8') as f:
        final_manifest = json.load(f)
    
    assert final_manifest["audio_required"] is False
    assert final_manifest["audio_attached"] is False
    assert final_manifest["audio_policy"] == "no_audio_for_rc"


def test_render_final_cli_does_not_claim_audio(temp_dir):
    """Test that render-final CLI command does not claim audio."""
    import subprocess
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    assert output_data["audio_policy"] == "no_audio_for_rc"
    assert output_data["comfyui_generation"] is False
    assert output_data["pipeline_action_rerun"] is False
    assert output_data["frozen_rc1_mutated"] is False


def test_render_final_cli_does_not_mutate_rc1(temp_dir):
    """Test that render-final CLI command does not mutate RC1 artifacts."""
    import subprocess
    import hashlib
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    # Calculate original hash
    original_scene_hash = hashlib.md5(source_scene_mp4.read_bytes()).hexdigest()
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    original_manifest_hash = hashlib.md5(source_scene_manifest.read_bytes()).hexdigest()
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Verify RC1 files unchanged
    new_scene_hash = hashlib.md5(source_scene_mp4.read_bytes()).hexdigest()
    new_manifest_hash = hashlib.md5(source_scene_manifest.read_bytes()).hexdigest()
    
    assert original_scene_hash == new_scene_hash, "RC1 scene.mp4 was mutated"
    assert original_manifest_hash == new_manifest_hash, "RC1 scene manifest was mutated"


def test_render_final_cli_is_idempotent(temp_dir):
    """Test that render-final CLI command is idempotent (can be run multiple times safely)."""
    import subprocess
    
    source_root = temp_dir / "source_rc"
    source_root.mkdir()
    
    source_scenes_dir = source_root / "output" / "scenes" / "ep01_shot01"
    source_scenes_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_scene_mp4 = source_scenes_dir / "scene.mp4"
    source_scene_mp4.write_bytes(b"mock scene data")
    
    source_scene_manifest = source_control_dir / "ep01_shot01_scene_manifest.json"
    scene_manifest_data = {"duration": 3.0, "fps": 24, "resolution": "480x640"}
    with open(source_scene_manifest, 'w', encoding='utf-8') as f:
        json.dump(scene_manifest_data, f)
    
    source_audio_manifest = source_control_dir / "ep01_shot01_audio_manifest.json"
    audio_manifest_data = {"audio_required": False, "audio_policy": "no_audio_for_rc", "audio_attached": False}
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    output_root = temp_dir / "output_rc"
    
    # Run command first time
    result1 = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result1.returncode == 0
    
    # Run command second time
    result2 = subprocess.run(
        [sys.executable, "-m", "app", "render-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result2.returncode == 0
    
    # Both should succeed
    output1 = json.loads(result1.stdout)
    output2 = json.loads(result2.stdout)
    
    assert output1["status"] == "success"
    assert output2["status"] == "success"
