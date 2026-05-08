"""Tests for editorial timeline model."""
import json
import pytest
from app.editorial.timeline_model import (
    TimelineModel,
    SceneContract,
    ShotContract,
    AssetPlacement,
)


class TestTimelineModelSerializable:
    def test_timeline_to_json(self):
        model = TimelineModel(project_id="test_project")
        raw = model.to_dict()
        assert raw["project_id"] == "test_project"
        assert raw["timeline_version"] == "mvp_v1"
        text = model.to_json()
        parsed = json.loads(text)
        assert parsed["project_id"] == "test_project"

    def test_timeline_roundtrip(self):
        model = TimelineModel(project_id="test_rt")
        scene = SceneContract(scene_id="s1", duration_sec=10.0)
        model.add_scene(scene)
        data = model.to_dict()
        restored = TimelineModel.from_dict(data)
        assert restored.project_id == "test_rt"
        assert len(restored.scenes) == 1
        assert restored.scenes[0].scene_id == "s1"

    def test_timeline_from_json(self):
        text = '{"project_id": "from_json", "timeline_version": "mvp_v1", "fps": 24, "resolution": {"width": 1344, "height": 768}, "tracks": {"video_main": [], "video_overlay": [], "audio_voice": [], "audio_music": [], "subtitles": [], "effects": []}, "scenes": [], "markers": [], "operations": [], "operator_review_required": true, "final_render_allowed": false}'
        model = TimelineModel.from_json(text)
        assert model.project_id == "from_json"

    def test_timeline_default_final_render_allowed_false(self):
        model = TimelineModel()
        assert model.final_render_allowed is False

    def test_timeline_default_operator_review_required_true(self):
        model = TimelineModel()
        assert model.operator_review_required is True


class TestSceneShotContract:
    def test_scene_contract_valid(self):
        scene = SceneContract(scene_id="scene_01", duration_sec=30.0)
        assert scene.validate() == []

    def test_scene_contract_empty_id(self):
        scene = SceneContract(scene_id="")
        errs = scene.validate()
        assert any("scene_id must be non-empty" in e for e in errs)

    def test_scene_contract_negative_duration(self):
        scene = SceneContract(scene_id="s1", duration_sec=-1)
        errs = scene.validate()
        assert any("duration_sec must be >= 0" in e for e in errs)

    def test_scene_contract_invalid_status(self):
        scene = SceneContract(scene_id="s1", status="invalid_status")
        errs = scene.validate()
        assert any("status must be one of" in e for e in errs)

    def test_shot_contract_valid(self):
        shot = ShotContract(shot_id="shot_001")
        assert shot.validate() == []

    def test_shot_contract_empty_id(self):
        shot = ShotContract(shot_id="")
        errs = shot.validate()
        assert any("shot_id must be non-empty" in e for e in errs)

    def test_shot_contract_negative_duration(self):
        shot = ShotContract(shot_id="s1", duration_sec=-5)
        errs = shot.validate()
        assert any("duration_sec must be >= 0" in e for e in errs)

    def test_shot_contract_invalid_fit_policy(self):
        shot = ShotContract(shot_id="s1", fit_policy="invalid_fit")
        errs = shot.validate()
        assert any("fit_policy must be one of" in e for e in errs)


class TestTimelineModelValidation:
    def test_validate_tracks_passes(self):
        model = TimelineModel()
        assert model.validate_tracks() == []

    def test_validate_tracks_missing(self):
        model = TimelineModel()
        model.tracks = {}
        errs = model.validate_tracks()
        assert len(errs) > 0
        assert any("missing required track" in e for e in errs)

    def test_validate_scene_duplicate(self):
        model = TimelineModel()
        model.add_scene(SceneContract(scene_id="dup"))
        model.add_scene(SceneContract(scene_id="dup"))
        errs = model.validate()
        assert any("duplicate scene_id" in e for e in errs)
