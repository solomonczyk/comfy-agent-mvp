"""KT-6 frame extraction and assembly via ffmpeg subprocess.

Thin, minimal wrappers around ffmpeg. Does not attempt any smart handling —
the pipeline stays deterministic and debuggable.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _ensure_ffmpeg() -> None:
    """Raise a clear error if ffmpeg is not available on PATH."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found on PATH. KT-6 video pipeline requires ffmpeg."
        )
    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "ffprobe not found on PATH. KT-6 video pipeline requires ffprobe."
        )


def probe_video(input_path: Path) -> dict[str, Any]:
    """Return basic video metadata via ffprobe (duration, fps, frame count, dims)."""
    _ensure_ffmpeg()
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_streams",
        "-show_format",
        "-of", "json",
        str(input_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}

    # Parse r_frame_rate "num/den"
    r_rate = stream.get("r_frame_rate", "0/1")
    try:
        num, den = r_rate.split("/")
        fps = float(num) / float(den) if float(den) else 0.0
    except Exception:
        fps = 0.0

    duration = float(fmt.get("duration", 0.0) or 0.0)
    nb_frames_raw = stream.get("nb_frames")
    try:
        nb_frames = int(nb_frames_raw) if nb_frames_raw else int(round(fps * duration))
    except Exception:
        nb_frames = 0

    return {
        "duration_s": duration,
        "fps": fps,
        "frame_count": nb_frames,
        "width": stream.get("width"),
        "height": stream.get("height"),
        "codec": stream.get("codec_name"),
    }


def extract_frames(input_path: Path, frames_dir: Path, fps: float | None = None) -> int:
    """Extract all frames from input_path into frames_dir as PNG.

    Frames are named frame_000001.png, frame_000002.png, ... (6-digit padding).
    If `fps` is provided, ffmpeg resamples to that rate; otherwise the
    source fps is preserved.

    Returns the count of frames extracted.
    """
    _ensure_ffmpeg()
    frames_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = ["ffmpeg", "-y", "-i", str(input_path)]
    if fps is not None and fps > 0:
        cmd += ["-vf", f"fps={fps}"]
    cmd += ["-start_number", "1", str(frames_dir / "frame_%06d.png")]

    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return len(sorted(frames_dir.glob("frame_*.png")))


def assemble_frames(frames_dir: Path, output_path: Path, fps: float = 24.0) -> Path:
    """Assemble a contiguous sequence frame_000001.png, frame_000002.png... into a video.

    The frames in `frames_dir` MUST be contiguously numbered starting from 1
    (e.g. frame_000001.png, frame_000002.png, ...). Returns output_path on success.
    """
    _ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(fps),
        "-start_number", "1",
        "-i", str(frames_dir / "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path
