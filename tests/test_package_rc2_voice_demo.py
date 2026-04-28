"""RC2-PACK2: Tests for package-rc2-voice-demo CLI command."""
import sys
import json
import pytest
from pathlib import Path


def test_package_rc2_voice_demo_cli_command_creates_package_root(tmp_path):
    """Test that package-rc2-voice-demo CLI command creates package root."""
    import subprocess
    
    # Create mock source RC2 voice root
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    # Create mock media files
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    # Create mock control artifacts
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "duration_fit_strategy": "extend_video_to_match_voiceover",
        "duration_delta_seconds": 0.0,
        "sample_rate": 24000,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "resolution": "480x640",
        "file_size": 266027,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "artifacts": []
    }
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "records": []
    }
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    # Create output pack root
    output_pack_root = tmp_path / "output_pack"
    
    # Run package-rc2-voice-demo command
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0, f"package-rc2-voice-demo command failed: {result.stderr}"
    
    # Parse JSON output
    output_data = json.loads(result.stdout)
    assert output_data["status"] == "success"
    
    # Verify package root exists
    pack_root = Path(output_data["package_root"])
    assert pack_root.exists()
    assert pack_root.is_dir()


def test_package_rc2_voice_demo_cli_copies_final_mp4_with_voiceover(tmp_path):
    """Test that package-rc2-voice-demo CLI command copies final MP4 with voiceover."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "resolution": "480x640",
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify final MP4 with voiceover is copied
    final_with_voiceover = Path(output_data["final_with_voiceover_path"])
    assert final_with_voiceover.exists()
    assert final_with_voiceover.stat().st_size > 0


def test_package_rc2_voice_demo_cli_copies_voiceover_audio(tmp_path):
    """Test that package-rc2-voice-demo CLI command copies voiceover audio."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify voiceover audio is copied
    voiceover_audio = Path(output_data["voiceover_audio_path"])
    assert voiceover_audio.exists()
    assert voiceover_audio.stat().st_size > 0


def test_package_rc2_voice_demo_cli_copies_voiceover_control_artifacts(tmp_path):
    """Test that package-rc2-voice-demo CLI command copies voiceover control artifacts."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify voiceover control artifacts are copied
    voiceover_script = Path(output_data["voiceover_script_path"])
    assert voiceover_script.exists()
    
    voiceover_manifest = Path(output_data["voiceover_manifest_path"])
    assert voiceover_manifest.exists()
    
    final_with_voiceover_manifest = Path(output_data["final_with_voiceover_manifest_path"])
    assert final_with_voiceover_manifest.exists()
    
    artifact_index = Path(output_data["artifact_index_path"])
    assert artifact_index.exists()
    
    ledger = Path(output_data["ledger_path"])
    assert ledger.exists()
    
    checksums = Path(output_data["checksums_path"])
    assert checksums.exists()
    
    freeze_summary = Path(output_data["freeze_summary_path"])
    assert freeze_summary.exists()


def test_package_rc2_voice_demo_cli_writes_validation_json(tmp_path):
    """Test that package-rc2-voice-demo CLI command writes validation JSON."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify validation report is written
    validation_report_path = Path(output_data["validation_report_path"])
    assert validation_report_path.exists()
    
    with open(validation_report_path, 'r', encoding='utf-8') as f:
        validation_report = json.load(f)
    
    assert "validation_status" in validation_report
    assert "checks" in validation_report
    assert "summary" in validation_report
    assert "voiceover_metadata" in validation_report


def test_package_rc2_voice_demo_cli_writes_readme(tmp_path):
    """Test that package-rc2-voice-demo CLI command writes README."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify README is written
    readme_path = Path(output_data["readme_path"])
    assert readme_path.exists()
    
    readme_content = readme_path.read_text(encoding='utf-8')
    assert "RC2 Voiceover Demo Pack" in readme_content
    assert "real voiceover" in readme_content
    assert "edge-tts" in readme_content


def test_package_rc2_voice_demo_cli_does_not_mutate_source_root(tmp_path):
    """Test that package-rc2-voice-demo CLI command does not mutate source root."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    # Create a marker file in source root to detect mutation
    source_marker = source_root / "source_marker.txt"
    source_marker.write_text("RC2 voice source marker")
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Verify source marker file still exists and unchanged
    assert source_marker.exists()
    assert source_marker.read_text(encoding='utf-8') == "RC2 voice source marker"
    
    # Verify source files unchanged
    assert source_final_with_voiceover.read_bytes() == b"mock video with voiceover data"
    assert source_voiceover_audio.read_bytes() == b"mock real voiceover audio data"


def test_package_rc2_voice_demo_cli_records_voiceover_honestly(tmp_path):
    """Test that package-rc2-voice-demo CLI command records voiceover honestly."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify audio_kind is voiceover
    assert output_data["audio_kind"] == "voiceover"
    
    # Verify duration_fit_passed is true
    assert output_data["duration_fit_passed"] == True
    
    # Verify boundary compliance
    assert output_data["frozen_rc1_mutated"] == False
    assert output_data["frozen_rc2_demo_pack_mutated"] == False
    assert output_data["rc2_voice_root_mutated"] == False
    assert output_data["comfyui_generation"] == False
    assert output_data["pipeline_action_rerun"] == False
    assert output_data["tts_regenerated"] == False
    assert output_data["ffmpeg_rerun"] == False


def test_package_rc2_voice_demo_cli_checksums_use_package_relative_paths(tmp_path):
    """Test that package-rc2-voice-demo CLI checksums use package-relative paths."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify proof checksums file exists
    proof_checksums_path = Path(output_data["proof_checksums_path"])
    assert proof_checksums_path.exists()
    
    # Read proof checksums and verify all paths are package-relative
    proof_checksums_content = proof_checksums_path.read_text(encoding='utf-8')
    lines = proof_checksums_content.strip().split('\n')
    
    for line in lines:
        if line.strip():
            # Each line should be: <hash> <relative_path>
            parts = line.split(None, 1)
            assert len(parts) == 2, f"Invalid checksum line: {line}"
            hash_val, rel_path = parts
            
            # Verify path is relative (not absolute)
            assert not Path(rel_path).is_absolute(), f"Path should be relative, got absolute: {rel_path}"
            
            # Verify path does not contain drive letter or backslash at start
            assert not rel_path.startswith(('C:', 'c:', 'D:', 'd:', 'E:', 'e:', 'F:', 'f:', 'G:', 'g:')), f"Path should not have drive letter: {rel_path}"
            
            # Verify path starts with expected package-relative prefixes
            assert rel_path.startswith(('output/', 'output\\', 'proof/', 'proof\\')), f"Path should start with output/ or proof/, got: {rel_path}"
    
    # Verify ledger is in checksums with correct relative path
    ledger_line_found = False
    for line in lines:
        if 'ep01_shot01_ledger.json' in line:
            ledger_line_found = True
            parts = line.split(None, 1)
            ledger_rel_path = parts[1]
            assert ledger_rel_path in ('output/control/ep01_shot01_ledger.json', 'output\\control\\ep01_shot01_ledger.json'), f"Ledger path should be output/control/ep01_shot01_ledger.json, got: {ledger_rel_path}"
    
    assert ledger_line_found, "Ledger should be in proof checksums"


def test_package_rc2_voice_demo_cli_no_malformed_absolute_paths_in_package(tmp_path):
    """Test that package-rc2-voice-demo CLI does not contain malformed absolute paths in package files."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_voiceover = source_final_dir / "ep01_final_with_voiceover.mp4"
    source_final_with_voiceover.write_bytes(b"mock video with voiceover data")
    
    source_voiceover_audio = source_audio_dir / "ep01_real_voiceover.wav"
    source_voiceover_audio.write_bytes(b"mock real voiceover audio data")
    
    source_voiceover_script = source_control_dir / "ep01_voiceover_script.txt"
    source_voiceover_script.write_text("Mock voiceover script")
    
    source_voiceover_manifest = source_control_dir / "ep01_voiceover_manifest.json"
    voiceover_manifest_data = {
        "audio_kind": "voiceover",
        "duration": 9.336,
        "voiceover_duration": 9.336,
        "target_video_duration": 9.336,
        "duration_fit_passed": True,
        "tts_engine": "edge-tts"
    }
    with open(source_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(voiceover_manifest_data, f)
    
    source_final_with_voiceover_manifest = source_control_dir / "ep01_final_with_voiceover_manifest.json"
    final_manifest_data = {
        "duration": 9.336,
        "audio_attached": True,
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_final_with_voiceover_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    source_checksums = source_control_dir / "CHECKSUMS_SHA256.txt"
    source_checksums.write_text("mock checksums")
    
    source_freeze_summary = source_control_dir / "RC2_VOICE1_FREEZE_SUMMARY.json"
    freeze_summary_data = {
        "status": "accepted",
        "freeze_version": "RC2-VOICE1-FREEZE1",
        "audio_kind": "voiceover",
        "duration_fit_passed": True
    }
    with open(source_freeze_summary, 'w', encoding='utf-8') as f:
        json.dump(freeze_summary_data, f)
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-voice-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Check all JSON files in package for malformed absolute paths
    # source_roots.json and validation report are allowed to have absolute paths
    # (they document source roots and validation paths)
    # Control artifacts should not have malformed absolute package paths
    json_files_to_check = [
        output_pack_root / "output" / "control" / "artifact_index.json",
        output_pack_root / "output" / "control" / "ep01_voiceover_manifest.json",
        output_pack_root / "output" / "control" / "ep01_final_with_voiceover_manifest.json",
        output_pack_root / "output" / "control" / "ep01_shot01_ledger.json",
        output_pack_root / "output" / "control" / "RC2_VOICE1_FREEZE_SUMMARY.json",
    ]
    
    for json_file in json_files_to_check:
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for malformed absolute paths that look like package files but are absolute
            # Pattern: f:\ComfyUI\comfy-agent-mvp\output\... (missing data directory)
            malformed_pattern = r'f:\\\\ComfyUI\\\\comfy-agent-mvp\\\\output\\\\'
            import re
            if re.search(malformed_pattern, content, re.IGNORECASE):
                raise AssertionError(f"Found malformed absolute path in {json_file}: missing data directory in path")
            
            # Check for AppData paths (not allowed in control artifacts)
            if 'AppData' in content:
                raise AssertionError(f"Found AppData path in {json_file}")
            
            # Check for Temp paths (not allowed in control artifacts)
            if '\\Temp\\' in content or '/tmp/' in content:
                raise AssertionError(f"Found Temp path in {json_file}")
            
            # Check for pytest paths (not allowed in control artifacts)
            if 'pytest-of-' in content:
                raise AssertionError(f"Found pytest path in {json_file}")
    
    # Check checksums file for malformed paths
    checksums_file = output_pack_root / "proof" / "CHECKSUMS_SHA256.txt"
    if checksums_file.exists():
        checksums_content = checksums_file.read_text(encoding='utf-8')
        
        # Check for malformed absolute paths
        if 'f:\\ComfyUI\\comfy-agent-mvp\\output\\' in checksums_content.lower():
            raise AssertionError(f"Found malformed absolute path in checksums file")
        
        if 'AppData' in checksums_content or 'pytest-of-' in checksums_content:
            raise AssertionError(f"Found forbidden path pattern in checksums file")
