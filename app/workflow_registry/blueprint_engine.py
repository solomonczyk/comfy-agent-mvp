"""Blueprint engine for workflow registry.

Provides functionality to work with pipeline blueprints,
including stage execution planning, state transition validation,
and operator review point identification.
"""

from __future__ import annotations

from typing import Any

from app.workflow_registry.models import (
    PipelineBlueprint,
    PipelineStage,
    StateTransition,
)


class BlueprintEngine:
    """Engine for working with pipeline blueprints."""

    @staticmethod
    def get_stage(
        blueprint: PipelineBlueprint,
        stage_id: str,
    ) -> PipelineStage | None:
        """Get a stage by ID from the blueprint."""
        for stage in blueprint.stages:
            if stage.stage_id == stage_id:
                return stage
        return None

    @staticmethod
    def get_next_stage(
        blueprint: PipelineBlueprint,
        current_stage_id: str | None = None,
    ) -> PipelineStage | None:
        """Get the next stage in the pipeline order."""
        if not blueprint.stage_order:
            return None

        if current_stage_id is None:
            # Return first stage
            first_stage_id = blueprint.stage_order[0]
            return BlueprintEngine.get_stage(blueprint, first_stage_id)

        try:
            current_index = blueprint.stage_order.index(current_stage_id)
            next_index = current_index + 1
            if next_index < len(blueprint.stage_order):
                next_stage_id = blueprint.stage_order[next_index]
                return BlueprintEngine.get_stage(blueprint, next_stage_id)
        except ValueError:
            pass

        return None

    @staticmethod
    def get_previous_stage(
        blueprint: PipelineBlueprint,
        current_stage_id: str,
    ) -> PipelineStage | None:
        """Get the previous stage in the pipeline order."""
        if not blueprint.stage_order:
            return None

        try:
            current_index = blueprint.stage_order.index(current_stage_id)
            prev_index = current_index - 1
            if prev_index >= 0:
                prev_stage_id = blueprint.stage_order[prev_index]
                return BlueprintEngine.get_stage(blueprint, prev_stage_id)
        except ValueError:
            pass

        return None

    @staticmethod
    def is_operator_review_point(
        blueprint: PipelineBlueprint,
        stage_id: str,
    ) -> bool:
        """Check if a stage is an operator review point."""
        stage = BlueprintEngine.get_stage(blueprint, stage_id)
        if stage:
            return stage.operator_review_point
        return stage_id in blueprint.operator_review_points

    @staticmethod
    def get_operator_review_points(
        blueprint: PipelineBlueprint,
    ) -> list[PipelineStage]:
        """Get all operator review points in the blueprint."""
        review_points: list[PipelineStage] = []
        for stage in blueprint.stages:
            if stage.operator_review_point:
                review_points.append(stage)
        return review_points

    @staticmethod
    def get_required_artifacts_for_stage(
        blueprint: PipelineBlueprint,
        stage_id: str,
    ) -> list[str]:
        """Get required artifacts for a specific stage."""
        stage = BlueprintEngine.get_stage(blueprint, stage_id)
        if stage:
            return stage.required_artifacts
        return []

    @staticmethod
    def get_optional_artifacts_for_stage(
        blueprint: PipelineBlueprint,
        stage_id: str,
    ) -> list[str]:
        """Get optional artifacts for a specific stage."""
        stage = BlueprintEngine.get_stage(blueprint, stage_id)
        if stage:
            return stage.optional_artifacts
        return []

    @staticmethod
    def validate_state_transition(
        blueprint: PipelineBlueprint,
        from_state: str,
        to_state: str,
        trigger_action: str,
    ) -> bool:
        """Validate if a state transition is allowed by the blueprint."""
        for transition in blueprint.state_transitions:
            if (
                transition.from_state == from_state
                and transition.to_state == to_state
                and transition.trigger_action == trigger_action
            ):
                return True
        return False

    @staticmethod
    def get_allowed_transitions_from_state(
        blueprint: PipelineBlueprint,
        from_state: str,
    ) -> list[StateTransition]:
        """Get all allowed transitions from a given state."""
        return [
            t
            for t in blueprint.state_transitions
            if t.from_state == from_state
        ]

    @staticmethod
    def is_gate_required_for_action(
        blueprint: PipelineBlueprint,
        action: str,
    ) -> bool:
        """Check if a gate is required for a given action."""
        return action in blueprint.dangerous_action_gates

    @staticmethod
    def get_execution_plan(
        blueprint: PipelineBlueprint,
        start_stage_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate an execution plan for the blueprint."""
        plan: dict[str, Any] = {
            "blueprint_id": blueprint.blueprint_id,
            "stages_to_execute": [],
            "review_points": [],
            "gate_requirements": [],
        }

        start_index = 0
        if start_stage_id:
            try:
                start_index = blueprint.stage_order.index(start_stage_id)
            except ValueError:
                start_index = 0

        for i in range(start_index, len(blueprint.stage_order)):
            stage_id = blueprint.stage_order[i]
            stage = BlueprintEngine.get_stage(blueprint, stage_id)
            if stage:
                stage_info = {
                    "stage_id": stage.stage_id,
                    "stage_name": stage.stage_name,
                    "stage_type": stage.stage_type,
                    "order": i,
                    "gate_required": stage.gate_required,
                    "operator_review_point": stage.operator_review_point,
                }
                plan["stages_to_execute"].append(stage_info)

                if stage.operator_review_point:
                    plan["review_points"].append(stage_id)

                if stage.gate_required:
                    plan["gate_requirements"].append(stage_id)

        return plan

    @staticmethod
    def validate_blueprint_integrity(
        blueprint: PipelineBlueprint,
    ) -> list[str]:
        """Validate the integrity of a pipeline blueprint."""
        errors: list[str] = []

        # Check that all stage_order references exist
        stage_ids = {stage.stage_id for stage in blueprint.stages}
        for stage_id in blueprint.stage_order:
            if stage_id not in stage_ids:
                errors.append(
                    f"stage_order references unknown stage_id: {stage_id}"
                )

        # Check that all operator_review_points reference existing stages
        for review_point in blueprint.operator_review_points:
            if review_point not in stage_ids:
                errors.append(
                    f"operator_review_points references unknown stage_id: {review_point}"
                )

        # Check that all dangerous_action_gates reference existing stages
        for gate_stage in blueprint.dangerous_action_gates:
            if gate_stage not in stage_ids:
                errors.append(
                    f"dangerous_action_gates references unknown stage_id: {gate_stage}"
                )

        # Check state transitions reference valid states
        all_states = set()
        for transition in blueprint.state_transitions:
            all_states.add(transition.from_state)
            all_states.add(transition.to_state)

        # Basic validation - states should be defined somewhere if transitions exist
        if blueprint.state_transitions and not all_states:
            errors.append("State transitions defined but no valid states found")

        return errors
