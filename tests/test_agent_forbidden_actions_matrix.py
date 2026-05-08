"""Tests for Combine V2 Agent Forbidden Actions Matrix — agent_forbidden_actions_matrix.json."""

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

EXPECTED_GLOBAL_FORBIDDEN_KEYS = [
    "generation",
    "retry",
    "visual_acceptance",
    "preview_render",
    "voice_generation",
    "assembly",
    "downstream",
    "production_accepted_true",
    "comfyui_submit",
]


@pytest.fixture(scope="module")
def forbidden_matrix() -> dict:
    """Load the agent_forbidden_actions_matrix.json file."""
    matrix_path = AGENTS_DIR / "agent_forbidden_actions_matrix.json"
    assert matrix_path.exists(), f"File not found: {matrix_path}"
    with open(matrix_path, encoding="utf-8") as f:
        return json.load(f)


class TestForbiddenActionsMatrix:
    """Tests for the forbidden actions matrix structure and content."""

    def test_forbidden_actions_matrix_exists(self, forbidden_matrix: dict) -> None:
        """Verify agent_forbidden_actions_matrix.json exists and is valid JSON."""
        assert isinstance(forbidden_matrix, dict), (
            "Expected forbidden_matrix to be a dict"
        )
        assert "global_forbidden_actions" in forbidden_matrix, (
            "Missing 'global_forbidden_actions' key"
        )
        assert "per_agent_forbidden_actions" in forbidden_matrix, (
            "Missing 'per_agent_forbidden_actions' key"
        )

    def test_global_forbidden_generation(self, forbidden_matrix: dict) -> None:
        """Verify global_forbidden_actions has a 'generation' entry."""
        global_forbidden = forbidden_matrix.get("global_forbidden_actions", {})
        assert "generation" in global_forbidden, (
            "global_forbidden_actions missing 'generation' entry"
        )

    def test_global_forbidden_comfyui_submit(self, forbidden_matrix: dict) -> None:
        """Verify global_forbidden_actions has a 'comfyui_submit' entry."""
        global_forbidden = forbidden_matrix.get("global_forbidden_actions", {})
        assert "comfyui_submit" in global_forbidden, (
            "global_forbidden_actions missing 'comfyui_submit' entry"
        )

    def test_all_forbidden_entry_types(self, forbidden_matrix: dict) -> None:
        """Verify all expected forbidden action keys exist in global_forbidden_actions."""
        global_forbidden = forbidden_matrix.get("global_forbidden_actions", {})
        for key in EXPECTED_GLOBAL_FORBIDDEN_KEYS:
            assert key in global_forbidden, (
                f"global_forbidden_actions missing expected key '{key}'"
            )

    def test_each_entry_has_gate_and_enforcement(
        self, forbidden_matrix: dict
    ) -> None:
        """Verify each global_forbidden_actions entry has 'gate' and 'enforcement'
        fields."""
        global_forbidden = forbidden_matrix.get("global_forbidden_actions", {})
        for key, entry in global_forbidden.items():
            assert "gate" in entry, (
                f"global_forbidden_actions entry '{key}' missing 'gate' field"
            )
            assert "enforcement" in entry, (
                f"global_forbidden_actions entry '{key}' missing 'enforcement' field"
            )

    def test_per_agent_forbidden_exists(self, forbidden_matrix: dict) -> None:
        """Verify per_agent_forbidden_actions exists and has entries for all
        17 agents."""
        per_agent = forbidden_matrix.get("per_agent_forbidden_actions", {})
        assert isinstance(per_agent, dict), (
            "per_agent_forbidden_actions should be a dict"
        )
        for agent_id in EXPECTED_AGENT_IDS:
            assert agent_id in per_agent, (
                f"per_agent_forbidden_actions missing entry for '{agent_id}'"
            )

    def test_no_generation_allowed(self, forbidden_matrix: dict) -> None:
        """Verify the 'generation' entry has enforcement indicating it is blocked."""
        global_forbidden = forbidden_matrix.get("global_forbidden_actions", {})
        generation_entry = global_forbidden.get("generation", {})
        enforcement = generation_entry.get("enforcement", "")
        assert enforcement in (
            "blocked_in_registry_layer",
            "blocked",
            "forbidden",
        ), (
            f"'generation' enforcement should indicate blocking, "
            f"got '{enforcement}'"
        )
