"""Tests for recipe-check CLI command."""
import json
import tempfile
from pathlib import Path

import pytest

from app.cli import recipe_check
from argparse import Namespace


class TestRecipeCLI:
    """Test recipe-check CLI command."""

    def test_valid_pass_settings_returns_exit_code_0(self):
        """Test that valid pass settings returns exit code 0."""
        # Create temporary settings file with valid settings
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 0
        finally:
            Path(settings_path).unlink()

    def test_warn_settings_returns_exit_code_0(self):
        """Test that warn settings returns exit code 0."""
        # Create temporary settings file with warn settings
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 6,  # Below min
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face",  # Missing some terms
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 0
        finally:
            Path(settings_path).unlink()

    def test_fail_settings_returns_exit_code_2(self):
        """Test that fail settings returns exit code 2."""
        # Create temporary settings file with fail settings
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 12,  # Exceeds max
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 2
        finally:
            Path(settings_path).unlink()

    def test_missing_settings_file_returns_exit_code_1(self):
        """Test that missing settings file returns exit code 1."""
        args = Namespace(
            settings="nonexistent_file.json",
            task_type="storyboard_keyframes",
            hardware="gtx_1060_5gb",
            project_profile=None,
            json=True,
        )
        
        exit_code = recipe_check(args)
        assert exit_code == 1

    def test_invalid_json_returns_exit_code_1(self):
        """Test that invalid JSON returns exit code 1."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json")
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 1
        finally:
            Path(settings_path).unlink()

    def test_direct_observed_settings_format_is_accepted(self):
        """Test that direct observed settings format is accepted."""
        # Format A: direct observed settings
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 0
        finally:
            Path(settings_path).unlink()

    def test_wrapped_observed_settings_format_is_accepted(self):
        """Test that wrapped observed_settings format is accepted."""
        # Format B: wrapped with "observed_settings" key
        settings_data = {
            "observed_settings": {
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "steps": 20,
                "cfg": 7.0,
                "width": 480,
                "height": 640,
                "batch_size": 2,
                "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            },
            "raw_nodes": {},
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 0
        finally:
            Path(settings_path).unlink()

    def test_project_profile_file_is_accepted_and_does_not_crash(self):
        """Test that project profile file is accepted and does not crash."""
        # Create temporary settings file
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        # Create temporary project profile file
        project_profile_data = {
            "reference_lock_required": False,
            "custom_key": "custom_value",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(project_profile_data, f)
            project_profile_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=project_profile_path,
                json=True,
            )
            
            exit_code = recipe_check(args)
            assert exit_code == 0
        finally:
            Path(settings_path).unlink()
            Path(project_profile_path).unlink()

    def test_output_json_contains_verdict_score_recipe_id_issues_recommended_settings(self):
        """Test that output JSON contains required fields."""
        # Capture stdout
        import io
        import sys
        
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                exit_code = recipe_check(args)
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout
            
            assert exit_code == 0
            
            # Parse output JSON
            result = json.loads(output)
            
            # Verify required fields
            assert "verdict" in result
            assert "score" in result
            assert "recipe_id" in result
            assert "issues" in result
            assert "recommended_settings" in result
        finally:
            Path(settings_path).unlink()

    def test_command_is_read_only_does_not_modify_settings_file(self):
        """Test that command is read-only and does not modify settings file."""
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            # Read original file content
            with open(settings_path, "r") as f:
                original_content = f.read()
            
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            # Capture stdout to avoid polluting test output
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                exit_code = recipe_check(args)
            finally:
                sys.stdout = old_stdout
            
            # Read file content after command
            with open(settings_path, "r") as f:
                new_content = f.read()
            
            # Verify file was not modified
            assert original_content == new_content
        finally:
            Path(settings_path).unlink()

    def test_recipe_check_output_includes_summary(self):
        """Test that recipe-check CLI output includes summary."""
        # Create temporary settings file with valid settings
        settings_data = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "steps": 20,
            "cfg": 7.0,
            "width": 480,
            "height": 640,
            "batch_size": 2,
            "negative_prompt": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            from io import StringIO
            import sys
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            args = Namespace(
                settings=settings_path,
                task_type="storyboard_keyframes",
                hardware="gtx_1060_5gb",
                project_profile=None,
                json=True,
            )
            
            exit_code = recipe_check(args)
            
            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            assert exit_code == 0
            output_dict = json.loads(output)
            
            # Verify summary is present
            assert "summary" in output_dict
            assert "title" in output_dict["summary"]
            assert "risk_level" in output_dict["summary"]
            assert "operator_message" in output_dict["summary"]
            assert "top_reasons" in output_dict["summary"]
            assert "recommended_next_action" in output_dict["summary"]
            
            # Verify pass verdict produces correct summary
            assert output_dict["summary"]["title"] == "Recipe ready"
            assert output_dict["summary"]["risk_level"] == "low"
        finally:
            Path(settings_path).unlink()
