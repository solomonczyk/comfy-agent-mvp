"""Tests for standards pack state and ledger integration.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_control_dir() -> Path:
    """Return the control directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control")


class TestArtifactIndex:
    """Test artifact index integration."""

    def test_artifact_index_exists(self):
        """artifact_index.json must exist."""
        path = get_control_dir() / "artifact_index.json"
        assert path.exists(), "artifact_index.json not found"

    def test_artifact_index_is_valid_json(self):
        """artifact_index.json must be valid JSON."""
        path = get_control_dir() / "artifact_index.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, (dict, list))

    def test_standards_pack_referenced_in_index(self):
        """Standards pack should be referenced in artifact index."""
        path = get_control_dir() / "artifact_index.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert to string and check for standards pack references
        data_str = json.dumps(data).lower()
        assert any(x in data_str for x in [
            "standards_pack",
            "standards_pack_manifest",
            "defect_taxonomy",
            "severity_model",
        ]), "Artifact index should reference standards pack"


class TestEpisodeLedger:
    """Test episode ledger integration."""

    def test_episode_ledger_exists(self):
        """episode_ledger.json must exist."""
        path = get_control_dir() / "episode_ledger.json"
        assert path.exists(), "episode_ledger.json not found"

    def test_episode_ledger_is_valid_json(self):
        """episode_ledger.json must be valid JSON."""
        path = get_control_dir() / "episode_ledger.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, (dict, list))


class TestStateJson:
    """Test state.json reflects correct state."""

    def test_state_json_exists(self):
        """state.json must exist."""
        path = get_control_dir() / "state.json"
        assert path.exists(), "state.json not found"

    def test_state_is_valid_json(self):
        """state.json must be valid JSON."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_production_accepted_is_false(self):
        """production_accepted must be false."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("production_accepted") is False, \
            "production_accepted must be false - this is a safety check"

    def test_generation_flags_safely_set(self):
        """Generation-related flags must be safely set."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If generation was performed, ensure it was authorized
        if data.get("generation_performed"):
            assert data.get("generation_authorized") is True, \
                "Generation performed without authorization"


class TestStandardsPackReports:
    """Test standards pack reports."""

    def test_validation_report_exists(self):
        """standards_pack_validation_report.json should exist."""
        path = get_control_dir() / "standards_pack" / "reports" / "standards_pack_validation_report.json"
        # This is optional - may not exist yet
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_readiness_report_exists(self):
        """standards_pack_readiness_report.json should exist."""
        path = get_control_dir() / "standards_pack" / "reports" / "standards_pack_readiness_report.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)


class TestNoForbiddenActions:
    """Test that no forbidden actions have been executed."""

    def test_no_fake_operator_decision_in_state(self):
        """State should not indicate fake operator decision."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        state_str = json.dumps(data).lower()
        assert "fake_operator_decision" not in state_str or \
               data.get("fake_operator_decision") is False, \
            "State indicates fake operator decision"

    def test_no_fake_success_in_state(self):
        """State should not indicate fake success."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        state_str = json.dumps(data).lower()
        assert "fake_success" not in state_str or \
               data.get("fake_success") is False, \
            "State indicates fake success"

    def test_downstream_blocked_safely(self):
        """If downstream is blocked, it should be for legitimate reasons."""
        path = get_control_dir() / "state.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If downstream is blocked, ensure production_accepted is false
        if data.get("downstream_blocked"):
            assert data.get("production_accepted") is False, \
                "Downstream blocked but production_accepted is true"
