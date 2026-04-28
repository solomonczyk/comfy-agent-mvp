"""Factory for building ShotControlService instances.

MK-CTRL26 — Centralizes service construction to avoid duplication
across CLI, tests, and other entry points.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .action_plan import ActionPlanBuilder
from .gate import ShotExecutionGate
from .handlers import build_default_handler_registry
from .orchestrator import ShotControlOrchestrator
from .service import ShotControlService
from .shot_controller import ShotController


def build_shot_control_service(
    project_root: Path | str = ".",
    enable_mock_handlers: bool = True,
) -> ShotControlService:
    """Build a ShotControlService with default configuration.
    
    Args:
        project_root: Root directory for the project (where output/control lives).
        enable_mock_handlers: If True, use mock handlers (safe for testing).
            If False, use real handlers. Real execution requires explicit opt-in at runtime
            via allow_real_execution flag and COMFY_AGENT_REAL_EXECUTION_ENABLED environment variable.
    
    Returns:
        Configured ShotControlService instance.
    """
    project_root = Path(project_root)
    
    # Build core components
    controller = ShotController(project_root)
    gate = ShotExecutionGate()
    planner = ActionPlanBuilder()
    
    # Build handlers
    if enable_mock_handlers:
        # Use mock handlers for testing
        handler_registry = build_default_handler_registry(enable_mock_handlers=True)
    else:
        # Use real handlers with safe defaults
        # Real handlers require explicit opt-in at runtime via allow_real_execution flag
        # and COMFY_AGENT_REAL_EXECUTION_ENABLED environment variable
        from .real_generate_handler import (
            build_real_generate_frames_handler_registry,
            build_real_assemble_scene_handler_registry,
            build_real_qa_review_handler_registry,
            build_real_attach_audio_handler_registry,
            build_real_render_episode_handler_registry,
        )
        from .generate_frames_runner import GenerateFramesRunner
        from .assemble_scene_runner import AssembleSceneRunner
        from .qa_review_runner import QaReviewRunner
        from .attach_audio_runner import AttachAudioRunner
        from .render_episode_runner import RenderEpisodeRunner
        from .real_execution_guard import is_real_execution_globally_enabled
        
        # Check if global kill switch is enabled
        # If enabled, configure real handlers with runner factory
        # If disabled, use safe defaults (enable_real_handlers=False, runner_factory=None)
        global_enabled = is_real_execution_globally_enabled()
        
        if global_enabled:
            # Create runner factories that return runners with subprocess execution enabled
            def generate_frames_runner_factory():
                return GenerateFramesRunner(
                    project_root=project_root,
                    allow_subprocess_execution=True,
                )
            def assemble_scene_runner_factory():
                return AssembleSceneRunner(
                    project_root=project_root,
                    allow_subprocess_execution=True,
                )
            def qa_review_runner_factory():
                return QaReviewRunner(
                    project_root=project_root,
                    allow_subprocess_execution=True,
                )
            def attach_audio_runner_factory():
                return AttachAudioRunner(
                    project_root=project_root,
                    allow_subprocess_execution=True,
                )
            def render_episode_runner_factory():
                return RenderEpisodeRunner(
                    project_root=project_root,
                    allow_subprocess_execution=True,
                )
            enable_real_handlers = True
        else:
            generate_frames_runner_factory = None
            assemble_scene_runner_factory = None
            qa_review_runner_factory = None
            attach_audio_runner_factory = None
            render_episode_runner_factory = None
            enable_real_handlers = False
        
        # Build separate registries and merge them
        generate_frames_registry = build_real_generate_frames_handler_registry(
            enable_real_handlers=enable_real_handlers,
            runner_factory=generate_frames_runner_factory,
            output_root=project_root / "output",
        )
        assemble_scene_registry = build_real_assemble_scene_handler_registry(
            enable_real_handlers=enable_real_handlers,
            runner_factory=assemble_scene_runner_factory,
            output_root=project_root / "output",
        )
        qa_review_registry = build_real_qa_review_handler_registry(
            enable_real_handlers=enable_real_handlers,
            runner_factory=qa_review_runner_factory,
            output_root=project_root / "output",
        )
        attach_audio_registry = build_real_attach_audio_handler_registry(
            enable_real_handlers=enable_real_handlers,
            runner_factory=attach_audio_runner_factory,
            output_root=project_root / "output",
        )
        render_episode_registry = build_real_render_episode_handler_registry(
            enable_real_handlers=enable_real_handlers,
            runner_factory=render_episode_runner_factory,
            output_root=project_root / "output",
        )
        
        # Merge registries: start with generate_frames registry and add assemble_scene, qa_review, attach_audio, render_episode
        handler_registry = generate_frames_registry
        # Register assemble_scene handler from its registry
        assemble_scene_handler = assemble_scene_registry.get("assemble_scene")
        handler_registry.register(
            "assemble_scene",
            assemble_scene_handler,
            enabled=True,
            description="Real assemble_scene handler (MK-CTRL21)",
        )
        # Register qa_review handler from its registry
        qa_review_handler = qa_review_registry.get("qa_review")
        handler_registry.register(
            "qa_review",
            qa_review_handler,
            enabled=True,
            description="Real qa_review handler (MK-CTRL31)",
        )
        # Register attach_audio handler from its registry
        attach_audio_handler = attach_audio_registry.get("attach_audio")
        handler_registry.register(
            "attach_audio",
            attach_audio_handler,
            enabled=True,
            description="Real attach_audio handler (MK-CTRL32)",
        )
        # Register render_episode handler from its registry
        render_episode_handler = render_episode_registry.get("render_episode")
        handler_registry.register(
            "render_episode",
            render_episode_handler,
            enabled=True,
            description="Real render_episode handler (MK-CTRL33)",
        )
    
    handlers = handler_registry.enabled_handlers()
    
    # Build service
    service = ShotControlService(
        controller=controller,
        gate=gate,
        planner=planner,
        handlers=handlers,
        handler_registry=handler_registry,
        ledger_root=project_root,
    )
    
    return service
