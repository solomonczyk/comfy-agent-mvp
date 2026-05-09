"""Integration tests for checkpoint resolution against the real ComfyUI installation.

RC-COMBINE-V2-98001-99000:
  - Verifies resolver finds the actual ComfyUI root on this machine
  - Verifies all 4 expected checkpoint files are discovered
  - Fails if the resolver cannot find local .safetensors from ComfyUI/models/checkpoints
  - Tests the acceptable_local_candidate_found status for sd_xl_base_1.0_0.9vae.safetensors

These tests use the real filesystem (no mocking). They pass only when the
ComfyUI installation is correctly configured and the resolver scan paths
are up to date.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Expected checkpoints from the real ComfyUI installation
# ---------------------------------------------------------------------------

EXPECTED_REAL_CHECKPOINTS = [
    "CyberRealisticXLPlay_V7.0_FP16.safetensors",
    "juggernautXL_version2.safetensors",
    "realvisxlV50_v50Bakedvae.safetensors",
    "sd_xl_base_1.0_0.9vae.safetensors",
]


def test_find_comfyui_root() -> None:
    """The resolver must locate the ComfyUI installation on this machine.

    Fails if _find_comfyui_root() returns None — indicates the resolver's
    candidate paths do not include the actual ComfyUI directory.
    """
    from app.asset_resolution.checkpoint_resolution import _find_comfyui_root

    root = _find_comfyui_root()
    assert root is not None, (
        "ComfyUI root not found by resolver. "
        "Check _find_comfyui_root() candidate paths."
    )
    assert root.exists(), f"ComfyUI root path does not exist: {root}"
    assert (root / "main.py").exists(), (
        f"ComfyUI root {root} has no main.py — wrong directory?"
    )


def test_scan_local_checkpoints_finds_real_files() -> None:
    """Inventory scan must find all expected checkpoint files.

    Fails if the resolver's scan returns fewer than 4 checkpoints,
    indicating a broken scan path or missing ComfyUI root detection.
    """
    from app.asset_resolution.checkpoint_resolution import scan_local_checkpoint_inventory

    project_root = str(Path(__file__).parent.parent)
    inventory = scan_local_checkpoint_inventory(project_root)

    assert inventory["comfyui_root_found"] is True, (
        "ComfyUI root not found during inventory scan"
    )
    assert inventory["total_checkpoints_found"] >= 4, (
        f"Expected >= 4 checkpoints, found {inventory['total_checkpoints_found']}. "
        f"Scanned dirs: {inventory['checkpoint_directories_scanned']}"
    )

    found_names = {c["file_name"] for c in inventory["found_checkpoints"]}
    for name in EXPECTED_REAL_CHECKPOINTS:
        assert name in found_names, (
            f"Expected checkpoint {name} not found in scan results. "
            f"Found: {sorted(found_names)}"
        )


def test_sdxl_base_acceptable_match_detected() -> None:
    """sd_xl_base_1.0_0.9vae.safetensors must be detected as acceptable local candidate.

    This test fails if the acceptable mapping (checkpoint_sdxl_base →
    sd_xl_base_1.0_0.9vae.safetensors) is not recognized.
    """
    from app.asset_resolution.checkpoint_resolution import (
        ACCEPTABLE_CANDIDATE_NAMES,
        EXPECTED_CHECKPOINT_ASSET,
    )

    # Verify the mapping exists
    acceptable = ACCEPTABLE_CANDIDATE_NAMES.get(EXPECTED_CHECKPOINT_ASSET, [])
    assert "sd_xl_base_1.0_0.9vae.safetensors" in acceptable, (
        "checkpoint_sdxl_base acceptable mapping missing sd_xl_base_1.0_0.9vae.safetensors"
    )


def test_resolver_does_not_claim_acquisition_required(tmp_path: Path) -> None:
    """When real checkpoints exist, resolver must NOT claim acquisition_required.

    Full resolution test with real filesystem scan and synthetic blocker artifacts.
    """
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    control_dir = tmp_path / "output" / "control"
    wf_dir = control_dir / "workflow_assets"
    wf_dir.mkdir(parents=True)

    # Create real-looking blocker artifacts
    _write_json(control_dir / "generation_gate_decision.json", {
        "generation_can_be_authorized": False,
        "generation_gate_decision": "blocked_by_missing_assets",
        "reason": "missing checkpoint_sdxl_base",
        "blockers": [
            {"type": "missing_required_assets",
             "detail": "Required assets missing: ['checkpoint_sdxl_base']"},
            {"type": "active_asset_blocker",
             "missing_asset": "checkpoint_sdxl_base",
             "detail": "Asset blocker active for: checkpoint_sdxl_base"},
        ],
        "asset_blocker_active": True,
    })
    _write_json(control_dir / "generation_runtime_blocker_report.json", {
        "missing_asset": "checkpoint_sdxl_base",
    })
    _write_json(control_dir / "controlled_asset_acquisition_gate_packet.json", {
        "missing_asset": "checkpoint_sdxl_base",
    })
    _write_json(wf_dir / "asset_requirements.json", {
        "checkpoint_required": True,
        "required_checkpoints": ["checkpoint_sdxl_base"],
    })
    _write_json(wf_dir / "asset_inventory.json", {
        "missing_assets": ["checkpoint_sdxl_base"],
    })
    _write_json(wf_dir / "asset_resolution_plan.json", {
        "missing_assets": ["checkpoint_sdxl_base"],
    })
    _write_json(wf_dir / "asset_verification_report.json", {
        "required_assets_available": False,
        "errors": ["checkpoint_sdxl_base"],
    })

    # Run resolution with real filesystem (NOT mocked)
    project_root = str(tmp_path)
    result = resolve_checkpoint_asset(project_root)

    # Must NOT claim acquisition required — checkpoints exist locally
    assert result["acquisition_required"] is False, (
        "Resolver claimed acquisition_required but real checkpoints exist. "
        "Check _find_comfyui_root() candidate paths."
    )

    # Should resolve via exact or acceptable match
    assert result["checkpoint_resolved"] is True, (
        "Resolver did not resolve checkpoint despite real checkpoints existing. "
        f"Branch: {result['selected_branch']}, Status: {result.get('resolution_status')}"
    )

    # Verify fine-grained status
    resolution_status = result.get("resolution_status")
    assert resolution_status in ("exact_match_found", "acceptable_local_candidate_found"), (
        f"Expected exact_match_found or acceptable_local_candidate_found, got {resolution_status}"
    )

    # Forbidden flags
    assert result["download_authorized"] is False
    assert result["download_performed"] is False
    assert result["install_authorized"] is False
    assert result["install_performed"] is False
    assert result["generation_performed"] is False
    assert result["comfyui_submit_executed"] is False
    assert result["production_accepted"] is False
