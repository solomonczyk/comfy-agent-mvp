"""
Data models for Director-lite commands and history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class DirectorCommandType(Enum):
    """Types of director commands."""
    STATUS = "status"
    VALIDATE = "validate"
    INSPECT = "inspect"
    HISTORY = "history"
    HELP = "help"


@dataclass
class DirectorCommand:
    """Represents a director command execution."""
    command_type: DirectorCommandType
    project_root: str
    episode_id: str
    shot_id: Optional[str] = None
    json_output: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = False
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class DirectorHistoryRecord:
    """Represents a record in director command history."""
    timestamp: str
    command: str
    episode_id: str
    shot_id: Optional[str]
    project_root: str
    read_only: bool = True
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "command": self.command,
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "project_root": self.project_root,
            "read_only": self.read_only,
            "success": self.success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DirectorHistoryRecord':
        """Create from dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            command=data.get("command", ""),
            episode_id=data.get("episode_id", ""),
            shot_id=data.get("shot_id"),
            project_root=data.get("project_root", ""),
            read_only=data.get("read_only", True),
            success=data.get("success", False)
        )


@dataclass
class StatusResult:
    """Result of status command."""
    current_state: str
    expected_next_action: str
    is_done: bool
    available_actions: List[str]
    blocked_actions: Dict[str, str]
    artifact_path: Optional[str]
    brief_path: Optional[str]
    ledger_path: Optional[str]
    known_limitations: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "is_done": self.is_done,
            "available_actions": self.available_actions,
            "blocked_actions": self.blocked_actions,
            "artifact_path": self.artifact_path,
            "brief_path": self.brief_path,
            "ledger_path": self.ledger_path,
            "known_limitations": self.known_limitations or []
        }


@dataclass
class ValidationResult:
    """Result of validate command."""
    validation_status: str
    passed_checks: int
    warnings: int
    errors: int
    artifact_index_status: str
    terminal_state_status: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "validation_status": self.validation_status,
            "passed_checks": self.passed_checks,
            "warnings": self.warnings,
            "errors": self.errors,
            "artifact_index_status": self.artifact_index_status,
            "terminal_state_status": self.terminal_state_status,
            "details": self.details or {}
        }


@dataclass
class InspectResult:
    """Result of inspect command."""
    project_profile: Optional[str]
    prompt_pack: Optional[str]
    submitted_workflow: Optional[str]
    observed_settings: Optional[str]
    frames_manifest: Optional[str]
    generated_frame: Optional[str]
    qc_report: Optional[str]
    scene_mp4: Optional[str]
    scene_manifest: Optional[str]
    qa_report: Optional[str]
    audio_manifest: Optional[str]
    final_manifest: Optional[str]
    ledger: Optional[str]
    artifact_index: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_profile": self.project_profile,
            "prompt_pack": self.prompt_pack,
            "submitted_workflow": self.submitted_workflow,
            "observed_settings": self.observed_settings,
            "frames_manifest": self.frames_manifest,
            "generated_frame": self.generated_frame,
            "qc_report": self.qc_report,
            "scene_mp4": self.scene_mp4,
            "scene_manifest": self.scene_manifest,
            "qa_report": self.qa_report,
            "audio_manifest": self.audio_manifest,
            "final_manifest": self.final_manifest,
            "ledger": self.ledger,
            "artifact_index": self.artifact_index
        }


@dataclass
class HistoryEvent:
    """Represents an event from the ledger."""
    event_type: str
    timestamp: str
    requested_action: Optional[str]
    success: Optional[bool]
    handler_status: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "requested_action": self.requested_action,
            "success": self.success,
            "handler_status": self.handler_status
        }


@dataclass
class HistoryResult:
    """Result of history command."""
    events: List[HistoryEvent]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "events": [event.to_dict() for event in self.events],
            "summary": self.summary
        }
