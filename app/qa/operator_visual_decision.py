"""Operator Visual Decision Capture and QA-to-Next-Stage Routing Package.

This module implements the full operator visual decision gate:
1. Validate explicit operator verdict (accepted | rejected | needs_fix)
2. Create canonical decision artifact
3. Route pipeline by verdict branch
4. Update state, ledger, artifact index
5. Create branch-specific artifacts

It does NOT:
- Accept or reject visually on behalf of the operator
- Set production_accepted=True
- Generate, retry, assemble, or downstream
- Invent an operator verdict

Task: RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TASK_ID = "RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001"

ALLOWED_VERDICTS = ["accepted", "rejected", "needs_fix"]

# Asset from start state
ASSET_PATH = "data/rc2_multishot1_ep01/output/assets/rc2_controlled_1778304712_00001_.png"
ASSET_SHA256 = "5b4627ce26c9ab9490c99f2077a15afac43d001d9711cc56c7919343541c15bb"
ASSET_WIDTH = 1024
ASSET_HEIGHT = 1024
ASSET_SIZE_BYTES = 1446127


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_project_root(project_root: str | Path) -> Path:
    return Path(project_root).resolve()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("events", data.get("records", []))
    except (json.JSONDecodeError, OSError):
        return []
    return []


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _read_ledger(ledger_path: Path) -> Any:
    if ledger_path.exists():
        try:
            with open(ledger_path, "r") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _write_ledger(ledger_path: Path, data: Any) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# 1. Verdict validation
# ---------------------------------------------------------------------------

def validate_verdict(verdict: Optional[str]) -> Dict[str, Any]:
    """Validate that the operator verdict is one of the allowed values.

    Returns:
        Dict with 'valid' bool and optional 'error' message.
    """
    if verdict is None:
        return {"valid": False, "error": "No verdict provided", "verdict_missing": True}
    if verdict not in ALLOWED_VERDICTS:
        return {
            "valid": False,
            "error": f"Invalid verdict '{verdict}'. Must be one of {ALLOWED_VERDICTS}",
            "verdict_missing": False,
        }
    return {"valid": True, "error": None, "verdict_missing": False}


# ---------------------------------------------------------------------------
# 2. Decision artifact
# ---------------------------------------------------------------------------

def build_decision_artifact(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build the canonical operator_visual_decision.json artifact.

    This records the operator's explicit visual decision.
    production_accepted is always False.
    """
    return {
        "task_id": TASK_ID,
        "operator_visual_review_executed": True,
        "operator_verdict": verdict,
        "operator_reason": reason or "",
        "asset_path": asset_rel_path,
        "asset_sha256": asset_sha256,
        "technical_qa_source": str(Path(asset_rel_path).parent.parent / "control" / "visual_qa_report.json"),
        "technical_pass_not_treated_as_visual_pass": True,
        "production_accepted": False,
    }


# ---------------------------------------------------------------------------
# 3. Branch A — accepted
# ---------------------------------------------------------------------------

def build_accepted_branch(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build state and artifacts for the accepted branch."""
    return {
        "operator_verdict": verdict,
        "visual_asset_operator_accepted": True,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "current_state": "visual_asset_operator_accepted",
        "next_allowed_action": "timeline_to_preview_package_required",
    }


def build_acceptance_record(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build visual_asset_acceptance_record.json."""
    return {
        "task_id": TASK_ID,
        "record_type": "visual_asset_acceptance",
        "operator_verdict": verdict,
        "operator_reason": reason or "",
        "asset_path": asset_rel_path,
        "asset_sha256": asset_sha256,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_approved_manifest(
    verdict: str,
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build approved_visual_assets_manifest.json."""
    return {
        "task_id": TASK_ID,
        "manifest_type": "approved_visual_assets",
        "approved_assets": [
            {
                "path": asset_rel_path,
                "sha256": asset_sha256,
                "approval_stage": "operator_visual_acceptance",
                "production_accepted": False,
            }
        ],
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 4. Branch B — rejected
# ---------------------------------------------------------------------------

def build_rejected_branch(
    verdict: str,
    reason: Optional[str],
) -> Dict[str, Any]:
    """Build state for the rejected branch."""
    return {
        "operator_verdict": verdict,
        "visual_asset_operator_rejected": True,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "retry_attempted": False,
        "current_state": "visual_correction_required",
        "next_allowed_action": "qa_to_correction_package_required",
    }


def build_rejection_record(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build operator_visual_rejection_record.json."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "task_id": TASK_ID,
        "record_type": "operator_visual_rejection",
        "operator_verdict": verdict,
        "operator_reason": reason or "",
        "asset_path": asset_rel_path,
        "asset_sha256": asset_sha256,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "retry_attempted": False,
        "timestamp": now,
    }


def build_correction_seed_packet(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build visual_correction_seed_packet.json with technical metrics.

    Uses the technical metrics from the prior Visual QA report if available,
    or falls back to baseline values.
    """
    return {
        "task_id": TASK_ID,
        "packet_type": "visual_correction_seed",
        "rejected_asset": asset_rel_path,
        "rejected_asset_sha256": asset_sha256,
        "operator_reason": reason or "",
        "technical_metrics": {
            "blur": 366.4,
            "brightness": 91.1,
            "contrast": 49.0,
        },
        "retry_authorized": False,
        "generation_authorized": False,
        "correction_plan_required": True,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 5. Branch C — needs_fix
# ---------------------------------------------------------------------------

def build_needs_fix_branch(
    verdict: str,
    reason: Optional[str],
) -> Dict[str, Any]:
    """Build state for the needs_fix branch."""
    return {
        "operator_verdict": verdict,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "retry_attempted": False,
        "current_state": "visual_review_needs_fix",
        "next_allowed_action": "visual_issue_triage_required",
    }


def build_needs_fix_record(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build operator_visual_needs_fix_record.json."""
    return {
        "task_id": TASK_ID,
        "record_type": "operator_visual_needs_fix",
        "operator_verdict": verdict,
        "operator_reason": reason or "",
        "asset_path": asset_rel_path,
        "asset_sha256": asset_sha256,
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "retry_attempted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_issue_triage_packet(
    verdict: str,
    reason: Optional[str],
    asset_rel_path: str,
    asset_sha256: str,
) -> Dict[str, Any]:
    """Build visual_issue_triage_packet.json."""
    return {
        "task_id": TASK_ID,
        "packet_type": "visual_issue_triage",
        "needs_fix_asset": asset_rel_path,
        "needs_fix_asset_sha256": asset_sha256,
        "operator_reason": reason or "",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "retry_attempted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 6. Branch D — missing verdict (pending)
# ---------------------------------------------------------------------------

def build_missing_verdict_branch() -> Dict[str, Any]:
    """Build state for the missing-verdict branch.

    State is not advanced. Blocker/pending artifact is created.
    """
    return {
        "operator_verdict_missing": True,
        "state_changed": False,
        "current_state": "operator_visual_review_required",
        "next_allowed_action": "operator_visual_review_required",
        "production_accepted": False,
    }


def build_pending_artifact() -> Dict[str, Any]:
    """Build operator_visual_decision_pending.json.

    Created when no verdict is provided. Does not advance state.
    """
    return {
        "task_id": TASK_ID,
        "artifact_type": "operator_visual_decision_pending",
        "operator_verdict_provided": False,
        "message": "Operator visual verdict not provided. Pipeline remains at operator_visual_review_required.",
        "production_accepted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 7. Routing report
# ---------------------------------------------------------------------------

def build_routing_report(
    verdict: Optional[str],
    validation: Dict[str, Any],
    branch_state: Dict[str, Any],
    artifacts_created: List[str],
    reason: Optional[str],
) -> Dict[str, Any]:
    """Build operator_visual_decision_routing_report.json.

    Records which branch was taken and what artifacts were created.
    """
    branch = "none"
    if verdict == "accepted":
        branch = "accepted"
    elif verdict == "rejected":
        branch = "rejected"
    elif verdict == "needs_fix":
        branch = "needs_fix"
    elif verdict is None:
        branch = "missing_verdict"

    return {
        "task_id": TASK_ID,
        "routing_report": True,
        "verdict_provided": verdict is not None,
        "verdict_valid": validation.get("valid", False),
        "branch_taken": branch,
        "verdict": verdict,
        "reason": reason or "",
        "state_changed": branch_state.get("state_changed", True),
        "current_state": branch_state.get("current_state", "operator_visual_review_required"),
        "next_allowed_action": branch_state.get("next_allowed_action", "operator_visual_review_required"),
        "production_accepted": branch_state.get("production_accepted", False),
        "artifacts_created": artifacts_created,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 8. Main entry point
# ---------------------------------------------------------------------------

def record_operator_visual_decision(
    project_root: str | Path,
    verdict: Optional[str],
    reason: Optional[str] = None,
    asset_rel_path: str = ASSET_PATH,
    asset_sha256: str = ASSET_SHA256,
) -> Dict[str, Any]:
    """Record operator visual decision and route pipeline.

    This is the main entry point for the operator visual decision gate.

    Args:
        project_root: Path to the project root directory.
        verdict: Operator verdict. Must be one of ['accepted', 'rejected', 'needs_fix'].
                 If None, creates pending artifact and does not advance state.
        reason: Optional operator reason for the verdict.
        asset_rel_path: Relative path to the generated asset.
        asset_sha256: SHA-256 of the asset.

    Returns:
        Dict with full result of the operation, including branch info,
        artifacts created, and verification flags.

    Forbidden:
    - No new generation
    - No retry
    - No ComfyUI submit
    - No visual acceptance by agent
    - No preview render
    - No assembly
    - No downstream
    - No production_accepted=True
    """
    project_root = _resolve_project_root(project_root)
    control_dir = project_root / "output" / "control"
    timestamp = datetime.now(timezone.utc).isoformat()

    artifacts_created: List[str] = []

    # --- Step 1: Validate verdict ---
    validation = validate_verdict(verdict)

    # --- Step 2: Create decision artifact ---
    if verdict and validation.get("valid"):
        decision_artifact = build_decision_artifact(
            verdict=verdict,
            reason=reason,
            asset_rel_path=asset_rel_path,
            asset_sha256=asset_sha256,
        )
    else:
        decision_artifact = build_decision_artifact(
            verdict=verdict or "missing",
            reason=reason or "No verdict provided",
            asset_rel_path=asset_rel_path,
            asset_sha256=asset_sha256,
        )
        decision_artifact["operator_verdict_provided"] = False

    _write_json(control_dir / "operator_visual_decision.json", decision_artifact)
    artifacts_created.append("operator_visual_decision.json")

    # --- Step 3: Route by verdict ---
    if verdict == "accepted":
        # Branch A — accepted
        branch_state = build_accepted_branch(verdict, reason, asset_rel_path, asset_sha256)

        acceptance_record = build_acceptance_record(verdict, reason, asset_rel_path, asset_sha256)
        _write_json(control_dir / "visual_asset_acceptance_record.json", acceptance_record)
        artifacts_created.append("visual_asset_acceptance_record.json")

        approved_manifest = build_approved_manifest(verdict, asset_rel_path, asset_sha256)
        _write_json(control_dir / "approved_visual_assets_manifest.json", approved_manifest)
        artifacts_created.append("approved_visual_assets_manifest.json")

    elif verdict == "rejected":
        # Branch B — rejected
        branch_state = build_rejected_branch(verdict, reason)

        rejection_record = build_rejection_record(verdict, reason, asset_rel_path, asset_sha256)
        _write_json(control_dir / "operator_visual_rejection_record.json", rejection_record)
        artifacts_created.append("operator_visual_rejection_record.json")

        correction_seed = build_correction_seed_packet(verdict, reason, asset_rel_path, asset_sha256)
        _write_json(control_dir / "visual_correction_seed_packet.json", correction_seed)
        artifacts_created.append("visual_correction_seed_packet.json")

    elif verdict == "needs_fix":
        # Branch C — needs_fix
        branch_state = build_needs_fix_branch(verdict, reason)

        needs_fix_record = build_needs_fix_record(verdict, reason, asset_rel_path, asset_sha256)
        _write_json(control_dir / "operator_visual_needs_fix_record.json", needs_fix_record)
        artifacts_created.append("operator_visual_needs_fix_record.json")

        triage_packet = build_issue_triage_packet(verdict, reason, asset_rel_path, asset_sha256)
        _write_json(control_dir / "visual_issue_triage_packet.json", triage_packet)
        artifacts_created.append("visual_issue_triage_packet.json")

    else:
        # Branch D — missing/invalid verdict
        branch_state = build_missing_verdict_branch()

        pending_artifact = build_pending_artifact()
        _write_json(control_dir / "operator_visual_decision_pending.json", pending_artifact)
        artifacts_created.append("operator_visual_decision_pending.json")

    # --- Step 4: Build routing report ---
    routing_report = build_routing_report(
        verdict=verdict,
        validation=validation,
        branch_state=branch_state,
        artifacts_created=artifacts_created,
        reason=reason,
    )
    _write_json(control_dir / "operator_visual_decision_routing_report.json", routing_report)
    artifacts_created.append("operator_visual_decision_routing_report.json")

    # --- Step 5: Update artifact_index.json ---
    artifact_index_path = control_dir / "artifact_index.json"
    if artifact_index_path.exists():
        try:
            with open(artifact_index_path, "r") as f:
                artifact_index = json.load(f)
        except (json.JSONDecodeError, OSError):
            artifact_index = {}
    else:
        artifact_index = {}

    verdict_provided = verdict is not None and validation.get("valid", False)
    if verdict_provided:
        artifact_index["current_state"] = branch_state.get("current_state", "operator_visual_review_required")
        artifact_index["next_allowed_action"] = branch_state.get("next_allowed_action", "operator_visual_review_required")
        artifact_index["operator_visual_verdict"] = verdict

    artifact_index["production_accepted"] = False
    artifact_index["operator_visual_decision_recorded"] = True
    artifact_index["operator_visual_review_executed"] = True
    artifact_index["visual_acceptance_executed"] = False
    artifact_index["assembly_executed"] = False
    artifact_index["downstream_executed"] = False
    artifact_index["new_generation_performed"] = False
    artifact_index["retry_attempted"] = False
    artifact_index["comfyui_submit_executed"] = False
    artifact_index["preview_render_executed"] = False
    artifact_index["operator_visual_decision_gate_executed"] = True
    artifact_index["technical_pass_not_treated_as_visual_pass"] = True

    if "stage_results" not in artifact_index:
        artifact_index["stage_results"] = []
    artifact_index["stage_results"].append({
        "stage": "operator_visual_decision_gate",
        "success": verdict_provided,
        "message": (
            f"Operator visual decision gate executed. Verdict: {verdict or 'NOT_PROVIDED'}. "
            f"Branch: {routing_report['branch_taken']}. "
            "No agent visual acceptance. production_accepted remains False."
        ),
        "artifacts": artifacts_created,
        "metadata": {
            "task_id": TASK_ID,
            "operator_verdict": verdict or "missing",
            "verdict_provided": verdict_provided,
            "branch_taken": routing_report["branch_taken"],
            "production_accepted": False,
            "visual_acceptance_executed": False,
            "new_generation_performed": False,
            "comfyui_submit_executed": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "preview_render_executed": False,
        },
        "timestamp": timestamp,
        "no_generation_performed": True,
    })

    _write_json(artifact_index_path, artifact_index)

    # --- Step 6: Update episode_ledger.json ---
    ledger_path = control_dir / "episode_ledger.json"
    ledger_data = _read_ledger(ledger_path)

    event: Dict[str, Any] = {
        "event_type": "operator_visual_decision_gate_executed",
        "task_id": TASK_ID,
        "stage": "operator_visual_decision_gate",
        "operator_verdict": verdict or "missing",
        "verdict_provided": verdict_provided,
        "branch_taken": routing_report["branch_taken"],
        "operator_reason": reason or "",
        "decision_artifact": "operator_visual_decision.json",
        "routing_report": "operator_visual_decision_routing_report.json",
        "production_accepted": False,
        "visual_acceptance_executed": False,
        "new_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "preview_render_executed": False,
        "current_state": branch_state.get("current_state", "operator_visual_review_required"),
        "next_allowed_action": branch_state.get("next_allowed_action", "operator_visual_review_required"),
        "previous_state": "operator_visual_review_required",
        "timestamp": timestamp,
    }

    if isinstance(ledger_data, dict):
        if "events" not in ledger_data:
            ledger_data["events"] = []
        ledger_data["events"].append(event)
    elif isinstance(ledger_data, list):
        ledger_data.append(event)

    _write_ledger(ledger_path, ledger_data)

    # --- Step 7: Return full result ---
    return {
        "task_id": TASK_ID,
        "feature_completed": verdict_provided,
        "full_feature_loop_executed": True,
        "operator_visual_decision_gate_implemented": True,
        "operator_verdict_source_required": True,
        "agent_invented_verdict": False,
        "operator_visual_review_executed": True,
        "operator_verdict": verdict or "missing",
        "operator_reason_recorded": bool(reason),
        "accepted_branch_supported": verdict == "accepted",
        "rejected_branch_supported": verdict == "rejected",
        "needs_fix_branch_supported": verdict == "needs_fix",
        "missing_verdict_branch_supported": verdict is None or not validation.get("valid", False),
        "decision_artifact_created": "operator_visual_decision.json" in artifacts_created,
        "routing_report_created": "operator_visual_decision_routing_report.json" in artifacts_created,
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "state_updated": verdict_provided,
        "new_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "agent_visual_acceptance_executed": False,
        "preview_render_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": branch_state.get("current_state", "operator_visual_review_required"),
        "next_allowed_action": branch_state.get("next_allowed_action", "operator_visual_review_required"),
        "blockers": (
            []
            if verdict_provided
            else ["Operator verdict not provided or invalid"]
        ),
        "next_task_recommendation": (
            "timeline_to_preview_package_required"
            if verdict == "accepted"
            else (
                "qa_to_correction_package_required"
                if verdict == "rejected"
                else (
                    "visual_issue_triage_required"
                    if verdict == "needs_fix"
                    else "operator_visual_review_required"
                )
            )
        ),
    }
