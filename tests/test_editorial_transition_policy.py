"""Tests for editorial transition policy."""
import pytest
from app.editorial.transition_policy import TransitionPolicy


class TestTransitionPolicyForbiddenTransitionsBlocked:
    def test_forbidden_transition_in_default(self):
        policy = TransitionPolicy(
            default="random_wipe",
            forbidden_transitions=["random_wipe", "spin", "excessive_glitch"],
        )
        errs = policy.validate()
        assert any("forbidden" in e for e in errs)

    def test_forbidden_transition_in_new_topic(self):
        policy = TransitionPolicy(
            new_topic="spin",
            forbidden_transitions=["random_wipe", "spin", "excessive_glitch"],
        )
        errs = policy.validate()
        assert any("forbidden" in e for e in errs)

    def test_default_policy_valid(self):
        policy = TransitionPolicy.default_policy()
        errs = policy.validate()
        assert errs == []


class TestFadeRatioValidated:
    def test_fade_ratio_too_large(self):
        policy = TransitionPolicy(max_total_fade_ratio=1.5)
        errs = policy.validate()
        assert any("max_total_fade_ratio must be in [0, 1]" in e for e in errs)

    def test_fade_ratio_negative(self):
        policy = TransitionPolicy(max_total_fade_ratio=-0.1)
        errs = policy.validate()
        assert any("max_total_fade_ratio must be in [0, 1]" in e for e in errs)

    def test_fade_ratio_zero(self):
        policy = TransitionPolicy(max_total_fade_ratio=0.0)
        errs = policy.validate()
        assert errs == []

    def test_fade_ratio_valid(self):
        policy = TransitionPolicy(max_total_fade_ratio=0.35)
        assert policy.validate() == []


class TestTransitionPolicyDefaults:
    def test_default_values(self):
        policy = TransitionPolicy()
        assert policy.default == "hard_cut"
        assert "random_wipe" in policy.forbidden_transitions
        assert "spin" in policy.forbidden_transitions
        assert "excessive_glitch" in policy.forbidden_transitions
        assert policy.max_total_fade_ratio == 0.35

    def test_is_transition_allowed(self):
        policy = TransitionPolicy()
        assert policy.is_transition_allowed("hard_cut") is True
        assert policy.is_transition_allowed("crossfade") is True
        assert policy.is_transition_allowed("random_wipe") is False
        assert policy.is_transition_allowed("spin") is False

    def test_to_dict(self):
        policy = TransitionPolicy.default_policy()
        data = policy.to_dict()
        assert data["default"] == "hard_cut"
        assert "forbidden_transitions" in data
