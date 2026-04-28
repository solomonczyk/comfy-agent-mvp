"""KT-6 minimal frame processor.

First usable local processing step: applies a deterministic PIL-based
enhancement (autocontrast + mild sharpen) to selected frames. Intentionally
minimal — no SDXL, no judge, no QC heuristics. This proves the wiring of the
pipeline end-to-end; richer processors can be swapped in later.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


def process_frame(src: Path, dst: Path) -> None:
    """Apply a minimal visible transformation and write to dst.

    - Autocontrast: normalizes histogram.
    - Mild sharpen (factor=1.3): small but visible.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        rgb = img.convert("RGB")
        ac = ImageOps.autocontrast(rgb, cutoff=1)
        sharpened = ImageEnhance.Sharpness(ac).enhance(1.3)
        sharpened.save(dst, format="PNG")


def process_frames_sequential(
    selected_paths: list[Path],
    processed_dir: Path,
) -> list[Path]:
    """Process the given frames in order, writing them contiguously into
    processed_dir as frame_000001.png, frame_000002.png, ...

    Returns the list of written destination paths.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, src in enumerate(selected_paths, start=1):
        dst = processed_dir / f"frame_{i:06d}.png"
        process_frame(src, dst)
        written.append(dst)
    return written
