"""RC-COMBINE-V2-HUMAN-PREVIEW-REVIEW-GATE-001 — Human Preview Review Decision Gate Processor.

Closes the feature-level layer for human/operator preview review decision processing.

The agent MUST NOT:
- Choose a visual verdict itself
- Consider a preview accepted based on technical признаки alone
- Proceed to voice/audio generation

The agent MAY ONLY:
- Check for the presence of a human/operator decision input
- Validate it against the schema
- Apply the allowed state transition via the state machine
- Create artifacts/proof of the gate decision
- Stop before voice/audio generation

If no real operator verdict is available, honestly record the blocker
and keep state: preview_operator_review_required.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.orchestrator.state_machine import CombineStateMachine

TASK_ID = "RC-COMBINE-V2-HUMAN-PREVIEW-REVIEW-GATE-001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_project_root(project_root: Optional[str]) -> Path:
    if project_root:
        return Path(project_root).resolve()
    return Path.cwd().resolve()


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_ledger(ledger_path: Path) -> list:
    data = _read_json(ledger_path)
    return data if isinstance(data, list) else []


def _write_ledger(ledger_path: Path, events: list) -> None:
    _write_json(ledger_path, events)


# ---------------------------------------------------------------------------
# Operator Decision Schema (canonical, gate-owned)
# ---------------------------------------------------------------------------

VALID_VERDICTS = ["accepted_for_voice_stage", "rejected_needs_preview_fix", "needs_manual_review"]

OPERATOR_DECISION_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Preview Operator Decision Input",
    "description": "Operator decision on preview render quality. Must be provided by a human operator.",
    "type": "object",
    "required": [
        "operator_verdict",
        "operator_notes",
        "visual_review_performed_by_operator",
        "preview_lowres_reviewed",
        "preview_gif_reviewed",
        "contact_sheet_reviewed",
        "production_accepted",
    ],
    "properties": {
        "operator_verdict": {
            "type": "string",
            "enum": VALID_VERDICTS,
            "description": "Operator verdict on preview quality. accepted_for_voice_stage enables voice readiness; rejected_needs_preview_fix triggers correction plan; needs_manual_review keeps state pending operator manual review.",
        },
        "operator_notes": {
            "type": "string",
            "description": "Free-text notes from the operator about the preview.",
        },
        "visual_review_performed_by_operator": {
            "type": "boolean",
            "description": "Must be true — indicates a human performed the visual review.",
        },
        "preview_lowres_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the low-res MP4 preview.",
        },
        "preview_gif_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the GIF preview.",
        },
        "contact_sheet_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the contact sheet.",
        },
        "production_accepted": {
            "type": "boolean",
            "const": False,
            "description": "Must be false — production acceptance is a later gate.",
        },
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Verdict -> target state mapping (authoritative)
# ---------------------------------------------------------------------------

VERDICT_TO_TARGET_STATE: Dict[str, str] = {
    "accepted_for_voice_stage": "voice_generation_authorization_required",
    "rejected_needs_preview_fix": "preview_correction_plan_required",
    "needs_manual_review": "preview_operator_review_required",
}

# ---------------------------------------------------------------------------
# 1. Operator Decision Validation
# ---------------------------------------------------------------------------


def validate_operator_decision(
    decision: Dict[str, Any],
) -> Tuple[bool, str]:
    """Validate operator decision structure and semantics.

    The agent must NOT:
    - Accept preview on behalf of operator
    - Set visual_review_performed_by_operator to true
    - Override operator_verdict
    - Set production_accepted to true

    Returns:
        (is_valid, message)
    """
    if not isinstance(decision, dict):
        return False, "Decision is not a valid JSON object"

    required_fields = [
        "operator_verdict",
        "operator_notes",
        "visual_review_performed_by_operator",
        "preview_lowres_reviewed",
        "preview_gif_reviewed",
        "contact_sheet_reviewed",
        "production_accepted",
    ]
    missing = [f for f in required_fields if f not in decision]
    if missing:
        return False, f"Missing required fields: {missing}"

    # production_accepted must be false at this gate
    if decision.get("production_accepted", False):
        return (
            False,
            "production_accepted must be false at the preview review gate. "
            "Production acceptance is a downstream gate, not here.",
        )

    # visual_review must be true and indicates human performed it
    if not decision.get("visual_review_performed_by_operator", False):
        return (
            False,
            "visual_review_performed_by_operator must be true. "
            "Agent must not set this field — only a human operator may assert visual review.",
        )

    # Verdict must be one of the three valid options
    verdict = decision.get("operator_verdict", "")
    if verdict not in VALID_VERDICTS:
        return False, (
            f"Unknown operator_verdict: '{verdict}'. "
            f"Must be one of {VALID_VERDICTS}. "
            f"Agent must not fabricate verdicts."
        )

    return True, "Decision valid — operator verdict accepted."


# ---------------------------------------------------------------------------
# 2. Operator Decision Ingestion
# ---------------------------------------------------------------------------


def read_operator_decision(
    control_dir: Path,
    decision_file: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Read and validate operator decision from file.

    Args:
        control_dir: Path to control directory.
        decision_file: Optional explicit path to decision file.

    Returns:
        (found, decision_data, message)
    """
    if decision_file:
        decision_path = Path(decision_file)
    else:
        decision_path = control_dir / "preview_operator_decision_input.json"

    if not decision_path.exists():
        return False, None, f"Operator decision file not found: {decision_path}"

    data = _read_json(decision_path)
    if data is None:
        return False, None, "Operator decision file contains invalid JSON"

    valid, msg = validate_operator_decision(data)
    if not valid:
        return False, data, msg

    return True, data, "Operator decision valid"


# ---------------------------------------------------------------------------
# 3. Target State Resolution (with state machine validation)
# ---------------------------------------------------------------------------


def resolve_target_state(
    verdict: str,
) -> Tuple[bool, str, str]:
    """Resolve the target state from an operator verdict.

    Validates that the transition is allowed by the state machine.

    Returns:
        (valid, target_state, message)
    """
    if verdict not in VERDICT_TO_TARGET_STATE:
        return False, "", f"Unknown verdict '{verdict}' — no target state defined."

    target_state = VERDICT_TO_TARGET_STATE[verdict]

    # Validate that the transition exists in the state machine
    if not CombineStateMachine.is_valid_state(target_state):
        return (
            False,
            "",
            f"Target state '{target_state}' is not a valid state machine state.",
        )

    return True, target_state, f"Target state resolved: {target_state}"


# ---------------------------------------------------------------------------
# 4. Gate Proof Builder
# ---------------------------------------------------------------------------


def build_gate_proof(
    verdict_found: bool,
    verdict: Optional[str],
    decision_valid: bool,
    target_state: str,
    transition_valid: bool,
    blocked: bool,
    blocker_reason: Optional[str],
    artifacts_created: List[str],
) -> Dict[str, Any]:
    """Build the canonical gate proof artifact.

    Every field is frozen at decision time. The proof documents what the
    gate decided and why — it is NOT mutable by a future agent step.
    """
    return {
        "task_id": TASK_ID,
        "feature_completed": True,
        "previous_layer": "RC-COMBINE-V2-POST-PREVIEW-OPERATOR-REVIEW-REPAIR-001-FIX",
        "previous_commit": "12227a4",
        "human_preview_review_gate_executed": True,
        "operator_decision_found": verdict_found,
        "operator_decision_valid": decision_valid,
        "operator_verdict": verdict if verdict_found else None,
        "agent_did_not_choose_verdict": True,
        "agent_did_not_accept_preview": True,
        "agent_did_not_override": True,
        "state_machine_transition_valid": transition_valid,
        "blocked": blocked,
        "blocker_reason": blocker_reason,
        "target_state": target_state,
        "production_accepted": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "artifacts_created": artifacts_created,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_blocker_packet() -> Dict[str, Any]:
    """Build a blocker packet when no valid operator decision is available."""
    return {
        "task_id": TASK_ID,
        "gate_blocked": True,
        "blocker_type": "missing_operator_decision",
        "reason": (
            "Operator preview decision has not been provided. "
            "The gate cannot proceed without a valid operator verdict. "
            "Agent must not fabricate or infer a verdict."
        ),
        "resolution": (
            "Create preview_operator_decision_input.json with a valid operator verdict "
            f"({', '.join(VALID_VERDICTS)})."
        ),
        "agent_may_not_choose_verdict": True,
        "agent_may_not_accept_preview": True,
        "fake_visual_acceptance_prevented": True,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "preview_operator_review_required",
        "next_allowed_action": "preview_operator_review_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 5. Artifact Index and Ledger Updates
# ---------------------------------------------------------------------------


def build_artifact_index_update(
    target_state: str,
    verdict: Optional[str],
    blocked: bool,
    artifacts: List[str],
) -> Dict[str, Any]:
    """Build artifact index update payload."""
    update: Dict[str, Any] = {
        "task_id": TASK_ID,
        "current_state": target_state,
        "next_allowed_action": target_state,
        "production_accepted": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "human_preview_review_gate_executed": True,
        "operator_verdict": verdict,
        "gate_blocked": blocked,
        "artifacts": artifacts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return update


def build_ledger_events(
    target_state: str,
    verdict: Optional[str],
    blocked: bool,
    decision_valid: bool,
    artifacts: List[str],
) -> list:
    """Build ledger events for the gate cycle."""
    timestamp = datetime.now(timezone.utc).isoformat()
    events = []

    if blocked:
        events.append({
            "event_type": "human_preview_review_gate_blocked",
            "task_id": TASK_ID,
            "stage": "preview_operator_review_required",
            "blocker_type": "missing_operator_decision",
            "fake_visual_acceptance_prevented": True,
            "agent_may_not_choose_verdict": True,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "artifacts_created": artifacts,
            "timestamp": timestamp,
        })
    else:
        events.append({
            "event_type": "human_preview_review_gate_executed",
            "task_id": TASK_ID,
            "stage": target_state,
            "operator_verdict": verdict,
            "decision_valid": decision_valid,
            "agent_did_not_choose_verdict": True,
            "agent_did_not_accept_preview": True,
            "agent_did_not_override": True,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "artifacts_created": artifacts,
            "timestamp": timestamp,
        })

    return events


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_human_preview_review_gate(
    project_root: Optional[str] = None,
    decision_file: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the Human Preview Review Decision Gate.

    This is the canonical entry point for processing a human operator's
    preview review decision. It enforces that:

    1. The agent does NOT choose or infer a verdict.
    2. The agent does NOT accept preview on behalf of the operator.
    3. The agent does NOT override an operator decision.
    4. State transitions are validated against the CombineStateMachine.
    5. All decisions are frozen in a proof artifact.
    6. The system stops before voice/audio generation.

    Args:
        project_root: Path to the project root (default: cwd).
        decision_file: Optional explicit path to operator decision file.
        dry_run: If True, validate and report without writing artifacts.

    Returns:
        A result dict with gate status, target state, and proof info.
    """
    root = _resolve_project_root(project_root)
    control_dir = root / "output" / "control"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Default: stay at current state if blocked
    default_state = "preview_operator_review_required"

    # ------------------------------------------------------------------
    # Step 1: Check for operator decision
    # ------------------------------------------------------------------
    verdict_found, decision_data, decision_msg = read_operator_decision(
        control_dir, decision_file
    )

    if not verdict_found:
        # No operator decision — block and stay in current state
        blocker = build_blocker_packet()

        target_state = default_state
        transition_valid = CombineStateMachine.can_transition(
            default_state, default_state
        )

        artifacts = [
            "human_preview_review_gate_proof.json",
            "human_preview_review_gate_blocker.json",
        ]

        proof = build_gate_proof(
            verdict_found=False,
            verdict=None,
            decision_valid=False,
            target_state=target_state,
            transition_valid=transition_valid,
            blocked=True,
            blocker_reason=decision_msg,
            artifacts_created=artifacts,
        )

        if not dry_run:
            _write_json(
                control_dir / "human_preview_review_gate_proof.json", proof
            )
            _write_json(
                control_dir / "human_preview_review_gate_blocker.json", blocker
            )

            # Update artifact index
            existing_index = _read_json(control_dir / "artifact_index.json") or {}
            index_update = build_artifact_index_update(
                target_state=target_state,
                verdict=None,
                blocked=True,
                artifacts=artifacts,
            )
            existing_index.update(index_update)
            _write_json(control_dir / "artifact_index.json", existing_index)

            # Update ledger
            ledger_path = control_dir / "episode_ledger.json"
            existing_ledger = _read_ledger(ledger_path)
            new_events = build_ledger_events(
                target_state=target_state,
                verdict=None,
                blocked=True,
                decision_valid=False,
                artifacts=artifacts,
            )
            existing_ledger.extend(new_events)
            _write_ledger(ledger_path, existing_ledger)

        return {
            "task_id": TASK_ID,
            "status": "blocked",
            "gate_blocked": True,
            "blocker_type": "missing_operator_decision",
            "operator_verdict_provided": False,
            "operator_decision_found": False,
            "decision_message": decision_msg,
            "fake_visual_acceptance_prevented": True,
            "agent_may_not_choose_verdict": True,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_state,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 2: Validate decision semantics
    # ------------------------------------------------------------------
    decision_valid, decision_msg = validate_operator_decision(decision_data)

    if not decision_valid:
        # Invalid decision — block with message, stay in current state
        target_state = default_state
        transition_valid = CombineStateMachine.can_transition(
            default_state, default_state
        )

        artifacts = ["human_preview_review_gate_proof.json"]

        proof = build_gate_proof(
            verdict_found=True,
            verdict=decision_data.get("operator_verdict", ""),
            decision_valid=False,
            target_state=target_state,
            transition_valid=transition_valid,
            blocked=True,
            blocker_reason=decision_msg,
            artifacts_created=artifacts,
        )

        if not dry_run:
            _write_json(
                control_dir / "human_preview_review_gate_proof.json", proof
            )

        return {
            "task_id": TASK_ID,
            "status": "error",
            "gate_blocked": True,
            "operator_verdict_provided": True,
            "decision_valid": False,
            "decision_message": decision_msg,
            "operator_verdict": decision_data.get("operator_verdict", ""),
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_state,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 3: Resolve target state from verdict
    # ------------------------------------------------------------------
    verdict = decision_data["operator_verdict"]
    state_valid, target_state, state_msg = resolve_target_state(verdict)

    if not state_valid:
        # Target state not found in state machine — safety block
        target_state = default_state

        artifacts = ["human_preview_review_gate_proof.json"]

        proof = build_gate_proof(
            verdict_found=True,
            verdict=verdict,
            decision_valid=True,
            target_state=default_state,
            transition_valid=False,
            blocked=True,
            blocker_reason=state_msg,
            artifacts_created=artifacts,
        )

        if not dry_run:
            _write_json(
                control_dir / "human_preview_review_gate_proof.json", proof
            )

        return {
            "task_id": TASK_ID,
            "status": "error",
            "gate_blocked": True,
            "state_machine_error": state_msg,
            "operator_verdict_provided": True,
            "operator_verdict": verdict,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": default_state,
            "next_allowed_action": default_state,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 4: Validate state machine transition
    # ------------------------------------------------------------------
    from_state = default_state
    to_state = target_state

    # Self-loop (needs_manual_review): no state machine transition needed,
    # state stays the same. Skip transition validation.
    is_self_loop = (from_state == to_state)

    if is_self_loop:
        transition_valid = True
    else:
        transition_valid = CombineStateMachine.can_transition(from_state, to_state)

    if not transition_valid:
        # State machine says no — safety block
        target_state = default_state

        artifacts = ["human_preview_review_gate_proof.json"]

        proof = build_gate_proof(
            verdict_found=True,
            verdict=verdict,
            decision_valid=True,
            target_state=default_state,
            transition_valid=False,
            blocked=True,
            blocker_reason=(
                f"State machine forbids transition from '{from_state}' "
                f"to '{to_state}'. The state machine must be updated before "
                f"this transition can proceed."
            ),
            artifacts_created=artifacts,
        )

        if not dry_run:
            _write_json(
                control_dir / "human_preview_review_gate_proof.json", proof
            )

        return {
            "task_id": TASK_ID,
            "status": "error",
            "gate_blocked": True,
            "state_machine_error": (
                f"Forbidden transition: {from_state} -> {to_state}"
            ),
            "operator_verdict_provided": True,
            "operator_verdict": verdict,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": default_state,
            "next_allowed_action": default_state,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 5: Gate passed — create proof artifacts
    # ------------------------------------------------------------------
    artifacts = ["human_preview_review_gate_proof.json"]

    proof = build_gate_proof(
        verdict_found=True,
        verdict=verdict,
        decision_valid=True,
        target_state=target_state,
        transition_valid=True,
        blocked=False,
        blocker_reason=None,
        artifacts_created=artifacts,
    )

    if dry_run:
        return {
            "task_id": TASK_ID,
            "status": "ok",
            "gate_passed": True,
            "dry_run": True,
            "selected_branch": verdict,
            "operator_verdict": verdict,
            "operator_verdict_provided": True,
            "decision_valid": True,
            "state_machine_transition_valid": True,
            "from_state": from_state,
            "to_state": to_state,
            "current_state": target_state,
            "next_allowed_action": target_state,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "writes_blocked": True,
            "message": "Dry-run: gate would pass but no artifacts were written.",
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 6: Write artifacts
    # ------------------------------------------------------------------
    _write_json(control_dir / "human_preview_review_gate_proof.json", proof)

    # Update artifact index
    existing_index = _read_json(control_dir / "artifact_index.json") or {}
    index_update = build_artifact_index_update(
        target_state=target_state,
        verdict=verdict,
        blocked=False,
        artifacts=artifacts,
    )
    existing_index.update(index_update)
    _write_json(control_dir / "artifact_index.json", existing_index)

    # Update ledger
    ledger_path = control_dir / "episode_ledger.json"
    existing_ledger = _read_ledger(ledger_path)
    new_events = build_ledger_events(
        target_state=target_state,
        verdict=verdict,
        blocked=False,
        decision_valid=True,
        artifacts=artifacts,
    )
    existing_ledger.extend(new_events)
    _write_ledger(ledger_path, existing_ledger)

    # ------------------------------------------------------------------
    # Step 7: Return result
    # ------------------------------------------------------------------
    return {
        "task_id": TASK_ID,
        "status": "ok",
        "gate_passed": True,
        "selected_branch": verdict,
        "operator_verdict": verdict,
        "operator_verdict_provided": True,
        "decision_valid": True,
        "state_machine_transition_valid": True,
        "from_state": from_state,
        "to_state": to_state,
        "current_state": target_state,
        "next_allowed_action": target_state,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "artifacts": artifacts,
        "forbidden_actions": {
            "voice_generation": False,
            "assembly": False,
            "downstream": False,
            "production_accepted": False,
        },
        "timestamp": timestamp,
    }
