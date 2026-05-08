"""Tests for QA reference memory module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.reference_memory import (
    add_feedback_entry,
    get_negative_references,
    get_positive_references,
    load_operator_feedback_memory,
    save_negative_reference,
)


class TestOperatorFeedbackMemory:
    def test_load_empty_memory(self, tmp_path):
        memory = load_operator_feedback_memory(tmp_path)
        assert memory == {"feedback_entries": []}

    def test_add_feedback_entry(self, tmp_path):
        entry = add_feedback_entry(
            feedback_dir=tmp_path,
            candidate_version="v12",
            asset_path="output/assets/test.png",
            label="negative",
            failed_regions=["mouth", "teeth"],
            defects=["bad_teeth", "unnatural_mouth"],
            operator_comment="teeth do not pass visual approval",
        )
        assert entry["candidate_version"] == "v12"
        assert entry["label"] == "negative"
        assert "timestamp" in entry

        # Verify persisted
        memory = load_operator_feedback_memory(tmp_path)
        assert len(memory["feedback_entries"]) == 1

    def test_get_negative_references(self, tmp_path):
        add_feedback_entry(tmp_path, "v12", "asset1.png", "negative", defects=["bad_teeth"])
        add_feedback_entry(tmp_path, "v12", "asset2.png", "positive", defects=[])
        negs = get_negative_references(tmp_path)
        assert len(negs) == 1
        assert negs[0]["candidate_version"] == "v12"

    def test_get_positive_references(self, tmp_path):
        add_feedback_entry(tmp_path, "v12", "asset1.png", "negative", defects=["bad_teeth"])
        add_feedback_entry(tmp_path, "v12", "asset2.png", "positive", defects=[])
        pos = get_positive_references(tmp_path)
        assert len(pos) == 1
        assert pos[0]["asset_path"] == "asset2.png"

    def test_multiple_feedback_entries(self, tmp_path):
        add_feedback_entry(tmp_path, "v12", "asset1.png", "negative")
        add_feedback_entry(tmp_path, "v12", "asset2.png", "negative")
        add_feedback_entry(tmp_path, "v13", "asset3.png", "positive")
        memory = load_operator_feedback_memory(tmp_path)
        assert len(memory["feedback_entries"]) == 3


class TestNegativeReference:
    def test_save_negative_reference(self, tmp_path):
        ref = save_negative_reference(
            ref_dir=tmp_path,
            candidate_version="v12",
            asset_path="output/assets/test.png",
            failed_regions=["mouth", "teeth"],
            defects=["bad_teeth"],
            operator_comment="teeth do not pass visual approval",
        )
        assert ref["label"] == "negative"
        assert ref["candidate_version"] == "v12"

        # Verify file exists
        ref_file = tmp_path / "negative" / "v12_bad_teeth_reference.json"
        assert ref_file.exists()

        # Verify file contents
        with open(ref_file) as f:
            data = json.load(f)
        assert data["asset_path"] == "output/assets/test.png"

    def test_negative_reference_has_expected_fields(self, tmp_path):
        ref = save_negative_reference(
            ref_dir=tmp_path,
            candidate_version="v12",
            asset_path="output/assets/combine_v2_v12_candidate_1778235995_00001_.png",
            failed_regions=["mouth", "teeth", "lips"],
            defects=["bad_teeth", "unnatural_mouth", "lip_teeth_boundary_failed"],
            operator_comment="teeth do not pass visual approval",
        )
        assert ref["failed_regions"] == ["mouth", "teeth", "lips"]
        assert len(ref["defects"]) == 3
