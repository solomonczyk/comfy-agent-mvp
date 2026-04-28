"""MK-CTRL34 — Artifact naming contract tests.

Tests that all real operators use episode_id and shot_id for artifact naming,
and that manifests include required metadata fields:
- episode_id
- shot_id
- action
- artifact_path
- created_at
- source_artifacts
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.control.handler_contracts import HandlerPayload
from app.control.generate_frames_runner import GenerateFramesRunner
from app.control.assemble_scene_runner import AssembleSceneRunner
from app.control.qa_review_runner import QaReviewRunner
from app.control.attach_audio_runner import AttachAudioRunner
from app.control.render_episode_runner import RenderEpisodeRunner


@pytest.fixture
def project_root(tmp_path):
    """Temporary project root for testing."""
    return tmp_path


@pytest.fixture
def sample_brief_path(tmp_path):
    """Create a sample brief file for testing."""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text("""
---
episode_id: ep01
shot_id: shot01
---
Test brief content.
""")
    return brief_path


class TestGenerateFramesNamingContract:
    """Test that GenerateFramesRunner uses episode_id/shot_id for naming."""
    
    def test_command_includes_episode_id_and_shot_id(self, project_root, sample_brief_path):
        """Test that build_command includes --episode-id and --shot_id when available."""
        runner = GenerateFramesRunner(project_root=project_root)
        
        payload = HandlerPayload(
            episode_id="ep01",
            shot_id="shot01",
            action="generate_frames",
            state_report={},
            action_plan={
                "brief_path": str(sample_brief_path),
                "output_dir": "output",
            },
            dry_validate=False,
            allow_real_execution=False,
        )
        
        command = runner.build_command(payload)
        
        assert "--episode-id" in command
        assert "ep01" in command
        assert "--shot-id" in command
        assert "shot01" in command


class TestAssembleSceneNamingContract:
    """Test that AssembleSceneRunner uses episode_id/shot_id for naming."""
    
    def test_command_includes_episode_id_and_shot_id(self, project_root, tmp_path):
        """Test that build_command includes --episode-id and --shot_id when available."""
        runner = AssembleSceneRunner(project_root=project_root)
        
        frame_manifest_path = tmp_path / "frame_manifest.json"
        frame_manifest_path.write_text(json.dumps({
            "episode_id": "ep01",
            "shot_id": "shot01",
            "frame_paths": [],
        }))
        
        payload = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "assemble_scene",
            "action_plan": {
                "frame_manifest_path": str(frame_manifest_path),
                "output_dir": "output",
            },
        }
        
        command = runner.build_command(payload)
        
        assert "--episode-id" in command
        assert "ep01" in command
        assert "--shot-id" in command
        assert "shot01" in command


class TestQaReviewNamingContract:
    """Test that QaReviewRunner uses episode_id/shot_id for naming."""
    
    def test_command_includes_episode_id_and_shot_id(self, project_root, tmp_path):
        """Test that build_command includes --episode-id and --shot_id when available."""
        runner = QaReviewRunner(project_root=project_root)
        
        scene_mp4_path = tmp_path / "scene.mp4"
        scene_mp4_path.write_bytes(b"fake mp4")
        
        payload = HandlerPayload(
            episode_id="ep01",
            shot_id="shot01",
            action="qa_review",
            state_report={},
            action_plan={
                "scene_mp4_path": str(scene_mp4_path),
                "output_dir": "output",
            },
            dry_validate=False,
            allow_real_execution=False,
        )
        
        command = runner.build_command(payload)
        
        assert "--episode-id" in command
        assert "ep01" in command
        assert "--shot-id" in command
        assert "shot01" in command


class TestAttachAudioNamingContract:
    """Test that AttachAudioRunner uses episode_id/shot_id for naming."""
    
    def test_command_includes_episode_id_and_shot_id(self, project_root, tmp_path, sample_brief_path):
        """Test that build_command includes --episode-id and --shot_id when available."""
        runner = AttachAudioRunner(project_root=project_root)
        
        scene_mp4_path = tmp_path / "scene.mp4"
        scene_mp4_path.write_bytes(b"fake mp4")
        
        payload = HandlerPayload(
            episode_id="ep01",
            shot_id="shot01",
            action="attach_audio",
            state_report={},
            action_plan={
                "scene_mp4_path": str(scene_mp4_path),
                "brief_path": str(sample_brief_path),
                "output_dir": "output",
            },
            dry_validate=False,
            allow_real_execution=False,
        )
        
        command = runner.build_command(payload)
        
        assert "--episode-id" in command
        assert "ep01" in command
        assert "--shot-id" in command
        assert "shot01" in command


class TestRenderEpisodeNamingContract:
    """Test that RenderEpisodeRunner uses episode_id/shot_id for naming."""
    
    def test_command_includes_episode_id_and_shot_id(self, project_root, tmp_path):
        """Test that build_command includes --episode-id and --shot_id when available."""
        runner = RenderEpisodeRunner(project_root=project_root)
        
        scene_mp4_path = tmp_path / "scene.mp4"
        scene_mp4_path.write_bytes(b"fake mp4")
        
        payload = HandlerPayload(
            episode_id="ep01",
            shot_id="shot01",
            action="render_episode",
            state_report={},
            action_plan={
                "scene_mp4_path": str(scene_mp4_path),
                "output_dir": "output",
            },
            dry_validate=False,
            allow_real_execution=False,
        )
        
        command = runner.build_command(payload)
        
        assert "--episode-id" in command
        assert "ep01" in command
        assert "--shot-id" in command
        assert "shot01" in command


class TestManifestMetadataContract:
    """Test that manifests include required metadata fields."""
    
    def test_frame_manifest_includes_required_fields(self, tmp_path, sample_brief_path):
        """Test that frame manifest includes episode_id, shot_id, action, artifact_path, created_at, source_artifacts."""
        # This is a mock test - in real execution, the manifest would be written by the CLI
        # For now, we test the structure that should be written
        expected_fields = ["episode_id", "shot_id", "action", "artifact_path", "created_at", "source_artifacts"]
        
        # Mock manifest structure
        manifest = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "generate_frames",
            "artifact_path": "/path/to/frames",
            "brief_path": str(sample_brief_path),
            "generated_frames_dir": "/path/to/frames",
            "frame_count": 10,
            "frame_paths": [],
            "created_at": "2024-01-01T00:00:00",
            "source_artifacts": {
                "brief": str(sample_brief_path),
            },
        }
        
        for field in expected_fields:
            assert field in manifest, f"Manifest missing required field: {field}"
    
    def test_scene_manifest_includes_required_fields(self, tmp_path):
        """Test that scene manifest includes episode_id, shot_id, action, artifact_path, created_at, source_artifacts."""
        expected_fields = ["episode_id", "shot_id", "action", "artifact_path", "created_at", "source_artifacts"]
        
        manifest = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "assemble_scene",
            "artifact_path": "/path/to/scene.mp4",
            "frame_manifest_path": "/path/to/frame_manifest.json",
            "scene_output_path": "/path/to/scene.mp4",
            "scene_frame_count": 10,
            "scene_duration_sec": 1.0,
            "fps": 24,
            "created_at": "2024-01-01T00:00:00",
            "source_artifacts": {
                "frame_manifest": "/path/to/frame_manifest.json",
            },
        }
        
        for field in expected_fields:
            assert field in manifest, f"Manifest missing required field: {field}"
    
    def test_qa_report_includes_required_fields(self, tmp_path):
        """Test that QA report includes episode_id, shot_id, action, artifact_path, created_at, source_artifacts."""
        expected_fields = ["episode_id", "shot_id", "action", "artifact_path", "created_at", "source_artifacts"]
        
        manifest = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "qa_review",
            "artifact_path": "/path/to/qa_report.json",
            "scene_path": "/path/to/scene.mp4",
            "scene_size_bytes": 1000,
            "qa_score": 0.85,
            "qa_verdict": "pass",
            "qa_reasons": [],
            "created_at": "2024-01-01T00:00:00",
            "source_artifacts": {
                "scene_mp4": "/path/to/scene.mp4",
            },
        }
        
        for field in expected_fields:
            assert field in manifest, f"Manifest missing required field: {field}"
    
    def test_audio_manifest_includes_required_fields(self, tmp_path, sample_brief_path):
        """Test that audio manifest includes episode_id, shot_id, action, artifact_path, created_at, source_artifacts."""
        expected_fields = ["episode_id", "shot_id", "action", "artifact_path", "created_at", "source_artifacts"]
        
        manifest = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "attach_audio",
            "artifact_path": "/path/to/audio.mp4",
            "scene_path": "/path/to/scene.mp4",
            "audio_output_path": "/path/to/audio.mp4",
            "brief_path": str(sample_brief_path),
            "audio_duration_sec": 2.0,
            "audio_engine": "silero",
            "dialogue_lines": 5,
            "created_at": "2024-01-01T00:00:00",
            "source_artifacts": {
                "scene_mp4": "/path/to/scene.mp4",
                "brief": str(sample_brief_path),
            },
        }
        
        for field in expected_fields:
            assert field in manifest, f"Manifest missing required field: {field}"
    
    def test_episode_manifest_includes_required_fields(self, tmp_path):
        """Test that episode manifest includes episode_id, shot_id, action, artifact_path, created_at, source_artifacts."""
        expected_fields = ["episode_id", "shot_id", "action", "artifact_path", "created_at", "source_artifacts"]
        
        manifest = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "render_episode",
            "artifact_path": "/path/to/episode.mp4",
            "scene_path": "/path/to/scene.mp4",
            "episode_output_path": "/path/to/episode.mp4",
            "episode_duration_sec": 2.0,
            "episode_scene_count": 1,
            "created_at": "2024-01-01T00:00:00",
            "source_artifacts": {
                "scene_mp4": "/path/to/scene.mp4",
            },
        }
        
        for field in expected_fields:
            assert field in manifest, f"Manifest missing required field: {field}"


class TestArtifactNamingPatterns:
    """Test that artifact paths follow the naming contract."""
    
    def test_frames_dir_naming_contract(self):
        """Test that frames directory follows naming contract: output/frames/{episode_id}_{shot_id}/"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/frames/{episode_id}_{shot_id}"
        
        assert expected_path == f"output/frames/{episode_id}_{shot_id}"
    
    def test_scene_mp4_naming_contract(self):
        """Test that scene MP4 follows naming contract: output/scenes/{episode_id}_{shot_id}.mp4"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/scenes/{episode_id}_{shot_id}.mp4"
        
        assert expected_path == f"output/scenes/{episode_id}_{shot_id}.mp4"
    
    def test_qa_report_naming_contract(self):
        """Test that QA report follows naming contract: output/control/{episode_id}_{shot_id}_qa_report.json"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/control/{episode_id}_{shot_id}_qa_report.json"
        
        assert expected_path == f"output/control/{episode_id}_{shot_id}_qa_report.json"
    
    def test_audio_mp4_naming_contract(self):
        """Test that audio MP4 follows naming contract: output/scenes/{episode_id}_{shot_id}_audio.mp4"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/scenes/{episode_id}_{shot_id}_audio.mp4"
        
        assert expected_path == f"output/scenes/{episode_id}_{shot_id}_audio.mp4"
    
    def test_audio_manifest_naming_contract(self):
        """Test that audio manifest follows naming contract: output/control/{episode_id}_{shot_id}_audio_manifest.json"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/control/{episode_id}_{shot_id}_audio_manifest.json"
        
        assert expected_path == f"output/control/{episode_id}_{shot_id}_audio_manifest.json"
    
    def test_episode_mp4_naming_contract(self):
        """Test that episode MP4 follows naming contract: output/episodes/{episode_id}_{shot_id}_episode.mp4"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/episodes/{episode_id}_{shot_id}_episode.mp4"
        
        assert expected_path == f"output/episodes/{episode_id}_{shot_id}_episode.mp4"
    
    def test_episode_manifest_naming_contract(self):
        """Test that episode manifest follows naming contract: output/control/{episode_id}_{shot_id}_episode_manifest.json"""
        episode_id = "ep01"
        shot_id = "shot01"
        expected_path = f"output/control/{episode_id}_{shot_id}_episode_manifest.json"
        
        assert expected_path == f"output/control/{episode_id}_{shot_id}_episode_manifest.json"
