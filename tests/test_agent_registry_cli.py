"""Tests for Combine V2 Agent Registry CLI commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")

CLI_MODULE = "app.cli"
CLI_COMMANDS = [
    "combine-build-agent-registry",
    "combine-validate-agent-registry",
    "combine-build-agent-operator-review",
]


@pytest.mark.cli
class TestAgentRegistryCLI:
    """Tests for agent registry CLI commands using subprocess."""

    @pytest.mark.parametrize("command", CLI_COMMANDS)
    def test_cli_help_exit_code(self, command: str) -> None:
        """Verify each agent registry CLI command accepts --help and exits with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", CLI_MODULE, command, "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, (
            f"'{command} --help' failed with exit code {result.returncode}.\n"
            f"stderr: {result.stderr}"
        )

    def test_cli_build_command_registered(self) -> None:
        """Run combine-build-agent-registry --help and verify it shows help text."""
        result = subprocess.run(
            [sys.executable, "-m", CLI_MODULE, "combine-build-agent-registry", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "combine-build-agent-registry" in result.stdout
        assert "--project-root" in result.stdout

    def test_cli_validate_command_registered(self) -> None:
        """Run combine-validate-agent-registry --help and verify it shows help text."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                CLI_MODULE,
                "combine-validate-agent-registry",
                "--help",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "combine-validate-agent-registry" in result.stdout
        assert "--project-root" in result.stdout

    def test_cli_operator_review_command_registered(self) -> None:
        """Run combine-build-agent-operator-review --help and verify it shows help text."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                CLI_MODULE,
                "combine-build-agent-operator-review",
                "--help",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "combine-build-agent-operator-review" in result.stdout
        assert "--project-root" in result.stdout

    def test_cli_build_requires_project_root(self) -> None:
        """Verify combine-build-agent-registry without --project-root exits with an error."""
        result = subprocess.run(
            [sys.executable, "-m", CLI_MODULE, "combine-build-agent-registry"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode != 0, (
            "combine-build-agent-registry should fail when --project-root "
            "is not provided"
        )

    def test_cli_validate_requires_project_root(self) -> None:
        """Verify combine-validate-agent-registry without --project-root exits with an error."""
        result = subprocess.run(
            [sys.executable, "-m", CLI_MODULE, "combine-validate-agent-registry"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode != 0, (
            "combine-validate-agent-registry should fail when --project-root "
            "is not provided"
        )

    def test_cli_no_generation_in_help(self) -> None:
        """Verify help text for agent registry commands does not contain
        generation-related operations."""
        for command in CLI_COMMANDS:
            result = subprocess.run(
                [sys.executable, "-m", CLI_MODULE, command, "--help"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            stdout_lower = result.stdout.lower()
            assert "generation" not in stdout_lower, (
                f"Help for '{command}' should not mention 'generation'. "
                f"Found in: {result.stdout}"
            )
