"""Tests for Visual Reference Curator Agent.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

import json
from pathlib import Path
import pytest
import tempfile
import shutil

from app.agents.visual_reference_curator import (
    VisualReferenceCuratorRunner,
    ReferenceClassifier,
    VisualReferenceCuratorContract,
    VisualReferenceCuratorArtifacts,
)


class TestVisualReferenceCuratorAgent:
    """Test the visual reference curator agent."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial state.json
        state = {
            "current_state": "operator_visual_review_required",
            "next_allowed_action": "operator_visual_review_required",
            "production_accepted": False,
        }
        with open(control_dir / "state.json", "w") as f:
            json.dump(state, f)
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def classifier(self, temp_project_root):
        return ReferenceClassifier(temp_project_root)

    @pytest.fixture
    def runner(self, temp_project_root):
        return VisualReferenceCuratorRunner(temp_project_root)

    def test_agent_contract_exists(self):
        """Test that the agent contract exists and defines forbidden actions."""
        contract = VisualReferenceCuratorContract.get_contract()

        assert contract["role"] == "visual_reference_curator"
        assert contract["task_id"] == "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001"
        assert "perform_generation" in contract["forbidden_actions"]
        assert "attempt_retry" in contract["forbidden_actions"]
        assert "submit_to_comfyui" in contract["forbidden_actions"]
        assert "claim_visual_acceptance" in contract["forbidden_actions"]
        assert "set_production_accepted_true" in contract["forbidden_actions"]
        assert "delete_canonical_references" in contract["forbidden_actions"]
        assert contract["may_set_production_accepted"] == False
        assert contract["may_authorize_generation"] == False
        assert contract["may_authorize_retry"] == False
        assert contract["may_authorize_comfyui_submit"] == False
        assert contract["may_authorize_downstream"] == False

    def test_tool_policy_exists(self):
        """Test that the tool policy exists and defines forbidden tools."""
        policy = VisualReferenceCuratorContract.get_tool_policy()

        assert policy["policy_id"] == "visual_reference_curator_tool_policy"
        assert policy["task_id"] == "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001"
        assert policy["role"] == "visual_reference_curator"
        assert "comfyui_submit" in policy["forbidden_tools"]
        assert "image_generation" in policy["forbidden_tools"]
        assert "retry_engine" in policy["forbidden_tools"]
        assert policy["no_generation_authorized"] == True
        assert policy["no_retry_authorized"] == True
        assert policy["no_comfyui_submit_authorized"] == True
        assert policy["no_downstream_authorized"] == True

    def test_reference_roles_defined(self):
        """Test that reference roles are defined."""
        contract = VisualReferenceCuratorContract.get_contract()

        assert "identity_reference" in contract["reference_roles"]
        assert "composition_reference" in contract["reference_roles"]
        assert "quality_reference" in contract["reference_roles"]
        assert "environment_reference" in contract["reference_roles"]
        assert "character_in_environment_reference" in contract["reference_roles"]
        assert "negative_reference" in contract["reference_roles"]

    def test_classifier_classifies_closeup_as_quality_reference(self, classifier):
        """Test that close-up references are classified as quality_reference only."""
        # Create a test reference file
        reference_dir = classifier.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = reference_dir / "eye_closeup_detail.png"
        test_file.touch()
        
        result = classifier.classify_references()
        
        assert "reference_role_map" in result
        assert result["reference_role_map"]["eye_closeup_detail.png"] == "quality_reference"
        assert "eye_closeup_detail.png" in result["quality_only_refs"]

    def test_classifier_classifies_environment_as_environment_reference(self, classifier):
        """Test that environment references are classified correctly."""
        reference_dir = classifier.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = reference_dir / "scene_environment_background.png"
        test_file.touch()
        
        result = classifier.classify_references()
        
        assert result["reference_role_map"]["scene_environment_background.png"] == "environment_reference"

    def test_classifier_classifies_identity_as_identity_reference(self, classifier):
        """Test that identity references are classified correctly."""
        reference_dir = classifier.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = reference_dir / "character_identity_portrait.png"
        test_file.touch()
        
        result = classifier.classify_references()
        
        assert result["reference_role_map"]["character_identity_portrait.png"] == "identity_reference"

    def test_classifier_default_to_composition_reference(self, classifier):
        """Test that unknown references default to composition_reference."""
        reference_dir = classifier.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = reference_dir / "generic_shot.png"
        test_file.touch()
        
        result = classifier.classify_references()
        
        assert result["reference_role_map"]["generic_shot.png"] == "composition_reference"

    def test_register_negative_reference(self, classifier):
        """Test that rejected assets are registered as negative references."""
        negative_ref = classifier.register_negative_reference(
            "reference_bound_1779193743_00001_.png",
            "extreme distorted face close-up, wrong framing"
        )
        
        assert negative_ref["asset_path"] == "reference_bound_1779193743_00001_.png"
        assert negative_ref["role"] == "negative_reference"
        assert "rejection_reason" in negative_ref
        assert "registered_at" in negative_ref

    def test_diagnose_reference_misuse_detects_closeup(self, classifier):
        """Test that misuse diagnosis detects extreme face crop."""
        diagnosis = classifier.diagnose_reference_misuse(
            "extreme distorted face close-up, wrong framing"
        )
        
        assert diagnosis["misuse_detected"] == True
        assert "no_extreme_face_crop" in diagnosis["violated_constraints"]
        assert "use_normal_framing" in diagnosis["recommended_fixes"]

    def test_diagnose_reference_misuse_detects_distortion(self, classifier):
        """Test that misuse diagnosis detects distortion."""
        diagnosis = classifier.diagnose_reference_misuse(
            "distorted nose perspective, eye artifacts"
        )
        
        assert diagnosis["misuse_detected"] == True
        assert "no_distorted_perspective" in diagnosis["violated_constraints"]

    def test_diagnose_reference_misuse_detects_facial_artifacts(self, classifier):
        """Test that misuse diagnosis detects facial artifacts."""
        diagnosis = classifier.diagnose_reference_misuse(
            "eye/mouth artifacts, distorted features"
        )
        
        assert diagnosis["misuse_detected"] == True
        assert "check_eyes_mouth" in diagnosis["violated_constraints"]

    def test_diagnose_reference_misuse_detects_reference_misuse(self, classifier):
        """Test that misuse diagnosis detects reference misuse."""
        diagnosis = classifier.diagnose_reference_misuse(
            "reference misuse, wrong reference used as composition target"
        )
        
        assert diagnosis["misuse_detected"] == True
        assert "respect_reference_roles" in diagnosis["violated_constraints"]

    def test_runner_run_creates_corrective_package(self, runner):
        """Test that runner creates corrective generation package."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up, wrong framing, eye/mouth artifacts, reference misuse"
        )
        
        assert result["task_id"] == "RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001"
        assert result["verdict"] == "CORRECTIVE_PACKAGE_READY"
        assert result["next_state"] == "corrective_reference_bound_generation_authorization_required"
        assert result["next_action"] == "corrective_reference_bound_generation_authorization_required"
        assert result["generation_performed"] == False
        assert result["retry_attempted"] == False
        assert result["comfyui_submit_executed"] == False
        assert result["visual_acceptance_executed"] == False
        assert result["assembly_executed"] == False
        assert result["downstream_executed"] == False
        assert result["production_accepted"] == False

    def test_runner_run_registers_negative_reference(self, runner):
        """Test that runner registers rejected asset as negative reference."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        assert result["negative_reference"]["asset_path"] == "reference_bound_1779193743_00001_.png"
        assert result["negative_reference"]["role"] == "negative_reference"

    def test_runner_run_classifies_references(self, runner):
        """Test that runner classifies canonical references."""
        # Create some test references
        reference_dir = runner.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        (reference_dir / "eye_closeup.png").touch()
        (reference_dir / "scene_env.png").touch()
        
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        assert result["classification_results"]["total_references"] == 2
        assert len(result["classification_results"]["quality_only_refs"]) > 0

    def test_corrective_package_blocks_extreme_face_crop(self, runner):
        """Test that corrective package blocks extreme face crop."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        package = result["corrective_package"]
        assert package["framing_constraints"]["no_extreme_face_crop"] == True
        assert package["framing_constraints"]["normal_framing_required"] == True

    def test_corrective_package_checks_eyes_mouth(self, runner):
        """Test that corrective package requires checking eyes/mouth."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="eye/mouth artifacts"
        )
        
        package = result["corrective_package"]
        assert package["framing_constraints"]["check_eyes_mouth"] == True

    def test_corrective_package_respects_reference_roles(self, runner):
        """Test that corrective package respects reference roles."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="reference misuse"
        )
        
        package = result["corrective_package"]
        assert package["reference_role_constraints"]["respect_reference_roles"] == True

    def test_artifacts_generate_all(self, runner):
        """Test that all required artifacts are generated."""
        classification_results = runner.classifier.classify_references()
        negative_reference = runner.classifier.register_negative_reference(
            "reference_bound_1779193743_00001_.png",
            "extreme distorted face close-up"
        )
        misuse_diagnosis = runner.classifier.diagnose_reference_misuse(
            "extreme distorted face close-up"
        )
        corrective_package = runner._create_corrective_package(
            classification_results, misuse_diagnosis
        )
        
        runner.artifacts.generate_all_artifacts(
            classification_results,
            negative_reference,
            misuse_diagnosis,
            corrective_package,
            "corrective_reference_bound_generation_authorization_required",
            "corrective_reference_bound_generation_authorization_required",
        )
        
        control_dir = runner.project_root / "output" / "control"
        
        # Check that all required artifacts exist
        assert (control_dir / "visual_reference_curator_agent_contract.json").exists()
        assert (control_dir / "canonical_reference_role_map.json").exists()
        assert (control_dir / "reference_usage_policy.json").exists()
        assert (control_dir / "negative_reference_evidence.json").exists()
        assert (control_dir / "reference_misuse_diagnosis.json").exists()
        assert (control_dir / "corrective_reference_bound_generation_package.json").exists()
        assert (control_dir / "corrective_generation_authorization_packet.json").exists()

    def test_artifacts_update_state(self, runner):
        """Test that state is updated correctly."""
        runner.artifacts.update_state(
            "corrective_reference_bound_generation_authorization_required",
            "corrective_reference_bound_generation_authorization_required"
        )
        
        state_path = runner.project_root / "output" / "control" / "state.json"
        with open(state_path, "r") as f:
            state = json.load(f)
        
        assert state["current_state"] == "corrective_reference_bound_generation_authorization_required"
        assert state["next_allowed_action"] == "corrective_reference_bound_generation_authorization_required"
        assert state["production_accepted"] == False

    def test_artifacts_update_artifact_index(self, runner):
        """Test that artifact index is updated."""
        runner.artifacts.update_artifact_index(
            "CORRECTIVE_PACKAGE_READY",
            "corrective_reference_bound_generation_authorization_required",
            "corrective_reference_bound_generation_authorization_required"
        )
        
        index_path = runner.project_root / "output" / "control" / "artifact_index.json"
        with open(index_path, "r") as f:
            index = json.load(f)
        
        assert "last_verdict" in index
        assert index["last_verdict"] == "CORRECTIVE_PACKAGE_READY"
        assert index["last_state"] == "corrective_reference_bound_generation_authorization_required"

    def test_artifacts_update_episode_ledger(self, runner):
        """Test that episode ledger is updated."""
        runner.artifacts.update_episode_ledger(
            "CORRECTIVE_PACKAGE_READY",
            "corrective_reference_bound_generation_authorization_required",
            "corrective_reference_bound_generation_authorization_required"
        )
        
        ledger_path = runner.project_root / "output" / "control" / "episode_ledger.json"
        with open(ledger_path, "r") as f:
            ledger = json.load(f)
        
        assert len(ledger["episodes"]) > 0
        last_episode = ledger["episodes"][-1]
        assert last_episode["agent"] == "visual_reference_curator"
        assert last_episode["generation_performed"] == False
        assert last_episode["production_accepted"] == False

    def test_no_generation_performed(self, runner):
        """Test that no generation is performed."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        assert result["generation_performed"] == False
        assert result["retry_attempted"] == False
        assert result["comfyui_submit_executed"] == False

    def test_production_accepted_remains_false(self, runner):
        """Test that production_accepted remains false."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        assert result["production_accepted"] == False
        
        # Also check state file
        state_path = runner.project_root / "output" / "control" / "state.json"
        with open(state_path, "r") as f:
            state = json.load(f)
        
        assert state["production_accepted"] == False

    def test_quality_refs_cannot_become_composition_target(self, runner):
        """Test that quality refs are marked as forbidden composition targets."""
        reference_dir = runner.project_root / "reference"
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        (reference_dir / "eye_closeup.png").touch()
        
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        package = result["corrective_package"]
        quality_refs = package["reference_role_constraints"]["quality_only_refs"]
        forbidden_as_composition = package["reference_role_constraints"]["forbidden_as_composition_target"]
        
        # Quality refs should be in the forbidden list
        for ref in quality_refs:
            assert ref in forbidden_as_composition

    def test_state_transitions_to_corrective_authorization_required(self, runner):
        """Test that state transitions to corrective authorization required."""
        result = runner.run(
            latest_generated_asset="reference_bound_1779193743_00001_.png",
            operator_visual_verdict="REJECTED",
            rejection_reason="extreme distorted face close-up"
        )
        
        assert result["next_state"] == "corrective_reference_bound_generation_authorization_required"
        assert result["next_action"] == "corrective_reference_bound_generation_authorization_required"
