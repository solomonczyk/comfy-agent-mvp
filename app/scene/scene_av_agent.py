"""
Scene AV Agent - MK-5

Attaches audio to scene videos and runs QC on synced scenes.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import subprocess
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

try:
    from moviepy import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False


@dataclass
class SceneAVConfig:
    """Configuration for scene AV attachment."""
    scene_manifest_path: str
    output_synced_dir: str
    av_route: str = "audio_mux"  # audio_mux or lipsync


@dataclass
class SceneAVResult:
    """Result of scene AV attachment."""
    scene_id: str
    status: str
    source_video_path: str
    source_audio_path: str
    av_route: str
    synced_scene_path: str
    av_processing_fragment: dict[str, Any]
    qc_fragment: dict[str, Any]
    decision_fragment: dict[str, Any]
    manifest_path: str
    error: str | None = None


class SceneAVAgent:
    """Agent for attaching audio to scene videos and running QC."""

    def __init__(
        self,
        manifests_dir: str,
        synced_output_dir: str,
    ):
        self.manifests_dir = Path(manifests_dir)
        self.synced_output_dir = Path(synced_output_dir)
        self.synced_output_dir.mkdir(parents=True, exist_ok=True)

    def _load_scene_manifest(self, scene_manifest_path: str) -> dict[str, Any]:
        """Load scene manifest from file."""
        with open(scene_manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _extract_audio_from_manifest(self, scene_manifest: dict[str, Any]) -> str | None:
        """Extract audio path from manifest audio section."""
        audio_section = scene_manifest.get("audio", {})
        audio_path = audio_section.get("audio_path")
        return audio_path

    def _extract_video_from_manifest(self, scene_manifest: dict[str, Any]) -> str:
        """Extract video path from manifest export section."""
        export_section = scene_manifest.get("export", {})
        video_path = export_section.get("export_path", "")
        return video_path

    def _attach_audio_mux(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
    ) -> dict[str, Any]:
        """Attach audio to video using audio mux (ffmpeg)."""
        if not FFMPEG_AVAILABLE:
            raise ValueError("subprocess not available for ffmpeg")

        # Get durations to determine if audio trimming is needed
        video_duration = 0
        original_audio_duration = 0

        if MOVIEPY_AVAILABLE:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            video_duration = video_clip.duration
            original_audio_duration = audio_clip.duration
            video_clip.close()
            audio_clip.close()

        # Practical handling strategy: trim audio to match video if audio is significantly longer
        # This makes the synced scene more usable by including the full video duration
        audio_to_use = audio_path
        trimmed_audio = False
        trimmed_audio_duration = original_audio_duration

        if original_audio_duration > 0 and video_duration > 0:
            av_ratio = original_audio_duration / video_duration
            if av_ratio > 1.5:  # Audio is 1.5x longer than video - trim it
                # Create temporary trimmed audio file
                temp_audio = output_path.replace(".mp4", "_temp_audio.wav")
                trim_cmd = [
                    "ffmpeg",
                    "-i", audio_path,
                    "-t", str(video_duration),
                    "-y",
                    temp_audio,
                ]
                trim_result = subprocess.run(trim_cmd, capture_output=True, text=True)
                if trim_result.returncode == 0:
                    audio_to_use = temp_audio
                    trimmed_audio = True
                    trimmed_audio_duration = video_duration

        # Use ffmpeg to combine video and audio
        # -i video: input video
        # -i audio: input audio (possibly trimmed)
        # -c:v libx264: video codec
        # -c:a aac: audio codec
        # -shortest: use shortest duration (as fallback)
        # -y: overwrite output
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_to_use,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            "-y",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temporary audio file if it was created
        if trimmed_audio:
            try:
                Path(audio_to_use).unlink()
            except:
                pass

        if result.returncode != 0:
            raise ValueError(f"ffmpeg failed: {result.stderr}")

        # Get actual synced duration for accurate reporting
        synced_duration = 0
        if MOVIEPY_AVAILABLE:
            synced_clip = VideoFileClip(output_path)
            synced_duration = synced_clip.duration
            synced_clip.close()

        return {
            "route": "audio_mux_ffmpeg",
            "video_duration": video_duration,
            "original_audio_duration": original_audio_duration,
            "trimmed_audio_duration": trimmed_audio_duration if trimmed_audio else original_audio_duration,
            "final_duration": synced_duration,
            "codec": "libx264",
            "audio_codec": "aac",
            "audio_trimmed": trimmed_audio,
            "av_ratio": original_audio_duration / video_duration if video_duration > 0 else 0,
        }

    def _assess_voiceover_readiness(
        self,
        scene_manifest: dict[str, Any],
    ) -> dict[str, Any]:
        """Assess whether a scene is suitable for voiceover attachment."""
        readiness_checks = {}
        readiness_verdict = "accept_voiceover"
        readiness_reasons = []

        # Get scene duration
        export_section = scene_manifest.get("export", {})
        video_path = export_section.get("export_path", "")
        
        video_duration = 0
        if MOVIEPY_AVAILABLE and video_path:
            try:
                video_clip = VideoFileClip(video_path)
                video_duration = video_clip.duration
                video_clip.close()
            except:
                pass

        # Check 1: Scene duration - very short scenes are not suitable for meaningful voiceover
        if video_duration < 1.0:
            readiness_checks["scene_duration"] = {
                "passed": False,
                "reason": f"Scene is too short ({video_duration}s) for meaningful voiceover",
                "duration": video_duration,
                "minimum_required": 1.0,
            }
            readiness_verdict = "reject_for_voiceover"
            readiness_reasons.append(f"Scene too short ({video_duration}s < 1.0s minimum) for voiceover")
        else:
            readiness_checks["scene_duration"] = {
                "passed": True,
                "duration": video_duration,
            }

        # Check 2: Voiceover text - reject trivial text hacks
        audio_section = scene_manifest.get("audio", {})
        voiceover_text = audio_section.get("voiceover_text", "")
        
        if voiceover_text:
            word_count = len(voiceover_text.split())
            char_count = len(voiceover_text.strip())
            
            # Reject if text is trivial (single character or very short)
            if char_count < 3:
                readiness_checks["voiceover_text"] = {
                    "passed": False,
                    "reason": f"Voiceover text is too trivial ({char_count} characters)",
                    "text": voiceover_text,
                    "char_count": char_count,
                    "minimum_required": 3,
                }
                readiness_verdict = "reject_for_voiceover"
                readiness_reasons.append(f"Voiceover text too trivial ({char_count} chars < 3 minimum)")
            elif word_count < 2:
                readiness_checks["voiceover_text"] = {
                    "passed": False,
                    "reason": f"Voiceover text is too short ({word_count} words)",
                    "text": voiceover_text,
                    "word_count": word_count,
                    "minimum_required": 2,
                }
                readiness_verdict = "reject_for_voiceover"
                readiness_reasons.append(f"Voiceover text too short ({word_count} words < 2 minimum)")
            else:
                readiness_checks["voiceover_text"] = {
                    "passed": True,
                    "text": voiceover_text,
                    "word_count": word_count,
                    "char_count": char_count,
                }
        else:
            readiness_checks["voiceover_text"] = {
                "passed": False,
                "reason": "No voiceover text found",
            }
            readiness_verdict = "no_voiceover_needed"
            readiness_reasons.append("No voiceover text provided")

        return {
            "verdict": readiness_verdict,
            "reasons": readiness_reasons,
            "checks": readiness_checks,
        }

    def _run_synced_scene_qc(
        self,
        synced_scene_path: str,
        source_video_path: str,
        source_audio_path: str,
        actual_audio_duration: float | None = None,
    ) -> dict[str, Any]:
        """Run lightweight QC on synced scene."""
        qc_checks = {}
        reasons = []
        verdict = "accept"

        # Check 1: Export validity (file exists and is readable)
        try:
            synced_path = Path(synced_scene_path)
            if not synced_path.exists():
                qc_checks["export_validity"] = {"passed": False, "reason": "Synced scene file does not exist"}
                verdict = "reject"
                reasons.append("Synced scene file does not exist")
            else:
                qc_checks["export_validity"] = {"passed": True}
        except Exception as e:
            qc_checks["export_validity"] = {"passed": False, "reason": str(e)}
            verdict = "reject"
            reasons.append(f"Export validity check failed: {e}")

        if verdict == "reject":
            return {
                "verdict": verdict,
                "reasons": reasons,
                "checks": qc_checks,
            }

        # Check 2: Audio stream presence (using moviepy)
        try:
            video_clip = VideoFileClip(synced_scene_path)
            has_audio = video_clip.audio is not None
            video_clip.close()

            if has_audio:
                qc_checks["audio_stream"] = {"passed": True}
            else:
                qc_checks["audio_stream"] = {"passed": False, "reason": "No audio stream detected"}
                verdict = "reject"
                reasons.append("No audio stream in synced scene")
        except Exception as e:
            qc_checks["audio_stream"] = {"passed": False, "reason": str(e)}
            verdict = "retry_candidate"
            reasons.append(f"Audio stream check failed: {e}")

        if verdict == "reject":
            return {
                "verdict": verdict,
                "reasons": reasons,
                "checks": qc_checks,
            }

        # Check 3: Duration sanity - honest validation with voiceover timing policy
        try:
            source_video = VideoFileClip(source_video_path)
            synced_video = VideoFileClip(synced_scene_path)

            source_video_duration = source_video.duration
            synced_duration = synced_video.duration

            source_video.close()
            synced_video.close()

            # Use provided actual_audio_duration if available, otherwise get from source audio
            if actual_audio_duration is not None:
                audio_duration = actual_audio_duration
            else:
                source_audio = AudioFileClip(source_audio_path)
                audio_duration = source_audio.duration
                source_audio.close()

            # Voiceover timing policy:
            # - For a usable synced scene, audio should be reasonably matched to video duration
            # - If audio is much longer than video, the voiceover won't fit and the scene is not usable
            # - If audio is much shorter than video, the scene will have silent gaps
            duration_diff = abs(synced_duration - source_video_duration)
            
            # Calculate audio/video ratio
            if source_video_duration > 0:
                av_ratio = audio_duration / source_video_duration
            else:
                av_ratio = 0

            # Check if synced duration matches source video (should be same due to -shortest)
            if duration_diff < 0.1:  # Tight tolerance for duration match
                qc_checks["duration_sanity"] = {
                    "passed": True,
                    "source_video_duration": source_video_duration,
                    "source_audio_duration": audio_duration,
                    "synced_duration": synced_duration,
                    "av_ratio": av_ratio,
                }
            else:
                # Duration mismatch - this is a real issue
                qc_checks["duration_sanity"] = {
                    "passed": False,
                    "reason": f"Duration mismatch: synced={synced_duration}s, source_video={source_video_duration}s",
                    "source_video_duration": source_video_duration,
                    "source_audio_duration": audio_duration,
                    "synced_duration": synced_duration,
                    "av_ratio": av_ratio,
                }
                verdict = "retry_candidate"
                reasons.append(f"Duration sanity check failed: synced={synced_duration}s vs source={source_video_duration}s")

            # Voiceover timing policy: reject scenes with strong audio/video duration mismatch
            # Audio should be within reasonable range of video duration for usable voiceover
            # Acceptable range: 0.5x to 2.0x for normal videos
            # For very short videos (<1s), use 3.0x as upper limit since TTS has minimum duration
            max_ratio = 3.0 if source_video_duration < 1.0 else 2.0
            if av_ratio < 0.5:  # Audio is less than half the video duration - will have silent gaps
                if verdict != "reject":
                    verdict = "retry_candidate"
                    reasons.append(f"Voiceover timing policy: audio is too short for scene (ratio={av_ratio:.1f}:1) - will have silent gaps")
            elif av_ratio > max_ratio:  # Audio is too long for the video duration
                if verdict != "reject":
                    verdict = "retry_candidate"
                    reasons.append(f"Voiceover timing policy: audio is too long for scene (ratio={av_ratio:.1f}:1) - won't fit without destructive trimming")

        except Exception as e:
            qc_checks["duration_sanity"] = {"passed": False, "reason": str(e)}
            verdict = "retry_candidate"
            reasons.append(f"Duration sanity check failed: {e}")

        # Check 4: Basic A/V attachment integrity
        try:
            synced_clip = VideoFileClip(synced_scene_path)
            has_video = synced_clip.duration > 0
            has_audio = synced_clip.audio is not None
            synced_clip.close()

            if has_video and has_audio:
                qc_checks["av_integrity"] = {"passed": True, "has_video": has_video, "has_audio": has_audio}
            else:
                qc_checks["av_integrity"] = {
                    "passed": False,
                    "reason": f"Missing streams: has_video={has_video}, has_audio={has_audio}",
                }
                verdict = "retry_candidate"
                reasons.append("A/V attachment integrity check failed")
        except Exception as e:
            qc_checks["av_integrity"] = {"passed": False, "reason": str(e)}
            verdict = "retry_candidate"
            reasons.append(f"A/V integrity check failed: {e}")

        return {
            "verdict": verdict,
            "reasons": reasons,
            "checks": qc_checks,
        }

    def _create_synced_linkage(
        self,
        scene_manifest: dict[str, Any],
        synced_scene_path: str,
        av_route: str,
        av_processing_fragment: dict[str, Any],
        qc_fragment: dict[str, Any],
        decision_fragment: dict[str, Any],
    ) -> dict[str, Any]:
        """Create synced scene linkage fragment."""
        scene_id = scene_manifest.get("video_id", "unknown")
        source_video_path = scene_manifest.get("export", {}).get("export_path", "")
        source_audio_path = scene_manifest.get("audio", {}).get("audio_path", "")

        linkage = {
            "scene_id": scene_id,
            "source_video_path": source_video_path,
            "source_audio_path": source_audio_path,
            "synced_scene_path": synced_scene_path,
            "av_route": av_route,
            "av_processing": av_processing_fragment,
            "qc": qc_fragment,
            "decision": decision_fragment,
            "synced_at": datetime.now().isoformat(),
            "linkage_type": "scene_av_synced",
        }

        return linkage

    def _update_manifest_with_synced_scene(
        self,
        scene_manifest: dict[str, Any],
        synced_scene_path: str,
        av_route: str,
        av_processing_fragment: dict[str, Any],
        qc_fragment: dict[str, Any],
        decision_fragment: dict[str, Any],
        linkage: dict[str, Any],
    ) -> dict[str, Any]:
        """Update scene manifest with synced scene information."""
        # Add synced section if not exists
        if "synced" not in scene_manifest:
            scene_manifest["synced"] = {}

        scene_manifest["synced"]["synced_scene_path"] = synced_scene_path
        scene_manifest["synced"]["av_route"] = av_route
        scene_manifest["synced"]["av_processing"] = av_processing_fragment
        scene_manifest["synced"]["qc"] = qc_fragment
        scene_manifest["synced"]["decision"] = decision_fragment
        scene_manifest["synced"]["generated_at"] = datetime.now().isoformat()
        scene_manifest["synced"]["linkage"] = linkage

        return scene_manifest

    def _save_manifest(self, manifest: dict[str, Any], manifest_path: str) -> None:
        """Save updated manifest to file."""
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def attach_audio_to_scene(
        self,
        config: SceneAVConfig,
    ) -> SceneAVResult:
        """Attach audio to scene video and run QC.

        Args:
            config: SceneAVConfig with scene manifest path and settings

        Returns:
            SceneAVResult with synced scene path and QC information
        """
        try:
            # Step 1: Load scene manifest
            scene_manifest = self._load_scene_manifest(config.scene_manifest_path)
            scene_id = scene_manifest.get("video_id", "unknown")

            # Step 2: Extract source video and audio paths
            source_video_path = self._extract_video_from_manifest(scene_manifest)
            source_audio_path = self._extract_audio_from_manifest(scene_manifest)

            if not source_video_path:
                raise ValueError("Source video path not found in manifest")
            if not source_audio_path:
                raise ValueError("Source audio path not found in manifest")

            # Step 2.5: Assess voiceover readiness before proceeding
            voiceover_readiness = self._assess_voiceover_readiness(scene_manifest)
            
            # If scene is not voiceover-ready, skip AV attachment and return early
            if voiceover_readiness["verdict"] == "reject_for_voiceover":
                return SceneAVResult(
                    scene_id=scene_id,
                    status="completed",
                    source_video_path=source_video_path,
                    source_audio_path=source_audio_path,
                    av_route=config.av_route,
                    synced_scene_path="",  # No synced scene produced
                    av_processing_fragment={},
                    qc_fragment={
                        "verdict": "reject_for_voiceover",
                        "reasons": voiceover_readiness["reasons"],
                        "checks": voiceover_readiness["checks"],
                    },
                    decision_fragment={
                        "verdict": "reject_for_voiceover",
                        "reasons": voiceover_readiness["reasons"],
                    },
                    manifest_path=config.scene_manifest_path,
                    error=None,
                )

            # Step 3: Generate synced scene output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            synced_filename = f"scene_synced_{scene_id}_{timestamp}.mp4"
            synced_scene_path = str(self.synced_output_dir / synced_filename)

            # Step 4: Attach audio using selected route
            if config.av_route == "audio_mux":
                av_processing_fragment = self._attach_audio_mux(
                    video_path=source_video_path,
                    audio_path=source_audio_path,
                    output_path=synced_scene_path,
                )
            else:
                raise ValueError(f"Unsupported AV route: {config.av_route}")

            # Step 5: Run QC on synced scene (use original audio duration for voiceover timing policy)
            original_audio_duration = av_processing_fragment.get("original_audio_duration", 0)
            qc_fragment = self._run_synced_scene_qc(
                synced_scene_path=synced_scene_path,
                source_video_path=source_video_path,
                source_audio_path=source_audio_path,
                actual_audio_duration=original_audio_duration,
            )

            # Step 6: Extract decision from QC
            decision_fragment = {
                "verdict": qc_fragment["verdict"],
                "reasons": qc_fragment["reasons"],
            }

            # Step 7: Create synced linkage
            linkage = self._create_synced_linkage(
                scene_manifest=scene_manifest,
                synced_scene_path=synced_scene_path,
                av_route=config.av_route,
                av_processing_fragment=av_processing_fragment,
                qc_fragment=qc_fragment,
                decision_fragment=decision_fragment,
            )

            # Step 8: Update manifest with synced scene information
            updated_manifest = self._update_manifest_with_synced_scene(
                scene_manifest=scene_manifest,
                synced_scene_path=synced_scene_path,
                av_route=config.av_route,
                av_processing_fragment=av_processing_fragment,
                qc_fragment=qc_fragment,
                decision_fragment=decision_fragment,
                linkage=linkage,
            )

            # Step 9: Save updated manifest
            self._save_manifest(updated_manifest, config.scene_manifest_path)

            return SceneAVResult(
                scene_id=scene_id,
                status="completed",
                source_video_path=source_video_path,
                source_audio_path=source_audio_path,
                av_route=config.av_route,
                synced_scene_path=synced_scene_path,
                av_processing_fragment=av_processing_fragment,
                qc_fragment=qc_fragment,
                decision_fragment=decision_fragment,
                manifest_path=config.scene_manifest_path,
                error=None,
            )

        except Exception as e:
            return SceneAVResult(
                scene_id="unknown",
                status="failed",
                source_video_path="",
                source_audio_path="",
                av_route=config.av_route,
                synced_scene_path="",
                av_processing_fragment={},
                qc_fragment={},
                decision_fragment={},
                manifest_path=config.scene_manifest_path,
                error=str(e),
            )


def run_scene_av(
    scene_manifest_path: str,
    av_route: str = "audio_mux",
) -> dict[str, Any]:
    """Run scene AV attachment and QC.

    Args:
        scene_manifest_path: Path to scene manifest JSON
        av_route: AV attachment route (default: audio_mux)

    Returns:
        Dictionary with generation results
    """
    # Set up paths
    manifests_dir = "data/manifests"
    synced_output_dir = "data/videos/synced_scenes"

    # Check ffmpeg availability
    if not FFMPEG_AVAILABLE:
        return {
            "status": "failed",
            "error": "subprocess not available for ffmpeg",
            "scene_id": "unknown",
            "source_video_path": "",
            "source_audio_path": "",
            "av_route": av_route,
            "synced_scene_path": "",
            "av_processing_fragment": {},
            "qc_fragment": {},
            "decision_fragment": {},
            "manifest_path": scene_manifest_path,
        }

    # Create config
    config = SceneAVConfig(
        scene_manifest_path=scene_manifest_path,
        output_synced_dir=synced_output_dir,
        av_route=av_route,
    )

    # Create agent and attach audio
    agent = SceneAVAgent(manifests_dir, synced_output_dir)
    result = agent.attach_audio_to_scene(config)

    return {
        "status": result.status,
        "scene_id": result.scene_id,
        "source_video_path": result.source_video_path,
        "source_audio_path": result.source_audio_path,
        "av_route": result.av_route,
        "synced_scene_path": result.synced_scene_path,
        "av_processing_fragment": result.av_processing_fragment,
        "qc_fragment": result.qc_fragment,
        "decision_fragment": result.decision_fragment,
        "manifest_path": result.manifest_path,
        "error": result.error,
    }
