"""
Test: combine-review-updated-corrective-retry-v4-implementation-plan
Task ID: RC-COMBINE-V2-2781-2840

Tests the operator review gate for updated Retry V4 implementation plan.
Covers:
- approval_branch: true
- rejection_branch: true
- missing_updated_plan_blocks: true
- invalid_state_blocks: true
- runtime_generation_forbidden: true
- comfyui_submit_forbidden: true
- retry_forbidden: true
- visual_qa_forbidden: true
- assembly_forbidden: true
- downstream_forbidden: true
- production_accepted_false: true
- state_transition_correct_on_approval: true
- state_transition_correct_on_rejection: true
- canonical_artifacts_updated: true
"""

import pytest
import json
from pathlib import Path
from argparse import Namespace


class TestCombineCorrectiveRetryV4UpdatedImplementationPlanReview:
    """Test suite for RC-COMBINE-V2-2781-2840"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with required artifacts."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create updated implementation plan
        updated_plan = {
            "task_id": "RC-COMBINE-V2-2721-2780",
            "plan_type": "corrective_retry_v4_updated_implementation_plan",
            "stage": "corrective_retry_v4_retry_implementation_plan_update_required",
            "shot_id": "shot02",
            "timestamp": "2026-05-07T06:21:11.742760+00:00",
            "source_visual_qa_failed_reasons": ["excessive_empty_space", "subject_too_small"],
            "approved_visual_correction_plan_id": "RC-COMBINE-V2-2721-2780",
            "target_shot_id": "shot02",
            "runtime_saveimage_prefix": "combine_v2_corrective_retry_v4_shot02",
            "collector_uses_runtime_saveimage_prefix": True,
            "old_shot01_outputs_forbidden": True,
            "stub_outputs_forbidden": True,
            "production_accepted": False,
            "prompt_patch": {
                "positive_prompt_additions": ["medium shot", "subject dominant"],
                "negative_prompt_additions": ["tiny person", "distant subject"],
                "source": "approved_visual_correction_plan"
            },
            "pre_submit_validation_contract": {
                "prompt_patch_present": True,
                "subject_scale_requirements_present": True,
                "empty_space_requirements_present": True,
                "composition_requirements_present": True,
                "runtime_prefix_consistency_required": True,
                "max_generations": 1,
                "dry_run_for_preflight_only": True,
                "real_submit_requires_separate_operator_authorization": True
            },
            "post_submit_validation_contract": {
                "asset_exists": True,
                "asset_readable": True,
                "sha256_present": True,
                "stub_asset_detected": False,
                "old_shot01_asset_used": False,
                "runtime_prefix_match_required": True,
                "visual_qa_required_after_generation": True,
                "production_accepted": False
            },
            "generation_gate": {
                "generation_allowed": False,
                "comfyui_submit_allowed": False,
                "retry_execution_allowed": False,
                "next_gate": "operator_retry_v4_updated_implementation_plan_review_required",
                "note": "Generation requires separate operator authorization after plan review approval"
            },
            "new_generation_performed": False,
            "new_comfyui_submit_executed": False,
            "retry_attempted": False,
            "workflow_mutated": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "current_state": "corrective_retry_v4_retry_implementation_plan_update_required",
            "next_allowed_action": "operator_retry_v4_updated_implementation_plan_review_required"
        }

        with open(control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json", 'w') as f:
            json.dump(updated_plan, f, indent=2)

        # Create review packet
        review_packet = {
            "task_id": "RC-COMBINE-V2-2721-2780",
            "packet_type": "corrective_retry_v4_updated_implementation_plan_review_packet",
            "stage": "operator_retry_v4_updated_implementation_plan_review_required",
            "shot_id": "shot02",
            "timestamp": "2026-05-07T06:21:11.742760+00:00",
            "updated_implementation_plan_path": "output/control/combine_v2_corrective_retry_v4_updated_implementation_plan.json",
            "summary": {
                "prompt_patch_present": True,
                "negative_prompt_patch_present": True,
                "subject_scale_requirements_present": True,
                "empty_space_requirements_present": True,
                "composition_requirements_present": True,
                "pre_submit_contract_present": True,
                "post_submit_contract_present": True,
                "runtime_prefix_invariants_present": True,
                "generation_gate_closed": True
            },
            "operator_actions": [
                "approve_updated_retry_implementation_plan",
                "request_updated_retry_implementation_plan_changes",
                "reject_updated_retry_implementation_plan"
            ],
            "hard_boundary": {
                "generation_allowed": False,
                "comfyui_submit_allowed": False,
                "retry_execution_allowed": False,
                "assembly_allowed": False,
                "downstream_allowed": False,
                "production_accepted": False
            },
            "new_generation_performed": False,
            "new_comfyui_submit_executed": False,
            "retry_attempted": False,
            "workflow_mutated": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": "corrective_retry_v4_retry_implementation_plan_update_required",
            "next_allowed_action": "operator_retry_v4_updated_implementation_plan_review_required"
        }

        with open(control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json", 'w') as f:
            json.dump(review_packet, f, indent=2)

        return tmp_path

    def setup_artifact_index(self, temp_project, current_state, next_allowed_action, production_accepted=False):
        """Setup artifact_index.json with given state."""
        control_dir = temp_project / "output" / "control"
        artifact_index = {
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "production_accepted": production_accepted,
            "downstream_blocked": True,
            "stage_results": []
        }
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f, indent=2)

        # Create empty ledger
        with open(control_dir / "episode_ledger.json", 'w') as f:
            json.dump([], f, indent=2)

    def test_approval_branch(self, temp_project):
        """Test approve_updated_retry_implementation_plan decision branch."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 0, "Should succeed with approve decision"

        # Verify artifact created
        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"
        assert review_path.exists(), "Operator review artifact should be created"

        with open(review_path) as f:
            review = json.load(f)

        assert review["operator_decision"] == "approve_updated_retry_implementation_plan"
        assert review["operator_approved"] is True
        assert review["updated_plan_reviewed"] is True
        assert review["plan_structurally_valid"] is True

    def test_rejection_branch(self, temp_project):
        """Test reject_updated_retry_implementation_plan decision branch."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=False,
            reject=True,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 0, "Should succeed with reject decision"

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["operator_decision"] == "reject_updated_retry_implementation_plan"
        assert review["operator_approved"] is False
        assert review["next_allowed_action"] == "operator_retry_v4_updated_implementation_plan_revision_required"

    def test_missing_updated_plan_blocks(self, temp_project):
        """Test that missing updated plan blocks execution."""
        control_dir = temp_project / "output" / "control"
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        # Remove the updated plan
        plan_path = control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        plan_path.unlink()

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail when updated plan is missing"

    def test_invalid_state_blocks(self, temp_project):
        """Test that invalid state is rejected."""
        # Setup invalid state
        self.setup_artifact_index(temp_project, "completed", "none")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail with invalid state"

    def test_runtime_generation_forbidden(self, temp_project):
        """Test that plan with generation_allowed=true is rejected."""
        control_dir = temp_project / "output" / "control"
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        # Modify plan to illegally authorize generation
        plan_path = control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        plan["generation_gate"]["generation_allowed"] = True
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail when plan illegally authorizes generation"

    def test_comfyui_submit_forbidden(self, temp_project):
        """Test that plan with comfyui_submit_allowed=true is rejected."""
        control_dir = temp_project / "output" / "control"
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        # Modify plan to illegally authorize ComfyUI submit
        plan_path = control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        plan["generation_gate"]["comfyui_submit_allowed"] = True
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail when plan illegally authorizes ComfyUI submit"

    def test_retry_forbidden(self, temp_project):
        """Test that plan with retry_execution_allowed=true is rejected."""
        control_dir = temp_project / "output" / "control"
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        # Modify plan to illegally authorize retry
        plan_path = control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        plan["generation_gate"]["retry_execution_allowed"] = True
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail when plan illegally authorizes retry"

    def test_invalid_max_generations(self, temp_project):
        """Test that plan with max_generations != 1 is rejected."""
        control_dir = temp_project / "output" / "control"
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        # Modify plan to have invalid max_generations
        plan_path = control_dir / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)
        plan["pre_submit_validation_contract"]["max_generations"] = 2
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        result = combine_review_updated_corrective_retry_v4_implementation_plan(args)
        assert result == 1, "Should fail when plan has invalid max_generations"

    def test_production_accepted_false(self, temp_project):
        """Test that approval does not set production_accepted."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["production_accepted"] is False

    def test_state_transition_correct_on_approval(self, temp_project):
        """Test that approval transitions to correct state."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["current_state"] == "operator_retry_v4_generation_authorization_required"
        assert review["next_allowed_action"] == "operator_retry_v4_generation_authorization_required"

    def test_state_transition_correct_on_rejection(self, temp_project):
        """Test that rejection transitions to correct state."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=False,
            reject=True,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["current_state"] == "operator_retry_v4_updated_implementation_plan_review_required"
        assert review["next_allowed_action"] == "operator_retry_v4_updated_implementation_plan_revision_required"

    def test_canonical_artifacts_updated(self, temp_project):
        """Test that canonical artifacts are properly updated."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"

        # Verify artifact_index.json
        with open(control_dir / "artifact_index.json") as f:
            artifact_index = json.load(f)

        assert artifact_index["operator_updated_retry_v4_implementation_plan_review_executed"] is True
        assert artifact_index["updated_retry_v4_implementation_plan_approved"] is True
        assert artifact_index["production_accepted"] is False
        assert artifact_index["generation_gate_opened"] is False
        assert artifact_index["retry_authorized"] is False

        # Verify episode_ledger.json
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "operator_retry_v4_updated_implementation_plan_reviewed"
        assert last_event["operator_approved"] is True

    def test_approval_does_not_authorize_runtime_actions(self, temp_project):
        """Test that approval does not authorize generation, retry, visual QA, assembly, or downstream."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["generation_authorized"] is False
        assert review["retry_authorized"] is False
        assert review["comfyui_submit_authorized"] is False
        assert review["visual_qa_authorized"] is False
        assert review["assembly_authorized"] is False
        assert review["downstream_authorized"] is False
        assert review["new_generation_performed"] is False
        assert review["new_comfyui_submit_executed"] is False
        assert review["retry_attempted"] is False
        assert review["visual_qa_executed"] is False
        assert review["assembly_executed"] is False
        assert review["downstream_executed"] is False

    def test_visual_qa_forbidden(self, temp_project):
        """Test that approval does not authorize visual QA."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["visual_qa_authorized"] is False
        assert review["visual_qa_executed"] is False

    def test_assembly_forbidden(self, temp_project):
        """Test that approval does not authorize assembly."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["assembly_authorized"] is False
        assert review["assembly_executed"] is False

    def test_downstream_forbidden(self, temp_project):
        """Test that approval does not authorize downstream."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["downstream_authorized"] is False
        assert review["downstream_executed"] is False

    def test_review_artifact_has_required_fields(self, temp_project):
        """Test that review artifact has all required fields."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_retry_implementation_plan_update_required", "operator_retry_v4_updated_implementation_plan_review_required")

        from app.cli import combine_review_updated_corrective_retry_v4_implementation_plan

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            json=True
        )

        combine_review_updated_corrective_retry_v4_implementation_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        # Required fields per spec
        assert review["task_id"] == "RC-COMBINE-V2-2781-2840"
        assert review["review_type"] == "operator_review_updated_retry_v4_implementation_plan"
        assert review["previous_layer"] == "RC-COMBINE-V2-2721-2780"
        assert review["previous_commit"] == "2759d52"
        assert review["updated_plan_reviewed"] is True
        assert review["operator_approved"] is True
        assert review["plan_structurally_valid"] is True
        assert review["generation_authorized"] is False
        assert review["retry_authorized"] is False
        assert review["comfyui_submit_authorized"] is False
        assert review["visual_qa_authorized"] is False
        assert review["assembly_authorized"] is False
        assert review["downstream_authorized"] is False
        assert review["production_accepted"] is False
        assert review["next_allowed_action"] == "operator_retry_v4_generation_authorization_required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
