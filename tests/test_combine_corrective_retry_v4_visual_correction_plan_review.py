"""
Test: combine-review-corrective-retry-v4-visual-correction-plan
Task ID: RC-COMBINE-V2-2661-2720

Tests the operator review gate for V4 visual correction plan.
Covers:
- requires_visual_correction_plan: true
- requires_review_packet: true
- approve_branch: true
- request_changes_branch: true
- reject_branch: true
- approval_does_not_generate: true
- approval_does_not_submit_comfyui: true
- approval_does_not_mutate_workflow: true
- approval_does_not_set_production_accepted: true
- approved_plan_routes_to_retry_implementation_plan_update: true
- next_allowed_action_not_none: true
"""

import pytest
import json
from pathlib import Path
from argparse import Namespace


class TestCombineCorrectiveRetryV4VisualCorrectionPlanReview:
    """Test suite for RC-COMBINE-V2-2661-2720"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with required artifacts."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create visual correction plan
        visual_correction_plan = {
            "task_id": "RC-COMBINE-V2-2601-2660",
            "stage": "corrective_retry_v4_visual_correction_plan_required",
            "plan_type": "corrective_retry_v4_visual_correction_plan",
            "shot_id": "shot02",
            "timestamp": "2026-05-07T05:42:33.711974+00:00",
            "visual_qa_verdict_used": True,
            "visual_qa_verdict": "failed",
            "failed_reasons": [
                "excessive_empty_space",
                "subject_scale_check",
                "empty_space_check",
                "prompt_scene_alignment_check",
                "weak_composition",
                "composition_check",
                "prompt_scene_alignment_weak",
                "shot_intent_not_satisfied",
                "subject_too_small",
                "production_quality_check",
                "shot_intent_alignment_check"
            ],
            "correction_mapping": {
                "subject_too_small": {
                    "failure": "Subject too small in frame",
                    "corrective_actions": [
                        "increase subject scale",
                        "target subject height ratio: 0.40-0.60 of frame height"
                    ],
                    "target_subject_height_ratio": "0.40-0.60",
                    "minimum_subject_height_ratio": "0.30"
                },
                "excessive_empty_space": {
                    "failure": "Excessive empty space - background dominates",
                    "corrective_actions": [
                        "reduce empty background dominance",
                        "target empty-space ratio <= 0.45"
                    ],
                    "target_empty_space_ratio_max": "0.45"
                },
                "weak_composition": {
                    "failure": "Weak composition - flat or unbalanced",
                    "corrective_actions": [
                        "define composition target",
                        "subject must be clear focal point"
                    ],
                    "composition_target": "cinematic subject-focused framing"
                },
                "shot_intent_not_satisfied": {
                    "failure": "Shot intent not satisfied - frame does not match target",
                    "corrective_actions": [
                        "restate shot intent",
                        "require prompt/graph to express shot02 target"
                    ]
                },
                "prompt_scene_alignment_weak": {
                    "failure": "Prompt/scene alignment weak",
                    "corrective_actions": [
                        "strengthen prompt with explicit subject scale"
                    ]
                }
            },
            "retry_prompt_patch": {
                "positive_prompt_additions": [
                    "subject fills 40-60% of frame height",
                    "minimal background",
                    "foreground subject emphasis"
                ],
                "negative_prompt_additions": [
                    "small person in vast space",
                    "landscape without subject",
                    "tiny subject"
                ],
                "camera_framing_requirements": [
                    "empty space <= 45% of frame",
                    "subject dominant in composition"
                ],
                "subject_scale_requirements": [
                    "subject height >= 40% of frame",
                    "reject if subject < 30% of frame"
                ],
                "composition_requirements": [
                    "subject is clear focal point",
                    "balanced cinematic framing"
                ],
                "rejection_criteria": [
                    "subject smaller than 30% of frame height",
                    "empty space exceeds 45% of frame"
                ]
            },
            "generation_performed": False,
            "comfyui_execution": False,
            "retry_attempted": False,
            "workflow_mutated": False,
            "production_accepted": False,
            "next_allowed_action": "operator_retry_v4_visual_correction_plan_review_required"
        }

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json", 'w') as f:
            json.dump(visual_correction_plan, f, indent=2)

        # Create review packet
        review_packet = {
            "task_id": "RC-COMBINE-V2-2601-2660",
            "packet_type": "corrective_retry_v4_visual_correction_plan_review_packet",
            "stage": "operator_retry_v4_visual_correction_plan_review_required",
            "shot_id": "shot02",
            "timestamp": "2026-05-07T05:42:33.711974+00:00",
            "visual_correction_plan_path": "output/control/combine_v2_corrective_retry_v4_visual_correction_plan.json",
            "operator_decision_required": True,
            "allowed_decisions": [
                "approve_visual_correction_plan",
                "request_visual_correction_plan_changes",
                "reject_visual_correction_plan"
            ],
            "decision_guidance": {
                "approve_visual_correction_plan": "Proceed with retry using the correction plan specifications",
                "request_visual_correction_plan_changes": "Request modifications to specific correction requirements",
                "reject_visual_correction_plan": "Reject the plan and route to manual review"
            },
            "generation_performed": False,
            "comfyui_execution": False,
            "retry_attempted": False,
            "workflow_mutated": False,
            "production_accepted": False
        }

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan_review_packet.json", 'w') as f:
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

    def test_requires_visual_correction_plan(self, temp_project):
        """Test that command requires visual correction plan."""
        control_dir = temp_project / "output" / "control"

        # Setup valid state
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        # Remove the plan
        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        plan_path.unlink()

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 1, "Should fail when visual correction plan is missing"

    def test_requires_review_packet(self, temp_project):
        """Test that command requires review packet."""
        control_dir = temp_project / "output" / "control"

        # Setup valid state
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        # Remove the review packet
        packet_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan_review_packet.json"
        packet_path.unlink()

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 1, "Should fail when review packet is missing"

    def test_approve_branch(self, temp_project):
        """Test approve_visual_correction_plan decision branch."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan_for_controlled_retry_update",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 0, "Should succeed with approve decision"

        # Verify artifact created
        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"
        assert review_path.exists(), "Operator review artifact should be created"

        with open(review_path) as f:
            review = json.load(f)

        assert review["operator_decision"] == "approve_visual_correction_plan"
        assert review["visual_correction_plan_approved"] is True
        assert review["next_allowed_action"] == "corrective_retry_v4_retry_implementation_plan_update_required"

    def test_request_changes_branch(self, temp_project):
        """Test request_visual_correction_plan_changes decision branch."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="request_visual_correction_plan_changes",
            reason="operator_requests_changes_to_correction_requirements",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 0, "Should succeed with request_changes decision"

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["operator_decision"] == "request_visual_correction_plan_changes"
        assert review["visual_correction_plan_approved"] is False
        assert review["next_allowed_action"] == "corrective_retry_v4_visual_correction_plan_required"
        assert len(review["requested_changes"]) > 0

    def test_reject_branch(self, temp_project):
        """Test reject_visual_correction_plan decision branch."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="reject_visual_correction_plan",
            reason="operator_rejects_correction_plan",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 0, "Should succeed with reject decision"

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["operator_decision"] == "reject_visual_correction_plan"
        assert review["visual_correction_plan_approved"] is False
        assert review["next_allowed_action"] == "manual_review_required"

    def test_approval_does_not_generate(self, temp_project):
        """Test that approval does not perform generation."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["generation_performed"] is False
        assert review["retry_attempted"] is False

    def test_approval_does_not_submit_comfyui(self, temp_project):
        """Test that approval does not submit to ComfyUI."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["comfyui_execution"] is False

    def test_approval_does_not_mutate_workflow(self, temp_project):
        """Test that approval does not mutate workflow."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["workflow_mutated"] is False

    def test_approval_does_not_set_production_accepted(self, temp_project):
        """Test that approval does not set production_accepted."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["production_accepted"] is False

    def test_approved_plan_routes_to_retry_implementation_plan_update(self, temp_project):
        """Test that approved plan routes to corrective_retry_v4_retry_implementation_plan_update_required."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        assert review["next_allowed_action"] == "corrective_retry_v4_retry_implementation_plan_update_required"

    def test_next_allowed_action_not_none(self, temp_project):
        """Test that next_allowed_action is never none."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        for decision in ["approve_visual_correction_plan", "request_visual_correction_plan_changes", "reject_visual_correction_plan"]:
            # Reset artifact_index for each decision
            self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

            args = Namespace(
                project_root=str(temp_project),
                shot_id="shot02",
                decision=decision,
                reason=f"test_{decision}",
                json=True
            )

            combine_review_corrective_retry_v4_visual_correction_plan(args)

            control_dir = temp_project / "output" / "control"
            with open(control_dir / "artifact_index.json") as f:
                artifact_index = json.load(f)

            assert artifact_index["next_allowed_action"] is not None
            assert artifact_index["next_allowed_action"] != "none"

    def test_approval_extracts_all_correction_requirements(self, temp_project):
        """Test that approval extracts all correction requirements from the plan."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_visual_correction_plan_review.json"

        with open(review_path) as f:
            review = json.load(f)

        # Verify all approved elements are present
        assert review["approved_failed_reasons"] is not None
        assert len(review["approved_failed_reasons"]) > 0
        assert review["approved_subject_scale_requirements"] is not None
        assert review["approved_empty_space_requirements"] is not None
        assert review["approved_composition_requirements"] is not None
        assert review["approved_prompt_patch_recommendations"] is not None

    def test_invalid_state_rejected(self, temp_project):
        """Test that invalid state is rejected."""
        # Setup invalid state
        self.setup_artifact_index(temp_project, "completed", "none")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 1, "Should fail with invalid state"

    def test_production_accepted_true_rejected(self, temp_project):
        """Test that production_accepted=true is rejected."""
        # Setup state with production_accepted=true
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required", production_accepted=True)

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        result = combine_review_corrective_retry_v4_visual_correction_plan(args)
        assert result == 1, "Should fail when production_accepted is true"

    def test_artifact_index_updated(self, temp_project):
        """Test that artifact_index.json is properly updated."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            artifact_index = json.load(f)

        assert artifact_index["operator_visual_correction_plan_review_executed"] is True
        assert artifact_index["visual_correction_plan_approved"] is True
        assert artifact_index["production_accepted"] is False
        assert artifact_index["downstream_blocked"] is True

    def test_episode_ledger_updated(self, temp_project):
        """Test that episode_ledger.json is properly updated."""
        self.setup_artifact_index(temp_project, "corrective_retry_v4_visual_correction_plan_required", "operator_retry_v4_visual_correction_plan_review_required")

        from app.cli import combine_review_corrective_retry_v4_visual_correction_plan

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            decision="approve_visual_correction_plan",
            reason="operator_approves_visual_correction_plan",
            json=True
        )

        combine_review_corrective_retry_v4_visual_correction_plan(args)

        control_dir = temp_project / "output" / "control"
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "operator_retry_v4_visual_correction_plan_reviewed"
        assert last_event["operator_decision"] == "approve_visual_correction_plan"
        assert last_event["visual_correction_plan_approved"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
