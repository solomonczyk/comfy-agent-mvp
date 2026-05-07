"""RC-COMBINE-V2-3901-4200 — Test V6 candidate freeze and operator visual review artifacts.

Tests that freeze artifacts are correctly structured and consistent.
"""

import json
import tempfile
from pathlib import Path
import pytest


FREEZE_RESULT_SCHEMA = {
    "task_id": "RC-COMBINE-V2-3901-4200",
    "v6_candidate_found": True,
    "v6_candidate_frozen": True,
    "candidate_is_improved": True,
    "candidate_better_than_previous": True,
    "production_accepted": False,
    "new_generation_performed": False,
    "retry_attempted": False,
    "visual_acceptance_executed": False,
    "assembly_executed": False,
    "downstream_executed": False,
    "current_state": "targeted_visual_refinement_plan_required",
    "next_allowed_action": "targeted_visual_refinement_plan_required",
    "visual_progress_confirmed": True,
}

OPERATOR_REVIEW_SCHEMA = {
    "candidate_is_improved": True,
    "candidate_better_than_previous": True,
    "production_accepted": False,
    "remaining_defects": [
        "eye/eyelash artifacts",
        "possible eye symmetry issue",
        "over-smoothed skin",
        "AI-gloss/plastic look",
        "minor fabric/detail artifacts"
    ],
    "next_action": "targeted_visual_refinement_plan_required",
}

REFINEMENT_PLAN_SCHEMA = {
    "plan_type": "targeted_visual_refinement_plan",
    "task_id": "RC-COMBINE-V2-3901-4200",
    "v6_candidate_frozen": True,
    "visual_progress_confirmed": True,
    "production_accepted": False,
    "generation_forbidden": True,
}


@pytest.fixture
def real_freeze_result():
    path = Path("data/rc2_multishot1_ep01/output/control/combine_v2_v6_candidate_freeze_result.json")
    if not path.exists():
        pytest.skip("Real freeze result not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def real_outputs_manifest():
    path = Path("data/rc2_multishot1_ep01/output/control/combine_v2_v6_candidate_outputs_manifest.json")
    if not path.exists():
        pytest.skip("Real outputs manifest not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def real_operator_review():
    path = Path("data/rc2_multishot1_ep01/output/control/combine_v2_v6_operator_visual_review.json")
    if not path.exists():
        pytest.skip("Real operator review not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def real_refinement_plan():
    path = Path("data/rc2_multishot1_ep01/output/control/combine_v2_v6_targeted_refinement_plan.json")
    if not path.exists():
        pytest.skip("Real refinement plan not found")
    with open(path) as f:
        return json.load(f)


class TestV6FreezeResultArtifact:
    """Tests for combine_v2_v6_candidate_freeze_result.json"""

    def test_freeze_result_has_all_required_fields(self, real_freeze_result):
        for key, expected in FREEZE_RESULT_SCHEMA.items():
            assert key in real_freeze_result, f"Missing field: {key}"
            assert real_freeze_result[key] == expected, \
                f"Field {key} expected {expected} got {real_freeze_result[key]}"

    def test_freeze_result_has_asset_details(self, real_freeze_result):
        assert real_freeze_result["frozen_asset_readable"] is True
        assert isinstance(real_freeze_result["frozen_asset_size_bytes"], int)
        assert real_freeze_result["frozen_asset_size_bytes"] > 0
        assert isinstance(real_freeze_result["frozen_asset_sha256"], str)
        assert len(real_freeze_result["frozen_asset_sha256"]) == 64
        assert real_freeze_result["frozen_asset_width"] == 1024
        assert real_freeze_result["frozen_asset_height"] == 1024

    def test_freeze_result_has_operator_verdict(self, real_freeze_result):
        verdict = real_freeze_result["operator_verdict"]
        for key, expected in OPERATOR_REVIEW_SCHEMA.items():
            assert key in verdict
            assert verdict[key] == expected, \
                f"verdict.{key} expected {expected} got {verdict[key]}"

    def test_freeze_result_no_forbidden_actions(self, real_freeze_result):
        assert real_freeze_result["new_generation_performed"] is False
        assert real_freeze_result["retry_attempted"] is False
        assert real_freeze_result["visual_acceptance_executed"] is False
        assert real_freeze_result["assembly_executed"] is False
        assert real_freeze_result["downstream_executed"] is False

    def test_freeze_result_has_source_references(self, real_freeze_result):
        assert "source_generation_task" in real_freeze_result
        assert real_freeze_result["source_generation_task"] == "RC-COMBINE-V2-3601-3900"
        assert "source_clean_sdxl_v6_result" in real_freeze_result
        assert "source_clean_sdxl_v6_manifest" in real_freeze_result


class TestV6OutputsManifestArtifact:
    """Tests for combine_v2_v6_candidate_outputs_manifest.json"""

    def test_manifest_is_list(self, real_outputs_manifest):
        assert isinstance(real_outputs_manifest, list)
        assert len(real_outputs_manifest) >= 1

    def test_manifest_entry_fields(self, real_outputs_manifest):
        entry = real_outputs_manifest[0]
        required_fields = ["path", "filename", "size_bytes", "sha256",
                           "width", "height", "readable"]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

    def test_manifest_entry_values(self, real_outputs_manifest):
        entry = real_outputs_manifest[0]
        assert entry["readable"] is True
        assert entry["width"] == 1024
        assert entry["height"] == 1024
        assert entry["size_bytes"] > 0
        assert len(entry["sha256"]) == 64
        assert entry["filename"].endswith(".png")
        assert "v6" in entry["filename"].lower() or "v6" in entry["path"].lower()

    def test_manifest_has_task_references(self, real_outputs_manifest):
        entry = real_outputs_manifest[0]
        assert "source_task_id" in entry
        assert "frozen_by_task_id" in entry
        assert "frozen_timestamp" in entry


class TestV6OperatorVisualReviewArtifact:
    """Tests for combine_v2_v6_operator_visual_review.json"""

    def test_operator_review_has_required_fields(self, real_operator_review):
        assert real_operator_review["review_type"] == "operator_visual_review_v6"
        assert real_operator_review["task_id"] == "RC-COMBINE-V2-3901-4200"
        assert "candidate_asset" in real_operator_review

    def test_operator_review_asset_verification(self, real_operator_review):
        assert real_operator_review["asset_readable"] is True
        assert real_operator_review["asset_size_bytes"] == 1460975
        assert real_operator_review["asset_sha256"] == "9e40f5a2bf8e83341541839980ccbae0ff71dc5678e81acb3538dc8f6a65f617"
        assert real_operator_review["asset_width"] == 1024
        assert real_operator_review["asset_height"] == 1024

    def test_operator_review_verdict_correct(self, real_operator_review):
        verdict = real_operator_review["verdict"]
        for key, expected in OPERATOR_REVIEW_SCHEMA.items():
            assert key in verdict
            assert verdict[key] == expected

    def test_operator_review_comparison_fields(self, real_operator_review):
        for section in ["comparison_to_baseline", "comparison_to_v5"]:
            assert section in real_operator_review
            comp = real_operator_review[section]
            assert comp["still_below_production_bar"] is True

    def test_operator_review_no_false_pass(self, real_operator_review):
        assert real_operator_review["verdict"]["production_accepted"] is False


class TestV6TargetedRefinementPlanArtifact:
    """Tests for combine_v2_v6_targeted_refinement_plan.json"""

    def test_refinement_plan_has_required_fields(self, real_refinement_plan):
        for key, expected in REFINEMENT_PLAN_SCHEMA.items():
            assert key in real_refinement_plan
            assert real_refinement_plan[key] == expected

    def test_refinement_plan_no_forbidden_generation(self, real_refinement_plan):
        assert real_refinement_plan["generation_forbidden"] is True
        assert real_refinement_plan["retry_forbidden"] is True
        assert real_refinement_plan["no_new_candidate"] is True

    def test_refinement_plan_defects_structured(self, real_refinement_plan):
        assert "remaining_defects" in real_refinement_plan
        defects = real_refinement_plan["remaining_defects"]
        assert len(defects) == 5
        for defect in defects:
            for field in ["defect", "category", "severity",
                          "proposed_refinement_type", "notes"]:
                assert field in defect, f"Missing field: {field} in defect {defect['defect']}"

    def test_refinement_plan_scope(self, real_refinement_plan):
        assert real_refinement_plan["scope"] == "targeted_refinement_only"

    def test_refinement_plan_state(self, real_refinement_plan):
        assert real_refinement_plan["current_state"] == "targeted_visual_refinement_plan_required"
        assert real_refinement_plan["next_allowed_action"] == "targeted_visual_refinement_plan"


class TestArtifactIndexConsistency:
    """Tests that artifact_index.json reflects the freeze."""

    @pytest.fixture
    def artifact_index(self):
        path = Path("data/rc2_multishot1_ep01/output/control/artifact_index.json")
        if not path.exists():
            pytest.skip("artifact_index.json not found")
        with open(path) as f:
            return json.load(f)

    def test_artifact_index_state(self, artifact_index):
        assert artifact_index["current_state"] == "targeted_refinement_generation_authorization_required"
        assert artifact_index["next_allowed_action"] == "targeted_refinement_generation_authorization_required"
        assert artifact_index["v6_candidate_frozen"] is True
        assert artifact_index["visual_progress_confirmed"] is True
        assert artifact_index["production_accepted"] is False
        assert artifact_index["assembly_allowed"] is False
        assert artifact_index["downstream_allowed"] is False

    def test_artifact_index_contains_freeze_artifacts(self, artifact_index):
        v6_artifacts = [
            "combine_v2_v6_candidate_freeze_result.json",
            "combine_v2_v6_candidate_outputs_manifest.json",
            "combine_v2_v6_operator_visual_review.json",
            "combine_v2_v6_targeted_refinement_plan.json"
        ]
        artifacts_list = artifact_index.get("artifacts", [])
        for a in v6_artifacts:
            found = any(a in entry for entry in artifacts_list)
            assert found, f"Artifact {a} not found in index artifacts"

    def test_artifact_index_last_task(self, artifact_index):
        assert artifact_index["last_task_id"] in ("RC-COMBINE-V2-3901-4200", "RC-COMBINE-V2-4201-4500")
