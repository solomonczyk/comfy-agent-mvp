"""Tests for combine-validate-output-path-contract CLI command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_combine_validate_output_path_contract_creates_contract():
    """Test that combine-validate-output-path-contract creates the output path contract."""
    from app.cli import combine_validate_output_path_contract
    import argparse

    # Create a temporary project root
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create args
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )

        # Run the command
        result = combine_validate_output_path_contract(args)

        # Check return code
        assert result == 0

        # Check that contract file was created
        contract_path = control_dir / "combine_v2_output_path_contract.json"
        assert contract_path.exists()

        # Load and verify contract content
        with open(contract_path, 'r') as f:
            contract = json.load(f)

        assert contract["native_comfy_output_dir"] == r"F:\ComfyUI\comfyUI_portable_inst\ComfyUI_windows_portable_nvidia_cu126\ComfyUI_windows_portable\ComfyUI\output"
        assert contract["canonical_project_assets_dir"] == str(project_root / "output" / "assets")
        assert contract["manifest_must_reference_canonical_project_asset"] == True
        assert contract["native_output_is_staging_only"] == True
        assert contract["project_root_output_dir_is_not_canonical_for_this_rc"] == True
        assert "contract_created_at" in contract
        assert contract["rc_identifier"] == "RC-COMBINE-V2-681-740"

        # Check that validation file was created
        validation_path = control_dir / "combine_v2_output_path_contract_validation.json"
        assert validation_path.exists()

        # Load and verify validation content
        with open(validation_path, 'r') as f:
            validation = json.load(f)

        assert validation["contract_valid"] == True
        assert validation["native_comfy_output_is_staging_only"] == True
        assert "validation_timestamp" in validation
        assert "validation_checks" in validation


def test_combine_validate_output_path_contract_with_existing_assets():
    """Test that combine-validate-output-path-contract validates canonical assets."""
    from app.cli import combine_validate_output_path_contract
    import argparse

    # Create a temporary project root with assets
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        assets_dir = project_root / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy asset
        dummy_asset = assets_dir / "test_asset.png"
        dummy_asset.write_bytes(b"fake png data")

        # Create args
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )

        # Run the command
        result = combine_validate_output_path_contract(args)

        # Check return code
        assert result == 0

        # Load validation result
        validation_path = control_dir / "combine_v2_output_path_contract_validation.json"
        with open(validation_path, 'r') as f:
            validation = json.load(f)

        # Should detect canonical assets exist
        assert validation["canonical_project_asset_exists"] == True


def test_combine_validate_output_path_contract_with_manifest():
    """Test that combine-validate-output-path-contract checks manifest references."""
    from app.cli import combine_validate_output_path_contract
    import argparse

    # Create a temporary project root with manifest
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create a manifest that references canonical assets
        manifest = {
            "generated_assets": [
                {
                    "path": str(project_root / "output" / "assets" / "asset.png"),
                    "width": 1024,
                    "height": 1024
                }
            ]
        }
        manifest_path = control_dir / "combine_v2_generation_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        # Create args
        args = argparse.Namespace(
            project_root=str(project_root),
            json=True
        )

        # Run the command
        result = combine_validate_output_path_contract(args)

        # Check return code
        assert result == 0

        # Load validation result
        validation_path = control_dir / "combine_v2_output_path_contract_validation.json"
        with open(validation_path, 'r') as f:
            validation = json.load(f)

        # Should detect manifest references canonical assets
        assert validation["manifest_references_canonical_project_asset"] == True


if __name__ == "__main__":
    test_combine_validate_output_path_contract_creates_contract()
    test_combine_validate_output_path_contract_with_existing_assets()
    test_combine_validate_output_path_contract_with_manifest()
    print("All tests passed!")
