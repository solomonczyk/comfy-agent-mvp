"""Tests for checkpoint asset resolution — core resolution logic.

RC-COMBINE-V2-94001-98000:
  - exact_checkpoint_available_branch
  - missing_checkpoint_acquisition_required_branch
  - artifact_index_updated
  - episode_ledger_updated
  - production_accepted_false
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, PropertyMock

import pytest

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_root(tmp_path: Path) -> str:
    """Create a minimal project root with blocker artifacts."""
    control_dir = tmp_path / "output" / "control"
    wf_assets_dir = control_dir / "workflow_assets"
    wf_assets_dir.mkdir(parents=True, exist_ok=True)

    # generation_gate_decision.json
    _write_json(control_dir / "generation_gate_decision.json", {
        "task_id": "RC-COMBINE-V2-86001-94000",
        "generation_gate_decision": "blocked_by_missing_assets",
        "generation_can_be_authorized": False,
        "reason": "Required assets not available; Active asset blocker: checkpoint_sdxl_base",
        "blockers": [
            {
                "type": "missing_required_assets",
                "detail": "Required assets missing: ['checkpoint_sdxl_base']",
            },
            {
                "type": "active_asset_blocker",
                "detail": "Asset blocker active for: checkpoint_sdxl_base",
                "blocker_id": "asset_blocker_2026-05-08",
                "missing_asset": "checkpoint_sdxl_base",
            },
        ],
        "asset_blocker_active": True,
    })

    # generation_runtime_blocker_report.json
    _write_json(control_dir / "generation_runtime_blocker_report.json", {
        "task_id": "RC-COMBINE-V2-86001-94000",
        "blocker_type": "generation_runtime_blocker",
        "decision": "blocked_by_missing_assets",
        "missing_asset": "checkpoint_sdxl_base",
    })

    # controlled_asset_acquisition_gate_packet.json
    _write_json(control_dir / "controlled_asset_acquisition_gate_packet.json", {
        "task_id": "RC-COMBINE-V2-86001-94000",
        "decision": "blocked_by_missing_assets",
        "missing_asset": "checkpoint_sdxl_base",
    })

    # asset_requirements.json
    _write_json(control_dir / "workflow_assets" / "asset_requirements.json", {
        "checkpoint_required": True,
        "required_checkpoints": ["checkpoint_sdxl_base"],
    })

    # asset_inventory.json
    _write_json(control_dir / "workflow_assets" / "asset_inventory.json", {
        "available_assets": [],
        "missing_assets": ["checkpoint_sdxl_base"],
    })

    # asset_resolution_plan.json
    _write_json(control_dir / "workflow_assets" / "asset_resolution_plan.json", {
        "missing_assets": ["checkpoint_sdxl_base"],
    })

    # asset_verification_report.json
    _write_json(control_dir / "workflow_assets" / "asset_verification_report.json", {
        "required_assets_available": False,
        "errors": ["checkpoint_sdxl_base"],
    })

    return str(tmp_path)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Test: exact_checkpoint_available_branch
# ---------------------------------------------------------------------------

def test_exact_checkpoint_available_branch(project_root: str) -> None:
    """When the exact SDXL checkpoint is found locally, resolution should
    select the exact_checkpoint_available branch without requiring
    operator review or acquisition."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
        evaluate_checkpoint_candidates,
        resolve_checkpoint_asset,
    )

    # We need to mock _find_comfyui_root and _scan_comfyui_checkpoints
    # to simulate finding the exact checkpoint
    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [
                {
                    "file_name": "sd_xl_base_1.0.safetensors",
                    "file_path": "/fake/comfyui/models/checkpoints/sd_xl_base_1.0.safetensors",
                    "file_size_bytes": 6_944_000_000,
                    "source": "/fake/comfyui/models/checkpoints",
                },
            ]

            inventory = scan_local_checkpoint_inventory(project_root)
            assert inventory["inventory_checked"] is True
            assert len(inventory["sdxl_compatible_found"]) == 1
            assert inventory["sdxl_exact_match_found"] is True
            assert inventory["total_valid_candidates"] == 1

            candidate_review = evaluate_checkpoint_candidates(inventory)
            assert candidate_review["exact_match_available"] is True
            assert candidate_review["requires_operator_review"] is False
            assert candidate_review["no_candidates_found"] is False

            # Full resolution should pick exact match branch
            result = resolve_checkpoint_asset(project_root)
            assert result["selected_branch"] == "exact_checkpoint_available"
            assert result["checkpoint_resolved"] is True
            assert result["local_candidate_found"] is False
            assert result["operator_review_required"] is False
            assert result["acquisition_required"] is False
            assert result["download_authorized"] is False
            assert result["download_performed"] is False
            assert result["install_authorized"] is False
            assert result["install_performed"] is False
            assert result["generation_performed"] is False
            assert result["comfyui_submit_executed"] is False
            assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: valid_local_candidate_branch
# ---------------------------------------------------------------------------

def test_valid_local_candidate_branch(project_root: str) -> None:
    """When a valid SDXL candidate exists but is not the exact expected
    checkpoint, the resolution should flag operator review required."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
        evaluate_checkpoint_candidates,
        resolve_checkpoint_asset,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            # Found SDXL checkpoint but not named sd_xl_base
            mock_scan.return_value = [
                {
                    "file_name": "sd_xl_turbo_1.0.safetensors",
                    "file_path": "/fake/comfyui/models/checkpoints/sd_xl_turbo_1.0.safetensors",
                    "file_size_bytes": 6_900_000_000,
                    "source": "/fake/comfyui/models/checkpoints",
                },
            ]

            inventory = scan_local_checkpoint_inventory(project_root)
            assert len(inventory["sdxl_compatible_found"]) == 1

            candidate_review = evaluate_checkpoint_candidates(inventory)
            assert candidate_review["exact_match_available"] is False
            assert candidate_review["substitution_candidate_available"] is True
            assert candidate_review["requires_operator_review"] is True

            result = resolve_checkpoint_asset(project_root)
            assert result["selected_branch"] == "local_candidate_operator_review_required"
            assert result["checkpoint_resolved"] is False
            assert result["local_candidate_found"] is True
            assert result["operator_review_required"] is True
            assert result["acquisition_required"] is False
            assert result["substitution_packet_created"] is True
            assert result["generation_performed"] is False
            assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: missing_checkpoint_acquisition_required_branch
# ---------------------------------------------------------------------------

def test_missing_checkpoint_acquisition_required_branch(project_root: str) -> None:
    """When no SDXL-compatible checkpoint is found locally, the resolution
    should select acquisition_required and create acquisition contracts."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
        evaluate_checkpoint_candidates,
        resolve_checkpoint_asset,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            # No checkpoints found at all
            mock_scan.return_value = []

            inventory = scan_local_checkpoint_inventory(project_root)
            assert inventory["total_checkpoints_found"] == 0

            candidate_review = evaluate_checkpoint_candidates(inventory)
            assert candidate_review["no_candidates_found"] is True
            assert candidate_review["exact_match_available"] is False
            assert candidate_review["substitution_candidate_available"] is False

            result = resolve_checkpoint_asset(project_root)
            assert result["selected_branch"] == "acquisition_required"
            assert result["checkpoint_resolved"] is False
            assert result["acquisition_required"] is True
            assert result["generation_performed"] is False
            assert result["production_accepted"] is False

            # Check acquisition contracts were created
            acq = result.get("acquisition_contracts_created", {})
            assert acq.get("source_allowlist_decision") is True
            assert acq.get("acquisition_execution_contract") is True
            assert acq.get("install_verification_contract") is True
            assert acq.get("acquisition_blocker_report") is True


# ---------------------------------------------------------------------------
# Test: artifact_index_updated
# ---------------------------------------------------------------------------

def test_artifact_index_updated(project_root: str) -> None:
    """After checkpoint resolution, artifact_index.json must contain
    the checkpoint resolution entries."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            resolve_checkpoint_asset(project_root)

    control_dir = Path(project_root) / "output" / "control"
    index_path = control_dir / "artifact_index.json"
    assert index_path.exists()

    index = json.loads(index_path.read_text())
    assert index.get("checkpoint_resolution_executed") is True
    assert index.get("checkpoint_resolution_task_id") == "RC-COMBINE-V2-94001-98000"
    assert index.get("checkpoint_resolved") is False
    assert index.get("generation_performed") is False
    assert index.get("comfyui_submit_executed") is False
    assert index.get("production_accepted") is False


# ---------------------------------------------------------------------------
# Test: episode_ledger_updated
# ---------------------------------------------------------------------------

def test_episode_ledger_updated(project_root: str) -> None:
    """After checkpoint resolution, episode_ledger.json must contain
    a checkpoint_asset_resolution_executed entry."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            resolve_checkpoint_asset(project_root)

    control_dir = Path(project_root) / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    assert ledger_path.exists()

    ledger = json.loads(ledger_path.read_text())
    assert isinstance(ledger, list)
    entries = [e for e in ledger if e.get("event") == "checkpoint_asset_resolution_executed"]
    assert len(entries) == 1

    entry = entries[0]
    assert entry["task_id"] == "RC-COMBINE-V2-94001-98000"
    assert entry["generation_performed"] is False
    assert entry["comfyui_submit_executed"] is False
    assert entry["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test: production_accepted_false
# ---------------------------------------------------------------------------

def test_production_accepted_false(project_root: str) -> None:
    """All resolution branches must set production_accepted=false."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            # Test all branches
            for checkpoints, expected_branch in [
                ([{
                    "file_name": "sd_xl_base_1.0.safetensors",
                    "file_size_bytes": 6_944_000_000,
                    "file_path": "/fake/a.safetensors",
                    "source": "/fake/checkpoints",
                }], "exact_checkpoint_available"),
                ([{
                    "file_name": "sd_xl_turbo_1.0.safetensors",
                    "file_size_bytes": 6_900_000_000,
                    "file_path": "/fake/b.safetensors",
                    "source": "/fake/checkpoints",
                }], "local_candidate_operator_review_required"),
                ([], "acquisition_required"),
            ]:
                mock_scan.return_value = checkpoints
                result = resolve_checkpoint_asset(project_root)
                assert result["selected_branch"] == expected_branch, (
                    f"Expected {expected_branch} but got {result['selected_branch']}"
                )
                assert result["production_accepted"] is False, (
                    f"production_accepted must be false for {expected_branch}"
                )


# ---------------------------------------------------------------------------
# Test: state_transition_correct
# ---------------------------------------------------------------------------

def test_state_transition_correct(project_root: str) -> None:
    """State transitions must be correct for each resolution branch."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            # Exact match → generation_operator_authorization_required
            mock_scan.return_value = [{
                "file_name": "sd_xl_base_1.0.safetensors",
                "file_size_bytes": 6_944_000_000,
                "file_path": "/fake/a.safetensors",
                "source": "/fake/checkpoints",
            }]
            result = resolve_checkpoint_asset(project_root)
            assert result["current_state"] == "generation_operator_authorization_required"
            assert result["next_allowed_action"] == "generation_operator_authorization_required"

            # Local candidate → controlled_checkpoint_acquisition_operator_review_required
            mock_scan.return_value = [{
                "file_name": "sd_xl_turbo_1.0.safetensors",
                "file_size_bytes": 6_900_000_000,
                "file_path": "/fake/b.safetensors",
                "source": "/fake/checkpoints",
            }]
            result = resolve_checkpoint_asset(project_root)
            assert result["current_state"] == "controlled_checkpoint_acquisition_operator_review_required"
            assert result["next_allowed_action"] == "controlled_checkpoint_acquisition_operator_review_required"

            # Missing → controlled_asset_acquisition_required
            mock_scan.return_value = []
            result = resolve_checkpoint_asset(project_root)
            assert result["current_state"] == "controlled_asset_acquisition_required"
            assert result["next_allowed_action"] == "controlled_asset_acquisition_required"
