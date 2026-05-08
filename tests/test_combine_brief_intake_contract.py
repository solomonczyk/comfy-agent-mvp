"""Tests for Brief Intake data contract and schema."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from app.brief.intake import (
    BriefIntakeData,
    ProjectConstraints,
    ContentIntent,
    SuccessCriteria,
    ForbiddenActions,
    build_brief_intake,
)


class TestBriefIntakeData:
    """Test the BriefIntakeData dataclass schema."""

    def test_defaults(self):
        """Default instance has safe defaults."""
        data = BriefIntakeData()
        assert data.production_accepted is False
        assert data.operator_review_required is True
        assert data.content_type == "unknown"
        assert data.language == "en"
        assert data.missing_fields == []
        assert data.forbidden_actions == []
        assert data.success_criteria == []

    def test_to_dict_includes_all_fields(self):
        """to_dict() returns all expected fields."""
        data = BriefIntakeData(
            project_id="test_project",
            source_input="Create a video",
            normalized_task_summary="Create a video",
            content_type="educational",
        )
        d = data.to_dict()
        assert d["project_id"] == "test_project"
        assert d["source_input"] == "Create a video"
        assert d["content_type"] == "educational"
        assert d["production_accepted"] is False
        assert d["operator_review_required"] is True
        assert d["readiness_for_director_planner"] is False

    def test_minimal_valid_contract_fields(self):
        """A minimally valid contract has all fields expected by DirectorPlannerAgent."""
        contract = BriefIntakeData(
            project_id="rc2_multishot1_ep01",
            source_input="Create an educational video about AI",
            normalized_task_summary="Create an educational video about AI",
            content_type="educational",
            target_audience="beginners",
            goal="Create an educational video explaining AI concepts",
            expected_output="short educational video",
            language="en",
            readiness_for_director_planner=True,
        )
        required_for_director = [
            "project_id",
            "source_input",
            "normalized_task_summary",
            "content_type",
            "target_audience",
            "goal",
            "expected_output",
            "language",
            "readiness_for_director_planner",
            "operator_review_required",
            "production_accepted",
        ]
        d = contract.to_dict()
        for field in required_for_director:
            assert field in d, f"Missing field required by DirectorPlannerAgent: {field}"


class TestProjectConstraints:
    """Test the ProjectConstraints dataclass."""

    def test_defaults(self):
        c = ProjectConstraints()
        assert c.language == "en"
        assert c.constraints == []
        assert c.technical_restrictions == []

    def test_to_dict(self):
        c = ProjectConstraints(
            duration_target="30 seconds",
            format_hint="16:9",
            language="en",
            style_tone="professional",
        )
        d = c.to_dict()
        assert d["duration_target"] == "30 seconds"
        assert d["format_hint"] == "16:9"


class TestContentIntent:
    """Test the ContentIntent dataclass."""

    def test_defaults(self):
        ci = ContentIntent()
        assert ci.content_type == "unknown"
        assert ci.secondary_purposes == []

    def test_to_dict(self):
        ci = ContentIntent(
            content_type="educational",
            goal="Explain AI pipeline",
            target_audience="beginners",
            expected_output="explainer video",
        )
        d = ci.to_dict()
        assert d["content_type"] == "educational"
        assert d["goal"] == "Explain AI pipeline"


class TestSuccessCriteria:
    """Test the SuccessCriteria dataclass."""

    def test_defaults(self):
        sc = SuccessCriteria()
        assert sc.criteria == []
        assert sc.generated_defaults is False

    def test_to_dict(self):
        sc = SuccessCriteria(
            criteria=["Asset is valid", "Content matches intent"],
            generated_defaults=True,
        )
        d = sc.to_dict()
        assert len(d["criteria"]) == 2


class TestForbiddenActions:
    """Test the ForbiddenActions dataclass."""

    def test_default_blocked(self):
        fa = ForbiddenActions()
        assert fa.generation_blocked is True
        assert fa.comfyui_submit_blocked is True
        assert fa.assembly_blocked is True
        assert fa.downstream_blocked is True
        assert fa.production_acceptance_blocked is True

    def test_to_dict(self):
        fa = ForbiddenActions(
            forbidden_actions=["generation_without_review"],
            dangerous_actions_blocked=["skip_review"],
        )
        d = fa.to_dict()
        assert "generation_without_review" in d["forbidden_actions"]
        assert "skip_review" in d["dangerous_actions_blocked"]


class TestBuildBriefIntakeArtifacts:
    """Test that build_brief_intake creates all expected artifacts."""

    def _run_build(self, input_text: str, project_root: str | None = None) -> dict:
        if project_root is None:
            project_root = str(Path(tempfile.mkdtemp()))
        return build_brief_intake(project_root, input_text)

    def test_valid_educational_brief_creates_all_artifacts(self):
        """A valid brief creates all 6 canonical artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_build(
                "Create a short educational explainer video about AI pipeline. "
                "Target audience is beginners. Style should be clear and practical.",
                tmpdir,
            )
            assert result["brief_contract_created"] is True
            assert len(result["artifacts_created"]) == 6

            # Verify files exist on disk
            for artifact in result["artifacts_created"]:
                assert Path(tmpdir, artifact).exists(), f"Missing artifact: {artifact}"

    def test_contract_json_has_correct_fields(self):
        """The brief_contract.json has all expected fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create a promotional video for a product launch targeting professionals.")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            assert contract_path.exists()
            with open(contract_path) as f:
                contract = json.load(f)
            assert contract["project_id"] == Path(tmpdir).name
            assert contract["content_type"] == "promotional"
            assert contract["production_accepted"] is False
            assert contract["operator_review_required"] is True
            assert "goal" in contract
            assert "expected_output" in contract
            assert "forbidden_actions" in contract
            assert "success_criteria" in contract
            assert "missing_fields" in contract

    def test_content_type_inferred_correctly(self):
        """Content type is inferred from keywords."""
        test_cases = [
            ("Create an educational explainer about python", "educational"),
            ("Make a promotional advertisement for a product", "promotional"),
            ("Create an entertaining comedy sketch", "entertainment"),
            ("Make a documentary about space", "documentary"),
            ("Create a step by step tutorial", "tutorial"),
            ("Make a product showcase video", "product_visual"),
            ("Take a portrait photo", "portrait"),
            ("Tell a cinematic story", "narrative"),
            ("Create a short social media reel", "social_media"),
        ]
        for text, expected_type in test_cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                build_brief_intake(tmpdir, text)
                contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
                with open(contract_path) as f:
                    contract = json.load(f)
                assert contract["content_type"] == expected_type, f"For '{text}': expected {expected_type}, got {contract['content_type']}"

    def test_target_audience_inferred(self):
        """Target audience is inferred from keywords."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create a tutorial for beginners who are new to AI")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert contract["target_audience"] == "beginners"

    def test_duration_extracted(self):
        """Duration target is extracted from text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create a 30 second explainer video")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert contract["duration_target"] is not None
            assert "30" in contract["duration_target"]

    def test_format_extracted(self):
        """Format/aspect ratio is extracted from text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create a vertical 9:16 video for TikTok")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert contract["format_hint"] is not None

    def test_forbidden_actions_always_present(self):
        """Forbidden actions are always present in the contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create any video")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert len(contract["forbidden_actions"]) >= 7
            assert "generation_without_operator_authorization" in contract["forbidden_actions"]
            assert "comfyui_submit" in contract["forbidden_actions"]
            assert "production_acceptance" in contract["forbidden_actions"]

    def test_success_criteria_have_defaults(self):
        """Success criteria have sensible defaults when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(tmpdir, "Create an educational video")
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert len(contract["success_criteria"]) >= 3

    def test_production_accepted_false(self):
        """production_accepted is always false in brief intake."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result["production_accepted"] is False
            contract_path = Path(tmpdir, "output/control/brief/brief_contract.json")
            with open(contract_path) as f:
                contract = json.load(f)
            assert contract["production_accepted"] is False

    def test_generation_not_performed(self):
        """generation_performed is false in build result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Create any video")
            assert result["generation_performed"] is False
            assert result["comfyui_submit_executed"] is False
            assert result["assembly_executed"] is False
            assert result["downstream_executed"] is False
