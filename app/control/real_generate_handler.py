"""MK-CTRL11 — Real generate_frames handler adapter.

Fail-safe by default. Real execution requires double opt-in:
  1. handler constructed with enable_real_execution=True
  2. incoming HandlerPayload.allow_real_execution=True
  3. incoming HandlerPayload.dry_validate=False

No top-level imports from production systems (app.comfy, app.render,
app.voice, requests, ffmpeg runners).  Any real import must happen lazily
inside the double-opt-in execution branch only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .handler_contracts import HandlerPayload, HandlerResult
from .handlers import HandlerRegistry


class RealGenerateFramesHandler:
    """Real-ready handler for ``generate_frames``.

    Accepts an optional *runner_factory* that will only be invoked when:
      1. ``payload.dry_validate`` is ``False``
      2. ``payload.allow_real_execution`` is ``True``
      3. ``self.enable_real_execution`` is ``True``
      4. ``runner_factory`` is not ``None``

    The handler can be called either with a :class:`HandlerPayload` (or plain
    ``dict``).
    """

    def __init__(
        self,
        runner_factory: Callable[[], Any] | None = None,
        enable_real_execution: bool = False,
        output_root: Path | str = "output",
    ) -> None:
        self.runner_factory = runner_factory
        self.enable_real_execution = enable_real_execution
        self.output_root = Path(output_root)

    def __call__(
        self,
        payload: dict | HandlerPayload | None = None,
        /,
        **kwargs: Any,
    ) -> dict:
        """Run the handler and return a JSON-serialisable dict."""
        # Normalise input to a HandlerPayload
        if payload is None:
            payload = HandlerPayload(
                episode_id=kwargs.get("episode_id", ""),
                shot_id=kwargs.get("shot_id", ""),
                action="generate_frames",
                state_report=kwargs.get("state_report", {}),
                action_plan=kwargs.get("action_plan", {}),
            )
        elif isinstance(payload, dict):
            payload = HandlerPayload(**payload)

        assert isinstance(payload, HandlerPayload)

        # Guard: wrong action
        if payload.action != "generate_frames":
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                would_execute=False,
                executed=False,
                reason=(
                    f"Unsupported action '{payload.action}'; "
                    "expected 'generate_frames'"
                ),
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Extract action-plan fields
        action_plan = (
            payload.action_plan if isinstance(payload.action_plan, dict) else {}
        )
        brief_path = action_plan.get("brief_path")
        command_preview = action_plan.get("command_preview")
        expected_outputs = action_plan.get("expected_outputs")

        output_dir = str(
            self.output_root / payload.episode_id / payload.shot_id
        )

        # Guard: dry validation
        if payload.dry_validate:
            artifacts: dict[str, Any] = {
                "brief_path": brief_path,
                "output_dir": output_dir,
            }
            if command_preview is not None:
                artifacts["command_preview"] = command_preview
            if expected_outputs is not None:
                artifacts["expected_outputs"] = expected_outputs

            return HandlerResult(
                handler="generate_frames",
                status="validated",
                would_execute=True,
                executed=False,
                reason="dry_validate=True — real runner was not invoked",
                artifacts=artifacts,
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Guard: enable_real_execution flag on handler
        if not self.enable_real_execution:
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                would_execute=True,
                executed=False,
                reason=(
                    "enable_real_execution=False — "
                    "handler real execution is disabled"
                ),
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Guard: explicit real-execution flag on payload
        if not payload.allow_real_execution:
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                would_execute=True,
                executed=False,
                reason=(
                    "allow_real_execution=False — "
                    "payload real execution is disabled"
                ),
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Guard: runner factory configured
        if self.runner_factory is None:
            return HandlerResult(
                handler="generate_frames",
                status="blocked",
                would_execute=True,
                executed=False,
                reason="No runner factory is configured for this handler",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # All guards passed — attempt real execution
        try:
            runner = self.runner_factory()
            # Pass the full payload to the runner (GenerateFramesRunner expects payload dict)
            result = runner(payload.to_dict())
        except Exception as exc:
            return HandlerResult(
                handler="generate_frames",
                status="failed",
                would_execute=True,
                executed=False,
                reason=f"Runner raised {type(exc).__name__}: {exc}",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                    "exception_type": type(exc).__name__,
                },
            ).to_dict()

        # Normalise result
        if isinstance(result, dict):
            artifacts = result
        else:
            artifacts = {"output": result}

        return HandlerResult(
            handler="generate_frames",
            status="executed",
            would_execute=True,
            executed=True,
            reason="Runner executed successfully",
            artifacts=artifacts,
            metadata={
                "episode_id": payload.episode_id,
                "shot_id": payload.shot_id,
                "action": payload.action,
            },
        ).to_dict()


def build_real_generate_frames_handler_registry(
    enable_real_handlers: bool = False,
    runner_factory: Callable[[], Any] | None = None,
    output_root: Path | str = "output",
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` with ``generate_frames`` using the
    real handler adapter.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        The handler is registered **enabled** but with
        ``enable_real_execution=False`` and ``runner_factory=None``.
        Dry validation works; real execution is blocked internally.
      * ``enable_real_handlers=True``:
        The handler receives *runner_factory* if provided.
        Even with a real runner wired, the handler still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    handler = RealGenerateFramesHandler(
        runner_factory=runner_factory if enable_real_handlers else None,
        enable_real_execution=enable_real_handlers,
        output_root=output_root,
    )
    registry = HandlerRegistry()
    registry.register(
        "generate_frames",
        handler,
        enabled=True,
        description="Real generate_frames handler (MK-CTRL11)",
    )
    return registry


def build_real_assemble_scene_handler_registry(
    enable_real_handlers: bool = False,
    runner_factory: Callable[[], Any] | None = None,
    output_root: Path | str = "output",
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` with ``assemble_scene`` using the
    real handler adapter.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        The handler is registered **enabled** but with
        ``enable_real_execution=False`` and ``runner_factory=None``.
        Dry validation works; real execution is blocked internally.
      * ``enable_real_handlers=True``:
        The handler receives *runner_factory* if provided.
        Even with a real runner wired, the handler still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    from .real_handlers import RealAssembleSceneHandler
    from .assemble_scene_runner import AssembleSceneRunner

    handler = RealAssembleSceneHandler(
        runner_callable=runner_factory() if runner_factory and enable_real_handlers else None,
        allow_real_execution=enable_real_handlers,
    )
    registry = HandlerRegistry()
    registry.register(
        "assemble_scene",
        handler,
        enabled=True,
        description="Real assemble_scene handler (MK-CTRL21)",
    )
    return registry


def build_real_qa_review_handler_registry(
    enable_real_handlers: bool = False,
    runner_factory: Callable[[], Any] | None = None,
    output_root: Path | str = "output",
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` with ``qa_review`` using the
    real handler adapter.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        The handler is registered **enabled** but with
        ``enable_real_execution=False`` and ``runner_factory=None``.
        Dry validation works; real execution is blocked internally.
      * ``enable_real_handlers=True``:
        The handler receives *runner_factory* if provided.
        Even with a real runner wired, the handler still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    from .real_handlers import RealQaReviewHandler

    handler = RealQaReviewHandler(
        runner_callable=runner_factory() if runner_factory and enable_real_handlers else None,
        allow_real_execution=enable_real_handlers,
    )
    registry = HandlerRegistry()
    registry.register(
        "qa_review",
        handler,
        enabled=True,
        description="Real qa_review handler (MK-CTRL22)",
    )
    return registry


def build_real_attach_audio_handler_registry(
    enable_real_handlers: bool = False,
    runner_factory: Callable[[], Any] | None = None,
    output_root: Path | str = "output",
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` with ``attach_audio`` using the
    real handler adapter.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        The handler is registered **enabled** but with
        ``enable_real_execution=False`` and ``runner_factory=None``.
        Dry validation works; real execution is blocked internally.
      * ``enable_real_handlers=True``:
        The handler receives *runner_factory* if provided.
        Even with a real runner wired, the handler still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    from .real_handlers import RealAttachAudioHandler

    handler = RealAttachAudioHandler(
        runner_callable=runner_factory() if runner_factory and enable_real_handlers else None,
        allow_real_execution=enable_real_handlers,
    )
    registry = HandlerRegistry()
    registry.register(
        "attach_audio",
        handler,
        enabled=True,
        description="Real attach_audio handler (MK-CTRL23)",
    )
    return registry


def build_real_render_episode_handler_registry(
    enable_real_handlers: bool = False,
    runner_factory: Callable[[], Any] | None = None,
    output_root: Path | str = "output",
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` with ``render_episode`` using the
    real handler adapter.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        The handler is registered **enabled** but with
        ``enable_real_execution=False`` and ``runner_factory=None``.
        Dry validation works; real execution is blocked internally.
      * ``enable_real_handlers=True``:
        The handler receives *runner_factory* if provided.
        Even with a real runner wired, the handler still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    from .real_handlers import RealRenderEpisodeHandler

    handler = RealRenderEpisodeHandler(
        runner_callable=runner_factory() if runner_factory and enable_real_handlers else None,
        allow_real_execution=enable_real_handlers,
    )
    registry = HandlerRegistry()
    registry.register(
        "render_episode",
        handler,
        enabled=True,
        description="Real render_episode handler (MK-CTRL24)",
    )
    return registry
