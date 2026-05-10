"""Tests for Script Supervisor Standards Agent.

Validates that the agent loads standards integration, creates contracts,
and performs all required audits with traceable rule references.
"""

import json
import pytest
from pathlib import Path


def test_script_supervisor_agent_exists():
    """ScriptSupervisorStandardsAgent class exists and can be instantiated."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    assert agent.AGENT_ID == "script_supervisor_continuity_guard_standards"
    assert agent.TASK_ID == "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001"


def test_script_supervisor_loads_standards_integration():
    """Agent loads standards integration and uses script_supervisor role standard."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    assert audit_result["standards_pack_version"] == "1.0.0"
    assert audit_result["traceable"] is True
    
    # Check that findings have traceable rule references
    findings = audit_result["audit_results"]["timeline_consistency"]["findings"]
    assert len(findings) > 0
    assert all("standard_id" in f for f in findings)
    assert all("policy_id" in f for f in findings)
    assert all("rule_id" in f for f in findings)


def test_script_supervisor_checks_timeline_artifacts():
    """Agent checks timeline model, marker registry, and edit decision list."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    timeline = audit_result["audit_results"]["timeline_consistency"]
    assert "timeline_model_present" in timeline
    assert "marker_registry_present" in timeline
    assert "edit_decision_list_present" in timeline
    assert "overall_pass" in timeline


def test_script_supervisor_checks_preview_artifacts():
    """Agent checks preview artifacts and detects static/duplicate risk."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    preview = audit_result["audit_results"]["preview_audit"]
    assert "preview_artifacts_registered" in preview
    assert "preview_static_or_duplicate_risk_checked" in preview
    assert "duplicate_static_ratio" in preview
    assert "path_consistency_checked" in preview


def test_script_supervisor_detects_or_records_static_duplicate_preview_risk():
    """Agent detects or records static/duplicate preview frame risk."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    preview = audit_result["audit_results"]["preview_audit"]
    # Should have checked for static/duplicate risk
    assert preview["preview_static_or_duplicate_risk_checked"] is True
    assert "duplicate_static_ratio" in preview


def test_script_supervisor_checks_contact_sheet_usefulness():
    """Agent evaluates contact sheet usefulness for scene development proof."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    contact_sheet = audit_result["audit_results"]["contact_sheet_audit"]
    assert "contact_sheet_useful" in contact_sheet
    assert "contact_sheet_usefulness_checked" in contact_sheet


def test_script_supervisor_checks_fake_operator_decision_absence():
    """Agent checks for and detects fake operator decisions."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    fake_decision = audit_result["audit_results"]["fake_decision_audit"]
    assert "fake_operator_decision_checked" in fake_decision
    assert "fake_operator_decision_detected" in fake_decision
    assert "human_operator_decision_found" in fake_decision


def test_script_supervisor_blocks_voice_assembly_downstream():
    """Agent ensures voice, assembly, and downstream remain blocked."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    downstream = audit_result["audit_results"]["downstream_guard"]
    assert downstream["production_accepted"] is False
    assert downstream["voice_generation_ready"] is False  # May be true but should be checked
    assert downstream["assembly_allowed"] is False
    assert downstream["downstream_allowed"] is False
    
    # Overall audit should maintain these blocks
    assert audit_result["production_accepted"] is False
    assert audit_result["voice_generation_ready"] is False
    assert audit_result["assembly_allowed"] is False
    assert audit_result["downstream_allowed"] is False


def test_script_supervisor_does_not_set_production_accepted():
    """Agent never sets production_accepted to true."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    assert audit_result["production_accepted"] is False


def test_script_supervisor_does_not_execute_generation_or_render():
    """Agent does not perform any generation, rendering, or ComfyUI execution."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    assert audit_result["generation_performed"] is False
    assert audit_result["comfyui_submit_executed"] is False
    assert audit_result["retry_attempted"] is False
    assert audit_result["preview_render_executed"] is False
    assert audit_result["final_render_executed"] is False
    assert audit_result["voice_generation_executed"] is False
    assert audit_result["assembly_executed"] is False
    assert audit_result["downstream_executed"] is False


def test_script_supervisor_creates_agent_contract():
    """Agent contract artifact contains correct role and forbidden actions."""
    contract_path = Path("data/rc2_multishot1_ep01/output/control/script_supervisor/script_supervisor_agent_contract.json")
    assert contract_path.exists()
    
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract["agent_id"] == "script_supervisor_continuity_guard_standards"
    assert contract["role"] == "script_supervisor"
    assert "generation" in contract["forbidden_actions"]
    assert "comfyui_submit" in contract["forbidden_actions"]
    assert "production_accepted_true" in contract["forbidden_actions"]
    assert contract["may_set_production_accepted"] is False


def test_script_supervisor_uses_script_supervisor_role_standard():
    """Agent references script_supervisor role standard in findings."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    # Check that findings reference the correct role standard
    findings = audit_result["audit_results"]["timeline_consistency"]["findings"]
    script_supervisor_findings = [f for f in findings if f.get("role") == "script_supervisor"]
    assert len(script_supervisor_findings) > 0


def test_script_supervisor_updates_artifact_index_and_ledger():
    """Agent updates artifact_index.json and episode_ledger.json."""
    from app.agents.script_supervisor import ScriptSupervisorStandardsAgent

    agent = ScriptSupervisorStandardsAgent("data/rc2_multishot1_ep01")
    audit_result = agent.run_full_audit()
    
    # Write artifacts should update index and ledger
    written = agent.write_all_artifacts(audit_result)
    index = agent.update_artifact_index(audit_result)
    ledger = agent.update_episode_ledger(audit_result)
    
    # Check index was updated
    assert index["script_supervisor_agent_created"] is True
    assert index["script_supervisor_standards_driven"] is True
    assert index["production_accepted"] is False
    
    # Check ledger was updated
    assert len(ledger) > 0
    # Some ledger entries use "event" instead of "event_type" — check both
    script_supervisor_events = [
        e for e in ledger
        if e.get("event_type") == "script_supervisor_standards_audit"
        or e.get("event") == "script_supervisor_standards_audit"
    ]
    assert len(script_supervisor_events) > 0


def test_script_supervisor_all_required_artifacts_created():
    """All required script supervisor artifacts are created."""
    required_artifacts = [
        "script_supervisor_agent_contract.json",
        "script_supervisor_standards_binding.json",
        "script_supervisor_timeline_consistency_report.json",
        "script_supervisor_preview_audit_report.json",
        "script_supervisor_contact_sheet_audit_report.json",
        "script_supervisor_path_consistency_report.json",
        "script_supervisor_fake_decision_audit.json",
        "script_supervisor_downstream_guard_report.json",
        "script_supervisor_blocker_packet.json",
        "script_supervisor_operator_review_packet.json",
        "script_supervisor_readiness_report.json",
        "script_supervisor_proof.json"
    ]
    
    script_supervisor_dir = Path("data/rc2_multishot1_ep01/output/control/script_supervisor")
    for artifact in required_artifacts:
        assert (script_supervisor_dir / artifact).exists(), f"Missing artifact: {artifact}"
