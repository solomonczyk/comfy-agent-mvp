"""Tests for Script Supervisor Agent Contract.

Validates that the agent contract contains the correct role, responsibilities,
permissions, and forbidden actions as specified.
"""

import json
import os
import pytest
from pathlib import Path


def test_agent_contract_exists():
    """Agent contract JSON artifact exists at canonical path."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor_agent_contract.json")
    assert path.exists(), f"Contract not found at {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["agent_id"] == "script_supervisor_continuity_guard"
    assert data["role"] == "Script Supervisor / Continuity Guard Agent"


def test_agent_contract_responsibilities():
    """Agent contract contains all required responsibilities."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor_agent_contract.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    responsibilities = set(data["responsibilities"])
    required = {
        "timeline continuity",
        "preview continuity",
        "duplicate/static frame detection",
        "contact sheet usefulness validation",
        "path consistency validation",
        "operator decision authenticity guard",
        "voice rejection reconciliation",
        "proof consistency audit",
    }
    for r in required:
        assert r in responsibilities, f"Missing responsibility: {r}"


def test_agent_contract_forbidden_actions():
    """Agent contract forbids all dangerous actions."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor_agent_contract.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    forbidden = set(data["forbidden_actions"])
    required = {
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
    }
    for action in required:
        assert action in forbidden, f"Missing forbidden action: {action}"


def test_agent_contract_permissions():
    """Agent contract correctly denies permission to accept preview/voice/production."""
    path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor_agent_contract.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["may_block_pipeline"] is True
    assert data["may_accept_preview"] is False
    assert data["may_accept_voice"] is False
    assert data["may_set_production_accepted"] is False


def test_agent_contract_code_exists():
    """Python ScriptSupervisorAgent class exists with correct contract."""
    from app.agents.film_crew.script_supervisor import ScriptSupervisorAgent

    agent = ScriptSupervisorAgent(project_root="/tmp/test")
    contract = agent.get_contract()
    assert contract["agent_id"] == "script_supervisor_continuity_guard"
    assert contract["role"] == "Script Supervisor / Continuity Guard Agent"
    assert contract["may_block_pipeline"] is True
    assert contract["may_accept_preview"] is False
    assert contract["may_set_production_accepted"] is False


def test_agent_permission_matrix():
    """Script Supervisor permission matrix correctly restricts all dangerous actions."""
    from app.agents.film_crew.script_supervisor import ScriptSupervisorAgent

    agent = ScriptSupervisorAgent(project_root="/tmp/test")
    matrix = agent.get_permission_matrix()
    assert matrix["may_execute_generation"] is False
    assert matrix["may_execute_retry"] is False
    assert matrix["may_execute_comfyui_submit"] is False
    assert matrix["may_execute_preview_render"] is False
    assert matrix["may_execute_voice_generation"] is False
    assert matrix["may_execute_assembly"] is False
    assert matrix["may_execute_downstream"] is False
    assert matrix["may_make_operator_decision"] is False


def test_agent_mcp_access_matrix():
    """Script Supervisor MCP access correctly denies write operations."""
    from app.agents.film_crew.script_supervisor import ScriptSupervisorAgent

    agent = ScriptSupervisorAgent(project_root="/tmp/test")
    mcp = agent.get_mcp_access_matrix()
    assert mcp["filesystem.read"] == "allowed"
    assert mcp["filesystem.write"] == "denied"
    assert mcp["comfyui.submit"] == "denied"
    assert mcp["voice.generate"] == "denied"
    assert mcp["assembly.execute"] == "denied"
    assert mcp["downstream.execute"] == "denied"
    assert mcp["production.accept"] == "denied"
    assert mcp["operator.decision_write"] == "denied"
