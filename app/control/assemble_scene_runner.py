"""MK-CTRL21 — Assemble Scene Runner.

Builds and executes the assemble-scene command.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .artifact_parser import parse_generation_artifacts, evaluate_artifact_acceptance
from .real_execution_guard import is_real_execution_globally_enabled


class AssembleSceneRunner:
    """Runner for assemble_scene action.

    Builds and executes:
    python -m app assemble-scene --frame-manifest <path> --output <dir>
    """

    def __init__(
        self,
        project_root: Path | str,
        allow_subprocess_execution: bool = False,
        timeout_sec: int = 3600,
    ) -> None:
        """Initialize runner.

        Args:
            project_root: Project root directory for resolving paths.
            allow_subprocess_execution: Whether to allow subprocess execution.
                Default False for dry mode.
            timeout_sec: Subprocess timeout in seconds.
        """
        self.project_root = Path(project_root)
        self.allow_subprocess_execution = allow_subprocess_execution
        self.timeout_sec = timeout_sec

    def build_command(self, payload: dict[str, Any]) -> list[str]:
        """Build assemble-scene command from payload.

        Args:
            payload: Dict with action_plan containing frame_manifest_path and output_dir.

        Returns:
            Command list for subprocess execution.
        """
        action_plan = payload.get("action_plan", {})
        frame_manifest_path = action_plan.get("frame_manifest_path")
        output_dir_raw = action_plan.get("output_dir", "output")
        episode_id = payload.get("episode_id", "")
        shot_id = payload.get("shot_id", "")
        
        # Resolve output_dir relative to project_root
        output_dir_obj = Path(output_dir_raw)
        if not output_dir_obj.is_absolute():
            output_dir_obj = self.project_root / output_dir_obj
        output_dir = str(output_dir_obj)

        if not frame_manifest_path:
            raise ValueError("frame_manifest_path is required for assemble_scene")

        command = [
            sys.executable,
            "-m",
            "app",
            "assemble-scene",
            "--frame-manifest",
            str(frame_manifest_path),
            "--output",
            output_dir,
        ]
        
        # MK-CTRL34 — Add episode_id and shot_id if available
        if episode_id:
            command.extend(["--episode-id", episode_id])
        if shot_id:
            command.extend(["--shot-id", shot_id])
        
        return command

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute assemble_scene action.

        Args:
            payload: HandlerPayload dict with action_plan and metadata.

        Returns:
            Dict with execution result, artifacts, and audit fields.
        """
        # Validate payload
        episode_id = payload.get("episode_id")
        shot_id = payload.get("shot_id")
        action = payload.get("action")

        if not episode_id:
            raise ValueError("Missing required field: episode_id")
        if not shot_id:
            raise ValueError("Missing required field: shot_id")
        if action != "assemble_scene":
            raise ValueError(f"Wrong action for AssembleSceneRunner: {action}")

        # Validate action_plan
        action_plan = payload.get("action_plan", {})
        frame_manifest_path = action_plan.get("frame_manifest_path")
        output_dir = action_plan.get("output_dir", "output")

        if not frame_manifest_path:
            return {
                "handler": "assemble_scene_runner",
                "status": "validation_failed",
                "executed": False,
                "reason": "frame_manifest_path is required for assemble_scene",
                "frame_manifest_path": None,
                "output_dir": output_dir,
                "stdout": "",
                "stderr": "",
                "returncode": None,
                "artifact_status": "not_applicable",
                "artifact_accepted": False,
                "artifact_reason": "validation failed: missing frame_manifest_path",
                "real_execution_requested": False,
                "subprocess_allowed": False,
                "global_real_execution_enabled": is_real_execution_globally_enabled(),
                "subprocess_invoked": False,
                "production_executed": False,
            }

        # Verify frame manifest exists
        frame_manifest_file = Path(frame_manifest_path)
        if not frame_manifest_file.exists():
            return {
                "handler": "assemble_scene_runner",
                "status": "validation_failed",
                "executed": False,
                "reason": f"frame manifest not found: {frame_manifest_path}",
                "frame_manifest_path": frame_manifest_path,
                "output_dir": output_dir,
                "stdout": "",
                "stderr": "",
                "returncode": None,
                "artifact_status": "not_applicable",
                "artifact_accepted": False,
                "artifact_reason": "validation failed: frame manifest not found",
                "real_execution_requested": False,
                "subprocess_allowed": False,
                "global_real_execution_enabled": is_real_execution_globally_enabled(),
                "subprocess_invoked": False,
                "production_executed": False,
            }

        command = self.build_command(payload)

        # Default mode: command ready but not executed
        if not self.allow_subprocess_execution:
            verdict = evaluate_artifact_acceptance(
                returncode=0,
                subprocess_invoked=False,
                scene_output_path=None,
                output_exists=False,
                output_size_bytes=None,
            )
            return {
                "handler": "assemble_scene_runner",
                "status": "command_ready",
                "executed": False,
                "command": command,
                "frame_manifest_path": frame_manifest_path,
                "output_dir": output_dir,
                "reason": "command built but not executed",
                "scene_output_path": None,
                "scene_manifest_path": None,
                "scene_duration_sec": None,
                "scene_frame_count": None,
                "stdout": "",
                "stderr": "",
                "returncode": None,
                "artifact_status": verdict["artifact_status"],
                "artifact_accepted": verdict["artifact_accepted"],
                "artifact_reason": verdict["artifact_reason"],
                "real_execution_requested": False,
                "subprocess_allowed": False,
                "global_real_execution_enabled": is_real_execution_globally_enabled(),
                "subprocess_invoked": False,
                "production_executed": False,
            }

        # Check global kill switch
        global_enabled = is_real_execution_globally_enabled()
        if not global_enabled:
            verdict = evaluate_artifact_acceptance(
                returncode=0,
                subprocess_invoked=False,
                scene_output_path=None,
                output_exists=False,
                output_size_bytes=None,
            )
            return {
                "handler": "assemble_scene_runner",
                "status": "blocked",
                "executed": False,
                "command": command,
                "frame_manifest_path": frame_manifest_path,
                "output_dir": output_dir,
                "reason": "real execution blocked by global kill switch (COMFY_AGENT_REAL_EXECUTION_ENABLED)",
                "scene_output_path": None,
                "scene_manifest_path": None,
                "scene_duration_sec": None,
                "scene_frame_count": None,
                "stdout": "",
                "stderr": "",
                "returncode": None,
                "artifact_status": verdict["artifact_status"],
                "artifact_accepted": verdict["artifact_accepted"],
                "artifact_reason": verdict["artifact_reason"],
                "real_execution_requested": True,
                "subprocess_allowed": True,
                "global_real_execution_enabled": False,
                "subprocess_invoked": False,
                "production_executed": False,
            }

        # Subprocess execution mode
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_sec,
        )

        # Parse artifacts from stdout
        artifacts = parse_generation_artifacts(result.stdout, cwd=self.project_root)

        # Evaluate artifact acceptance (MK-CTRL21: use scene artifacts)
        verdict = evaluate_artifact_acceptance(
            returncode=result.returncode,
            subprocess_invoked=True,
            scene_output_path=artifacts.get("scene_output_path"),
            output_exists=artifacts.get("output_exists", False),
            output_size_bytes=artifacts.get("output_size_bytes"),
            scene_frame_count=artifacts.get("scene_frame_count"),  # MK-CTRL21R — Pass scene_frame_count
        )

        # Adjust status based on artifact acceptance
        if verdict["artifact_accepted"]:
            status = "executed" if result.returncode == 0 else "failed"
        else:
            status = verdict["artifact_status"]

        # MK-CTRL21 — Wrap artifact fields in "artifacts" key for action_runner compatibility
        artifact_fields = {
            "scene_output_path": artifacts.get("scene_output_path"),
            "scene_manifest_path": artifacts.get("scene_manifest_path"),
            "scene_duration_sec": artifacts.get("scene_duration_sec"),
            "scene_frame_count": artifacts.get("scene_frame_count"),
            "artifact_status": verdict["artifact_status"],
            "artifact_accepted": verdict["artifact_accepted"],
            "artifact_reason": verdict["artifact_reason"],
        }

        return {
            "handler": "assemble_scene_runner",
            "status": status,
            "executed": True,
            "command": command,
            "frame_manifest_path": frame_manifest_path,
            "output_dir": output_dir,
            "reason": f"subprocess completed with returncode {result.returncode}, artifact_status={verdict['artifact_status']}",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "artifacts": artifact_fields,  # MK-CTRL21 — Nested for action_runner compatibility
            "real_execution_requested": True,
            "subprocess_allowed": True,
            "global_real_execution_enabled": True,
            "subprocess_invoked": True,
            "production_executed": True,
        }
