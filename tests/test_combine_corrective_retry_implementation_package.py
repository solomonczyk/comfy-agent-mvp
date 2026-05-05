"""RC-COMBINE-V2-801-860 — Test controlled corrective retry implementation package.

Tests for the combine-build-corrective-retry-package CLI command.
"""

import json
import tempfile
from pathlib import Path
import pytest
import argparse

from app.cli import combine_build_corrective_retry_package, combine_authorize_corrective_retry_implementation


class TestCombineCorrectiveRetryImplementationPackage:
    """Test controlled corrective retry implementation package build."""

    def setup_control_dir(self, project_root: Path):
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        return control_dir

    def create_preconditions_for_build(self, control_dir: Path):
        # Create authorization artifact
        auth = {
            "stage": "controlled_retry_authorization_required",
            "operator_decision": "approve_corrective_retry_implementation",
            "corrective_retry_implementation_authorized": True,
            "retry_generation_authorized": False,
            "generation_allowed": False,
            "retry_allowed": False,
            "comfyui_execution": False,
            "workflow_submitted": False,
            "production_accepted": False,
            "reason": "operator_approved_corrective_retry_package_preparation_after_visual_rejection",
            "timestamp": "2024-01-01T00:00:00",
            "next_allowed_action": "corrective_retry_implementation_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_authorization.json", 'w') as f:
            json.dump(auth, f, indent=2)

        # Create corrective retry plan
        plan = {
            "stage": "corrective_retry_plan_required",
            "plan_type": "controlled_corrective_retry_plan",
            "source_asset": "output/assets/combine_v2_1777917278_00001_.png",
            "failure_basis": [
                "semantic_content_failed",
                "subject_not_recognizable",
                "blur_or_softness",
                "low_detail_quality",
                "composition_failed",
                "production_quality_failed"
            ],
            "blind_retry_allowed": False,
            "retry_requires_operator_authorization": True,
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        # Create failure classification
        failure = {
            "classification": "rebuilt_asset_visual_failure",
            "source_asset": "output/assets/combine_v2_1777917278_00001_.png",
            "failure_basis": [
                "semantic_content_failed",
                "subject_not_recognizable",
                "blur_or_softness",
                "low_detail_quality",
                "composition_failed",
                "production_quality_failed"
            ],
            "blind_retry_allowed": False,
            "production_accepted": False
        }
        with open(control_dir / "combine_v2_rebuilt_asset_failure_classification.json", 'w') as f:
            json.dump(failure, f, indent=2)

    def test_build_corrective_retry_package_success(self, tmp_path):
        """Test building corrective retry implementation package."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result_code = combine_build_corrective_retry_package(args)
        assert result_code == 0

        # Verify all required artifacts were created
        required_artifacts = [
            "combine_v2_corrective_retry_implementation_report.json",
            "combine_v2_corrective_retry_prompt_patch.json",
            "combine_v2_corrective_retry_workflow_patch.json",
            "combine_v2_corrective_retry_quality_pipeline_patch.json",
            "combine_v2_corrective_retry_preflight_report.json",
            "combine_v2_operator_retry_generation_authorization_request.json"
        ]

        for artifact_name in required_artifacts:
            artifact_path = control_dir / artifact_name
            assert artifact_path.exists(), f"Artifact {artifact_name} was not created"

    def test_implementation_report_contents(self, tmp_path):
        """Test implementation report has correct structure."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'r') as f:
            report = json.load(f)

        assert report["stage"] == "corrective_retry_implementation_required"
        assert report["package_type"] == "controlled_corrective_retry_implementation"
        assert report["source_failed_asset"] == "output/assets/combine_v2_1777917278_00001_.png"
        assert report["blind_retry_allowed"] is False
        assert report["prompt_patch_created"] is True
        assert report["workflow_patch_created"] is True
        assert report["quality_pipeline_patch_created"] is True
        assert report["preflight_created"] is True
        assert report["retry_generation_authorization_required"] is True
        assert report["generation_allowed"] is False
        assert report["retry_allowed"] is False
        assert report["retry_attempted"] is False
        assert report["comfyui_execution"] is False
        assert report["workflow_submitted"] is False
        assert report["downstream_executed"] is False
        assert report["production_accepted"] is False
        assert report["next_allowed_action"] == "operator_retry_generation_authorization_required"

    def test_prompt_patch_addresses_failures(self, tmp_path):
        """Test prompt patch addresses all failure categories."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_corrective_retry_prompt_patch.json", 'r') as f:
            patch = json.load(f)

        assert patch["patch_type"] == "corrective_retry_prompt_patch"
        assert "unclear_subject" in patch["prompt_corrections"]
        assert "semantic_content_failure" in patch["prompt_corrections"]
        assert "subject_not_recognizable" in patch["prompt_corrections"]
        assert "weak_composition" in patch["prompt_corrections"]
        assert "low_detail_quality" in patch["prompt_corrections"]
        assert "production_quality_failure" in patch["prompt_corrections"]
        assert patch["generation_allowed"] is False

    def test_workflow_patch_enforces_constraints(self, tmp_path):
        """Test workflow patch enforces resolution and path constraints."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_corrective_retry_workflow_patch.json", 'r') as f:
            patch = json.load(f)

        assert patch["patch_type"] == "corrective_retry_workflow_patch"
        assert patch["workflow_corrections"]["rebuild_recipe_active"] is True
        assert patch["workflow_corrections"]["minimum_short_side_enforced"] is True
        assert patch["workflow_corrections"]["minimum_short_side"] == 1024
        assert patch["workflow_corrections"]["legacy_512_workflow_blocked"] is True
        assert patch["workflow_corrections"]["output_path_contract_preserved"] is True
        assert patch["workflow_corrections"]["save_image_collector_canonical"] is True
        assert patch["generation_allowed"] is False

    def test_quality_pipeline_patch_blocks_blind_retry(self, tmp_path):
        """Test quality pipeline patch requires preflight and QA."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_corrective_retry_quality_pipeline_patch.json", 'r') as f:
            patch = json.load(f)

        assert patch["patch_type"] == "corrective_retry_quality_pipeline_patch"
        assert patch["quality_pipeline_corrections"]["blind_retry_blocked"] is True
        assert patch["quality_pipeline_corrections"]["preflight_before_retry_submit"] is True
        assert patch["quality_pipeline_corrections"]["manifest_must_reference_canonical_project_asset"] is True
        assert patch["quality_pipeline_corrections"]["post_generation_visual_qa_required"] is True
        assert patch["quality_pipeline_corrections"]["downstream_blocked_until_qa_acceptance"] is True
        assert patch["generation_allowed"] is False

    def test_preflight_report_all_checks_passed(self, tmp_path):
        """Test preflight report shows all checks passed."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_corrective_retry_preflight_report.json", 'r') as f:
            report = json.load(f)

        assert report["preflight_type"] == "corrective_retry_preflight"
        assert report["all_checks_passed"] is True
        assert report["checks"]["prompt_patch_ready"] is True
        assert report["checks"]["workflow_patch_ready"] is True
        assert report["checks"]["quality_pipeline_patch_ready"] is True
        assert report["checks"]["implementation_authorized"] is True
        assert report["checks"]["blind_retry_blocked"] is True
        assert report["checks"]["legacy_512_blocked"] is True
        assert report["checks"]["minimum_short_side_1024_enforced"] is True
        assert report["checks"]["output_path_contract_preserved"] is True
        assert report["checks"]["post_qa_required"] is True
        assert report["checks"]["downstream_blocked"] is True
        assert report["generation_allowed"] is False

    def test_operator_retry_generation_authorization_request(self, tmp_path):
        """Test operator retry generation authorization request artifact."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "combine_v2_operator_retry_generation_authorization_request.json", 'r') as f:
            auth = json.load(f)

        assert auth["stage"] == "operator_retry_generation_authorization_required"
        assert auth["operator_review_required"] is True
        assert auth["recommended_operator_decision"] == "approve_one_corrective_retry_generation"
        assert "approve_one_corrective_retry_generation" in auth["operator_actions"]
        assert "request_corrective_retry_package_changes" in auth["operator_actions"]
        assert "manual_review" in auth["operator_actions"]
        assert "abort_route" in auth["operator_actions"]
        assert auth["retry_generation_authorized"] is False
        assert auth["generation_allowed"] is False
        assert auth["retry_allowed"] is False
        assert auth["workflow_submitted"] is False
        assert auth["production_accepted"] is False
        assert auth["next_allowed_action"] == "operator_retry_generation_authorization_required"

    def test_artifact_index_updated(self, tmp_path):
        """Test artifact index is updated after package build."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["current_state"] == "operator_retry_generation_authorization_required"
        assert artifact_index["next_allowed_action"] == "operator_retry_generation_authorization_required"
        assert artifact_index["corrective_retry_package_created"] is True
        assert artifact_index["prompt_patch_created"] is True
        assert artifact_index["workflow_patch_created"] is True
        assert artifact_index["quality_pipeline_patch_created"] is True
        assert artifact_index["preflight_report_created"] is True
        assert artifact_index["operator_retry_generation_authorization_request_created"] is True
        assert artifact_index["legacy_512_workflow_blocked"] is True
        assert artifact_index["minimum_short_side_1024_enforced"] is True
        assert artifact_index["output_path_contract_preserved"] is True
        assert artifact_index["blind_retry_allowed"] is False
        assert artifact_index["generation_allowed"] is False
        assert artifact_index["retry_allowed"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False

    def test_ledger_updated(self, tmp_path):
        """Test episode ledger is updated after package build."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        with open(control_dir / "episode_ledger.json", 'r') as f:
            ledger = json.load(f)

        assert isinstance(ledger, list)
        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "corrective_retry_implementation_package_created"
        assert last_event["prompt_patch_created"] is True
        assert last_event["workflow_patch_created"] is True
        assert last_event["quality_pipeline_patch_created"] is True
        assert last_event["preflight_report_created"] is True
        assert last_event["operator_retry_generation_authorization_request_created"] is True
        assert last_event["generation_allowed"] is False
        assert last_event["retry_allowed"] is False

    def test_missing_authorization_fails(self, tmp_path):
        """Test package build fails without authorization artifact."""
        control_dir = self.setup_control_dir(tmp_path)
        # Only create plan, not authorization
        plan = {
            "stage": "corrective_retry_plan_required",
            "plan_type": "controlled_corrective_retry_plan",
            "source_asset": "output/assets/test.png",
            "failure_basis": ["semantic_content_failed"],
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result_code = combine_build_corrective_retry_package(args)
        assert result_code == 1

    def test_unauthorized_decision_fails(self, tmp_path):
        """Test package build fails if authorization was not approved."""
        control_dir = self.setup_control_dir(tmp_path)

        auth = {
            "stage": "controlled_retry_authorization_required",
            "operator_decision": "abort_route",
            "corrective_retry_implementation_authorized": False,
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_authorization.json", 'w') as f:
            json.dump(auth, f, indent=2)

        plan = {
            "stage": "corrective_retry_plan_required",
            "plan_type": "controlled_corrective_retry_plan",
            "source_asset": "output/assets/test.png",
            "failure_basis": ["semantic_content_failed"],
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result_code = combine_build_corrective_retry_package(args)
        assert result_code == 1

    def test_next_allowed_action_is_operator_retry_generation_authorization(self, tmp_path):
        """Test that next_allowed_action points to operator_retry_generation_authorization_required."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result_code = combine_build_corrective_retry_package(args)
        assert result_code == 0

        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["next_allowed_action"] == "operator_retry_generation_authorization_required"

    def test_generation_and_retry_blocked_after_package_build(self, tmp_path):
        """Test that generation and retry remain blocked after package build."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_preconditions_for_build(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        combine_build_corrective_retry_package(args)

        # Check all artifacts block generation
        for artifact_name in [
            "combine_v2_corrective_retry_implementation_report.json",
            "combine_v2_corrective_retry_prompt_patch.json",
            "combine_v2_corrective_retry_workflow_patch.json",
            "combine_v2_corrective_retry_quality_pipeline_patch.json",
            "combine_v2_corrective_retry_preflight_report.json",
            "combine_v2_operator_retry_generation_authorization_request.json"
        ]:
            with open(control_dir / artifact_name, 'r') as f:
                artifact = json.load(f)
            assert artifact["generation_allowed"] is False, f"{artifact_name} should block generation"

        # Check artifact index
        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["generation_allowed"] is False
        assert artifact_index["retry_allowed"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False

    def test_full_authorize_then_build_flow(self, tmp_path):
        """Test the full flow: authorize then build package."""
        control_dir = self.setup_control_dir(tmp_path)

        # Create preconditions for authorization
        auth_request = {
            "stage": "controlled_retry_authorization_required",
            "operator_review_required": True,
            "recommended_operator_decision": "approve_corrective_retry_implementation",
            "generation_allowed": False,
            "retry_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_controlled_retry_authorization_request.json", 'w') as f:
            json.dump(auth_request, f, indent=2)

        plan = {
            "stage": "corrective_retry_plan_required",
            "plan_type": "controlled_corrective_retry_plan",
            "source_asset": "output/assets/test.png",
            "failure_basis": [
                "semantic_content_failed",
                "subject_not_recognizable",
                "blur_or_softness",
                "low_detail_quality",
                "composition_failed",
                "production_quality_failed"
            ],
            "blind_retry_allowed": False,
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)

        # Step 1: Authorize
        auth_args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="approve_corrective_retry_implementation",
            reason="operator_approved_corrective_retry_package_preparation_after_visual_rejection",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(auth_args)
        assert result_code == 0

        # Step 2: Build package
        build_args = argparse.Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result_code = combine_build_corrective_retry_package(build_args)
        assert result_code == 0

        # Verify final state
        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["current_state"] == "operator_retry_generation_authorization_required"
        assert artifact_index["corrective_retry_implementation_authorized"] is True
        assert artifact_index["corrective_retry_package_created"] is True
        assert artifact_index["prompt_patch_created"] is True
        assert artifact_index["workflow_patch_created"] is True
        assert artifact_index["quality_pipeline_patch_created"] is True
        assert artifact_index["preflight_report_created"] is True
        assert artifact_index["operator_retry_generation_authorization_request_created"] is True
        assert artifact_index["legacy_512_workflow_blocked"] is True
        assert artifact_index["minimum_short_side_1024_enforced"] is True
        assert artifact_index["output_path_contract_preserved"] is True
        assert artifact_index["blind_retry_allowed"] is False
        assert artifact_index["generation_allowed"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False
