"""Tests for standards pack CLI commands.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = "data/rc2_multishot1_ep01"


class TestStandardsListCommand:
    """Test combine-standards-list CLI command."""

    def test_standards_list_command_exists(self):
        """CLI must have combine-standards-list command."""
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-standards-list", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command not found: {result.stderr}"
        assert "standards" in result.stdout.lower()

    def test_standards_list_outputs_json(self):
        """combine-standards-list --json must output valid JSON."""
        result = subprocess.run(
            [
                sys.executable, "-m", "app.cli",
                "combine-standards-list",
                "--project-root", PROJECT_ROOT,
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data.get("status") == "ok"
        assert "standards" in data
        assert isinstance(data["standards"], list)


class TestStandardsValidateCommand:
    """Test combine-standards-validate CLI command."""

    def test_standards_validate_command_exists(self):
        """CLI must have combine-standards-validate command."""
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-standards-validate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command not found: {result.stderr}"

    def test_standards_validate_outputs_json(self):
        """combine-standards-validate --json must output valid JSON."""
        result = subprocess.run(
            [
                sys.executable, "-m", "app.cli",
                "combine-standards-validate",
                "--project-root", PROJECT_ROOT,
                "--json",
            ],
            capture_output=True,
            text=True,
        )

        # Should return 0 or 1, not crash
        assert result.returncode in (0, 1), f"Command crashed: {result.stderr}"

        data = json.loads(result.stdout)
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data


class TestStandardsInspectCommand:
    """Test combine-standards-inspect CLI command."""

    def test_standards_inspect_command_exists(self):
        """CLI must have combine-standards-inspect command."""
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-standards-inspect", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command not found: {result.stderr}"

    def test_standards_inspect_outputs_json(self):
        """combine-standards-inspect --json must output valid JSON."""
        result = subprocess.run(
            [
                sys.executable, "-m", "app.cli",
                "combine-standards-inspect",
                "--project-root", PROJECT_ROOT,
                "--standard-id", "defect_taxonomy",
                "--json",
            ],
            capture_output=True,
            text=True,
        )

        # May return 0 or 1 depending on if standard exists
        assert result.returncode in (0, 1), f"Command crashed: {result.stderr}"

        data = json.loads(result.stdout)
        assert "standard_id" in data


class TestStandardsReadinessCommand:
    """Test combine-standards-readiness-report CLI command."""

    def test_standards_readiness_command_exists(self):
        """CLI must have combine-standards-readiness-report command."""
        result = subprocess.run(
            [sys.executable, "-m", "app.cli", "combine-standards-readiness-report", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command not found: {result.stderr}"

    def test_standards_readiness_outputs_json(self):
        """combine-standards-readiness-report --json must output valid JSON."""
        result = subprocess.run(
            [
                sys.executable, "-m", "app.cli",
                "combine-standards-readiness-report",
                "--project-root", PROJECT_ROOT,
                "--json",
            ],
            capture_output=True,
            text=True,
        )

        # Should not crash
        assert result.returncode in (0, 1), f"Command crashed: {result.stderr}"

        # Output should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, dict)


class TestCLIJsonOutput:
    """Test that CLI commands produce deterministic JSON output."""

    def test_standards_list_deterministic(self):
        """Running list twice should produce same structure."""
        results = []
        for _ in range(2):
            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-standards-list",
                    "--project-root", PROJECT_ROOT,
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            results.append(json.loads(result.stdout))

        # Same number of standards
        assert len(results[0]["standards"]) == len(results[1]["standards"])

    def test_standards_validate_deterministic(self):
        """Running validate twice should produce same valid flag."""
        results = []
        for _ in range(2):
            result = subprocess.run(
                [
                    sys.executable, "-m", "app.cli",
                    "combine-standards-validate",
                    "--project-root", PROJECT_ROOT,
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode in (0, 1)
            results.append(json.loads(result.stdout))

        # Same validity
        assert results[0]["valid"] == results[1]["valid"]
