"""
Tests for Knowledge Bootstrapper.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from app.kb.bootstrap import KnowledgeBootstrapper
from app.kb.models import (
    KBReadinessReport,
    ProjectManifest,
    SeriesBible,
    ReferenceLockContract,
)


class TestKnowledgeBootstrapper:
    """Test KnowledgeBootstrapper functionality."""
    
    @pytest.fixture
    def bootstrapper(self, tmp_path):
        """Create a bootstrapper with temp output dir."""
        return KnowledgeBootstrapper(base_output_dir=str(tmp_path))
    
    @pytest.fixture
    def temp_source_root(self, tmp_path):
        """Create a temporary source root with sample files."""
        source_root = tmp_path / "test_source"
        source_root.mkdir()
        
        # Create sample files
        (source_root / "script.md").write_text("# Test Script")
        (source_root / "readme.txt").write_text("Test readme")
        (source_root / "reference.png").write_bytes(b"fake png")
        
        return str(source_root)
    
    def test_bootstrap_empty_project_creates_kb_readiness_report_with_kb_ready_false(self, bootstrapper):
        """Test that bootstrap_empty_project creates kb_readiness_report with kb_ready=false."""
        report = bootstrapper.bootstrap_empty_project("test_project")
        
        assert report.kb_ready is False
        assert report.ready_for_reference_selection is False
        assert report.ready_for_generation is False
    
    def test_bootstrap_empty_project_does_not_fake_character_canon(self, bootstrapper):
        """Test that bootstrap_empty_project does not fake character canon."""
        bootstrapper.bootstrap_empty_project("test_project")
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        # Character canon should not exist for empty project
        assert not (project_dir / "character_canon.json").exists()
    
    def test_bootstrap_from_raw_brief_creates_project_manifest(self, bootstrapper):
        """Test that bootstrap_from_raw_brief creates project_manifest."""
        brief = "Test Project\nThis is a test project about a character."
        report = bootstrapper.bootstrap_from_raw_brief("test_project", brief)
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        assert (project_dir / "project_manifest.json").exists()
        
        with open(project_dir / "project_manifest.json", 'r', encoding='utf-8') as f:
            manifest = ProjectManifest.from_dict(json.load(f))
        
        assert manifest.project_id == "test_project"
        assert manifest.project_title == "Test Project"
    
    def test_bootstrap_from_raw_brief_creates_preliminary_series_bible(self, bootstrapper):
        """Test that bootstrap_from_raw_brief creates preliminary series_bible."""
        brief = "Test Project\nThis is a test project."
        report = bootstrapper.bootstrap_from_raw_brief("test_project", brief)
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        assert (project_dir / "series_bible.json").exists()
        
        with open(project_dir / "series_bible.json", 'r', encoding='utf-8') as f:
            bible = SeriesBible.from_dict(json.load(f))
        
        assert bible.title == "Test Project"
    
    def test_bootstrap_from_raw_brief_blocks_generation(self, bootstrapper):
        """Test that bootstrap_from_raw_brief blocks generation."""
        brief = "Test Project\nThis is a test project."
        report = bootstrapper.bootstrap_from_raw_brief("test_project", brief)
        
        assert report.ready_for_generation is False
        assert report.kb_ready is False
    
    def test_bootstrap_from_source_root_creates_source_inventory(self, bootstrapper, temp_source_root):
        """Test that bootstrap_from_source_root creates source_inventory."""
        report = bootstrapper.bootstrap_from_source_root("test_project", temp_source_root)
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        assert (project_dir / "source_inventory.json").exists()
        
        with open(project_dir / "source_inventory.json", 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        
        assert inventory["markdown_files"] == 1
        assert inventory["text_files"] == 1
        assert inventory["image_files"] == 1
    
    def test_source_inventory_counts_markdown_text_image_video_files(self, bootstrapper, temp_source_root):
        """Test that source_inventory counts markdown/text/image/video files."""
        report = bootstrapper.bootstrap_from_source_root("test_project", temp_source_root)
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        with open(project_dir / "source_inventory.json", 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        
        assert "markdown_files" in inventory
        assert "text_files" in inventory
        assert "image_files" in inventory
        assert "video_files" in inventory
    
    def test_reference_lock_contract_defaults_downstream_generation_allowed_false(self, bootstrapper):
        """Test that reference_lock_contract defaults downstream_generation_allowed=false."""
        brief = "Test Project"
        bootstrapper.bootstrap_from_raw_brief("test_project", brief)
        
        project_dir = Path(bootstrapper.base_output_dir) / "test_project" / "output" / "control"
        
        with open(project_dir / "reference_lock_contract.json", 'r', encoding='utf-8') as f:
            lock = ReferenceLockContract.from_dict(json.load(f))
        
        assert lock.downstream_generation_allowed is False
        assert lock.approval_timestamp is None
        assert lock.approved_by is None
    
    def test_kb_readiness_report_ready_for_generation_false_until_references_approved(self, bootstrapper):
        """Test that kb_readiness_report ready_for_generation=false until references approved."""
        brief = "Test Project"
        report = bootstrapper.bootstrap_from_raw_brief("test_project", brief)
        
        assert report.ready_for_generation is False
        assert "references" in " ".join(report.blocking_reasons).lower() or len(report.blocking_reasons) > 0
    
    def test_no_comfyui_or_subprocess_is_called(self, bootstrapper):
        """Test that no ComfyUI or subprocess is called."""
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")) as mock_subprocess:
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Run bootstrap methods
                bootstrapper.bootstrap_empty_project("test_project")
                
                brief = "Test Project"
                bootstrapper.bootstrap_from_raw_brief("test_project", brief)
                
                # If we get here, no subprocess was called
                assert mock_subprocess.call_count == 0
