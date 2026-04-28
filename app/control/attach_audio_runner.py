"""Attach audio runner for executing attach-audio as a subprocess.

MK-CTRL32 — Runner for attach_audio action that calls the attach-audio CLI command.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .handler_contracts import HandlerPayload
from .real_execution_guard import is_real_execution_globally_enabled


class AttachAudioRunner:
    """Runner for attach_audio action that calls the attach-audio CLI command.

    This runner:
    - Calls `python -m app attach-audio --scene <scene_mp4_path> --brief <brief_path> --output <output_dir>`
    - Parses the output to extract audio output path and manifest
    - Returns artifacts dict with scene_mp4_with_audio_path, audio_manifest_path, artifact_accepted

    Safety:
    - Requires allow_subprocess_execution=True to actually run
    - Otherwise returns dry-run artifacts without executing
    """

    def __init__(
        self,
        project_root: Path | str = ".",
        allow_subprocess_execution: bool = False,
        timeout_sec: int = 300,
    ) -> None:
        """Initialize attach audio runner.

        Args:
            project_root: Root directory for the project.
            allow_subprocess_execution: If True, actually run subprocess.
                If False, return dry-run artifacts without executing.
            timeout_sec: Timeout for subprocess execution in seconds.
        """
        self.project_root = Path(project_root)
        self.allow_subprocess_execution = allow_subprocess_execution
        self.timeout_sec = timeout_sec

    def build_command(self, payload: HandlerPayload | dict) -> list[str]:
        """Build the attach-audio command from payload.

        Args:
            payload: HandlerPayload or dict containing action_plan with scene_mp4_path and brief_path.

        Returns:
            List of command arguments.
        """
        # Normalize payload to dict
        if isinstance(payload, HandlerPayload):
            action_plan = payload.action_plan or {}
            episode_id = payload.episode_id if payload.episode_id else ""
            shot_id = payload.shot_id if payload.shot_id else ""
        else:
            action_plan = payload.get("action_plan", {})
            episode_id = payload.get("episode_id", "")
            shot_id = payload.get("shot_id", "")
        
        scene_mp4_path = action_plan.get("scene_mp4_path")
        brief_path = action_plan.get("brief_path")
        output_dir = action_plan.get("output_dir", "output")

        # Resolve output_dir relative to project_root
        if not Path(output_dir).is_absolute():
            output_dir = self.project_root / output_dir

        command = [
            sys.executable,
            "-m",
            "app",
            "attach-audio",
            "--scene",
            str(scene_mp4_path),
            "--brief",
            str(brief_path),
            "--output",
            str(output_dir),
        ]
        
        # MK-CTRL34 — Add episode_id and shot_id if available
        if episode_id:
            command.extend(["--episode-id", episode_id])
        if shot_id:
            command.extend(["--shot-id", shot_id])
        
        return command

    def __call__(self, payload: HandlerPayload | dict) -> dict[str, Any]:
        """Execute attach audio and return artifacts.

        Args:
            payload: HandlerPayload or dict containing action_plan.

        Returns:
            Dict with artifacts including scene_mp4_with_audio_path, audio_manifest_path, artifact_accepted.
            The result is wrapped in an "artifacts" key for compatibility with handler wrapping.
        """
        # Normalize payload to dict
        if isinstance(payload, HandlerPayload):
            action_plan = payload.action_plan or {}
            episode_id = payload.episode_id if payload.episode_id else ""
            shot_id = payload.shot_id if payload.shot_id else ""
        else:
            action_plan = payload.get("action_plan", {})
            episode_id = payload.get("episode_id", "")
            shot_id = payload.get("shot_id", "")
        
        scene_mp4_path = action_plan.get("scene_mp4_path")
        brief_path = action_plan.get("brief_path")
        output_dir = action_plan.get("output_dir", "output")

        # Resolve output_dir relative to project_root
        if not Path(output_dir).is_absolute():
            output_dir = self.project_root / output_dir

        command = self.build_command(payload)

        if not self.allow_subprocess_execution:
            return {
                "executed": False,
                "status": "dry_run",
                "command": command,
                "scene_mp4_path": str(scene_mp4_path),
                "brief_path": str(brief_path),
                "output_dir": str(output_dir),
                "scene_mp4_with_audio_path": None,
                "audio_manifest_path": None,
                "artifact_accepted": False,
                "artifact_reason": "dry run - subprocess not executed",
                "artifacts": {
                    "handler": "attach_audio_runner",
                    "status": "dry_run",
                    "executed": False,
                    "command": command,
                    "scene_mp4_path": str(scene_mp4_path),
                    "brief_path": str(brief_path),
                    "output_dir": str(output_dir),
                    "scene_mp4_with_audio_path": None,
                    "audio_manifest_path": None,
                    "artifact_accepted": False,
                    "artifact_reason": "dry run - subprocess not executed",
                }
            }

        # Check global kill switch
        global_enabled = is_real_execution_globally_enabled()
        if not global_enabled:
            return {
                "executed": False,
                "status": "blocked",
                "command": command,
                "scene_mp4_path": str(scene_mp4_path),
                "brief_path": str(brief_path),
                "output_dir": str(output_dir),
                "scene_mp4_with_audio_path": None,
                "audio_manifest_path": None,
                "artifact_accepted": False,
                "artifact_reason": "real execution blocked by global kill switch (COMFY_AGENT_REAL_EXECUTION_ENABLED)",
                "artifacts": {
                    "handler": "attach_audio_runner",
                    "status": "blocked",
                    "executed": False,
                    "command": command,
                    "scene_mp4_path": str(scene_mp4_path),
                    "brief_path": str(brief_path),
                    "output_dir": str(output_dir),
                    "scene_mp4_with_audio_path": None,
                    "audio_manifest_path": None,
                    "artifact_accepted": False,
                    "artifact_reason": "real execution blocked by global kill switch (COMFY_AGENT_REAL_EXECUTION_ENABLED)",
                    "real_execution_requested": True,
                    "subprocess_allowed": True,
                    "global_real_execution_enabled": False,
                    "subprocess_invoked": False,
                    "production_executed": False,
                }
            }

        try:
            # Direct function call instead of subprocess to avoid module path issues
            from app.cli import attach_audio as attach_audio_cli
            import argparse
            
            # Create args namespace for attach_audio function
            # MK-CTRL37R-B — Include episode_id and shot_id for deterministic naming and metadata
            class Args:
                def __init__(self):
                    self.scene = str(scene_mp4_path)
                    self.brief = str(brief_path)
                    self.output = str(output_dir)
                    self.episode_id = episode_id if episode_id else ""
                    self.shot_id = shot_id if shot_id else ""
            
            args = Args()
            
            # Capture stdout to parse audio output path and manifest
            import io
            import sys as sys_module
            old_stdout = sys_module.stdout
            old_stderr = sys_module.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                sys_module.stdout = stdout_capture
                sys_module.stderr = stderr_capture
                returncode = attach_audio_cli(args)
                stdout_str = stdout_capture.getvalue()
                stderr_str = stderr_capture.getvalue()
            finally:
                sys_module.stdout = old_stdout
                sys_module.stderr = old_stderr

            # Parse output to extract audio output path and manifest
            audio_output_path = None
            audio_manifest_path = None

            for line in stdout_str.splitlines():
                if line.startswith("Audio attached MP4 saved:"):
                    audio_output_path = line.split(":", 1)[1].strip()
                elif line.startswith("Audio manifest saved:"):
                    audio_manifest_path = line.split(":", 1)[1].strip()

            # Determine artifact acceptance
            # For attach_audio, if the output file exists and has content, accept it
            artifact_accepted = False
            artifact_reason = "audio output not generated"
            
            if audio_output_path and Path(audio_output_path).exists():
                file_size = Path(audio_output_path).stat().st_size
                if file_size > 0:
                    artifact_accepted = True
                    artifact_reason = f"audio attached successfully, output size: {file_size} bytes"
                else:
                    artifact_reason = "audio output file is empty"
            else:
                artifact_reason = "audio output file not created"

            artifacts = {
                "handler": "attach_audio_runner",
                "status": "executed",
                "executed": True,
                "command": command,
                "returncode": returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "scene_mp4_path": str(scene_mp4_path),
                "brief_path": str(brief_path),
                "output_dir": str(output_dir),
                "scene_mp4_with_audio_path": audio_output_path,
                "audio_manifest_path": audio_manifest_path,
                "artifact_status": "accepted" if artifact_accepted else "failed",
                "artifact_accepted": artifact_accepted,
                "artifact_reason": artifact_reason,
                "real_execution_requested": True,
                "subprocess_allowed": True,
                "global_real_execution_enabled": True,
                "subprocess_invoked": False,  # Direct function call, not subprocess
                "production_executed": True,
            }

            return {
                "executed": True,
                "status": "executed",
                "artifacts": artifacts,
            }
        except Exception as e:
            artifacts = {
                "handler": "attach_audio_runner",
                "status": "error",
                "executed": False,
                "command": command,
                "scene_mp4_path": str(scene_mp4_path),
                "brief_path": str(brief_path),
                "output_dir": str(output_dir),
                "scene_mp4_with_audio_path": None,
                "audio_manifest_path": None,
                "artifact_accepted": False,
                "artifact_reason": f"error: {e}",
            }
            return {
                "executed": False,
                "status": "error",
                "artifacts": artifacts,
            }
