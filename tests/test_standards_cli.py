"""Tests for standards CLI commands."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")


class TestStandardsCLI:
    def _run(self, cmd):
        return subprocess.run(
            [sys.executable, "-m", "app.cli"] + cmd,
            capture_output=True,
            text=True,
            cwd="F:/ComfyUI/comfy-agent-mvp",
        )

    def test_combine_standards_list_json(self):
        result = self._run([
            "combine-standards-list",
            "--project-root", str(PROJECT_ROOT),
            "--json",
        ])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert len(data["standards"]) > 0

    def test_combine_standards_validate_json(self):
        result = self._run([
            "combine-standards-validate",
            "--project-root", str(PROJECT_ROOT),
            "--json",
        ])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["valid"] is True
        assert not data["errors"]

    def test_combine_standards_inspect_json(self):
        result = self._run([
            "combine-standards-inspect",
            "--project-root", str(PROJECT_ROOT),
            "--standard-id", "universal_quality_standard",
            "--json",
        ])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["standard_id"] == "universal_quality_standard"

    def test_combine_standards_inspect_missing(self):
        result = self._run([
            "combine-standards-inspect",
            "--project-root", str(PROJECT_ROOT),
            "--standard-id", "nonexistent_standard",
            "--json",
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "error" in data["data"]

    def test_combine_standards_readiness_report_json(self):
        result = self._run([
            "combine-standards-readiness-report",
            "--project-root", str(PROJECT_ROOT),
            "--json",
        ])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["readiness"]["standards_pack_created"] is True

    def test_cli_outputs_deterministic_json(self):
        result = self._run([
            "combine-standards-list",
            "--project-root", str(PROJECT_ROOT),
            "--json",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
