"""Tests that forbidden actions are NOT performed during checkpoint resolution.

RC-COMBINE-V2-94001-98000:
  - fake_availability_blocked
  - unapproved_download_blocked
  - unapproved_install_blocked
  - generation_not_executed
  - comfyui_submit_not_executed
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

    for name in ["generation_gate_decision.json", "generation_runtime_blocker_report.json",
                  "controlled_asset_acquisition_gate_packet.json"]:
        (control_dir / name).write_text(json.dumps({"dummy": True}))

    (control_dir / "generation_gate_decision.json").write_text(json.dumps({
        "generation_can_be_authorized": False,
        "generation_gate_decision": "blocked_by_missing_assets",
        "reason": "missing checkpoint_sdxl_base",
        "blockers": [{"type": "active_asset_blocker", "missing_asset": "checkpoint_sdxl_base"}],
        "asset_blocker_active": True,
    }))
    (wf_assets_dir / "asset_requirements.json").write_text(json.dumps({"checkpoint_required": True}))
    (wf_assets_dir / "asset_inventory.json").write_text(json.dumps({"missing_assets": ["checkpoint_sdxl_base"]}))
    (wf_assets_dir / "asset_resolution_plan.json").write_text(json.dumps({"missing_assets": ["checkpoint_sdxl_base"]}))
    (wf_assets_dir / "asset_verification_report.json").write_text(json.dumps({
        "required_assets_available": False, "errors": ["checkpoint_sdxl_base"],
    }))

    return str(tmp_path)


# ---------------------------------------------------------------------------
# Forbidden action checks
# ---------------------------------------------------------------------------

def test_generation_not_executed(project_root: str) -> None:
    """Checkpoint resolution must NEVER execute generation."""
    # Verify the module does not import any generation-related execution modules
    import app.asset_resolution.checkpoint_resolution as cr
    source = Path(cr.__file__).read_text()

    # Must NOT import or reference generation execution modules
    forbidden_imports = ["run_workflow", "submit_to_comfy", "comfy_client", "generation_service"]
    for imp in forbidden_imports:
        assert imp not in source, f"Source must not import {imp}"

    # Must not call any generation function
    assert "def _run_generation" not in source
    assert "def _submit_to_comfy" not in source


def test_comfyui_submit_not_executed(project_root: str) -> None:
    """Checkpoint resolution must NEVER submit to ComfyUI."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            result = resolve_checkpoint_asset(project_root)
            assert result["comfyui_submit_executed"] is False


def test_fake_availability_blocked(project_root: str) -> None:
    """Resolution must not create fake checkpoint availability claims."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            result = resolve_checkpoint_asset(project_root)
            assert result["fake_checkpoint_availability_created"] is False

    # Check no artifact claims fake availability
    control_dir = Path(project_root) / "output" / "control"
    resolution_path = control_dir / "checkpoint_resolution_decision.json"
    if resolution_path.exists():
        decision = json.loads(resolution_path.read_text())
        assert decision.get("fake_checkpoint_availability_created") is False

    # Check acquisition blocker report forbids fake availability
    blocker_path = control_dir / "checkpoint_acquisition_blocker_report.json"
    if blocker_path.exists():
        blocker = json.loads(blocker_path.read_text())
        assert blocker.get("fake_availability_forbidden") is True


def test_unapproved_download_blocked(project_root: str) -> None:
    """Resolution must not authorize or perform downloads without operator approval."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            result = resolve_checkpoint_asset(project_root)
            assert result["download_authorized"] is False
            assert result["download_performed"] is False

    # Check acquisition artifacts enforce download_authorized=False
    control_dir = Path(project_root) / "output" / "control"

    for art_name in [
        "checkpoint_source_allowlist_decision.json",
        "checkpoint_acquisition_execution_contract.json",
    ]:
        art_path = control_dir / art_name
        if art_path.exists():
            data = json.loads(art_path.read_text())
            assert data.get("download_authorized") is False, (
                f"{art_name} must set download_authorized=false"
            )


def test_unapproved_install_blocked(project_root: str) -> None:
    """Resolution must not authorize or perform installs without operator approval."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []

            result = resolve_checkpoint_asset(project_root)
            assert result["install_authorized"] is False
            assert result["install_performed"] is False

    # Check install verification contract enforces install_authorized=False
    control_dir = Path(project_root) / "output" / "control"
    install_path = control_dir / "checkpoint_install_verification_contract.json"
    if install_path.exists():
        data = json.loads(install_path.read_text())
        assert data.get("install_authorized") is False
        assert data.get("install_performed") is False
        assert data.get("fake_install_proof_forbidden") is True


def test_retry_not_attempted(project_root: str) -> None:
    """Resolution must NEVER attempt retry."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = [{
                "file_name": "sd_xl_base_1.0.safetensors",
                "file_size_bytes": 6_944_000_000,
                "file_path": "/fake/a.safetensors",
                "source": "/fake/checkpoints",
            }]

            result = resolve_checkpoint_asset(project_root)
            assert result["retry_attempted"] is False


def test_visual_qa_not_executed(project_root: str) -> None:
    """Resolution must NEVER execute visual QA."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []
            result = resolve_checkpoint_asset(project_root)
            assert result.get("visual_qa_executed", False) is False


def test_assembly_not_executed(project_root: str) -> None:
    """Resolution must NEVER execute assembly."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []
            result = resolve_checkpoint_asset(project_root)
            assert result["assembly_executed"] is False
            assert result["downstream_executed"] is False


def test_no_preview_render(project_root: str) -> None:
    """Resolution must NEVER execute preview render."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            mock_scan.return_value = []
            result = resolve_checkpoint_asset(project_root)
            assert result.get("preview_render_executed", False) is False


def test_no_blind_substitution(project_root: str) -> None:
    """Resolution must not perform blind substitution without operator review."""
    from app.asset_resolution.checkpoint_resolution import resolve_checkpoint_asset

    with patch("app.asset_resolution.checkpoint_resolution._find_comfyui_root") as mock_find:
        mock_find.return_value = Path("/fake/comfyui")
        with patch("app.asset_resolution.checkpoint_resolution._scan_comfyui_checkpoints") as mock_scan:
            # SDXL candidate exists but not exact match
            mock_scan.return_value = [{
                "file_name": "sd_xl_turbo_1.0.safetensors",
                "file_size_bytes": 6_900_000_000,
                "file_path": "/fake/b.safetensors",
                "source": "/fake/checkpoints",
            }]

            result = resolve_checkpoint_asset(project_root)
            # Must require operator review, not auto-substitute
            assert result["operator_review_required"] is True
            assert result["checkpoint_resolved"] is False
            assert result["substitution_packet_created"] is True

    # Check the substitution packet forbids blind substitution
    control_dir = Path(project_root) / "output" / "control"
    packet_path = control_dir / "checkpoint_substitution_operator_review_packet.json"
    if packet_path.exists():
        packet = json.loads(packet_path.read_text())
        assert packet.get("auto_substitution_not_performed") is True
        assert packet.get("blind_substitution_forbidden") is True
