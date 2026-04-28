"""
Tests for Director-lite command implementations.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.director.commands import DirectorCommands
from app.director.history import DirectorHistory
from app.director.help import DirectorHelp
from app.director.models import (
    DirectorHistoryRecord,
    StatusResult,
    ValidationResult,
    InspectResult,
    HistoryEvent,
    HistoryResult
)


@pytest.fixture
def project_root():
    """Fixture for project root path."""
    return "f:\\ComfyUI\\comfy-agent-mvp\\data\\rc_mir_erdan_ep01"


@pytest.fixture
def episode_id():
    """Fixture for episode ID."""
    return "ep01"


@pytest.fixture
def shot_id():
    """Fixture for shot ID."""
    return "shot01"


@pytest.fixture
def director_commands(project_root):
    """Fixture for DirectorCommands instance."""
    return DirectorCommands(project_root)


class TestDirectorCommands:
    """Tests for DirectorCommands class."""
    
    def test_status_returns_terminal_state(self, director_commands, episode_id, shot_id):
        """Test that status command returns terminal RC1 state."""
        result = director_commands.status(episode_id, shot_id, json_output=True)
        
        assert isinstance(result, StatusResult)
        assert result.current_state == "episode_rendered"
        assert result.expected_next_action == "none"
        assert result.is_done is True
        assert result.available_actions == []
        assert "generate_frames" in result.blocked_actions
    
    def test_validate_returns_passed(self, director_commands, episode_id, shot_id):
        """Test that validate command returns validation passed."""
        result = director_commands.validate(episode_id, shot_id, json_output=True)
        
        assert isinstance(result, ValidationResult)
        assert result.validation_status == "passed"
        assert result.passed_checks == 67
        assert result.warnings == 0
        assert result.errors == 0
    
    def test_inspect_lists_artifacts(self, director_commands, episode_id, shot_id):
        """Test that inspect command lists artifact paths."""
        result = director_commands.inspect(episode_id, shot_id, json_output=True)
        
        assert isinstance(result, InspectResult)
        assert result.project_profile is not None
        assert result.prompt_pack is not None
        assert result.frames_manifest is not None
        assert result.generated_frame is not None
        assert result.ledger is not None
        assert result.artifact_index is not None
    
    def test_history_returns_events(self, director_commands, episode_id, shot_id):
        """Test that history command returns ledger events."""
        result = director_commands.history(episode_id, shot_id, json_output=True)
        
        assert isinstance(result, HistoryResult)
        assert len(result.events) > 0
        assert "total_events" in result.summary
        assert result.summary["total_events"] > 0
    
    def test_help_returns_text(self, director_commands):
        """Test that help command returns help text."""
        result = director_commands.help()
        
        assert isinstance(result, str)
        assert "Director-lite" in result
        assert "status" in result
        assert "validate" in result


class TestDirectorHistory:
    """Tests for DirectorHistory class."""
    
    def test_log_command_writes_history(self, project_root):
        """Test that log_command writes to history file."""
        history = DirectorHistory(project_root)
        
        record = history.log_command(
            command="status",
            episode_id="ep01",
            shot_id="shot01",
            success=True
        )
        
        assert isinstance(record, DirectorHistoryRecord)
        assert record.command == "status"
        assert record.episode_id == "ep01"
        assert record.shot_id == "shot01"
        assert record.read_only is True
        assert record.success is True
    
    def test_get_history_returns_records(self, project_root):
        """Test that get_history returns history records."""
        history = DirectorHistory(project_root)
        
        # Log a command first
        history.log_command("status", "ep01", "shot01", True)
        
        records = history.get_history()
        
        assert len(records) > 0
        assert all(isinstance(r, DirectorHistoryRecord) for r in records)
    
    def test_get_history_with_limit(self, project_root):
        """Test that get_history respects limit parameter."""
        history = DirectorHistory(project_root)
        
        # Log multiple commands
        for i in range(5):
            history.log_command(f"command_{i}", "ep01", "shot01", True)
        
        records = history.get_history(limit=3)
        
        assert len(records) == 3


class TestDirectorHelp:
    """Tests for DirectorHelp class."""
    
    def test_get_command_help(self):
        """Test that get_command_help returns help for a command."""
        help_data = DirectorHelp.get_command_help("status")
        
        assert "description" in help_data
        assert "usage" in help_data
        assert "parameters" in help_data
    
    def test_list_commands(self):
        """Test that list_commands returns all commands."""
        commands = DirectorHelp.list_commands()
        
        assert isinstance(commands, list)
        assert "status" in commands
        assert "validate" in commands
        assert "inspect" in commands
        assert "history" in commands
        assert "help" in commands
    
    def test_format_command_help(self):
        """Test that format_command_help returns formatted help."""
        help_text = DirectorHelp.format_command_help("status")
        
        assert isinstance(help_text, str)
        assert "status" in help_text
        assert "Description:" in help_text
        assert "Usage:" in help_text
    
    def test_format_overview(self):
        """Test that format_overview returns formatted overview."""
        overview = DirectorHelp.format_overview()
        
        assert isinstance(overview, str)
        assert "Director-lite" in overview
        assert "Commands:" in overview


class TestDirectorModels:
    """Tests for director models."""
    
    def test_director_history_record_to_dict(self):
        """Test that DirectorHistoryRecord.to_dict works."""
        record = DirectorHistoryRecord(
            timestamp="2026-04-28T06:00:00Z",
            command="status",
            episode_id="ep01",
            shot_id="shot01",
            project_root="/path/to/project",
            read_only=True,
            success=True
        )
        
        data = record.to_dict()
        
        assert data["timestamp"] == "2026-04-28T06:00:00Z"
        assert data["command"] == "status"
        assert data["read_only"] is True
        assert data["success"] is True
    
    def test_director_history_record_from_dict(self):
        """Test that DirectorHistoryRecord.from_dict works."""
        data = {
            "timestamp": "2026-04-28T06:00:00Z",
            "command": "status",
            "episode_id": "ep01",
            "shot_id": "shot01",
            "project_root": "/path/to/project",
            "read_only": True,
            "success": True
        }
        
        record = DirectorHistoryRecord.from_dict(data)
        
        assert record.timestamp == "2026-04-28T06:00:00Z"
        assert record.command == "status"
        assert record.read_only is True
        assert record.success is True
    
    def test_status_result_to_dict(self):
        """Test that StatusResult.to_dict works."""
        result = StatusResult(
            current_state="episode_rendered",
            expected_next_action="none",
            is_done=True,
            available_actions=[],
            blocked_actions={"generate_frames": "shot is already done"},
            artifact_path="output/control/ep01_shot01_final_manifest.json",
            brief_path="data/briefs/ep01_shot01_brief.md",
            ledger_path="output/control/ep01_shot01_ledger.json",
            known_limitations=["no audio"]
        )
        
        data = result.to_dict()
        
        assert data["current_state"] == "episode_rendered"
        assert data["expected_next_action"] == "none"
        assert data["is_done"] is True
    
    def test_validation_result_to_dict(self):
        """Test that ValidationResult.to_dict works."""
        result = ValidationResult(
            validation_status="passed",
            passed_checks=67,
            warnings=0,
            errors=0,
            artifact_index_status="exists",
            terminal_state_status="terminal"
        )
        
        data = result.to_dict()
        
        assert data["validation_status"] == "passed"
        assert data["passed_checks"] == 67
        assert data["errors"] == 0
    
    def test_inspect_result_to_dict(self):
        """Test that InspectResult.to_dict works."""
        result = InspectResult(
            project_profile="output/control/project_profile.json",
            prompt_pack="output/control/prompt_pack.json",
            submitted_workflow="output/control/ep01_shot01_submitted_workflow.json",
            observed_settings="output/control/ep01_shot01_observed_settings.json",
            frames_manifest="output/control/frames_manifest.json",
            generated_frame="output/frames/ep01_shot01/000001.png",
            qc_report="output/control/ep01_shot01_qc_report.json",
            scene_mp4="output/scenes/ep01_shot01/scene.mp4",
            scene_manifest="output/control/ep01_shot01_scene_manifest.json",
            qa_report="output/control/qa_report.json",
            audio_manifest="output/control/ep01_shot01_audio_manifest.json",
            final_manifest="output/control/ep01_shot01_final_manifest.json",
            ledger="output/control/ep01_shot01_ledger.json",
            artifact_index="output/control/artifact_index.json"
        )
        
        data = result.to_dict()
        
        assert data["project_profile"] == "output/control/project_profile.json"
        assert data["prompt_pack"] == "output/control/prompt_pack.json"
    
    def test_history_event_to_dict(self):
        """Test that HistoryEvent.to_dict works."""
        event = HistoryEvent(
            event_type="state_transition",
            timestamp="2026-04-28T06:00:00Z",
            requested_action=None,
            success=None,
            handler_status=None
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "state_transition"
        assert data["timestamp"] == "2026-04-28T06:00:00Z"
    
    def test_history_result_to_dict(self):
        """Test that HistoryResult.to_dict works."""
        event = HistoryEvent(
            event_type="state_transition",
            timestamp="2026-04-28T06:00:00Z",
            requested_action=None,
            success=None,
            handler_status=None
        )
        
        result = HistoryResult(
            events=[event],
            summary={"total_events": 1}
        )
        
        data = result.to_dict()
        
        assert len(data["events"]) == 1
        assert data["summary"]["total_events"] == 1
