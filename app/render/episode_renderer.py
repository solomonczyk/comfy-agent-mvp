"""MK-E3 — Episode renderer.

Concatenates per-scene MP4 files into a final episode MP4 using ffmpeg concat demuxer.
Preserves audio streams when present.
"""
from __future__ import annotations

import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path

from .exceptions import EpisodeRenderError

log = logging.getLogger(__name__)


class EpisodeRenderer:
    def __init__(self, output_dir: Path | str = "output/episodes") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, episode_title: str, scene_mp4s: list[Path]) -> Path:
        if not scene_mp4s:
            raise EpisodeRenderError("scene_mp4s is empty")

        for p in scene_mp4s:
            if not p.exists():
                raise EpisodeRenderError(f"Scene MP4 not found: {p}")

        sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", episode_title)
        sanitized = sanitized.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{sanitized}_{timestamp}.mp4"

        # Build ffmpeg concat list
        concat_list_path = self.output_dir / f"_concat_{timestamp}.txt"
        lines = [f"file '{p.resolve()}'" for p in scene_mp4s]
        concat_list_path.write_text("\n".join(lines), encoding="utf-8")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(output_path),
        ]
        log.info(f"[FFMPEG] {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        concat_list_path.unlink(missing_ok=True)

        if result.returncode != 0:
            raise EpisodeRenderError(
                f"ffmpeg concat failed: {result.stderr}"
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise EpisodeRenderError(f"Output file empty or missing: {output_path}")

        log.info(f"Episode rendered -> {output_path}")
        return output_path
