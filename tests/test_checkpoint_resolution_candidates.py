"""Tests for checkpoint resolution candidate evaluation.

RC-COMBINE-V2-94001-98000:
  - valid_local_candidate_branch
  - candidate_requires_operator_review
  - invalid_checkpoint_rejected
  - sd15_checkpoint_rejected_for_sdxl_requirement
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_root(tmp_path: Path) -> str:
    """Create a minimal project root."""
    control_dir = tmp_path / "output" / "control"
    wf_assets_dir = control_dir / "workflow_assets"
    wf_assets_dir.mkdir(parents=True, exist_ok=True)

    # Minimal blocker artifacts
    for name in [
        "generation_gate_decision.json",
        "generation_runtime_blocker_report.json",
        "controlled_asset_acquisition_gate_packet.json",
    ]:
        (control_dir / name).write_text(json.dumps({"dummy": True}))

    # asset_requirements
    (wf_assets_dir / "asset_requirements.json").write_text(json.dumps({
        "checkpoint_required": True,
        "required_checkpoints": ["checkpoint_sdxl_base"],
    }))
    (wf_assets_dir / "asset_inventory.json").write_text(json.dumps({"missing_assets": ["checkpoint_sdxl_base"]}))
    (wf_assets_dir / "asset_resolution_plan.json").write_text(json.dumps({"missing_assets": ["checkpoint_sdxl_base"]}))
    (wf_assets_dir / "asset_verification_report.json").write_text(json.dumps({
        "required_assets_available": False,
        "errors": ["checkpoint_sdxl_base"],
    }))

    # Ensure generation_gate_decision has proper blockers
    (control_dir / "generation_gate_decision.json").write_text(json.dumps({
        "generation_can_be_authorized": False,
        "generation_gate_decision": "blocked_by_missing_assets",
        "reason": "missing checkpoint_sdxl_base",
        "blockers": [{"type": "active_asset_blocker", "missing_asset": "checkpoint_sdxl_base"}],
        "asset_blocker_active": True,
    }))

    return str(tmp_path)


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("file_name,expected_type", [
    ("sd_xl_base_1.0.safetensors", "sdxl"),
    ("sdXL_v10.safetensors", "sdxl"),
    ("sd_xl_turbo_1.0.safetensors", "sdxl"),
    ("sd1.5_base.safetensors", "sd15"),
    ("sd15_v11.safetensors", "sd15"),
    ("v1-5-pruned-emaonly.safetensors", "sd15"),
    ("something_random.safetensors", "unknown"),
])
def test_checkpoint_type_detection(file_name: str, expected_type: str) -> None:
    """Checkpoint type detection must correctly classify checkpoints."""
    from app.asset_resolution.checkpoint_resolution import _detect_checkpoint_type

    ckpt = {"file_name": file_name, "file_size_bytes": 3_000_000_000}
    detected = _detect_checkpoint_type(ckpt)
    assert detected == expected_type, (
        f"Expected {expected_type} for {file_name}, got {detected}"
    )


# ---------------------------------------------------------------------------
# Test: valid_local_candidate_branch
# ---------------------------------------------------------------------------

def test_valid_local_candidate_detection(project_root: str) -> None:
    """SDXL-compatible checkpoint should be detected as valid candidate."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
        evaluate_checkpoint_candidates,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [{
                "file_name": "sd_xl_turbo_1.0.safetensors",
                "file_size_bytes": 6_900_000_000,
                "file_path": "/fake/comfyui/models/checkpoints/sd_xl_turbo_1.0.safetensors",
                "source": "/fake/comfyui/models/checkpoints",
            }]

            inventory = scan_local_checkpoint_inventory(project_root)
            assert len(inventory["valid_candidates"]) == 1
            assert inventory["total_valid_candidates"] == 1

            review = evaluate_checkpoint_candidates(inventory)
            assert len(review["valid_candidates"]) == 1
            assert review["substitution_candidate_available"] is True
            assert review["requires_operator_review"] is True


# ---------------------------------------------------------------------------
# Test: candidate_requires_operator_review
# ---------------------------------------------------------------------------

def test_candidate_requires_operator_review(project_root: str) -> None:
    """When an SDXL candidate is found but is not the exact expected
    checkpoint, operator review must be required."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
        evaluate_checkpoint_candidates,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [{
                "file_name": "sdxl_v40.safetensors",
                "file_size_bytes": 6_800_000_000,
                "file_path": "/fake/a.safetensors",
                "source": "/fake/checkpoints",
            }]

            inventory = scan_local_checkpoint_inventory(project_root)
            review = evaluate_checkpoint_candidates(inventory)

            assert review["exact_match_available"] is False
            assert review["substitution_candidate_available"] is True
            assert review["requires_operator_review"] is True
            assert review["requires_operator_approval"] is True

            # Each candidate should flag auto_substitution_allowed=False
            for c in review["candidates"]:
                assert c["auto_substitution_allowed"] is False
                assert c["requires_operator_approval"] is True


# ---------------------------------------------------------------------------
# Test: invalid_checkpoint_rejected
# ---------------------------------------------------------------------------

def test_invalid_checkpoint_rejected(project_root: str) -> None:
    """Invalid/unrecognized checkpoints must not be treated as valid candidates."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [{
                "file_name": "random_model.safetensors",
                "file_size_bytes": 2_000_000_000,
                "file_path": "/fake/a.safetensors",
                "source": "/fake/checkpoints",
            }]

            inventory = scan_local_checkpoint_inventory(project_root)
            # 2GB file without keywords is classified as sd15_suspect and rejected
            assert len(inventory["valid_candidates"]) == 0
            assert inventory["total_valid_candidates"] == 0
            # Should be in rejected due to size-based SD1.5 suspicion
            assert len(inventory["rejected_checkpoints"]) == 1


# ---------------------------------------------------------------------------
# Test: sd15_checkpoint_rejected_for_sdxl_requirement
# ---------------------------------------------------------------------------

def test_sd15_checkpoint_rejected(project_root: str) -> None:
    """SD1.5 checkpoints must be explicitly rejected for SDXL requirement."""
    from app.asset_resolution.checkpoint_resolution import (
        scan_local_checkpoint_inventory,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [
                {
                    "file_name": "sd15_base.safetensors",
                    "file_size_bytes": 2_000_000_000,
                    "file_path": "/fake/a.safetensors",
                    "source": "/fake/checkpoints",
                },
                {
                    "file_name": "v1-5-pruned-emaonly.safetensors",
                    "file_size_bytes": 1_700_000_000,
                    "file_path": "/fake/b.safetensors",
                    "source": "/fake/checkpoints",
                },
            ]

            inventory = scan_local_checkpoint_inventory(project_root)

            # SD1.5 should be in sd15_found list
            assert len(inventory["sd15_found"]) == 2

            # SD1.5 must not be in valid_candidates
            assert len(inventory["valid_candidates"]) == 0

            # SD1.5 should be rejected
            assert len(inventory["rejected_checkpoints"]) == 2
            for r in inventory["rejected_checkpoints"]:
                assert "incompatible" in r["rejection_reason"].lower()


# ---------------------------------------------------------------------------
# Test: acquisition_required when only sd15 available
# ---------------------------------------------------------------------------

def test_acquisition_required_when_only_sd15(project_root: str) -> None:
    """When only SD1.5 checkpoints exist, resolution must require acquisition."""
    from app.asset_resolution.checkpoint_resolution import (
        resolve_checkpoint_asset,
    )

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [{
                "file_name": "sd15_v11.safetensors",
                "file_size_bytes": 2_000_000_000,
                "file_path": "/fake/a.safetensors",
                "source": "/fake/checkpoints",
            }]

            result = resolve_checkpoint_asset(project_root)
            assert result["selected_branch"] == "acquisition_required"
            assert result["checkpoint_resolved"] is False
            assert result["acquisition_required"] is True
            assert result["generation_performed"] is False


# ---------------------------------------------------------------------------
# Test: file_size_heuristic
# ---------------------------------------------------------------------------

def test_large_file_detected_as_sdxl_suspect() -> None:
    """Files > 5GB should be detected as sdxl_suspect even without SDXL keywords."""
    from app.asset_resolution.checkpoint_resolution import _detect_checkpoint_type

    ckpt = {"file_name": "my_custom_model.safetensors", "file_size_bytes": 6_500_000_000}
    detected = _detect_checkpoint_type(ckpt)
    assert detected == "sdxl_suspect"


def test_small_file_unknown() -> None:
    """Files without keywords and < 5GB should remain unknown."""
    from app.asset_resolution.checkpoint_resolution import _detect_checkpoint_type

    ckpt = {"file_name": "custom_model.safetensors", "file_size_bytes": 3_000_000_000}
    detected = _detect_checkpoint_type(ckpt)
    assert detected == "unknown"
