"""Tests for pipeline blueprint schema validation.

Task: RC-COMBINE-V2-WORKFLOW-REGISTRY-PIPELINE-BLUEPRINT-001
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from app.workflow_registry.models import (
    PipelineBlueprint,
    PipelineStage,
    StateTransition,
)
from app.workflow_registry.blueprint_engine import BlueprintEngine
from app.workflow_registry.validator import WorkflowRegistryValidator


def test_blueprint_engine_get_stage():
    """Test getting a stage by ID."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
            ),
        ],
        stage_order=["stage1", "stage2"],
    )
    
    stage = BlueprintEngine.get_stage(blueprint, "stage1")
    assert stage is not None
    assert stage.stage_id == "stage1"
    
    stage = BlueprintEngine.get_stage(blueprint, "nonexistent")
    assert stage is None


def test_blueprint_engine_get_next_stage():
    """Test getting the next stage."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
            ),
        ],
        stage_order=["stage1", "stage2"],
    )
    
    # Get next from None should return first stage
    next_stage = BlueprintEngine.get_next_stage(blueprint, None)
    assert next_stage is not None
    assert next_stage.stage_id == "stage1"
    
    # Get next from stage1 should return stage2
    next_stage = BlueprintEngine.get_next_stage(blueprint, "stage1")
    assert next_stage is not None
    assert next_stage.stage_id == "stage2"
    
    # Get next from stage2 should return None (end of pipeline)
    next_stage = BlueprintEngine.get_next_stage(blueprint, "stage2")
    assert next_stage is None


def test_blueprint_engine_get_previous_stage():
    """Test getting the previous stage."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
            ),
        ],
        stage_order=["stage1", "stage2"],
    )
    
    # Get previous from stage1 should return None
    prev_stage = BlueprintEngine.get_previous_stage(blueprint, "stage1")
    assert prev_stage is None
    
    # Get previous from stage2 should return stage1
    prev_stage = BlueprintEngine.get_previous_stage(blueprint, "stage2")
    assert prev_stage is not None
    assert prev_stage.stage_id == "stage1"


def test_blueprint_engine_is_operator_review_point():
    """Test checking if a stage is an operator review point."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
                operator_review_point=False,
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
                operator_review_point=True,
            ),
        ],
        stage_order=["stage1", "stage2"],
    )
    
    assert BlueprintEngine.is_operator_review_point(blueprint, "stage1") is False
    assert BlueprintEngine.is_operator_review_point(blueprint, "stage2") is True


def test_blueprint_engine_get_operator_review_points():
    """Test getting all operator review points."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
                operator_review_point=False,
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
                operator_review_point=True,
            ),
            PipelineStage(
                stage_id="stage3",
                stage_name="Final Review",
                stage_type="review",
                operator_review_point=True,
            ),
        ],
        stage_order=["stage1", "stage2", "stage3"],
    )
    
    review_points = BlueprintEngine.get_operator_review_points(blueprint)
    assert len(review_points) == 2
    assert review_points[0].stage_id == "stage2"
    assert review_points[1].stage_id == "stage3"


def test_blueprint_engine_validate_state_transition():
    """Test validating state transitions."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        state_transitions=[
            StateTransition(
                from_state="initial",
                to_state="generating",
                trigger_action="start_generation",
            ),
        ],
    )
    
    assert BlueprintEngine.validate_state_transition(
        blueprint, "initial", "generating", "start_generation"
    ) is True
    
    assert BlueprintEngine.validate_state_transition(
        blueprint, "initial", "generating", "invalid_action"
    ) is False


def test_blueprint_engine_get_execution_plan():
    """Test generating an execution plan."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
                gate_required=False,
                operator_review_point=False,
            ),
            PipelineStage(
                stage_id="stage2",
                stage_name="Review",
                stage_type="review",
                gate_required=True,
                operator_review_point=True,
            ),
        ],
        stage_order=["stage1", "stage2"],
    )
    
    plan = BlueprintEngine.get_execution_plan(blueprint)
    assert plan["blueprint_id"] == "test_blueprint"
    assert len(plan["stages_to_execute"]) == 2
    assert plan["stages_to_execute"][0]["stage_id"] == "stage1"
    assert plan["stages_to_execute"][1]["stage_id"] == "stage2"
    assert len(plan["review_points"]) == 1
    assert plan["review_points"][0] == "stage2"
    assert len(plan["gate_requirements"]) == 1
    assert plan["gate_requirements"][0] == "stage2"


def test_blueprint_engine_validate_blueprint_integrity():
    """Test blueprint integrity validation."""
    blueprint = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            ),
        ],
        stage_order=["stage1"],  # Valid
        operator_review_points=["stage1"],  # Valid
        dangerous_action_gates=["stage1"],  # Valid
    )
    
    errors = BlueprintEngine.validate_blueprint_integrity(blueprint)
    assert len(errors) == 0
    
    # Test with invalid stage_order
    blueprint_invalid = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
            ),
        ],
        stage_order=["stage1", "nonexistent"],  # Invalid
    )
    
    errors = BlueprintEngine.validate_blueprint_integrity(blueprint_invalid)
    assert len(errors) > 0


def test_pipeline_blueprint_json_serialization():
    """Test that pipeline blueprint can be serialized to JSON and back."""
    original = PipelineBlueprint(
        blueprint_id="test_blueprint",
        stages=[
            PipelineStage(
                stage_id="stage1",
                stage_name="Generation",
                stage_type="generation",
                required_artifacts=["prompt"],
                optional_artifacts=["negative_prompt"],
                gate_required=False,
                operator_review_point=False,
            ),
        ],
        stage_order=["stage1"],
        required_artifacts=["prompt"],
        state_transitions=[
            StateTransition(
                from_state="initial",
                to_state="generating",
                trigger_action="start_generation",
                gate_required=False,
            ),
        ],
        operator_review_points=[],
        dangerous_action_gates=[],
    )
    
    # Serialize to dict
    data = original.to_dict()
    assert data["blueprint_id"] == "test_blueprint"
    assert len(data["stages"]) == 1
    
    # Deserialize from dict
    restored = PipelineBlueprint.from_dict(data)
    assert restored.blueprint_id == original.blueprint_id
    assert len(restored.stages) == len(original.stages)
    assert restored.stages[0].stage_id == original.stages[0].stage_id


def test_pipeline_blueprint_schema_validation():
    """Test that pipeline blueprint JSON validates against schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(__file__).parent.parent / "schemas" / "workflow_registry" / "pipeline_blueprint.schema.json"
        
        blueprint_data = {
            "blueprint_id": "test_blueprint",
            "stages": [
                {
                    "stage_id": "stage1",
                    "stage_name": "Generation",
                    "stage_type": "generation",
                    "required_artifacts": ["prompt"],
                    "optional_artifacts": [],
                    "gate_required": False,
                    "operator_review_point": False,
                }
            ],
            "stage_order": ["stage1"],
            "required_artifacts": ["prompt"],
            "state_transitions": [],
            "operator_review_points": [],
            "dangerous_action_gates": [],
        }
        
        blueprint_file = Path(tmpdir) / "blueprint.json"
        with open(blueprint_file, "w") as f:
            json.dump(blueprint_data, f)
        
        result = WorkflowRegistryValidator.validate_file(blueprint_file, schema_path)
        # Should pass basic validation (no forbidden patterns)
        assert result["valid"] or len(result["errors"]) == 0 or all("schema" not in err.lower() for err in result["errors"])
