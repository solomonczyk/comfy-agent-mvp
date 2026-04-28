"""
Director-lite command implementations.

Provides read-only commands for inspecting frozen RC proof packs.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.director.models import (
    StatusResult,
    ValidationResult,
    InspectResult,
    HistoryEvent,
    HistoryResult,
    DirectorHistoryRecord
)
from app.director.history import DirectorHistory
from app.director.help import DirectorHelp


class DirectorCommands:
    """Director-lite command implementations."""
    
    def __init__(self, project_root: str):
        """Initialize director commands.
        
        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.history_logger = DirectorHistory(project_root)
    
    def status(
        self,
        episode_id: str,
        shot_id: str,
        json_output: bool = False
    ) -> StatusResult:
        """Get current pipeline status.
        
        Args:
            episode_id: Episode ID
            shot_id: Shot ID
            json_output: Whether to output as JSON
            
        Returns:
            StatusResult with current status
        """
        # Read shot state
        state_path = self.control_dir / episode_id / f"{shot_id}_state.json"
        
        if not state_path.exists():
            raise FileNotFoundError(f"Shot state not found: {state_path}")
        
        with open(state_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        # Read artifact index for known limitations
        artifact_index_path = self.control_dir / "artifact_index.json"
        known_limitations = None
        
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r', encoding='utf-8') as f:
                artifact_index = json.load(f)
                known_limitations = artifact_index.get("known_limitations")
        
        # Read final manifest if exists
        final_manifest_path = self.control_dir / f"{episode_id}_{shot_id}_final_manifest.json"
        artifact_path = str(final_manifest_path) if final_manifest_path.exists() else None
        
        # Read brief path
        brief_path = self.project_root / "data" / "briefs" / f"{episode_id}_{shot_id}_brief.md"
        brief_path = str(brief_path) if brief_path.exists() else None
        
        # Read ledger path
        ledger_path = self.control_dir / f"{episode_id}_{shot_id}_ledger.json"
        ledger_path = str(ledger_path) if ledger_path.exists() else None
        
        # Derive is_done from current_state and expected_next_action
        is_done = (
            state_data.get("current_state") == "episode_rendered" or
            state_data.get("expected_next_action") == "none"
        )
        
        # For informational purposes, show blocked actions even though Director-lite is read-only
        production_actions = ["generate_frames", "assemble_scene", "qa_review", "attach_audio", "render_episode"]
        blocked_actions = {
            action: "shot is already done"
            for action in production_actions
        }
        
        result = StatusResult(
            current_state=state_data.get("current_state", "unknown"),
            expected_next_action=state_data.get("expected_next_action", "unknown"),
            is_done=is_done,
            available_actions=[],  # Director-lite is read-only, doesn't compute available actions
            blocked_actions=blocked_actions,  # Informational only
            artifact_path=artifact_path,
            brief_path=brief_path,
            ledger_path=ledger_path,
            known_limitations=known_limitations
        )
        
        # Log command
        self.history_logger.log_command(
            command="status",
            episode_id=episode_id,
            shot_id=shot_id,
            success=True
        )
        
        return result
    
    def validate(
        self,
        episode_id: str,
        shot_id: str,
        json_output: bool = False
    ) -> ValidationResult:
        """Validate RC artifacts.
        
        Args:
            episode_id: Episode ID
            shot_id: Shot ID
            json_output: Whether to output as JSON
            
        Returns:
            ValidationResult with validation status
        """
        # Import validation logic directly to avoid subprocess encoding issues
        import sys
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        
        from validate_rc_artifacts import RCValidator
        
        # Run validation
        validator = RCValidator(str(self.project_root), episode_id, shot_id)
        
        # Capture print output by redirecting stdout
        from io import StringIO
        import contextlib
        
        output_buffer = StringIO()
        with contextlib.redirect_stdout(output_buffer):
            success = validator.run_all_validations()
        
        output = output_buffer.getvalue()
        
        # Get counts from validator
        passed = len(validator.passed_checks)
        warnings = len(validator.warnings)
        errors = len(validator.errors)
        
        validation_status = "passed" if errors == 0 else "failed"
        
        # Check terminal state
        state_path = self.control_dir / episode_id / f"{shot_id}_state.json"
        terminal_state_status = "unknown"
        
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                if state_data.get("current_state") == "episode_rendered":
                    terminal_state_status = "terminal"
        
        # Check artifact index
        artifact_index_path = self.control_dir / "artifact_index.json"
        artifact_index_status = "unknown"
        
        if artifact_index_path.exists():
            artifact_index_status = "exists"
        
        result = ValidationResult(
            validation_status=validation_status,
            passed_checks=passed,
            warnings=warnings,
            errors=errors,
            artifact_index_status=artifact_index_status,
            terminal_state_status=terminal_state_status,
            details={"output": output}
        )
        
        # Log command
        self.history_logger.log_command(
            command="validate",
            episode_id=episode_id,
            shot_id=shot_id,
            success=True
        )
        
        return result
    
    def inspect(
        self,
        episode_id: str,
        shot_id: str,
        json_output: bool = False
    ) -> InspectResult:
        """Inspect artifact paths.
        
        Args:
            episode_id: Episode ID
            shot_id: Shot ID
            json_output: Whether to output as JSON
            
        Returns:
            InspectResult with artifact paths
        """
        # Read artifact index
        artifact_index_path = self.control_dir / "artifact_index.json"
        
        if not artifact_index_path.exists():
            raise FileNotFoundError(f"Artifact index not found: {artifact_index_path}")
        
        with open(artifact_index_path, 'r', encoding='utf-8') as f:
            artifact_index = json.load(f)
        
        # Extract artifact paths from list
        artifacts_list = artifact_index.get("artifacts", [])
        artifacts_dict = {}
        for artifact in artifacts_list:
            if isinstance(artifact, dict):
                name = artifact.get("name", "")
                path = artifact.get("path")
                if name and path:
                    artifacts_dict[name] = path
        
        # Read frames manifest to find generated frame
        frames_manifest_path = self.control_dir / "frames_manifest.json"
        generated_frame = None
        if frames_manifest_path.exists():
            try:
                with open(frames_manifest_path, 'r', encoding='utf-8') as f:
                    frames_manifest = json.load(f)
                # frames_manifest has "frame_paths" array with absolute paths
                frame_paths = frames_manifest.get("frame_paths", [])
                if frame_paths:
                    generated_frame = frame_paths[0]
            except (json.JSONDecodeError, KeyError):
                pass
        
        result = InspectResult(
            project_profile=artifacts_dict.get("project_profile.json"),
            prompt_pack=artifacts_dict.get("prompt_pack.json"),
            submitted_workflow=artifacts_dict.get("ep01_shot01_submitted_workflow.json"),
            observed_settings=artifacts_dict.get("ep01_shot01_observed_settings.json"),
            frames_manifest=artifacts_dict.get("frames_manifest.json"),
            generated_frame=generated_frame,
            qc_report=artifacts_dict.get("ep01_shot01_qc_report.json"),
            scene_mp4=artifacts_dict.get("scene.mp4"),
            scene_manifest=artifacts_dict.get("ep01_shot01_scene_manifest.json"),
            qa_report=artifacts_dict.get("qa_report.json"),
            audio_manifest=artifacts_dict.get("ep01_shot01_audio_manifest.json"),
            final_manifest=artifacts_dict.get("ep01_shot01_final_manifest.json"),
            ledger=artifacts_dict.get("ep01_shot01_ledger.json"),
            artifact_index=str(artifact_index_path)
        )
        
        # Log command
        self.history_logger.log_command(
            command="inspect",
            episode_id=episode_id,
            shot_id=shot_id,
            success=True
        )
        
        return result
    
    def history(
        self,
        episode_id: str,
        shot_id: str,
        json_output: bool = False
    ) -> HistoryResult:
        """Get pipeline event history from ledger.
        
        Args:
            episode_id: Episode ID
            shot_id: Shot ID
            json_output: Whether to output as JSON
            
        Returns:
            HistoryResult with events and summary
        """
        # Read ledger
        ledger_path = self.control_dir / f"{episode_id}_{shot_id}_ledger.json"
        
        if not ledger_path.exists():
            raise FileNotFoundError(f"Ledger not found: {ledger_path}")
        
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger_data = json.load(f)
        
        # Extract events - ledger might have different structure
        events_data = ledger_data.get("events", [])
        events = []
        
        for event_data in events_data:
            event = HistoryEvent(
                event_type=event_data.get("event_type", "unknown"),
                timestamp=event_data.get("timestamp", ""),
                requested_action=event_data.get("requested_action"),
                success=event_data.get("success"),
                handler_status=event_data.get("handler_status")
            )
            events.append(event)
        
        # If no events found, try alternative structure
        if not events:
            # Try reading from "records" field if it exists
            records_data = ledger_data.get("records", [])
            for record_data in records_data:
                event = HistoryEvent(
                    event_type=record_data.get("event_type", "unknown"),
                    timestamp=record_data.get("timestamp", ""),
                    requested_action=record_data.get("requested_action"),
                    success=record_data.get("success"),
                    handler_status=record_data.get("handler_status")
                )
                events.append(event)
        
        # Create summary
        summary = {
            "total_events": len(events),
            "state_transitions": len([e for e in events if e.event_type == "state_transition"]),
            "actions_executed": len([e for e in events if e.event_type == "action_executed"]),
            "actions_denied": len([e for e in events if e.event_type == "action_denied"]),
            "inspections": len([e for e in events if e.event_type == "inspect"])
        }
        
        result = HistoryResult(
            events=events,
            summary=summary
        )
        
        # Log command
        self.history_logger.log_command(
            command="history",
            episode_id=episode_id,
            shot_id=shot_id,
            success=True
        )
        
        return result
    
    def help(self, command: Optional[str] = None) -> str:
        """Get help for director commands.
        
        Args:
            command: Optional command name for specific help
            
        Returns:
            Help text
        """
        if command:
            return DirectorHelp.format_command_help(command)
        else:
            return DirectorHelp.format_overview()
