"""MK-3B — Scene Video Quality & Retry Robustness v1.

Enhances MK-3 with scene-quality heuristics:
- Motion weakness / near-frozen output detection
- Repetitive frame detection
- Temporal inconsistency detection
- Visual degradation detection
- Scene change analysis against intended motion prompt

Supports three verdicts: accept, retry_candidate, reject based on honest heuristics.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.assets.paths import ASSET_PATHS, ensure_asset_dirs
from app.video.comfy_processor import process_frames_via_comfy
from app.video.frames import assemble_frames
from app.video.manifest import VideoManifest, VideoManifestPersistence
from app.video.video_qc import run_video_qc


def _compute_dhash_similarity(dhash1: str, dhash2: str) -> float:
    """Compute similarity between two dhash values.

    Args:
        dhash1: First dhash string
        dhash2: Second dhash string

    Returns:
        Similarity ratio (0.0 = completely different, 1.0 = identical)
    """
    if len(dhash1) != len(dhash2):
        return 0.0

    matching = sum(1 for a, b in zip(dhash1, dhash2) if a == b)
    return matching / len(dhash1)


def _analyze_frame_motion(qc_report: dict[str, Any]) -> dict[str, Any]:
    """Analyze motion characteristics from QC per-frame data.

    Args:
        qc_report: Video QC report with per_frame_qc data

    Returns:
        Motion analysis dict with motion_score, repetitive_ratio, frozen_ratio
    """
    per_frame_qc = qc_report.get("per_frame_qc", [])
    if not per_frame_qc:
        return {"motion_score": 0.0, "repetitive_ratio": 1.0, "frozen_ratio": 1.0}

    # Analyze dhash similarities between consecutive frames
    similarities = []
    for i in range(len(per_frame_qc) - 1):
        dhash1 = per_frame_qc[i].get("dhash", "")
        dhash2 = per_frame_qc[i + 1].get("dhash", "")
        if dhash1 and dhash2:
            sim = _compute_dhash_similarity(dhash1, dhash2)
            similarities.append(sim)

    if not similarities:
        return {"motion_score": 0.0, "repetitive_ratio": 1.0, "frozen_ratio": 1.0}

    # Motion score: lower similarity = more motion
    avg_similarity = sum(similarities) / len(similarities)
    motion_score = 1.0 - avg_similarity

    # Repetitive frames: very high similarity (>0.95)
    repetitive_count = sum(1 for s in similarities if s > 0.95)
    repetitive_ratio = repetitive_count / len(similarities)

    # Frozen output: extremely high similarity (>0.98)
    frozen_count = sum(1 for s in similarities if s > 0.98)
    frozen_ratio = frozen_count / len(similarities)

    return {
        "motion_score": motion_score,
        "repetitive_ratio": repetitive_ratio,
        "frozen_ratio": frozen_ratio,
        "avg_frame_similarity": avg_similarity,
    }


def _analyze_temporal_consistency(qc_report: dict[str, Any]) -> dict[str, Any]:
    """Analyze temporal consistency across frames.

    Args:
        qc_report: Video QC report with per_frame_qc data

    Returns:
        Temporal consistency analysis
    """
    per_frame_qc = qc_report.get("per_frame_qc", [])
    if not per_frame_qc:
        return {"temporal_inconsistency": False, "brightness_variance": 0.0}

    # Analyze brightness variance
    means = [f.get("mean", 0) for f in per_frame_qc]
    if not means:
        return {"temporal_inconsistency": False, "brightness_variance": 0.0}

    avg_mean = sum(means) / len(means)
    variance = sum((m - avg_mean) ** 2 for m in means) / len(means)

    # High brightness variance may indicate flickering or inconsistent lighting
    temporal_inconsistency = variance > 100.0

    return {
        "temporal_inconsistency": temporal_inconsistency,
        "brightness_variance": variance,
        "avg_brightness": avg_mean,
    }


def _compute_scene_quality_verdict(
    qc_report: dict[str, Any],
    motion_analysis: dict[str, Any],
    temporal_analysis: dict[str, Any],
    intended_motion: str = "subtle motion",
    comfy_recipe: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    """Compute scene quality verdict with heuristics beyond file validity.

    Args:
        qc_report: Video QC report
        motion_analysis: Motion analysis from _analyze_frame_motion
        temporal_analysis: Temporal analysis from _analyze_temporal_consistency
        intended_motion: Intended motion level from prompt
        comfy_recipe: ComfyUI recipe used for generation

    Returns:
        Tuple of (verdict, reasons)
    """
    reasons = []
    verdict = "accept"

    # Check file-level QC first
    qc_verdict = qc_report.get("verdict", "reject")
    if qc_verdict == "reject":
        verdict = "reject"
        reasons.extend(qc_report.get("reasons", ["File-level QC failed"]))
        return verdict, reasons

    # Use QC's frozen_output check for reliable frozen detection
    frozen_check = qc_report.get("checks", {}).get("frozen_output", {})
    if not frozen_check.get("passed", True):
        verdict = "retry_candidate"
        reasons.append("Frozen output detected by QC")

    # Motion weakness detection using our analysis
    frozen_ratio = motion_analysis.get("frozen_ratio", 0.0)
    if frozen_ratio > 0.5:
        if verdict == "accept":
            verdict = "retry_candidate"
        reasons.append("Near-frozen output detected (low motion)")

    # Check for low-quality generation settings (very low steps)
    if comfy_recipe:
        steps = comfy_recipe.get("steps", 20)
        if steps < 10:
            if verdict == "accept":
                verdict = "retry_candidate"
            reasons.append(f"Low-quality generation settings (steps={steps})")

    # Repetitive frames
    repetitive_ratio = motion_analysis.get("repetitive_ratio", 0.0)
    if repetitive_ratio > 0.5:
        if verdict == "accept":
            verdict = "retry_candidate"
        reasons.append("Repetitive frames detected")

    # Temporal inconsistency (flickering)
    if temporal_analysis.get("temporal_inconsistency", False):
        if verdict == "accept":
            verdict = "retry_candidate"
        reasons.append("Temporal inconsistency (brightness flickering)")

    # Motion score vs intended motion
    motion_score = motion_analysis.get("motion_score", 0.0)
    if "subtle" in intended_motion.lower():
        # For subtle motion, very low motion is acceptable but not zero
        if motion_score < 0.15:
            if verdict == "accept":
                verdict = "retry_candidate"
            reasons.append("Insufficient motion for intended subtle motion")
    elif "dynamic" in intended_motion.lower() or "strong" in intended_motion.lower():
        # For dynamic motion, expect higher motion
        if motion_score < 0.2:
            if verdict == "accept":
                verdict = "retry_candidate"
            reasons.append("Insufficient motion for intended dynamic motion")
    elif "static" in intended_motion.lower() or "frozen" in intended_motion.lower():
        # For static/frozen prompts, any motion is acceptable but we flag low motion quality
        if motion_score > 0.15:
            if verdict == "accept":
                verdict = "retry_candidate"
            reasons.append("Unexpected motion for static scene")

    # If no issues, accept
    if not reasons:
        verdict = "accept"

    return verdict, reasons


@dataclass
class SceneGenerationConfig:
    """Configuration for scene generation."""
    reference_image_path: str
    scene_prompt: str | None = None
    video_workflow: str = "comfy_img2img_v1"
    num_frames: int = 8
    fps: float = 12.0
    comfy_recipe: dict[str, Any] | None = None
    reference_locked: bool = False
    batch_mode: bool = False
    bounded_mode: bool = False


@dataclass
class SceneResult:
    """Result of scene generation."""
    scene_id: str
    status: str
    reference_image_path: str
    generated_video_prompt: str
    selected_video_workflow: str
    video_path: str | None
    manifest_path: str | None
    qc_report_path: str | None
    scene_verdict: str | None
    scene_reasons: list[str] = field(default_factory=list)
    generation_start: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    generation_end: str | None = None
    error: str | None = None
    timing_breakdown: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "status": self.status,
            "reference_image_path": self.reference_image_path,
            "generated_video_prompt": self.generated_video_prompt,
            "selected_video_workflow": self.selected_video_workflow,
            "video_path": self.video_path,
            "manifest_path": self.manifest_path,
            "qc_report_path": self.qc_report_path,
            "scene_verdict": self.scene_verdict,
            "scene_reasons": self.scene_reasons,
            "generation_start": self.generation_start,
            "generation_end": self.generation_end,
            "error": self.error,
            "timing_breakdown": self.timing_breakdown,
        }


class SceneAgent:
    """Reference-to-Video Scene Agent v1."""

    def __init__(self):
        ensure_asset_dirs()
        self.manifests_dir = ASSET_PATHS.manifests
        self.scenes_dir = ASSET_PATHS.video_dir("scenes")

    def _generate_scene_id(self) -> str:
        """Generate unique scene ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique = str(uuid.uuid4())[:8]
        return f"scene_{timestamp}_{unique}"

    def _build_video_prompt(self, reference_image_path: str, user_prompt: str | None = None) -> str:
        """Build video prompt from reference image and optional user prompt.

        Args:
            reference_image_path: Path to reference image
            user_prompt: Optional user-specified prompt

        Returns:
            Generated video prompt
        """
        # Default prompt for scene generation
        base_prompt = "cinematic scene, subtle motion, professional quality, realistic details, smooth transitions"

        if user_prompt:
            # Combine user prompt with base scene prompt
            return f"{user_prompt}, {base_prompt}"

        # Extract context from reference image path if available
        ref_path = Path(reference_image_path)
        if "portrait" in ref_path.name.lower():
            return f"portrait scene, subtle head movement, natural lighting, {base_prompt}"
        elif "landscape" in ref_path.name.lower():
            return f"landscape scene, gentle camera movement, atmospheric lighting, {base_prompt}"
        else:
            return base_prompt

    def _select_video_workflow(self, config: SceneGenerationConfig) -> str:
        """Select video workflow based on configuration.

        Args:
            config: Scene generation configuration

        Returns:
            Selected video workflow ID
        """
        # For v1, use a single default workflow
        # Future: add workflow selection logic based on reference analysis
        return config.video_workflow

    async def _generate_video_frames(
        self,
        reference_image_path: str,
        prompt: str,
        num_frames: int,
        output_dir: Path,
        comfy_recipe: dict[str, Any] | None = None,
        reference_locked: bool = False,
        batch_mode: bool = False,
        bounded_mode: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Generate video frames from reference image using img2img.

        Args:
            reference_image_path: Path to reference image
            prompt: Video prompt
            num_frames: Number of frames to generate
            output_dir: Output directory for frames
            comfy_recipe: Optional ComfyUI recipe overrides

        Returns:
            List of frame linkage records
        """
        reference_path = Path(reference_image_path).resolve()
        if not reference_path.exists():
            raise FileNotFoundError(f"Reference image not found: {reference_image_path}")

        # Create synthetic input frames by copying reference image
        # In a real implementation, this would use actual video generation
        # For v1 proof, we use the comfy_processor with the reference as input
        selected_paths = [reference_path] * num_frames

        # Process frames via comfy (img2img with slight variations)
        per_frame_linkage, generation_diagnostics = await process_frames_via_comfy(
            selected_paths=selected_paths,
            processed_dir=output_dir,
            prompt=prompt,
            comfy_recipe=comfy_recipe,
            reference_locked=reference_locked,
            batch_mode=batch_mode,
            bounded_mode=bounded_mode,
        )

        return per_frame_linkage, generation_diagnostics

    def _compute_scene_verdict(
        self,
        qc_report: dict[str, Any],
        video_prompt: str,
        comfy_recipe: dict[str, Any] | None = None,
    ) -> tuple[str, list[str], dict[str, Any]]:
        """Compute scene verdict from QC report with quality heuristics.

        Args:
            qc_report: Video QC report
            video_prompt: Generated video prompt to extract intended motion
            comfy_recipe: ComfyUI recipe used for generation

        Returns:
            Tuple of (verdict, reasons, quality_analysis)
        """
        # Extract intended motion from prompt
        intended_motion = "subtle motion"
        if "dynamic" in video_prompt.lower():
            intended_motion = "dynamic motion"
        elif "strong" in video_prompt.lower():
            intended_motion = "strong motion"

        # Run quality heuristics
        motion_analysis = _analyze_frame_motion(qc_report)
        temporal_analysis = _analyze_temporal_consistency(qc_report)

        # Compute verdict with heuristics
        verdict, reasons = _compute_scene_quality_verdict(
            qc_report=qc_report,
            motion_analysis=motion_analysis,
            temporal_analysis=temporal_analysis,
            intended_motion=intended_motion,
            comfy_recipe=comfy_recipe,
        )

        quality_analysis = {
            "motion_analysis": motion_analysis,
            "temporal_analysis": temporal_analysis,
            "intended_motion": intended_motion,
        }

        return verdict, reasons, quality_analysis

    async def generate_scene(
        self,
        reference_image_path: str,
        user_prompt: str | None = None,
        num_frames: int = 8,
        fps: float = 12.0,
        comfy_recipe: dict[str, Any] | None = None,
        reference_locked: bool = False,
        batch_mode: bool = False,
        bounded_mode: bool = False,
    ) -> SceneResult:
        """Generate a scene from reference image.

        Args:
            reference_image_path: Path to reference image
            user_prompt: Optional user-specified prompt
            num_frames: Number of video frames to generate
            fps: Output video FPS
            comfy_recipe: Optional ComfyUI recipe overrides

        Returns:
            SceneResult with generation details and verdict
        """
        scene_id = self._generate_scene_id()
        scene_dir = self.scenes_dir / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        frames_dir = scene_dir / "frames"
        processed_dir = scene_dir / "processed"
        video_path = scene_dir / "scene.mp4"

        config = SceneGenerationConfig(
            reference_image_path=reference_image_path,
            scene_prompt=user_prompt,
            num_frames=num_frames,
            fps=fps,
            comfy_recipe=comfy_recipe,
            reference_locked=reference_locked,
            batch_mode=batch_mode,
            bounded_mode=bounded_mode,
        )

        # Timing breakdown
        import time
        timing_breakdown = {
            "route": "reference_locked" if reference_locked else "standard",
            "pre_scene_latency_s": 0,
            "generation_latency_s": 0,
            "candidate_loop_count": 0,
            "prep_pass_count": 0,
            "generation_path": "unknown",
            "copy_fallback_used": False,
            "real_generation_used": False,
            "comfy_submission_count": 0,
            "images_per_submission": [],
            "generation_strategy": "unknown",
        }
        pre_scene_start = time.time()
        generation_start = time.time()

        result = SceneResult(
            scene_id=scene_id,
            status="running",
            reference_image_path=reference_image_path,
            generated_video_prompt="",
            selected_video_workflow="",
            video_path=str(video_path),
            manifest_path=str(self.manifests_dir / f"video_{scene_id}.json"),
            qc_report_path=None,
            scene_verdict=None,
        )

        # Initialize video manifest
        persistence = VideoManifestPersistence(self.manifests_dir)
        manifest = VideoManifest(
            video_id=scene_id,
            input_path=reference_image_path,
            video_dir=scene_dir,
        )
        persistence.save(manifest)

        try:
            # Step 1: Build video prompt
            video_prompt = self._build_video_prompt(reference_image_path, user_prompt)
            result.generated_video_prompt = video_prompt

            # Step 2: Select video workflow
            video_workflow = self._select_video_workflow(config)
            result.selected_video_workflow = video_workflow

            # Step 3: Generate video frames
            print(f"[MK-3] Generating {num_frames} frames from reference: {reference_image_path}")
            per_frame_linkage, generation_diagnostics = await self._generate_video_frames(
                reference_image_path=reference_image_path,
                prompt=video_prompt,
                num_frames=num_frames,
                output_dir=processed_dir,
                comfy_recipe=comfy_recipe,
                reference_locked=reference_locked,
                batch_mode=batch_mode,
                bounded_mode=config.bounded_mode,
            )

            # Calculate pre-scene latency
            pre_scene_end = time.time()
            timing_breakdown["pre_scene_latency_s"] = pre_scene_end - pre_scene_start
            
            # Calculate generation latency
            generation_end = time.time()
            timing_breakdown["generation_latency_s"] = generation_end - generation_start
            
            # Update generation path diagnostics
            timing_breakdown["generation_path"] = "real_generation" if generation_diagnostics.get("real_generation_used") else "unknown"
            timing_breakdown["copy_fallback_used"] = generation_diagnostics.get("copy_fallback_used", False)
            timing_breakdown["real_generation_used"] = generation_diagnostics.get("real_generation_used", False)
            timing_breakdown["real_generation_count"] = generation_diagnostics.get("real_generation_count", 0)
            timing_breakdown["copy_fallback_count"] = generation_diagnostics.get("copy_fallback_count", 0)
            timing_breakdown["comfy_submission_count"] = generation_diagnostics.get("comfy_submission_count", 0)
            timing_breakdown["images_per_submission"] = generation_diagnostics.get("images_per_submission", [])
            timing_breakdown["generation_strategy"] = generation_diagnostics.get("generation_strategy", "unknown")
            timing_breakdown["frames_requested"] = generation_diagnostics.get("total_frames_requested", 0)
            timing_breakdown["frames_generated"] = generation_diagnostics.get("frames_generated", 0)
            processed_count = sum(1 for e in per_frame_linkage if e.get("processed_frame"))
            if processed_count == 0:
                raise RuntimeError("No frames were generated")
            
            # MK-6K-R: Validate all frames before scene assembly with stage-based tracing
            print(f"[MK-6K-R] Validating {processed_count} frames before scene assembly...")
            frame_validity_diagnostics = {
                "total_frames": processed_count,
                "valid_frames": 0,
                "invalid_frames": 0,
                "black_frames": 0,
                "blue_frames": 0,
                "per_frame_diagnostics": [],
                "black_frame_root_cause": "unknown",
                "first_bad_stage": "unknown",
            }
            
            for entry in per_frame_linkage:
                frame_diag = entry.get("frame_diagnostics", {})
                stage_b = frame_diag.get("stage_b_fetched", {})
                
                is_black = stage_b.get("black_frame", False)
                is_blue = stage_b.get("blue_frame", False)
                is_invalid = stage_b.get("invalid", False)
                mean_brightness = stage_b.get("mean_brightness", 0)
                std_brightness = stage_b.get("std_brightness", 0)
                blue_ratio = stage_b.get("blue_dominance_ratio", 0)
                
                frame_validity = {
                    "frame_index": entry.get("index"),
                    "source_submission_index": frame_diag.get("source_submission_index"),
                    "source_output_index": frame_diag.get("source_output_index"),
                    "output_filename": frame_diag.get("output_filename"),
                    "output_node": frame_diag.get("output_node"),
                    "prompt_id": frame_diag.get("prompt_id"),
                    # Stage B diagnostics
                    "stage_b": {
                        "black_frame": is_black,
                        "blue_frame": is_blue,
                        "invalid": is_invalid,
                        "mean_brightness": mean_brightness,
                        "std_brightness": std_brightness,
                        "blue_dominance_ratio": blue_ratio,
                    },
                    # Stage C diagnostics
                    "stage_c": frame_diag.get("stage_c_decoded", {}),
                    # Stage D diagnostics
                    "stage_d": frame_diag.get("stage_d_linked", {}),
                }
                
                if is_invalid:
                    frame_validity_diagnostics["invalid_frames"] += 1
                    if is_black:
                        frame_validity_diagnostics["black_frames"] += 1
                    if is_blue:
                        frame_validity_diagnostics["blue_frames"] += 1
                    print(f"[MK-6K-R] Frame {entry.get('index')}: INVALID (black={is_black}, blue={is_blue}, mean={mean_brightness:.1f}, std={std_brightness:.1f}, blue_ratio={blue_ratio:.2f})")
                else:
                    frame_validity_diagnostics["valid_frames"] += 1
                    print(f"[MK-6K-R] Frame {entry.get('index')}: VALID (mean={mean_brightness:.1f}, std={std_brightness:.1f}, blue_ratio={blue_ratio:.2f})")
                
                frame_validity_diagnostics["per_frame_diagnostics"].append(frame_validity)
            
            # MK-6K-R: Classify root cause and first bad stage
            if frame_validity_diagnostics["invalid_frames"] > 0:
                # Check if invalid frames are from specific submissions or outputs
                invalid_frame_sources = {}
                for diag in frame_validity_diagnostics["per_frame_diagnostics"]:
                    if diag["stage_b"]["invalid"]:
                        source_key = f"submission_{diag['source_submission_index']}_output_{diag['source_output_index']}"
                        invalid_frame_sources[source_key] = invalid_frame_sources.get(source_key, 0) + 1
                
                if invalid_frame_sources:
                    frame_validity_diagnostics["black_frame_root_cause"] = f"invalid_outputs_at_sources: {list(invalid_frame_sources.keys())}"
                    print(f"[MK-6K-R] Invalid frame sources: {frame_validity_diagnostics['black_frame_root_cause']}")
                
                # Determine first bad stage based on diagnostics
                # Stage B is the fetched payload from ComfyUI - if invalid here, defect is in Comfy generation
                if frame_validity_diagnostics["invalid_frames"] > 0:
                    frame_validity_diagnostics["first_bad_stage"] = "stage_b_fetched_payload"
                    print(f"[MK-6K-R] First bad stage: {frame_validity_diagnostics['first_bad_stage']} (defect in Comfy generation)")
            
            # Add frame validity to generation diagnostics
            generation_diagnostics["frame_validity"] = frame_validity_diagnostics
            timing_breakdown["frame_validity"] = frame_validity_diagnostics

            manifest.set_processing(
                processed_dir=processed_dir,
                processed_count=processed_count,
                processor=video_workflow,
                per_frame=per_frame_linkage,
                prompt=video_prompt,
                recipe=comfy_recipe,
            )
            persistence.save(manifest)

            # Step 4: Assemble video
            print(f"[MK-3] Assembling video from {processed_count} frames")
            assemble_frames(processed_dir, video_path, fps=fps)
            manifest.set_export(video_path, fps=fps)
            persistence.save(manifest)

            # Step 5: Run video QC
            print(f"[MK-3] Running video QC")
            manifest_path = self.manifests_dir / f"video_{scene_id}.json"
            qc_report = run_video_qc(manifest_path=str(manifest_path))
            result.qc_report_path = qc_report.get("qc_report_path")

            # Step 6: Compute scene verdict with quality heuristics
            scene_verdict, scene_reasons, quality_analysis = self._compute_scene_verdict(
                qc_report, video_prompt, comfy_recipe
            )
            result.scene_verdict = scene_verdict
            result.scene_reasons = scene_reasons

            # Add frame-integrity diagnostics to timing_breakdown
            if quality_analysis:
                motion_analysis = quality_analysis.get("motion_analysis", {})
                # Get frame count from summary export_frame_count
                summary = qc_report.get("summary", {})
                timing_breakdown["frame_integrity"] = {
                    "frame_count": summary.get("export_frame_count", 0),
                    "motion_score": motion_analysis.get("motion_score", 0),
                    "repetitive_ratio": motion_analysis.get("repetitive_ratio", 0),
                    "frozen_ratio": motion_analysis.get("frozen_ratio", 0),
                }

            # Update manifest with scene decision and quality analysis
            manifest.set_qc({
                "scene_verdict": scene_verdict,
                "scene_reasons": scene_reasons,
                "qc_report_path": result.qc_report_path,
                "quality_analysis": quality_analysis,
            })
            manifest.complete()
            persistence.save(manifest)

            result.status = "completed"
            result.generation_end = datetime.utcnow().isoformat()
            result.timing_breakdown = timing_breakdown

            print(f"[MK-3] Scene generation complete: {scene_verdict.upper()}")
            print(f"[MK-3] Video: {video_path}")
            print(f"[MK-3] Manifest: {result.manifest_path}")
            print(f"[MK-3] QC Report: {result.qc_report_path}")

        except Exception as exc:
            result.status = "failed"
            result.error = str(exc)
            result.generation_end = datetime.utcnow().isoformat()
            manifest.fail(str(exc))
            persistence.save(manifest)
            raise

        return result


async def run_scene_agent(
    reference_image_path: str,
    user_prompt: str | None = None,
    num_frames: int = 8,
    fps: float = 12.0,
    comfy_recipe: dict[str, Any] | None = None,
    reference_locked: bool = False,
    batch_mode: bool = False,
    bounded_mode: bool = False,
) -> SceneResult:
    """Run scene agent with reference image.

    Args:
        reference_image_path: Path to reference image
        user_prompt: Optional user-specified prompt
        num_frames: Number of video frames to generate
        fps: Output video FPS
        comfy_recipe: Optional ComfyUI recipe overrides

    Returns:
        SceneResult with generation details and verdict
    """
    agent = SceneAgent()
    return await agent.generate_scene(
        reference_image_path=reference_image_path,
        user_prompt=user_prompt,
        num_frames=num_frames,
        fps=fps,
        comfy_recipe=comfy_recipe,
        reference_locked=reference_locked,
        batch_mode=batch_mode,
        bounded_mode=bounded_mode,
    )
