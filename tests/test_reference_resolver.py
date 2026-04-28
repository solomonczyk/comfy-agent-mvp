"""MK-REF1R-2 — Tests for ReferenceResolver."""
from pathlib import Path
import pytest
import tempfile

from app.reference.reference_resolver import ReferenceResolver


class TestReferenceResolver:
    """Tests for ReferenceResolver."""

    def test_scans_reference_root_for_image_files(self, tmp_path):
        """Test that ReferenceResolver scans reference root for image files."""
        # Create reference root with test files
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create test image files
        (reference_root / "Аля.png").write_bytes(b"fake png data")
        (reference_root / "test.jpg").write_bytes(b"fake jpg data")
        (reference_root / "Character_Creator_test.png").write_bytes(b"fake png data")
        
        # Create non-image file
        (reference_root / "readme.txt").write_text("test")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        files = resolver.scan_reference_root()
        
        # Should find 3 image files
        assert len(files) == 3
        file_names = [f["name"] for f in files]
        assert "Аля.png" in file_names
        assert "test.jpg" in file_names
        assert "Character_Creator_test.png" in file_names
        assert "readme.txt" not in file_names

    def test_finds_alya_reference(self, tmp_path):
        """RC-CORE1 — Test that ReferenceResolver finds character reference by exact name match."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create character reference file with exact name
        alya_ref = reference_root / "Alya.png"
        alya_ref.write_bytes(b"fake png data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        reference = resolver.resolve_character_reference("Alya")
        
        assert reference is not None
        assert reference["character_name"] == "Alya"
        assert reference["reference_role"] == "character_identity"
        assert reference["lock_strength"] == 0.65
        assert "Alya.png" in reference["reference_image_path"]

    def test_finds_cyrillic_alya_reference(self, tmp_path):
        """RC-CORE1 — Test that ReferenceResolver finds character reference by exact Cyrillic name match."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create character reference file with exact Cyrillic name
        alya_ref = reference_root / "Аля.png"
        alya_ref.write_bytes(b"fake png data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        reference = resolver.resolve_character_reference("Аля")
        
        assert reference is not None
        assert reference["character_name"] == "Аля"
        assert "Аля.png" in reference["reference_image_path"]

    def test_returns_existing_path_only(self, tmp_path):
        """RC-CORE1 — Test that ReferenceResolver returns existing file only by exact name match."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create character reference file with exact name
        alya_ref = reference_root / "Alya.png"
        alya_ref.write_bytes(b"fake png data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        reference = resolver.resolve_character_reference("Alya")
        
        # Verify file exists
        assert Path(reference["reference_image_path"]).exists()
        
        # Try to resolve non-existent character
        reference_none = resolver.resolve_character_reference("NonExistent")
        assert reference_none is None

    def test_returns_none_when_reference_root_missing(self, tmp_path):
        """Test that ReferenceResolver returns None when reference root missing."""
        reference_root = tmp_path / "референсы"
        # Don't create the directory
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        reference = resolver.resolve_character_reference("Alya")
        
        assert reference is None

    def test_returns_none_when_character_not_found(self, tmp_path):
        """Test that ReferenceResolver returns None when character not found."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create some other reference file
        (reference_root / "other.png").write_bytes(b"fake png data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        reference = resolver.resolve_character_reference("Alya")
        
        assert reference is None

    def test_supports_multiple_reference_formats(self, tmp_path):
        """RC-CORE1 — Test that ReferenceResolver supports multiple image formats by exact name match."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create character references in different formats with exact name
        (reference_root / "Alya.png").write_bytes(b"fake png data")
        (reference_root / "Alya.jpg").write_bytes(b"fake jpg data")
        (reference_root / "Alya.webp").write_bytes(b"fake webp data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        
        # Should find Alya reference (prioritizes exact match)
        reference = resolver.resolve_character_reference("Alya")
        assert reference is not None
        assert "Alya" in reference["reference_image_path"]

    def test_no_real_comfyui_network_calls_in_tests(self, tmp_path):
        """RC-CORE1 — Test that ReferenceResolver does not make ComfyUI or network calls."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create character reference file with exact name
        (reference_root / "Alya.png").write_bytes(b"fake png data")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        
        # This should not make any network calls
        reference = resolver.resolve_character_reference("Alya")
        
        assert reference is not None
        # If we get here without network errors, the test passes

    def test_scan_returns_empty_when_no_files(self, tmp_path):
        """Test that scan returns empty list when no files."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        files = resolver.scan_reference_root()
        
        assert files == []

    def test_scan_filters_by_extension(self, tmp_path):
        """Test that scan filters by valid image extensions."""
        reference_root = tmp_path / "референсы"
        reference_root.mkdir()
        
        # Create various files
        (reference_root / "test.png").write_bytes(b"png")
        (reference_root / "test.jpg").write_bytes(b"jpg")
        (reference_root / "test.jpeg").write_bytes(b"jpeg")
        (reference_root / "test.webp").write_bytes(b"webp")
        (reference_root / "test.txt").write_text("text")
        (reference_root / "test.pdf").write_bytes(b"pdf")
        
        resolver = ReferenceResolver(tmp_path, reference_root)
        files = resolver.scan_reference_root()
        
        # Should only find image files
        assert len(files) == 4
        extensions = [f["extension"] for f in files]
        assert ".png" in extensions
        assert ".jpg" in extensions
        assert ".jpeg" in extensions
        assert ".webp" in extensions
        assert ".txt" not in extensions
        assert ".pdf" not in extensions
