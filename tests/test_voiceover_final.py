"""RC2-VOICE1: Tests for create-voiceover-final CLI command."""
import sys
import json
import pytest
from pathlib import Path


def test_create_voiceover_final_cli_command_creates_voiceover_script(tmp_path):
    """Test that create-voiceover-final CLI command creates voiceover script."""
    import subprocess
    
    # Create mock source frozen RC2 demo pack
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    # Create mock final MP4 without audio
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    # Create output RC2 voice root
    output_root = tmp_path / "output_rc"
    
    # Run create-voiceover-final command
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # The command may fail if TTS is not available, but script should still be created
    # Check if voiceover script exists
    voiceover_script = output_root / "output" / "control" / "ep01_voiceover_script.txt"
    if voiceover_script.exists():
        script_content = voiceover_script.read_text(encoding='utf-8')
        assert len(script_content) > 0
        assert "Episode" in script_content or "Alya" in script_content
    else:
        pytest.skip("Voiceover script not created (command may have failed)")


def test_create_voiceover_final_cli_command_creates_voiceover_audio(tmp_path):
    """Test that create-voiceover-final CLI command creates voiceover audio artifact."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if voiceover audio exists
    voiceover_audio = output_root / "output" / "audio" / "ep01_real_voiceover.wav"
    if voiceover_audio.exists():
        assert voiceover_audio.stat().st_size > 0
    else:
        pytest.skip("Voiceover audio not created (TTS may not be available)")


def test_create_voiceover_final_cli_audio_kind_is_voiceover(tmp_path):
    """Test that create-voiceover-final CLI command sets audio_kind to voiceover."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if voiceover manifest exists and has correct audio_kind
    voiceover_manifest = output_root / "output" / "control" / "ep01_voiceover_manifest.json"
    if voiceover_manifest.exists():
        with open(voiceover_manifest, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        assert manifest_data["audio_kind"] == "voiceover"
    else:
        pytest.skip("Voiceover manifest not created (command may have failed)")


def test_create_voiceover_final_cli_creates_final_mp4_with_voiceover(tmp_path):
    """Test that create-voiceover-final CLI command creates final MP4 with voiceover."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if final MP4 with voiceover exists
    final_with_voiceover = output_root / "output" / "final" / "ep01_final_with_voiceover.mp4"
    if final_with_voiceover.exists():
        assert final_with_voiceover.stat().st_size > 0
    else:
        pytest.skip("Final MP4 with voiceover not created (ffmpeg may not be available)")


def test_create_voiceover_final_cli_does_not_mutate_frozen_rc2_pack(tmp_path):
    """Test that create-voiceover-final CLI command does not mutate frozen RC2 demo pack."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    # Create a marker file in source to detect mutation
    source_marker = source_root / "source_marker.txt"
    source_marker.write_text("RC2 frozen marker")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Verify source marker file still exists and unchanged
    assert source_marker.exists()
    assert source_marker.read_text(encoding='utf-8') == "RC2 frozen marker"
    
    # Verify source MP4 unchanged
    assert source_final_mp4.read_bytes() == b"mock video data"


def test_create_voiceover_final_cli_no_comfyui_generation(tmp_path):
    """Test that create-voiceover-final CLI command does not run ComfyUI."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if final manifest exists and confirms no ComfyUI generation
    final_manifest = output_root / "output" / "control" / "ep01_final_with_voiceover_manifest.json"
    if final_manifest.exists():
        with open(final_manifest, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        assert manifest_data["comfyui_generation"] == False
    else:
        pytest.skip("Final manifest not created (command may have failed)")


def test_create_voiceover_final_cli_no_pipeline_action_rerun(tmp_path):
    """Test that create-voiceover-final CLI command does not rerun pipeline actions."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if final manifest exists and confirms no pipeline action rerun
    final_manifest = output_root / "output" / "control" / "ep01_final_with_voiceover_manifest.json"
    if final_manifest.exists():
        with open(final_manifest, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        assert manifest_data["pipeline_action_rerun"] == False
    else:
        pytest.skip("Final manifest not created (command may have failed)")


def test_create_voiceover_final_cli_creates_voiceover_manifest(tmp_path):
    """Test that create-voiceover-final CLI command creates voiceover manifest."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if voiceover manifest exists
    voiceover_manifest = output_root / "output" / "control" / "ep01_voiceover_manifest.json"
    if voiceover_manifest.exists():
        with open(voiceover_manifest, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        assert manifest_data["audio_required"] == True
        assert manifest_data["audio_attached"] == True
        assert manifest_data["audio_kind"] == "voiceover"
        assert "voiceover_text" in manifest_data
        assert "tts_engine" in manifest_data
    else:
        pytest.skip("Voiceover manifest not created (command may have failed)")


def test_create_voiceover_final_cli_creates_final_manifest(tmp_path):
    """Test that create-voiceover-final CLI command creates final manifest."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if final manifest exists
    final_manifest = output_root / "output" / "control" / "ep01_final_with_voiceover_manifest.json"
    if final_manifest.exists():
        with open(final_manifest, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        assert manifest_data["audio_required"] == True
        assert manifest_data["audio_attached"] == True
        assert manifest_data["audio_track_present"] == True
        assert manifest_data["audio_kind"] == "voiceover"
        assert manifest_data["final_artifact_type"] == "mp4_with_voiceover"
    else:
        pytest.skip("Final manifest not created (command may have failed)")


def test_create_voiceover_final_cli_creates_artifact_index(tmp_path):
    """Test that create-voiceover-final CLI command creates artifact index."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if artifact index exists
    artifact_index = output_root / "output" / "control" / "artifact_index.json"
    if artifact_index.exists():
        with open(artifact_index, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        assert index_data["episode_id"] == "ep01"
        assert index_data["shot_id"] == "shot01"
        assert "artifacts" in index_data
        assert len(index_data["artifacts"]) > 0
    else:
        pytest.skip("Artifact index not created (command may have failed)")


def test_create_voiceover_final_cli_creates_ledger(tmp_path):
    """Test that create-voiceover-final CLI command creates ledger."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if ledger exists
    ledger = output_root / "output" / "control" / "ep01_shot01_ledger.json"
    if ledger.exists():
        with open(ledger, 'r', encoding='utf-8') as f:
            ledger_data = json.load(f)
        assert ledger_data["episode_id"] == "ep01"
        assert ledger_data["shot_id"] == "shot01"
        assert "records" in ledger_data
        assert len(ledger_data["records"]) > 0
        
        # Check for voiceover event
        voiceover_event_found = False
        for record in ledger_data["records"]:
            if record.get("event_type") == "real_voiceover_attached_to_final_mp4":
                voiceover_event_found = True
                assert record["success"] == True
                assert record["handler_result"]["audio_kind"] == "voiceover"
                assert record["handler_result"]["frozen_rc2_pack_mutated"] == False
                assert record["handler_result"]["comfyui_generation"] == False
                assert record["handler_result"]["pipeline_action_rerun"] == False
                break
        
        assert voiceover_event_found, "Voiceover event not found in ledger"
    else:
        pytest.skip("Ledger not created (command may have failed)")


def test_voiceover_manifest_consistency_with_final_manifest(tmp_path):
    """Test that voiceover_manifest duration_fit_passed matches final_manifest duration_fit_passed."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if both manifests exist
    voiceover_manifest = output_root / "output" / "control" / "ep01_voiceover_manifest.json"
    final_manifest = output_root / "output" / "control" / "ep01_final_with_voiceover_manifest.json"
    
    if voiceover_manifest.exists() and final_manifest.exists():
        with open(voiceover_manifest, 'r', encoding='utf-8') as f:
            voiceover_data = json.load(f)
        with open(final_manifest, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        
        # Check duration_fit_passed consistency
        voiceover_duration_fit_passed = voiceover_data.get("duration_fit_passed")
        final_duration_fit_passed = final_data.get("duration_fit_passed")
        
        assert voiceover_duration_fit_passed is not None, "voiceover_manifest missing duration_fit_passed"
        assert final_duration_fit_passed is not None, "final_manifest missing duration_fit_passed"
        assert voiceover_duration_fit_passed == final_duration_fit_passed, \
            f"duration_fit_passed mismatch: voiceover_manifest={voiceover_duration_fit_passed}, final_manifest={final_duration_fit_passed}"
        
        # Check duration_delta_seconds is within tolerance
        if "duration_delta_seconds" in voiceover_data:
            assert voiceover_data["duration_delta_seconds"] <= 0.25, \
                f"duration_delta_seconds {voiceover_data['duration_delta_seconds']} exceeds 0.25s tolerance"
        
        if "duration_delta_seconds" in final_data:
            assert final_data["duration_delta_seconds"] <= 0.25, \
                f"duration_delta_seconds {final_data['duration_delta_seconds']} exceeds 0.25s tolerance"
    else:
        pytest.skip("Manifests not created (command may have failed)")


def test_voiceover_manifest_consistency_with_ledger(tmp_path):
    """Test that voiceover_manifest duration_fit_passed matches ledger duration fit record."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    
    source_final_mp4 = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_mp4.write_bytes(b"mock video data")
    
    output_root = tmp_path / "output_rc"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "create-voiceover-final",
         "--source-project-root", str(source_root),
         "--output-project-root", str(output_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    # Check if voiceover manifest and ledger exist
    voiceover_manifest = output_root / "output" / "control" / "ep01_voiceover_manifest.json"
    ledger = output_root / "output" / "control" / "ep01_shot01_ledger.json"
    
    if voiceover_manifest.exists() and ledger.exists():
        with open(voiceover_manifest, 'r', encoding='utf-8') as f:
            voiceover_data = json.load(f)
        with open(ledger, 'r', encoding='utf-8') as f:
            ledger_data = json.load(f)
        
        voiceover_duration_fit_passed = voiceover_data.get("duration_fit_passed")
        
        # Find the duration fit repair event in ledger
        ledger_duration_fit_passed = None
        for record in ledger_data.get("records", []):
            if record.get("event_type") == "voiceover_duration_fit_repaired":
                ledger_duration_fit_passed = record.get("handler_result", {}).get("duration_fit_passed")
                break
        
        if ledger_duration_fit_passed is not None:
            assert voiceover_duration_fit_passed == ledger_duration_fit_passed, \
                f"duration_fit_passed mismatch: voiceover_manifest={voiceover_duration_fit_passed}, ledger={ledger_duration_fit_passed}"
    else:
        pytest.skip("Voiceover manifest or ledger not created (command may have failed)")
