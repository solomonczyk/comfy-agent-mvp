"""RC-COMBINE-V2-4501-4800 — Test V6 targeted refinement generation runtime guards.

Tests that the runtime guards correctly enforce:
- operator authorization is required before generation
- only one generation is allowed
- second generation is blocked
- targeted package is required
- canonical output is registered
- visual acceptance is blocked
- production_accepted is false
- assembly and downstream are blocked
- final state requires operator visual review
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def authorization_artifact(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_generation_authorization.json"
    if not path.exists():
        pytest.skip("Authorization artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def execution_package(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_execution_package.json"
    if not path.exists():
        pytest.skip("Execution package not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def generation_gate(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_generation_gate.json"
    if not path.exists():
        pytest.skip("Generation gate not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def result_artifact(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_result.json"
    if not path.exists():
        pytest.skip("Result artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def artifact_index(project_root):
    path = project_root / "output" / "control" / "artifact_index.json"
    if not path.exists():
        pytest.skip("artifact_index.json not found")
    with open(path) as f:
        return json.load(f)


class TestOperatorAuthorizationRequired:
    def test_authorization_created(self, authorization_artifact):
        assert authorization_artifact is not None

    def test_authorization_grants_generation(self, authorization_artifact):
        assert authorization_artifact.get("operator_authorized") is True
        assert authorization_artifact.get("generation_allowed") is True

    def test_authorization_limits_to_one(self, authorization_artifact):
        assert authorization_artifact.get("max_new_generations") == 1
        assert authorization_artifact.get("second_generation_allowed") is False
        assert authorization_artifact.get("blind_retry_allowed") is False


class TestOneGenerationAllowed:
    def test_generation_count_is_one(self, result_artifact):
        assert result_artifact.get("generation_count") == 1

    def test_second_generation_not_attempted(self, result_artifact):
        assert result_artifact.get("second_generation_attempted") is False

    def test_workflow_submitted(self, result_artifact):
        assert result_artifact.get("workflow_submitted") is True

    def test_comfyui_executed(self, result_artifact):
        assert result_artifact.get("comfyui_execution") is True


class TestSecondGenerationBlocked:
    def test_gate_blocks_second(self, generation_gate):
        assert generation_gate.get("max_new_generations") == 1
        assert generation_gate.get("second_generation_allowed") is False
        assert generation_gate.get("blind_retry_allowed") is False

    def test_result_blocks_second(self, result_artifact):
        assert result_artifact.get("generation_count") <= 1

    def test_authorization_blocks_second(self, authorization_artifact):
        assert authorization_artifact.get("second_generation_allowed") is False


class TestTargetedPackageRequired:
    def test_execution_package_exists(self, execution_package):
        assert execution_package is not None

    def test_execution_package_type(self, execution_package):
        assert execution_package.get("package_type") == "v6_targeted_refinement_execution"

    def test_execution_package_params(self, execution_package):
        assert execution_package.get("no_whole_recipe_change") is True
        strategy = execution_package.get("refinement_strategy", {})
        assert strategy.get("new_workflow_required") is False
        assert strategy.get("new_checkpoint_required") is False

    def test_execution_package_generation_not_performed(self, execution_package):
        assert execution_package.get("generation_not_performed") is True


class TestCanonicalOutputRegistered:
    def test_outputs_manifest_exists(self, project_root):
        path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_outputs_manifest.json"
        assert path.exists(), "Outputs manifest not found"

    def test_canonical_outputs_in_result(self, result_artifact):
        assert result_artifact.get("canonical_outputs_registered") is True

    def test_asset_paths_in_result(self, result_artifact):
        assets = result_artifact.get("output_asset_paths", [])
        assert len(assets) >= 1
        for asset in assets:
            assert "targeted_refinement" in asset

    def test_asset_readable(self, result_artifact):
        assert result_artifact.get("asset_readable") is True
        assert len(result_artifact.get("sha256", "")) == 64


class TestVisualAcceptanceBlocked:
    def test_authorization_blocks_visual_acceptance(self, authorization_artifact):
        assert authorization_artifact.get("visual_acceptance_allowed") is False

    def test_result_visual_acceptance_not_executed(self, result_artifact):
        assert result_artifact.get("visual_acceptance_executed") is False


class TestProductionAcceptedFalse:
    def test_production_not_accepted_in_authorization(self, authorization_artifact):
        assert authorization_artifact.get("production_acceptance_allowed") is False

    def test_production_not_accepted_in_result(self, result_artifact):
        assert result_artifact.get("production_accepted") is False

    def test_production_not_accepted_in_gate(self, generation_gate):
        assert generation_gate.get("production_acceptance_allowed") is False

    def test_production_not_accepted_in_index(self, artifact_index):
        assert artifact_index.get("production_accepted") is False


class TestAssemblyDownstreamBlocked:
    def test_assembly_downstream_blocked_in_authorization(self, authorization_artifact):
        assert authorization_artifact.get("assembly_allowed") is False
        assert authorization_artifact.get("downstream_allowed") is False

    def test_assembly_downstream_not_executed_in_result(self, result_artifact):
        assert result_artifact.get("assembly_executed") is False
        assert result_artifact.get("downstream_executed") is False

    def test_assembly_downstream_blocked_in_index(self, artifact_index):
        assert artifact_index.get("assembly_allowed") is False
        assert artifact_index.get("downstream_allowed") is False


class TestOperatorReviewRequiredFinalState:
    def test_final_state_in_result(self, result_artifact):
        assert result_artifact.get("current_state") == "operator_visual_review_required"
        assert result_artifact.get("next_allowed_action") == "operator_visual_review_required"

    def test_final_state_in_index(self, artifact_index):
        assert artifact_index.get("current_state") == "operator_visual_review_required"
        assert artifact_index.get("next_allowed_action") == "operator_visual_review_required"

    def test_operator_review_packet_exists(self, project_root):
        path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_operator_review_packet.json"
        assert path.exists(), "Operator review packet not found"
