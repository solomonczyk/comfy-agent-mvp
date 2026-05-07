"""RC-COMBINE-V2-4801-5100 — Test V7 identity/fidelity refinement package and generation gate.

Verifies:
- V7 identity/fidelity-locked refinement package created
- V7 generation gate created and closed
- generation_allowed_now=false
- new_generation_blocked
- production_accepted=false
- assembly/downstream blocked
"""

import json
from pathlib import Path
import pytest


IDENTITY_FIDELITY_SCHEMA = {
    "package_type": "v7_identity_fidelity_locked_refinement",
    "generation_not_performed": True,
    "operator_authorization_required": True,
}

GENERATION_GATE_SCHEMA = {
    "gate_type": "v7_identity_fidelity_generation",
    "generation_allowed_now": False,
    "requires_operator_authorization": True,
    "max_new_generations": 1,
    "blind_retry_allowed": False,
    "second_generation_allowed": False,
    "visual_acceptance_allowed": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_acceptance_allowed": False,
    "generation_executed": False,
    "comfyui_submit_executed": False,
    "visual_acceptance_executed": False,
    "assembly_executed": False,
    "downstream_executed": False,
    "production_accepted": False,
}


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def identity_fidelity_package(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_locked_refinement_package.json"
    if not path.exists():
        pytest.skip("V7 identity fidelity refinement package not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def generation_gate(project_root):
    path = project_root / "output" / "control" / "combine_v2_v7_identity_fidelity_generation_gate.json"
    if not path.exists():
        pytest.skip("V7 generation gate not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def artifact_index(project_root):
    path = project_root / "output" / "control" / "artifact_index.json"
    if not path.exists():
        pytest.skip("Artifact index not found")
    with open(path) as f:
        return json.load(f)


class TestIdentityFidelityRefinementPackage:
    def test_package_schema(self, identity_fidelity_package):
        for key, expected in IDENTITY_FIDELITY_SCHEMA.items():
            assert identity_fidelity_package.get(key) == expected, f"{key} mismatch"

    def test_task_id(self, identity_fidelity_package):
        assert identity_fidelity_package["task_id"] == "RC-COMBINE-V2-4801-5100"

    def test_dual_reference_strategy_present(self, identity_fidelity_package):
        strategy = identity_fidelity_package.get("dual_reference_strategy", {})
        assert strategy.get("concept_reference") == "previous_v6_fantasy_candidate"
        assert strategy.get("quality_reference") == "v6_targeted_refinement_elderly_portrait"

    def test_preserved_from_v6_fantasy_candidate(self, identity_fidelity_package):
        preserved = identity_fidelity_package.get("preserved_from_previous_v6_fantasy_candidate", {})
        assert preserved.get("character_age") is not None
        assert preserved.get("fantasy_portrait_style") is True
        assert preserved.get("white_hair_direction") is not None
        assert preserved.get("blue_fantasy_background_mood") is True
        assert preserved.get("elegant_white_dress_wardrobe") is True
        assert preserved.get("close_portrait_framing") is True
        assert preserved.get("soft_clean_lighting") is True
        assert preserved.get("attractive_fantasy_character_identity") is True

    def test_transferred_from_quality_reference(self, identity_fidelity_package):
        transferred = identity_fidelity_package.get("transferred_from_quality_reference_traits", {})
        assert len(transferred) >= 6
        assert "natural_skin_texture" in transferred
        assert "better_eye_realism" in transferred
        assert "less_plastic_gloss" in transferred
        assert "believable_facial_micro_detail" in transferred
        assert "cleaner_lighting" in transferred
        assert "realistic_facial_structure" in transferred

    def test_forbidden_transformations(self, identity_fidelity_package):
        forbidden = identity_fidelity_package.get("explicit_forbidden_transformations", [])
        assert any("elderly" in f for f in forbidden)
        assert any("age increase" in f or "age_increase" in f for f in forbidden)
        assert any("wrinkle" in f for f in forbidden)

    def test_identity_fidelity_constraints_present(self, identity_fidelity_package):
        constraints = identity_fidelity_package.get("identity_fidelity_constraints", {})
        assert "age_lock" in constraints
        assert "identity_lock" in constraints
        assert "style_lock" in constraints
        assert "wardrobe_lock" in constraints
        assert "background_lock" in constraints

    def test_age_lock_active(self, identity_fidelity_package):
        age_lock = identity_fidelity_package.get("identity_fidelity_constraints", {}).get("age_lock", {})
        assert age_lock.get("enabled") is True
        assert "young" in age_lock.get("value", "").lower()

    def test_style_lock_active(self, identity_fidelity_package):
        style_lock = identity_fidelity_package.get("identity_fidelity_constraints", {}).get("style_lock", {})
        assert style_lock.get("enabled") is True
        assert "fantasy" in style_lock.get("value", "").lower()

    def test_prompt_anchors_present(self, identity_fidelity_package):
        positive = identity_fidelity_package.get("prompt_anchors_positive", [])
        negative = identity_fidelity_package.get("prompt_anchors_negative", [])
        assert len(positive) >= 6
        assert len(negative) >= 6

    def test_denoising_reduced(self, identity_fidelity_package):
        params = identity_fidelity_package.get("refinement_parameters", {})
        assert params.get("denoising_strength", 1.0) < 0.7, "Denoising must be reduced to preserve identity"

    def test_elderly_age_drift_forbidden_in_v7(self, identity_fidelity_package):
        forbidden = identity_fidelity_package.get("explicit_forbidden_transformations", [])
        assert any("elderly" in f for f in forbidden)
        assert any("age" in f for f in forbidden)
        age_lock = identity_fidelity_package.get("identity_fidelity_constraints", {}).get("age_lock", {})
        negative = age_lock.get("negative_guard", "")
        assert "elderly" in negative or "old" in negative


class TestIdentityFidelityGenerationGate:
    def test_gate_schema(self, generation_gate):
        for key, expected in GENERATION_GATE_SCHEMA.items():
            assert generation_gate.get(key) == expected, f"{key} mismatch"

    def test_task_id(self, generation_gate):
        assert generation_gate["task_id"] == "RC-COMBINE-V2-4801-5100"

    def test_generation_blocked(self, generation_gate):
        assert generation_gate["generation_allowed_now"] is False
        assert generation_gate["requires_operator_authorization"] is True

    def test_new_generation_blocked(self, generation_gate):
        assert generation_gate["max_new_generations"] == 1
        assert generation_gate["second_generation_allowed"] is False
        assert generation_gate["blind_retry_allowed"] is False

    def test_assembly_downstream_blocked(self, generation_gate):
        assert generation_gate["assembly_allowed"] is False
        assert generation_gate["downstream_allowed"] is False
        assert generation_gate["production_acceptance_allowed"] is False
        assert generation_gate["visual_acceptance_allowed"] is False

    def test_no_execution_occurred(self, generation_gate):
        assert generation_gate["generation_executed"] is False
        assert generation_gate["comfyui_submit_executed"] is False
        assert generation_gate["visual_acceptance_executed"] is False
        assert generation_gate["assembly_executed"] is False
        assert generation_gate["downstream_executed"] is False
        assert generation_gate["production_accepted"] is False

    def test_state_transition(self, generation_gate):
        assert generation_gate["current_state"] == "v7_identity_fidelity_generation_authorization_required"
        assert generation_gate["next_allowed_action"] == "v7_identity_fidelity_generation_authorization_required"

    def test_next_generation_command_present(self, generation_gate):
        cmd = generation_gate.get("next_generation_command", {})
        assert cmd.get("command_type") == "cli_combine_command"


class TestArtifactIndexState:
    def test_production_accepted_false(self, artifact_index):
        assert artifact_index["production_accepted"] is False

    def test_assembly_downstream_blocked(self, artifact_index):
        assert artifact_index.get("assembly_allowed") is False
        assert artifact_index["downstream_allowed"] is False

    def test_current_best_concept_candidate(self, artifact_index):
        assert artifact_index.get("current_best_concept_candidate") == "previous_v6_fantasy_candidate"

    def test_current_best_quality_reference(self, artifact_index):
        assert artifact_index.get("current_best_quality_reference") == "v6_targeted_refinement_elderly_portrait"

    def test_current_state(self, artifact_index):
        assert artifact_index["current_state"] == "v7_identity_fidelity_generation_authorization_required"

    def test_next_allowed_action(self, artifact_index):
        assert artifact_index["next_allowed_action"] == "v7_identity_fidelity_generation_authorization_required"
