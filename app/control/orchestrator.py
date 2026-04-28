"""MK-CTRL6 — Unified shot control orchestrator.

Single facade that coordinates inspect → gate → plan → (optional execute).
Does not directly call ComfyUI, ffmpeg, or TTS.
"""
from __future__ import annotations

from .action_plan import ActionPlanBuilder
from .action_runner import ActionRunResult, ControlledActionRunner
from .gate import ActionGateDecision, ShotExecutionGate
from .models import ActionPlan, ShotControlResponse, ShotStateReport
from .shot_controller import ShotController


class ShotControlOrchestrator:
    """Unified control entry point: dry_run (pure) or execute (one action)."""

    def __init__(
        self,
        controller: ShotController,
        gate: ShotExecutionGate,
        planner: ActionPlanBuilder,
        runner: ControlledActionRunner | None = None,
    ) -> None:
        self.controller = controller
        self.gate = gate
        self.planner = planner
        self.runner = runner

    # ── public API ────────────────────────────────────────────────────

    def dry_run(
        self, episode_id: str, shot_id: str, requested_action: str
    ) -> ShotControlResponse:
        """Inspect + gate + plan only. No execution, no side effects."""
        report, decision, plan = self._inspect_gate_plan(
            episode_id, shot_id, requested_action
        )
        return ShotControlResponse(
            episode_id=episode_id,
            shot_id=shot_id,
            requested_action=requested_action,
            mode="dry_run",
            state_report=report.to_dict(),
            gate_decision=decision.to_dict(),
            action_plan=plan.to_dict(),
            action_result=None,
            ledger_enabled=self._ledger_enabled(),
            success=decision.allowed,
            reason=plan.reason,
        )

    def execute(
        self, episode_id: str, shot_id: str, requested_action: str, allow_real_execution: bool = False
    ) -> ShotControlResponse:
        """Inspect + gate + plan + at most one handler call.
        
        Args:
            episode_id: Episode identifier.
            shot_id: Shot identifier.
            requested_action: Action to execute.
            allow_real_execution: If True, allows real subprocess execution (MK-CTRL14).
                Default False for safety. Requires runner-level opt-in as well.
        """
        report, decision, plan = self._inspect_gate_plan(
            episode_id, shot_id, requested_action
        )

        if self.runner is None:
            raise RuntimeError(
                f"Action '{requested_action}' for {episode_id}/{shot_id} "
                "but no runner is configured"
            )

        result = self.runner.run_one(episode_id, shot_id, requested_action, allow_real_execution=allow_real_execution)

        return ShotControlResponse(
            episode_id=episode_id,
            shot_id=shot_id,
            requested_action=requested_action,
            mode="execute",
            state_report=report.to_dict(),
            gate_decision=decision.to_dict(),
            action_plan=plan.to_dict(),
            action_result=result.to_dict(),
            ledger_enabled=self._ledger_enabled(),
            success=result.allowed and (result.executed or result.requested_action == "none"),
            reason=result.reason,
        )

    # ── helpers ───────────────────────────────────────────────────────

    def _inspect_gate_plan(
        self, episode_id: str, shot_id: str, requested_action: str
    ) -> tuple[ShotStateReport, ActionGateDecision, ActionPlan]:
        """Shared inspect → gate → plan pipeline."""
        report = self.controller.inspect(episode_id, shot_id)
        decision = self.gate.decide(report, requested_action)
        # MK-GEN2R — Pass project_root to planner for prompt_pack detection
        plan = self.planner.build(report, requested_action, project_root=self.controller.root)
        return report, decision, plan

    def _ledger_enabled(self) -> bool:
        return self.runner is not None and self.runner.ledger is not None
