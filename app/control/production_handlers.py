"""MK-CTRL10 — Production handler adapters and registry factory.

ProductionHandlerAdapter wraps a real callable with fail-safe guards:
  - dry_validate=True  -> returns validated, never calls real callable
  - allow_real_execution=False -> returns blocked, never calls real callable
  - real_callable is None -> returns blocked, never calls real callable

Real execution requires BOTH:
  1. Registry built with enable_real_handlers=True
  2. Payload passed with allow_real_execution=True

No ComfyUI, ffmpeg, or TTS is invoked by this module itself.
"""
from __future__ import annotations

from typing import Any, Callable

from .handler_contracts import HandlerPayload, HandlerResult
from .handlers import HandlerRegistry


class ProductionHandlerAdapter:
    """Guarded adapter that wraps a real handler callable.

    Accepts either a :class:`HandlerPayload` (or plain dict) or legacy kwargs
    ``(episode_id, shot_id, report)`` so it can be registered directly in a
    :class:`HandlerRegistry` and consumed by :class:`ControlledActionRunner`.
    """

    def __init__(
        self,
        action: str,
        real_callable: Callable | None = None,
        description: str = "",
    ) -> None:
        self.action = action
        self.real_callable = real_callable
        self.description = description

    def __call__(self, payload: dict | HandlerPayload | None = None, /, **kwargs: Any) -> dict:
        """Run the adapter and return a JSON-serialisable dict."""
        # Normalise input to a HandlerPayload
        if payload is None:
            report = kwargs.get("report", {})
            state_report = report.to_dict() if hasattr(report, "to_dict") else (report if isinstance(report, dict) else {})
            payload = HandlerPayload(
                episode_id=kwargs.get("episode_id", ""),
                shot_id=kwargs.get("shot_id", ""),
                action=self.action,
                state_report=state_report,
                action_plan={},
            )
        elif isinstance(payload, dict):
            payload = HandlerPayload(**payload)

        assert isinstance(payload, HandlerPayload)

        # Guard 1: dry validation
        if payload.dry_validate:
            return HandlerResult(
                handler=self.action,
                status="validated",
                would_execute=True,
                executed=False,
                reason="dry_validate=True — real callable was not invoked",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Guard 2: explicit real-execution flag on payload
        if not payload.allow_real_execution:
            return HandlerResult(
                handler=self.action,
                status="blocked",
                would_execute=True,
                executed=False,
                reason="allow_real_execution=False — real execution is disabled on this payload",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # Guard 3: real callable actually configured
        if self.real_callable is None:
            return HandlerResult(
                handler=self.action,
                status="blocked",
                would_execute=True,
                executed=False,
                reason="No real callable is configured for this adapter",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                },
            ).to_dict()

        # All guards passed — attempt real execution
        try:
            raw = self.real_callable(payload)
        except Exception as exc:
            return HandlerResult(
                handler=self.action,
                status="failed",
                would_execute=True,
                executed=False,
                reason=f"Real callable raised {type(exc).__name__}: {exc}",
                metadata={
                    "episode_id": payload.episode_id,
                    "shot_id": payload.shot_id,
                    "action": payload.action,
                    "exception_type": type(exc).__name__,
                },
            ).to_dict()

        artifacts = raw if isinstance(raw, dict) else {"output": raw}
        return HandlerResult(
            handler=self.action,
            status="executed",
            would_execute=True,
            executed=True,
            reason="Real callable executed successfully",
            artifacts=artifacts,
            metadata={
                "episode_id": payload.episode_id,
                "shot_id": payload.shot_id,
                "action": payload.action,
            },
        ).to_dict()


# Canonical action keys used across the control layer.
CANONICAL_ACTION_KEYS: list[str] = [
    "generate_frames",
    "continue_generation",
    "assemble_scene_video",
    "synthesize_and_mux_audio",
    "assemble_episode",
    "run_qa",
]


def build_production_handler_registry(
    enable_real_handlers: bool = False,
    real_callables: dict[str, Callable] | None = None,
) -> HandlerRegistry:
    """Return a :class:`HandlerRegistry` pre-loaded with production adapters.

    Safety design:
      * ``enable_real_handlers=False`` (default):
        All adapters are registered **enabled** but with ``real_callable=None``.
        This makes them callable for dry validation while internally blocking
        any real execution.
      * ``enable_real_handlers=True``:
        Adapters receive their real callables from *real_callables* where
        available.  Missing callables become ``None`` and block safely.
        Even with real callables wired, the adapter still requires
        ``payload.allow_real_execution=True`` before it actually runs.

    No production systems are started during construction.
    """
    real_callables = real_callables or {}
    registry = HandlerRegistry()

    for action in CANONICAL_ACTION_KEYS:
        real = real_callables.get(action) if enable_real_handlers else None
        adapter = ProductionHandlerAdapter(
            action=action,
            real_callable=real,
            description=f"Production adapter for '{action}'",
        )
        # Always register enabled so the adapter is reachable by the runner.
        # Internal guards (real_callable, payload flags) provide the safety.
        registry.register(
            action,
            adapter,
            enabled=True,
            description=adapter.description,
        )

    return registry
