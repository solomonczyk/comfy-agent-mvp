"""Tests for Combine V2 Agent Registry layer — agent_registry.json and agent_readiness_report.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
AGENTS_DIR = DATA_ROOT / "output" / "control" / "agents"

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

REQUIRED_FIELDS = [
    "agent_id",
    "name",
    "role",
    "responsibility",
    "dry_run_supported",
    "dangerous_actions",
    "operator_gate_required",
    "readiness_status",
    "next_integration_dependency",
]

AGENTS_WITH_OPERATOR_GATE = [
    "generation_executor_agent",
    "visual_qa_agent",
    "preview_render_agent",
    "assembly_agent",
    "production_acceptance_agent",
]


@pytest.fixture(scope="module")
def agent_registry() -> dict:
    """Load the agent_registry.json file."""
    registry_path = AGENTS_DIR / "agent_registry.json"
    with open(registry_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def readiness_report() -> dict:
    """Load the agent_readiness_report.json file."""
    report_path = AGENTS_DIR / "agent_readiness_report.json"
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


class TestAgentRegistry:
    """Tests for agent_registry.json structure and content."""

    def test_all_core_agents_registered(self, agent_registry: dict) -> None:
        """Verify that exactly 17 agents exist with the expected agent_ids."""
        agents = agent_registry["agents"]
        actual_ids = [a["agent_id"] for a in agents]
        assert len(agents) == 17, f"Expected 17 agents, got {len(agents)}"
        for expected_id in EXPECTED_AGENT_IDS:
            assert expected_id in actual_ids, f"Missing agent_id: {expected_id}"

    def test_all_agents_have_required_fields(self, agent_registry: dict) -> None:
        """Verify each agent in the registry has all required fields."""
        agents = agent_registry["agents"]
        for agent in agents:
            missing = [f for f in REQUIRED_FIELDS if f not in agent]
            assert not missing, (
                f"Agent {agent.get('agent_id', '<unknown>')} is missing "
                f"required fields: {missing}"
            )

    def test_dangerous_actions_mapped(self, agent_registry: dict) -> None:
        """Verify specific agents have the correct dangerous_actions assigned."""
        agents_by_id = {a["agent_id"]: a for a in agent_registry["agents"]}

        # generation_executor has generation + comfyui_submit
        gen_exec = agents_by_id["generation_executor_agent"]
        assert "generation" in gen_exec["dangerous_actions"], (
            "generation_executor_agent missing 'generation' in dangerous_actions"
        )
        assert "comfyui_submit" in gen_exec["dangerous_actions"], (
            "generation_executor_agent missing 'comfyui_submit' in dangerous_actions"
        )

        # visual_qa has visual_acceptance
        vqa = agents_by_id["visual_qa_agent"]
        assert "visual_acceptance" in vqa["dangerous_actions"], (
            "visual_qa_agent missing 'visual_acceptance' in dangerous_actions"
        )

        # correction_planner has retry
        corr = agents_by_id["correction_planner_agent"]
        assert "retry" in corr["dangerous_actions"], (
            "correction_planner_agent missing 'retry' in dangerous_actions"
        )

        # preview_render has preview_render
        preview = agents_by_id["preview_render_agent"]
        assert "preview_render" in preview["dangerous_actions"], (
            "preview_render_agent missing 'preview_render' in dangerous_actions"
        )

        # assembly has assembly
        assembly = agents_by_id["assembly_agent"]
        assert "assembly" in assembly["dangerous_actions"], (
            "assembly_agent missing 'assembly' in dangerous_actions"
        )

        # production_acceptance has production_acceptance
        prod_acc = agents_by_id["production_acceptance_agent"]
        assert "production_acceptance" in prod_acc["dangerous_actions"], (
            "production_acceptance_agent missing 'production_acceptance' "
            "in dangerous_actions"
        )

    def test_operator_gate_agents(self, agent_registry: dict) -> None:
        """Verify exactly 5 agents have operator_gate_required set to true."""
        agents = agent_registry["agents"]
        gated = [a for a in agents if a.get("operator_gate_required") is True]
        gated_ids = sorted(a["agent_id"] for a in gated)
        expected_sorted = sorted(AGENTS_WITH_OPERATOR_GATE)
        assert len(gated) == 5, (
            f"Expected exactly 5 agents with operator_gate_required=true, "
            f"got {len(gated)}"
        )
        assert gated_ids == expected_sorted, (
            f"Expected gated agents {expected_sorted}, got {gated_ids}"
        )

    def test_production_accepted_false(self, agent_registry: dict) -> None:
        """Verify registry.production_accepted is false."""
        assert agent_registry.get("production_accepted") is False, (
            "agent_registry.json production_accepted must be false at this layer"
        )


class TestReadinessReport:
    """Tests for agent_readiness_report.json structure and content."""

    def test_readiness_report(self, readiness_report: dict) -> None:
        """Verify all readiness boolean fields are true and ready_for_next_layer is true."""
        readiness_fields = [
            "all_core_agents_registered",
            "all_agents_have_contracts",
            "all_agents_have_required_fields",
            "dangerous_actions_mapped",
            "dry_run_behavior_defined",
            "dependency_graph_created",
            "execution_matrix_created",
            "forbidden_actions_matrix_created",
            "state_transition_map_created",
            "artifact_map_created",
        ]
        for field in readiness_fields:
            assert readiness_report.get(field) is True, (
                f"Readiness field '{field}' should be True but is "
                f"{readiness_report.get(field)}"
            )

        assert readiness_report.get("ready_for_next_layer") is True, (
            "ready_for_next_layer must be True for the registry layer to be complete"
        )

    def test_production_accepted_false_in_readiness(self, readiness_report: dict) -> None:
        """Verify readiness.production_accepted is false."""
        assert readiness_report.get("production_accepted") is False, (
            "agent_readiness_report.json production_accepted must be false "
            "at this layer"
        )
