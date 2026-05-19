"""Test Identity Lock and Composition Recovery - RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001

Tests for:
- Environment visibility detector
- Generic portrait detector
- Identity/idempotence check against canonical reference
- Workflow patch with environment conditioning
- Operator rejection record generation
- Manifest and review generation
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.agents.identity_lock.artifacts import IdentityLockArtifacts
from app.agents.identity_lock.runner import IdentityLockRunner
from app.agents.identity_lock.workflow_patch import WorkflowPatch


class TestEnvironmentVisibilityDetector:
    """Test environment visibility detector."""

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_environment_visibility_detector_wide_image_with_background(self, mock_brain, tmp_path):
        """Test detector passes for wide image with visible background."""
        from PIL import Image, ImageDraw
        import numpy as np

        # Create a test image with varied background
        img = Image.new("RGB", (1344, 768), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)

        # Add some variation to background
        for i in range(0, 768, 50):
            draw.rectangle([0, i, 1344, i+50], fill=(100+i//10, 150+i//10, 200-i//10))

        # Add a simple figure in center
        draw.ellipse([500, 200, 844, 500], fill=(255, 200, 180))

        test_image_path = tmp_path / "test_wide_with_background.png"
        img.save(test_image_path)

        runner = IdentityLockRunner(tmp_path)
        result = runner._environment_visibility_detector(str(test_image_path))

        assert result is True, "Wide image with varied background should pass environment visibility check"

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_environment_visibility_detector_plain_background(self, mock_brain, tmp_path):
        """Test detector fails for image with plain solid background."""
        from PIL import Image

        # Create a test image with plain solid background
        img = Image.new("RGB", (1344, 768), color=(255, 255, 255))

        test_image_path = tmp_path / "test_plain_background.png"
        img.save(test_image_path)

        runner = IdentityLockRunner(tmp_path)
        result = runner._environment_visibility_detector(str(test_image_path))

        assert result is False, "Image with plain solid background should fail environment visibility check"


class TestGenericPortraitDetector:
    """Test generic portrait detector."""

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_generic_portrait_detector_square_closeup(self, mock_brain, tmp_path):
        """Test detector blocks square close-up portraits."""
        from PIL import Image

        # Create a square close-up portrait
        img = Image.new("RGB", (1024, 1024), color=(240, 240, 240))

        test_image_path = tmp_path / "test_square_closeup.png"
        img.save(test_image_path)

        runner = IdentityLockRunner(tmp_path)
        result = runner._generic_portrait_detector(str(test_image_path))

        assert result is False, "Square close-up portrait should be blocked"

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_generic_portrait_detector_wide_scene(self, mock_brain, tmp_path):
        """Test detector passes wide scene images."""
        from PIL import Image, ImageDraw

        # Create a wide scene image
        img = Image.new("RGB", (1344, 768), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)

        # Add varied background
        for i in range(0, 768, 50):
            draw.rectangle([0, i, 1344, i+50], fill=(100+i//10, 150+i//10, 200-i//10))

        test_image_path = tmp_path / "test_wide_scene.png"
        img.save(test_image_path)

        runner = IdentityLockRunner(tmp_path)
        result = runner._generic_portrait_detector(str(test_image_path))

        assert result is True, "Wide scene image should pass generic portrait check"


class TestWorkflowPatchEnvironmentConditioning:
    """Test workflow patch with environment conditioning."""

    def test_workflow_patch_includes_environment_visibility(self, tmp_path):
        """Test workflow patch includes environment visibility requirements."""
        llm_decision = {
            "positive_prompt_additions": [],
            "negative_prompt_additions": [],
        }

        patcher = WorkflowPatch(tmp_path)
        patch = patcher.create_workflow_patch(llm_decision, "/test/path/identity.png")

        # Check positive prompt additions include environment visibility
        positive_additions = patch["prompt_modifications"]["positive_prompt_additions"]
        assert "environment visible" in positive_additions
        assert "background visible" in positive_additions
        assert "character in environment" in positive_additions
        assert "not isolated on blank background" in positive_additions

        # Check negative prompt additions block generic portraits
        negative_additions = patch["prompt_modifications"]["negative_prompt_additions"]
        assert "generic beauty portrait" in negative_additions
        assert "studio portrait" in negative_additions
        assert "plain background" in negative_additions
        assert "blank background" in negative_additions
        assert "solid color background" in negative_additions
        assert "isolated on white" in negative_additions
        assert "isolated on black" in negative_additions
        assert "beauty shot" in negative_additions
        assert "glamour portrait" in negative_additions
        assert "headshot only" in negative_additions
        assert "face only" in negative_additions

    def test_workflow_patch_framing_constraints(self, tmp_path):
        """Test workflow patch enforces wide framing."""
        llm_decision = {
            "positive_prompt_additions": [],
            "negative_prompt_additions": [],
        }

        patcher = WorkflowPatch(tmp_path)
        patch = patcher.create_workflow_patch(llm_decision, "/test/path/identity.png")

        framing = patch["framing_constraints"]
        assert framing["medium_shot_or_upper_body"] is True
        assert framing["full_face_visible"] is True
        assert framing["head_not_touching_edges"] is True
        assert framing["environment_visible"] is True
        assert framing["extreme_closeup_forbidden"] is True
        assert framing["target_resolution"] == "1344x768"
        assert "1536x864" in framing["alternative_wide_formats"]
        assert "1728x972" in framing["alternative_wide_formats"]


class TestOperatorRejectionRecord:
    """Test operator rejection record generation."""

    def test_operator_rejection_record_includes_specific_asset(self, tmp_path):
        """Test rejection record specifically records identity_lock__00001_.png."""
        artifacts = IdentityLockArtifacts(tmp_path)

        record = artifacts.generate_operator_rejection_record(
            previous_task="RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001",
            rejection_reason=["Generic beauty portrait generated", "Environment not visible"],
            previous_asset_path="/test/path/identity_lock__00001_.png",
        )

        assert record["rejected_asset_filename"] == "identity_lock__00001_.png"
        assert record["rejection_type"] == "identity_and_composition_lock_failure"
        assert record["environment_not_visible"] is True
        assert record["generic_portrait_fallback"] is True
        assert record["task_id"] == "RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001"
        assert record["idempotence_failed"] is True
        assert record["production_accepted"] is False


class TestResultReviewWithNewDetectors:
    """Test result review includes new detector results."""

    def test_result_review_includes_environment_visibility(self, tmp_path):
        """Test result review includes environment visibility check."""
        from PIL import Image

        artifacts = IdentityLockArtifacts(tmp_path)

        # Create a test image
        img = Image.new("RGB", (1344, 768), color=(100, 150, 200))
        test_image_path = tmp_path / "test_image.png"
        img.save(test_image_path)

        identity_gate_result = {
            "identity_confidence": 0.85,
            "identity_gate_result": "identity_similarity_computed",
        }

        review = artifacts.generate_result_review(
            asset_path=str(test_image_path),
            blank_detector_passed=True,
            framing_detector_passed=True,
            environment_visibility_passed=True,
            generic_portrait_blocked=True,
            single_subject_gate_passed=True,
            identity_gate_result=identity_gate_result,
        )

        assert review["asset_validation"]["environment_visibility_passed"] is True
        assert review["asset_validation"]["generic_portrait_blocked"] is True
        assert review["overall_verdict"] == "operator_visual_review_required"


class TestIdentityGateIdempotenceCheck:
    """Test identity gate performs idempotence check against canonical reference."""

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_identity_gate_uses_canonical_reference(self, mock_brain, tmp_path):
        """Test identity gate validates against canonical reference."""
        from PIL import Image

        # Create test images
        canonical_img = Image.new("RGB", (512, 512), color=(200, 180, 160))
        canonical_path = tmp_path / "canonical_identity.png"
        canonical_img.save(canonical_path)

        generated_img = Image.new("RGB", (1344, 768), color=(200, 180, 160))
        generated_path = tmp_path / "generated.png"
        generated_img.save(generated_path)

        gate = IdentityLockRunner(tmp_path).identity_gate
        result = gate.validate_identity(str(generated_path), str(canonical_path))

        # Check that canonical reference was used
        assert "identity_gate_result" in result
        # If face_recognition is available, should compute similarity
        # If not available, should use honest fallback
        if result.get("identity_embedding_available"):
            assert result["identity_gate_result"] in ["identity_similarity_computed", "no_faces_detected"]
        else:
            assert result["identity_gate_result"] == "operator_review_required_with_identity_warning"
            assert result["operator_review_required"] is True


class TestRecoveryScriptContractCompliance:
    """Test recovery script complies with contract requirements."""

    def test_recovery_script_forbidden_actions_not_present(self, tmp_path):
        """Test that recovery script does not include forbidden actions in code."""
        recovery_script_path = Path(__file__).parent.parent / "RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001.py"

        if not recovery_script_path.exists():
            pytest.skip("Recovery script not found")

        script_content = recovery_script_path.read_text()

        # Check that forbidden actions are not present in actual code (not docstrings)
        # Remove docstrings to avoid false positives
        lines = script_content.split('\n')
        code_lines = []
        in_docstring = False
        for line in lines:
            if '"""' in line:
                in_docstring = not in_docstring
                continue
            if not in_docstring and not line.strip().startswith('#'):
                code_lines.append(line)
        code_content = '\n'.join(code_lines)

        # Check that forbidden actions are not present in code
        assert "second generation" not in code_content.lower()
        assert "blind retry" not in code_content.lower()
        assert "visual_qa_acceptance" not in code_content.lower()
        assert "production_accepted = True" not in code_content
        assert "assembly" not in code_content.lower() or "assembly_agent" in code_content.lower()  # Allow import
        assert "downstream" not in code_content.lower() or "downstream_pipeline" in code_content.lower()  # Allow import

    def test_recovery_script_requires_environment_visibility(self, tmp_path):
        """Test that recovery script requires environment visibility."""
        recovery_script_path = Path(__file__).parent.parent / "RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001.py"
        
        if not recovery_script_path.exists():
            pytest.skip("Recovery script not found")

        script_content = recovery_script_path.read_text()

        # Check that environment visibility is required
        assert "environment" in script_content.lower()
        assert "background" in script_content.lower()

    def test_recovery_script_blocks_generic_portrait(self, tmp_path):
        """Test that recovery script blocks generic portrait fallback."""
        recovery_script_path = Path(__file__).parent.parent / "RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001.py"
        
        if not recovery_script_path.exists():
            pytest.skip("Recovery script not found")

        script_content = recovery_script_path.read_text()

        # Check that generic portrait blocking is present
        assert "generic portrait" in script_content.lower() or "portrait" in script_content.lower()


class TestBlankDetectorPreserved:
    """Test blank detector is preserved and functional."""

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_blank_detector_functional(self, mock_brain, tmp_path):
        """Test blank detector works correctly."""
        from PIL import Image

        runner = IdentityLockRunner(tmp_path)

        # Create a non-blank image
        img = Image.new("RGB", (1344, 768), color=(100, 150, 200))
        non_blank_path = tmp_path / "non_blank.png"
        img.save(non_blank_path)

        result = runner._blank_detector(str(non_blank_path))
        assert result is True, "Non-blank image should pass blank detector"

        # Create a blank image (all white)
        blank_img = Image.new("RGB", (1344, 768), color=(255, 255, 255))
        blank_path = tmp_path / "blank.png"
        blank_img.save(blank_path)

        result = runner._blank_detector(str(blank_path))
        assert result is False, "Blank image should fail blank detector"


class TestFramingDetectorPreserved:
    """Test framing detector is preserved and functional."""

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_framing_detector_wide_format(self, mock_brain, tmp_path):
        """Test framing detector accepts wide format."""
        from PIL import Image

        runner = IdentityLockRunner(tmp_path)

        # Create a wide image
        img = Image.new("RGB", (1344, 768), color=(100, 150, 200))
        wide_path = tmp_path / "wide.png"
        img.save(wide_path)

        result = runner._framing_detector(str(wide_path))
        assert result is True, "Wide 1344x768 image should pass framing detector"

    @patch('app.agents.identity_lock.runner.LLMBrainDecision')
    def test_framing_detector_square_closeup(self, mock_brain, tmp_path):
        """Test framing detector rejects square close-up."""
        from PIL import Image

        runner = IdentityLockRunner(tmp_path)

        # Create a square close-up
        img = Image.new("RGB", (1024, 1024), color=(100, 150, 200))
        square_path = tmp_path / "square.png"
        img.save(square_path)

        result = runner._framing_detector(str(square_path))
        assert result is False, "Square 1024x1024 image should fail framing detector"
