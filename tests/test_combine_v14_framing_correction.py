"""Tests for V14 framing correction package.

Verifies V13 operator rejection was recorded, framing defects registered,
and V14 correction package was created with framing/crop instructions.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

V14_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"
QA_NEG_REF_DIR = f"{V14_CONTROL_DIR}/qa/references/negative"
FRAMING_DEFECTS = [
    "head_not_fully_in_frame",
    "top_of_head_cropped",
    "over_tight_face_crop",
    "portrait_framing_failed",
]


class TestV13OperatorRejection:
    """Verify V13 operator rejection was recorded."""

    def test_v13_rejection_exists(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        assert path.exists(), "V13 operator visual rejection must exist"

    def test_v13_rejection_fields(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        with open(path) as f:
            rejection = json.load(f)

        assert rejection.get("candidate_version") == "v13"
        assert rejection.get("operator_decision") == "rejected"
        assert rejection.get("production_accepted") is False

    def test_v13_rejection_defects(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        with open(path) as f:
            rejection = json.load(f)

        assert rejection.get("rejection_reason") == "Head is not fully in frame."
        defects = rejection.get("defects", [])
        for defect in FRAMING_DEFECTS:
            assert defect in defects, f"Missing defect: {defect}"

    def test_v13_positive_traits_preserved(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        with open(path) as f:
            rejection = json.load(f)

        positives = rejection.get("positive_to_preserve", [])
        assert "face_quality" in positives
        assert "skin_detail" in positives
        assert "eye_quality" in positives
        assert "mouth_teeth_improvement" in positives
        assert "overall_realism" in positives


class TestV13NegativeFramingReference:
    """Verify V13 bad framing reference exists."""

    def test_v13_negative_framing_reference_exists(self):
        path = Path(QA_NEG_REF_DIR) / "v13_bad_framing_reference.json"
        assert path.exists(), "V13 bad framing reference must exist"

    def test_v13_negative_framing_reference_fields(self):
        path = Path(QA_NEG_REF_DIR) / "v13_bad_framing_reference.json"
        with open(path) as f:
            ref = json.load(f)

        assert ref.get("candidate_version") == "v13"
        assert ref.get("label") == "negative"
        assert ref.get("failed_regions") is not None
        for defect in FRAMING_DEFECTS:
            assert defect in ref.get("defects", []), f"Missing defect: {defect}"

    def test_v13_positive_quality_preserved_in_reference(self):
        path = Path(QA_NEG_REF_DIR) / "v13_bad_framing_reference.json"
        with open(path) as f:
            ref = json.load(f)

        preserved = ref.get("positive_quality_to_preserve", {})
        assert preserved.get("face_quality") is True
        assert preserved.get("skin_detail") is True
        assert preserved.get("eye_quality") is True
        assert preserved.get("mouth_teeth") is True
        assert preserved.get("overall_realism") is True


class TestV14FramingCorrectionPackage:
    """Verify V14 correction package created with framing fixes."""

    CORRECTION_ARTIFACTS = [
        "combine_v2_v14_correction_plan.json",
        "combine_v2_v14_prompt_patch.json",
        "combine_v2_v14_workflow_patch.json",
        "combine_v2_v14_quality_pipeline_patch.json",
    ]

    def test_all_correction_artifacts_exist(self):
        for name in self.CORRECTION_ARTIFACTS:
            assert (Path(V14_CONTROL_DIR) / name).exists(), f"Missing: {name}"

    def test_correction_plan_has_framing_goal(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_correction_plan.json"
        with open(path) as f:
            plan = json.load(f)

        assert plan.get("composition_goal") == "full head visible in frame"
        assert plan.get("framing") == "portrait with full head and hair visible"
        assert "crop_policy" in plan
        assert "safe_margin" in plan

    def test_correction_plan_has_v13_quality_preservation(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_correction_plan.json"
        with open(path) as f:
            plan = json.load(f)

        assert plan.get("preserve_quality_from_v13") is True
        assert plan.get("preserve_mouth_teeth_improvement") is True
        positives = plan.get("positive_traits_to_preserve", [])
        assert len(positives) >= 4

    def test_correction_plan_has_framing_defects_in_evidence(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_correction_plan.json"
        with open(path) as f:
            plan = json.load(f)

        evidence = plan.get("qa_evidence", {})
        critical = evidence.get("critical_failures", [])
        for defect in FRAMING_DEFECTS:
            assert defect in critical, f"Missing defect in evidence: {defect}"

    def test_prompt_patch_has_negative_framing_instructions(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_prompt_patch.json"
        with open(path) as f:
            patch = json.load(f)

        strengthened = [x.lower() for x in patch.get("negative_prompt_strengthened", [])]
        assert any("close-up" in x for x in strengthened), "Missing extreme close-up negation"
        assert any("crop" in x for x in strengthened), "Missing crop negation"
        assert any("head" in x for x in strengthened), "Missing head framing negation"

    def test_quality_pipeline_patch_has_framing_checks(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_quality_pipeline_patch.json"
        with open(path) as f:
            patch = json.load(f)

        checklist = [x.lower() for x in patch.get("qa_checklist_additions", [])]
        assert any("head" in x for x in checklist), "Missing head check in QA checklist"
        assert any("frame" in x for x in checklist), "Missing frame check in QA checklist"

    def test_production_not_accepted_in_package(self):
        for name in self.CORRECTION_ARTIFACTS:
            with open(Path(V14_CONTROL_DIR) / name) as f:
                artifact = json.load(f)
            assert artifact.get("production_accepted") is False, f"{name}: production_accepted must be False"
            assert artifact.get("assembly_allowed") is False or "assembly_allowed" not in artifact, \
                f"{name}: assembly_allowed must be False"
            assert artifact.get("downstream_allowed") is False or "downstream_allowed" not in artifact, \
                f"{name}: downstream_allowed must be False"


class TestV14OperatorFeedbackMemory:
    """Verify operator feedback memory updated with V13 framing defects."""

    def test_feedback_memory_has_v13_framing_entry(self):
        path = Path(V14_CONTROL_DIR) / "qa" / "feedback" / "operator_feedback_memory.json"
        with open(path) as f:
            memory = json.load(f)

        entries = memory.get("feedback_entries", [])
        v13_framing = [e for e in entries if e.get("candidate_version") == "v13" and "head" in str(e.get("defects", []))]
        assert len(v13_framing) >= 1, "No V13 framing entry in feedback memory"

    def test_framing_defects_in_feedback_entry(self):
        path = Path(V14_CONTROL_DIR) / "qa" / "feedback" / "operator_feedback_memory.json"
        with open(path) as f:
            memory = json.load(f)

        entries = memory.get("feedback_entries", [])
        v13_entries = [e for e in entries if e.get("candidate_version") == "v13"]
        for entry in v13_entries:
            defects = entry.get("defects", [])
            if any(d in FRAMING_DEFECTS for d in defects):
                return  # Found at least one with framing defects
        pytest.fail("No V13 feedback entry with framing defects found")
