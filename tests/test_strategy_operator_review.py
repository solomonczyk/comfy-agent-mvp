"""
Tests for app/visual_strategy/operator_review.py
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def project_root(tmp_path):
    """Minimal project root with required strategy artifacts."""
    strategy_dir = tmp_path / "output" / "control" / "fresh_visual_strategy"
    strategy_dir.mkdir(parents=True)

    readiness = {
        "readiness_assessment": {"overall_readiness": "ready_for_operator_review"},
        "readiness_checklist": {"all_artifacts_valid": True},
        "policy_readiness": {"qa_repairability_gate_active": True},
    }
    (strategy_dir / "fresh_visual_strategy_readiness_report.json").write_text(
        json.dumps(readiness), encoding="utf-8"
    )

    review_packet_src = {
        "strategy_summary": {"objective": "Fresh visual generation strategy"},
    }
    (strategy_dir / "visual_strategy_operator_review_packet.json").write_text(
        json.dumps(review_packet_src), encoding="utf-8"
    )

    brief = {"strategy_id": "test"}
    (strategy_dir / "fresh_visual_strategy_brief.json").write_text(
        json.dumps(brief), encoding="utf-8"
    )

    return tmp_path


def test_build_review_packet_creates_files(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    packet = builder.build_review_packet()

    assert (builder.review_dir / "operator_review_packet.json").exists()
    assert packet["generation_allowed"] is False
    assert packet["production_accepted"] is False
    assert "accepted_for_controlled_generation_gate_planning" in [
        opt["verdict"] for opt in packet["operator_decision_options"]
    ]


def test_build_decision_schema_creates_file(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    schema = builder.build_decision_schema()

    assert (builder.review_dir / "operator_decision_schema.json").exists()
    assert "operator_verdict" in schema["required_fields"]
    assert "human_operator" in schema["required_fields"]["decision_source"]["allowed_values"]


def test_process_valid_acceptance(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    result = builder.process_operator_decision(
        operator_verdict="accepted_for_controlled_generation_gate_planning",
        operator_source="human_operator",
        operator_name="TestOperator",
    )

    assert result["validation_report"]["decision_valid"] is True
    assert len(result["validation_report"]["errors"]) == 0
    assert result["routing_decision"]["next_state"] == "controlled_visual_generation_gate_planning_required"
    assert result["proof"]["generation_authorized_by_strategy_review"] is False
    assert result["proof"]["production_accepted"] is False
    assert result["proof"]["retry_attempted"] is False


def test_process_invalid_verdict_rejected(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    result = builder.process_operator_decision(
        operator_verdict="not_a_valid_verdict",
        operator_source="human_operator",
    )

    assert result["validation_report"]["decision_valid"] is False
    assert len(result["validation_report"]["errors"]) > 0
    assert result["routing_decision"]["next_state"] == "fresh_visual_strategy_operator_review_required"


def test_process_invalid_source_rejected(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    result = builder.process_operator_decision(
        operator_verdict="accepted_for_controlled_generation_gate_planning",
        operator_source="ai_agent",
    )

    assert result["validation_report"]["decision_valid"] is False
    assert any("decision_source" in e for e in result["validation_report"]["errors"])


def test_generation_never_authorized_by_strategy_review(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    for verdict in [
        "accepted_for_controlled_generation_gate_planning",
        "rejected_revision_required",
        "modification_required",
    ]:
        result = builder.process_operator_decision(
            operator_verdict=verdict,
            operator_source="human_operator",
        )
        assert result["proof"]["generation_authorized_by_strategy_review"] is False
        assert result["proof"]["production_accepted"] is False


def test_all_review_artifacts_created(project_root):
    from app.visual_strategy.operator_review import StrategyOperatorReviewBuilder

    builder = StrategyOperatorReviewBuilder(project_root)
    builder.build_review_packet()
    builder.build_decision_schema()
    builder.process_operator_decision(
        operator_verdict="accepted_for_controlled_generation_gate_planning",
        operator_source="human_operator",
    )

    expected_files = [
        "operator_review_packet.json",
        "operator_decision_schema.json",
        "operator_decision_validation_report.json",
        "operator_review_routing_decision.json",
        "operator_review_state_transition_report.json",
        "operator_review_proof.json",
    ]
    for fname in expected_files:
        assert (builder.review_dir / fname).exists(), f"Missing: {fname}"
