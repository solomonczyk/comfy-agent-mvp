"""State Audit Guard Contract - defines agent contract and responsibilities.

RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class StateAuditGuardContract:
    """Defines the contract for the State Audit Guard agent."""

    AGENT_ID = "state_audit_guard"
    TASK_ID = "RC-COMBINE-V2-STATE-AUDIT-GUARD-VERTICAL-SLICE-001"
    ROLE = "state_audit_guard"
    RESPONSIBILITY_ZONE = "state_consistency_and_audit_trail_validation"

    # Forbidden actions - agent cannot perform these
    FORBIDDEN_ACTIONS = [
        "claim_visual_acceptance",
        "set_production_accepted_true",
        "fake_operator_decision",
        "approve_for_downstream",
        "trigger_voice_generation",
        "trigger_assembly",
        "perform_generation",
        "modify_state_artifacts_without_audit_trail",
    ]

    # Decision outputs
    DECISION_OUTPUTS = ["ACCEPTED", "BLOCKED"]

    # Permissions
    MAY_SET_PRODUCTION_ACCEPTED = False
    MAY_AUTHORIZE_GENERATION = False
    MAY_AUTHORIZE_RETRY = False
    MAY_AUTHORIZE_RENDER = False
    MAY_AUTHORIZE_DOWNSTREAM = False

    # Required inputs
    REQUIRED_INPUTS = [
        "state_json",
        "artifact_index_json",
        "episode_ledger_json",
        "proof_artifacts",
        "git_status",
        "canonical_artifacts",
    ]

    # Required artifacts
    REQUIRED_ARTIFACTS = [
        "state.json",
        "artifact_index.json",
        "episode_ledger.json",
        "proof_json_files",
    ]

    # Blocker conditions
    BLOCKER_CONDITIONS = [
        "state_artifact_contradiction",
        "dirty_git",
        "missing_proof_artifacts",
        "fake_operator_decision",
        "forbidden_action_executed",
        "missing_canonical_artifact",
    ]

    @classmethod
    def get_contract(cls) -> Dict[str, Any]:
        """Get the full agent contract."""
        return {
            "agent_id": cls.AGENT_ID,
            "role": cls.ROLE,
            "task_id": cls.TASK_ID,
            "responsibility_zone": cls.RESPONSIBILITY_ZONE,
            "allowed_inputs": cls.REQUIRED_INPUTS,
            "required_artifacts": cls.REQUIRED_ARTIFACTS,
            "forbidden_actions": cls.FORBIDDEN_ACTIONS,
            "blocker_conditions": cls.BLOCKER_CONDITIONS,
            "decision_outputs": cls.DECISION_OUTPUTS,
            "may_set_production_accepted": cls.MAY_SET_PRODUCTION_ACCEPTED,
            "may_authorize_generation": cls.MAY_AUTHORIZE_GENERATION,
            "may_authorize_retry": cls.MAY_AUTHORIZE_RETRY,
            "may_authorize_render": cls.MAY_AUTHORIZE_RENDER,
            "may_authorize_downstream": cls.MAY_AUTHORIZE_DOWNSTREAM,
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_tool_policy(cls) -> Dict[str, Any]:
        """Get the tool policy for the agent."""
        return {
            "policy_id": "state_audit_guard_tool_policy",
            "task_id": cls.TASK_ID,
            "role": cls.ROLE,
            "allowed_tools": [
                "json_diff",
                "git_checker",
                "timeline_validator",
                "hash_verifier",
            ],
            "forbidden_tools": [
                "comfyui_submit",
                "image_generation",
                "render_engine",
                "voice_synthesis",
                "audio_synthesis",
                "assembly_pipeline",
                "downstream_pipeline",
            ],
            "no_generation_authorized": True,
            "no_retry_authorized": True,
            "no_render_authorized": True,
            "no_downstream_authorized": True,
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
