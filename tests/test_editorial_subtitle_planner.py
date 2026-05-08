"""Tests for editorial subtitle planner."""
import pytest
from app.editorial.subtitle_planner import SubtitlePlanner, SubtitleEntry


class TestSubtitlePlanValidated:
    def test_entry_added_successfully(self):
        planner = SubtitlePlanner()
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="Hello world",
            anchor_type="timecode",
            start_time="00:00:01",
            end_time="00:00:04",
            scene_id="scene_001",
        )
        errs = planner.add_entry(entry)
        assert errs == []
        assert len(planner.list_entries()) == 1


class TestSubtitleOverlapDetected:
    def test_overlapping_entries_detected(self):
        planner = SubtitlePlanner()
        e1 = SubtitleEntry(
            subtitle_id="sub_001",
            text="First",
            anchor_type="timecode",
            start_time="00:00:01",
            end_time="00:00:10",
            scene_id="scene_001",
        )
        e2 = SubtitleEntry(
            subtitle_id="sub_002",
            text="Second",
            anchor_type="timecode",
            start_time="00:00:05",
            end_time="00:00:15",
            scene_id="scene_001",
        )
        assert planner.add_entry(e1) == []
        errs = planner.add_entry(e2)
        assert any("overlaps" in e for e in errs)

    def test_non_overlapping_entries_ok(self):
        planner = SubtitlePlanner()
        e1 = SubtitleEntry(
            subtitle_id="sub_001",
            text="First",
            anchor_type="timecode",
            start_time="00:00:01",
            end_time="00:00:05",
            scene_id="scene_001",
        )
        e2 = SubtitleEntry(
            subtitle_id="sub_002",
            text="Second",
            anchor_type="timecode",
            start_time="00:00:06",
            end_time="00:00:10",
            scene_id="scene_001",
        )
        assert planner.add_entry(e1) == []
        assert planner.add_entry(e2) == []


class TestSubtitleValidation:
    def test_empty_text_rejected(self):
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="",
            anchor_type="timecode",
        )
        errs = entry.validate()
        assert any("text must be non-empty" in e for e in errs)

    def test_negative_duration_rejected(self):
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="Test",
            anchor_type="timecode",
            duration=-5,
        )
        errs = entry.validate()
        assert any("duration must be >= 0" in e for e in errs)

    def test_end_before_start(self):
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="Test",
            anchor_type="timecode",
            start_time="00:00:10",
            end_time="00:00:05",
        )
        errs = entry.validate()
        assert any("before start_time" in e for e in errs)

    def test_missing_anchor(self):
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="Test",
            anchor_type="",
        )
        errs = entry.validate()
        assert any("anchor_type is required" in e for e in errs)

    def test_unsupported_position(self):
        entry = SubtitleEntry(
            subtitle_id="sub_001",
            text="Test",
            anchor_type="timecode",
            position="invalid_position",
        )
        errs = entry.validate()
        assert any("position must be one of" in e for e in errs)

    def test_duplicate_subtitle_id(self):
        planner = SubtitlePlanner()
        e1 = SubtitleEntry(subtitle_id="dup", text="First", anchor_type="timecode")
        e2 = SubtitleEntry(subtitle_id="dup", text="Second", anchor_type="timecode")
        assert planner.add_entry(e1) == []
        errs = planner.add_entry(e2)
        assert any("duplicate subtitle_id" in e for e in errs)
