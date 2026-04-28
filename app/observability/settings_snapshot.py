"""MK-OBS2 — Observed settings snapshot writer.

Persists final observed generation settings to output/control/{episode_id}_{shot_id}_observed_settings.json
before ComfyUI submission.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


class ObservedSettingsSnapshotWriter:
    """Writes observed settings snapshots to disk.

    Writes human-readable JSON to output/control/{episode_id}_{shot_id}_observed_settings.json
    with atomic file operations (temp file + replace).
    """

    def __init__(self, project_root: Path | str) -> None:
        """Initialize snapshot writer.

        Args:
            project_root: Root directory for resolving output paths.
        """
        self.project_root = Path(project_root)

    def path_for(self, episode_id: str, shot_id: str) -> Path:
        """Get the output path for a given episode and shot.

        Args:
            episode_id: Episode identifier.
            shot_id: Shot identifier.

        Returns:
            Path to output/control/{episode_id}_{shot_id}_observed_settings.json
        """
        output_dir = self.project_root / "output" / "control"
        filename = f"{episode_id}_{shot_id}_observed_settings.json"
        return output_dir / filename

    def write(self, episode_id: str, shot_id: str, settings: dict) -> Path:
        """Write observed settings snapshot to disk.

        Args:
            episode_id: Episode identifier.
            shot_id: Shot identifier.
            settings: Settings dict to write (will not be mutated).

        Returns:
            Path to the written file.

        Raises:
            ValueError: If episode_id or shot_id is empty.
            OSError: If file write fails.
        """
        if not episode_id:
            raise ValueError("episode_id cannot be empty")
        if not shot_id:
            raise ValueError("shot_id cannot be empty")

        output_path = self.path_for(episode_id, shot_id)

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare wrapped output
        output_data = {"observed_settings": settings.copy()}

        # Atomic write: temp file + replace
        temp_path = output_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            # Atomic replace
            temp_path.replace(output_path)
        except Exception:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise

        return output_path
