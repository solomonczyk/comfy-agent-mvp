"""KT-6 video manifest persistence."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class VideoManifest:
    """Manifest tracking a video pipeline run end-to-end."""

    def __init__(
        self,
        video_id: str,
        input_path: str,
        video_dir: Path,
    ):
        self.video_id = video_id
        self.input_path = input_path
        self.video_dir = str(video_dir)
        self.started_at = datetime.utcnow().isoformat()
        self.completed_at: str | None = None
        self.status = "running"
        self.probe: dict[str, Any] = {}
        self.extraction: dict[str, Any] = {}
        self.selection: dict[str, Any] = {}
        self.processing: dict[str, Any] = {}
        self.export: dict[str, Any] = {}
        self.qc: dict[str, Any] = {}
        self.error: str | None = None

    def set_probe(self, probe: dict[str, Any]) -> None:
        self.probe = probe

    def set_extraction(self, frames_dir: Path, frame_count: int, fps: float | None) -> None:
        self.extraction = {
            "frames_dir": str(frames_dir),
            "frame_count": frame_count,
            "fps": fps,
            "completed_at": datetime.utcnow().isoformat(),
        }

    def set_selection(self, selected: list[str], strategy: str) -> None:
        self.selection = {
            "strategy": strategy,
            "selected_count": len(selected),
            "selected_frames": selected,
        }

    def set_processing(
        self,
        processed_dir: Path,
        processed_count: int,
        processor: str,
        per_frame: list[dict[str, Any]] | None = None,
        prompt: str | None = None,
        recipe: dict[str, Any] | None = None,
    ) -> None:
        self.processing = {
            "processed_dir": str(processed_dir),
            "processed_count": processed_count,
            "processor": processor,
            "prompt": prompt,
            "recipe": recipe,
            "per_frame": per_frame or [],
            "completed_at": datetime.utcnow().isoformat(),
        }

    def set_export(self, export_path: Path, fps: float) -> None:
        self.export = {
            "export_path": str(export_path),
            "fps": fps,
            "completed_at": datetime.utcnow().isoformat(),
        }

    def set_qc(self, qc_section: dict[str, Any]) -> None:
        """Attach a KT-8 QC summary (verdict, reasons, summary, report path).

        The full QC report lives in its own file at
        ``data/manifests/video_qc_{video_id}.json``. This hook stores a compact
        linkage inside the main manifest for traceability.
        """
        self.qc = qc_section

    def complete(self) -> None:
        self.completed_at = datetime.utcnow().isoformat()
        self.status = "completed"

    def fail(self, reason: str) -> None:
        self.completed_at = datetime.utcnow().isoformat()
        self.status = "failed"
        self.error = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "input_path": self.input_path,
            "video_dir": self.video_dir,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "probe": self.probe,
            "extraction": self.extraction,
            "selection": self.selection,
            "processing": self.processing,
            "export": self.export,
            "qc": self.qc,
            "error": self.error,
        }


class VideoManifestPersistence:
    """Saves and loads VideoManifest objects."""

    def __init__(self, manifests_dir: Path):
        self.manifests_dir = manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

    def save(self, manifest: VideoManifest) -> Path:
        path = self.manifests_dir / f"video_{manifest.video_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        return path
