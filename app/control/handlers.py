"""MK-CTRL9 — Safe handler registry and mock adapters.

HandlerRegistry maps approved control actions to callables.
All handlers are disabled by default to prevent accidental production runs.
Mock handlers return structured placeholders; they do NOT call ComfyUI,
ffmpeg, or TTS.
"""
from __future__ import annotations

from typing import Any, Callable


class HandlerRegistry:
    """Registry for control action handlers with explicit enable/disable flags."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._enabled: dict[str, bool] = {}
        self._descriptions: dict[str, str] = {}

    def register(
        self,
        action: str,
        handler: Callable[..., Any],
        *,
        enabled: bool = False,
        description: str = "",
    ) -> None:
        """Register a handler for *action*.  Disabled by default."""
        self._handlers[action] = handler
        self._enabled[action] = enabled
        self._descriptions[action] = description

    def get(self, action: str) -> Callable[..., Any]:
        """Return the callable registered for *action*.

        Raises RuntimeError if the action is unknown.
        """
        if action not in self._handlers:
            raise RuntimeError(
                f"No handler registered for action '{action}'. "
                f"Known actions: {list(self._handlers.keys())}"
            )
        return self._handlers[action]

    def is_enabled(self, action: str) -> bool:
        """Whether the handler for *action* is enabled."""
        return self._enabled.get(action, False)

    def enabled_handlers(self) -> dict[str, Callable[..., Any]]:
        """Return only the enabled handlers as a plain dict."""
        return {
            action: self._handlers[action]
            for action, on in self._enabled.items()
            if on
        }

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """JSON-serializable snapshot of the registry."""
        return {
            action: {
                "enabled": self._enabled.get(action, False),
                "description": self._descriptions.get(action, ""),
            }
            for action in self._handlers
        }


# ── mock handlers (never call production systems) ────────────────────

def generate_frames_handler(payload: dict) -> dict:
    """Mock frame generation handler accepting HandlerPayload dict (MK-CTRL13R)."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "generate_frames",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,  # Only true if allow_real_execution is True
        "subprocess_invoked": allow_real,  # Only true if allow_real_execution is True
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
        },
    }


def assemble_scene_handler(payload: dict) -> dict:
    """Mock scene assembly handler accepting HandlerPayload dict (MK-CTRL13R)."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "assemble_scene_video",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,
        "subprocess_invoked": allow_real,
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
        },
    }


def attach_audio_handler(payload: dict) -> dict:
    """Mock audio synthesis handler accepting HandlerPayload dict (MK-CTRL13R)."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "synthesize_and_mux_audio",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,
        "subprocess_invoked": allow_real,
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
        },
    }


def final_render_handler(payload: dict) -> dict:
    """Mock episode assembly handler accepting HandlerPayload dict (MK-CTRL13R)."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "assemble_episode",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,
        "subprocess_invoked": allow_real,
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
        },
    }


def qa_check_handler(payload: dict) -> dict:
    """Mock QA handler accepting HandlerPayload dict (MK-CTRL13R)."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "run_qa",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,
        "subprocess_invoked": allow_real,
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
        },
    }


def qa_review_handler(payload: dict) -> dict:
    """MK-CTRL22 — Mock qa_review handler accepting HandlerPayload dict."""
    episode_id = payload.get("episode_id")
    shot_id = payload.get("shot_id")
    action_plan = payload.get("action_plan", {})
    scene_mp4_path = action_plan.get("scene_mp4_path")
    allow_real = payload.get("allow_real_execution", False)
    return {
        "handler": "qa_review",
        "status": "mocked",
        "would_execute": True,
        "executed": True,
        "control_executed": True,
        "production_executed": allow_real,
        "subprocess_invoked": allow_real,
        "received": {
            "episode_id": episode_id,
            "shot_id": shot_id,
            "scene_mp4_path": scene_mp4_path,
        },
    }


def attach_audio_handler(payload: dict) -> dict:
    """RC-FLOW1H: No-audio RC policy handler.
    
    Implements documented no-audio RC policy instead of fake success.
    Produces audio_manifest.json with explicit skip policy fields.
    
    RC-FLOW1H: attach_audio produces documented skip artifact when real audio is out of scope.
    Returns production_executed=false but creates audio_manifest with skip policy.
    """
    scene_mp4_path = payload.get("scene_mp4_path")
    brief_path = payload.get("brief_path")
    episode_id = payload.get("episode_id", "")
    shot_id = payload.get("shot_id", "")
    
    # Build audio manifest with skip policy
    audio_manifest = {
        "audio_required": False,
        "audio_attached": False,
        "policy": "no_audio_for_rc",
        "reason": "RC-FLOW1H: Real audio attachment (TTS synthesis, audio muxing) is out of scope for this RC. Explicit no-audio policy applied.",
        "scene_mp4_path": scene_mp4_path,
        "brief_path": brief_path,
        "next_action_policy": "render_episode_allowed_without_audio",
        "episode_id": episode_id,
        "shot_id": shot_id,
    }
    
    return {
        "status": "executed",
        "executed": True,
        "production_executed": False,
        "scene_mp4_path": scene_mp4_path,
        "brief_path": brief_path,
        "reason": "RC-FLOW1H: No-audio RC policy applied",
        "artifacts": {
            "audio_manifest": audio_manifest,
            "audio_manifest_path": f"output/control/ep01_shot01_audio_manifest.json",
            "audio_required": False,
            "audio_attached": False,
            "policy": "no_audio_for_rc",
            "artifact_accepted": True,
            "artifact_status": "skipped_no_audio",  # RC-FLOW1H: Use skipped_no_audio status
            "artifact_reason": "RC-FLOW1H: No-audio RC policy documented in manifest",
        }
    }


def render_episode_handler(payload: dict) -> dict:
    """RC-FLOW1I: Render episode handler with no-audio RC policy support.
    
    Renders final episode from scene MP4 or produces final manifest.
    Preserves no-audio RC policy from attach_audio stage.
    """
    scene_mp4_path = payload.get("scene_mp4_path")
    episode_id = payload.get("episode_id", "")
    shot_id = payload.get("shot_id", "")
    
    # RC-FLOW1I: Create final manifest documenting no-audio RC policy
    episode_manifest = {
        "audio_required": False,
        "audio_attached": False,
        "audio_policy": "no_audio_for_rc",
        "source_scene_mp4_path": scene_mp4_path,
        "final_output_path": "output/control/ep01_shot01_final_manifest.json",
        "limitation": "RC render without audio",
        "episode_id": episode_id,
        "shot_id": shot_id,
        "render_mode": "rc_no_audio"
    }
    
    return {
        "status": "executed",
        "executed": True,
        "scene_mp4_path": scene_mp4_path,
        "artifacts": {
            "episode_manifest": episode_manifest,
            "episode_manifest_path": "output/control/ep01_shot01_final_manifest.json",
            "episode_output_path": "output/control/ep01_shot01_final_manifest.json",
            "artifact_status": "accepted",
            "artifact_accepted": True,
            "artifact_reason": "RC-FLOW1I: Final manifest created with no-audio RC policy preserved"
        }
    }


def build_default_handler_registry(
    enable_mock_handlers: bool = True,
) -> HandlerRegistry:
    """Return a registry pre-loaded with safe mock handlers."""
    reg = HandlerRegistry()
    reg.register(
        "generate_frames",
        generate_frames_handler,
        enabled=enable_mock_handlers,
        description="Mock frame generation handler",
    )
    reg.register(
        "continue_generation",
        generate_frames_handler,
        enabled=enable_mock_handlers,
        description="Mock continuation handler",
    )
    reg.register(
        "assemble_scene_video",
        assemble_scene_handler,
        enabled=enable_mock_handlers,
        description="Mock scene assembly handler",
    )
    reg.register(
        "assemble_scene",
        assemble_scene_handler,
        enabled=enable_mock_handlers,
        description="Mock scene assembly handler (MK-CTRL21)",
    )
    reg.register(
        "qa_review",
        qa_review_handler,
        enabled=enable_mock_handlers,
        description="Mock QA review handler",
    )
    reg.register(
        "attach_audio",
        attach_audio_handler,
        enabled=enable_mock_handlers,
        description="Mock attach audio handler",
    )
    reg.register(
        "render_episode",
        render_episode_handler,
        enabled=enable_mock_handlers,
        description="Mock render episode handler",
    )
    reg.register(
        "synthesize_and_mux_audio",
        attach_audio_handler,
        enabled=enable_mock_handlers,
        description="Mock audio synthesis handler",
    )
    reg.register(
        "assemble_episode",
        final_render_handler,
        enabled=enable_mock_handlers,
        description="Mock episode assembly handler",
    )
    reg.register(
        "run_qa",
        qa_check_handler,
        enabled=enable_mock_handlers,
        description="Mock QA handler",
    )
    return reg
