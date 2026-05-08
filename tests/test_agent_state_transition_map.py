"""Tests for Combine V2 Agent State Transition Map — agent_state_transition_map.json."""

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


@pytest.fixture(scope="module")
def state_transition_map() -> dict:
    """Load the agent_state_transition_map.json file."""
    map_path = AGENTS_DIR / "agent_state_transition_map.json"
    assert map_path.exists(), f"File not found: {map_path}"
    with open(map_path, encoding="utf-8") as f:
        return json.load(f)


class TestStateTransitionMap:
    """Tests for the state transition map structure and content."""

    def test_state_transition_map_exists(self, state_transition_map: dict) -> None:
        """Verify agent_state_transition_map.json exists and is valid JSON."""
        assert isinstance(state_transition_map, dict), (
            "Expected state_transition_map to be a dict"
        )
        assert "current_layer_state" in state_transition_map, (
            "Missing 'current_layer_state' key"
        )
        assert "agents" in state_transition_map, "Missing 'agents' key"

    def test_current_layer_state(self, state_transition_map: dict) -> None:
        """Verify current_layer_state is set to agent_registry_operator_review_required."""
        current_state = state_transition_map.get("current_layer_state", "")
        assert current_state == "agent_registry_operator_review_required", (
            f"Expected current_layer_state to be "
            f"'agent_registry_operator_review_required', got '{current_state}'"
        )

    def test_next_allowed_action(self, state_transition_map: dict) -> None:
        """Verify current_layer_next_action is set to
        agent_registry_operator_review_required."""
        next_action = state_transition_map.get("current_layer_next_action", "")
        assert next_action == "agent_registry_operator_review_required", (
            f"Expected current_layer_next_action to be "
            f"'agent_registry_operator_review_required', got '{next_action}'"
        )

    def test_production_accepted_false(self, state_transition_map: dict) -> None:
        """Verify production_accepted is false in the state transition map."""
        assert state_transition_map.get("production_accepted") is False, (
            "state_transition_map 'production_accepted' must be false at this layer"
        )

    def test_no_generation_transition(self, state_transition_map: dict) -> None:
        """Verify no_generation_transition is true."""
        assert state_transition_map.get("no_generation_transition") is True, (
            "no_generation_transition must be true at this layer"
        )

    def test_no_preview_render_transition(self, state_transition_map: dict) -> None:
        """Verify no_preview_render_transition is true."""
        assert state_transition_map.get("no_preview_render_transition") is True, (
            "no_preview_render_transition must be true at this layer"
        )

    def test_no_assembly_transition(self, state_transition_map: dict) -> None:
        """Verify no_assembly_transition is true."""
        assert state_transition_map.get("no_assembly_transition") is True, (
            "no_assembly_transition must be true at this layer"
        )

    def test_all_agents_in_transition_map(self, state_transition_map: dict) -> None:
        """Verify all 17 expected agent IDs appear in the transition map agents list."""
        agents = state_transition_map.get("agents", [])
        agent_ids = {a.get("agent_id") for a in agents}
        for expected_id in EXPECTED_AGENT_IDS:
            assert expected_id in agent_ids, (
                f"Agent '{expected_id}' is missing from state_transition_map agents"
            )
        assert len(agent_ids) == 17, (
            f"Expected 17 agents in transition map, got {len(agent_ids)}"
        )
