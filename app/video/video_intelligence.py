"""Video Intelligence v1 - Practical intelligence for video frame/segment selection.

Provides:
- Basic scene/shot segmentation using frame difference
- Keyframe/representative-frame selection
- Temporal defect heuristics (flicker, frozen, drift)
- Video intelligence report generation
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class SceneSegment:
    """A scene/shot segment in the video."""
    start_frame: int
    end_frame: int
    representative_frame: int
    avg_brightness: float
    motion_score: float
    decision: str = "process"  # process, skip, retry_candidate
    decision_reason: str = ""


@dataclass
class Keyframe:
    """A keyframe selected for processing."""
    frame_index: int
    score: float
    reason: str


@dataclass
class TemporalDefect:
    """A temporal defect detected in the video."""
    type: str
    start_frame: int
    end_frame: int
    severity: str  # low, medium, high
    description: str


@dataclass
class VideoIntelligenceReport:
    """Complete video intelligence report."""
    video_id: str
    total_frames: int
    fps: float
    scenes: list[SceneSegment] = field(default_factory=list)
    keyframes: list[Keyframe] = field(default_factory=list)
    defects: list[TemporalDefect] = field(default_factory=list)
    selected_subset: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "total_frames": self.total_frames,
            "fps": self.fps,
            "scenes": [
                {
                    "start_frame": s.start_frame,
                    "end_frame": s.end_frame,
                    "representative_frame": s.representative_frame,
                    "avg_brightness": s.avg_brightness,
                    "motion_score": s.motion_score,
                    "decision": s.decision,
                    "decision_reason": s.decision_reason,
                }
                for s in self.scenes
            ],
            "keyframes": [
                {"frame_index": k.frame_index, "score": k.score, "reason": k.reason}
                for k in self.keyframes
            ],
            "defects": [
                {
                    "type": d.type,
                    "start_frame": d.start_frame,
                    "end_frame": d.end_frame,
                    "severity": d.severity,
                    "description": d.description,
                }
                for d in self.defects
            ],
            "selected_subset": self.selected_subset,
            "metadata": self.metadata,
        }

    def save(self, path: Path) -> None:
        """Save report to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))


def make_per_scene_decisions(
    scenes: list[SceneSegment],
) -> list[SceneSegment]:
    """Make per-scene decisions (process/skip/retry_candidate) using real signals.

    Args:
        scenes: Scene segments

    Returns:
        Scene segments with decisions applied
    """
    for i, scene in enumerate(scenes):
        # Decision logic using real signals:
        # - Extremely low motion (< 2.0): skip (clearly frozen)
        # - Very low motion (2.0-5.0) with very poor brightness (< 20): skip (frozen + very dark)
        # - Very low motion (2.0-5.0) with poor-to-moderate brightness (20-50): retry_candidate (ambiguous, worth reconsideration)
        # - Low motion (5.0-10.0) with normal brightness: process (usable)
        # - Medium motion (10.0-20.0): process (good)
        # - High motion (> 20.0): process (interesting)
        # - Poor brightness (< 20) or high brightness (> 200): skip (poor visibility regardless of motion)

        motion = scene.motion_score
        brightness = scene.avg_brightness

        # First scene is always processed for context
        if i == 0:
            scene.decision = "process"
            scene.decision_reason = "First scene - always processed for context"
            continue

        # Skip poor brightness scenes (too dark or too bright)
        if brightness < 20.0:
            scene.decision = "skip"
            scene.decision_reason = f"Too dark (brightness {brightness:.2f}) - poor visibility"
            continue
        if brightness > 200.0:
            scene.decision = "skip"
            scene.decision_reason = f"Too bright (brightness {brightness:.2f}) - overexposed"
            continue

        # Extremely low motion - skip
        if motion < 2.0:
            scene.decision = "skip"
            scene.decision_reason = f"Extremely low motion ({motion:.2f}) - clearly frozen segment"
            continue

        # Very low motion with very poor brightness - skip
        if motion < 5.0 and brightness < 20.0:
            scene.decision = "skip"
            scene.decision_reason = f"Very low motion ({motion:.2f}) and very dark ({brightness:.2f}) - likely frozen and poor visibility"
            continue

        # Very low motion with poor-to-moderate brightness - retry_candidate (ambiguous)
        if motion < 5.0 and brightness >= 20.0 and brightness < 50.0:
            scene.decision = "retry_candidate"
            scene.decision_reason = f"Ambiguous low motion ({motion:.2f}) with moderate brightness ({brightness:.2f}) - worth reconsideration"
            continue

        # Low motion with normal brightness - process
        if motion >= 5.0 and motion < 10.0:
            scene.decision = "process"
            scene.decision_reason = f"Low motion ({motion:.2f}) with good brightness ({brightness:.2f}) - usable scene"
            continue

        # Medium motion - process
        if motion >= 10.0 and motion <= 20.0:
            scene.decision = "process"
            scene.decision_reason = f"Medium motion ({motion:.2f}) with good brightness ({brightness:.2f}) - good scene"
            continue

        # High motion - process
        if motion > 20.0:
            scene.decision = "process"
            scene.decision_reason = f"High motion ({motion:.2f}) - interesting scene"
            continue

        # Fallback for any other cases
        scene.decision = "retry_candidate"
        scene.decision_reason = f"Uncertain - motion {motion:.2f}, brightness {brightness:.2f}"

    return scenes


def detect_scene_segments(
    frames_dir: Path,
    threshold: float = 30.0,
    min_scene_length: int = 5,
    force_min_scenes: int = 1,
) -> list[SceneSegment]:
    """Detect scene/shot segments using frame difference.

    Args:
        frames_dir: Directory containing extracted frames
        threshold: Frame difference threshold for scene boundary
        min_scene_length: Minimum frames per scene
        force_min_scenes: Force at least this many scenes (for multi-scene demo)

    Returns:
        List of scene segments
    """
    # Get sorted frame paths
    frame_paths = sorted(frames_dir.glob("*.png"))
    if not frame_paths:
        return []

    # Read frames and compute differences
    frames = []
    for path in frame_paths:
        frame = cv2.imread(str(path))
        if frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray)

    if len(frames) < 2:
        return []

    # Compute frame differences
    prev_gray = frames[0]
    scene_boundaries = [0]

    for i, gray in enumerate(frames[1:], 1):
        # Compute frame difference
        diff = cv2.absdiff(prev_gray, gray)
        diff_score = np.mean(diff)

        if diff_score > threshold:
            scene_boundaries.append(i)

        prev_gray = gray

    # Add final boundary
    scene_boundaries.append(len(frames))

    # If too few scenes detected and force_min_scenes > 1, force time-based scenes
    if len(scene_boundaries) - 1 < force_min_scenes:
        scene_boundaries = []
        frames_per_scene = len(frames) // force_min_scenes
        for i in range(force_min_scenes):
            scene_boundaries.append(i * frames_per_scene)
        scene_boundaries.append(len(frames))

    # Create scene segments
    scenes = []
    for i in range(len(scene_boundaries) - 1):
        start = scene_boundaries[i]
        end = scene_boundaries[i + 1]
        length = end - start

        if length >= min_scene_length:
            # Select representative frame (middle of scene)
            representative = start + length // 2

            # Compute average brightness and motion score
            scene_frames = frames[start:end]
            avg_brightness = np.mean([np.mean(f) for f in scene_frames])

            # Simple motion score: variance of brightness
            motion_score = np.var([np.mean(f) for f in scene_frames])

            scenes.append(
                SceneSegment(
                    start_frame=start,
                    end_frame=end,
                    representative_frame=representative,
                    avg_brightness=float(avg_brightness),
                    motion_score=float(motion_score),
                )
            )

    return scenes


def select_keyframes(
    scenes: list[SceneSegment],
    max_keyframes: int = 10,
) -> list[Keyframe]:
    """Select keyframes from scene segments.

    Args:
        scenes: Scene segments
        max_keyframes: Maximum number of keyframes to select

    Returns:
        List of keyframes
    """
    keyframes = []

    # Select representative frame from each scene
    for scene in scenes:
        keyframes.append(
            Keyframe(
                frame_index=scene.representative_frame,
                score=scene.motion_score,
                reason="scene representative",
            )
        )

    # Sort by motion score (higher motion = more interesting)
    keyframes.sort(key=lambda k: k.score, reverse=True)

    # Limit to max_keyframes
    keyframes = keyframes[:max_keyframes]

    # Sort by frame index for processing order
    keyframes.sort(key=lambda k: k.frame_index)

    return keyframes


def detect_temporal_defects(
    frames_dir: Path,
    scenes: list[SceneSegment],
) -> list[TemporalDefect]:
    """Detect temporal defects in video.

    Args:
        frames_dir: Directory containing extracted frames
        scenes: Scene segments

    Returns:
        List of temporal defects
    """
    defects = []

    # Get sorted frame paths
    frame_paths = sorted(frames_dir.glob("*.png"))
    if not frame_paths:
        return defects

    # Read frames
    frames = []
    for path in frame_paths:
        frame = cv2.imread(str(path))
        if frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray)

    if len(frames) < 3:
        return defects

    # Detect flicker (rapid brightness changes)
    brightness_values = [np.mean(f) for f in frames]
    brightness_std = np.std(brightness_values)

    if brightness_std > 50:  # High variance suggests flicker
        defects.append(
            TemporalDefect(
                type="flicker",
                start_frame=0,
                end_frame=len(frames) - 1,
                severity="medium" if brightness_std < 100 else "high",
                description=f"High brightness variance ({brightness_std:.1f}) suggests flicker",
            )
        )

    # Detect frozen/repeated segments (low motion within scenes)
    for scene in scenes:
        if scene.motion_score < 10:  # Very low motion
            defects.append(
                TemporalDefect(
                    type="frozen_segment",
                    start_frame=scene.start_frame,
                    end_frame=scene.end_frame,
                    severity="low",
                    description=f"Scene {scene.start_frame}-{scene.end_frame} has very low motion",
                )
            )

    # Detect brightness drift (gradual brightness change)
    if len(brightness_values) > 10:
        # Check for monotonic brightness change
        first_half = brightness_values[: len(brightness_values) // 2]
        second_half = brightness_values[len(brightness_values) // 2 :]
        avg_first = np.mean(first_half)
        avg_second = np.mean(second_half)

        if abs(avg_second - avg_first) > 30:
            defects.append(
                TemporalDefect(
                    type="brightness_drift",
                    start_frame=0,
                    end_frame=len(frames) - 1,
                    severity="low",
                    description=f"Brightness drift detected ({avg_first:.1f} -> {avg_second:.1f})",
                )
            )

    return defects


def generate_video_intelligence_report(
    video_id: str,
    frames_dir: Path,
    fps: float,
    max_processed_frames: int | None = None,
    multi_scene: bool = False,
) -> VideoIntelligenceReport:
    """Generate complete video intelligence report.

    Args:
        video_id: Video identifier
        frames_dir: Directory containing extracted frames
        fps: Video frame rate
        max_processed_frames: Optional cap on frames to process
        multi_scene: If True, use lower threshold for multi-scene detection (v1.1 Layer 2)

    Returns:
        Video intelligence report
    """
    # Get frame count
    frame_paths = sorted(frames_dir.glob("*.png"))
    total_frames = len(frame_paths)

    # Detect scenes (lower threshold for multi-scene mode, force minimum scenes)
    threshold = 10.0 if multi_scene else 30.0
    min_scene_length = 3 if multi_scene else 5
    force_min_scenes = 3 if multi_scene else 1  # Always 1 for natural detection (Layer 3)
    scenes = detect_scene_segments(frames_dir, threshold=threshold, min_scene_length=min_scene_length, force_min_scenes=force_min_scenes)

    # Make per-scene decisions (v1.1 Layer 2, Layer 4 - always enabled for intelligence mode)
    scenes = make_per_scene_decisions(scenes)

    # Select keyframes (only from scenes with decision="process")
    processable_scenes = [s for s in scenes if s.decision == "process"]
    keyframes = select_keyframes(processable_scenes, max_keyframes=max_processed_frames or 10)

    # Detect defects
    defects = detect_temporal_defects(frames_dir, scenes)

    # Select subset for processing (use keyframes)
    selected_subset = [k.frame_index for k in keyframes]

    # Create report
    report = VideoIntelligenceReport(
        video_id=video_id,
        total_frames=total_frames,
        fps=fps,
        scenes=scenes,
        keyframes=keyframes,
        defects=defects,
        selected_subset=selected_subset,
        metadata={
            "num_scenes": len(scenes),
            "num_keyframes": len(keyframes),
            "num_defects": len(defects),
            "multi_scene_mode": multi_scene,
            "scenes_processed": len(processable_scenes),
            "scenes_skipped": len([s for s in scenes if s.decision == "skip"]),
            "scenes_retry": len([s for s in scenes if s.decision == "retry_candidate"]),
        },
    )

    return report
