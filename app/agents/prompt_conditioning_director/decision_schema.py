"""
Decision Schema

Schema validation for LLM decision output.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DecisionSchema:
    """
    Schema for LLM decision validation.

    Ensures LLM output matches required structure.
    """

    def validate(self, decision: Dict[str, Any]) -> List[str]:
        """
        Validate decision against schema.

        Args:
            decision: LLM decision dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required top-level fields
        required_fields = [
            "decision_type",
            "previous_failure_root_cause",
            "reference_role_assignments",
            "composition_policy",
            "prompt_patch",
            "workflow_patch_requirements",
            "generation_allowed_after_patch",
            "operator_review_required_after_generation",
        ]

        for field in required_fields:
            if field not in decision:
                errors.append(f"Missing required field: {field}")

        # Validate decision_type
        if "decision_type" in decision:
            if decision["decision_type"] != "prompt_conditioning_director_decision":
                errors.append(f"Invalid decision_type: {decision['decision_type']}")

        # Validate previous_failure_root_cause
        if "previous_failure_root_cause" in decision:
            if not isinstance(decision["previous_failure_root_cause"], list):
                errors.append("previous_failure_root_cause must be a list")
            elif len(decision["previous_failure_root_cause"]) == 0:
                errors.append("previous_failure_root_cause cannot be empty")

        # Validate reference_role_assignments
        if "reference_role_assignments" in decision:
            if not isinstance(decision["reference_role_assignments"], list):
                errors.append("reference_role_assignments must be a list")
            else:
                for i, assignment in enumerate(decision["reference_role_assignments"]):
                    if not isinstance(assignment, dict):
                        errors.append(f"reference_role_assignment {i} must be a dict")
                        continue

                    required_assignment_fields = [
                        "reference_path",
                        "allowed_use",
                        "forbidden_use",
                        "weight_policy",
                        "conditioning_region_policy",
                    ]

                    for field in required_assignment_fields:
                        if field not in assignment:
                            errors.append(f"reference_role_assignment {i} missing field: {field}")

                    # Validate allowed_use values
                    if "allowed_use" in assignment:
                        allowed_uses = [
                            "identity",
                            "style",
                            "quality_calibration",
                            "negative",
                            "composition",
                        ]
                        if assignment["allowed_use"] not in allowed_uses:
                            errors.append(
                                f"reference_role_assignment {i} invalid allowed_use: {assignment['allowed_use']}"
                            )

        # Validate composition_policy
        if "composition_policy" in decision:
            if not isinstance(decision["composition_policy"], dict):
                errors.append("composition_policy must be a dict")
            else:
                required_policy_fields = [
                    "required_framing",
                    "forbid_extreme_closeup",
                    "forbid_face_crop",
                    "face_must_be_fully_visible",
                    "head_should_not_touch_frame_edges",
                    "environment_visible",
                ]

                for field in required_policy_fields:
                    if field not in decision["composition_policy"]:
                        errors.append(f"composition_policy missing field: {field}")

                # Validate boolean fields
                boolean_fields = [
                    "forbid_extreme_closeup",
                    "forbid_face_crop",
                    "face_must_be_fully_visible",
                    "head_should_not_touch_frame_edges",
                    "environment_visible",
                ]

                for field in boolean_fields:
                    if field in decision["composition_policy"]:
                        if not isinstance(decision["composition_policy"][field], bool):
                            errors.append(f"composition_policy.{field} must be boolean")

        # Validate prompt_patch
        if "prompt_patch" in decision:
            if not isinstance(decision["prompt_patch"], dict):
                errors.append("prompt_patch must be a dict")
            else:
                required_patch_fields = [
                    "positive_prompt_additions",
                    "negative_prompt_additions",
                    "camera_language",
                    "reference_usage_notes",
                ]

                for field in required_patch_fields:
                    if field not in decision["prompt_patch"]:
                        errors.append(f"prompt_patch missing field: {field}")

                    if field in decision["prompt_patch"]:
                        if not isinstance(decision["prompt_patch"][field], list):
                            errors.append(f"prompt_patch.{field} must be a list")

        # Validate workflow_patch_requirements
        if "workflow_patch_requirements" in decision:
            if not isinstance(decision["workflow_patch_requirements"], list):
                errors.append("workflow_patch_requirements must be a list")

        # Validate boolean gates
        if "generation_allowed_after_patch" in decision:
            if not isinstance(decision["generation_allowed_after_patch"], bool):
                errors.append("generation_allowed_after_patch must be boolean")

        if "operator_review_required_after_generation" in decision:
            if not isinstance(decision["operator_review_required_after_generation"], bool):
                errors.append("operator_review_required_after_generation must be boolean")

        return errors

    def is_valid(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is valid."""
        errors = self.validate(decision)
        return len(errors) == 0
