"""Tests for MK-CTRL17 — Artifact parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.control.artifact_parser import evaluate_artifact_acceptance, parse_generation_artifacts


# ── Test 1 — parse stdout with episode path ───────────────────────────────

def test_parse_stdout_with_episode_path(tmp_path: Path) -> None:
    """Parse stdout with episode path should extract episode_output_path."""
    stdout = "Episode saved: output\\episodes\\test.mp4"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["episode_output_path"] is not None
    assert "test.mp4" in result["episode_output_path"]
    assert result["manifest_path"] is None
    assert result["output_exists"] is False
    assert result["output_size_bytes"] is None


# ── Test 2 — parse stdout with manifest path ─────────────────────────────

def test_parse_stdout_with_manifest_path(tmp_path: Path) -> None:
    """Parse stdout with manifest path should extract manifest_path."""
    stdout = "Manifest saved: output\\manifest.json"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["manifest_path"] is not None
    assert "manifest.json" in result["manifest_path"]
    assert result["episode_output_path"] is None
    assert result["output_exists"] is False
    assert result["output_size_bytes"] is None


# ── Test 3 — parse both paths from real-like stdout ───────────────────────

def test_parse_both_paths_from_real_stdout(tmp_path: Path) -> None:
    """Parse both paths from real-like stdout should extract both fields."""
    stdout = """Some output
Manifest saved: output\\manifest.json
More output
Episode saved: output\\episodes\\CTRL16_One_Shot_Proof_20260425_175656.mp4
End output"""
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["manifest_path"] is not None
    assert "manifest.json" in result["manifest_path"]
    assert result["episode_output_path"] is not None
    assert "CTRL16_One_Shot_Proof" in result["episode_output_path"]


# ── Test 4 — file existence and size verification ─────────────────────────

def test_file_existence_and_size_verification(tmp_path: Path) -> None:
    """Verify output file existence and size when file exists."""
    # Create a fake mp4 file
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes
    
    stdout = f"Episode saved: output\\episodes\\test.mp4"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["output_exists"] is True
    assert result["output_size_bytes"] == 1800
    assert result["episode_output_path"] is not None


# ── Test 5 — missing output file is not fatal ────────────────────────────

def test_missing_output_file_not_fatal(tmp_path: Path) -> None:
    """Missing output file should not be fatal, output_exists should be false."""
    stdout = "Episode saved: output\\episodes\\nonexistent.mp4"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["output_exists"] is False
    assert result["output_size_bytes"] is None
    assert result["episode_output_path"] is not None


# ── Test 6 — resolve relative paths correctly ─────────────────────────────

def test_resolve_relative_paths_correctly(tmp_path: Path) -> None:
    """Relative paths should be resolved relative to cwd."""
    stdout = "Episode saved: output\\episodes\\test.mp4"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["episode_output_path"] is not None
    # Should be an absolute path
    assert Path(result["episode_output_path"]).is_absolute()
    # Should contain the tmp_path
    assert str(tmp_path) in result["episode_output_path"]


# ── Test 7 — handle empty stdout ─────────────────────────────────────────

def test_handle_empty_stdout(tmp_path: Path) -> None:
    """Empty stdout should return None for all artifact fields."""
    result = parse_generation_artifacts("", cwd=tmp_path)
    
    assert result["manifest_path"] is None
    assert result["episode_output_path"] is None
    assert result["output_exists"] is False
    assert result["output_size_bytes"] is None


# ── Test 8 — handle stdout with no artifact lines ────────────────────────

def test_handle_stdout_with_no_artifact_lines(tmp_path: Path) -> None:
    """Stdout with no artifact lines should return None for artifact fields."""
    stdout = "Some random output\nNo artifact lines here\n"
    result = parse_generation_artifacts(stdout, cwd=tmp_path)
    
    assert result["manifest_path"] is None
    assert result["episode_output_path"] is None
    assert result["output_exists"] is False
    assert result["output_size_bytes"] is None


# ── MK-CTRL18 Tests — Artifact Acceptance Gate ─────────────────────────────


# ── Test 1 — returncode 0 + existing mp4 > 0 bytes is accepted ────────────

def test_returncode_zero_existing_mp4_accepted(tmp_path: Path) -> None:
    """returncode 0 + existing mp4 > 0 bytes should be accepted."""
    # Create a fake mp4 file
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    fake_mp4 = episodes_dir / "test.mp4"
    fake_mp4.write_bytes(b"fake video content" * 100)  # 1800 bytes

    stdout = "Episode saved: output\\episodes\\test.mp4"
    artifacts = parse_generation_artifacts(stdout, cwd=tmp_path)
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        episode_output_path=artifacts["episode_output_path"],
        output_exists=artifacts["output_exists"],
        output_size_bytes=artifacts["output_size_bytes"],
    )
    
    assert verdict["artifact_status"] == "accepted"
    assert verdict["artifact_accepted"] is True
    assert "accepted" in verdict["artifact_reason"]  # MK-CTRL21R — Accept "episode_output accepted" format


# ── Test 2 — returncode 0 + missing mp4 is failure ────────────────────────

def test_returncode_zero_missing_mp4_failure(tmp_path: Path) -> None:
    """returncode 0 + missing mp4 should be failure."""
    stdout = "Episode saved: output\\episodes\\missing.mp4"
    artifacts = parse_generation_artifacts(stdout, cwd=tmp_path)
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        episode_output_path=artifacts["episode_output_path"],
        output_exists=artifacts["output_exists"],
        output_size_bytes=artifacts["output_size_bytes"],
    )
    
    assert verdict["artifact_status"] == "missing"
    assert verdict["artifact_accepted"] is False
    assert "missing or does not exist" in verdict["artifact_reason"]


# ── Test 3 — returncode 0 + empty mp4 is failure ─────────────────────────

def test_returncode_zero_empty_mp4_failure(tmp_path: Path) -> None:
    """returncode 0 + empty mp4 should be failure."""
    # Create an empty mp4 file
    episodes_dir = tmp_path / "output" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    empty_mp4 = episodes_dir / "empty.mp4"
    empty_mp4.write_bytes(b"")

    stdout = "Episode saved: output\\episodes\\empty.mp4"
    artifacts = parse_generation_artifacts(stdout, cwd=tmp_path)
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=True,
        episode_output_path=artifacts["episode_output_path"],
        output_exists=artifacts["output_exists"],
        output_size_bytes=artifacts["output_size_bytes"],
    )
    
    assert verdict["artifact_status"] == "empty"
    assert verdict["artifact_accepted"] is False
    assert "empty" in verdict["artifact_reason"]


# ── Test 4 — returncode 1 is subprocess_failed ───────────────────────────

def test_returncode_one_subprocess_failed() -> None:
    """returncode 1 should be subprocess_failed."""
    verdict = evaluate_artifact_acceptance(
        returncode=1,
        subprocess_invoked=True,
        episode_output_path=None,
        output_exists=False,
        output_size_bytes=None,
    )
    
    assert verdict["artifact_status"] == "subprocess_failed"
    assert verdict["artifact_accepted"] is False
    assert "returncode 1" in verdict["artifact_reason"]


# ── Test 5 — dry command_ready unaffected ────────────────────────────────

def test_dry_command_ready_unaffected() -> None:
    """Dry command_ready should have not_applicable artifact status."""
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=False,
        episode_output_path=None,
        output_exists=False,
        output_size_bytes=None,
    )
    
    assert verdict["artifact_status"] == "not_applicable"
    assert verdict["artifact_accepted"] is False
    assert "not invoked" in verdict["artifact_reason"]


# ── Test 6 — kill switch blocked unaffected ─────────────────────────────

def test_kill_switch_blocked_unaffected() -> None:
    """Kill switch blocked should have not_applicable artifact status."""
    verdict = evaluate_artifact_acceptance(
        returncode=0,
        subprocess_invoked=False,
        episode_output_path=None,
        output_exists=False,
        output_size_bytes=None,
    )
    
    assert verdict["artifact_status"] == "not_applicable"
    assert verdict["artifact_accepted"] is False
