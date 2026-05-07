"""RC-COMBINE-V2-5101-5400 — Test V7 identity/fidelity generation artifacts.

Verifies:
- Operator authorization artifact created
- V7 workflow submitted
- Outputs manifest registered
- Result artifact created
- Operator review packet created
- Canonical output registered
"""

import json
from pathlib import Path
import pytest


AUTHORIZATION_SCHEMA = {
    "operator_authorized": True,
    "max_new_generations": 1,
    "generation_allowed": True,
    "blind_retry_allowed": False,
    "second_generation_allowed": False,
    "visual_acceptance_allowed": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_acceptance_allowed": False,
}

RESULT_SCHEMA = {
    "generation_count": 1,
    "second_generation_attempted": False,
    "workflow_submitted": True,
    "comfyui_execution": True,
    "canonical_outputs_registered": True,
    "visual_acceptance_executed": False,
    "production_accepted": False,
    "assembly_executed": False,
    "downstream_executed": False,
}


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def authorization(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_generation_authorization.json"
    if not path.exists():
        pytest.skip("Authorization artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def submitted_workflow(project_root):
    path = project_root / "output" / "control" / "shot02_v7_identity_fidelity_submitted_workflow.json"
    if not path.exists():
        pytest.skip("Submitted workflow not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def outputs_manifest(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_outputs_manifest.json"
    if not path.exists():
        pytest.skip("Outputs manifest not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def result(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_result.json"
    if not path.exists():
        pytest.skip("Result artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def review_packet(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_operator_review_packet.json"
    if not path.exists():
        pytest.skip("Operator review packet not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def artifact_index(project_root):
    path = project_root / "output" / "control" / "artifact_index.json"
    if not path.exists():
        pytest.skip("Artifact index not found")
    with open(path) as f:
        return json.load(f)


class TestOperatorAuthorization:
    def test_authorization_created(self, authorization):
        for key, expected in AUTHORIZATION_SCHEMA.items():
            assert authorization.get(key) == expected, f"{key} mismatch"

    def test_authorization_task_id(self, authorization):
        assert authorization["task_id"] == "RC-COMBINE-V2-5101-5400"

    def test_authorization_type(self, authorization):
        assert authorization.get("authorization_type") == "v7_identity_fidelity_refinement_generation"


class TestSubmittedWorkflow:
    def test_workflow_type(self, submitted_workflow):
        assert submitted_workflow["workflow_type"] == "v7_identity_fidelity_locked_refinement"

    def test_task_id(self, submitted_workflow):
        assert submitted_workflow["task_id"] == "RC-COMBINE-V2-5101-5400"

    def test_positive_prompt_present(self, submitted_workflow):
        prompt = submitted_workflow.get("positive_prompt", "")
        assert "young" in prompt.lower()
        assert "fantasy" in prompt.lower()
        assert "white hair" in prompt.lower()
        assert not any(bad in prompt.lower() for bad in ["elderly", "old woman", "wrinkles"])

    def test_negative_prompt_present(self, submitted_workflow):
        neg = submitted_workflow.get("negative_prompt", "")
        assert "elderly" in neg.lower()
        assert "wrinkles" in neg.lower()
        assert "passport" in neg.lower()

    def test_refinement_parameters(self, submitted_workflow):
        params = submitted_workflow.get("refinement_parameters", {})
        assert params.get("denoising_strength", 1.0) <= 0.6
        assert params.get("cfg_scale", 0) == 6.5

    def test_concept_reference_asset(self, submitted_workflow):
        ref = submitted_workflow.get("concept_reference_asset", "")
        assert "v6_candidate" in ref

    def test_quality_reference_asset(self, submitted_workflow):
        ref = submitted_workflow.get("quality_reference_asset", "")
        assert "targeted_refinement" in ref

    def test_identity_constraints_applied(self, submitted_workflow):
        constraints = submitted_workflow.get("identity_constraints_applied", {})
        assert constraints.get("age_lock") is True
        assert constraints.get("identity_lock") is True
        assert constraints.get("style_lock") is True
        assert constraints.get("wardrobe_lock") is True
        assert constraints.get("background_lock") is True

    def test_quality_traits_transferred(self, submitted_workflow):
        traits = submitted_workflow.get("quality_traits_transferred", [])
        assert "natural_skin_texture" in traits
        assert "better_eye_realism" in traits
        assert "less_plastic_gloss" in traits

    def test_forbidden_transformations(self, submitted_workflow):
        forbidden = submitted_workflow.get("forbidden_transformations", [])
        assert any("elderly" in f for f in forbidden)
        assert any("age" in f for f in forbidden)

    def test_generation_count_one(self, submitted_workflow):
        assert submitted_workflow["generation_count"] == 1

    def test_workflow_payload_has_nodes(self, submitted_workflow):
        payload = submitted_workflow.get("workflow_payload", {})
        assert len(payload) >= 7
        node_types = [n.get("class_type") for n in payload.values() if isinstance(n, dict)]
        assert "CheckpointLoaderSimple" in node_types
        assert "CLIPTextEncode" in node_types
        assert "KSampler" in node_types
        assert "EmptyLatentImage" in node_types
        assert "VAEDecode" in node_types
        assert "SaveImage" in node_types


class TestOutputsManifest:
    def test_manifest_exists(self, outputs_manifest):
        assert outputs_manifest["manifest_type"] == "v7_identity_fidelity_outputs_manifest"

    def test_workflow_submitted(self, outputs_manifest):
        assert outputs_manifest["workflow_submitted"] is True

    def test_generation_count(self, outputs_manifest):
        assert outputs_manifest["generation_count"] == 1

    def test_no_second_generation(self, outputs_manifest):
        assert outputs_manifest["second_generation_attempted"] is False

    def test_visual_qa_not_executed(self, outputs_manifest):
        assert outputs_manifest["visual_acceptance_executed"] is False

    def test_assembly_not_executed(self, outputs_manifest):
        assert outputs_manifest["assembly_executed"] is False

    def test_downstream_not_executed(self, outputs_manifest):
        assert outputs_manifest["downstream_executed"] is False

    def test_production_not_accepted(self, outputs_manifest):
        assert outputs_manifest["production_accepted"] is False


class TestResultArtifact:
    def test_result_schema(self, result):
        for key, expected in RESULT_SCHEMA.items():
            assert result.get(key) == expected, f"{key} mismatch"

    def test_task_id(self, result):
        assert result["task_id"] == "RC-COMBINE-V2-5101-5400"

    def test_package_used(self, result):
        assert result["v7_identity_fidelity_package_used"] is True

    def test_concept_reference_used(self, result):
        assert result["concept_reference_used"] is True

    def test_quality_reference_used(self, result):
        assert result["quality_reference_used"] is True


class TestOperatorReviewPacket:
    def test_review_packet_created(self, review_packet):
        assert review_packet["packet_type"] == "v7_identity_fidelity_operator_review_packet"

    def test_review_questions_present(self, review_packet):
        questions = review_packet.get("review_questions", {})
        assert "concept_preserved" in questions
        assert "quality_traits_transferred" in questions
        assert "age_drift_absent" in questions
        assert "fantasy_style_preserved" in questions

    def test_review_manual_required(self, review_packet):
        questions = review_packet.get("review_questions", {})
        assert questions["concept_preserved"] == "manual_review_required"
        assert questions["quality_traits_transferred"] == "manual_review_required"
        assert questions["age_drift_absent"] == "manual_review_required"
        assert questions["fantasy_style_preserved"] == "manual_review_required"
        assert questions["production_accepted"] is False

    def test_next_action(self, review_packet):
        assert review_packet["next_allowed_action"] == "operator_visual_review_required"

    def test_concept_reference_in_packet(self, review_packet):
        assert review_packet.get("concept_reference_exists") is True

    def test_quality_reference_in_packet(self, review_packet):
        assert review_packet.get("quality_reference_exists") is True


class TestArtifactIndexState:
    def test_current_state(self, artifact_index):
        assert artifact_index["current_state"] == "operator_visual_review_required"

    def test_next_allowed_action(self, artifact_index):
        assert artifact_index["next_allowed_action"] == "operator_visual_review_required"

    def test_production_accepted_false(self, artifact_index):
        assert artifact_index["production_accepted"] is False

    def test_assembly_allowed_false(self, artifact_index):
        assert artifact_index.get("assembly_allowed") is False

    def test_downstream_allowed_false(self, artifact_index):
        assert artifact_index.get("downstream_allowed") is False

    def test_visual_acceptance_not_executed(self, artifact_index):
        assert artifact_index["visual_acceptance_executed"] is False

    def test_generation_performed(self, artifact_index):
        assert artifact_index["generation_performed"] is True

    def test_no_second_generation(self, artifact_index):
        assert artifact_index["second_generation_attempted"] is False

    def test_v7_artifacts_referenced(self, artifact_index):
        assert artifact_index.get("v7_identity_fidelity_generation_authorization") is not None
        assert artifact_index.get("v7_identity_fidelity_submitted_workflow") is not None
        assert artifact_index.get("v7_identity_fidelity_outputs_manifest") is not None
        assert artifact_index.get("v7_identity_fidelity_result") is not None
        assert artifact_index.get("v7_identity_fidelity_operator_review_packet") is not None
