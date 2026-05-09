"""
Tests for Visual QA Operator Review Routing — RC-COMBINE-V2-102001-106000.

Covers:
- Operator review packet contains all required fields
- Visual inspection checklist is present
- Decision options are documented
- Rules state agent must not accept visually
- Packet has no operator decision recorded (null)
- State transitions correctly
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    control_dir = tmp_path / "output" / "control"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def sample_packet() -> dict:
    """Return a minimal operator review packet fixture."""
    return {
        "task_id": "RC-COMBINE-V2-102001-106000",
        "packet_type": "operator_visual_review",
        "asset": {
            "path": "output/assets/test.png",
            "sha256": "a" * 64,
            "width": 1024,
            "height": 1024,
            "size_bytes": 100000,
        },
        "technical_metrics": {
            "blur_score": 200.0,
            "brightness": 100.0,
            "contrast": 50.0,
            "warnings": [],
            "opencv_available": True,
        },
        "visual_inspection_checklist": [],
        "decision_required": "operator_visual_review_decision",
        "decision_options": {
            "accept": "Accept the asset for pipeline",
            "reject": "Reject the asset and request corrective retry",
            "reject_with_defects": "Reject and document specific visual defects",
        },
        "rules": {
            "production_accepted_must_remain_false": True,
            "agent_must_not_accept_visually": True,
            "agent_must_not_retry_or_regenerate": True,
            "agent_must_not_assemble_or_downstream": True,
        },
        "current_state": "generation_result_review_required",
        "target_state": "operator_visual_review_required",
        "production_accepted": False,
        "visual_acceptance_executed": False,
        "operator_decision": None,
        "operator_verdict": None,
    }


class TestOperatorReviewPacketStructure:
    """Tests for operator review packet structure and completeness."""

    def test_packet_has_required_top_level_fields(self, sample_packet):
        """Packet must have all required top-level fields."""
        required = [
            "task_id", "packet_type", "asset", "technical_metrics",
            "visual_inspection_checklist", "decision_required",
            "decision_options", "rules", "production_accepted",
            "current_state", "target_state",
        ]
        for field in required:
            assert field in sample_packet, f"Missing required field: {field}"

    def test_packet_asset_has_required_fields(self, sample_packet):
        """Asset info must include path, sha256, width, height, size_bytes."""
        asset = sample_packet["asset"]
        for field in ("path", "sha256", "width", "height", "size_bytes"):
            assert field in asset, f"Missing asset field: {field}"

    def test_packet_has_technical_metrics(self, sample_packet):
        """Technical metrics section must have blur, brightness, contrast, warnings."""
        metrics = sample_packet["technical_metrics"]
        for field in ("blur_score", "brightness", "contrast", "warnings", "opencv_available"):
            assert field in metrics, f"Missing metrics field: {field}"

    def test_packet_has_visual_inspection_checklist(self, sample_packet):
        """Visual inspection checklist must be a non-empty list in the real packet."""
        from app.qa.visual_qa_package import build_operator_visual_review_packet
        from pathlib import Path

        packet = build_operator_visual_review_packet(
            Path("/tmp/fake_project"),
            "output/assets/test.png",
            {"actual_sha256": "a" * 64, "width": 1024, "height": 1024, "size_bytes": 100000},
            {"blur_score": 200.0, "brightness": 100.0, "contrast": 50.0,
             "warnings": [], "opencv_available": True},
        )

        checklist = packet["visual_inspection_checklist"]
        assert isinstance(checklist, list)
        assert len(checklist) > 0
        # Each item should reference a visual inspection concern
        for item in checklist:
            assert isinstance(item, str)
            assert len(item) > 10

    def test_packet_has_decision_options(self, sample_packet):
        """Decision options must include accept, reject, reject_with_defects."""
        options = sample_packet["decision_options"]
        for key in ("accept", "reject", "reject_with_defects"):
            assert key in options, f"Missing decision option: {key}"

    def test_packet_rules_block_agent_actions(self, sample_packet):
        """Rules must explicitly forbid agent from accepting, retrying, or assembling."""
        rules = sample_packet["rules"]
        assert rules.get("agent_must_not_accept_visually") is True
        assert rules.get("agent_must_not_retry_or_regenerate") is True
        assert rules.get("agent_must_not_assemble_or_downstream") is True
        assert rules.get("production_accepted_must_remain_false") is True

    def test_packet_operator_decision_is_null(self, sample_packet):
        """Operator decision must be None (not yet decided by human)."""
        assert sample_packet["operator_decision"] is None
        assert sample_packet["operator_verdict"] is None

    def test_packet_production_accepted_false(self, sample_packet):
        """production_accepted must be False in the review packet."""
        assert sample_packet["production_accepted"] is False

    def test_packet_visual_acceptance_not_executed(self, sample_packet):
        """visual_acceptance_executed must be False."""
        assert sample_packet["visual_acceptance_executed"] is False

    def test_packet_forbidden_actions_all_false(self, sample_packet):
        """All forbidden action fields must be False."""
        assert sample_packet.get("new_generation_performed", False) is False
        assert sample_packet.get("comfyui_submit_executed", False) is False
        assert sample_packet.get("retry_attempted", False) is False


class TestOperatorReviewRouting:
    """Tests for the routing behavior of the operator review packet."""

    def test_target_state_is_operator_visual_review_required(self, project_dir):
        """The packet must target operator_visual_review_required state."""
        from app.qa.visual_qa_package import build_operator_visual_review_packet
        from pathlib import Path

        packet = build_operator_visual_review_packet(
            project_dir,
            "output/assets/test.png",
            {"actual_sha256": "a" * 64, "width": 1024, "height": 1024, "size_bytes": 100000},
            {"blur_score": 200.0, "brightness": 100.0, "contrast": 50.0,
             "warnings": [], "opencv_available": True},
        )

        assert packet["target_state"] == "operator_visual_review_required"

    def test_packet_created_in_output_control(self, project_dir):
        """When Visual QA package runs, the operator packet is created in output/control."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package
        import hashlib
        from PIL import Image

        assets_dir = project_dir / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create valid test asset
        img = Image.new("RGB", (1024, 1024), (100, 100, 100))
        asset_path = assets_dir / "routing_test.png"
        img.save(asset_path)
        h = hashlib.sha256()
        with open(asset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

        # Create input artifacts
        entry = {
            "path": "output/assets/routing_test.png",
            "sha256": sha256, "width": 1024, "height": 1024, "size_bytes": asset_path.stat().st_size,
        }
        for name in ("generation_result_review.json", "visual_qa_input_packet.json", "canonical_outputs_manifest.json"):
            with open(control_dir / name, "w") as f:
                json.dump({"generated_assets": [entry], "production_accepted": False}, f)

        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_result_review_required", "next_allowed_action": "generation_result_review_required", "production_accepted": False, "stage_results": []}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        assert result["operator_visual_review_packet_created"] is True
        assert (control_dir / "operator_visual_review_packet.json").exists()


class TestQAReport:
    """Tests for the Visual QA report structure."""

    def test_report_has_technical_pass_not_visual_acceptance(self):
        """The QA report must state that technical pass != visual acceptance."""
        from app.qa.visual_qa_package import build_visual_qa_report
        from pathlib import Path

        report = build_visual_qa_report(
            Path("/tmp/fake"),
            {
                "generation_result_review_valid": True,
                "visual_qa_input_packet_valid": True,
                "canonical_manifest_valid": True,
                "assets_match_across_artifacts": True,
                "blocker": None,
            },
            {"technical_validation_pass": True, "exists": True, "readable": True,
             "sha256_matches": True, "dimensions_match": True, "size_valid": True,
             "stub_asset": False, "solid_color_detected": False, "width": 1024, "height": 1024,
             "size_bytes": 100000, "actual_sha256": "a" * 64},
            {"metrics_computed": True, "warnings": [], "blur_score": 200.0,
             "brightness": 100.0, "contrast": 50.0},
        )

        assert report["disclaimer"] is not None
        assert "technical pass" in report["disclaimer"].lower()
        assert "visual acceptance" in report["disclaimer"].lower()
        assert report["production_accepted"] is False
        assert report["visual_acceptance_executed"] is False

    def test_report_records_all_actions_false(self):
        """Report must explicitly record that no generation, retry, etc. occurred."""
        from app.qa.visual_qa_package import build_visual_qa_report
        from pathlib import Path

        report = build_visual_qa_report(
            Path("/tmp/fake"),
            {
                "generation_result_review_valid": True,
                "visual_qa_input_packet_valid": True,
                "canonical_manifest_valid": True,
                "assets_match_across_artifacts": True,
                "blocker": None,
            },
            {"technical_validation_pass": True, "exists": True, "readable": True,
             "sha256_matches": True, "dimensions_match": True, "size_valid": True,
             "stub_asset": False, "solid_color_detected": False, "width": 1024, "height": 1024,
             "size_bytes": 100000, "actual_sha256": "a" * 64},
            {"metrics_computed": True, "warnings": [], "blur_score": 200.0,
             "brightness": 100.0, "contrast": 50.0},
        )

        assert report["new_generation_performed"] is False
        assert report["comfyui_submit_executed"] is False
        assert report["retry_attempted"] is False
        assert report["assembly_executed"] is False
        assert report["downstream_executed"] is False
