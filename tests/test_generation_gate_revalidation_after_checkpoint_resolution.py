"""Tests for generation gate revalidation after checkpoint resolution.

RC-COMBINE-V2-94001-98000:
  - generation_not_executed
  - comfyui_submit_not_executed
  - state_transition_correct
  - production_accepted_false
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_artifacts(control_dir: Path, resolution_branch: str,
                      checkpoint_resolved: bool, artifacts: dict | None = None) -> None:
    """Create checkpoint resolution artifacts for testing gate revalidation."""
    data = artifacts or {}

    # checkpoint_resolution_decision.json
    (control_dir / "checkpoint_resolution_decision.json").write_text(json.dumps({
        "task_id": "RC-COMBINE-V2-94001-98000",
        "resolution_branch": resolution_branch,
        "missing_checkpoint": "checkpoint_sdxl_base",
        "checkpoint_resolved": checkpoint_resolved,
        "local_candidate_found": resolution_branch == "local_candidate_operator_review_required",
        "operator_review_required": resolution_branch == "local_candidate_operator_review_required",
        "acquisition_required": resolution_branch == "acquisition_required",
        "exact_match_available": resolution_branch == "exact_checkpoint_available",
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "fake_checkpoint_availability_created": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "timestamp": "2026-05-08T00:00:00",
    }))


@pytest.fixture
def project_root(tmp_path: Path) -> str:
    """Create a temporary project root for testing."""
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Test: revalidation after exact checkpoint available
# ---------------------------------------------------------------------------

    # checkpoint_local_inventory_report.json
    (control_dir / "checkpoint_local_inventory_report.json").write_text(json.dumps({
        "task_id": "RC-COMBINE-V2-94001-98000",
        "inventory_checked": True,
        "sdxl_compatible_found": [
            {"file_name": "sd_xl_base_1.0.safetensors", "detected_type": "sdxl"}
        ] if resolution_branch == "exact_checkpoint_available" else [],
        "total_valid_candidates": 1 if resolution_branch != "acquisition_required" else 0,
        "total_checkpoints_found": 1,
        "timestamp": "2026-05-08T00:00:00",
    }))

    # checkpoint_candidate_review_report.json
    (control_dir / "checkpoint_candidate_review_report.json").write_text(json.dumps({
        "task_id": "RC-COMBINE-V2-94001-98000",
        "candidate_assets_reviewed": True,
        "exact_match_available": resolution_branch == "exact_checkpoint_available",
        "substitution_candidate_available": resolution_branch == "local_candidate_operator_review_required",
        "no_candidates_found": resolution_branch == "acquisition_required",
        "requires_operator_review": resolution_branch == "local_candidate_operator_review_required",
        "timestamp": "2026-05-08T00:00:00",
    }))


# ---------------------------------------------------------------------------
# Test: revalidation after exact checkpoint available
# ---------------------------------------------------------------------------

def test_revalidation_after_exact_checkpoint(project_root: str) -> None:
    """When exact checkpoint was resolved, revalidation must show
    gate is no longer blocked by checkpoint."""
    control_dir = Path(project_root) / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    _create_artifacts(control_dir, "exact_checkpoint_available", True)

    from app.asset_resolution.checkpoint_resolution import revalidate_generation_gate

    result = revalidate_generation_gate(project_root)

    assert result["gate_status"] == "checkpoint_resolved_generation_ready"
    assert result["generation_authorized"] is False
    assert result["generation_gate_blocked"] is False
    assert result["checkpoint_resolved"] is True
    assert result["operator_review_required"] is False
    assert result["acquisition_required"] is False
    assert result["generation_performed"] is False
    assert result["comfyui_submit_executed"] is False
    assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: revalidation after local candidate found
# ---------------------------------------------------------------------------

def test_revalidation_after_local_candidate(project_root: str) -> None:
    """When a local candidate was found but requires review, revalidation
    must indicate the gate is still blocked pending operator review."""
    control_dir = Path(project_root) / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    _create_artifacts(control_dir, "local_candidate_operator_review_required", False)

    from app.asset_resolution.checkpoint_resolution import revalidate_generation_gate

    result = revalidate_generation_gate(project_root)

    assert result["gate_status"] == "checkpoint_candidate_found_operator_review_required"
    assert result["generation_authorized"] is False
    assert result["generation_gate_blocked"] is True
    assert result["checkpoint_resolved"] is False
    assert result["operator_review_required"] is True
    assert result["acquisition_required"] is False
    assert result["generation_performed"] is False
    assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: revalidation after acquisition required
# ---------------------------------------------------------------------------

def test_revalidation_after_acquisition_required(project_root: str) -> None:
    """When acquisition is required, revalidation must show gate is blocked."""
    control_dir = Path(project_root) / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    _create_artifacts(control_dir, "acquisition_required", False)

    from app.asset_resolution.checkpoint_resolution import revalidate_generation_gate

    result = revalidate_generation_gate(project_root)

    assert result["gate_status"] == "checkpoint_acquisition_required_gate_blocked"
    assert result["generation_authorized"] is False
    assert result["generation_gate_blocked"] is True
    assert result["checkpoint_resolved"] is False
    assert result["acquisition_required"] is True
    assert result["generation_performed"] is False
    assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: revalidation with no resolution artifacts
# ---------------------------------------------------------------------------

def test_revalidation_with_no_resolution_artifacts(project_root: str) -> None:
    """When no resolution artifacts exist, revalidation must return an error."""
    control_dir = Path(project_root) / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    # Do NOT create resolution artifacts

    from app.asset_resolution.checkpoint_resolution import revalidate_generation_gate

    result = revalidate_generation_gate(project_root)

    assert "error" in result
    assert result["generation_authorized"] is False
    assert result["generation_gate_blocked"] is True
    assert result["generation_performed"] is False
    assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: state_transition_correct from revalidation perspective
# ---------------------------------------------------------------------------

def test_revalidation_forbidden_flags(project_root: str) -> None:
    """Revalidation must set all forbidden state flags correctly for all branches."""
    from app.asset_resolution.checkpoint_resolution import revalidate_generation_gate

    for branch, resolved in [
        ("exact_checkpoint_available", True),
        ("local_candidate_operator_review_required", False),
        ("acquisition_required", False),
    ]:
        control_dir = Path(project_root) / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        _create_artifacts(control_dir, branch, resolved)

        result = revalidate_generation_gate(project_root)

        assert result["generation_performed"] is False, f"Branch {branch}"
        assert result["comfyui_submit_executed"] is False, f"Branch {branch}"
        assert result["retry_attempted"] is False, f"Branch {branch}"
        assert result["visual_qa_executed"] is False, f"Branch {branch}"
        assert result["preview_render_executed"] is False, f"Branch {branch}"
        assert result["assembly_executed"] is False, f"Branch {branch}"
        assert result["downstream_executed"] is False, f"Branch {branch}"
        assert result["production_accepted"] is False, f"Branch {branch}"
