"""Identity Lock Contract - defines agent contract and responsibilities.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


class IdentityLockContract:
    """Defines the contract for the Identity Lock agent."""

    AGENT_ID = "identity_lock"
    TASK_ID = "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001"
    ROLE = "identity_lock"
    RESPONSIBILITY_ZONE = "canonical_character_identity_preservation"

    # Forbidden actions - agent cannot perform these
    FORBIDDEN_ACTIONS = [
        "perform_second_generation",
        "blind_retry",
        "fake_identity_similarity_score",
        "fake_prompt_id",
        "fake_assets",
        "use_quality_refs_as_identity_source",
        "use_composition_refs_as_identity_source",
        "allow_extra_human_subject",
        "use_square_1024_closeup_workflow",
        "claim_visual_qa_acceptance",
        "trigger_assembly",
        "set_production_accepted_true",
    ]

    # Allowed tools
    ALLOWED_TOOLS = [
        "llm_brain_decision",
        "identity_contract",
        "reference_router",
        "identity_gate",
        "single_subject_gate",
        "workflow_patch",
        "comfyui_submit",
        "blank_detector",
        "framing_detector",
        "state_updater",
    ]

    # Forbidden tools
    FORBIDDEN_TOOLS = [
        "retry_engine",
        "assembly_pipeline",
        "downstream_pipeline",
        "visual_acceptance_gate",
    ]

    # Reference roles
    REFERENCE_ROLES = [
        "identity_anchor",
        "composition",
        "quality_text_only",
        "negative_suppression_only",
    ]

    # Blocker conditions
    BLOCKER_CONDITIONS = [
        "second_generation_attempted",
        "blind_retry_attempted",
        "fake_identity_score_claimed",
        "quality_ref_used_as_identity",
        "composition_ref_used_as_identity",
        "extra_human_subject_allowed",
        "square_closeup_workflow_used",
        "visual_qa_acceptance_claimed",
        "assembly_executed",
        "downstream_executed",
        "production_accepted_set_true",
    ]

    # Required inputs
    REQUIRED_INPUTS = [
        "project_root",
        "state_json",
        "canonical_reference_inventory",
        "previous_rejected_assets",
        "operator_rejection_reason",
    ]

    # Required artifacts
    REQUIRED_ARTIFACTS = [
        "state.json",
        "artifact_index.json",
        "episode_ledger.json",
    ]

    # Decision outputs
    DECISION_OUTPUTS = ["IDENTITY_LOCK_GENERATION_AUTHORIZED", "BLOCKED"]

    # Permissions
    MAY_SET_PRODUCTION_ACCEPTED = False
    MAY_AUTHORIZE_GENERATION = True
    MAY_AUTHORIZE_RETRY = False
    MAY_AUTHORIZE_COMFYUI_SUBMIT = True
    MAY_AUTHORIZE_DOWNSTREAM = False

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
            "allowed_tools": cls.ALLOWED_TOOLS,
            "forbidden_tools": cls.FORBIDDEN_TOOLS,
            "reference_roles": cls.REFERENCE_ROLES,
            "blocker_conditions": cls.BLOCKER_CONDITIONS,
            "decision_outputs": cls.DECISION_OUTPUTS,
            "may_set_production_accepted": cls.MAY_SET_PRODUCTION_ACCEPTED,
            "may_authorize_generation": cls.MAY_AUTHORIZE_GENERATION,
            "may_authorize_retry": cls.MAY_AUTHORIZE_RETRY,
            "may_authorize_comfyui_submit": cls.MAY_AUTHORIZE_COMFYUI_SUBMIT,
            "may_authorize_downstream": cls.MAY_AUTHORIZE_DOWNSTREAM,
            "max_generations": 1,
            "stop_after_generation": True,
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_tool_policy(cls) -> Dict[str, Any]:
        """Get the tool policy for the agent."""
        return {
            "policy_id": "identity_lock_tool_policy",
            "task_id": cls.TASK_ID,
            "role": cls.ROLE,
            "allowed_tools": cls.ALLOWED_TOOLS,
            "forbidden_tools": cls.FORBIDDEN_TOOLS,
            "max_generations": 1,
            "no_retry_authorized": True,
            "no_downstream_authorized": True,
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
