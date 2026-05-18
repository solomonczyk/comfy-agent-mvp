"""
Tests for app/visual_generation/gate_plan.py and gate_authorization.py
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root(tmp_path):
    (tmp_path / "output" / "control").mkdir(parents=True)
    return tmp_path


def test_gate_plan_builds_artifacts(project_root):
    from app.visual_generation.gate_plan import GatePlanBuilder

    builder = GatePlanBuilder(project_root)
    plan = builder.build(max_generations=1)

    gate_dir = project_root / "output" / "control" / "controlled_visual_generation_gate"
    assert (gate_dir / "generation_gate_plan.json").exists()
    assert (gate_dir / "generation_stop_conditions.json").exists()

    assert plan["max_generations"] == 1
    assert plan["stop_conditions"]["retry_authorized"] is False
    assert plan["stop_conditions"]["second_generation_allowed"] is False
    assert plan["stop_conditions"]["visual_qa_acceptance_allowed"] is False
    assert plan["stop_conditions"]["assembly_allowed"] is False
    assert plan["stop_conditions"]["production_accepted"] is False
    assert plan["generation_authorized"] is False


def test_gate_plan_max_generations_enforced(project_root):
    from app.visual_generation.gate_plan import GatePlanBuilder

    builder = GatePlanBuilder(project_root)
    plan = builder.build(max_generations=1)
    assert plan["max_generations"] == 1


def test_stop_conditions_artifact_content(project_root):
    from app.visual_generation.gate_plan import GatePlanBuilder

    builder = GatePlanBuilder(project_root)
    builder.build()

    gate_dir = project_root / "output" / "control" / "controlled_visual_generation_gate"
    with open(gate_dir / "generation_stop_conditions.json", encoding="utf-8") as f:
        stop = json.load(f)

    assert stop["stop_after_first_generation"] is True
    assert stop["max_generations"] == 1
    assert stop["retry_authorized"] is False
    assert stop["second_generation_authorized"] is False
    assert stop["visual_qa_acceptance_authorized"] is False
    assert stop["assembly_authorized"] is False
    assert stop["production_accepted"] is False


def test_gate_authorization_create(project_root):
    from app.visual_generation.gate_authorization import GateAuthorization

    auth = GateAuthorization(project_root)
    doc = auth.create(max_generations=1)

    gate_dir = project_root / "output" / "control" / "controlled_visual_generation_gate"
    assert (gate_dir / "generation_gate_authorization.json").exists()
    assert doc["generation_authorized"] is True
    assert doc["max_generations"] == 1
    assert doc["retry_authorized"] is False
    assert doc["second_generation_allowed"] is False
    assert doc["production_accepted"] is False


def test_gate_authorization_is_authorized(project_root):
    from app.visual_generation.gate_authorization import GateAuthorization

    auth = GateAuthorization(project_root)
    assert auth.is_authorized() is False
    auth.create()
    assert auth.is_authorized() is True


def test_gate_authorization_load_missing(project_root):
    from app.visual_generation.gate_authorization import GateAuthorization

    auth = GateAuthorization(project_root)
    data = auth.load()
    assert data == {}
