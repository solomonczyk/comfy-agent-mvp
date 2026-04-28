"""MK-E2 — Frame assembler.

Assembles a list of frame PNG files into an MP4 video using ffmpeg.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .exceptions import FrameAssembleError


log = logging.getLogger(__name__)


class FrameAssembler:
    def __init__(self, output_dir: Path | str = "output/scenes") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble(
        self,
        scene_id: str,
        frame_paths: list[Path],
        fps: int,
        aspect_ratio: str = "4:3",
    ) -> Path:
        if not frame_paths:
            raise FrameAssembleError("frame_paths is empty")

        for p in frame_paths:
            if not p.exists():
                raise FrameAssembleError(f"Frame not found: {p}")

        # Sort by filename
        sorted_paths = sorted(frame_paths, key=lambda p: p.name)

        # Validate frames and check aspect ratio using cv2
        import cv2
        valid_paths: list[Path] = []
        first_shape: tuple[int, int] | None = None
        for frame_path in sorted_paths:
            frame = cv2.imread(str(frame_path))
            if frame is None:
                log.warning(f"Failed to read frame, skipping: {frame_path}")
                continue
            valid_paths.append(frame_path)
            if first_shape is None:
                first_shape = frame.shape[:2]  # (height, width)

        if not valid_paths:
            raise FrameAssembleError("No valid frames written to video")

        height, width = first_shape

        _ASPECT_RATIO_MAP: dict[str, tuple[int, int]] = {
            "4:3": (4, 3),
            "16:9": (16, 9),
            "9:16": (9, 16),
            "1:1": (1, 1),
            "3:2": (3, 2),
        }
        if aspect_ratio in _ASPECT_RATIO_MAP:
            ew, eh = _ASPECT_RATIO_MAP[aspect_ratio]
            expected_r = ew / eh
        else:
            parts = aspect_ratio.split(":")
            expected_r = float(parts[0]) / float(parts[1]) if len(parts) == 2 else 0.0
        actual_r = width / height
        if expected_r != 0.0 and abs(expected_r - actual_r) > 0.05:
            log.warning(
                f"Aspect ratio mismatch: expected {aspect_ratio} ({expected_r:.3f}), "
                f"got {width}x{height} ({actual_r:.3f}). Continuing with actual dimensions."
            )

        output_path = self.output_dir / f"{scene_id}.mp4"

        # Stage frames as frame_%04d.png in a temp dir for ffmpeg
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for idx, src in enumerate(valid_paths):
                dst = tmp_dir / f"frame_{idx:04d}.png"
                shutil.copy2(src, dst)

            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(tmp_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
            log.info(f"[FFMPEG] {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise FrameAssembleError(f"ffmpeg failed: {result.stderr}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FrameAssembleError(f"Output file empty or missing: {output_path}")

        log.info(f"Assembled {output_path}: {len(valid_paths)} frames, {output_path.stat().st_size / (1024*1024):.2f} MB")
        return output_path
