"""Permission definitions and enforcement for film crew agents.

Defines the allowed tools, forbidden actions, and MCP tool access matrix
that govern Script Supervisor and future film crew agent behavior.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Script Supervisor: Allowed Tools
# ---------------------------------------------------------------------------

SCRIPT_SUPERVISOR_ALLOWED_TOOLS: List[str] = [
    "filesystem_read",
    "json_artifact_read",
    "preview_media_read",
    "timeline_artifact_read",
    "safe_cli_validation",
    "pytest",
    "git_status",
]

# ---------------------------------------------------------------------------
# Script Supervisor: Forbidden Actions
# ---------------------------------------------------------------------------

SCRIPT_SUPERVISOR_FORBIDDEN_ACTIONS: List[str] = [
    "generation",
    "retry",
    "comfyui_submit",
    "preview_render",
    "voice_generation",
    "visual_acceptance",
    "operator_acceptance",
    "assembly",
    "downstream",
    "production_accepted_true",
    "model_download_install",
]

# ---------------------------------------------------------------------------
# Script Supervisor: Full Permission Matrix
# ---------------------------------------------------------------------------

SCRIPT_SUPERVISOR_PERMISSION_MATRIX: Dict[str, bool] = {
    "may_block_pipeline": True,
    "may_accept_preview": False,
    "may_accept_voice": False,
    "may_set_production_accepted": False,
    "may_execute_generation": False,
    "may_execute_retry": False,
    "may_execute_comfyui_submit": False,
    "may_execute_preview_render": False,
    "may_execute_voice_generation": False,
    "may_execute_assembly": False,
    "may_execute_downstream": False,
    "may_make_operator_decision": False,
}

# ---------------------------------------------------------------------------
# Agent MCP Tool Access Matrix
# ---------------------------------------------------------------------------

SCRIPT_SUPERVISOR_MCP_ACCESS: Dict[str, str] = {
    "filesystem.read": "allowed",
    "filesystem.write": "denied",
    "json.parse": "allowed",
    "json.write": "denied",
    "preview.read_metadata": "allowed",
    "preview.read_frames": "allowed",
    "timeline.read": "allowed",
    "cli.execute_safe": "allowed",
    "cli.execute_unsafe": "denied",
    "comfyui.submit": "denied",
    "comfyui.status": "allowed_readonly",
    "voice.generate": "denied",
    "audio.render": "denied",
    "assembly.execute": "denied",
    "downstream.execute": "denied",
    "operator.decision_read": "allowed",
    "operator.decision_write": "denied",
    "production.accept": "denied",
    "model.install": "denied",
    "model.download": "denied",
}


def get_script_supervisor_contract_dict() -> dict:
    """Return the canonical Script Supervisor agent contract as a dict."""
    return {
        "agent_id": "script_supervisor_continuity_guard",
        "role": "Script Supervisor / Continuity Guard Agent",
        "responsibilities": [
            "timeline continuity",
            "preview continuity",
            "duplicate/static frame detection",
            "contact sheet usefulness validation",
            "path consistency validation",
            "operator decision authenticity guard",
            "voice rejection reconciliation",
            "proof consistency audit",
        ],
        "allowed_tools": SCRIPT_SUPERVISOR_ALLOWED_TOOLS,
        "forbidden_actions": SCRIPT_SUPERVISOR_FORBIDDEN_ACTIONS,
        "may_block_pipeline": True,
        "may_accept_preview": False,
        "may_accept_voice": False,
        "may_set_production_accepted": False,
        "required_inputs": [
            "project_root",
            "control_path",
            "preview_artifacts_path",
        ],
        "required_outputs": [
            "script_supervisor_agent_contract.json",
            "script_supervisor_preview_audit_report.json",
            "script_supervisor_blocker_report.json",
            "voice_rejection_record.json",
            "post_preview_reconciliation_report.json",
        ],
    }
