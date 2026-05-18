"""Tests for fresh visual strategy quality reference integration."""

import json
import pytest
from pathlib import Path


PROJECT_ROOT = Path("f:/ComfyUI/comfy-agent-mvp")
CONTROL_DIR = PROJECT_ROOT / "data/rc2_multishot1_ep01/output/control"
FRESH_VISUAL_STRATEGY_DIR = CONTROL_DIR / "fresh_visual_strategy"
QUALITY_REFERENCES_DIR = CONTROL_DIR / "quality_references"


class TestStrategyBindsQualityReferenceAsCalibrationOnly:
    """Test that strategy binds quality reference as calibration only."""

    def test_reference_binding_exists(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        assert binding_path.exists(), "Reference binding file must exist"

    def test_binding_type_is_quality_calibration_only(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_type"] == "quality_calibration_only"

    def test_reference_id_matches(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["reference_id"] == "quality_ref_eye_closeup_001"

    def test_may_inform_quality_targets(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        semantics = data["binding_semantics"]
        assert semantics["may_inform_future_visual_quality_targets"] is True
        assert semantics["may_inform_eye_detail_quality"] is True
        assert semantics["may_inform_texture_realism_target"] is True
        assert semantics["may_inform_sharpness_and_detail_target"] is True


class TestStrategyRejectsFullCharacterUsage:
    """Test that strategy rejects full character usage."""

    def test_may_not_define_character_identity(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_define_character_identity"] is False

    def test_accepted_as_full_character_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["scope_boundary"]["accepted_as_full_character"] is False

    def test_full_character_in_forbidden_usage(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert "full_character_identity_reference" in data["forbidden_usage"]


class TestStrategyRejectsFullFaceUsage:
    """Test that strategy rejects full face usage."""

    def test_may_not_define_full_face(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_define_full_face"] is False

    def test_accepted_as_full_face_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["scope_boundary"]["accepted_as_full_face"] is False

    def test_full_face_in_forbidden_usage(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert "full_face_reference" in data["forbidden_usage"]


class TestStrategyRejectsFinalSceneUsage:
    """Test that strategy rejects final scene usage."""

    def test_may_not_define_final_scene(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_define_final_scene"] is False

    def test_accepted_as_final_scene_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["scope_boundary"]["accepted_as_final_scene"] is False

    def test_final_scene_in_forbidden_usage(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert "final_scene_asset" in data["forbidden_usage"]


class TestStrategyDoesNotOpenGenerationGate:
    """Test that strategy does not open generation gate."""

    def test_may_not_open_generation_gate(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_open_generation_gate"] is False

    def test_generation_authorization_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["integration_scope"]["generation_authorization"] is False


class TestStrategyDoesNotOpenAssemblyOrDownstream:
    """Test that strategy does not open assembly or downstream."""

    def test_may_not_open_assembly_gate(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_open_assembly_gate"] is False

    def test_assembly_authorization_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["integration_scope"]["assembly_authorization"] is False

    def test_downstream_authorization_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["integration_scope"]["downstream_authorization"] is False

    def test_assembly_in_forbidden_usage(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert "assembly_ready_asset" in data["forbidden_usage"]


class TestStrategyKeepsProductionAcceptedFalse:
    """Test that strategy keeps production_accepted false."""

    def test_may_not_set_production_accepted(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["binding_semantics"]["may_set_production_accepted"] is False

    def test_production_acceptance_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["integration_scope"]["production_acceptance"] is False

    def test_production_accepted_in_scope_boundary_is_false(self):
        binding_path = FRESH_VISUAL_STRATEGY_DIR / "fresh_visual_strategy_reference_binding.json"
        with open(binding_path) as f:
            data = json.load(f)
        assert data["scope_boundary"]["production_accepted"] is False


class TestStrategyUpdatesArtifactIndexAndLedger:
    """Test that strategy updates artifact index and ledger."""

    def test_artifact_index_state_updated(self):
        index_path = CONTROL_DIR / "artifact_index.json"
        with open(index_path) as f:
            data = json.load(f)
        assert data["current_state"] == "fresh_visual_strategy_reference_integrated"
        assert data["next_allowed_action"] == "fresh_visual_generation_plan_update_required"
        assert data["quality_reference_integrated"] is True
        assert data["quality_reference_id"] == "quality_ref_eye_closeup_001"

    def test_artifact_index_has_quality_reference_artifacts(self):
        index_path = CONTROL_DIR / "artifact_index.json"
        with open(index_path) as f:
            data = json.load(f)
        assert "fresh_visual_strategy_reference_binding" in data
        assert "fresh_visual_strategy_quality_reference_policy" in data
        assert "fresh_visual_strategy_scope_guard" in data
        assert "fresh_visual_strategy_update_report" in data

    def test_episode_ledger_has_integration_event(self):
        ledger_path = CONTROL_DIR / "episode_ledger.json"
        with open(ledger_path) as f:
            data = json.load(f)
        event_types = [entry.get("event_type") for entry in data]
        assert "fresh_visual_strategy_reference_integrated" in event_types

    def test_ledger_event_has_correct_state(self):
        ledger_path = CONTROL_DIR / "episode_ledger.json"
        with open(ledger_path) as f:
            data = json.load(f)
        integration_event = None
        for entry in data:
            if entry.get("event_type") == "fresh_visual_strategy_reference_integrated":
                integration_event = entry
                break
        assert integration_event is not None
        assert integration_event["current_state"] == "fresh_visual_strategy_reference_integrated"
        assert integration_event["next_allowed_action"] == "fresh_visual_generation_plan_update_required"
        assert integration_event["reference_id"] == "quality_ref_eye_closeup_001"


class TestStrategyPreservesGlobalDirtyCarryoverScope:
    """Test that strategy preserves global dirty carryover scope."""

    def test_proof_shows_carryover_not_modified(self):
        proof_path = CONTROL_DIR / "RC-COMBINE-V2-FRESH-VISUAL-STRATEGY-REFERENCE-INTEGRATION-001_proof.json"
        with open(proof_path) as f:
            data = json.load(f)
        assert data["carryover_modified_by_this_task"] is False
        assert data["carryover_staged_by_this_task"] is False
        assert data["carryover_committed_by_this_task"] is False
        assert data["global_dirty_carryover_preserved"] is True
