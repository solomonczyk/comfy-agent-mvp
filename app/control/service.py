"""MK-CTRL8 — Ledger-backed shot control service.

Production-safe entrypoint that wires the control stack with persistent
ledger enabled by default.  Uses injected handlers only; does not connect
real ComfyUI, ffmpeg, or TTS.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .action_plan import ActionPlanBuilder
from .action_runner import ControlledActionRunner
from .gate import ShotExecutionGate
from .handlers import HandlerRegistry
from .ledger import ShotLedgerStorage
from .models import ShotControlResponse
from .orchestrator import ShotControlOrchestrator
from .shot_controller import ShotController


class ShotControlService:
    """Wires controller + gate + planner + runner + ledger storage."""

    def __init__(
        self,
        controller: ShotController,
        gate: ShotExecutionGate,
        planner: ActionPlanBuilder,
        handlers: dict[str, Callable[..., Any]] | None = None,
        handler_registry: HandlerRegistry | None = None,
        ledger_root: Path | str = ".",
    ) -> None:
        self.controller = controller
        self.gate = gate
        self.planner = planner

        if handler_registry is not None:
            self.handlers = handler_registry.enabled_handlers()
            self.handler_registry = handler_registry  # Store for later access
        else:
            self.handlers = handlers or {}
            self.handler_registry = None

        self.ledger_root = Path(ledger_root)

        self._ledger = ShotLedgerStorage(self.ledger_root)
        self._runner = ControlledActionRunner(
            controller=controller,
            gate=gate,
            handlers=self.handlers,
            ledger=self._ledger,
            planner=planner,  # MK-CTRL21R
        )
        self._orchestrator = ShotControlOrchestrator(
            controller=controller,
            gate=gate,
            planner=planner,
            runner=self._runner,
        )

    def dry_run(
        self,
        episode_id: str,
        shot_id: str,
        requested_action: str,
    ) -> ShotControlResponse:
        """Inspect + gate + plan only. No execution, no ledger mutation."""
        return self._orchestrator.dry_run(episode_id, shot_id, requested_action)

    def execute(
        self,
        episode_id: str,
        shot_id: str,
        requested_action: str,
        allow_real_execution: bool = False,
    ) -> ShotControlResponse:
        """Inspect + gate + plan + at most one handler call with ledger.
        
        Args:
            episode_id: Episode identifier.
            shot_id: Shot identifier.
            requested_action: Action to execute.
            allow_real_execution: If True, allows real subprocess execution (MK-CTRL14).
                Default False for safety. Requires runner-level opt-in as well.
        """
        return self._orchestrator.execute(episode_id, shot_id, requested_action, allow_real_execution=allow_real_execution)
