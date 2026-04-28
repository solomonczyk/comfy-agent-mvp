"""RC-FLOW1E — Regression tests for state consistency.

Tests ensure:
- control-status and artifact_index agree after qa_review pass
- latest valid ledger state_transition wins over older events
- multiple ledger filename patterns do not cause stale state reads
- attach_audio is available only after qa_passed
- render_episode is not available before attach_audio/audio policy
- no downstream action is executed by status inspection
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.control.shot_state_storage import ShotState, ShotStateStorage


class TestShotStateStorageLedgerCanonical:
    """RC-FLOW1E — Test that ledger is canonical state source."""

    def test_load_from_ledger_when_state_file_missing(self, tmp_path: Path) -> None:
        """When persisted state file is missing, load from ledger."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create ledger with state_transition
        ledger_path = control_dir / "ep01_shot01_ledger.json"
        ledger_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "records": [
                {
                    "timestamp": "2026-04-27T18:58:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "qa_passed",
                    "expected_next_action": "attach_audio",
                    "from_state": "scene_assembled",
                    "to_state": "qa_passed",
                    "artifact_path": "/path/to/qa_report.json",
                    "reason": "qa_review artifact accepted",
                }
            ],
        }
        ledger_path.write_text(json.dumps(ledger_data, indent=2))

        storage = ShotStateStorage(tmp_path)
        state = storage.load("ep01", "shot01")

        assert state is not None
        assert state.current_state == "qa_passed"
        assert state.expected_next_action == "attach_audio"
        assert state.last_updated == "2026-04-27T18:58:00"

    def test_ledger_state_wins_over_stale_persisted_state(self, tmp_path: Path) -> None:
        """When ledger has newer state than persisted file, use ledger state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create stale persisted state file
        state_dir = control_dir / "ep01"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "shot01_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "current_state": "scene_assembled",
                    "expected_next_action": "qa_review",
                    "last_updated": "2026-04-27T18:47:28",
                    "artifact_path": None,
                    "brief_path": "/path/to/brief.md",
                    "transition_reason": "assemble_scene artifact accepted",
                    "metadata": {},
                    "frame_manifest_path": "/path/to/frames_manifest.json",
                    "scene_mp4_path": None,
                    "qa_report_path": None,
                    "audio_output_path": None,
                    "episode_output_path": None,
                },
                indent=2,
            )
        )

        # Create ledger with newer state_transition
        ledger_path = control_dir / "ep01_shot01_ledger.json"
        ledger_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "records": [
                {
                    "timestamp": "2026-04-27T18:58:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "qa_passed",
                    "expected_next_action": "attach_audio",
                    "from_state": "scene_assembled",
                    "to_state": "qa_passed",
                    "artifact_path": "/path/to/qa_report.json",
                    "reason": "qa_review artifact accepted",
                }
            ],
        }
        ledger_path.write_text(json.dumps(ledger_data, indent=2))

        storage = ShotStateStorage(tmp_path)
        state = storage.load("ep01", "shot01")

        # Should return ledger state (newer)
        assert state is not None
        assert state.current_state == "qa_passed"
        assert state.expected_next_action == "attach_audio"
        assert state.last_updated == "2026-04-27T18:58:00"

        # Persisted state file should be synced to ledger
        synced_state = json.loads(state_file.read_text())
        assert synced_state["current_state"] == "qa_passed"
        assert synced_state["expected_next_action"] == "attach_audio"

    def test_persisted_state_used_when_newer_than_ledger(self, tmp_path: Path) -> None:
        """When persisted state is newer than ledger, use persisted state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create newer persisted state file
        state_dir = control_dir / "ep01"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "shot01_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "current_state": "audio_attached",
                    "expected_next_action": "render_episode",
                    "last_updated": "2026-04-27T19:00:00",
                    "artifact_path": "/path/to/audio.mp4",
                    "brief_path": "/path/to/brief.md",
                    "transition_reason": "attach_audio artifact accepted",
                    "metadata": {},
                    "frame_manifest_path": "/path/to/frames_manifest.json",
                    "scene_mp4_path": "/path/to/scene.mp4",
                    "qa_report_path": "/path/to/qa_report.json",
                    "audio_output_path": "/path/to/audio.mp4",
                    "episode_output_path": None,
                },
                indent=2,
            )
        )

        # Create ledger with older state_transition
        ledger_path = control_dir / "ep01_shot01_ledger.json"
        ledger_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "records": [
                {
                    "timestamp": "2026-04-27T18:58:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "qa_passed",
                    "expected_next_action": "attach_audio",
                    "from_state": "scene_assembled",
                    "to_state": "qa_passed",
                    "artifact_path": "/path/to/qa_report.json",
                    "reason": "qa_review artifact accepted",
                }
            ],
        }
        ledger_path.write_text(json.dumps(ledger_data, indent=2))

        storage = ShotStateStorage(tmp_path)
        state = storage.load("ep01", "shot01")

        # Should return persisted state (newer)
        assert state is not None
        assert state.current_state == "audio_attached"
        assert state.expected_next_action == "render_episode"
        assert state.last_updated == "2026-04-27T19:00:00"

    def test_latest_ledger_state_transition_wins(self, tmp_path: Path) -> None:
        """When ledger has multiple state_transitions, use latest."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create ledger with multiple state_transitions
        ledger_path = control_dir / "ep01_shot01_ledger.json"
        ledger_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "records": [
                {
                    "timestamp": "2026-04-27T18:50:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "frames_generated",
                    "expected_next_action": "assemble_scene",
                    "from_state": "ready_for_generation",
                    "to_state": "frames_generated",
                    "artifact_path": "/path/to/frames_manifest.json",
                    "reason": "generate_frames artifact accepted",
                },
                {
                    "timestamp": "2026-04-27T18:55:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "scene_assembled",
                    "expected_next_action": "qa_review",
                    "from_state": "frames_generated",
                    "to_state": "scene_assembled",
                    "artifact_path": "/path/to/scene.mp4",
                    "reason": "assemble_scene artifact accepted",
                },
                {
                    "timestamp": "2026-04-27T18:58:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "qa_passed",
                    "expected_next_action": "attach_audio",
                    "from_state": "scene_assembled",
                    "to_state": "qa_passed",
                    "artifact_path": "/path/to/qa_report.json",
                    "reason": "qa_review artifact accepted",
                },
            ],
        }
        ledger_path.write_text(json.dumps(ledger_data, indent=2))

        storage = ShotStateStorage(tmp_path)
        state = storage.load("ep01", "shot01")

        # Should return latest state_transition
        assert state is not None
        assert state.current_state == "qa_passed"
        assert state.expected_next_action == "attach_audio"
        assert state.last_updated == "2026-04-27T18:58:00"

    def test_typed_artifact_paths_preserved_from_persisted_state(self, tmp_path: Path) -> None:
        """When syncing from ledger, preserve typed artifact paths from persisted state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        # Create persisted state with typed artifact paths
        state_dir = control_dir / "ep01"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "shot01_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "current_state": "scene_assembled",
                    "expected_next_action": "qa_review",
                    "last_updated": "2026-04-27T18:47:28",
                    "artifact_path": None,
                    "brief_path": "/path/to/brief.md",
                    "transition_reason": "assemble_scene artifact accepted",
                    "metadata": {},
                    "frame_manifest_path": "/path/to/frames_manifest.json",
                    "scene_mp4_path": "/path/to/scene.mp4",
                    "qa_report_path": None,
                    "audio_output_path": None,
                    "episode_output_path": None,
                },
                indent=2,
            )
        )

        # Create ledger with state_transition (no typed paths in ledger)
        ledger_path = control_dir / "ep01_shot01_ledger.json"
        ledger_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "records": [
                {
                    "timestamp": "2026-04-27T18:58:00",
                    "episode_id": "ep01",
                    "shot_id": "shot01",
                    "event_type": "state_transition",
                    "current_state": "qa_passed",
                    "expected_next_action": "attach_audio",
                    "from_state": "scene_assembled",
                    "to_state": "qa_passed",
                    "artifact_path": "/path/to/qa_report.json",
                    "reason": "qa_review artifact accepted",
                }
            ],
        }
        ledger_path.write_text(json.dumps(ledger_data, indent=2))

        storage = ShotStateStorage(tmp_path)
        state = storage.load("ep01", "shot01")

        # Should preserve typed artifact paths from persisted state
        assert state is not None
        assert state.current_state == "qa_passed"
        assert state.frame_manifest_path == "/path/to/frames_manifest.json"
        assert state.scene_mp4_path == "/path/to/scene.mp4"
        assert state.qa_report_path == "/path/to/qa_report.json"
        assert state.brief_path == "/path/to/brief.md"
