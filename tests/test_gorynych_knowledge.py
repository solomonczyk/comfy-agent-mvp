"""
Tests for GORYNYCH knowledge loading.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.gorynych.knowledge import (
    load_head_1,
    load_head_2,
    load_head_3,
    validate_knowledge_files,
    get_knowledge_dir,
)


class TestKnowledgeLoading:
    """Test knowledge file loading functionality."""
    
    def test_all_three_knowledge_files_load(self):
        """Test that all three knowledge files can be loaded."""
        head_1 = load_head_1()
        head_2 = load_head_2()
        head_3 = load_head_3()
        
        assert isinstance(head_1, str)
        assert isinstance(head_2, str)
        assert isinstance(head_3, str)
        
        assert len(head_1) > 0
        assert len(head_2) > 0
        assert len(head_3) > 0
        
        # Check that content contains expected keywords
        assert "Story Contract" in head_1
        assert "Character Canon" in head_2
        assert "Shot Contract" in head_3
    
    def test_missing_knowledge_file_raises_clear_error(self):
        """Test that missing knowledge file raises a clear FileNotFoundError."""
        # Temporarily rename a file to simulate missing
        knowledge_dir = get_knowledge_dir()
        head_1_path = knowledge_dir / "head_1.md"
        temp_path = knowledge_dir / "head_1.md.tmp"
        
        try:
            # Rename the file
            shutil.move(str(head_1_path), str(temp_path))
            
            # Attempt to load - should raise FileNotFoundError
            with pytest.raises(FileNotFoundError) as exc_info:
                load_head_1()
            
            # Check that error message is clear
            error_message = str(exc_info.value)
            assert "head_1.md" in error_message
            assert "not found" in error_message.lower()
            
        finally:
            # Restore the file
            if temp_path.exists():
                shutil.move(str(temp_path), str(head_1_path))
    
    def test_validate_knowledge_files_returns_true_when_all_files_exist(self):
        """Test that validate_knowledge_files returns True when all files exist."""
        result = validate_knowledge_files()
        assert result is True
    
    def test_validate_knowledge_files_returns_false_when_file_missing(self):
        """Test that validate_knowledge_files returns False when a file is missing."""
        knowledge_dir = get_knowledge_dir()
        head_2_path = knowledge_dir / "head_2.md"
        temp_path = knowledge_dir / "head_2.md.tmp"
        
        try:
            # Rename the file
            shutil.move(str(head_2_path), str(temp_path))
            
            # Validate should return False
            result = validate_knowledge_files()
            assert result is False
            
        finally:
            # Restore the file
            if temp_path.exists():
                shutil.move(str(temp_path), str(head_2_path))
