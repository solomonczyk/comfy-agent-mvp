"""Visual Reference Curator Contract - defines agent contract and responsibilities.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


class VisualReferenceCuratorContract:
    """Defines the contract for the Visual Reference Curator agent."""

    AGENT_ID = "visual_reference_curator"
    TASK_ID = "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001"
    ROLE = "visual_reference_curator"
    RESPONSIBILITY_ZONE = "canonical_reference_management_and_corrective_package_preparation"

    # Forbidden actions - agent cannot perform these
    FORBIDDEN_ACTIONS = [
        "perform_generation",
        "attempt_retry",
        "submit_to_comfyui",
        "claim_visual_acceptance",
        "approve_for_downstream",
        "trigger_assembly",
        "set_production_accepted_true",
        "delete_canonical_references",
        "move_canonical_references",
        "fake_operator_decision",
    ]

    # Allowed tools
    ALLOWED_TOOLS = [
        "reference_classifier",
        "reference_inventory_scanner",
        "negative_reference_registrar",
        "corrective_package_builder",
        "state_updater",
    ]

    # Forbidden tools
    FORBIDDEN_TOOLS = [
        "comfyui_submit",
        "image_generation",
        "retry_engine",
        "assembly_pipeline",
        "downstream_pipeline",
        "visual_acceptance_gate",
    ]

    # Reference roles
    REFERENCE_ROLES = [
        "identity_reference",
        "composition_reference",
        "quality_reference",
        "environment_reference",
        "character_in_environment_reference",
        "negative_reference",
    ]

    # Blocker conditions
    BLOCKER_CONDITIONS = [
        "generation_attempted",
        "retry_attempted",
        "comfyui_submit_executed",
        "visual_acceptance_claimed",
        "assembly_executed",
        "downstream_executed",
        "production_accepted_set_true",
        "canonical_reference_deleted",
        "canonical_reference_moved",
    ]

    # Required inputs
    REQUIRED_INPUTS = [
        "project_root",
        "state_json",
        "latest_generated_asset",
        "operator_visual_verdict",
        "rejection_reason",
    ]

    # Required artifacts
    REQUIRED_ARTIFACTS = [
        "state.json",
        "artifact_index.json",
        "episode_ledger.json",
    ]

    # Decision outputs
    DECISION_OUTPUTS = ["CORRECTIVE_PACKAGE_READY", "BLOCKED"]

    # Permissions
    MAY_SET_PRODUCTION_ACCEPTED = False
    MAY_AUTHORIZE_GENERATION = False
    MAY_AUTHORIZE_RETRY = False
    MAY_AUTHORIZE_COMFYUI_SUBMIT = False
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
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_tool_policy(cls) -> Dict[str, Any]:
        """Get the tool policy for the agent."""
        return {
            "policy_id": "visual_reference_curator_tool_policy",
            "task_id": cls.TASK_ID,
            "role": cls.ROLE,
            "allowed_tools": cls.ALLOWED_TOOLS,
            "forbidden_tools": cls.FORBIDDEN_TOOLS,
            "no_generation_authorized": True,
            "no_retry_authorized": True,
            "no_comfyui_submit_authorized": True,
            "no_downstream_authorized": True,
            "traceable": True,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
