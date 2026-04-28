"""ComfyUI submission data models."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubmitResult:
    prompt_id: str
    scene_id: str
    frame_paths: list[Path]
    elapsed_sec: float
    filename_prefix: str | None = None
