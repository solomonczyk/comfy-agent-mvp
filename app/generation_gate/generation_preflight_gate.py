"""
Generation Gate Preflight — evaluate, build, and validate generation gate artifacts.

RC-COMBINE-V2-86001-94000:
  Gate evaluates Workflow-to-Assets artifacts and produces one of:
  - READY path: all assets verified, create authorization contracts
  - BLOCKED path: assets missing, create blocker/acquisition package
  - INVALID path: workflow contract or asset report inconsistencies
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_ID = "RC-COMBINE-V2-86001-94000"
PREVIOUS_LAYER = "RC-COMBINE-V2-70001-86000 Workflow-to-Assets Package"
NEXT_LAYER = "generation_operator_authorization_required"


# ---------------------------------------------------------------------------
# Artifact paths (relative to output/control)
# ---------------------------------------------------------------------------

WORKFLOW_ASSETS_DIR = "workflow_assets"

ARTIFACT_PATHS = {
    "submitted_workflow_contract": f"{WORKFLOW_ASSETS_DIR}/submitted_workflow_contract.json",
    "workflow_validation_report": f"{WORKFLOW_ASSETS_DIR}/workflow_validation_report.json",
    "asset_requirements": f"{WORKFLOW_ASSETS_DIR}/asset_requirements.json",
    "asset_resolution_plan": f"{WORKFLOW_ASSETS_DIR}/asset_resolution_plan.json",
    "asset_verification_report": f"{WORKFLOW_ASSETS_DIR}/asset_verification_report.json",
    "asset_blocker_report": f"{WORKFLOW_ASSETS_DIR}/asset_blocker_report.json",
    "generation_preflight_operator_review_packet": f"{WORKFLOW_ASSETS_DIR}/generation_preflight_operator_review_packet.json",
}

GATE_ARTIFACTS = {
    "generation_gate_decision": "generation_gate_decision.json",
    "generation_authorization_contract": "generation_authorization_contract.json",
    "generation_execution_contract": "generation_execution_contract.json",
    "prompt_id_report_contract": "prompt_id_report_contract.json",
    "native_output_report_contract": "native_output_report_contract.json",
    "canonical_outputs_manifest_contract": "canonical_outputs_manifest_contract.json",
    "visual_qa_input_packet_contract": "visual_qa_input_packet_contract.json",
    "generation_runtime_blocker_report": "generation_runtime_blocker_report.json",
    "controlled_asset_acquisition_gate_packet": "controlled_asset_acquisition_gate_packet.json",
    "generation_blocked_operator_review_packet": "generation_blocked_operator_review_packet.json",
}

BLOCKED_STATE = "controlled_asset_acquisition_required"
READY_STATE = "generation_operator_authorization_required"
BLOCKED_STATE_GENERAL = "generation_gate_blocked"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_control_dir(project_root: str) -> Path:
    return Path(project_root) / "output" / "control"


def _get_workflow_assets_dir(control_dir: Path) -> Path:
    return control_dir / WORKFLOW_ASSETS_DIR


# ---------------------------------------------------------------------------
# Gate decision structure
# ---------------------------------------------------------------------------

GATE_DECISION_SCHEMA = {
    "generation_gate_decision": "blocked_by_missing_assets",
    "generation_can_be_authorized": False,
    "generation_can_execute_now": False,
    "comfyui_submit_allowed": False,
    "reason": "...",
    "blockers": [],
}


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_generation_gate(project_root: str) -> Dict[str, Any]:
    """Evaluate whether generation can proceed based on Workflow-to-Assets artifacts.

    Returns a canonical gate decision dict. Does NOT write any artifacts.
    """
    control_dir = _get_control_dir(project_root)
    wf_assets_dir = _get_workflow_assets_dir(control_dir)

    # --- Load all artifacts ---
    submitted_workflow_contract = _load_json(
        control_dir / ARTIFACT_PATHS["submitted_workflow_contract"]
    )
    workflow_validation_report = _load_json(
        control_dir / ARTIFACT_PATHS["workflow_validation_report"]
    )
    asset_requirements = _load_json(
        control_dir / ARTIFACT_PATHS["asset_requirements"]
    )
    asset_resolution_plan = _load_json(
        control_dir / ARTIFACT_PATHS["asset_resolution_plan"]
    )
    asset_verification_report = _load_json(
        control_dir / ARTIFACT_PATHS["asset_verification_report"]
    )
    asset_blocker_report = _load_json(
        control_dir / ARTIFACT_PATHS["asset_blocker_report"]
    )
    preflight_packet = _load_json(
        control_dir / ARTIFACT_PATHS["generation_preflight_operator_review_packet"]
    )

    timestamp = _utcnow()
    blockers: List[Dict[str, Any]] = []
    reason_parts: List[str] = []
    decision = "blocked_by_missing_assets"

    # --- 1. Validate workflow contract ---
    contract_valid = True
    if submitted_workflow_contract is None:
        contract_valid = False
        blockers.append({
            "type": "missing_workflow_contract",
            "detail": "submitted_workflow_contract.json not found",
        })
        reason_parts.append("Workflow contract missing")
    else:
        # Check for real execution proof — contract must NOT claim
        prompt_id = submitted_workflow_contract.get("prompt_id")
        generated_assets = submitted_workflow_contract.get("generated_assets")
        workflow_execution = submitted_workflow_contract.get("workflow_execution_performed", False)
        comfyui_submit = submitted_workflow_contract.get("comfyui_submit_executed", False)

        if prompt_id is not None:
            contract_valid = False
            blockers.append({
                "type": "invalid_workflow_contract",
                "detail": "Contract declares a prompt_id — this is execution proof, not a contract",
            })
            reason_parts.append("Workflow contract contains prompt_id (execution proof)")
        if generated_assets:
            contract_valid = False
            blockers.append({
                "type": "invalid_workflow_contract",
                "detail": "Contract lists generated assets — this is execution output, not a contract",
            })
            reason_parts.append("Workflow contract lists generated assets")
        if workflow_execution:
            contract_valid = False
            blockers.append({
                "type": "invalid_workflow_contract",
                "detail": "Contract claims workflow_execution_performed=true",
            })
            reason_parts.append("Workflow contract claims execution performed")
        if comfyui_submit:
            contract_valid = False
            blockers.append({
                "type": "invalid_workflow_contract",
                "detail": "Contract claims comfyui_submit_executed=true",
            })
            reason_parts.append("Workflow contract claims ComfyUI submit")

        # Validate shot IDs are present
        per_shot = submitted_workflow_contract.get("per_shot_workflow_contracts", [])
        if not per_shot:
            contract_valid = False
            blockers.append({
                "type": "invalid_workflow_contract",
                "detail": "No per_shot_workflow_contracts found",
            })
            reason_parts.append("No shot contracts in workflow contract")

    # --- 2. Validate workflow validation report ---
    report_valid = True
    if workflow_validation_report is None:
        report_valid = False
        blockers.append({
            "type": "missing_workflow_validation_report",
            "detail": "workflow_validation_report.json not found",
        })
        reason_parts.append("Workflow validation report missing")
    else:
        # Check KSampler and SaveImage requirements
        if not workflow_validation_report.get("ksampler_required", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "KSampler requirement not confirmed",
            })
            reason_parts.append("KSampler requirement not confirmed")
            report_valid = False
        if not workflow_validation_report.get("saveimage_required", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "SaveImage requirement not confirmed",
            })
            reason_parts.append("SaveImage requirement not confirmed")
            report_valid = False
        if not workflow_validation_report.get("filename_prefix_policy_defined", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "filename_prefix policy not defined",
            })
            reason_parts.append("filename_prefix policy not defined")
            report_valid = False
        if not workflow_validation_report.get("legacy_512_workflow_blocked", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "Legacy 512 workflow not blocked",
            })
            reason_parts.append("Legacy 512 workflow not blocked")
            report_valid = False
        if not workflow_validation_report.get("stub_workflow_blocked", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "Stub workflow not blocked",
            })
            reason_parts.append("Stub workflow not blocked")
            report_valid = False

        # Check for execution claims
        if workflow_validation_report.get("workflow_execution_performed", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "Validation report claims workflow_execution_performed=true",
            })
            reason_parts.append("Validation report claims execution performed")
            report_valid = False
        if workflow_validation_report.get("comfyui_submit_executed", False):
            blockers.append({
                "type": "invalid_workflow_validation",
                "detail": "Validation report claims comfyui_submit_executed=true",
            })
            reason_parts.append("Validation report claims ComfyUI submit")
            report_valid = False

    # --- 3. Validate asset readiness ---
    asset_verification_valid = True
    if asset_verification_report is None:
        asset_verification_valid = False
        blockers.append({
            "type": "missing_asset_verification_report",
            "detail": "asset_verification_report.json not found",
        })
        reason_parts.append("Asset verification report missing")
    else:
        required_available = asset_verification_report.get("required_assets_available", False)
        required_blocked = asset_verification_report.get("required_assets_blocked", False)
        missing_assets = asset_verification_report.get("errors", [])

        if not required_available:
            asset_verification_valid = False
            if missing_assets:
                blockers.append({
                    "type": "missing_required_assets",
                    "detail": f"Required assets missing: {missing_assets}",
                })
                reason_parts.append(f"Required assets not available: {missing_assets}")

        # Check for consistency with asset_blocker_report
        if asset_blocker_report is not None:
            blocker_active = True
            blocker_asset = asset_blocker_report.get("missing_or_invalid_asset", "unknown")
            preflight_allowed = asset_blocker_report.get("generation_preflight_allowed", True)

            if not preflight_allowed:
                blockers.append({
                    "type": "active_asset_blocker",
                    "detail": f"Asset blocker active for: {blocker_asset}. "
                              f"Generation preflight not allowed.",
                    "blocker_id": asset_blocker_report.get("blocker_id", "unknown"),
                    "missing_asset": blocker_asset,
                })
                reason_parts.append(f"Active asset blocker: {blocker_asset}")

        # Contradiction check: blocker says blocked but verification says ready
        if asset_blocker_report is not None and required_available:
            blocker_active = not asset_blocker_report.get("generation_preflight_allowed", True)
            if blocker_active and required_available:
                blockers.append({
                    "type": "inconsistent_state",
                    "detail": "asset_blocker_report is active but "
                              "asset_verification_report claims assets available",
                })
                reason_parts.append("Contradiction: blocker active but verification says ready")

    # --- 4. Validate preflight packet ---
    if preflight_packet is not None:
        has_asset_blocker = preflight_packet.get("has_asset_blocker", False)
        preflight_ready = preflight_packet.get("generation_preflight_ready", True)

        # Contradiction check: preflight packet says no-blocker but we found one
        if asset_blocker_report is not None and not has_asset_blocker:
            blockers.append({
                "type": "inconsistent_state",
                "detail": "Preflight packet says no asset blocker but asset_blocker_report exists",
            })
            reason_parts.append("Preflight packet contradicts asset_blocker_report")

    # --- 5. Determine final decision ---
    if not contract_valid:
        decision = "invalid_workflow_contract"
    elif not report_valid:
        decision = "invalid_workflow_contract"
    elif not asset_verification_valid:
        # Check if the blocker is the asset_blocker
        has_asset_blocker = asset_blocker_report is not None and \
            not asset_blocker_report.get("generation_preflight_allowed", True)
        if has_asset_blocker:
            decision = "blocked_by_missing_assets"
        else:
            # Check if there are any inconsistency blockers
            has_inconsistency = any(b["type"] == "inconsistent_state" for b in blockers)
            if has_inconsistency:
                decision = "inconsistent_state"
            else:
                decision = "invalid_asset_report"
    else:
        # All checks passed — check for active asset blockers
        if asset_blocker_report is not None and \
                not asset_blocker_report.get("generation_preflight_allowed", True):
            decision = "blocked_by_missing_assets"
        else:
            decision = "ready_for_operator_authorization"

    # Check for inconsistency blockers that override other classifications
    has_inconsistency = any(b["type"] == "inconsistent_state" for b in blockers)
    if has_inconsistency:
        decision = "inconsistent_state"

    generation_can_be_authorized = (decision == "ready_for_operator_authorization")

    if not reason_parts:
        reason_parts.append("All prerequisites verified ready")

    return {
        "task_id": TASK_ID,
        "generation_gate_decision": decision,
        "generation_can_be_authorized": generation_can_be_authorized,
        "generation_can_execute_now": False,
        "comfyui_submit_allowed": False,
        "reason": "; ".join(reason_parts),
        "blockers": blockers,
        "contract_valid": contract_valid,
        "report_valid": report_valid,
        "asset_verification_valid": asset_verification_valid,
        "asset_blocker_active": asset_blocker_report is not None and
                                not asset_blocker_report.get("generation_preflight_allowed", True),
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# Build generation gate package
# ---------------------------------------------------------------------------

def build_generation_gate_package(project_root: str) -> Dict[str, Any]:
    """Evaluate generation readiness and build the appropriate gate package.

    Returns a dict describing what was created. Does NOT perform generation.
    """
    control_dir = _get_control_dir(project_root)
    gate_decision = evaluate_generation_gate(project_root)

    gate_decision_path = control_dir / GATE_ARTIFACTS["generation_gate_decision"]
    _write_json(gate_decision_path, gate_decision)

    decision = gate_decision["generation_gate_decision"]
    asset_blocker_active = gate_decision.get("asset_blocker_active", False)
    timestamp = _utcnow()

    # Track what was created
    created: Dict[str, bool] = {}
    for key in GATE_ARTIFACTS:
        created[key] = False

    created["generation_gate_decision"] = True

    # Shared forbidden state flags
    forbidden = {
        "generation_authorized": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "workflow_execution_performed": False,
        "retry_attempted": False,
        "visual_qa_executed": False,
        "visual_acceptance_executed": False,
        "preview_render_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
    }

    if decision == "ready_for_operator_authorization":
        # --- READY PATH ---
        current_state = READY_STATE
        next_allowed_action = READY_STATE

        auth_contract = {
            "task_id": TASK_ID,
            "authorization_type": "generation_operator_authorization",
            "generation_authorized": False,
            "comfyui_submit_allowed": False,
            "preflight_validated": True,
            "asset_readiness_verified": True,
            "gate_decision": gate_decision["generation_gate_decision"],
            "max_generations_per_gate": 1,
            "forbidden_fake_prompt_id": True,
            "forbidden_fake_asset": True,
            "operator_authorization_required": True,
            "authorization_contract_ready": True,
            "timestamp": timestamp,
        }
        exec_contract = {
            "task_id": TASK_ID,
            "contract_type": "generation_execution_contract",
            "execution_not_authorized_yet": True,
            "operator_gate_required": True,
            "comfyui_submit_forbidden_until_authorized": True,
            "max_generations": 1,
            "timestamp": timestamp,
        }
        prompt_id_contract = {
            "task_id": TASK_ID,
            "contract_type": "prompt_id_report_contract",
            "prompt_id": None,
            "why_no_prompt_id": "Generation not yet performed — awaiting operator authorization",
            "timestamp": timestamp,
        }
        output_report_contract = {
            "task_id": TASK_ID,
            "contract_type": "native_output_report_contract",
            "native_outputs": [],
            "why_no_outputs": "Generation not yet performed — awaiting operator authorization",
            "timestamp": timestamp,
        }
        canonical_manifest_contract = {
            "task_id": TASK_ID,
            "contract_type": "canonical_outputs_manifest_contract",
            "canonical_outputs": [],
            "why_no_outputs": "Generation not yet performed — awaiting operator authorization",
            "timestamp": timestamp,
        }
        visual_qa_contract = {
            "task_id": TASK_ID,
            "contract_type": "visual_qa_input_packet_contract",
            "visual_qa_inputs": [],
            "why_no_inputs": "Generation not yet performed — awaiting operator authorization",
            "timestamp": timestamp,
        }

        _write_json(control_dir / GATE_ARTIFACTS["generation_authorization_contract"], auth_contract)
        _write_json(control_dir / GATE_ARTIFACTS["generation_execution_contract"], exec_contract)
        _write_json(control_dir / GATE_ARTIFACTS["prompt_id_report_contract"], prompt_id_contract)
        _write_json(control_dir / GATE_ARTIFACTS["native_output_report_contract"], output_report_contract)
        _write_json(control_dir / GATE_ARTIFACTS["canonical_outputs_manifest_contract"], canonical_manifest_contract)
        _write_json(control_dir / GATE_ARTIFACTS["visual_qa_input_packet_contract"], visual_qa_contract)

        for key in ["generation_authorization_contract", "generation_execution_contract",
                     "prompt_id_report_contract", "native_output_report_contract",
                     "canonical_outputs_manifest_contract", "visual_qa_input_packet_contract"]:
            created[key] = True

    elif decision in ("blocked_by_missing_assets", "invalid_workflow_contract",
                      "invalid_asset_report", "inconsistent_state"):
        # --- BLOCKED / INVALID PATH ---
        if decision == "blocked_by_missing_assets":
            current_state = BLOCKED_STATE
            next_allowed_action = BLOCKED_STATE
        else:
            current_state = BLOCKED_STATE_GENERAL
            next_allowed_action = BLOCKED_STATE_GENERAL

        # Determine which asset is missing
        missing_asset = "unknown"
        for b in gate_decision.get("blockers", []):
            if b["type"] in ("missing_required_assets", "active_asset_blocker"):
                missing_asset = b.get("missing_asset", b.get("detail", "unknown"))
                break
        if missing_asset == "unknown":
            # Try asset resolution plan
            resolution_plan = _load_json(
                control_dir / ARTIFACT_PATHS["asset_resolution_plan"]
            )
            if resolution_plan and resolution_plan.get("missing_assets"):
                missing_asset = resolution_plan["missing_assets"][0]

        runtime_blocker = {
            "task_id": TASK_ID,
            "blocker_type": "generation_runtime_blocker",
            "decision": decision,
            "missing_asset": missing_asset,
            "expected_asset_type": "checkpoint",
            "source_artifact": "asset_blocker_report.json / asset_verification_report.json",
            "why_generation_forbidden": gate_decision.get("reason", "Missing required assets"),
            "next_safe_action": f"Resolve missing asset '{missing_asset}' "
                               f"via controlled acquisition gate",
            "fake_availability_forbidden": True,
            "runtime_execution_forbidden": True,
            "generation_authorization_forbidden": True,
            "timestamp": timestamp,
        }

        acquisition_gate_packet = {
            "task_id": TASK_ID,
            "packet_type": "controlled_asset_acquisition_gate",
            "decision": decision,
            "missing_asset": missing_asset,
            "acquisition_instructions_path": (
                "output/control/MODEL_ASSET_INSTALL_INSTRUCTIONS.md"
            ),
            "trusted_sources": [
                "huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
            ],
            "manual_gate_required": True,
            "generation_forbidden_until_resolved": True,
            "operator_action_required": "Download and install missing checkpoint, "
                                         "then re-run generation gate evaluation",
            "timestamp": timestamp,
        }

        blocked_review_packet = {
            "task_id": TASK_ID,
            "packet_type": "generation_blocked_operator_review",
            "decision": decision,
            "gate_decision": gate_decision["generation_gate_decision"],
            "reason": gate_decision.get("reason", ""),
            "blockers": gate_decision.get("blockers", []),
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "generation_authorized": False,
            "generation_performed": False,
            "comfyui_submit_executed": False,
            "workflow_execution_performed": False,
            "retry_attempted": False,
            "visual_qa_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "operator_review_required": True,
            "timestamp": timestamp,
        }

        _write_json(
            control_dir / GATE_ARTIFACTS["generation_runtime_blocker_report"],
            runtime_blocker,
        )
        _write_json(
            control_dir / GATE_ARTIFACTS["controlled_asset_acquisition_gate_packet"],
            acquisition_gate_packet,
        )
        _write_json(
            control_dir / GATE_ARTIFACTS["generation_blocked_operator_review_packet"],
            blocked_review_packet,
        )

        created["generation_runtime_blocker_report"] = True
        created["controlled_asset_acquisition_gate_packet"] = True
        created["generation_blocked_operator_review_packet"] = True

    else:
        # Fallback — should not happen
        current_state = BLOCKED_STATE_GENERAL
        next_allowed_action = BLOCKED_STATE_GENERAL

    result = {
        "task_id": TASK_ID,
        "selected_branch": decision,
        "ready_branch_reached": decision == "ready_for_operator_authorization",
        "blocked_branch_reached": decision in (
            "blocked_by_missing_assets", "invalid_workflow_contract",
            "invalid_asset_report", "inconsistent_state",
        ),
        "invalid_branch_reached": decision in (
            "invalid_workflow_contract", "invalid_asset_report", "inconsistent_state",
        ),
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        **forbidden,
        **created,
        "timestamp": timestamp,
    }
    result["generation_gate_decision_path"] = str(gate_decision_path)

    # Update artifact index and episode ledger
    _update_artifact_index(project_root, result)
    _update_episode_ledger(project_root, result)

    return result


# ---------------------------------------------------------------------------
# Validate generation gate package
# ---------------------------------------------------------------------------

def validate_generation_gate_package(project_root: str) -> Dict[str, Any]:
    """Validate the existing generation gate package artifacts.

    Reads all artifacts and checks internal consistency.
    """
    control_dir = _get_control_dir(project_root)

    # Re-evaluate and compare
    gate_decision = evaluate_generation_gate(project_root)

    # Check that gate decision artifact exists
    gate_decision_path = control_dir / GATE_ARTIFACTS["generation_gate_decision"]
    if not gate_decision_path.exists():
        return {
            "task_id": TASK_ID,
            "validation_passed": False,
            "errors": ["generation_gate_decision.json not found"],
            "gate_decision": None,
        }

    saved_decision = _load_json(gate_decision_path)
    if saved_decision is None:
        return {
            "task_id": TASK_ID,
            "validation_passed": False,
            "errors": ["generation_gate_decision.json is invalid JSON"],
            "gate_decision": None,
        }

    errors = []
    warnings = []

    # Check that saved and current evaluation match
    if saved_decision.get("generation_gate_decision") != gate_decision.get("generation_gate_decision"):
        warnings.append(
            f"Saved decision '{saved_decision.get('generation_gate_decision')}' "
            f"differs from current evaluation '{gate_decision.get('generation_gate_decision')}'"
        )

    decision = saved_decision.get("generation_gate_decision", "")
    asset_blocker_active = saved_decision.get("asset_blocker_active", False)

    # Validate artifact presence based on decision
    if decision == "ready_for_operator_authorization":
        expected = [
            "generation_authorization_contract.json",
            "generation_execution_contract.json",
            "prompt_id_report_contract.json",
            "native_output_report_contract.json",
            "canonical_outputs_manifest_contract.json",
            "visual_qa_input_packet_contract.json",
        ]
        for name in expected:
            path = control_dir / name
            if not path.exists():
                errors.append(f"READY path artifact missing: {name}")
            else:
                data = _load_json(path)
                if data is None:
                    errors.append(f"READY path artifact invalid: {name}")

        # Forbidden checks for READY path
        if saved_decision.get("generation_authorized", False):
            errors.append("READY path must not set generation_authorized=true")
        if saved_decision.get("generation_performed", False):
            errors.append("READY path must not set generation_performed=true")
        if saved_decision.get("comfyui_submit_executed", False):
            errors.append("READY path must not set comfyui_submit_executed=true")

    elif decision in ("blocked_by_missing_assets",):
        expected = [
            "generation_runtime_blocker_report.json",
            "controlled_asset_acquisition_gate_packet.json",
            "generation_blocked_operator_review_packet.json",
        ]
        for name in expected:
            path = control_dir / name
            if not path.exists():
                errors.append(f"BLOCKED path artifact missing: {name}")
            else:
                data = _load_json(path)
                if data is None:
                    errors.append(f"BLOCKED path artifact invalid: {name}")

        # Verify that READY path artifacts do NOT exist
        ready_artifacts = [
            "generation_authorization_contract.json",
            "generation_execution_contract.json",
        ]
        for name in ready_artifacts:
            path = control_dir / name
            if path.exists():
                warnings.append(
                    f"BLOCKED path should not contain READY artifact: {name}"
                )

        # Check blocker report contents
        blocker_report = _load_json(
            control_dir / GATE_ARTIFACTS["generation_runtime_blocker_report"]
        )
        if blocker_report:
            if blocker_report.get("fake_availability_forbidden") is not True:
                errors.append("Blocker report must forbid fake availability")
            if blocker_report.get("runtime_execution_forbidden") is not True:
                errors.append("Blocker report must forbid runtime execution")

        # Forbidden checks for BLOCKED path
        if saved_decision.get("generation_authorized", False):
            errors.append("BLOCKED path must not set generation_authorized=true")
        if saved_decision.get("generation_performed", False):
            errors.append("BLOCKED path must not set generation_performed=true")

    elif decision in ("invalid_workflow_contract", "invalid_asset_report", "inconsistent_state"):
        expected = [
            "generation_runtime_blocker_report.json",
            "controlled_asset_acquisition_gate_packet.json",
            "generation_blocked_operator_review_packet.json",
        ]
        for name in expected:
            path = control_dir / name
            if not path.exists():
                errors.append(f"INVALID path artifact missing: {name}")

    # Contradiction checks
    _run_contradiction_checks(saved_decision, errors)

    return {
        "task_id": TASK_ID,
        "validation_passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "gate_decision": saved_decision,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "production_accepted": False,
    }


def _run_contradiction_checks(
    decision: Dict[str, Any], errors: List[str]
) -> None:
    """Run consistency checks on the decision dict."""
    # Cannot have both generated assets and no prompt_id
    if decision.get("generation_performed", False) and \
            not decision.get("prompt_id"):
        errors.append(
            "Contradiction: generation_performed=true but no prompt_id"
        )

    # Cannot have authorization without the right state
    if decision.get("generation_authorized", False) and \
            decision.get("generation_can_be_authorized", False) is False:
        errors.append(
            "Contradiction: generation_authorized=true but "
            "gate says cannot be authorized"
        )

    # Blocked path must not set authorization
    asset_blocker_active = decision.get("asset_blocker_active", False)
    if asset_blocker_active and decision.get("generation_authorized", False):
        errors.append(
            "Contradiction: asset_blocker_active=true but "
            "generation_authorized=true"
        )

    # production_accepted must be false in this layer
    if decision.get("production_accepted", False):
        errors.append(
            "Contradiction: production_accepted=true in generation gate layer"
        )


# ---------------------------------------------------------------------------
# Artifact Index and Episode Ledger updates
# ---------------------------------------------------------------------------

def _update_artifact_index(project_root: str, result: Dict[str, Any]) -> None:
    """Update artifact_index.json with generation gate artifacts."""
    control_dir = _get_control_dir(project_root)
    index_path = control_dir / "artifact_index.json"

    index = _load_json(index_path) or {}

    # Add generation gate entries
    index["generation_gate_layer_executed"] = True
    index["generation_gate_evaluated"] = True
    index["generation_gate_decision"] = result.get("selected_branch", "unknown")
    index["generation_gate_decision_artifact"] = str(
        control_dir / GATE_ARTIFACTS["generation_gate_decision"]
    )

    if result.get("generation_authorization_contract"):
        index["generation_authorization_contract_created"] = True
        index["generation_authorization_contract"] = GATE_ARTIFACTS["generation_authorization_contract"]
    else:
        index["generation_authorization_contract_created"] = False

    if result.get("generation_execution_contract"):
        index["generation_execution_contract_created"] = True
        index["generation_execution_contract"] = GATE_ARTIFACTS["generation_execution_contract"]

    if result.get("generation_runtime_blocker_report"):
        index["generation_runtime_blocker_report_created"] = True
        index["generation_runtime_blocker_report"] = GATE_ARTIFACTS["generation_runtime_blocker_report"]

    if result.get("controlled_asset_acquisition_gate_packet"):
        index["controlled_asset_acquisition_gate_packet_created"] = True
        index["controlled_asset_acquisition_gate_packet"] = GATE_ARTIFACTS["controlled_asset_acquisition_gate_packet"]

    if result.get("generation_blocked_operator_review_packet"):
        index["generation_blocked_operator_review_packet_created"] = True
        index["generation_blocked_operator_review_packet"] = GATE_ARTIFACTS["generation_blocked_operator_review_packet"]

    # Forbidden state flags
    index["generation_authorized"] = False
    index["generation_performed"] = False
    index["comfyui_submit_executed"] = False
    index["workflow_execution_performed"] = False
    index["retry_attempted"] = False
    index["visual_qa_executed"] = False
    index["visual_acceptance_executed"] = False
    index["preview_render_executed"] = False
    index["assembly_executed"] = False
    index["downstream_executed"] = False
    index["production_accepted"] = False

    # State
    index["current_state"] = result.get("current_state", BLOCKED_STATE)
    index["next_allowed_action"] = result.get("next_allowed_action", BLOCKED_STATE)
    index["timestamp"] = _utcnow()

    _write_json(index_path, index)


def _update_episode_ledger(project_root: str, result: Dict[str, Any]) -> None:
    """Add a ledger entry for the generation gate evaluation."""
    control_dir = _get_control_dir(project_root)
    ledger_path = control_dir / "episode_ledger.json"

    ledger = _load_json(ledger_path) or []

    entry = {
        "event": "generation_gate_evaluated",
        "task_id": TASK_ID,
        "selected_branch": result.get("selected_branch", "unknown"),
        "generation_gate_decision": result.get("selected_branch", "unknown"),
        "generation_authorized": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "workflow_execution_performed": False,
        "retry_attempted": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": result.get("current_state", BLOCKED_STATE),
        "next_allowed_action": result.get("next_allowed_action", BLOCKED_STATE),
        "previous_layer": PREVIOUS_LAYER,
        "next_layer": NEXT_LAYER,
        "timestamp": _utcnow(),
    }

    ledger.append(entry)
    _write_json(ledger_path, ledger)
