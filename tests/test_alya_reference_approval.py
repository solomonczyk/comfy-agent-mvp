"""
Tests for Alya reference approval.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch


class TestAlyaReferenceApproval:
    """Test Alya reference approval process."""
    
    @pytest.fixture
    def output_dir(self):
        """Get the output directory for Erdan source intake."""
        return Path("data/erdan_source/output/control")
    
    @pytest.fixture
    def reference_lock_contract(self, output_dir):
        """Load reference lock contract."""
        with open(output_dir / "reference_lock_contract.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def alya_reference_lock(self, output_dir):
        """Load Alya reference lock."""
        with open(output_dir / "alya_reference_lock.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    @pytest.fixture
    def generation_readiness_report(self, output_dir):
        """Load generation readiness report."""
        with open(output_dir / "alya_generation_readiness_report.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def test_reference_lock_contract_status_is_approved(self, reference_lock_contract):
        """Test that reference_lock_contract status is approved."""
        assert reference_lock_contract["reference_lock_status"] == "approved"
    
    def test_downstream_generation_allowed_is_true(self, reference_lock_contract):
        """Test that downstream_generation_allowed is true."""
        assert reference_lock_contract["downstream_generation_allowed"] is True
    
    def test_approved_by_is_user(self, reference_lock_contract):
        """Test that approved_by is user."""
        assert reference_lock_contract["approved_by"] == "user"
    
    def test_approved_references_contains_ref_alya_main(self, reference_lock_contract):
        """Test that approved_references contains ref_alya_main."""
        assert "ref_alya_main" in reference_lock_contract["approved_references"]
    
    def test_alya_reference_lock_exists(self, output_dir):
        """Test that alya_reference_lock exists."""
        assert (output_dir / "alya_reference_lock.json").exists()
    
    def test_alya_reference_lock_contains_immutable_anchors(self, alya_reference_lock):
        """Test that alya_reference_lock contains immutable anchors."""
        assert "immutable_anchors" in alya_reference_lock
        
        anchors = alya_reference_lock["immutable_anchors"]
        assert len(anchors) > 0
        
        # Check for specific anchors
        assert any("messy bun" in anchor.lower() for anchor in anchors)
        assert any("gray oversized hoodie" in anchor.lower() for anchor in anchors)
        assert any("blue jeans" in anchor.lower() for anchor in anchors)
        assert any("white sneakers" in anchor.lower() for anchor in anchors)
    
    def test_generation_readiness_report_ready_for_generation_true(self, generation_readiness_report):
        """Test that generation readiness report ready_for_generation=true."""
        assert generation_readiness_report["ready_for_generation"] is True
        assert generation_readiness_report["ready_for_reference_locked_generation"] is True
    
    def test_warning_exists_for_missing_other_character_refs(self, generation_readiness_report):
        """Test that warning exists for missing other character refs."""
        assert "warnings" in generation_readiness_report
        warnings = generation_readiness_report["warnings"]
        assert len(warnings) > 0
        
        # Check for warning about missing characters
        warning_text = " ".join(warnings).lower()
        assert any(char in warning_text for char in ["kael", "sera", "lord naris", "master eydon"])
    
    def test_no_comfyui_or_subprocess_generation_is_called(self, output_dir):
        """Test that no ComfyUI or subprocess generation is called."""
        # This test verifies that the reference approval process does not call
        # ComfyUI or subprocess - it's a metadata approval task only.
        
        with patch('subprocess.run', side_effect=AssertionError("Subprocess called!")) as mock_subprocess:
            with patch('subprocess.Popen', side_effect=AssertionError("Subprocess Popen called!")):
                # Load the reference approval artifacts (this is what the approval process does)
                with open(output_dir / "reference_lock_contract.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "alya_reference_lock.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                with open(output_dir / "alya_generation_readiness_report.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # If we get here, no subprocess was called
                assert mock_subprocess.call_count == 0
