"""
Tests for Resolution Policy Module

Tests gate behavior for retry resolution policy enforcement.
"""

import pytest
from app.production_cards.resolution_policy import (
    ResolutionPolicy,
    ProjectTargetType,
    create_resolution_preflight_gate,
)


class TestResolutionPolicyValidation:
    """Test resolution validation logic."""

    def test_480x640_blocked_for_scene(self):
        """480x640 is forbidden for scene retry."""
        result = ResolutionPolicy.validate_resolution(
            width=480,
            height=640,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "forbidden_resolution"
        assert result["resolution"] == "480x640"
        assert result["target_type"] == "scene"

    def test_480x640_blocked_for_video(self):
        """480x640 is forbidden for video retry."""
        result = ResolutionPolicy.validate_resolution(
            width=480,
            height=640,
            target_type=ProjectTargetType.VIDEO,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "forbidden_resolution"
        assert result["resolution"] == "480x640"
        assert result["target_type"] == "video"

    def test_480x640_blocked_for_episode(self):
        """480x640 is forbidden for episode retry."""
        result = ResolutionPolicy.validate_resolution(
            width=480,
            height=640,
            target_type=ProjectTargetType.EPISODE,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "forbidden_resolution"
        assert result["resolution"] == "480x640"
        assert result["target_type"] == "episode"

    def test_1536x864_accepted_for_scene_retry(self):
        """1536x864 is accepted as preferred scene retry resolution."""
        result = ResolutionPolicy.validate_resolution(
            width=1536,
            height=864,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "1536x864"
        assert result["orientation"] == "landscape"

    def test_1344x768_accepted_as_minimum_scene_retry(self):
        """1344x768 is accepted as minimum scene retry resolution."""
        result = ResolutionPolicy.validate_resolution(
            width=1344,
            height=768,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "1344x768"
        assert result["orientation"] == "landscape"

    def test_1024x576_below_minimum_blocked(self):
        """1024x576 is below minimum scene retry resolution and blocked."""
        result = ResolutionPolicy.validate_resolution(
            width=1024,
            height=576,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "below_minimum_resolution"
        assert result["resolution"] == "1024x576"

    def test_portrait_allows_480x640(self):
        """Portrait target type allows 480x640."""
        result = ResolutionPolicy.validate_resolution(
            width=480,
            height=640,
            target_type=ProjectTargetType.PORTRAIT,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "480x640"
        assert result["orientation"] == "portrait"

    def test_identity_validation_allows_1024x1024(self):
        """Identity validation allows 1024x1024 square resolution."""
        result = ResolutionPolicy.validate_resolution(
            width=1024,
            height=1024,
            target_type=ProjectTargetType.IDENTITY_VALIDATION,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "1024x1024"
        assert result["orientation"] == "square"

    def test_identity_validation_allows_1152x896(self):
        """Identity validation allows 1152x896 landscape resolution."""
        result = ResolutionPolicy.validate_resolution(
            width=1152,
            height=896,
            target_type=ProjectTargetType.IDENTITY_VALIDATION,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "1152x896"
        assert result["orientation"] == "landscape"

    def test_identity_validation_allows_896x1152(self):
        """Identity validation allows 896x1152 portrait resolution."""
        result = ResolutionPolicy.validate_resolution(
            width=896,
            height=1152,
            target_type=ProjectTargetType.IDENTITY_VALIDATION,
            operator_approved=False
        )
        assert result["valid"] is True
        assert result["reason"] == "policy_compliant"
        assert result["resolution"] == "896x1152"
        assert result["orientation"] == "portrait"

    def test_operator_approval_bypasses_policy(self):
        """Operator approval bypasses resolution policy."""
        result = ResolutionPolicy.validate_resolution(
            width=480,
            height=640,
            target_type=ProjectTargetType.SCENE,
            operator_approved=True
        )
        assert result["valid"] is True
        assert result["reason"] == "operator_approved"
        assert result["policy_bypassed"] is True

    def test_below_minimum_resolution_blocked(self):
        """Resolutions below minimum are blocked for scene/video/episode."""
        result = ResolutionPolicy.validate_resolution(
            width=1000,
            height=562,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "below_minimum_resolution"

    def test_portrait_orientation_blocked_for_scene(self):
        """Portrait orientation is blocked for scene target."""
        result = ResolutionPolicy.validate_resolution(
            width=768,
            height=1344,
            target_type=ProjectTargetType.SCENE,
            operator_approved=False
        )
        assert result["valid"] is False
        assert result["reason"] == "orientation_mismatch"
        assert result["detected_orientation"] == "portrait"
        assert result["required_orientation"] == "landscape"


class TestResolutionPreflightGate:
    """Test resolution preflight gate function."""

    def test_gate_blocks_480x640_for_scene(self):
        """Gate blocks 480x640 for scene retry."""
        result = create_resolution_preflight_gate(
            width=480,
            height=640,
            project_root="f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
            operator_approved=False
        )
        assert result["gate_open"] is False
        assert result["retry_gate_open"] is False
        assert result["next_allowed_action"] == "resolution_policy_review"
        assert result["preflight_proof"]["resolution_allowed"] is False
        assert result["preflight_proof"]["resolution"] == "480x640"
        assert result["resolution_policy_enforced"] is True

    def test_gate_allows_1536x864_for_scene(self):
        """Gate allows 1536x864 for scene retry."""
        result = create_resolution_preflight_gate(
            width=1536,
            height=864,
            project_root="f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
            operator_approved=False
        )
        assert result["gate_open"] is True
        assert result["retry_gate_open"] is True
        assert result["next_allowed_action"] == "retry_generate_frames"
        assert result["preflight_proof"]["resolution_allowed"] is True
        assert result["preflight_proof"]["resolution"] == "1536x864"
        assert result["resolution_policy_enforced"] is True

    def test_gate_includes_policy_summary(self):
        """Gate includes policy summary in preflight proof."""
        result = create_resolution_preflight_gate(
            width=480,
            height=640,
            project_root="f:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
            operator_approved=False
        )
        assert "policy_summary" in result["preflight_proof"]
        assert "forbidden_resolutions" in result["preflight_proof"]["policy_summary"]
        assert "preferred_scene_retry_resolution" in result["preflight_proof"]["policy_summary"]


class TestPolicySummary:
    """Test policy summary retrieval."""

    def test_scene_policy_summary(self):
        """Scene policy summary contains required fields."""
        summary = ResolutionPolicy.get_policy_summary(ProjectTargetType.SCENE)
        assert summary["orientation_required"] == "landscape"
        assert summary["aspect_ratio"] == "16:9"
        assert summary["fast_debug_resolution"] == (1024, 576)
        assert summary["minimum_scene_retry_resolution"] == (1344, 768)
        assert summary["preferred_scene_retry_resolution"] == (1536, 864)
        assert summary["final_delivery_resolution"] == (1920, 1080)
        assert (480, 640) in summary["forbidden_resolutions"]

    def test_video_policy_summary(self):
        """Video policy summary contains required fields."""
        summary = ResolutionPolicy.get_policy_summary(ProjectTargetType.VIDEO)
        assert summary["orientation_required"] == "landscape"
        assert summary["aspect_ratio"] == "16:9"
        assert (480, 640) in summary["forbidden_resolutions"]

    def test_episode_policy_summary(self):
        """Episode policy summary contains required fields."""
        summary = ResolutionPolicy.get_policy_summary(ProjectTargetType.EPISODE)
        assert summary["orientation_required"] == "landscape"
        assert summary["aspect_ratio"] == "16:9"
        assert (480, 640) in summary["forbidden_resolutions"]

    def test_portrait_policy_summary(self):
        """Portrait policy summary contains required fields."""
        summary = ResolutionPolicy.get_policy_summary(ProjectTargetType.PORTRAIT)
        assert summary["orientation_required"] == "portrait"
        assert summary["aspect_ratio"] == "9:16"
        assert (480, 640) in summary["allowed_resolutions"]

    def test_identity_validation_policy_summary(self):
        """Identity validation policy summary contains required fields."""
        summary = ResolutionPolicy.get_policy_summary(ProjectTargetType.IDENTITY_VALIDATION)
        assert summary["orientation_required"] == "portrait_or_landscape"
        assert summary["aspect_ratio"] == "flexible"
        assert (1024, 1024) in summary["allowed_resolutions"]
        assert (1152, 896) in summary["allowed_resolutions"]
