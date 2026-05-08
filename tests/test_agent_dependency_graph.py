"""Tests for Combine V2 Agent Dependency Graph — agent_dependency_graph.json."""

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
def dependency_graph() -> dict:
    """Load the agent_dependency_graph.json file."""
    graph_path = AGENTS_DIR / "agent_dependency_graph.json"
    assert graph_path.exists(), f"File not found: {graph_path}"
    with open(graph_path, encoding="utf-8") as f:
        return json.load(f)


class TestDependencyGraph:
    """Tests for the agent dependency graph structure and content."""

    def test_dependency_graph_exists(self, dependency_graph: dict) -> None:
        """Verify agent_dependency_graph.json exists and is valid JSON."""
        assert isinstance(dependency_graph, dict), (
            "Expected dependency_graph to be a dict"
        )
        assert "production_pipeline_order" in dependency_graph, (
            "Missing 'production_pipeline_order' key"
        )
        assert "edges" in dependency_graph, "Missing 'edges' key"

    def test_all_agents_in_pipeline(self, dependency_graph: dict) -> None:
        """Verify the production pipeline order contains all 17 expected agent IDs."""
        pipeline = dependency_graph.get("production_pipeline_order", [])
        pipeline_ids = [entry["agent_id"] for entry in pipeline]
        for expected_id in EXPECTED_AGENT_IDS:
            assert expected_id in pipeline_ids, (
                f"Agent '{expected_id}' is missing from production_pipeline_order"
            )
        assert len(pipeline_ids) == 17, (
            f"Expected 17 agents in pipeline order, got {len(pipeline_ids)}"
        )

    def test_correct_pipeline_order(self, dependency_graph: dict) -> None:
        """Verify the first 2 and last 2 agents in the pipeline order are correct."""
        pipeline = dependency_graph.get("production_pipeline_order", [])
        assert len(pipeline) >= 4, (
            f"Pipeline too short to check first/last positions: {len(pipeline)}"
        )

        # First 2
        assert pipeline[0]["agent_id"] == "brief_intake_agent", (
            f"First agent should be brief_intake_agent, got {pipeline[0]['agent_id']}"
        )
        assert pipeline[1]["agent_id"] == "director_planner_agent", (
            f"Second agent should be director_planner_agent, "
            f"got {pipeline[1]['agent_id']}"
        )

        # Last 2
        assert pipeline[-2]["agent_id"] == "assembly_agent", (
            f"Second-to-last agent should be assembly_agent, "
            f"got {pipeline[-2]['agent_id']}"
        )
        assert pipeline[-1]["agent_id"] == "production_acceptance_agent", (
            f"Last agent should be production_acceptance_agent, "
            f"got {pipeline[-1]['agent_id']}"
        )

    def test_edges_defined(self, dependency_graph: dict) -> None:
        """Verify at least 17 edges are defined in the dependency graph."""
        edges = dependency_graph.get("edges", [])
        assert len(edges) >= 17, (
            f"Expected at least 17 edges, got {len(edges)}"
        )

    def test_conditional_paths(self, dependency_graph: dict) -> None:
        """Verify conditional paths exist for visual_qa_agent branches."""
        conditional_paths = dependency_graph.get("conditional_paths", [])

        # Check visual_qa_agent -> correction_planner (rejected)
        rejected_path = any(
            p.get("from") == "visual_qa_agent"
            and p.get("branch") == "rejected"
            and p.get("to") == "correction_planner_agent"
            for p in conditional_paths
        )
        assert rejected_path, (
            "Missing conditional path: visual_qa_agent (rejected) -> "
            "correction_planner_agent"
        )

        # Check visual_qa_agent -> editorial_timeline (accepted)
        accepted_path = any(
            p.get("from") == "visual_qa_agent"
            and p.get("branch") == "accepted"
            and p.get("to") == "editorial_timeline_agent"
            for p in conditional_paths
        )
        assert accepted_path, (
            "Missing conditional path: visual_qa_agent (accepted) -> "
            "editorial_timeline_agent"
        )

    def test_parallel_group_exists(self, dependency_graph: dict) -> None:
        """Verify editorial_parallel group exists with subtitle, transition, and
        voice_casting agents."""
        parallel_groups = dependency_graph.get("parallel_groups", [])
        editorial_group = None
        for group in parallel_groups:
            if group.get("group_id") == "editorial_parallel":
                editorial_group = group
                break

        assert editorial_group is not None, (
            "Missing parallel group 'editorial_parallel'"
        )
        group_agents = editorial_group.get("agents", [])
        for agent_id in ("subtitle_agent", "transition_agent", "voice_casting_agent"):
            assert agent_id in group_agents, (
                f"editorial_parallel group missing agent '{agent_id}'"
            )

    def test_no_generation_downstream_edges(self, dependency_graph: dict) -> None:
        """Verify no edge has a 'to' field pointing to 'generation' or 'downstream',
        which are not valid agent_ids."""
        edges = dependency_graph.get("edges", [])
        invalid_targets = {"generation", "downstream"}
        for edge in edges:
            target = edge.get("to", "")
            assert target not in invalid_targets, (
                f"Edge from '{edge.get('from')}' has invalid target '{target}' — "
                f"these are not agent_ids"
            )
