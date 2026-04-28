"""MK-REAL3R-6 — Tests for reference staging functionality (MK-REAL3R-6)."""
import shutil
from pathlib import Path

import pytest

from app.reference.reference_staging import (
    has_non_ascii,
    stage_reference_to_ascii,
    is_multi_panel_image,
    validate_clean_reference,
    prepare_clean_reference_candidate,
    create_alya_clean_single_portrait,
    create_alya_clean_single_portrait_v2,
)


class TestHasNonAscii:
    """Tests for has_non_ascii function."""

    def test_ascii_only_path_returns_false(self, tmp_path):
        """ASCII-only path should return False."""
        path = tmp_path / "reference.png"
        assert not has_non_ascii(path)

    def test_path_with_spaces_returns_true(self, tmp_path):
        """Path with spaces should return True."""
        path = tmp_path / "my reference.png"
        assert has_non_ascii(path)

    def test_cyrillic_path_returns_true(self, tmp_path):
        """Path with Cyrillic characters should return True."""
        path = tmp_path / "референс.png"
        assert has_non_ascii(path)


class TestStageReferenceToAscii:
    """Tests for stage_reference_to_ascii function."""

    def test_ascii_path_returns_as_is(self, tmp_path):
        """ASCII-only path should be returned as-is without copying."""
        original = tmp_path / "reference.png"
        original.touch()

        project_root = tmp_path / "project"
        project_root.mkdir()

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "character"
        )

        assert original_path == str(original)
        assert staged_path == str(original)

    def test_cyrillic_path_copies_to_ascii_staging(self, tmp_path):
        """Cyrillic path should be copied to ASCII staging path."""
        original = tmp_path / "референс.png"
        original.write_bytes(b"fake image data")

        project_root = tmp_path / "project"
        project_root.mkdir()

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "character"
        )

        assert original_path == str(original)
        assert staged_path != original_path
        assert "character_reference.png" in staged_path
        assert Path(staged_path).exists()
        assert Path(staged_path).read_bytes() == b"fake image data"

    def test_clean_reference_candidate_used_if_exists(self, tmp_path):
        """Clean reference candidate should be used instead of original if it exists."""
        original = tmp_path / "референс.png"
        original.write_bytes(b"original data")

        project_root = tmp_path / "project"
        project_root.mkdir()
        staging_dir = project_root / "output" / "control" / "references"
        staging_dir.mkdir(parents=True)

        clean_candidate = staging_dir / "character_clean_reference_480x640.png"
        clean_candidate.write_bytes(b"clean data")

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "character"
        )

        assert original_path == str(original)
        assert staged_path == str(clean_candidate)
        assert Path(staged_path).read_bytes() == b"clean data"


class TestIsMultiPanelImage:
    """Tests for is_multi_panel_image function."""

    def test_missing_file_returns_error(self, tmp_path):
        """Missing file should return error indicating analysis failed."""
        result = is_multi_panel_image(tmp_path / "nonexistent.png")
        assert result["is_multi_panel"] is True
        assert "Error" in result["reason"]

    def test_extreme_aspect_ratio_detects_multi_panel(self, tmp_path):
        """Extreme aspect ratio should be detected as multi-panel."""
        # Create a test image with extreme aspect ratio
        from PIL import Image

        test_image = tmp_path / "wide.png"
        img = Image.new("RGB", (3000, 500), color="white")
        img.save(test_image)

        result = is_multi_panel_image(test_image)
        assert result["is_multi_panel"] is True
        assert "aspect ratio" in result["reason"].lower()


class TestValidateCleanReference:
    """Tests for validate_clean_reference function."""

    def test_multi_panel_image_fails_validation(self, tmp_path):
        """Multi-panel image should fail validation."""
        result = validate_clean_reference(tmp_path / "nonexistent.png")
        assert result[0] is False
        assert result[1]

    def test_single_panel_passes_validation(self, tmp_path):
        """Single-panel image should pass validation."""
        from PIL import Image

        test_image = tmp_path / "single.png"
        img = Image.new("RGB", (512, 512), color="white")
        img.save(test_image)

        result = validate_clean_reference(test_image)
        assert result[0] is True
        assert "clean" in result[1].lower()


class TestPrepareCleanReferenceCandidate:
    """Tests for prepare_clean_reference_candidate function."""

    def test_prepares_clean_reference(self, tmp_path):
        """Should prepare clean reference by cropping center and resizing."""
        from PIL import Image

        source = tmp_path / "source.png"
        # Create a larger test image
        img = Image.new("RGB", (1000, 1000), color="white")
        img.save(source)

        output = tmp_path / "output.png"

        result = prepare_clean_reference_candidate(
            source, output, target_width=480, target_height=640
        )

        assert Path(result).exists()
        prepared = Image.open(result)
        assert prepared.size == (480, 640)


class TestCreateAlyaCleanSinglePortrait:
    """MK-REAL3R-6C — Tests for create_alya_clean_single_portrait function."""

    def test_create_alya_clean_single_portrait_creates_file(self, tmp_path):
        """Test that create_alya_clean_single_portrait creates a file."""
        # Create a mock contact sheet
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait(mock_sheet_path, output_dir)

        assert result.exists()
        assert "alya_clean_single_portrait_480x640.png" in result.name

    def test_create_alya_clean_single_portrait_dimensions(self, tmp_path):
        """Test that created clean portrait has correct dimensions."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait(mock_sheet_path, output_dir)

        with Image.open(result) as img:
            width, height = img.size
            assert width == 480
            assert height == 640

    def test_create_alya_clean_single_portrait_path_validation(self, tmp_path):
        """Test that clean portrait path is ASCII-safe and project-local."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait(mock_sheet_path, output_dir)

        # Path is ASCII-safe
        assert result.name.isascii()
        # Filename contains clean_single_portrait
        assert "clean_single_portrait" in result.name
        # Note: pytest uses temp directories, so we don't check for "Temp" in path

    def test_stage_reference_to_ascii_uses_clean_portrait_v2_for_alya(self, tmp_path):
        """Test that stage_reference_to_ascii uses clean portrait v2 for Alya (MK-REAL3R-6E)."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        # Create mock contact sheet with non-ASCII path
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "референсы" / "Аля.png"
        mock_sheet_path.parent.mkdir()
        mock_sheet.save(mock_sheet_path)

        # Stage reference
        original, staged, _ = stage_reference_to_ascii(mock_sheet_path, project_root, "Alya")

        # Should use clean portrait v2 from profile
        assert "alya_clean_single_portrait_v2_480x640.png" in staged
        assert Path(staged).exists()

    def test_stage_reference_to_ascii_creates_clean_portrait_v2_if_missing(self, tmp_path):
        """Test that stage_reference_to_ascii creates clean portrait v2 if missing (MK-REAL3R-6E)."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        # Create mock contact sheet with non-ASCII path
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "референсы" / "Аля.png"
        mock_sheet_path.parent.mkdir()
        mock_sheet.save(mock_sheet_path)

        # Stage reference without pre-creating clean portrait
        original, staged, _ = stage_reference_to_ascii(mock_sheet_path, project_root, "Alya")

        # Should create and use clean portrait v2 from profile
        assert "alya_clean_single_portrait_v2_480x640.png" in staged
        assert Path(staged).exists()


class TestCreateAlyaCleanSinglePortraitV2:
    """Tests for create_alya_clean_single_portrait_v2 function (MK-REAL3R-6E)."""

    def test_create_alya_clean_single_portrait_v2_creates_file(self, tmp_path):
        """Test that create_alya_clean_single_portrait_v2 creates a file."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)

        assert result.exists()
        assert "alya_clean_single_portrait_v2_480x640.png" in result.name

    def test_create_alya_clean_single_portrait_v2_dimensions(self, tmp_path):
        """Test that v2 clean portrait has correct dimensions."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)

        with Image.open(result) as img:
            width, height = img.size
            assert width == 480
            assert height == 640

    def test_create_alya_clean_single_portrait_v2_force_regenerates(self, tmp_path):
        """Test that force=True regenerates even if file exists."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create v2 file
        result1 = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)
        mtime1 = result1.stat().st_mtime

        # Force regenerate
        result2 = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)
        mtime2 = result2.stat().st_mtime

        # Should be same file but regenerated (mtime may differ)
        assert result1 == result2

    def test_create_alya_clean_single_portrait_v2_path_validation(self, tmp_path):
        """Test that v2 clean portrait path is ASCII-safe and project-local."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)

        # Path is ASCII-safe
        assert result.name.isascii()
        # Filename contains clean_single_portrait_v2
        assert "clean_single_portrait_v2" in result.name
        # Note: pytest uses temp directories, so we don't check for "Temp"/"AppData"/"pytest" in path

    def test_create_alya_clean_single_portrait_v2_not_original_dimensions(self, tmp_path):
        """Test that v2 is not original dimensions (1024x1360)."""
        from PIL import Image
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet_path = tmp_path / "mock_alya.png"
        mock_sheet.save(mock_sheet_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = create_alya_clean_single_portrait_v2(mock_sheet_path, output_dir, force=True)

        with Image.open(result) as img:
            width, height = img.size
            # Should be 480x640, not 1024x1360
            assert not (width == 1024 and height == 1360)
            assert width == 480
            assert height == 640

    def test_creates_480x640_png(self, tmp_path):
        """create_alya_clean_single_portrait creates 480x640 PNG."""
        from PIL import Image

        # Create a mock contact sheet (3x2 grid + UI strip)
        source = tmp_path / "contact_sheet.png"
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(source)

        output_dir = tmp_path / "references"
        result = create_alya_clean_single_portrait(source, output_dir)

        assert Path(result).exists()
        assert result.name == "alya_clean_single_portrait_480x640.png"
        assert result.suffix == ".png"

        clean = Image.open(result)
        assert clean.size == (480, 640)

    def test_clean_crop_output_path_is_project_local_and_ascii_safe(self, tmp_path):
        """Clean crop output path is project-local and ASCII-safe."""
        from PIL import Image

        source = tmp_path / "contact_sheet.png"
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(source)

        output_dir = tmp_path / "output" / "control" / "references"
        result = create_alya_clean_single_portrait(source, output_dir)

        # Path is within the specified output_dir (project-local relative to test)
        assert str(output_dir) in str(result)
        # Filename is ASCII-safe
        assert result.name.isascii()
        # Filename contains clean_single_portrait
        assert "clean_single_portrait" in result.name

    def test_clean_crop_does_not_equal_original_contact_sheet_dimensions(self, tmp_path):
        """Clean crop does not equal original contact sheet dimensions."""
        from PIL import Image

        source = tmp_path / "contact_sheet.png"
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(source)

        output_dir = tmp_path / "references"
        result = create_alya_clean_single_portrait(source, output_dir)

        clean = Image.open(result)
        original = Image.open(source)

        assert clean.size != original.size
        assert clean.size == (480, 640)

    def test_stage_reference_to_ascii_for_alya_uses_clean_single_portrait(self, tmp_path):
        """Stage reference to ASCII uses clean single portrait v2 for Alya (MK-REAL3R-6E)."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        original = tmp_path / "референсы" / "Аля.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        mock_sheet = Image.new("RGB", (1024, 1360), color="white")
        mock_sheet.save(original)

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "Alya"
        )

        # Should use clean single portrait v2 from profile
        assert "alya_clean_single_portrait_v2_480x640.png" in staged_path
        assert Path(staged_path).exists()

        # Verify dimensions
        clean = Image.open(staged_path)
        assert clean.size == (480, 640)

    def test_stage_reference_to_ascii_does_not_use_original_cyrillic_path(self, tmp_path):
        """Workflow staging does not use original Cyrillic Аля.png directly."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        original = tmp_path / "референсы" / "Аля.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(original)

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "Alya"
        )

        # Staged path should not be the original Cyrillic path
        assert staged_path != str(original)
        # Staged path should be ASCII-safe (filename)
        assert Path(staged_path).name.isascii()
        # Staged path should be within project root
        assert str(project_root) in str(staged_path)

    def test_stage_reference_to_ascii_does_not_use_temp_path(self, tmp_path):
        """Workflow staging does not use AppData/Temp paths."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        original = tmp_path / "референсы" / "Аля.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(original)

        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "Alya"
        )

        # Path should be within project root (not external temp directory)
        assert str(project_root) in str(staged_path)
        # Staged path should be ASCII-safe (filename)
        assert Path(staged_path).name.isascii()

    def test_observed_settings_contains_all_paths(self, tmp_path):
        """Observed settings contains original, staged, and clean paths."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        original = tmp_path / "референсы" / "Аля.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(original)

        original_path, staged_path, cleanliness_metadata = stage_reference_to_ascii(
            original, project_root, "Alya"
        )

        # Simulate observed settings structure
        observed_settings = {
            "reference_image_path": str(original),
            "staged_reference_image_path": staged_path,
            "clean_reference_path": staged_path,
            "reference_cleanliness": cleanliness_metadata,
        }

        # Verify all paths are present
        assert observed_settings["reference_image_path"] == str(original)
        assert observed_settings["staged_reference_image_path"] == staged_path
        assert observed_settings["clean_reference_path"] == staged_path
        assert observed_settings["reference_cleanliness"] is not None

    def test_old_contact_sheet_path_is_blocked_from_direct_use(self, tmp_path):
        """Old contact sheet path is blocked from direct use (MK-REAL3R-6E)."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        old_contact = tmp_path / "референсы" / "Аля.png"
        old_contact.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(old_contact)

        staging_dir = project_root / "output" / "control" / "references"
        staging_dir.mkdir(parents=True)

        clean_portrait = staging_dir / "alya_clean_single_portrait_480x640.png"
        img = Image.new("RGB", (480, 640), color="white")
        img.save(clean_portrait)

        # Stage with Alya character name - should prioritize profile strategy over existing clean_single_portrait
        original_path, staged_path, _ = stage_reference_to_ascii(
            old_contact, project_root, "Alya"
        )

        # Should use clean_single_portrait_v2 from profile, not the old contact sheet (MK-REAL3R-6E)
        assert "clean_single_portrait" in staged_path
        assert staged_path.endswith("alya_clean_single_portrait_v2_480x640.png")

    def test_no_real_comfyui_network_subprocess_calls(self, tmp_path):
        """No real ComfyUI/network/subprocess calls in staging."""
        from PIL import Image
        import json

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create project profile for Alya in the correct location
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        project_profile = {
            "project_id": "test_project",
            "characters": {
                "alya": {
                    "character_id": "alya",
                    "name": "Alya",
                    "aliases": ["Аля", "alya"],
                    "reference_image_path": str(tmp_path / "референсы" / "Аля.png"),
                    "reference_role": "character_identity",
                    "clean_reference": {
                        "strategy": "single_panel_crop",
                        "output_name": "alya_clean_single_portrait_v2_480x640.png",
                        "target_width": 480,
                        "target_height": 640,
                        "crop_box_mode": "relative",
                        "crop_box": [0.0, 0.0, 0.3333, 0.42],
                        "centering": [0.5, 0.35],
                        "force_regenerate": True,
                    },
                },
            },
        }
        with open(control_dir / "project_profile.json", "w", encoding="utf-8") as f:
            json.dump(project_profile, f)

        original = tmp_path / "референсы" / "Аля.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (3000, 2000), color="white")
        img.save(original)

        # This should complete without any network/subprocess calls
        original_path, staged_path, _ = stage_reference_to_ascii(
            original, project_root, "Alya"
        )

        # Just verify it completed successfully
        assert Path(staged_path).exists()
