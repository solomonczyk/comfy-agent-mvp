"""MK-CTRL17 — Production artifact capture parser.

Parses subprocess stdout to extract generation artifact paths.
Resolves relative paths and verifies file existence.

MK-CTRL20 — Added frame manifest parsing for generation-only command contract.
MK-CTRL21 — Added scene artifact parsing for assemble_scene command contract.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_generation_artifacts(stdout: str, cwd: Path | None = None) -> dict[str, Any]:
    """Parse generation artifacts from subprocess stdout.

    MK-CTRL20 — Detects lines from generation-only command:
    - Frame manifest saved: <path>
    - Generated frames dir: <path>
    - Generated frame count: <count>

    MK-CTRL21 — Detects lines from assemble_scene command:
    - Scene MP4 saved: <path>
    - Scene manifest saved: <path>
    - Scene duration seconds: <duration>
    - Scene frame count: <count>

    MK-CTRL22 — Detects lines from qa-review command:
    - QA report saved: <path>
    - QA verdict: pass/fail
    - QA score: <float>
    - QA reasons: <comma-separated reasons>

    MK-CTRL23 — Detects lines from attach-audio command:
    - Audio attached MP4 saved: <path>
    - Audio manifest saved: <path>
    - Audio duration seconds: <duration>
    - Audio engine: <engine>
    - Audio skipped: no dialogue

    MK-CTRL24 — Detects lines from render-episode command:
    - Episode MP4 saved: <path>
    - Episode manifest saved: <path>
    - Episode duration seconds: <duration>
    - Episode scene count: <count>

    Also maintains backward compatibility with:
    - Manifest saved: <path>
    - Episode saved: <path>

    Args:
        stdout: Subprocess stdout text.
        cwd: Current working directory for resolving relative paths.
            If None, uses current working directory.

    Returns:
        Dict with artifact fields:
        - frame_manifest_path: str | None (MK-CTRL20)
        - generated_frames_dir: str | None (MK-CTRL20)
        - frame_count: int | None (MK-CTRL20)
        - scene_output_path: str | None (MK-CTRL21)
        - scene_manifest_path: str | None (MK-CTRL21)
        - scene_duration_sec: float | None (MK-CTRL21)
        - scene_frame_count: int | None (MK-CTRL21)
        - qa_report_path: str | None (MK-CTRL22)
        - qa_verdict: str | None (MK-CTRL22)
        - qa_score: float | None (MK-CTRL22)
        - qa_reasons: list[str] (MK-CTRL22)
        - audio_output_path: str | None (MK-CTRL23)
        - audio_manifest_path: str | None (MK-CTRL23)
        - audio_duration_sec: float | None (MK-CTRL23)
        - audio_engine: str | None (MK-CTRL23)
        - audio_skipped: bool (MK-CTRL23)
        - episode_output_path: str | None (MK-CTRL24)
        - episode_manifest_path: str | None (MK-CTRL24)
        - episode_duration_sec: float | None (MK-CTRL24)
        - episode_scene_count: int | None (MK-CTRL24)
        - manifest_path: str | None (legacy)
        - episode_output_path: str | None (legacy)
        - output_exists: bool
        - output_size_bytes: int | None
    """
    frame_manifest_path: str | None = None
    generated_frames_dir: str | None = None
    frame_count: int | None = None
    scene_output_path: str | None = None
    scene_manifest_path: str | None = None
    scene_duration_sec: float | None = None
    scene_frame_count: int | None = None
    qa_report_path: str | None = None  # MK-CTRL22
    qa_verdict: str | None = None  # MK-CTRL22
    qa_score: float | None = None  # MK-CTRL22
    qa_reasons: list[str] = []  # MK-CTRL22
    audio_output_path: str | None = None  # MK-CTRL23
    audio_manifest_path: str | None = None  # MK-CTRL23
    audio_duration_sec: float | None = None  # MK-CTRL23
    audio_engine: str | None = None  # MK-CTRL23
    audio_skipped: bool = False  # MK-CTRL23
    episode_output_path: str | None = None  # MK-CTRL24
    episode_manifest_path: str | None = None  # MK-CTRL24
    episode_duration_sec: float | None = None  # MK-CTRL24
    episode_scene_count: int | None = None  # MK-CTRL24
    manifest_path: str | None = None

    # MK-CTRL20 — Parse frame manifest (generation-only command)
    frame_manifest_match = re.search(r"Frame manifest saved:\s*(.+)", stdout)
    if frame_manifest_match:
        frame_manifest_path = frame_manifest_match.group(1).strip()

    # MK-CTRL20 — Parse generated frames dir
    frames_dir_match = re.search(r"Generated frames dir:\s*(.+)", stdout)
    if frames_dir_match:
        generated_frames_dir = frames_dir_match.group(1).strip()

    # MK-CTRL20 — Parse frame count
    frame_count_match = re.search(r"Generated frame count:\s*(\d+)", stdout)
    if frame_count_match:
        frame_count = int(frame_count_match.group(1))

    # MK-CTRL21 — Parse scene MP4 path
    scene_mp4_match = re.search(r"Scene MP4 saved:\s*(.+)", stdout)
    if scene_mp4_match:
        scene_output_path = scene_mp4_match.group(1).strip()

    # MK-CTRL21 — Parse scene manifest path
    scene_manifest_match = re.search(r"Scene manifest saved:\s*(.+)", stdout)
    if scene_manifest_match:
        scene_manifest_path = scene_manifest_match.group(1).strip()

    # MK-CTRL21 — Parse scene duration
    scene_duration_match = re.search(r"Scene duration seconds:\s*([\d.]+)", stdout)
    if scene_duration_match:
        scene_duration_sec = float(scene_duration_match.group(1))

    # MK-CTRL21 — Parse scene frame count
    scene_frame_count_match = re.search(r"Scene frame count:\s*(\d+)", stdout)
    if scene_frame_count_match:
        scene_frame_count = int(scene_frame_count_match.group(1))

    # MK-CTRL22 — Parse QA report path
    qa_report_match = re.search(r"QA report saved:\s*(.+)", stdout)
    if qa_report_match:
        qa_report_path = qa_report_match.group(1).strip()

    # MK-CTRL22 — Parse QA verdict
    qa_verdict_match = re.search(r"QA verdict:\s*(\w+)", stdout)
    if qa_verdict_match:
        qa_verdict = qa_verdict_match.group(1).strip()

    # MK-CTRL22 — Parse QA score
    qa_score_match = re.search(r"QA score:\s*([\d.]+)", stdout)
    if qa_score_match:
        qa_score = float(qa_score_match.group(1))

    # MK-CTRL22 — Parse QA reasons
    qa_reasons_match = re.search(r"QA reasons:\s*(.+)", stdout)
    if qa_reasons_match:
        qa_reasons = qa_reasons_match.group(1).strip().split(",")

    # MK-CTRL23 — Parse audio output path
    audio_output_match = re.search(r"Audio attached MP4 saved:\s*(.+)", stdout)
    if audio_output_match:
        audio_output_path = audio_output_match.group(1).strip()

    # MK-CTRL23 — Parse audio manifest path
    audio_manifest_match = re.search(r"Audio manifest saved:\s*(.+)", stdout)
    if audio_manifest_match:
        audio_manifest_path = audio_manifest_match.group(1).strip()

    # MK-CTRL23 — Parse audio duration seconds
    audio_duration_match = re.search(r"Audio duration seconds:\s*([\d.]+)", stdout)
    if audio_duration_match:
        audio_duration_sec = float(audio_duration_match.group(1))

    # MK-CTRL23 — Parse audio engine
    audio_engine_match = re.search(r"Audio engine:\s*(\w+)", stdout)
    if audio_engine_match:
        audio_engine = audio_engine_match.group(1).strip()

    # MK-CTRL23 — Parse audio skipped
    audio_skipped_match = re.search(r"Audio skipped:\s*(.+)", stdout)
    if audio_skipped_match:
        audio_skipped = audio_skipped_match.group(1).strip() == "no dialogue"

    # MK-CTRL24 — Parse episode output path
    episode_output_match = re.search(r"Episode MP4 saved:\s*(.+)", stdout)
    if episode_output_match:
        episode_output_path = episode_output_match.group(1).strip()

    # MK-CTRL24 — Parse episode manifest path
    episode_manifest_match = re.search(r"Episode manifest saved:\s*(.+)", stdout)
    if episode_manifest_match:
        episode_manifest_path = episode_manifest_match.group(1).strip()

    # MK-CTRL24 — Parse episode duration seconds
    episode_duration_match = re.search(r"Episode duration seconds:\s*([\d.]+)", stdout)
    if episode_duration_match:
        episode_duration_sec = float(episode_duration_match.group(1))

    # MK-CTRL24 — Parse episode scene count
    episode_scene_count_match = re.search(r"Episode scene count:\s*(\d+)", stdout)
    if episode_scene_count_match:
        episode_scene_count = int(episode_scene_count_match.group(1))

    # Parse legacy manifest path
    manifest_match = re.search(r"Manifest saved:\s*(.+)", stdout)
    if manifest_match:
        manifest_path = manifest_match.group(1).strip()

    # Parse legacy episode output path
    episode_match = re.search(r"Episode saved:\s*(.+)", stdout)
    if episode_match:
        episode_output_path = episode_match.group(1).strip()

    # Resolve paths relative to cwd if provided
    base_dir = Path(cwd) if cwd else Path.cwd()
    if frame_manifest_path and not Path(frame_manifest_path).is_absolute():
        frame_manifest_path = str(base_dir / frame_manifest_path)
    if generated_frames_dir and not Path(generated_frames_dir).is_absolute():
        generated_frames_dir = str(base_dir / generated_frames_dir)
    if scene_output_path and not Path(scene_output_path).is_absolute():
        scene_output_path = str(base_dir / scene_output_path)
    if scene_manifest_path and not Path(scene_manifest_path).is_absolute():
        scene_manifest_path = str(base_dir / scene_manifest_path)
    if qa_report_path and not Path(qa_report_path).is_absolute():  # MK-CTRL22
        qa_report_path = str(base_dir / qa_report_path)
    if manifest_path and not Path(manifest_path).is_absolute():
        manifest_path = str(base_dir / manifest_path)
    if episode_output_path and not Path(episode_output_path).is_absolute():
        episode_output_path = str(base_dir / episode_output_path)
    if audio_output_path and not Path(audio_output_path).is_absolute():  # MK-CTRL23
        audio_output_path = str(base_dir / audio_output_path)
    if audio_manifest_path and not Path(audio_manifest_path).is_absolute():  # MK-CTRL23
        audio_manifest_path = str(base_dir / audio_manifest_path)
    if episode_output_path and not Path(episode_output_path).is_absolute():  # MK-CTRL24
        episode_output_path = str(base_dir / episode_output_path)
    if episode_manifest_path and not Path(episode_manifest_path).is_absolute():  # MK-CTRL24
        episode_manifest_path = str(base_dir / episode_manifest_path)

    # Verify output file existence and size
    output_exists = False
    output_size_bytes: int | None = None
    
    # MK-CTRL24 — Prioritize episode output for output verification
    if episode_output_path:
        episode_path = Path(episode_output_path)
        if episode_path.exists():
            output_exists = True
            output_size_bytes = episode_path.stat().st_size
    # MK-CTRL23 — Prioritize audio output for output verification
    elif audio_output_path:
        audio_path = Path(audio_output_path)
        if audio_path.exists():
            output_exists = True
            output_size_bytes = audio_path.stat().st_size
    # MK-CTRL22 — Prioritize QA report for output verification
    elif qa_report_path:
        qa_report_file = Path(qa_report_path)
        if qa_report_file.exists():
            output_exists = True
            output_size_bytes = qa_report_file.stat().st_size
    # MK-CTRL21 — Prioritize scene MP4 for output verification
    elif scene_output_path:
        scene_path = Path(scene_output_path)
        if scene_path.exists():
            output_exists = True
            output_size_bytes = scene_path.stat().st_size
    # MK-CTRL20 — Next prioritize frame manifest for output verification
    elif frame_manifest_path:
        manifest_file = Path(frame_manifest_path)
        if manifest_file.exists():
            output_exists = True
            output_size_bytes = manifest_file.stat().st_size

    return {
        "frame_manifest_path": frame_manifest_path,
        "generated_frames_dir": generated_frames_dir,
        "frame_count": frame_count,
        "scene_output_path": scene_output_path,
        "scene_manifest_path": scene_manifest_path,
        "scene_duration_sec": scene_duration_sec,
        "scene_frame_count": scene_frame_count,
        "qa_report_path": qa_report_path,  # MK-CTRL22
        "qa_verdict": qa_verdict,  # MK-CTRL22
        "qa_score": qa_score,  # MK-CTRL22
        "qa_reasons": qa_reasons,  # MK-CTRL22
        "audio_output_path": audio_output_path,  # MK-CTRL23
        "audio_manifest_path": audio_manifest_path,  # MK-CTRL23
        "audio_duration_sec": audio_duration_sec,  # MK-CTRL23
        "audio_engine": audio_engine,  # MK-CTRL23
        "audio_skipped": audio_skipped,  # MK-CTRL23
        "episode_output_path": episode_output_path,  # MK-CTRL24
        "episode_manifest_path": episode_manifest_path,  # MK-CTRL24
        "episode_duration_sec": episode_duration_sec,  # MK-CTRL24
        "episode_scene_count": episode_scene_count,  # MK-CTRL24
        "manifest_path": manifest_path,
        "output_exists": output_exists,
        "output_size_bytes": output_size_bytes,
    }


def evaluate_artifact_acceptance(
    returncode: int,
    subprocess_invoked: bool,
    frame_manifest_path: str | None = None,
    frame_count: int | None = None,
    output_exists: bool = False,
    output_size_bytes: int | None = None,
    scene_output_path: str | None = None,
    scene_manifest_path: str | None = None,
    scene_duration_sec: float | None = None,
    scene_frame_count: int | None = None,
    qa_report_path: str | None = None,  # MK-CTRL22
    qa_verdict: str | None = None,  # MK-CTRL22
    qa_score: float | None = None,  # MK-CTRL22
    qa_reasons: list[str] | None = None,  # MK-CTRL22
    audio_output_path: str | None = None,  # MK-CTRL23
    audio_manifest_path: str | None = None,  # MK-CTRL23
    audio_duration_sec: float | None = None,  # MK-CTRL23
    audio_engine: str | None = None,  # MK-CTRL23
    audio_skipped: bool = False,  # MK-CTRL23
    episode_output_path: str | None = None,  # MK-CTRL24
    episode_manifest_path: str | None = None,  # MK-CTRL24
    episode_duration_sec: float | None = None,  # MK-CTRL24
    episode_scene_count: int | None = None,  # MK-CTRL24
) -> dict[str, Any]:
    """Evaluate artifact acceptance after subprocess execution.

    MK-CTRL18 — Artifact acceptance gate.
    MK-CTRL20 — Updated to accept frame artifacts for generate_frames.
    MK-CTRL21 — Updated to accept scene artifacts for assemble_scene.
    MK-CTRL22 — Updated to accept QA report artifacts for qa_review.
    MK-CTRL23 — Updated to accept audio artifacts for attach_audio.
    MK-CTRL24 — Updated to accept episode artifacts for render_episode.

    Args:
        returncode: Subprocess return code.
        subprocess_invoked: Whether subprocess was invoked.
        frame_manifest_path: Path to frame manifest file (MK-CTRL20).
        frame_count: Number of frames generated (MK-CTRL20).
        output_exists: Whether output file exists.
        output_size_bytes: Size of output file in bytes.
        scene_output_path: Path to scene MP4 file (MK-CTRL21).
        scene_manifest_path: Path to scene manifest file (MK-CTRL21).
        scene_duration_sec: Scene duration in seconds (MK-CTRL21).
        scene_frame_count: Number of frames in scene (MK-CTRL21).
        qa_report_path: Path to QA report file (MK-CTRL22).
        qa_verdict: QA verdict (pass/fail) (MK-CTRL22).
        qa_score: QA score (0-1) (MK-CTRL22).
        qa_reasons: List of QA failure reasons (MK-CTRL22).
        audio_output_path: Path to audio-attached MP4 file (MK-CTRL23).
        audio_manifest_path: Path to audio manifest file (MK-CTRL23).
        audio_duration_sec: Audio duration in seconds (MK-CTRL23).
        audio_engine: Audio engine used (MK-CTRL23).
        audio_skipped: Whether audio was skipped (MK-CTRL23).
        episode_output_path: Path to episode MP4 file (MK-CTRL24).
        episode_manifest_path: Path to episode manifest file (MK-CTRL24).
        episode_duration_sec: Episode duration in seconds (MK-CTRL24).
        episode_scene_count: Number of scenes in episode (MK-CTRL24).

    Returns:
        Dict with verdict fields:
        - artifact_status: "accepted" | "missing" | "empty" | "subprocess_failed" | "not_applicable"
        - artifact_accepted: bool
        - artifact_reason: str
    """
    # Case D — dry / blocked: subprocess not invoked
    if not subprocess_invoked:
        return {
            "artifact_status": "not_applicable",
            "artifact_accepted": False,
            "artifact_reason": "subprocess not invoked (dry or blocked mode)",
        }

    # Case C — subprocess failure
    if returncode != 0:
        return {
            "artifact_status": "subprocess_failed",
            "artifact_accepted": False,
            "artifact_reason": f"subprocess failed with returncode {returncode}",
        }

    # MK-CTRL22 — Case A: QA report acceptance (preferred for qa_review)
    if qa_report_path and output_exists:
        # Check QA verdict - pass requires verdict="pass" and score >= 0.70
        if qa_verdict == "pass" and qa_score is not None and qa_score >= 0.70:
            return {
                "artifact_status": "accepted",
                "artifact_accepted": True,
                "artifact_reason": f"QA report accepted: returncode=0, verdict=pass, score={qa_score}",
                "qa_verdict": qa_verdict,
                "qa_score": qa_score,
            }
        elif qa_verdict == "fail":
            # Subprocess succeeded but QA failed - this is a special case
            return {
                "artifact_status": "qa_failed",
                "artifact_accepted": False,
                "artifact_reason": f"QA verdict fail: score={qa_score}, reasons={qa_reasons or 'none'}",
                "qa_verdict": qa_verdict,
                "qa_score": qa_score,
                "qa_reasons": qa_reasons or [],
            }
        elif qa_score is not None and qa_score < 0.70:
            return {
                "artifact_status": "qa_failed",
                "artifact_accepted": False,
                "artifact_reason": f"QA score below threshold: score={qa_score} < 0.70",
                "qa_verdict": qa_verdict or "fail",
                "qa_score": qa_score,
            }

    # MK-CTRL22 — Case B: missing QA report
    if qa_report_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"QA report missing or does not exist (path={qa_report_path}, exists={output_exists})",
        }

    # MK-CTRL23 — Case A0: audio skipped (no dialogue) - check first, doesn't require audio_output_path
    if audio_skipped:
        return {
            "artifact_status": "skipped_no_audio",
            "artifact_accepted": True,
            "artifact_reason": "audio skipped: no dialogue",
            "audio_manifest_path": audio_manifest_path,
        }

    # MK-CTRL23 — Case A: audio artifact acceptance (preferred for attach_audio)
    if audio_output_path and output_exists:
        # Case A2: audio attached successfully
        if output_size_bytes and output_size_bytes > 0:
            return {
                "artifact_status": "accepted",
                "artifact_accepted": True,
                "artifact_reason": f"audio attached: duration={audio_duration_sec}, engine={audio_engine}",
                "audio_output_path": audio_output_path,
                "audio_manifest_path": audio_manifest_path,
                "audio_duration_sec": audio_duration_sec,
                "audio_engine": audio_engine,
            }
        # Case A3: empty audio output
        else:
            return {
                "artifact_status": "empty",
                "artifact_accepted": False,
                "artifact_reason": f"audio output is empty or zero bytes (path={audio_output_path}, size={output_size_bytes})",
            }

    # MK-CTRL23 — Case B: missing audio output
    if audio_output_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"audio output missing or does not exist (path={audio_output_path}, exists={output_exists})",
        }

    # MK-CTRL24 — Case A: episode artifact acceptance (preferred for render_episode)
    if episode_output_path and output_exists:
        if output_size_bytes and output_size_bytes > 0:
            return {
                "artifact_status": "accepted",
                "artifact_accepted": True,
                "artifact_reason": f"episode artifact accepted: returncode=0, duration={episode_duration_sec}, scene_count={episode_scene_count}",
                "episode_output_path": episode_output_path,
                "episode_manifest_path": episode_manifest_path,
                "episode_duration_sec": episode_duration_sec,
                "episode_scene_count": episode_scene_count,
            }
        else:
            return {
                "artifact_status": "empty",
                "artifact_accepted": False,
                "artifact_reason": f"episode output is empty or zero bytes (path={episode_output_path}, size={output_size_bytes})",
            }

    # MK-CTRL24 — Case B: missing episode output
    if episode_output_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"episode output missing or does not exist (path={episode_output_path}, exists={output_exists})",
        }

    # MK-CTRL21 — Case A: scene artifact acceptance (preferred for assemble_scene)
    if scene_output_path and output_exists:
        if scene_frame_count is not None and scene_frame_count > 0:
            return {
                "artifact_status": "accepted",
                "artifact_accepted": True,
                "artifact_reason": f"scene artifact accepted: returncode=0, scene MP4 exists, frame_count={scene_frame_count}",
            }
        elif scene_frame_count is not None and scene_frame_count == 0:
            return {
                "artifact_status": "empty",
                "artifact_accepted": False,
                "artifact_reason": f"scene artifact empty: scene_frame_count={scene_frame_count}",
            }

    # MK-CTRL21 — Case B: missing scene MP4
    if scene_output_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"scene MP4 missing or does not exist (path={scene_output_path}, exists={output_exists})",
        }

    # MK-CTRL20 — Case A: frame artifact acceptance (preferred for generate_frames)
    if frame_manifest_path and output_exists:
        if frame_count is not None and frame_count > 0:
            return {
                "artifact_status": "accepted",
                "artifact_accepted": True,
                "artifact_reason": f"frame artifact accepted: returncode=0, frame_manifest exists, frame_count={frame_count}",
            }
        elif frame_count is not None and frame_count == 0:
            return {
                "artifact_status": "empty",
                "artifact_accepted": False,
                "artifact_reason": f"frame artifact empty: frame_count={frame_count}",
            }

    # MK-CTRL20 — Case B: missing frame manifest
    if frame_manifest_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"frame_manifest missing or does not exist (path={frame_manifest_path}, exists={output_exists})",
        }

    # Legacy: Case B — missing episode artifact
    if episode_output_path and not output_exists:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": f"episode_output_path missing or does not exist (path={episode_output_path}, exists={output_exists})",
        }

    # MK-CTRL20 — Case B: no artifact at all (both frame_manifest and episode_output are None)
    if not frame_manifest_path and not episode_output_path and not scene_output_path:
        return {
            "artifact_status": "missing",
            "artifact_accepted": False,
            "artifact_reason": "no artifact found (no frame_manifest, scene_output, or episode_output)",
        }

    # Legacy: Case B — empty artifact
    if output_size_bytes is None or output_size_bytes == 0:
        return {
            "artifact_status": "empty",
            "artifact_accepted": False,
            "artifact_reason": f"output file is empty (size_bytes={output_size_bytes})",
        }

    # Legacy: Case A — success (episode artifact)
    if episode_output_path and output_exists:
        return {
            "artifact_status": "accepted",
            "artifact_accepted": True,
            "artifact_reason": f"episode_output accepted (path={episode_output_path}, size={output_size_bytes})",
        }

    # Fallback: no artifact found
    return {
        "artifact_status": "missing",
        "artifact_accepted": False,
        "artifact_reason": "no artifact found",
    }
