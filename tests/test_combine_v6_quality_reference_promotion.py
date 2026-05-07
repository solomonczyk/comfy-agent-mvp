"""RC-COMBINE-V2-4801-5100 — Test V6 quality reference promotion.

Verifies:
- targeted refinement promoted as quality reference (not production accepted)
- previous V6 candidate preserved as concept reference
- quality traits extracted
- concept drift detected
- elderly age drift forbidden in V7
"""

import json
from pathlib import Path
import pytest


QUALITY_REFERENCE_SCHEMA = {
    "skin_realism_improved": True,
    "eye_detail_improved": True,
    "facial_texture_improved": True,
    "lighting_naturalness_improved": True,
    "reduced_ai_plastic_look": True,
    "better_micro_detail": True,
    "more_believable_face_structure": True,
}

DRIFT_TAXONOMY_REQUIRED = [
    "age_drift",
    "identity_drift",
    "style_drift",
    "wardrobe_drift",
    "fantasy_character_direction_lost",
    "background_mood_changed",
    "target_character_not_preserved",
    "production_quality_failed_due_to_fidelity",
]


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def operator_visual_review(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_operator_visual_review.json"
    if not path.exists():
        pytest.skip("Operator visual review not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def quality_reference_traits(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_quality_reference_traits.json"
    if not path.exists():
        pytest.skip("Quality reference traits not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def drift_taxonomy(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_concept_fidelity_drift_taxonomy.json"
    if not path.exists():
        pytest.skip("Concept fidelity drift taxonomy not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def root_cause_audit(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_quality_vs_fidelity_root_cause_audit.json"
    if not path.exists():
        pytest.skip("Root cause audit not found")
    with open(path) as f:
        return json.load(f)


class TestOperatorVisualReview:
    def test_targeted_refinement_promoted_as_quality_reference(self, operator_visual_review):
        assert operator_visual_review["promoted_as_quality_reference"] is True

    def test_targeted_refinement_not_production_accepted(self, operator_visual_review):
        assert operator_visual_review["production_accepted"] is False

    def test_previous_v6_candidate_preserved_as_concept_reference(self, operator_visual_review):
        assert operator_visual_review["previous_v6_candidate_preserved_as_concept_reference"] is True

    def test_quality_better_than_previous_v6(self, operator_visual_review):
        assert operator_visual_review["quality_better_than_previous_v6"] is True

    def test_concept_fidelity_failed(self, operator_visual_review):
        assert operator_visual_review["concept_fidelity_failed"] is True

    def test_standalone_visual_quality_strong(self, operator_visual_review):
        assert operator_visual_review["standalone_visual_quality"] == "strong_reference"

    def test_reason_not_production(self, operator_visual_review):
        assert "drift" in operator_visual_review.get("reason_not_production", "")


class TestQualityReferenceTraits:
    def test_all_quality_traits_present(self, quality_reference_traits):
        traits = quality_reference_traits.get("extracted_quality_traits", {})
        for key in QUALITY_REFERENCE_SCHEMA:
            assert traits.get(key) == QUALITY_REFERENCE_SCHEMA[key], f"Missing trait: {key}"

    def test_quality_traits_extracted_flag(self, quality_reference_traits):
        assert "extracted_quality_traits" in quality_reference_traits

    def test_quality_traits_applicable_list_present(self, quality_reference_traits):
        applicable = quality_reference_traits.get("extracted_quality_traits", {}).get(
            "quality_traits_applicable_to_v7", []
        )
        assert len(applicable) > 0

    def test_quality_traits_not_applicable_list_present(self, quality_reference_traits):
        not_applicable = quality_reference_traits.get("extracted_quality_traits", {}).get(
            "quality_traits_NOT_applicable", []
        )
        assert len(not_applicable) > 0
        assert "age_characteristics_elderly" in not_applicable

    def test_source_asset_documented(self, quality_reference_traits):
        assert quality_reference_traits.get("source_asset") is not None


class TestConceptFidelityDriftTaxonomy:
    def test_all_drift_categories_detected(self, drift_taxonomy):
        categories = drift_taxonomy.get("drift_categories", {})
        for required in DRIFT_TAXONOMY_REQUIRED:
            assert required in categories, f"Missing drift category: {required}"
            assert categories[required]["detected"] is True

    def test_concept_drift_detected_flag(self, drift_taxonomy):
        assert "drift_categories" in drift_taxonomy

    def test_summary_present(self, drift_taxonomy):
        assert len(drift_taxonomy.get("summary", "")) > 0

    def test_elderly_age_drift_forbidden(self, drift_taxonomy):
        age_drift = drift_taxonomy.get("drift_categories", {}).get("age_drift", {})
        assert age_drift.get("detected") is True


class TestQualityVsFidelityRootCauseAudit:
    def test_root_causes_list_present(self, root_cause_audit):
        causes = root_cause_audit.get("root_causes", [])
        assert len(causes) >= 6

    def test_cause_prompt_age_drift(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "prompt_caused_age_drift" in causes

    def test_cause_missing_age_lock(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "missing_explicit_age_lock" in causes

    def test_cause_missing_identity_lock(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "missing_identity_concept_lock" in causes

    def test_cause_missing_wardrobe_lock(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "missing_wardrobe_lock" in causes

    def test_cause_missing_style_lock(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "missing_style_lock" in causes

    def test_cause_too_much_freedom(self, root_cause_audit):
        causes = [c["cause"] for c in root_cause_audit.get("root_causes", [])]
        assert "too_much_freedom_in_refinement_package" in causes

    def test_lesson_present(self, root_cause_audit):
        assert len(root_cause_audit.get("lesson", "")) > 0
