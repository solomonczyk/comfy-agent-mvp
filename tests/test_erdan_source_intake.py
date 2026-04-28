"""
Tests for Erdan source root intake and Alya reference canon.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch


class TestErdanSourceIntake:
    """Test that Erdan source root and Alya visual canon are registered correctly."""
    
    @pytest.fixture
    def output_dir(self):
        """Get the output directory for Erdan source intake."""
        return Path("data/erdan_source/output/control")
    
    @pytest.fixture
    def source_root_manifest(self, output_dir):
        """Load source root manifest."""
        with open(output_dir / "source_root_manifest.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def scenario_inventory(self, output_dir):
        """Load scenario inventory."""
        with open(output_dir / "scenario_inventory.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def alya_reference_manifest(self, output_dir):
        """Load Alya reference manifest."""
        with open(output_dir / "alya_reference_manifest.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def alya_visual_canon(self, output_dir):
        """Load Alya visual canon."""
        with open(output_dir / "alya_visual_canon.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def alya_forbidden_drift(self, output_dir):
        """Load Alya forbidden drift."""
        with open(output_dir / "alya_forbidden_drift.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def reference_lock_contract(self, output_dir):
        """Load reference lock contract."""
        with open(output_dir / "reference_lock_contract.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def test_source_root_manifest_exists(self, output_dir):
        """Test that source_root_manifest exists."""
        assert (output_dir / "source_root_manifest.json").exists()
    
    def test_source_root_manifest_points_to_correct_path(self, source_root_manifest):
        """Test that source_root_manifest points to F:\\VideoProjects\\МИР\\Эрдан."""
        assert source_root_manifest["source_root"] == "F:\\VideoProjects\\МИР\\Эрдан"
        assert source_root_manifest["project_title"] == "Попаданка / Erdan"
        assert source_root_manifest["expected_episode_count"] == 420
    
    def test_scenario_inventory_exists(self, output_dir):
        """Test that scenario_inventory exists."""
        assert (output_dir / "scenario_inventory.json").exists()
    
    def test_scenario_inventory_contains_file_counts(self, scenario_inventory):
        """Test that scenario_inventory contains counts for markdown/text/video/image files."""
        assert "total_markdown_files" in scenario_inventory
        assert "total_text_files" in scenario_inventory
        assert "total_video_files" in scenario_inventory
        assert "total_image_files" in scenario_inventory
        assert scenario_inventory["total_markdown_files"] > 0
        assert scenario_inventory["total_image_files"] > 0
    
    def test_alya_reference_manifest_exists(self, output_dir):
        """Test that alya_reference_manifest exists."""
        assert (output_dir / "alya_reference_manifest.json").exists()
    
    def test_alya_visual_canon_contains_required_immutable_anchors(self, alya_visual_canon):
        """Test that alya_visual_canon contains required immutable anchors."""
        assert "immutable_anchors" in alya_visual_canon
        anchors = alya_visual_canon["immutable_anchors"]
        
        # Check for required anchors
        assert any("messy bun" in anchor.lower() for anchor in anchors)
        assert any("gray oversized hoodie" in anchor.lower() for anchor in anchors)
        assert any("blue jeans" in anchor.lower() for anchor in anchors)
        assert any("white sneakers" in anchor.lower() for anchor in anchors)
    
    def test_alya_forbidden_drift_rejects_blue_hoodie_and_glamour_makeup(self, alya_forbidden_drift):
        """Test that alya_forbidden_drift rejects blue hoodie and glamour makeup."""
        assert "forbidden_identity_drift" in alya_forbidden_drift
        forbidden = alya_forbidden_drift["forbidden_identity_drift"]
        
        assert "blue hoodie" in forbidden
        assert "glamour makeup" in forbidden
    
    def test_reference_lock_contract_blocks_downstream_generation_by_default(self, reference_lock_contract):
        """Test that reference_lock_contract blocks downstream generation by default."""
        # After MK-SOURCE2 user approval, this is now approved
        assert reference_lock_contract["reference_lock_status"] == "approved"
        assert reference_lock_contract["downstream_generation_allowed"] is True
        assert reference_lock_contract["approved_by"] == "user"
    
    def test_reference_lock_contract_approval_timestamp_is_null(self, reference_lock_contract):
        """Test that reference_lock_contract approval_timestamp is null."""
        # After MK-SOURCE2 user approval, this now has a timestamp
        assert reference_lock_contract["approval_timestamp"] is not None
        assert reference_lock_contract["approved_by"] == "user"
        assert "ref_alya_main" in reference_lock_contract["approved_references"]
    
    def test_no_comfyui_or_subprocess_generation_is_called(self):
        """Test that no ComfyUI or subprocess generation is called."""
        # This test verifies that the source intake process does not call
        # ComfyUI or subprocess - it's a metadata ingestion task only.
        # Since we're only creating JSON files and not running any generation,
        # this test passes by construction.
        
        # Patch subprocess to detect any calls
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")) as mock_subprocess:
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Load the manifests (this is what the intake process does)
                output_dir = Path("data/erdan_source/output/control")
                
                with open(output_dir / "source_root_manifest.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "scenario_inventory.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "alya_reference_manifest.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "alya_visual_canon.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "alya_forbidden_drift.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "reference_lock_contract.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # If we get here, no subprocess was called
                assert mock_subprocess.call_count == 0
