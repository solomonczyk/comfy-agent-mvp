"""Tests for Combine V2 Agent Contracts — each agent's contract JSON file."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
AGENTS_DIR = DATA_ROOT / "output" / "control" / "agents"
CONTRACTS_DIR = AGENTS_DIR / "contracts"

EXPECTED_AGENT_IDS = [
    "brief_intake_agent",
    "director_planner_agent",
    "shot_planner_agent",
    "workflow_authoring_agent",
    "workflow_validation_agent",
    "asset_resolver_agent",
    "generation_executor_agent",
    "output_collector_agent",
    "visual_qa_agent",
    "correction_planner_agent",
    "editorial_timeline_agent",
    "subtitle_agent",
    "transition_agent",
    "voice_casting_agent",
    "preview_render_agent",
    "assembly_agent",
    "production_acceptance_agent",
]

REQUIRED_CONTRACT_FIELDS = [
    "agent_id",
    "role",
    "responsibility",
    "input_contract",
    "output_contract",
    "allowed_actions",
    "forbidden_actions",
    "required_artifacts",
    "owned_artifacts",
    "state_inputs",
    "state_outputs",
    "dry_run_supported",
    "dangerous_actions",
    "operator_gate_required",
    "tests_required",
    "handoff_to_next_agents",
    "acceptance_criteria",
    "exit_criteria",
    "blocked_conditions",
]


@pytest.fixture(scope="module")
def contract_file_paths() -> list[Path]:
    """Return sorted list of all contract JSON file paths."""
    return sorted(CONTRACTS_DIR.glob("*.json"))


@pytest.fixture(scope="module")
def loaded_contracts() -> dict[str, dict]:
    """Load all contract files into a dict keyed by agent_id."""
    contracts = {}
    for contract_path in sorted(CONTRACTS_DIR.glob("*.json")):
        with open(contract_path, encoding="utf-8") as f:
            contract = json.load(f)
            contracts[contract["agent_id"]] = contract
    return contracts


class TestContractsExistence:
    """Tests for contract file existence and completeness."""

    def test_contracts_exist_for_all_agents(
        self, contract_file_paths: list[Path]
    ) -> None:
        """Verify the contracts directory has exactly 17 agent contract JSON files."""
        assert (
            len(contract_file_paths) == 17
        ), f"Expected 17 contract files, got {len(contract_file_paths)}"


class TestContractFields:
    """Tests for per-contract field requirements."""

    def test_required_contract_fields(self, loaded_contracts: dict[str, dict]) -> None:
        """Verify each contract has all required fields present."""
        for agent_id, contract in loaded_contracts.items():
            missing = [f for f in REQUIRED_CONTRACT_FIELDS if f not in contract]
            assert not missing, (
                f"Contract for '{agent_id}' is missing required fields: {missing}"
            )

    def test_contract_not_stub(self, loaded_contracts: dict[str, dict]) -> None:
        """Verify each contract has at least 1 allowed_action and 1 acceptance_criterion."""
        for agent_id, contract in loaded_contracts.items():
            allowed = contract.get("allowed_actions", [])
            assert len(allowed) >= 1, (
                f"Contract for '{agent_id}' has no allowed_actions — "
                f"likely a stub"
            )
            criteria = contract.get("acceptance_criteria", [])
            assert len(criteria) >= 1, (
                f"Contract for '{agent_id}' has no acceptance_criteria — "
                f"likely a stub"
            )

    def test_generation_executor_forbidden_actions(
        self, loaded_contracts: dict[str, dict]
    ) -> None:
        """Verify generation_executor_agent's forbidden_actions includes
        retry_without_authorization."""
        gen_exec = loaded_contracts.get("generation_executor_agent")
        assert gen_exec is not None, "generation_executor_agent contract not found"
        forbidden = gen_exec.get("forbidden_actions", [])
        assert "retry_without_authorization" in forbidden, (
            "generation_executor_agent should forbid 'retry_without_authorization'"
        )

    def test_production_acceptance_terminal(
        self, loaded_contracts: dict[str, dict]
    ) -> None:
        """Verify production_acceptance_agent's handoff_to_next_agents is an empty list."""
        prod_acc = loaded_contracts.get("production_acceptance_agent")
        assert prod_acc is not None, (
            "production_acceptance_agent contract not found"
        )
        handoff = prod_acc.get("handoff_to_next_agents", [])
        assert handoff == [], (
            "production_acceptance_agent should have empty handoff_to_next_agents "
            "since it is the terminal agent"
        )

    def test_contract_dry_run_consistency(
        self, loaded_contracts: dict[str, dict]
    ) -> None:
        """Verify dry_run_supported values match expectations for key agents."""
        gen_exec = loaded_contracts.get("generation_executor_agent", {})
        assert gen_exec.get("dry_run_supported") is False, (
            "generation_executor_agent should have dry_run_supported=false"
        )

        preview = loaded_contracts.get("preview_render_agent", {})
        assert preview.get("dry_run_supported") is True, (
            "preview_render_agent should have dry_run_supported=true"
        )

    def test_no_production_accepted_in_contracts(
        self, loaded_contracts: dict[str, dict]
    ) -> None:
        """Verify no contract has production_accepted set to true."""
        for agent_id, contract in loaded_contracts.items():
            if "production_accepted" in contract:
                assert contract["production_accepted"] is False, (
                    f"Contract for '{agent_id}' has production_accepted=true, "
                    f"which should not be set at this layer"
                )
