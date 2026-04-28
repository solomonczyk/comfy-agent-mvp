"""MK-CTRL2 — Shot execution gate.

Pure permission layer.  Decides whether a requested action is allowed
for a given shot state.  Never executes, writes, or mutates anything.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import ShotStateReport


@dataclass
class ActionGateDecision:
    episode_id: str
    shot_id: str
    requested_action: str
    allowed: bool
    reason: str
    current_state: str
    expected_next_action: str
    is_blocked: bool
    is_done: bool

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "requested_action": self.requested_action,
            "allowed": self.allowed,
            "reason": self.reason,
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "is_blocked": self.is_blocked,
            "is_done": self.is_done,
        }


class ShotExecutionGate:
    """Pure gate — decides, never executes."""

    KNOWN_ACTIONS: frozenset[str] = frozenset(
        [
            "create_brief",
            "generate_frames",
            "continue_generation",
            "assemble_scene",
            "assemble_scene_video",
            "qa_review",  # MK-CTRL22
            "attach_audio",  # MK-CTRL23
            "render_episode",  # MK-CTRL24
            "synthesize_and_mux_audio",
            "assemble_episode",
            "run_qa",
            "none",
        ]
    )

    def decide(self, report: ShotStateReport, requested_action: str, action_plan: Any = None) -> ActionGateDecision:
        is_blocked = report.current_state == "blocked"
        is_done = report.is_done
        expected = report.next_action

        # MK-RECIPE7 — Check action plan allowed status first
        if action_plan is not None and hasattr(action_plan, "allowed"):
            if not action_plan.allowed:
                # If action plan is not allowed, deny with its reason
                return self._deny(report, requested_action, action_plan.reason or "action plan not allowed")

        # MK-RECIPE7 — Check recipe validation from action plan if provided
        if action_plan is not None:
            recipe_validation = getattr(action_plan, "recipe_validation", None)
            if isinstance(recipe_validation, dict) and recipe_validation.get("available"):
                verdict = recipe_validation.get("verdict")
                if verdict == "fail" and requested_action == "generate_frames":
                    return self._deny(report, requested_action, "recipe validation failed")

        # Rule 4 — unknown action
        if requested_action not in self.KNOWN_ACTIONS:
            return self._deny(report, requested_action, "unknown action")

        # Rule 6 — "none" only when blocked or done
        if requested_action == "none":
            if is_done:
                return self._allow(report, requested_action, "done state: none is valid")
            if is_blocked:
                return self._allow(report, requested_action, "blocked state: none is valid")
            return self._deny(report, requested_action, "'none' is not a valid execution action for this state")

        # Rule 1 — blocked state
        if is_blocked:
            reason = f"blocked: {report.blocked_reason or 'no reason'}"
            return self._deny(report, requested_action, reason)

        # Rule 2 — done state
        if is_done:
            return self._deny(report, requested_action, "shot is already done")

        # Rule 3 — exact next action only
        if requested_action != expected:
            return self._deny(
                report, requested_action,
                f"expected next action is '{expected}', got '{requested_action}'"
            )

        # Rule 5 — valid action
        return self._allow(report, requested_action, "action matches next expected step")

    def assert_allowed(self, report: ShotStateReport, requested_action: str, action_plan: Any = None) -> None:
        decision = self.decide(report, requested_action, action_plan=action_plan)
        if not decision.allowed:
            raise RuntimeError(
                f"Action '{requested_action}' denied for {report.episode_id}/{report.shot_id}: "
                f"{decision.reason}"
            )

    # ── helpers ───────────────────────────────────────────────────────

    def _allow(self, report: ShotStateReport, action: str, reason: str) -> ActionGateDecision:
        return ActionGateDecision(
            episode_id=report.episode_id,
            shot_id=report.shot_id,
            requested_action=action,
            allowed=True,
            reason=reason,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            is_blocked=report.current_state == "blocked",
            is_done=report.is_done,
        )

    def _deny(self, report: ShotStateReport, action: str, reason: str) -> ActionGateDecision:
        return ActionGateDecision(
            episode_id=report.episode_id,
            shot_id=report.shot_id,
            requested_action=action,
            allowed=False,
            reason=reason,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            is_blocked=report.current_state == "blocked",
            is_done=report.is_done,
        )
