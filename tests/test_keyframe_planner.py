"""Tests for MK-P4 — KeyframePlanner.

Coverage:
  - returns list[SceneKeyframePlan], one per scene
  - total_frames equals round(duration_sec * fps)
  - first keyframe timestamp is 0.0
  - last keyframe timestamp equals duration_hint_sec
  - keyframe count matches len(keyframe_hints) when hints provided
  - when hints empty → count equals min_keyframes
  - hint values match scene.keyframe_hints when provided
  - when hints empty → hints are auto-generated strings, not empty
  - keyframe indices are 0-based and sequential
  - plan() is idempotent
  - multi-scene brief → correct plan count
  - min_keyframes=3 produces at least 3 keyframes when hints absent
"""
from __future__ import annotations

import math

import pytest

from app.brief.models import BriefModel, CharacterDef, ProjectMeta, SceneDef
from app.keyframes.models import SceneKeyframePlan
from app.keyframes.planner import KeyframePlanner


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_brief(*scenes: SceneDef, fps: int = 8) -> BriefModel:
    return BriefModel(
        meta=ProjectMeta(title="Test", target_duration_sec=10.0, fps=fps),
        characters=[CharacterDef(name="A", visual_description="desc")],
        scenes=list(scenes),
    )


def _scene(
    scene_id: str = "s01",
    duration: float = 3.0,
    hints: list[str] | None = None,
) -> SceneDef:
    return SceneDef(
        scene_id=scene_id,
        characters_in_scene=[],
        action="test",
        duration_hint_sec=duration,
        keyframe_hints=hints if hints is not None else [],
    )


# ── return type ───────────────────────────────────────────────────────────────

def test_returns_list_of_scene_keyframe_plans():
    brief = _make_brief(_scene())
    result = KeyframePlanner().plan(brief)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], SceneKeyframePlan)


def test_multi_scene_plan_count():
    brief = _make_brief(_scene("s01"), _scene("s02"), _scene("s03"))
    result = KeyframePlanner().plan(brief)
    assert len(result) == 3


def test_scene_id_preserved():
    brief = _make_brief(_scene("s07"))
    result = KeyframePlanner().plan(brief)
    assert result[0].scene_id == "s07"


# ── total_frames ──────────────────────────────────────────────────────────────

def test_total_frames_equals_round_duration_times_fps():
    brief = _make_brief(_scene(duration=3.0), fps=8)
    plan = KeyframePlanner().plan(brief)[0]
    assert plan.total_frames == round(3.0 * 8)


def test_total_frames_non_integer_duration():
    brief = _make_brief(_scene(duration=2.5), fps=8)
    plan = KeyframePlanner().plan(brief)[0]
    assert plan.total_frames == round(2.5 * 8)


# ── timestamps ────────────────────────────────────────────────────────────────

def test_first_keyframe_timestamp_is_zero():
    brief = _make_brief(_scene(duration=3.0))
    plan = KeyframePlanner().plan(brief)[0]
    assert plan.keyframes[0].timestamp_sec == 0.0


def test_last_keyframe_timestamp_equals_duration():
    duration = 3.0
    brief = _make_brief(_scene(duration=duration))
    plan = KeyframePlanner().plan(brief)[0]
    assert plan.keyframes[-1].timestamp_sec == duration


# ── keyframe count ────────────────────────────────────────────────────────────

def test_keyframe_count_matches_hints_length_when_provided():
    hints = ["sit", "look up", "reach"]
    brief = _make_brief(_scene(hints=hints))
    plan = KeyframePlanner().plan(brief)[0]
    assert len(plan.keyframes) == len(hints)


def test_keyframe_count_equals_min_when_hints_empty():
    brief = _make_brief(_scene(hints=[]))
    plan = KeyframePlanner(min_keyframes=2).plan(brief)[0]
    assert len(plan.keyframes) == 2


def test_min_keyframes_3_produces_3_when_hints_empty():
    brief = _make_brief(_scene(hints=[]))
    plan = KeyframePlanner(min_keyframes=3).plan(brief)[0]
    assert len(plan.keyframes) == 3


def test_min_keyframes_respected_when_hints_fewer():
    # 1 hint but min_keyframes=3 → should produce 3
    brief = _make_brief(_scene(hints=["only_one"]))
    plan = KeyframePlanner(min_keyframes=3).plan(brief)[0]
    assert len(plan.keyframes) >= 3


# ── hint values ───────────────────────────────────────────────────────────────

def test_hint_values_match_scene_hints():
    hints = ["кот сидит", "взгляд вверх", "лунный свет"]
    brief = _make_brief(_scene(hints=hints))
    plan = KeyframePlanner().plan(brief)[0]
    for kf, expected in zip(plan.keyframes, hints):
        assert kf.hint == expected


def test_auto_hints_not_empty_when_no_hints():
    brief = _make_brief(_scene(hints=[]))
    plan = KeyframePlanner().plan(brief)[0]
    for kf in plan.keyframes:
        assert kf.hint != ""


def test_auto_hints_are_strings():
    brief = _make_brief(_scene(hints=[]))
    plan = KeyframePlanner().plan(brief)[0]
    for kf in plan.keyframes:
        assert isinstance(kf.hint, str)


# ── indices ───────────────────────────────────────────────────────────────────

def test_indices_are_zero_based():
    brief = _make_brief(_scene(hints=["a", "b", "c"]))
    plan = KeyframePlanner().plan(brief)[0]
    assert plan.keyframes[0].index == 0


def test_indices_are_sequential():
    hints = ["a", "b", "c", "d"]
    brief = _make_brief(_scene(hints=hints))
    plan = KeyframePlanner().plan(brief)[0]
    for i, kf in enumerate(plan.keyframes):
        assert kf.index == i


# ── idempotency ───────────────────────────────────────────────────────────────

def test_idempotent():
    brief = _make_brief(_scene(hints=["x", "y"]))
    p = KeyframePlanner()
    r1 = p.plan(brief)
    r2 = p.plan(brief)
    assert r1[0].keyframes[0].timestamp_sec == r2[0].keyframes[0].timestamp_sec
    assert r1[0].keyframes[-1].timestamp_sec == r2[0].keyframes[-1].timestamp_sec
    assert [kf.hint for kf in r1[0].keyframes] == [kf.hint for kf in r2[0].keyframes]


# ── scene splitting ───────────────────────────────────────────────────────────

def test_long_scene_split_into_sub_scenes():
    brief = _make_brief(_scene("s01", duration=10.0))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    assert len(result) == 2


def test_sub_scene_ids_follow_alpha_suffix_pattern():
    brief = _make_brief(_scene("s01", duration=10.0))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    assert result[0].scene_id == "s01a"
    assert result[1].scene_id == "s01b"


def test_sub_scene_total_duration_equals_original():
    brief = _make_brief(_scene("s01", duration=10.0))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    total = sum(p.duration_sec for p in result)
    assert abs(total - 10.0) < 1e-9


def test_each_sub_scene_duration_within_max():
    brief = _make_brief(_scene("s01", duration=10.0))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    for plan in result:
        assert plan.duration_sec <= 5.0


def test_hints_distributed_across_sub_scenes():
    hints = ["alarm screen visible", "hand reaches in", "red error line on screen"]
    brief = _make_brief(_scene("s01", duration=10.0, hints=hints))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    all_hints = [kf.hint for p in result for kf in p.keyframes]
    for h in hints:
        assert any(h in ah for ah in all_hints)


def test_scene_within_max_not_split():
    brief = _make_brief(_scene("s01", duration=5.0))
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    assert len(result) == 1
    assert result[0].scene_id == "s01"


def test_four_scenes_each_10s_produce_8_sub_scenes():
    brief = _make_brief(
        _scene("s01", duration=10.0),
        _scene("s02", duration=10.0),
        _scene("s03", duration=10.0),
        _scene("s04", duration=10.0),
    )
    planner = KeyframePlanner(max_scene_duration_sec=5.0)
    result = planner.plan(brief)
    assert len(result) == 8


def test_max_scene_duration_15s_caps_frames_at_12():
    brief = _make_brief(_scene("s01", duration=10.0), fps=8)
    planner = KeyframePlanner(max_scene_duration_sec=1.5)
    result = planner.plan(brief)
    for plan in result:
        assert plan.total_frames <= 12, f"{plan.scene_id} has {plan.total_frames} frames > 12"


def test_max_scene_duration_15s_produces_7_sub_scenes_for_10s():
    brief = _make_brief(_scene("s01", duration=10.0), fps=8)
    planner = KeyframePlanner(max_scene_duration_sec=1.5)
    result = planner.plan(brief)
    assert len(result) == math.ceil(10.0 / 1.5)
