"""Tests for Script Supervisor CLI commands.

Validates that combine-script-supervisor-* CLI commands execute correctly
and return valid JSON output.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CLI_MODULE = "app.cli"


def _run_cli(command: str, expect_success: bool = True) -> dict:
    """Run a CLI command and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, "-m", CLI_MODULE, command,
         "--project-root", str(PROJECT_ROOT), "--json"],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    if expect_success:
        assert result.returncode == 0, f"CLI {command} failed:\nstdout:{result.stdout}\nstderr:{result.stderr}"
    return json.loads(result.stdout)


def test_cli_script_supervisor_audit_exists():
    """combine-script-supervisor-audit command can be invoked."""
    from app.cli import combine_script_supervisor_audit
    assert callable(combine_script_supervisor_audit)


def test_cli_script_supervisor_report_exists():
    """combine-script-supervisor-report command can be invoked."""
    from app.cli import combine_script_supervisor_report
    assert callable(combine_script_supervisor_report)


def test_cli_script_supervisor_readiness_exists():
    """combine-script-supervisor-readiness command can be invoked."""
    from app.cli import combine_script_supervisor_readiness
    assert callable(combine_script_supervisor_readiness)


def test_cli_script_supervisor_audit_output():
    """combine-script-supervisor-audit produces valid JSON with required fields."""
    data = _run_cli("combine-script-supervisor-audit")

    assert data["role"] == "script_supervisor"
    assert data["agent_id"] == "script_supervisor_continuity_guard_standards"
    assert data["production_accepted"] is False
    assert data["voice_generation_ready"] is False
    assert data["assembly_allowed"] is False
    assert data["downstream_allowed"] is False
    assert data["generation_performed"] is False
    assert data["comfyui_submit_executed"] is False
    assert data["traceable"] is True

    # Check audit results exist
    assert "audit_results" in data
    assert "timeline_consistency" in data["audit_results"]
    assert "preview_audit" in data["audit_results"]
    assert "contact_sheet_audit" in data["audit_results"]
    assert "fake_decision_audit" in data["audit_results"]
    assert "downstream_guard" in data["audit_results"]
    assert "path_consistency" in data["audit_results"]

    # Check artifacts_written in JSON output
    assert "artifacts_written" in data
    assert data["artifacts_written"]["agent_contract"].endswith("script_supervisor_agent_contract.json")
    assert data["artifacts_written"]["proof"].endswith("script_supervisor_proof.json")


def test_cli_script_supervisor_readiness_output():
    """combine-script-supervisor-readiness produces valid JSON with readiness fields."""
    data = _run_cli("combine-script-supervisor-readiness")

    assert "current_state" in data
    assert "next_allowed_action" in data
    assert "blocker_detected" in data
    assert "production_accepted" in data


def test_cli_script_supervisor_report_output():
    """combine-script-supervisor-report produces valid JSON with reports_written."""
    data = _run_cli("combine-script-supervisor-report")

    assert data["status"] == "ok"
    assert "reports_written" in data
    assert data["project_root"] == str(PROJECT_ROOT)


def test_cli_script_supervisor_subprocess_audit():
    """combine-script-supervisor-audit in subprocess returns valid JSON."""
    result = subprocess.run(
        [sys.executable, "-m", CLI_MODULE, "combine-script-supervisor-audit",
         "--project-root", str(PROJECT_ROOT), "--json"],
        capture_output=True, text=True, cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["agent_id"] == "script_supervisor_continuity_guard_standards"
