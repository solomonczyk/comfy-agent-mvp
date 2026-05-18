"""
Tests for app/visual_generation/state_router.py
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True)

    # Seed state.json
    state = {
        "current_state": "controlled_visual_generation_gate_planning_required",
        "next_allowed_action": "controlled_visual_generation_gate_planning_required",
        "production_accepted": False,
        "retry_attempted": False,
    }
    (control_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Seed artifact_index.json
    index = {
        "current_state": "controlled_visual_generation_gate_planning_required",
        "stage_results": [],
    }
    (control_dir / "artifact_index.json").write_text(json.dumps(index), encoding="utf-8")

    # Seed episode_ledger.json
    (control_dir / "episode_ledger.json").write_text("[]", encoding="utf-8")

    return tmp_path


def test_route_success_state(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    manifest = {
        "generation_performed": True,
        "generation_count": 1,
        "prompt_id": "abc123",
        "generated_assets": [{"path": "/some/file.png", "exists": True}],
    }
    proof = {"generation_performed": True}

    state = router.route_success(manifest, proof)

    assert state["current_state"] == "fresh_visual_candidate_operator_review_required"
    assert state["next_allowed_action"] == "fresh_visual_candidate_operator_review_required"
    assert state["generation_performed"] is True
    assert state["generation_count"] == 1
    assert state["retry_attempted"] is False
    assert state["production_accepted"] is False


def test_route_success_updates_state_json(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    router.route_success({"prompt_id": "x", "generated_assets": []}, {})

    state_path = project_root / "output" / "control" / "state.json"
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    assert state["current_state"] == "fresh_visual_candidate_operator_review_required"
    assert state["production_accepted"] is False


def test_route_success_updates_artifact_index(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    router.route_success({"prompt_id": "x", "generated_assets": []}, {})

    idx_path = project_root / "output" / "control" / "artifact_index.json"
    with open(idx_path, encoding="utf-8") as f:
        idx = json.load(f)

    assert idx["current_state"] == "fresh_visual_candidate_operator_review_required"
    assert len(idx["stage_results"]) == 1
    stage = idx["stage_results"][0]
    assert stage["metadata"]["retry_attempted"] is False
    assert stage["metadata"]["second_generation_attempted"] is False
    assert stage["metadata"]["production_accepted"] is False


def test_route_success_appends_episode_ledger(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    router.route_success({"prompt_id": "p1", "generated_assets": []}, {})

    ledger_path = project_root / "output" / "control" / "episode_ledger.json"
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    assert len(ledger) == 1
    entry = ledger[0]
    assert entry["event_type"] == "fresh_visual_candidate_generation"
    assert entry["retry_attempted"] is False
    assert entry["production_accepted"] is False


def test_route_blocker_state(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    preflight_report = {
        "preflight_passed": False,
        "blockers": ["ComfyUI unreachable at 127.0.0.1:8188"],
        "checks": {},
    }
    state = router.route_blocker(preflight_report)

    assert state["current_state"] == "controlled_visual_generation_blocked"
    assert state["next_allowed_action"] == "controlled_visual_generation_blocker_review_required"
    assert state["generation_performed"] is False
    assert state["production_accepted"] is False


def test_route_execution_failure_state(project_root):
    from app.visual_generation.state_router import GenerationStateRouter

    router = GenerationStateRouter(project_root)
    exec_report = {
        "failure": True,
        "failure_reason": "ComfyUI timeout",
        "generation_count": 1,
    }
    state = router.route_execution_failure(exec_report)

    assert state["current_state"] == "fresh_visual_generation_result_reconciliation_required"
    assert state["retry_attempted"] is False
    assert state["production_accepted"] is False
