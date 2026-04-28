"""MK-CTRL3 — Controlled action runner.

Reads shot state, checks permission via gate, executes exactly one
registered handler if allowed.  No production systems are hardwired.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from .action_plan import ActionPlanBuilder  # MK-CTRL21R
from .gate import ShotExecutionGate
from .handler_contracts import HandlerPayload
from .ledger import ShotLedgerRecord, ShotLedgerStorage, compact_recipe_validation_for_ledger
from .models import ShotStateReport
from .shot_controller import ShotController
from .shot_state_storage import ShotState, ShotStateStorage


@dataclass
class ActionRunResult:
    episode_id: str
    shot_id: str
    requested_action: str
    allowed: bool
    executed: bool
    executed_action: str | None
    current_state: str
    expected_next_action: str
    reason: str
    handler_result: dict | None = None
    control_executed: bool | None = None
    production_executed: bool | None = None
    handler_status: str | None = None
    subprocess_invoked: bool | None = None

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "requested_action": self.requested_action,
            "allowed": self.allowed,
            "executed": self.executed,
            "executed_action": self.executed_action,
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "reason": self.reason,
            "handler_result": self.handler_result,
            "control_executed": self.control_executed,
            "production_executed": self.production_executed,
            "handler_status": self.handler_status,
            "subprocess_invoked": self.subprocess_invoked,
        }


class ControlledActionRunner:
    """Execute one action per call through controller + gate + injected handlers."""

    def __init__(
        self,
        controller: ShotController,
        gate: ShotExecutionGate,
        handlers: dict[str, Callable[..., dict]],
        ledger: ShotLedgerStorage | None = None,
        planner: ActionPlanBuilder | None = None,  # MK-CTRL21R
    ) -> None:
        self.controller = controller
        self.gate = gate
        self.handlers = handlers
        self.ledger = ledger
        self.planner = planner or ActionPlanBuilder()  # MK-CTRL21R
        self.state_storage = ShotStateStorage(controller.root) if ledger else None

    def run_one(
        self,
        episode_id: str,
        shot_id: str,
        requested_action: str,
        allow_real_execution: bool = False,
    ) -> ActionRunResult:
        """Inspect, gate-check, and execute exactly one handler if allowed.
        
        Args:
            episode_id: Episode identifier.
            shot_id: Shot identifier.
            requested_action: Action to execute.
            allow_real_execution: If True, allows real subprocess execution (MK-CTRL14).
                Default False for safety. Requires runner-level opt-in as well.
        """
        report = self.controller.inspect(episode_id, shot_id)
        self._write_ledger(
            episode_id, shot_id,
            event_type="inspect",
            current_state=report.current_state,
            expected_next_action=report.next_action,
        )

        # MK-RECIPE7 — Build action plan to get recipe_validation for ledger evidence
        plan = self.planner.build(report, requested_action, project_root=self.controller.root)
        compact_recipe_validation = compact_recipe_validation_for_ledger(plan.recipe_validation)

        decision = self.gate.decide(report, requested_action, action_plan=plan)

        if not decision.allowed:
            self._write_ledger(
                episode_id, shot_id,
                event_type="action_denied",
                requested_action=requested_action,
                allowed=False,
                control_executed=False,
                production_executed=False,
                handler_status=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason=decision.reason,
                recipe_validation=compact_recipe_validation,
            )
            return ActionRunResult(
                episode_id=episode_id,
                shot_id=shot_id,
                requested_action=requested_action,
                allowed=False,
                executed=False,
                executed_action=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason=decision.reason,
                control_executed=False,
                production_executed=False,
                handler_status=None,
                subprocess_invoked=False,
            )

        if requested_action == "none":
            self._write_ledger(
                episode_id, shot_id,
                event_type="gate_decision",
                requested_action=requested_action,
                allowed=True,
                control_executed=False,
                production_executed=False,
                handler_status=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason="'none' is not an executable action",
            )
            return ActionRunResult(
                episode_id=episode_id,
                shot_id=shot_id,
                requested_action=requested_action,
                allowed=True,
                executed=False,
                executed_action=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason="'none' is not an executable action",
                control_executed=False,
                production_executed=False,
                handler_status=None,
                subprocess_invoked=False,
            )

        self._write_ledger(
            episode_id, shot_id,
            event_type="gate_decision",
            requested_action=requested_action,
            allowed=True,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            reason="action matches next expected step",
        )

        # MK-RECIPE7 — Action plan already built above, reuse it
        # plan = self.planner.build(report, requested_action)

        handler = self.handlers.get(requested_action)
        if handler is None:
            raise RuntimeError(
                f"Action '{requested_action}' is allowed but no handler is registered"
            )

        # RC-FLOW1D — Check action plan executable status and missing inputs before invoking handler
        # If action_plan.executable=false or missing_inputs is non-empty, do NOT invoke handler
        if not plan.executable or plan.missing_inputs:
            # Log blocked execution due to missing inputs
            self._write_ledger(
                episode_id, shot_id,
                event_type="action_blocked",
                requested_action=requested_action,
                allowed=True,
                executed=False,
                success=False,
                control_executed=True,
                production_executed=None,
                handler_status="blocked",
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason=f"action blocked: executable={plan.executable}, missing_inputs={plan.missing_inputs}",
            )
            # Return early without invoking handler
            return ActionRunResult(
                episode_id=episode_id,
                shot_id=shot_id,
                requested_action=requested_action,
                allowed=True,
                executed=False,
                executed_action=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason=f"action blocked: executable={plan.executable}, missing_inputs={plan.missing_inputs}",
                handler_result=None,
                control_executed=True,
                production_executed=None,
                handler_status="blocked",
            )

        # Build HandlerPayload for modern handlers (MK-CTRL13R)
        # Use the full action_plan from planner, not just brief_path
        brief_path = None
        for p in [
            self.controller.root / f"data/briefs/{episode_id}_{shot_id}_brief.md",
            self.controller.root / f"data/briefs/{shot_id}_brief.md",
            self.controller.root / f"data/{shot_id}_brief.md",
        ]:
            if p.exists() and p.stat().st_size > 0:
                brief_path = p
                break
        
        # MK-CTRL21R — Use full action_plan from planner, not minimal dict
        action_plan_dict = plan.to_dict()
        if brief_path:
            action_plan_dict["brief_path"] = str(brief_path)

        payload = HandlerPayload(
            episode_id=episode_id,
            shot_id=shot_id,
            action=requested_action,
            dry_validate=not allow_real_execution,  # Dry validate if not allowing real execution
            allow_real_execution=allow_real_execution,  # Propagate service-level flag (MK-CTRL14)
            state_report=report.to_dict(),
            action_plan=action_plan_dict,  # MK-CTRL21R — Use full action_plan
            extra={},
        )

        try:
            # Pass payload.to_dict() to handlers for compatibility
            handler_result = handler(payload.to_dict())
        except Exception:
            self._write_ledger(
                episode_id, shot_id,
                event_type="action_failed",
                requested_action=requested_action,
                allowed=True,
                executed=False,
                success=False,
                control_executed=True,
                production_executed=None,
                handler_status="failed",
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason="handler raised an exception",
            )
            raise

        # Derive production semantics from the handler_result dict.
        # Convert HandlerResult to dict if needed (MK-CTRL13R)
        if hasattr(handler_result, 'to_dict'):
            handler_result = handler_result.to_dict()
        
        # Prefer production_executed field if available (MK-CTRL26R)
        # Otherwise fall back to executed field for backward compatibility
        production_executed = (
            handler_result.get("production_executed")
            if isinstance(handler_result, dict) and "production_executed" in handler_result
            else (
                handler_result.get("executed")
                if isinstance(handler_result, dict)
                else None
            )
        )
        # Preserve subprocess_invoked field if available (MK-CTRL26R)
        # Default to false if not available (MK-CTRL26R-2)
        subprocess_invoked = (
            handler_result.get("subprocess_invoked")
            if isinstance(handler_result, dict) and "subprocess_invoked" in handler_result
            else None
        )
        handler_status = (
            handler_result.get("status")
            if isinstance(handler_result, dict)
            else None
        )

        # MK-CTRL15R: Handle blocked execution semantics
        # When real execution is blocked (e.g., by global kill switch), it should not be marked as successful
        is_blocked = handler_status == "blocked"
        
        # MK-CTRL26R-2: Ensure subprocess_invoked is false when blocked, not None
        if is_blocked and subprocess_invoked is None:
            subprocess_invoked = False
        
        # RC-FLOW1G: Handle mock handler semantics - mock handlers must not return production_executed=true
        # If handler_status is "mocked" and production_executed is False, allow execution but mark as not successful
        is_mocked_without_production = handler_status == "mocked" and production_executed is False
        
        # MK-CTRL18: Handle artifact failure semantics
        # When artifact is not accepted (missing, empty, or subprocess_failed), record as action_failed
        artifacts = handler_result.get("artifacts", {}) if isinstance(handler_result, dict) else {}
        artifact_accepted = artifacts.get("artifact_accepted", True)  # Default to True for backward compatibility
        artifact_status = artifacts.get("artifact_status", None)
        
        if is_blocked:
            event_type = "action_blocked"
            executed = False
            success = False
            # Extract reason from handler result artifacts if available
            reason = artifacts.get("reason", "real execution blocked") if isinstance(handler_result, dict) else "real execution blocked"
        elif is_mocked_without_production:
            # RC-FLOW1G: Mock handler without production execution should not be marked as successful
            # But handler was still invoked (executed=True), just not real production
            event_type = "action_executed"
            executed = True  # Handler was invoked (mocked)
            success = False  # But no real production execution
            reason = handler_result.get("reason", "mock handler does not produce real artifacts") if isinstance(handler_result, dict) else "mock handler does not produce real artifacts"
        elif not artifact_accepted and artifact_status not in ["not_applicable", None]:
            # Artifact failure: missing, empty, or subprocess_failed
            event_type = "action_failed"
            executed = True  # Subprocess was invoked
            success = False
            reason = artifacts.get("artifact_reason", "artifact not accepted")
        else:
            event_type = "action_executed"
            executed = True
            success = True
            reason = "handler executed successfully"

        self._write_ledger(
            episode_id, shot_id,
            event_type=event_type,
            requested_action=requested_action,
            allowed=True,
            executed=executed,
            success=success,
            control_executed=True,
            production_executed=production_executed,
            handler_status=handler_status,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            reason=reason,
            handler_result=handler_result,
            recipe_validation=compact_recipe_validation,  # MK-RECIPE7
        )

        # MK-CTRL19 — State transition after accepted artifact
        # MK-CTRL20 — Use frame_manifest_path instead of episode_output_path
        # MK-CTRL21 — Add scene artifact handling for assemble_scene
        # MK-CTRL22 — Add QA report handling for qa_review (both pass and fail)
        # MK-CTRL23 — Add audio artifact handling for attach_audio
        # MK-CTRL24 — Add episode artifact handling for render_episode
        # MK-CTRL37R — Store typed artifact paths for proper handoff between actions
        # Only transition if: action_executed, artifact_accepted=true, and action is generate_frames, assemble_scene, qa_review, attach_audio, or render_episode
        if (
            event_type == "action_executed"
            and success is True
            and requested_action in ["generate_frames", "assemble_scene", "qa_review", "attach_audio", "render_episode"]
            and self.state_storage is not None
        ):
            from_state = report.current_state
            
            # MK-CTRL37R — Load existing state to preserve typed artifacts
            existing_state = self.state_storage.load(episode_id, shot_id)
            
            # Initialize typed artifact paths from existing state (or None)
            frame_manifest_path = existing_state.frame_manifest_path if existing_state else None
            scene_mp4_path = existing_state.scene_mp4_path if existing_state else None
            qa_report_path = existing_state.qa_report_path if existing_state else None
            audio_output_path = existing_state.audio_output_path if existing_state else None
            episode_output_path = existing_state.episode_output_path if existing_state else None
            
            # Determine target state based on action and update typed artifact paths
            if requested_action == "generate_frames":
                to_state = "frames_generated"
                next_action = "assemble_scene"
                # MK-CTRL20 — Store frame_manifest_path
                frame_manifest_path = artifacts.get("frame_manifest_path") or artifacts.get("episode_output_path")
                artifact_path = frame_manifest_path  # Legacy field
                transition_reason = "generate_frames artifact accepted"
            elif requested_action == "assemble_scene":
                # RC-FLOW1B — Prevent state transition when mocked without scene artifact/manifest
                # Only allow transition if production_executed=true OR scene manifest exists
                scene_output_path = artifacts.get("scene_output_path")
                scene_manifest_path = artifacts.get("scene_manifest_path")
                
                # Check if we have a valid scene artifact or manifest
                has_scene_artifact = (
                    (production_executed is True and scene_output_path) or
                    scene_manifest_path is not None
                )
                
                if not has_scene_artifact and handler_status == "mocked":
                    # Mocked execution without artifact - do not transition state
                    to_state = from_state  # Stay in current state
                    next_action = report.next_action  # Keep same next action
                    scene_mp4_path = None
                    artifact_path = None
                    transition_reason = "assemble_scene mocked without artifact - state not transitioned"
                else:
                    # Valid artifact or production execution - allow transition
                    to_state = "scene_assembled"
                    next_action = "qa_review"  # MK-CTRL21 — Next action after scene assembly
                    # MK-CTRL21 — Store scene_output_path as scene_mp4_path
                    scene_mp4_path = scene_output_path or scene_manifest_path
                    artifact_path = scene_mp4_path  # Legacy field
                    transition_reason = "assemble_scene artifact accepted"
            elif requested_action == "qa_review":
                # MK-CTRL22 — Handle both QA pass and fail
                artifact_status = artifacts.get("artifact_status")
                if artifact_status == "accepted" and artifacts.get("artifact_accepted") is True:
                    to_state = "qa_passed"
                    next_action = "attach_audio"  # MK-CTRL22 — Next action after QA pass
                    # MK-CTRL22 — Store qa_report_path (but keep scene_mp4_path for attach_audio)
                    qa_report_path = artifacts.get("qa_report_path")
                    artifact_path = qa_report_path  # Legacy field
                    transition_reason = "qa_review artifact accepted"
                elif artifact_status == "qa_failed":
                    # QA failed - transition to qa_failed state
                    to_state = "qa_failed"
                    next_action = "generate_frames"  # MK-CTRL22 — Next action after QA fail (regenerate)
                    qa_report_path = artifacts.get("qa_report_path")
                    artifact_path = qa_report_path  # Legacy field
                    transition_reason = f"qa_review failed: {artifacts.get('artifact_reason', 'unknown')}"
                else:
                    # No transition for other statuses - still return ActionRunResult
                    pass
            elif requested_action == "attach_audio":
                # MK-CTRL23 — Handle audio attachment (including skipped audio)
                artifact_status = artifacts.get("artifact_status")
                if artifact_status in ["accepted", "skipped_no_audio"] and artifacts.get("artifact_accepted") is True:
                    to_state = "audio_attached"
                    next_action = "render_episode"  # MK-CTRL23 — Next action after audio attached
                    # MK-CTRL37R-FIX — Store scene_mp4_with_audio_path (the actual audio MP4) not audio_manifest_path
                    # The attach_audio runner returns scene_mp4_with_audio_path, not audio_output_path
                    audio_output_path = artifacts.get("scene_mp4_with_audio_path") or artifacts.get("audio_output_path") or artifacts.get("audio_manifest_path")
                    artifact_path = audio_output_path  # Legacy field
                    transition_reason = artifacts.get("artifact_reason", "attach_audio artifact accepted")
                    
                    # RC-FLOW1H: Write audio_manifest.json for no-audio policy
                    audio_manifest = artifacts.get("audio_manifest")
                    audio_manifest_path = artifacts.get("audio_manifest_path")
                    if audio_manifest and audio_manifest_path:
                        # Resolve audio_manifest_path relative to controller root
                        from pathlib import Path
                        import json
                        manifest_path = Path(self.controller.root) / audio_manifest_path
                        manifest_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(manifest_path, 'w') as f:
                            json.dump(audio_manifest, f, indent=2)
                else:
                    # Audio attachment failed - no transition, but still return ActionRunResult
                    pass
            elif requested_action == "render_episode":
                # MK-CTRL24 — Handle episode rendering
                artifact_status = artifacts.get("artifact_status")
                if artifact_status == "accepted" and artifacts.get("artifact_accepted") is True:
                    to_state = "episode_rendered"
                    next_action = "none"  # MK-CTRL24 — episode_rendered is terminal state
                    # MK-CTRL24 — Store episode_output_path
                    episode_output_path = artifacts.get("episode_output_path")
                    artifact_path = episode_output_path  # Legacy field
                    transition_reason = artifacts.get("artifact_reason", "render_episode artifact accepted")
                    
                    # RC-FLOW1I: Write episode_manifest.json for final manifest
                    episode_manifest = artifacts.get("episode_manifest")
                    episode_manifest_path = artifacts.get("episode_manifest_path")
                    if episode_manifest and episode_manifest_path:
                        # Resolve episode_manifest_path relative to controller root
                        from pathlib import Path
                        import json
                        manifest_path = Path(self.controller.root) / episode_manifest_path
                        manifest_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(manifest_path, 'w') as f:
                            json.dump(episode_manifest, f, indent=2)
                else:
                    # Episode rendering failed - no transition, but still return ActionRunResult
                    pass
            else:
                # Should not happen given the condition above, but still return ActionRunResult
                pass
            
            # Only persist state if we actually have a transition (variables are defined)
            if 'to_state' in locals() and 'next_action' in locals():
                # Persist new state with typed artifact paths
                new_state = ShotState(
                    episode_id=episode_id,
                    shot_id=shot_id,
                    current_state=to_state,
                    expected_next_action=next_action,
                    last_updated=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    artifact_path=artifact_path,  # Legacy field
                    brief_path=report.brief_path,  # Preserve brief_path
                    transition_reason=transition_reason,
                    # MK-CTRL37R — Typed artifact paths
                    frame_manifest_path=frame_manifest_path,
                    scene_mp4_path=scene_mp4_path,
                    qa_report_path=qa_report_path,
                    audio_output_path=audio_output_path,
                    episode_output_path=episode_output_path,
                )
                self.state_storage.save(new_state)
                
                # Record state transition in ledger
                self._write_ledger(
                    episode_id, shot_id,
                    event_type="state_transition",
                    from_state=from_state,
                    to_state=to_state,
                    reason=transition_reason,
                    artifact_path=artifact_path,
                    current_state=to_state,
                    expected_next_action=next_action,
                )

        return ActionRunResult(
            episode_id=episode_id,
            shot_id=shot_id,
            requested_action=requested_action,
            allowed=True,
            executed=executed,
            executed_action=requested_action if not is_blocked else None,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            reason=reason,
            handler_result=handler_result,
            control_executed=True,
            production_executed=production_executed,
            handler_status=handler_status,
            subprocess_invoked=subprocess_invoked,
        )

    def run_next(self, episode_id: str, shot_id: str) -> ActionRunResult:
        """Inspect shot and execute the next allowed action automatically."""
        report = self.controller.inspect(episode_id, shot_id)
        next_action = report.next_action

        # Blocked must be caught before done/none shortcut
        if report.current_state == "blocked":
            decision = self.gate.decide(report, next_action)
            return ActionRunResult(
                episode_id=episode_id,
                shot_id=shot_id,
                requested_action=next_action,
                allowed=False,
                executed=False,
                executed_action=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason=decision.reason,
                control_executed=False,
                production_executed=False,
                handler_status=None,
            )

        if next_action == "none" or report.is_done:
            return ActionRunResult(
                episode_id=episode_id,
                shot_id=shot_id,
                requested_action="none",
                allowed=True,
                executed=False,
                executed_action=None,
                current_state=report.current_state,
                expected_next_action=report.next_action,
                reason="next action is 'none' — nothing to execute",
                control_executed=False,
                production_executed=False,
                handler_status=None,
            )
        return self.run_one(episode_id, shot_id, next_action)

    def _write_ledger(self, episode_id: str, shot_id: str, **kwargs: Any) -> None:
        if self.ledger is None:
            return
        record = ShotLedgerRecord(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            episode_id=episode_id,
            shot_id=shot_id,
            **kwargs,
        )
        self.ledger.append(episode_id, shot_id, record)
