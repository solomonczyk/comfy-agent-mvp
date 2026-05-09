"""Script Supervisor / Continuity Guard Agent.

The first vertical-slice agent in the AI Film Crew layer. This agent:
  - Performs read-only preview continuity audits
  - Detects duplicate/static frames and useless contact sheets
  - Guards against fake operator decisions
  - Records voice rejection state
  - Produces canonical blocker reports
  - NEVER generates, renders, submits, or modifies production artifacts

This agent sits on top of existing Combine CLI/state/artifacts and extends
the agent registry layer with a real domain-specific role.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.film_crew.audit import run_full_continuity_audit
from app.agents.film_crew.permissions import (
    SCRIPT_SUPERVISOR_ALLOWED_TOOLS,
    SCRIPT_SUPERVISOR_FORBIDDEN_ACTIONS,
    SCRIPT_SUPERVISOR_PERMISSION_MATRIX,
    SCRIPT_SUPERVISOR_MCP_ACCESS,
    get_script_supervisor_contract_dict,
)


class ScriptSupervisorAgent:
    """Script Supervisor / Continuity Guard Agent.

    This agent is a read-only auditor that enforces preview continuity,
    operator decision authenticity, and pipeline safety. It never performs
    generation, rendering, or any production action.

    Attributes:
        agent_id: Unique identifier for this agent.
        project_root: Root path of the project being audited.
        control_path: Path to the output/control directory.
    """

    def __init__(self, project_root: str):
        self.agent_id = "script_supervisor_continuity_guard"
        self.project_root = project_root
        self.control_path = os.path.join(project_root, "output", "control")

    # -----------------------------------------------------------------------
    # Agent Contract
    # -----------------------------------------------------------------------

    def get_contract(self) -> Dict[str, Any]:
        """Return the canonical agent role contract."""
        return get_script_supervisor_contract_dict()

    def get_permission_matrix(self) -> Dict[str, bool]:
        """Return the permission matrix dict."""
        return dict(SCRIPT_SUPERVISOR_PERMISSION_MATRIX)

    def get_allowed_tools(self) -> list:
        """Return the list of allowed tools."""
        return list(SCRIPT_SUPERVISOR_ALLOWED_TOOLS)

    def get_forbidden_actions(self) -> list:
        """Return the list of forbidden actions."""
        return list(SCRIPT_SUPERVISOR_FORBIDDEN_ACTIONS)

    def get_mcp_access_matrix(self) -> Dict[str, str]:
        """Return the MCP tool access matrix."""
        return dict(SCRIPT_SUPERVISOR_MCP_ACCESS)

    # -----------------------------------------------------------------------
    # Audit Entry Point
    # -----------------------------------------------------------------------

    def run_audit(self) -> Dict[str, Any]:
        """Execute the full continuity audit pipeline.

        Returns:
            Dict with all audit results, reports, and blocker status.
        """
        return run_full_continuity_audit(self.project_root)

    # -----------------------------------------------------------------------
    # Artifact Persistence
    # -----------------------------------------------------------------------

    def _ensure_control_dir(self) -> str:
        """Ensure the control directory exists, return its path."""
        os.makedirs(self.control_path, exist_ok=True)
        return self.control_path

    def _write_artifact(self, filename: str, data: Dict[str, Any]) -> str:
        """Write a JSON artifact to the control directory.

        Args:
            filename: Name of the artifact file.
            data: Data to serialize as JSON.

        Returns:
            Full path to the written artifact.
        """
        ctrl = self._ensure_control_dir()
        path = os.path.join(ctrl, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def write_all_artifacts(self, audit_result: Dict[str, Any]) -> Dict[str, str]:
        """Write all canonical artifacts from an audit result.

        Returns:
            Dict mapping artifact names to file paths.
        """
        written = {}

        # 1. Agent contract
        written["agent_contract"] = self._write_artifact(
            "script_supervisor_agent_contract.json",
            self.get_contract(),
        )

        # 2. Preview audit report
        written["preview_audit"] = self._write_artifact(
            "script_supervisor_preview_audit_report.json",
            audit_result.get("preview_audit", {}),
        )

        # 3. Blocker report
        written["blocker_report"] = self._write_artifact(
            "script_supervisor_blocker_report.json",
            audit_result.get("blocker", {}),
        )

        # 4. Voice rejection record
        written["voice_rejection_record"] = self._write_artifact(
            "voice_rejection_record.json",
            audit_result.get("voice_rejection_record", {}),
        )

        # 5. Post-preview reconciliation report
        written["reconciliation_report"] = self._write_artifact(
            "post_preview_reconciliation_report.json",
            audit_result.get("reconciliation", {}),
        )

        return written

    # -----------------------------------------------------------------------
    # State / Index / Ledger Updates
    # -----------------------------------------------------------------------

    def update_artifact_index(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update artifact_index.json with script supervisor results.

        Safe: only modifies the index file, not any production artifacts.
        """
        index_path = os.path.join(self.control_path, "artifact_index.json")
        index: Dict[str, Any] = {}
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                index = {}

        blocker = audit_result.get("blocker", {})

        # Update fields
        index["script_supervisor_agent_created"] = True
        index["script_supervisor_blocker_active"] = blocker.get("blocker_detected", False)
        index["script_supervisor_blocker_type"] = blocker.get("blocker_type")
        index["script_supervisor_audit_timestamp"] = audit_result.get(
            "audit_timestamp", datetime.now(timezone.utc).isoformat()
        )
        index["script_supervisor_audit_executed"] = True
        index["preview_valid"] = blocker.get("preview_valid", False)
        index["contact_sheet_useful"] = blocker.get("contact_sheet_useful", False)
        index["voice_generation_allowed"] = blocker.get("voice_generation_allowed", False)
        index["voice_generation_ready"] = blocker.get("voice_generation_ready", False)
        index["assembly_allowed"] = blocker.get("assembly_allowed", False)
        index["downstream_allowed"] = blocker.get("downstream_allowed", False)
        index["production_accepted"] = blocker.get("production_accepted", False)
        index["fake_success_prevented"] = blocker.get("fake_success_prevented", False)

        # Update state based on blocker
        if blocker.get("blocker_detected", False):
            index["next_allowed_action"] = "preview_correction_plan_required"
            index["current_state"] = "preview_operator_review_required"

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def update_episode_ledger(self, audit_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Record script supervisor audit event in the episode ledger."""
        ledger_path = os.path.join(self.control_path, "episode_ledger.json")
        ledger: list = []
        if os.path.isfile(ledger_path):
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except (json.JSONDecodeError, IOError):
                ledger = []

        event = {
            "event_type": "script_supervisor_audit",
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blocker_detected": audit_result.get("blocker", {}).get("blocker_detected", False),
            "blocker_type": audit_result.get("blocker", {}).get("blocker_type"),
            "preview_valid": audit_result.get("blocker", {}).get("preview_valid", False),
            "voice_generation_allowed": audit_result.get("blocker", {}).get("voice_generation_allowed", False),
            "assembly_allowed": audit_result.get("blocker", {}).get("assembly_allowed", False),
            "downstream_allowed": audit_result.get("blocker", {}).get("downstream_allowed", False),
            "production_accepted": audit_result.get("blocker", {}).get("production_accepted", False),
            "generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
        }
        ledger.append(event)

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)

        return ledger
