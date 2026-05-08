"""Tests for editorial marker registry."""
import pytest
from app.editorial.marker_registry import MarkerRegistry, Marker


class TestMarkerRegistryValidatesDuplicates:
    def test_duplicate_marker_id_rejected(self):
        registry = MarkerRegistry()
        registry.set_known_scene_ids({"scene_001"})
        m1 = Marker(marker_id="dup", scene_id="scene_001", anchor_type="scene_id")
        m2 = Marker(marker_id="dup", scene_id="scene_001", anchor_type="scene_id")
        assert registry.register(m1) == []
        errs = registry.register(m2)
        assert any("duplicate marker_id" in e for e in errs)

    def test_multiple_unique_markers_ok(self):
        registry = MarkerRegistry()
        registry.set_known_scene_ids({"scene_001"})
        m1 = Marker(marker_id="m1", scene_id="scene_001", anchor_type="scene_id")
        m2 = Marker(marker_id="m2", scene_id="scene_001", anchor_type="timecode", timecode="00:00:01")
        assert registry.register(m1) == []
        assert registry.register(m2) == []
        assert len(registry.list_markers()) == 2


class TestMarkerRegistryRejectsUnknownScene:
    def test_unknown_scene_rejected(self):
        registry = MarkerRegistry()
        registry.set_known_scene_ids({"scene_001"})
        m = Marker(marker_id="bad", scene_id="scene_999", anchor_type="scene_id")
        errs = registry.register(m)
        assert any("not found in known scenes" in e for e in errs)

    def test_empty_known_scenes_with_scene_ref(self):
        registry = MarkerRegistry()
        m = Marker(marker_id="m1", scene_id="nonexistent", anchor_type="scene_id")
        errs = registry.register(m)
        assert any("not found in known scenes" in e for e in errs)


class TestMarkerValidation:
    def test_invalid_anchor_type(self):
        m = Marker(marker_id="m1", anchor_type="invalid_type")
        errs = m.validate(set())
        assert any("anchor_type must be one of" in e for e in errs)

    def test_empty_marker_id(self):
        m = Marker(marker_id="")
        errs = m.validate(set())
        assert any("marker_id must be non-empty" in e for e in errs)

    def test_invalid_timecode(self):
        m = Marker(marker_id="m1", timecode="not-a-timecode", anchor_type="timecode")
        errs = m.validate({"scene_001"})
        assert any("invalid timecode format" in e for e in errs)

    def test_valid_timecode(self):
        m = Marker(marker_id="m1", timecode="00:05:30", anchor_type="timecode")
        errs = m.validate({"scene_001"})
        assert errs == [] or not any("invalid timecode" in e for e in errs)

    def test_to_dict_list(self):
        registry = MarkerRegistry()
        registry.set_known_scene_ids({"s1"})
        registry.register(Marker(marker_id="m1", scene_id="s1", anchor_type="scene_id"))
        items = registry.to_dict_list()
        assert len(items) == 1
        assert items[0]["marker_id"] == "m1"
