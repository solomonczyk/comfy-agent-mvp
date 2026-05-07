"""RC-COMBINE-V2-4201-4500 — Test targeted refinement execution package and generation gate.

Verifies:
- targeted refinement package correctly targets remaining visual defects
- genesis gate is closed (generation not allowed)
- assembly and downstream are blocked
- production_accepted is false
"""

import json
from pathlib import Path
import pytest


TARGETED_REFINEMENT_SCHEMA = {
    "package_type": "v6_targeted_refinement_execution",
    "v6_candidate_preserved": True,
    "generation_not_performed": True,
    "operator_authorization_required": True,
}

GENERATION_GATE_SCHEMA = {
    "gate_type": "targeted_refinement_generation",
    "generation_allowed_now": False,
    "requires_operator_authorization": True,
    "max_new_generations": 1,
    "blind_retry_allowed": False,
    "second_generation_allowed": False,
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
def refinement_package(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_execution_package.json"
    if not path.exists():
        pytest.skip("Refinement execution package not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def generation_gate(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_generation_gate.json"
    if not path.exists():
        pytest.skip("Generation gate not found")
    with open(path) as f:
        return json.load(f)


class TestTargetedRefinementPackage:
    def test_refinement_schema(self, refinement_package):
        for key, expected in TARGETED_REFINEMENT_SCHEMA.items():
            assert refinement_package.get(key) == expected, f"{key} mismatch"

    def test_task_id(self, refinement_package):
        assert refinement_package["task_id"] == "RC-COMBINE-V2-4201-4500"

    def test_v6_candidate_preserved(self, refinement_package):
        assert refinement_package["v6_candidate_preserved"] is True

    def test_all_defects_targeted(self, refinement_package):
        defects = refinement_package.get("target_defects", [])
        defect_descriptions = [d["defect"] for d in defects]
        expected = [
            "eye/eyelash artifacts",
            "possible eye symmetry issue",
            "over-smoothed skin",
            "AI-gloss/plastic look",
            "minor fabric/detail artifacts",
        ]
        for exp in expected:
            assert exp in defect_descriptions, f"Missing defect: {exp}"

    def test_improvements_preserved(self, refinement_package):
        preserved = refinement_package.get("previous_improvements_preserved", [])
        expected = [
            "close portrait composition",
            "face framing",
            "white hair direction",
            "blue background mood",
            "clean lighting",
            "better subject scale",
        ]
        for exp in expected:
            assert exp in preserved, f"Missing preserved improvement: {exp}"

    def test_no_whole_recipe_change(self, refinement_package):
        assert refinement_package["no_whole_recipe_change"] is True

    def test_generation_not_performed(self, refinement_package):
        assert refinement_package["generation_not_performed"] is True

    def test_refinement_strategy(self, refinement_package):
        strategy = refinement_package.get("refinement_strategy", {})
        assert strategy.get("new_workflow_required") is False
        assert strategy.get("new_checkpoint_required") is False
        assert strategy.get("random_seed_change") is False
        assert strategy.get("generation_count") == 1
        assert strategy.get("refinement_only") is True

    def test_preserved_recipe_parameters(self, refinement_package):
        params = refinement_package.get("preserved_recipe_parameters", {})
        assert params.get("checkpoint") == "juggernautXL_version2.safetensors"
        assert params.get("resolution") == "1024x1024"
        assert params.get("negative_prompt") == "unchanged"
        assert params.get("workflow_graph") == "unchanged"

    def test_adjusted_parameters_present(self, refinement_package):
        adjusted = refinement_package.get("adjusted_parameters", {})
        assert "cfg_scale" in adjusted
        assert "denoising_strength" in adjusted
        assert "positive_prompt" in adjusted


class TestGenerationGate:
    def test_gate_schema(self, generation_gate):
        for key, expected in GENERATION_GATE_SCHEMA.items():
            assert generation_gate.get(key) == expected, f"{key} mismatch at {key}"

    def test_task_id(self, generation_gate):
        assert generation_gate["task_id"] == "RC-COMBINE-V2-4201-4500"

    def test_generation_blocked(self, generation_gate):
        assert generation_gate["generation_allowed_now"] is False
        assert generation_gate["requires_operator_authorization"] is True

    def test_only_one_generation_allowed(self, generation_gate):
        assert generation_gate["max_new_generations"] == 1
        assert generation_gate["second_generation_allowed"] is False
        assert generation_gate["blind_retry_allowed"] is False

    def test_assembly_downstream_blocked(self, generation_gate):
        assert generation_gate["assembly_allowed"] is False
        assert generation_gate["downstream_allowed"] is False
        assert generation_gate["production_acceptance_allowed"] is False

    def test_no_execution_occurred(self, generation_gate):
        assert generation_gate["generation_executed"] is False
        assert generation_gate["comfyui_submit_executed"] is False
        assert generation_gate["visual_acceptance_executed"] is False
        assert generation_gate["assembly_executed"] is False
        assert generation_gate["downstream_executed"] is False
        assert generation_gate["production_accepted"] is False

    def test_state_transition(self, generation_gate):
        assert generation_gate["current_state"] == "targeted_refinement_generation_authorization_required"
        assert generation_gate["next_allowed_action"] == "targeted_refinement_generation_authorization_required"

    def test_next_generation_command_present(self, generation_gate):
        cmd = generation_gate.get("next_generation_command", {})
        assert cmd.get("command_type") == "cli_combine_command"
        assert "combine-run-clean-sdxl-v6-candidate" in cmd.get("command", "")
        assert cmd.get("generation_executed") is not True  # not executed
