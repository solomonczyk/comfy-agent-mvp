"""
Resolution/Aspect Ratio Policy Module

Enforces explicit resolution policy for scene/video/episode retry generation.
Blocks invalid portrait/low-res defaults from passing into retry generation.
"""

from typing import Dict, Any, Tuple, Optional
from enum import Enum


class ProjectTargetType(Enum):
    """Project target types requiring specific resolution policies."""
    SCENE = "scene"
    VIDEO = "video"
    EPISODE = "episode"
    PORTRAIT = "portrait"
    IDENTITY_VALIDATION = "identity_validation"


class ResolutionPolicy:
    """Explicit resolution policy for different project target types."""
    
    # Forbidden resolutions for scene/video/episode retry
    FORBIDDEN_RESOLUTIONS = {
        (480, 640): "portrait_9_16_low_res",
        (640, 480): "landscape_4_3_low_res",
    }
    
    # Allowed resolutions by target type
    POLICY_BY_TARGET = {
        ProjectTargetType.SCENE: {
            "orientation_required": "landscape",
            "aspect_ratio": "16:9",
            "fast_debug_resolution": (1024, 576),
            "minimum_scene_retry_resolution": (1344, 768),
            "preferred_scene_retry_resolution": (1536, 864),
            "final_delivery_resolution": (1920, 1080),
            "forbidden_resolutions": [(480, 640)],
        },
        ProjectTargetType.VIDEO: {
            "orientation_required": "landscape",
            "aspect_ratio": "16:9",
            "fast_debug_resolution": (1024, 576),
            "minimum_scene_retry_resolution": (1344, 768),
            "preferred_scene_retry_resolution": (1536, 864),
            "final_delivery_resolution": (1920, 1080),
            "forbidden_resolutions": [(480, 640)],
        },
        ProjectTargetType.EPISODE: {
            "orientation_required": "landscape",
            "aspect_ratio": "16:9",
            "fast_debug_resolution": (1024, 576),
            "minimum_scene_retry_resolution": (1344, 768),
            "preferred_scene_retry_resolution": (1536, 864),
            "final_delivery_resolution": (1920, 1080),
            "forbidden_resolutions": [(480, 640)],
        },
        ProjectTargetType.PORTRAIT: {
            "orientation_required": "portrait",
            "aspect_ratio": "9:16",
            "allowed_resolutions": [(480, 640), (512, 768), (576, 1024)],
        },
        ProjectTargetType.IDENTITY_VALIDATION: {
            "orientation_required": "portrait_or_landscape",
            "aspect_ratio": "flexible",
            "allowed_resolutions": [(1024, 1024), (1152, 896), (896, 1152)],
        },
    }
    
    @classmethod
    def validate_resolution(
        cls,
        width: int,
        height: int,
        target_type: ProjectTargetType,
        operator_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Validate resolution against policy for target type.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            target_type: Project target type (scene, video, episode, portrait, identity_validation)
            operator_approved: Whether operator explicitly approved this resolution
        
        Returns:
            Dictionary with validation result
        """
        resolution = (width, height)
        policy = cls.POLICY_BY_TARGET.get(target_type, {})
        
        # Check if operator explicitly approved (bypasses policy)
        if operator_approved:
            return {
                "valid": True,
                "resolution": f"{width}x{height}",
                "target_type": target_type.value,
                "reason": "operator_approved",
                "policy_bypassed": True,
            }
        
        # Check forbidden resolutions
        forbidden = policy.get("forbidden_resolutions", [])
        if resolution in forbidden:
            return {
                "valid": False,
                "resolution": f"{width}x{height}",
                "target_type": target_type.value,
                "reason": "forbidden_resolution",
                "forbidden_reason": cls.FORBIDDEN_RESOLUTIONS.get(resolution, "unknown"),
                "orientation_required": policy.get("orientation_required"),
                "recommended_resolution": policy.get("preferred_scene_retry_resolution"),
            }
        
        # Check orientation requirement
        orientation_required = policy.get("orientation_required")
        if orientation_required:
            aspect_ratio = width / height
            if orientation_required == "landscape" and aspect_ratio < 1.0:
                return {
                    "valid": False,
                    "resolution": f"{width}x{height}",
                    "target_type": target_type.value,
                    "reason": "orientation_mismatch",
                    "detected_orientation": "portrait",
                    "required_orientation": "landscape",
                    "recommended_resolution": policy.get("preferred_scene_retry_resolution"),
                }
            elif orientation_required == "portrait" and aspect_ratio > 1.0:
                return {
                    "valid": False,
                    "resolution": f"{width}x{height}",
                    "target_type": target_type.value,
                    "reason": "orientation_mismatch",
                    "detected_orientation": "landscape",
                    "required_orientation": "portrait",
                }
        
        # Check minimum resolution for scene/video/episode
        if target_type in [ProjectTargetType.SCENE, ProjectTargetType.VIDEO, ProjectTargetType.EPISODE]:
            min_res = policy.get("minimum_scene_retry_resolution")
            if min_res and (width < min_res[0] or height < min_res[1]):
                return {
                    "valid": False,
                    "resolution": f"{width}x{height}",
                    "target_type": target_type.value,
                    "reason": "below_minimum_resolution",
                    "minimum_required": f"{min_res[0]}x{min_res[1]}",
                    "recommended_resolution": policy.get("preferred_scene_retry_resolution"),
                }
        
        # Resolution is valid
        return {
            "valid": True,
            "resolution": f"{width}x{height}",
            "target_type": target_type.value,
            "reason": "policy_compliant",
            "orientation": "landscape" if width > height else "portrait" if height > width else "square",
        }
    
    @classmethod
    def get_policy_summary(cls, target_type: ProjectTargetType) -> Dict[str, Any]:
        """
        Get policy summary for a target type.
        
        Args:
            target_type: Project target type
        
        Returns:
            Dictionary with policy details
        """
        return cls.POLICY_BY_TARGET.get(target_type, {})
    
    @classmethod
    def detect_target_type_from_project(cls, project_root: str) -> ProjectTargetType:
        """
        Detect project target type from project metadata.
        
        Args:
            project_root: Path to project root
        
        Returns:
            Detected ProjectTargetType
        """
        from pathlib import Path
        import json
        
        project_path = Path(project_root)
        
        # Check for episode/project metadata
        episode_plan_path = project_path / "output" / "control" / "episode_plan.json"
        if episode_plan_path.exists():
            try:
                with open(episode_plan_path, encoding="utf-8") as f:
                    episode_plan = json.load(f)
                if episode_plan.get("episode_id"):
                    return ProjectTargetType.EPISODE
            except (json.JSONDecodeError, IOError):
                pass
        
        # Check for scene manifests
        frames_dir = project_path / "output" / "frames"
        if frames_dir.exists() and any(frames_dir.iterdir()):
            return ProjectTargetType.SCENE
        
        # Check for portrait/single-frame reference
        briefs_dir = project_path / "data" / "briefs"
        if briefs_dir.exists():
            for brief_file in briefs_dir.glob("*_brief.md"):
                try:
                    with open(brief_file, encoding="utf-8") as f:
                        content = f.read().lower()
                    if "portrait" in content or "single" in content:
                        return ProjectTargetType.PORTRAIT
                except IOError:
                    pass
        
        # Default to scene (most common for film production)
        return ProjectTargetType.SCENE


def create_resolution_preflight_gate(
    width: int,
    height: int,
    project_root: str,
    operator_approved: bool = False
) -> Dict[str, Any]:
    """
    Create resolution preflight gate for retry generation.
    
    This gate checks if the resolution is allowed for the project target type
    and blocks generation if the resolution is invalid.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        project_root: Path to project root
        operator_approved: Whether operator explicitly approved this resolution
    
    Returns:
        Dictionary with gate decision and preflight proof
    """
    # Detect target type
    target_type = ResolutionPolicy.detect_target_type_from_project(project_root)
    
    # Validate resolution
    validation = ResolutionPolicy.validate_resolution(width, height, target_type, operator_approved)
    
    # Build gate decision
    gate_open = validation["valid"]
    next_allowed_action = "retry_generate_frames" if gate_open else "resolution_policy_review"
    
    # Build preflight proof
    preflight_proof = {
        "final_emptylatentimage_width": width,
        "final_emptylatentimage_height": height,
        "resolution": f"{width}x{height}",
        "aspect_ratio": f"{width}:{height}" if width != height else "1:1",
        "aspect_ratio_source": "prompt_pack",
        "target_type": target_type.value,
        "resolution_allowed": gate_open,
        "validation_result": validation,
        "policy_summary": ResolutionPolicy.get_policy_summary(target_type),
    }
    
    return {
        "gate_open": gate_open,
        "next_allowed_action": next_allowed_action,
        "retry_gate_open": gate_open,
        "preflight_proof": preflight_proof,
        "resolution_policy_enforced": True,
    }
