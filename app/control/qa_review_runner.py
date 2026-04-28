"""QA review runner for executing qa-review as a subprocess.

MK-CTRL31 — Runner for qa_review action that calls the qa-review CLI command.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .handler_contracts import HandlerPayload


class QaReviewRunner:
    """Runner for qa_review action that calls the qa-review CLI command.

    This runner:
    - Calls `python -m app qa-review --scene <scene_mp4_path> --output <output_dir>`
    - Parses the output to extract QA report path, verdict, and score
    - Returns artifacts dict with qa_report_path, qa_verdict, qa_score, artifact_accepted

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
        """Initialize QA review runner.

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
        """Build the qa-review command from payload.

        Args:
            payload: HandlerPayload or dict containing action_plan with scene_mp4_path.

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
        output_dir = action_plan.get("output_dir", "output")

        # Resolve output_dir relative to project_root
        if not Path(output_dir).is_absolute():
            output_dir = self.project_root / output_dir

        command = [
            sys.executable,
            "-m",
            "app",
            "qa-review",
            "--scene",
            str(scene_mp4_path),
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
        """Execute QA review and return artifacts.

        Args:
            payload: HandlerPayload or dict containing action_plan.

        Returns:
            Dict with artifacts including qa_report_path, qa_verdict, qa_score, artifact_accepted.
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
                "output_dir": str(output_dir),
                "qa_report_path": None,
                "qa_verdict": None,
                "qa_score": None,
                "artifact_accepted": False,
                "artifact_reason": "dry run - subprocess not executed",
                "artifacts": {
                    "handler": "qa_review_runner",
                    "status": "dry_run",
                    "executed": False,
                    "command": command,
                    "scene_mp4_path": str(scene_mp4_path),
                    "output_dir": str(output_dir),
                    "qa_report_path": None,
                    "qa_verdict": None,
                    "qa_score": None,
                    "artifact_accepted": False,
                    "artifact_reason": "dry run - subprocess not executed",
                }
            }

        try:
            # Direct function call instead of subprocess to avoid module path issues
            from app.cli import qa_review as qa_review_cli
            import argparse
            
            # Create args namespace for qa_review function
            # MK-CTRL37R-B — Include episode_id and shot_id for deterministic naming and metadata
            class Args:
                def __init__(self):
                    self.scene = str(scene_mp4_path)
                    self.output = str(output_dir)
                    self.episode_id = episode_id if episode_id else ""
                    self.shot_id = shot_id if shot_id else ""
            
            args = Args()
            
            # Capture stdout to parse QA report path, verdict, and score
            import io
            import sys as sys_module
            old_stdout = sys_module.stdout
            old_stderr = sys_module.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                sys_module.stdout = stdout_capture
                sys_module.stderr = stderr_capture
                returncode = qa_review_cli(args)
                stdout_str = stdout_capture.getvalue()
                stderr_str = stderr_capture.getvalue()
            finally:
                sys_module.stdout = old_stdout
                sys_module.stderr = old_stderr

            # Parse output to extract QA report path, verdict, and score
            qa_report_path = None
            qa_verdict = None
            qa_score = None

            for line in stdout_str.splitlines():
                if line.startswith("QA report saved:"):
                    qa_report_path = line.split(":", 1)[1].strip()
                elif line.startswith("QA verdict:"):
                    qa_verdict = line.split(":", 1)[1].strip()
                elif line.startswith("QA score:"):
                    qa_score = float(line.split(":", 1)[1].strip())

            # Determine artifact acceptance
            artifact_accepted = qa_verdict == "pass" and qa_score is not None and qa_score >= 0.70
            artifact_status = "accepted" if artifact_accepted else "qa_failed"
            artifact_reason = f"qa_review verdict={qa_verdict}, score={qa_score}"

            artifacts = {
                "handler": "qa_review_runner",
                "status": "executed",
                "executed": True,
                "command": command,
                "returncode": returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "scene_mp4_path": str(scene_mp4_path),
                "output_dir": str(output_dir),
                "qa_report_path": qa_report_path,
                "qa_verdict": qa_verdict,
                "qa_score": qa_score,
                "artifact_status": artifact_status,
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
                "handler": "qa_review_runner",
                "status": "error",
                "executed": False,
                "command": command,
                "scene_mp4_path": str(scene_mp4_path),
                "output_dir": str(output_dir),
                "qa_report_path": None,
                "qa_verdict": None,
                "qa_score": None,
                "artifact_accepted": False,
                "artifact_reason": f"error: {e}",
            }
            return {
                "executed": False,
                "status": "error",
                "artifacts": artifacts,
            }
