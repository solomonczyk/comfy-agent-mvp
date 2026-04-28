"""RC2-PACK1: Tests for package-rc2-demo CLI command."""
import sys
import json
import pytest
from pathlib import Path


def test_package_rc2_demo_cli_command_creates_package_root(tmp_path):
    """Test that package-rc2-demo CLI command creates package root."""
    import subprocess
    
    # Create mock source RC2 audio root
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    # Create mock media files
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    # Create mock control artifacts
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
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
    
    # Create mock RC1 frozen root
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    # Create mock RC2 render root
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    # Create output pack root
    output_pack_root = tmp_path / "output_pack"
    
    # Run package-rc2-demo command
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0, f"package-rc2-demo command failed: {result.stderr}"
    
    # Parse JSON output
    output_data = json.loads(result.stdout)
    assert output_data["status"] == "success"
    
    # Verify package root exists
    pack_root = Path(output_data["package_root"])
    assert pack_root.exists()
    assert pack_root.is_dir()


def test_package_rc2_demo_cli_copies_final_mp4_with_audio(tmp_path):
    """Test that package-rc2-demo CLI command copies final MP4 with audio."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify final MP4 with audio is copied
    final_with_audio = Path(output_data["final_with_audio_path"])
    assert final_with_audio.exists()
    assert final_with_audio.stat().st_size > 0


def test_package_rc2_demo_cli_copies_audio_artifact(tmp_path):
    """Test that package-rc2-demo CLI command copies audio artifact."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify audio artifact is copied
    audio_file = Path(output_data["audio_path"])
    assert audio_file.exists()
    assert audio_file.stat().st_size > 0


def test_package_rc2_demo_cli_copies_manifests_index_ledger(tmp_path):
    """Test that package-rc2-demo CLI command copies manifests, index, and ledger."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify control artifacts are copied
    audio_manifest = Path(output_data["audio_manifest_path"])
    assert audio_manifest.exists()
    
    final_with_audio_manifest = Path(output_data["final_with_audio_manifest_path"])
    assert final_with_audio_manifest.exists()
    
    artifact_index = Path(output_data["artifact_index_path"])
    assert artifact_index.exists()
    
    ledger = Path(output_data["ledger_path"])
    assert ledger.exists()


def test_package_rc2_demo_cli_writes_validation_json(tmp_path):
    """Test that package-rc2-demo CLI command writes validation JSON."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
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


def test_package_rc2_demo_cli_writes_readme(tmp_path):
    """Test that package-rc2-demo CLI command writes README."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
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
    assert "RC2 Demo Proof Pack" in readme_content
    assert "technical placeholder" in readme_content


def test_package_rc2_demo_cli_does_not_mutate_rc1(tmp_path):
    """Test that package-rc2-demo CLI command does not mutate RC1."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    # Create a marker file in RC1 to detect mutation
    rc1_marker = rc1_frozen_root / "rc1_marker.txt"
    rc1_marker.write_text("RC1 frozen marker")
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Verify RC1 marker file still exists and unchanged
    assert rc1_marker.exists()
    assert rc1_marker.read_text(encoding='utf-8') == "RC1 frozen marker"
    
    # Verify no new files were created in RC1
    rc1_files_before = ["rc1_marker.txt"]
    rc1_files_after = [f.name for f in rc1_frozen_root.iterdir()]
    assert set(rc1_files_after) == set(rc1_files_before)


def test_package_rc2_demo_cli_does_not_mutate_rc2_source_root(tmp_path):
    """Test that package-rc2-demo CLI command does not mutate RC2 source root."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    # Create a marker file in RC2 source root to detect mutation
    source_marker = source_root / "source_marker.txt"
    source_marker.write_text("RC2 source marker")
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    # Verify RC2 source marker file still exists and unchanged
    assert source_marker.exists()
    assert source_marker.read_text(encoding='utf-8') == "RC2 source marker"
    
    # Verify source files unchanged
    assert source_final_with_audio.read_bytes() == b"mock video with audio data"
    assert source_audio.read_bytes() == b"mock audio data"


def test_package_rc2_demo_cli_records_technical_placeholder_honestly(tmp_path):
    """Test that package-rc2-demo CLI command records technical_placeholder honestly."""
    import subprocess
    
    source_root = tmp_path / "source_rc"
    source_root.mkdir()
    
    source_final_dir = source_root / "output" / "final"
    source_final_dir.mkdir(parents=True)
    source_audio_dir = source_root / "output" / "audio"
    source_audio_dir.mkdir(parents=True)
    source_control_dir = source_root / "output" / "control"
    source_control_dir.mkdir(parents=True)
    
    source_final_with_audio = source_final_dir / "ep01_final_with_audio.mp4"
    source_final_with_audio.write_bytes(b"mock video with audio data")
    
    source_final_no_audio = source_final_dir / "ep01_final_no_audio.mp4"
    source_final_no_audio.write_bytes(b"mock video data")
    
    source_audio = source_audio_dir / "ep01_voiceover.wav"
    source_audio.write_bytes(b"mock audio data")
    
    source_audio_manifest = source_control_dir / "ep01_audio_manifest.json"
    audio_manifest_data = {
        "audio_kind": "technical_placeholder",
        "duration": 3.0,
        "sample_rate": 44100,
        "file_size": 264678
    }
    with open(source_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest_data, f)
    
    source_final_with_audio_manifest = source_control_dir / "ep01_final_with_audio_manifest.json"
    final_manifest_data = {
        "duration": 3.0,
        "resolution": "480x640",
        "file_size": 47281,
        "audio_attached": True
    }
    with open(source_final_with_audio_manifest, 'w', encoding='utf-8') as f:
        json.dump(final_manifest_data, f)
    
    source_artifact_index = source_control_dir / "artifact_index.json"
    artifact_index_data = {"episode_id": "ep01", "shot_id": "shot01", "artifacts": []}
    with open(source_artifact_index, 'w', encoding='utf-8') as f:
        json.dump(artifact_index_data, f)
    
    source_ledger = source_control_dir / "ep01_shot01_ledger.json"
    ledger_data = {"episode_id": "ep01", "shot_id": "shot01", "records": []}
    with open(source_ledger, 'w', encoding='utf-8') as f:
        json.dump(ledger_data, f)
    
    rc1_frozen_root = tmp_path / "rc1_frozen"
    rc1_frozen_root.mkdir()
    
    rc2_render_root = tmp_path / "rc2_render"
    rc2_render_root.mkdir()
    
    output_pack_root = tmp_path / "output_pack"
    
    result = subprocess.run(
        [sys.executable, "-m", "app", "package-rc2-demo",
         "--source-project-root", str(source_root),
         "--output-pack-root", str(output_pack_root),
         "--episode", "ep01",
         "--shot", "shot01",
         "--rc1-frozen-root", str(rc1_frozen_root),
         "--rc2-render-root", str(rc2_render_root),
         "--json"],
        capture_output=True,
        text=True,
        cwd="f:\\ComfyUI\\comfy-agent-mvp"
    )
    
    assert result.returncode == 0
    
    output_data = json.loads(result.stdout)
    
    # Verify audio_kind is technical_placeholder
    assert output_data["audio_kind"] == "technical_placeholder"
    
    # Verify boundary compliance
    assert output_data["frozen_rc1_mutated"] == False
    assert output_data["rc2_render_mutated"] == False
    assert output_data["comfyui_generation"] == False
    assert output_data["pipeline_action_rerun"] == False
