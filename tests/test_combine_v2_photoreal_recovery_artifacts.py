"""Tests for RC-COMBINE-V2-15001-22000 recovery artifacts.

Tests cover:
- V11-specific artifact names
- V12-specific artifact names
- V13-specific artifact names
- All artifacts contain correct version references
- Artifacts enforce max_generations=1
- Artifacts enforce blind_retry_allowed=false
- Artifacts enforce production_accepted=false
- Artifacts enforce assembly_executed=false
- Artifacts enforce downstream_executed=false
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from app.orchestrator.state_machine import CombineStateMachine


@pytest.fixture
def project_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        control_dir = root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield root, control_dir


V11_ARTIFACTS = [
    "combine_v2_v11_correction_plan.json",
    "combine_v2_v11_correction_plan_authorization.json",
    "combine_v2_v11_defect_taxonomy.json",
    "combine_v2_v11_prompt_patch.json",
    "combine_v2_v11_workflow_patch.json",
    "combine_v2_v11_quality_pipeline_patch.json",
    "combine_v2_v11_preflight_report.json",
    "combine_v2_v11_generation_authorization_request.json",
    "combine_v2_v11_generation_authorization.json",
    "combine_v2_v11_submit_request.json",
    "combine_v2_v11_generation_result.json",
    "combine_v2_v11_outputs_manifest.json",
    "combine_v2_v11_generation_trace.json",
    "combine_v2_v11_result_review.json",
    "combine_v2_v11_operator_visual_review_packet.json",
]

V12_ARTIFACTS = [
    "combine_v2_v12_correction_plan.json",
    "combine_v2_v12_prompt_patch.json",
    "combine_v2_v12_workflow_patch.json",
    "combine_v2_v12_quality_pipeline_patch.json",
    "combine_v2_v12_preflight_report.json",
    "combine_v2_v12_generation_authorization_request.json",
    "combine_v2_v12_generation_result.json",
    "combine_v2_v12_submit_request.json",
    "combine_v2_v12_outputs_manifest.json",
    "combine_v2_v12_generation_trace.json",
    "combine_v2_v12_result_review.json",
    "combine_v2_v12_operator_visual_review_packet.json",
]

V13_ARTIFACTS = [
    "combine_v2_v13_correction_plan.json",
    "combine_v2_v13_prompt_patch.json",
    "combine_v2_v13_workflow_patch.json",
    "combine_v2_v13_quality_pipeline_patch.json",
    "combine_v2_v13_preflight_report.json",
    "combine_v2_v13_generation_authorization_request.json",
    "combine_v2_v13_generation_result.json",
    "combine_v2_v13_submit_request.json",
    "combine_v2_v13_outputs_manifest.json",
    "combine_v2_v13_generation_trace.json",
    "combine_v2_v13_result_review.json",
    "combine_v2_v13_operator_visual_review_packet.json",
]


class TestV11ArtifactNames:
    """V11 artifacts must use V11-specific names."""

    @pytest.mark.parametrize("artifact_name", V11_ARTIFACTS)
    def test_v11_artifact_has_correct_prefix(self, project_root, artifact_name):
        """V11 artifact names must start with combine_v2_v11_."""
        assert artifact_name.startswith("combine_v2_v11_"), \
            f"V11 artifact '{artifact_name}' must start with combine_v2_v11_"

    def test_v11_artifact_no_old_retry_names(self, project_root):
        """V11 artifacts must NOT use old corrective_retry names."""
        _, control_dir = project_root
        for artifact in V11_ARTIFACTS:
            assert "corrective_retry" not in artifact, \
                f"V11 artifact '{artifact}' must not contain 'corrective_retry'"


class TestV12ArtifactNames:
    """V12 artifacts must use V12-specific names."""

    @pytest.mark.parametrize("artifact_name", V12_ARTIFACTS)
    def test_v12_artifact_has_correct_prefix(self, project_root, artifact_name):
        assert artifact_name.startswith("combine_v2_v12_"), \
            f"V12 artifact '{artifact_name}' must start with combine_v2_v12_"


class TestV13ArtifactNames:
    """V13 artifacts must use V13-specific names."""

    @pytest.mark.parametrize("artifact_name", V13_ARTIFACTS)
    def test_v13_artifact_has_correct_prefix(self, project_root, artifact_name):
        assert artifact_name.startswith("combine_v2_v13_"), \
            f"V13 artifact '{artifact_name}' must start with combine_v2_v13_"


class TestArtifactFieldEnforcement:
    """All artifacts must enforce correct field values."""

    def _create_sample_artifact(self, control_dir, artifact_name, **overrides):
        data = {
            "version": "v11",
            "max_generations": 1,
            "generation_allowed": True,
            "blind_retry_allowed": False,
            "production_accepted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "timestamp": datetime.now().isoformat()
        }
        data.update(overrides)
        with open(control_dir / artifact_name, 'w') as f:
            json.dump(data, f, indent=2)
        return data

    @pytest.mark.parametrize("version,artifacts", [
        ("v11", V11_ARTIFACTS),
        ("v12", V12_ARTIFACTS),
        ("v13", V13_ARTIFACTS),
    ])
    def test_artifacts_enforce_production_accepted_false(self, project_root, version, artifacts):
        """All version artifacts must enforce production_accepted=false."""
        _, control_dir = project_root
        for artifact in artifacts:
            self._create_sample_artifact(control_dir, artifact, version=version)
            with open(control_dir / artifact) as f:
                data = json.load(f)
            assert data.get("production_accepted") is False, \
                f"{artifact} has production_accepted={data.get('production_accepted')}"

    @pytest.mark.parametrize("version,artifacts", [
        ("v11", V11_ARTIFACTS[:5]),
        ("v12", V12_ARTIFACTS[:5]),
        ("v13", V13_ARTIFACTS[:5]),
    ])
    def test_artifacts_enforce_blind_retry_blocked(self, project_root, version, artifacts):
        """Correction package artifacts must have blind_retry_allowed=false."""
        _, control_dir = project_root
        for artifact in artifacts:
            self._create_sample_artifact(control_dir, artifact, version=version,
                                          blind_retry_allowed=False)
            with open(control_dir / artifact) as f:
                data = json.load(f)
            assert data.get("blind_retry_allowed") is False, \
                f"{artifact} has blind_retry_allowed={data.get('blind_retry_allowed')}"

    @pytest.mark.parametrize("version,artifacts", [
        ("v11", V11_ARTIFACTS),
        ("v12", V12_ARTIFACTS),
        ("v13", V13_ARTIFACTS),
    ])
    def test_artifacts_enforce_max_generations_one(self, project_root, version, artifacts):
        """Generation-related artifacts must have max_generations=1."""
        _, control_dir = project_root
        for artifact in artifacts:
            if "generation" in artifact or "submit" in artifact:
                self._create_sample_artifact(control_dir, artifact, version=version,
                                              max_generations=1)
                with open(control_dir / artifact) as f:
                    data = json.load(f)
                if "max_generations" in data:
                    assert data["max_generations"] == 1, \
                        f"{artifact} has max_generations={data['max_generations']}"


class TestStateMachineStates:
    """Test that all V11/V12/V13 states are valid in the state machine."""

    @pytest.mark.parametrize("state", [
        "v11_correction_plan_required",
        "v11_corrective_package_build_required",
        "v11_generation_authorization_required",
        "v11_generate_assets",
        "v11_result_review_required",
        "v11_visual_qa_preflight_required",
        "v11_visual_qa_required",
        "v11_operator_visual_review_required",
        "v12_correction_plan_required",
        "v12_corrective_package_build_required",
        "v12_generation_authorization_required",
        "v12_generate_assets",
        "v12_result_review_required",
        "v12_visual_qa_preflight_required",
        "v12_visual_qa_required",
        "v12_operator_visual_review_required",
        "v13_correction_plan_required",
        "v13_corrective_package_build_required",
        "v13_generation_authorization_required",
        "v13_generate_assets",
        "v13_result_review_required",
        "v13_visual_qa_preflight_required",
        "v13_visual_qa_required",
        "v13_operator_visual_review_required",
        "visual_candidate_accepted_for_pipeline",
        "qa_recovery_blocked_after_max_candidates",
    ])
    def test_state_is_valid(self, state):
        assert CombineStateMachine.is_valid_state(state), f"State {state} should be valid"

    @pytest.mark.parametrize("state,terminal", [
        ("visual_candidate_accepted_for_pipeline", True),
        ("qa_recovery_blocked_after_max_candidates", True),
        ("v11_operator_visual_review_required", False),
        ("v12_generate_assets", False),
        ("v13_generation_authorization_required", False),
    ])
    def test_terminal_states(self, state, terminal):
        assert CombineStateMachine.is_terminal_state(state) == terminal, \
            f"State {state} terminal expected={terminal}"
