"""Scene audio mux layer.

Muxes a WAV audio file into a per-scene MP4 using ffmpeg subprocess.

ffmpeg command:
    ffmpeg -y -i <video> -i <audio> -c:v copy -c:a aac -shortest <output>

Rules:
- Missing video -> RuntimeError
- Missing audio -> RuntimeError
- ffmpeg non-zero exit -> RuntimeError with stderr
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class SceneAudioMuxer:
    """Muxes audio WAV into a scene MP4 using ffmpeg."""

    def mux(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Mux audio into video.

        Args:
            video_path: Path to source MP4.
            audio_path: Path to source WAV.
            output_path: Path for the output MP4 with audio.

        Returns:
            output_path after successful mux.

        Raises:
            RuntimeError: If inputs are missing or ffmpeg fails.
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_path = Path(output_path)

        if not video_path.exists():
            raise RuntimeError(f"[mux] video not found: {video_path}")
        if not audio_path.exists():
            raise RuntimeError(f"[mux] audio not found: {audio_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        log.info(f"[mux] {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"[mux] ffmpeg failed for scene video '{video_path.name}': {result.stderr}"
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"[mux] output file empty or missing: {output_path}")

        log.info(f"[mux] muxed -> {output_path}")
        return output_path
