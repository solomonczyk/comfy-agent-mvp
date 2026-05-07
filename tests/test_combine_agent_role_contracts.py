"""RC-COMBINE-V2-5401-5700 — Agent role contract integrity tests."""
from __future__ import annotations

import json
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)
CONTRACTS_DIR = CONTROL_DIR / "agent_role_contracts"


def _load(name: str) -> dict:
    p = CONTROL_DIR / name
    assert p.exists(), f"Missing control artifact: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_contract(name: str) -> dict:
    p = CONTRACTS_DIR / name
    assert p.exists(), f"Missing contract: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


REQUIRED_CONTRACT_SECTIONS = [
    "agent_id",
    "agent_name",
    "professional_role",
    "mission",
    "business_goal",
    "operational_goal",
    "zone_of_responsibility",
    "authority_level",
    "allowed_actions",
    "forbidden_actions",
    "required_inputs",
    "required_outputs",
    "required_artifacts",
    "acceptance_criteria",
    "rejection_criteria",
    "quality_bar",
    "handoff_to_next_agent",
    "handoff_blockers",
    "runtime_boundaries",
    "dangerous_actions_policy",
    "operator_gate_rules",
    "proof_requirements",
    "failure_handling",
    "contradiction_checks",
    "canonical_json_output_schema",
    "production_accepted_policy",
]

REQUIRED_CONTRACT_FILES = [
    "orchestrator_pipeline_controller_contract.json",
    "brief_intent_agent_contract.json",
    "workflow_recipe_architect_contract.json",
    "generation_executor_contract.json",
    "asset_manifest_collector_contract.json",
    "visual_quality_agent_contract.json",
    "retry_corrective_planner_contract.json",
    "assembly_downstream_guard_contract.json",
    "evidence_freeze_auditor_contract.json",
]


def test_all_required_agent_contracts_exist():
    for fname in REQUIRED_CONTRACT_FILES:
        assert (
            CONTRACTS_DIR / fname
        ).exists(), f"Missing required contract: {fname}"


def test_contracts_are_not_empty_or_stub():
    for fname in REQUIRED_CONTRACT_FILES:
        p = CONTRACTS_DIR / fname
        size = p.stat().st_size
        assert size >= 1024, f"Contract is stub: {fname} ({size} bytes)"


def test_each_contract_has_required_instruction_sections():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        for section in REQUIRED_CONTRACT_SECTIONS:
            assert section in contract, (
                f"Missing section '{section}' in {fname}"
            )
            assert contract[section] is not None, (
                f"Section '{section}' is None in {fname}"
            )
            if isinstance(contract[section], list):
                assert len(contract[section]) > 0, (
                    f"Section '{section}' is empty list in {fname}"
                )
            elif isinstance(contract[section], dict):
                assert len(contract[section]) > 0, (
                    f"Section '{section}' is empty dict in {fname}"
                )
            elif isinstance(contract[section], str):
                assert len(contract[section]) > 10, (
                    f"Section '{section}' is too short in {fname}"
                )


def test_visual_quality_agent_has_blocking_authority():
    contract = _load_contract("visual_quality_agent_contract.json")
    allowed = contract.get("allowed_actions", [])
    assert any("visual verdict" in a.lower() for a in allowed), (
        "Visual QA agent must have visual verdict authority"
    )
    forbidden = contract.get("forbidden_actions", [])
    assert any("set production_accepted" in f.lower() for f in forbidden), (
        "Visual QA agent must not set production_accepted"
    )
    assert contract.get("authority_level") == "visual_quality_blocker", (
        "Visual QA agent must have visual_quality_blocker authority"
    )


def test_technical_pass_not_equal_visual_pass():
    contract = _load_contract("visual_quality_agent_contract.json")
    mission = contract.get("mission", "")
    assert (
        "technical PASS" in mission.lower() or "technical" in mission.lower()
    ), "Mission must reference technical PASS"
    assert (
        "visual PASS" in mission.lower() or "visual" in mission.lower()
    ), "Mission must reference visual PASS"
    forbidden = " ".join(contract.get("forbidden_actions", []))
    assert "conflate technical pass with visual pass" in forbidden.lower(), (
        "Must forbid conflating technical PASS with visual PASS"
    )


def test_production_accepted_false_without_operator_review():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        policy = contract.get("production_accepted_policy", "")
        assert "must remain false" in policy.lower(), (
            f"production_accepted_policy must require false in {fname}"
        )


def test_contract_index_exists():
    data = _load("combine_v2_agent_role_contract_index.json")
    assert data.get("combine_v2_agent_role_contract_index") is not None
    agents = data["combine_v2_agent_role_contract_index"].get("agents", [])
    assert len(agents) == 9, f"Expected 9 agents, got {len(agents)}"


def test_contract_index_lists_all_contracts():
    data = _load("combine_v2_agent_role_contract_index.json")
    agents = data["combine_v2_agent_role_contract_index"]["agents"]
    indexed_files = {a["contract_file"] for a in agents}
    assert indexed_files == set(REQUIRED_CONTRACT_FILES), (
        f"Index missing contracts: {set(REQUIRED_CONTRACT_FILES) - indexed_files}"
    )


def test_contracts_have_unique_agent_ids():
    ids = []
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        ids.append(contract.get("agent_id", ""))
    assert len(ids) == len(set(ids)), "Duplicate agent_ids found"


def test_each_contract_has_non_empty_allowed_actions():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        actions = contract.get("allowed_actions", [])
        assert len(actions) >= 5, (
            f"Too few allowed_actions in {fname}: {len(actions)}"
        )


def test_each_contract_has_non_empty_forbidden_actions():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        actions = contract.get("forbidden_actions", [])
        assert len(actions) >= 3, (
            f"Too few forbidden_actions in {fname}: {len(actions)}"
        )


def test_each_contract_has_canonical_output_schema():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        schema = contract.get("canonical_json_output_schema", {})
        assert len(schema) > 0, (
            f"Missing canonical_json_output_schema in {fname}"
        )


def test_each_contract_has_failure_handling():
    for fname in REQUIRED_CONTRACT_FILES:
        contract = _load_contract(fname)
        handling = contract.get("failure_handling", {})
        assert len(handling) > 0, (
            f"Missing failure_handling in {fname}"
        )


def test_orchestrator_forbids_generation_and_visual_acceptance():
    contract = _load_contract("orchestrator_pipeline_controller_contract.json")
    forbidden = " ".join(contract.get("forbidden_actions", []))
    assert "perform generation" in forbidden.lower()
    assert "visual acceptance" in forbidden.lower()
    assert "set production_accepted" in forbidden.lower()


def test_generation_executor_requires_authorization():
    contract = _load_contract("generation_executor_contract.json")
    allowed = " ".join(contract.get("allowed_actions", []))
    assert "verify authorization gate" in allowed.lower()
    forbidden = " ".join(contract.get("forbidden_actions", []))
    assert "without authorization gate" in forbidden.lower()


def test_assembly_downstream_guard_blocks_when_not_accepted():
    contract = _load_contract("assembly_downstream_guard_contract.json")
    forbidden = " ".join(contract.get("forbidden_actions", []))
    assert "execute assembly operations without passing gate" in forbidden.lower()
    assert "execute render operations without passing gate" in forbidden.lower()


def test_evidence_freeze_auditor_can_reject_if_tests_pass():
    contract = _load_contract("evidence_freeze_auditor_contract.json")
    mission = contract.get("mission", "")
    assert "can reject" in mission.lower() or "reject" in mission.lower()
    verdicts = contract.get("canonical_json_output_schema", {}).get(
        "audit_report", {}
    ).get("verdict", "")
    assert "REJECTED" in verdicts
