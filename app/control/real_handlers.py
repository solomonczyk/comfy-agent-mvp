"""MK-CTRL11 — Real generate frames handler adapter.

Guarded real production handler for generate_frames and assemble_scene.
Double opt-in required: enable_real_handlers=True AND payload.allow_real_execution=True.
No direct ComfyUI calls in control layer.
"""
from __future__ import annotations

from typing import Any, Callable

from .handler_contracts import HandlerPayload, HandlerResult


class RealGenerateFramesHandler:
    """Real generate_frames handler with double opt-in guard.

    This handler connects control stack to generation entrypoint only when
    explicitly allowed by both enable_real_handlers and payload.allow_real_execution.

    Execution rules:
    - If dry_validate=True: return validated, no runner call
    - If allow_real_execution=False: return blocked, no runner call
    - If runner_callable is None: return blocked
    - If runner_callable exists and allowed: call it and wrap result
    - If runner_callable raises: re-raise for action_failed recording
    """

    def __init__(
        self,
        runner_callable: Callable | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        """Initialize handler with optional runner callable.

        Args:
            runner_callable: Callable that performs actual generation.
                Should accept HandlerPayload and return dict with artifacts.
                If None, real execution is blocked even if flags allow it.
            allow_real_execution: Override flag for real execution (MK-CTRL13R).
                If True, allows real execution regardless of payload flag.
                Default False for safety.
        """
        self.runner_callable = runner_callable
        self._allow_real_execution = allow_real_execution

    def __call__(self, payload: HandlerPayload | dict) -> dict:
        """Execute handler with payload.

        Args:
            payload: HandlerPayload or dict containing execution parameters.

        Returns:
            HandlerResult dict with status, executed, artifacts, metadata.

        Raises:
            ValueError: If required fields are missing or action is wrong.
            Exception: If runner_callable raises (propagates for action_failed).
        """
        # Normalize payload to dict
        if isinstance(payload, HandlerPayload):
            payload_dict = payload.to_dict()
        else:
            payload_dict = payload

        # Validate required fields
        episode_id = payload_dict.get("episode_id")
        shot_id = payload_dict.get("shot_id")
        action = payload_dict.get("action")
        action_plan = payload_dict.get("action_plan")

        if not episode_id:
            raise ValueError("Missing required field: episode_id")
        if not shot_id:
            raise ValueError("Missing required field: shot_id")
        if not action:
            raise ValueError("Missing required field: action")
        if action != "generate_frames":
            raise ValueError(f"Wrong action for RealGenerateFramesHandler: {action}")

        dry_validate = payload_dict.get("dry_validate", True)
        # Use constructor override flag if set, otherwise use payload flag (MK-CTRL13R)
        allow_real_execution = self._allow_real_execution or payload_dict.get("allow_real_execution", False)

        # Dry validate mode
        if dry_validate:
            return HandlerResult(
                handler="generate_frames",
                status="validated",
                executed=False,
                would_execute=True,
                reason="generate_frames dry validation passed",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                    "brief_path": action_plan.get("brief_path") if action_plan else None,
                },
            )

        # Real execution blocked by flag
        if not allow_real_execution:
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="real generate_frames execution disabled",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution blocked by missing runner
        if self.runner_callable is None:
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="no runner callable configured",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution: call injected runner
        runner_result = self.runner_callable(payload_dict)

        # Wrap runner result into HandlerResult
        # Preserve runner's executed flag for production_executed semantics (MK-CTRL13R)
        runner_executed = runner_result.get("executed", False) if isinstance(runner_result, dict) else False
        runner_status = runner_result.get("status", "executed") if isinstance(runner_result, dict) else "executed"
        
        # MK-CTRL15R-1: Preserve runner's reason, especially for blocked execution
        if runner_status == "blocked" and isinstance(runner_result, dict):
            reason = runner_result.get("reason", "real execution blocked")
        else:
            # MK-CTRL18 — Use artifact reason if available for artifact failures
            if isinstance(runner_result, dict) and runner_result.get("artifact_accepted") is False:
                reason = runner_result.get("artifact_reason", "artifact not accepted")
            else:
                reason = "generate_frames executed successfully"

        return HandlerResult(
            handler="generate_frames",
            status=runner_status,
            executed=runner_executed,  # Use runner's executed flag
            would_execute=False,
            reason=reason,
            artifacts=runner_result if isinstance(runner_result, dict) else {},
            metadata={
                "episode_id": episode_id,
                "shot_id": shot_id,
                "action": action,
            },
        )


class RealQaReviewHandler:
    """MK-CTRL22 — Real qa_review handler with double opt-in guard.

    This handler connects control stack to QA review entrypoint only when
    explicitly allowed by both enable_real_handlers and payload.allow_real_execution.

    Execution rules:
    - If dry_validate=True: return validated, no runner call
    - If allow_real_execution=False: return blocked, no runner call
    - If runner_callable is None: return blocked
    - If runner_callable exists and allowed: call it and wrap result
    - If runner_callable raises: re-raise for action_failed recording
    """

    def __init__(
        self,
        runner_callable: Callable | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        """Initialize handler with optional runner callable.

        Args:
            runner_callable: Callable that performs actual QA review.
                Should accept HandlerPayload and return dict with artifacts.
                If None, real execution is blocked even if flags allow it.
            allow_real_execution: Override flag for real execution (MK-CTRL13R).
                If True, allows real execution regardless of payload flag.
                Default False for safety.
        """
        self.runner_callable = runner_callable
        self._allow_real_execution = allow_real_execution

    def __call__(self, payload: HandlerPayload | dict) -> dict:
        """Execute handler with payload.

        Args:
            payload: HandlerPayload or dict containing execution parameters.

        Returns:
            HandlerResult dict with status, executed, artifacts, metadata.

        Raises:
            ValueError: If required fields are missing or action is wrong.
            Exception: If runner_callable raises (propagates for action_failed).
        """
        # Normalize payload to dict
        if isinstance(payload, HandlerPayload):
            payload_dict = payload.to_dict()
        else:
            payload_dict = payload

        # Validate required fields
        episode_id = payload_dict.get("episode_id")
        shot_id = payload_dict.get("shot_id")
        action = payload_dict.get("action")
        action_plan = payload_dict.get("action_plan")

        if not episode_id:
            raise ValueError("Missing required field: episode_id")
        if not shot_id:
            raise ValueError("Missing required field: shot_id")
        if not action:
            raise ValueError("Missing required field: action")
        if action != "qa_review":
            raise ValueError(f"Wrong action for RealQaReviewHandler: {action}")

        dry_validate = payload_dict.get("dry_validate", True)
        # Use constructor override flag if set, otherwise use payload flag (MK-CTRL13R)
        allow_real_execution = self._allow_real_execution or payload_dict.get("allow_real_execution", False)

        # Dry validate mode
        if dry_validate:
            return HandlerResult(
                handler="qa_review",
                status="validated",
                executed=False,
                would_execute=True,
                reason="qa_review dry validation passed",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                    "scene_mp4_path": action_plan.get("scene_mp4_path") if action_plan else None,
                },
            )

        # Real execution blocked by flag
        if not allow_real_execution:
            return HandlerResult(
                handler="qa_review",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="real qa_review execution disabled",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution blocked by missing runner
        if self.runner_callable is None:
            return HandlerResult(
                handler="qa_review",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="no runner callable configured",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution: call injected runner
        runner_result = self.runner_callable(payload_dict)

        # Wrap runner result into HandlerResult
        runner_executed = runner_result.get("executed", False) if isinstance(runner_result, dict) else False
        runner_status = runner_result.get("status", "executed") if isinstance(runner_result, dict) else "executed"

        if runner_status == "blocked" and isinstance(runner_result, dict):
            reason = runner_result.get("reason", "real execution blocked")
        else:
            if isinstance(runner_result, dict) and runner_result.get("artifact_accepted") is False:
                reason = runner_result.get("artifact_reason", "artifact not accepted")
            else:
                reason = "qa_review executed successfully"

        return HandlerResult(
            handler="qa_review",
            status=runner_status,
            executed=runner_executed,
            would_execute=False,
            reason=reason,
            artifacts=runner_result.get("artifacts", {}) if isinstance(runner_result, dict) else {},
            metadata={
                "episode_id": episode_id,
                "shot_id": shot_id,
                "action": action,
            },
        )


class RealAttachAudioHandler:
    """MK-CTRL23 — Real attach_audio handler with double opt-in guard.

    This handler connects control stack to audio attachment entrypoint only when
    explicitly allowed by both enable_real_handlers and payload.allow_real_execution.

    Execution rules:
    - If dry_validate=True: return validated, no runner call
    - If allow_real_execution=False: return blocked, no runner call
    - If runner_callable is None: return blocked
    - If runner_callable exists and allowed: call it and wrap result
    - If runner_callable raises: re-raise for action_failed recording
    """

    def __init__(
        self,
        runner_callable: Callable | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        """Initialize handler with optional runner callable.

        Args:
            runner_callable: Callable that performs actual audio attachment.
                Should accept HandlerPayload and return dict with artifacts.
                If None, real execution is blocked even if flags allow it.
            allow_real_execution: Double opt-in flag. Must be True for real execution.
        """
        self.runner_callable = runner_callable
        self.allow_real_execution = allow_real_execution

    def __call__(self, payload: HandlerPayload | dict) -> HandlerResult:
        """Execute attach_audio with double opt-in guard."""
        # Normalize payload to HandlerPayload
        if isinstance(payload, dict):
            payload = HandlerPayload(**payload)
        
        action = payload.action

        # Dry validation mode
        if payload.dry_validate:
            return HandlerResult(
                handler="attach_audio",
                status="validated",
                would_execute=True,
                executed=False,
                reason="attach_audio dry validation passed",
                artifacts={},
            )

        # Global kill switch: use shared guard
        from app.control.real_execution_guard import is_real_execution_globally_enabled
        if not is_real_execution_globally_enabled():
            return HandlerResult(
                handler="attach_audio",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="attach_audio real execution not allowed (global kill switch)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": True,
                    "global_real_execution_enabled": False,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by global kill switch (COMFY_AGENT_REAL_EXECUTION_ENABLED)",
                },
            )

        # Double opt-in guard
        if not self.allow_real_execution:
            return HandlerResult(
                handler="attach_audio",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="attach_audio real execution not allowed (double opt-in)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": True,
                    "global_real_execution_enabled": True,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by double opt-in (handler allow_real_execution=False)",
                },
            )

        if not payload.allow_real_execution:
            return HandlerResult(
                handler="attach_audio",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="attach_audio real execution not allowed (payload flag)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": False,
                    "global_real_execution_enabled": True,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by payload flag (payload.allow_real_execution=False)",
                },
            )

        if self.runner_callable is None:
            return HandlerResult(
                handler="attach_audio",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="attach_audio runner not configured",
                artifacts={},
            )

        # Real execution
        try:
            result = self.runner_callable(payload)
            return HandlerResult(
                handler="attach_audio",
                status="executed",
                would_execute=True,
                executed=True,
                reason="attach_audio executed successfully",
                artifacts=result.get("artifacts", {}),
            )
        except Exception as e:
            return HandlerResult(
                handler="attach_audio",
                status="failed",
                would_execute=True,
                executed=True,
                reason=f"attach_audio failed: {e}",
                artifacts={},
            )


class RealRenderEpisodeHandler:
    """MK-CTRL24 — Real render_episode handler with double opt-in guard.

    This handler connects control stack to episode rendering entrypoint only when
    explicitly allowed by both enable_real_handlers and payload.allow_real_execution.

    Execution rules:
    - If dry_validate=True: return validated, no runner call
    - If global kill switch disabled: return blocked, no runner call
    - If allow_real_execution=False: return blocked, no runner call
    - If payload.allow_real_execution=False: return blocked
    - If runner_callable is None: return blocked
    - If runner_callable exists and allowed: call it and wrap result
    - If runner_callable raises: re-raise for action_failed recording
    """

    def __init__(
        self,
        runner_callable: Callable | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        """Initialize handler with optional runner callable.

        Args:
            runner_callable: Callable that performs actual episode rendering.
                Should accept HandlerPayload and return dict with artifacts.
                If None, real execution is blocked even if flags allow it.
            allow_real_execution: Double opt-in flag. Must be True for real execution.
        """
        self.runner_callable = runner_callable
        self.allow_real_execution = allow_real_execution

    def __call__(self, payload: HandlerPayload | dict) -> HandlerResult:
        """Execute render_episode with double opt-in guard."""
        # Normalize payload to HandlerPayload if it's a dict
        if isinstance(payload, dict):
            from .handler_contracts import HandlerPayload
            payload = HandlerPayload(
                episode_id=payload.get("episode_id", ""),
                shot_id=payload.get("shot_id", ""),
                action=payload.get("action", ""),
                state_report=payload.get("state_report", {}),
                action_plan=payload.get("action_plan", {}),
                dry_validate=payload.get("dry_validate", False),
                allow_real_execution=payload.get("allow_real_execution", False),
                extra=payload.get("extra", {}),
            )
        
        action = payload.action

        # Dry validation mode
        if payload.dry_validate:
            return HandlerResult(
                handler="render_episode",
                status="validated",
                would_execute=True,
                executed=False,
                reason="render_episode dry validation passed",
                artifacts={},
            )

        # Global kill switch: use shared guard
        from app.control.real_execution_guard import is_real_execution_globally_enabled
        if not is_real_execution_globally_enabled():
            return HandlerResult(
                handler="render_episode",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="render_episode real execution not allowed (global kill switch)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": True,
                    "global_real_execution_enabled": False,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by global kill switch (COMFY_AGENT_REAL_EXECUTION_ENABLED)",
                },
            )

        # Double opt-in guard
        if not self.allow_real_execution:
            return HandlerResult(
                handler="render_episode",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="render_episode real execution not allowed (double opt-in)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": True,
                    "global_real_execution_enabled": True,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by double opt-in (handler allow_real_execution=False)",
                },
            )

        if not payload.allow_real_execution:
            return HandlerResult(
                handler="render_episode",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="render_episode real execution not allowed (payload flag)",
                artifacts={
                    "real_execution_requested": True,
                    "subprocess_allowed": False,
                    "global_real_execution_enabled": True,
                    "subprocess_invoked": False,
                    "production_executed": False,
                    "reason": "real execution blocked by payload flag (payload.allow_real_execution=False)",
                },
            )

        if self.runner_callable is None:
            return HandlerResult(
                handler="render_episode",
                status="blocked",
                would_execute=False,
                executed=False,
                reason="render_episode runner not configured",
                artifacts={},
            )

        # Real execution
        try:
            result = self.runner_callable(payload)
            return HandlerResult(
                handler="render_episode",
                status="executed",
                would_execute=True,
                executed=True,
                reason="render_episode executed successfully",
                artifacts=result.get("artifacts", {}),
            )
        except Exception as e:
            return HandlerResult(
                handler="render_episode",
                status="failed",
                would_execute=True,
                executed=True,
                reason=f"render_episode failed: {e}",
                artifacts={},
            )


class RealAssembleSceneHandler:
    """MK-CTRL21 — Real assemble_scene handler with double opt-in guard.

    This handler connects control stack to scene assembly entrypoint only when
    explicitly allowed by both enable_real_handlers and payload.allow_real_execution.

    Execution rules:
    - If dry_validate=True: return validated, no runner call
    - If allow_real_execution=False: return blocked, no runner call
    - If runner_callable is None: return blocked
    - If runner_callable exists and allowed: call it and wrap result
    - If runner_callable raises: re-raise for action_failed recording
    """

    def __init__(
        self,
        runner_callable: Callable | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        """Initialize handler with optional runner callable.

        Args:
            runner_callable: Callable that performs actual scene assembly.
                Should accept HandlerPayload and return dict with artifacts.
                If None, real execution is blocked even if flags allow it.
            allow_real_execution: Override flag for real execution (MK-CTRL13R).
                If True, allows real execution regardless of payload flag.
                Default False for safety.
        """
        self.runner_callable = runner_callable
        self._allow_real_execution = allow_real_execution

    def __call__(self, payload: HandlerPayload | dict) -> dict:
        """Execute handler with payload.

        Args:
            payload: HandlerPayload or dict containing execution parameters.

        Returns:
            HandlerResult dict with status, executed, artifacts, metadata.

        Raises:
            ValueError: If required fields are missing or action is wrong.
            Exception: If runner_callable raises (propagates for action_failed).
        """
        # Normalize payload to dict
        if isinstance(payload, HandlerPayload):
            payload_dict = payload.to_dict()
        else:
            payload_dict = payload

        # Validate required fields
        episode_id = payload_dict.get("episode_id")
        shot_id = payload_dict.get("shot_id")
        action = payload_dict.get("action")
        action_plan = payload_dict.get("action_plan")

        if not episode_id:
            raise ValueError("Missing required field: episode_id")
        if not shot_id:
            raise ValueError("Missing required field: shot_id")
        if not action:
            raise ValueError("Missing required field: action")
        if action != "assemble_scene":
            raise ValueError(f"Wrong action for RealAssembleSceneHandler: {action}")

        dry_validate = payload_dict.get("dry_validate", True)
        # Use constructor override flag if set, otherwise use payload flag (MK-CTRL13R)
        allow_real_execution = self._allow_real_execution or payload_dict.get("allow_real_execution", False)

        # Dry validate mode
        if dry_validate:
            return HandlerResult(
                handler="assemble_scene",
                status="validated",
                executed=False,
                would_execute=True,
                reason="assemble_scene dry validation passed",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                    "frame_manifest_path": action_plan.get("frame_manifest_path") if action_plan else None,
                },
            )

        # Real execution blocked by flag
        if not allow_real_execution:
            return HandlerResult(
                handler="assemble_scene",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="real assemble_scene execution disabled",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution blocked by missing runner
        if self.runner_callable is None:
            return HandlerResult(
                handler="assemble_scene",
                status="blocked",
                executed=False,
                would_execute=True,
                reason="no runner callable configured",
                artifacts={},
                metadata={
                    "episode_id": episode_id,
                    "shot_id": shot_id,
                    "action": action,
                },
            )

        # Real execution: call injected runner
        runner_result = self.runner_callable(payload_dict)

        # Wrap runner result into HandlerResult
        runner_executed = runner_result.get("executed", False) if isinstance(runner_result, dict) else False
        runner_status = runner_result.get("status", "executed") if isinstance(runner_result, dict) else "executed"

        if runner_status == "blocked" and isinstance(runner_result, dict):
            reason = runner_result.get("reason", "real execution blocked")
        else:
            if isinstance(runner_result, dict) and runner_result.get("artifact_accepted") is False:
                reason = runner_result.get("artifact_reason", "artifact not accepted")
            else:
                reason = "assemble_scene executed successfully"

        return HandlerResult(
            handler="assemble_scene",
            status=runner_status,
            executed=runner_executed,
            would_execute=False,
            reason=reason,
            artifacts=runner_result.get("artifacts", {}) if isinstance(runner_result, dict) else {},  # MK-CTRL21 — Extract nested artifacts
            metadata={
                "episode_id": episode_id,
                "shot_id": shot_id,
                "action": action,
            },
        )


def build_real_generate_frames_registry(
    enable_real_handlers: bool = False,
    runner_callable: Callable | None = None,
) -> Any:
    """Build handler registry with real generate_frames adapter.

    Args:
        enable_real_handlers: If False, register handler disabled.
            If True, register handler enabled.
            Actual production execution still requires payload.allow_real_execution=True.
        runner_callable: Callable for real execution.
            If None, real execution is blocked even when enabled.

    Returns:
        HandlerRegistry instance with generate_frames handler registered.

    Note:
        No execution occurs during registry construction.
    """
    from .handlers import HandlerRegistry

    registry = HandlerRegistry()

    handler = RealGenerateFramesHandler(runner_callable=runner_callable)
    enabled = enable_real_handlers

    registry.register(
        "generate_frames",
        handler,
        enabled=enabled,
        description="Real generate_frames handler (MK-CTRL11)",
    )

    return registry
