"""Tests for combine-run-rebuilt-asset-visual-qa CLI command."""

import json
import tempfile
from pathlib import Path
from PIL import Image
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_combine_run_rebuilt_asset_visual_qa_creates_artifacts():
    """Test that combine-run-rebuilt-asset-visual-qa creates all required artifacts."""
    from app.cli import combine_run_rebuilt_asset_visual_qa
    import argparse

    # Create a temporary project root with a test asset
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        assets_dir = project_root / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create a 1024x1024 test image
        test_asset = assets_dir / "combine_v2_1777917278_00001_.png"
        img = Image.new('RGB', (1024, 1024), color='red')
        img.save(test_asset)

        # Create args
        args = argparse.Namespace(
            project_root=str(project_root),
            asset="output/assets/combine_v2_1777917278_00001_.png",
            json=True
        )

        # Run the command
        result = combine_run_rebuilt_asset_visual_qa(args)

        # Check return code
        assert result == 0

        # Check that all artifacts were created
        qa_report_path = control_dir / "combine_v2_rebuilt_asset_visual_qa_report.json"
        assert qa_report_path.exists()

        failure_audit_path = control_dir / "combine_v2_rebuilt_asset_failure_audit.json"
        assert failure_audit_path.exists()

        operator_review_packet_path = control_dir / "combine_v2_rebuilt_asset_operator_review_packet.json"
        assert operator_review_packet_path.exists()

        retry_recommendation_path = control_dir / "combine_v2_rebuilt_asset_retry_recommendation_request.json"
        assert retry_recommendation_path.exists()

        # Load and verify QA report
        with open(qa_report_path, 'r') as f:
            qa_report = json.load(f)

        assert qa_report["source_asset"] == "output/assets/combine_v2_1777917278_00001_.png"
        assert qa_report["asset_exists"] == True
        assert qa_report["asset_readable"] == True
        assert qa_report["width"] == 1024
        assert qa_report["height"] == 1024
        assert qa_report["minimum_short_side_1024_valid"] == True
        assert qa_report["resolution_policy_passed"] == True
        assert qa_report["visual_qa_executed"] == True
        assert qa_report["qa_verdict"] == "qa_failed"
        assert len(qa_report["failure_categories"]) > 0
        assert qa_report["generation_performed"] == False
        assert qa_report["comfyui_execution"] == False
        assert qa_report["retry_attempted"] == False
        assert qa_report["assembly_executed"] == False
        assert qa_report["downstream_executed"] == False
        assert qa_report["production_accepted"] == False
        assert qa_report["next_allowed_action"] == "operator_visual_review"

        # Load and verify failure audit
        with open(failure_audit_path, 'r') as f:
            failure_audit = json.load(f)

        assert failure_audit["stage"] == "rebuilt_asset_visual_qa"
        assert failure_audit["qa_verdict"] == "qa_failed"
        assert failure_audit["generation_performed"] == False
        assert failure_audit["comfyui_execution"] == False
        assert failure_audit["next_allowed_action"] == "operator_visual_review"

        # Load and verify operator review packet
        with open(operator_review_packet_path, 'r') as f:
            operator_review_packet = json.load(f)

        assert operator_review_packet["stage"] == "operator_visual_review"
        assert operator_review_packet["operator_review_required"] == True
        assert len(operator_review_packet["operator_actions"]) > 0
        assert operator_review_packet["generation_performed"] == False
        assert operator_review_packet["comfyui_execution"] == False
        assert operator_review_packet["next_allowed_action"] == "operator_visual_review"

        # Load and verify retry recommendation
        with open(retry_recommendation_path, 'r') as f:
            retry_recommendation = json.load(f)

        assert retry_recommendation["stage"] == "retry_recommendation_request"
        assert retry_recommendation["retry_authorized"] == False
        assert retry_recommendation["generation_performed"] == False
        assert retry_recommendation["comfyui_execution"] == False
        assert retry_recommendation["next_allowed_action"] == "operator_visual_review"


def test_combine_run_rebuilt_asset_visual_qa_with_missing_asset():
    """Test that combine-run-rebuilt-asset-visual-qa handles missing asset."""
    from app.cli import combine_run_rebuilt_asset_visual_qa
    import argparse

    # Create a temporary project root without the asset
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create args pointing to non-existent asset
        args = argparse.Namespace(
            project_root=str(project_root),
            asset="output/assets/missing_asset.png",
            json=True
        )

        # Run the command
        result = combine_run_rebuilt_asset_visual_qa(args)

        # Check return code (should still succeed even if asset missing)
        assert result == 0

        # Load and verify QA report
        qa_report_path = control_dir / "combine_v2_rebuilt_asset_visual_qa_report.json"
        with open(qa_report_path, 'r') as f:
            qa_report = json.load(f)

        assert qa_report["asset_exists"] == False
        assert qa_report["asset_readable"] == False
        assert qa_report["qa_verdict"] == "qa_failed"


def test_combine_run_rebuilt_asset_visual_qa_with_absolute_path():
    """Test that combine-run-rebuilt-asset-visual-qa handles absolute asset path."""
    from app.cli import combine_run_rebuilt_asset_visual_qa
    import argparse

    # Create a temporary project root with a test asset
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        assets_dir = project_root / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Create a test image
        test_asset = assets_dir / "test_absolute.png"
        img = Image.new('RGB', (1024, 1024), color='blue')
        img.save(test_asset)

        # Create args with absolute path
        args = argparse.Namespace(
            project_root=str(project_root),
            asset=str(test_asset.absolute()),
            json=True
        )

        # Run the command
        result = combine_run_rebuilt_asset_visual_qa(args)

        # Check return code
        assert result == 0

        # Load and verify QA report
        qa_report_path = control_dir / "combine_v2_rebuilt_asset_visual_qa_report.json"
        with open(qa_report_path, 'r') as f:
            qa_report = json.load(f)

        assert qa_report["asset_exists"] == True
        assert qa_report["asset_readable"] == True
        assert qa_report["width"] == 1024
        assert qa_report["height"] == 1024


if __name__ == "__main__":
    test_combine_run_rebuilt_asset_visual_qa_creates_artifacts()
    test_combine_run_rebuilt_asset_visual_qa_with_missing_asset()
    test_combine_run_rebuilt_asset_visual_qa_with_absolute_path()
    print("All tests passed!")
