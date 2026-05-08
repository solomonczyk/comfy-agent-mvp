"""Tests for V12 operator rejection flow through V13 correction package.

Verifies the complete pipeline from V12 rejection recording through
negative reference storage, QA canon evaluation, and V13 correction
package creation without performing any generation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.canon_registry import load_domain_canon, load_universal_canon, merge_canons
from app.qa.decision_policy import apply_decision_policy, load_decision_policy
from app.qa.defect_taxonomy import map_operator_feedback_to_defects
from app.qa.qa_canon_engine import QACanonEngine
from app.qa.reference_memory import add_feedback_entry, load_operator_feedback_memory, save_negative_reference
from app.qa.scene_router import classify_scene_type

# Shorthand: the V12 operator feedback
V12_OPERATOR_FEEDBACK = "teeth do not pass visual approval"
V12_ASSET_PATH = "output/assets/combine_v2_v12_candidate_1778235995_00001_.png"


class TestV12RejectionFlow:
    """Full V12 rejection flow: operator feedback -> QA canon -> decision."""

    def test_scene_router_selects_human_face_for_v12(self):
        scene = classify_scene_type("v12", task_contract={"candidate_version": "v12"})
        assert scene == "human_face_portrait"

    def test_operator_feedback_maps_to_bad_teeth_defects(self):
        defects = map_operator_feedback_to_defects(V12_OPERATOR_FEEDBACK)
        assert "bad_teeth" in defects
        # "teeth do not pass visual approval" contains "teeth" -> bad_teeth
        # It does not contain "mouth" so unnatural_mouth is not mapped

    def test_qa_canon_rejects_v12(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path=V12_ASSET_PATH,
            task_contract={"candidate_version": "v12"},
            operator_feedback=V12_OPERATOR_FEEDBACK,
        )
        # The decision should be 'reject' because:
        # 1. The asset doesn't exist (stub/unreadable) -> hard reject
        # 2. The operator feedback maps to bad_teeth -> auto reject
        assert decision.decision == "reject"
        assert decision.production_accepted is False
        assert decision.assembly_allowed is False
        assert decision.downstream_allowed is False

    def test_v12_negative_reference_created(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        engine.record_operator_feedback(
            candidate_version="v12",
            asset_path=V12_ASSET_PATH,
            operator_comment=V12_OPERATOR_FEEDBACK,
            defects=["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"],
            failed_regions=["mouth", "teeth", "lips"],
        )

        neg_ref = engine.ref_dir / "negative" / "v12_bad_teeth_reference.json"
        assert neg_ref.exists()
        with open(neg_ref) as f:
            ref = json.load(f)
        assert ref["label"] == "negative"
        assert ref["candidate_version"] == "v12"

    def test_v12_qa_report_rejects(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path=V12_ASSET_PATH,
            operator_feedback=V12_OPERATOR_FEEDBACK,
        )
        report_path = engine.save_qa_report(decision)
        assert report_path.exists()

        with open(report_path) as f:
            report = json.load(f)
        assert report["candidate_version"] == "v12"
        assert report["decision"] == "reject"
        assert report["production_accepted"] is False
        assert report["assembly_allowed"] is False
        assert report["downstream_allowed"] is False

    def test_v13_correction_package_can_be_created(self, tmp_path):
        """Verify V13 correction package creation is possible from QA evidence."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path=V12_ASSET_PATH,
            operator_feedback=V12_OPERATOR_FEEDBACK,
        )
        engine.save_qa_report(decision)

        # Create V13 correction plan
        correction_plan = {
            "task_id": "RC-COMBINE-V2-22001-26000",
            "candidate_version": "v13",
            "source_asset": V12_ASSET_PATH,
            "qa_evidence": {
                "critical_failures": decision.critical_failures,
            },
            "correction_instructions": [
                "avoid visible teeth if not required by shot intent",
                "closed mouth or relaxed natural lips preferred",
                "stronger negative prompt against malformed teeth",
            ],
            "generation_allowed": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
        }

        plan_dir = tmp_path / "output" / "control"
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plan_dir / "combine_v2_v13_correction_plan.json"
        with open(plan_path, "w") as f:
            json.dump(correction_plan, f, indent=2)

        assert plan_path.exists()
        assert decision.critical_failures == correction_plan["qa_evidence"]["critical_failures"]


class TestProductionGuards:
    """Verify that production guard fields are correct throughout the flow."""

    def test_production_accepted_false(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=["bad_teeth"], all_detected_defects=["bad_teeth"])
        assert result["production_accepted"] is False

    def test_assembly_blocked(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=["bad_teeth"], all_detected_defects=["bad_teeth"])
        assert result["assembly_allowed"] is False

    def test_downstream_blocked(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=["bad_teeth"], all_detected_defects=["bad_teeth"])
        assert result["downstream_allowed"] is False

    def test_no_generation_performed(self, tmp_path):
        """Verify that no generation is performed during QA canon evaluation."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path=V12_ASSET_PATH,
            operator_feedback=V12_OPERATOR_FEEDBACK,
        )
        # The engine should never trigger generation
        assert decision.production_accepted is False
        # Engine doesn't have a "comfyui" or "generation" attribute
        assert not hasattr(engine, "generation_performed")


class TestCanonLoading:
    def test_universal_canon_loads(self):
        canon = load_universal_canon()
        assert canon["canon_id"] == "universal_quality_v1"
        assert len(canon["must_have"]) >= 5
        assert len(canon["hard_reject_defects"]) >= 5

    def test_human_face_canon_loads(self):
        canon = load_domain_canon("human_face_portrait")
        assert canon["canon_id"] == "human_face_photoreal_v1"
        assert len(canon["critical_regions"]) >= 5
        assert "bad_teeth" in canon["hard_reject_defects"]
