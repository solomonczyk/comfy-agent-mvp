"""MK-CTRL19 — Shot state persistence.

Stores shot lifecycle state in JSON files under output/control/<episode_id>/<shot_id>/state.json.
This allows controlled state transitions after accepted artifacts.

RC-FLOW1E — Ledger is canonical state source. Persisted state file is a derived mirror/cache.
When loading state, check ledger for latest state_transition and use it if newer than persisted state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ShotState:
    """Persisted shot state.
    
    MK-CTRL37R — Added typed artifact paths for proper artifact handoff between actions.
    Each action stores its output artifact in the appropriate field, and subsequent actions
    read from the correct field based on their input requirements.
    """
    episode_id: str
    shot_id: str
    current_state: str
    expected_next_action: str
    last_updated: str
    artifact_path: str | None = None  # Legacy field for backward compatibility
    brief_path: str | None = None  # MK-CTRL23
    transition_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # MK-CTRL37R — Typed artifact paths for proper handoff
    frame_manifest_path: str | None = None  # Output of generate_frames
    scene_mp4_path: str | None = None  # Output of assemble_scene, input to qa_review and attach_audio
    qa_report_path: str | None = None  # Output of qa_review
    audio_output_path: str | None = None  # Output of attach_audio, input to render_episode
    episode_output_path: str | None = None  # Output of render_episode

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "last_updated": self.last_updated,
            "artifact_path": self.artifact_path,
            "brief_path": self.brief_path,  # MK-CTRL23
            "transition_reason": self.transition_reason,
            "metadata": self.metadata,
            # MK-CTRL37R — Typed artifact paths
            "frame_manifest_path": self.frame_manifest_path,
            "scene_mp4_path": self.scene_mp4_path,
            "qa_report_path": self.qa_report_path,
            "audio_output_path": self.audio_output_path,
            "episode_output_path": self.episode_output_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShotState":
        return cls(
            episode_id=data.get("episode_id", ""),
            shot_id=data.get("shot_id", ""),
            current_state=data.get("current_state", ""),
            expected_next_action=data.get("expected_next_action", ""),
            last_updated=data.get("last_updated", ""),
            artifact_path=data.get("artifact_path"),
            brief_path=data.get("brief_path"),  # MK-CTRL23
            transition_reason=data.get("transition_reason"),
            metadata=data.get("metadata", {}),
            # MK-CTRL37R — Typed artifact paths
            frame_manifest_path=data.get("frame_manifest_path"),
            scene_mp4_path=data.get("scene_mp4_path"),
            qa_report_path=data.get("qa_report_path"),
            audio_output_path=data.get("audio_output_path"),
            episode_output_path=data.get("episode_output_path"),
        )


class ShotStateStorage:
    """Manages shot state persistence in JSON files.

    RC-FLOW1E — Ledger is canonical state source. When loading state, check ledger
    for latest state_transition and use it if newer than persisted state file.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.control_dir = self.root / "output" / "control"

    def _state_file_path(self, episode_id: str, shot_id: str) -> Path:
        """Get path to state file for a shot."""
        return self.control_dir / episode_id / f"{shot_id}_state.json"

    def _ledger_path(self, episode_id: str, shot_id: str) -> Path:
        """Get path to ledger file for a shot."""
        return self.control_dir / f"{episode_id}_{shot_id}_ledger.json"

    def _load_from_ledger(self, episode_id: str, shot_id: str) -> ShotState | None:
        """Load shot state from latest state_transition record in ledger.

        RC-FLOW1E — Ledger is canonical state source. Find the most recent
        state_transition event and construct ShotState from it.
        """
        ledger_path = self._ledger_path(episode_id, shot_id)
        if not ledger_path.exists():
            return None

        try:
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
            records = data.get("records", [])

            # Find the most recent state_transition record
            latest_transition = None
            latest_timestamp = ""
            for record in records:
                if record.get("event_type") == "state_transition":
                    timestamp = record.get("timestamp", "")
                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_transition = record

            if latest_transition is None:
                return None

            # Construct ShotState from state_transition record
            return ShotState(
                episode_id=episode_id,
                shot_id=shot_id,
                current_state=latest_transition.get("to_state") or latest_transition.get("current_state"),
                expected_next_action=latest_transition.get("expected_next_action"),
                last_updated=latest_timestamp,
                artifact_path=latest_transition.get("artifact_path"),
                brief_path=None,  # Not stored in ledger, will be preserved from persisted state
                transition_reason=latest_transition.get("reason"),
                metadata={},
                # Typed artifact paths - not available in ledger state_transition, will be None
                frame_manifest_path=None,
                scene_mp4_path=latest_transition.get("artifact_path") if latest_transition.get("to_state") == "scene_assembled" else None,
                qa_report_path=latest_transition.get("artifact_path") if latest_transition.get("to_state") == "qa_passed" else None,
                audio_output_path=latest_transition.get("artifact_path") if latest_transition.get("to_state") == "audio_attached" else None,
                episode_output_path=latest_transition.get("artifact_path") if latest_transition.get("to_state") == "episode_rendered" else None,
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def load(self, episode_id: str, shot_id: str) -> ShotState | None:
        """Load shot state from JSON file, with ledger as canonical source.

        RC-FLOW1E — Check ledger for latest state_transition. If ledger has a newer
        state than persisted state file, use ledger state and sync persisted state.
        """
        # Load from ledger (canonical source)
        ledger_state = self._load_from_ledger(episode_id, shot_id)

        # Load from persisted state file (cache/mirror)
        state_file = self._state_file_path(episode_id, shot_id)
        persisted_state = None
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                persisted_state = ShotState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                persisted_state = None

        # If ledger has state but persisted state doesn't, use ledger
        if ledger_state and not persisted_state:
            self.save(ledger_state)
            return ledger_state

        # If both exist, compare timestamps and use newer
        if ledger_state and persisted_state:
            if ledger_state.last_updated > persisted_state.last_updated:
                # Ledger is newer - sync persisted state and return ledger state
                # Preserve typed artifact paths from persisted state if not in ledger
                ledger_state.frame_manifest_path = ledger_state.frame_manifest_path or persisted_state.frame_manifest_path
                ledger_state.scene_mp4_path = ledger_state.scene_mp4_path or persisted_state.scene_mp4_path
                ledger_state.qa_report_path = ledger_state.qa_report_path or persisted_state.qa_report_path
                ledger_state.audio_output_path = ledger_state.audio_output_path or persisted_state.audio_output_path
                ledger_state.episode_output_path = ledger_state.episode_output_path or persisted_state.episode_output_path
                ledger_state.brief_path = ledger_state.brief_path or persisted_state.brief_path
                self.save(ledger_state)
                return ledger_state
            else:
                # Persisted state is newer or same - use it
                return persisted_state

        # If only persisted state exists, use it
        if persisted_state:
            return persisted_state

        # No state available
        return None

    def save(self, state: ShotState) -> None:
        """Save shot state to JSON file."""
        state_file = self._state_file_path(state.episode_id, state.shot_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def delete(self, episode_id: str, shot_id: str) -> None:
        """Delete shot state file."""
        state_file = self._state_file_path(episode_id, shot_id)
        if state_file.exists():
            state_file.unlink()
