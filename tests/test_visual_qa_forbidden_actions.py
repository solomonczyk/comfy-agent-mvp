"""
Tests for Visual QA Forbidden Actions — RC-COMBINE-V2-102001-106000.

Verifies that the Visual QA package does NOT:
- new_generation_performed
- comfyui_submit_executed
- retry_attempted
- visual_acceptance_executed
- operator_visual_decision_made_by_agent
- preview_render_executed
- assembly_executed
- downstream_executed
- production_accepted set to True

Also verifies state machine forbids certain transitions from generation_result_review_required.
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    (tmp_path / "output" / "control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "assets").mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestForbiddenActionsInOutput:
    """Tests that forbidden actions are never set in output artifacts."""

    def test_new_generation_not_performed(self, project_dir):
        """New generation must not be performed by the Visual QA package."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package
        import hashlib
        from PIL import Image

        assets_dir = project_dir / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (1024, 1024), (100, 100, 100))
        asset_path = assets_dir / "test.png"
        img.save(asset_path)
        h = hashlib.sha256()
        with open(asset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

        entry = {"path": "output/assets/test.png", "sha256": sha256, "width": 1024,
                 "height": 1024, "size_bytes": asset_path.stat().st_size}
        for name in ("generation_result_review.json", "visual_qa_input_packet.json", "canonical_outputs_manifest.json"):
            with open(control_dir / name, "w") as f:
                json.dump({"generated_assets": [entry], "production_accepted": False}, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_result_review_required", "next_allowed_action":
                       "generation_result_review_required", "production_accepted": False, "stage_results": []}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        result = run_generated_asset_visual_qa_package(str(project_dir))

        # All forbidden actions must be False
        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["retry_attempted"] is False
        assert result["visual_acceptance_executed"] is False
        assert result["operator_visual_decision_made_by_agent"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_visual_qa_report_has_forbidden_false(self, project_dir):
        """visual_qa_report.json must have all forbidden action fields set to False."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package
        import hashlib
        from PIL import Image

        assets_dir = project_dir / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (1024, 1024), (100, 100, 100))
        asset_path = assets_dir / "test2.png"
        img.save(asset_path)
        h = hashlib.sha256()
        with open(asset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

        entry = {"path": "output/assets/test2.png", "sha256": sha256, "width": 1024,
                 "height": 1024, "size_bytes": asset_path.stat().st_size}
        for name in ("generation_result_review.json", "visual_qa_input_packet.json", "canonical_outputs_manifest.json"):
            with open(control_dir / name, "w") as f:
                json.dump({"generated_assets": [entry], "production_accepted": False}, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_result_review_required", "next_allowed_action":
                       "generation_result_review_required", "production_accepted": False, "stage_results": []}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        run_generated_asset_visual_qa_package(str(project_dir))

        with open(control_dir / "visual_qa_report.json") as f:
            report = json.load(f)

        forbidden_fields = [
            "new_generation_performed",
            "comfyui_submit_executed",
            "retry_attempted",
            "assembly_executed",
            "downstream_executed",
        ]
        for field in forbidden_fields:
            assert report.get(field) is False, f"{field} must be False in report"

        assert report.get("production_accepted") is False
        assert report.get("visual_acceptance_executed") is False

    def test_operator_packet_has_forbidden_false(self, project_dir):
        """operator_visual_review_packet.json must have all forbidden fields set to False."""
        # Same setup as above - run once and check packet
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package
        import hashlib
        from PIL import Image

        assets_dir = project_dir / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (1024, 1024), (100, 100, 100))
        asset_path = assets_dir / "test3.png"
        img.save(asset_path)
        h = hashlib.sha256()
        with open(asset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

        entry = {"path": "output/assets/test3.png", "sha256": sha256, "width": 1024,
                 "height": 1024, "size_bytes": asset_path.stat().st_size}
        for name in ("generation_result_review.json", "visual_qa_input_packet.json", "canonical_outputs_manifest.json"):
            with open(control_dir / name, "w") as f:
                json.dump({"generated_assets": [entry], "production_accepted": False}, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_result_review_required", "next_allowed_action":
                       "generation_result_review_required", "production_accepted": False, "stage_results": []}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        run_generated_asset_visual_qa_package(str(project_dir))

        with open(control_dir / "operator_visual_review_packet.json") as f:
            packet = json.load(f)

        assert packet.get("production_accepted") is False
        assert packet.get("new_generation_performed", False) is False
        assert packet.get("comfyui_submit_executed", False) is False
        assert packet.get("retry_attempted", False) is False

    def test_artifact_index_has_forbidden_false(self, project_dir):
        """artifact_index.json must have forbidden actions set to False."""
        from app.qa.visual_qa_package import run_generated_asset_visual_qa_package
        import hashlib
        from PIL import Image

        assets_dir = project_dir / "output" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        control_dir = project_dir / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (1024, 1024), (100, 100, 100))
        asset_path = assets_dir / "test4.png"
        img.save(asset_path)
        h = hashlib.sha256()
        with open(asset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

        entry = {"path": "output/assets/test4.png", "sha256": sha256, "width": 1024,
                 "height": 1024, "size_bytes": asset_path.stat().st_size}
        for name in ("generation_result_review.json", "visual_qa_input_packet.json", "canonical_outputs_manifest.json"):
            with open(control_dir / name, "w") as f:
                json.dump({"generated_assets": [entry], "production_accepted": False}, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_result_review_required", "next_allowed_action":
                       "generation_result_review_required", "production_accepted": False, "stage_results": []}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        run_generated_asset_visual_qa_package(str(project_dir))

        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx.get("production_accepted") is False
        assert idx.get("visual_acceptance_executed") is False
        assert idx.get("new_generation_performed") is False
        assert idx.get("retry_attempted") is False
        assert idx.get("comfyui_submit_executed") is False


class TestStateMachineForbiddenTransitions:
    """Tests that the state machine correctly forbids unsafe transitions."""

    def test_forbidden_generation_transition(self):
        """generation_result_review_required cannot transition to generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "generate_assets"
        )

    def test_forbidden_real_generation_transition(self):
        """generation_result_review_required cannot transition to real_generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "real_generate_assets"
        )

    def test_forbidden_assembly_transition(self):
        """generation_result_review_required cannot transition to assembly_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "assembly_required"
        )

    def test_forbidden_qa_transition(self):
        """generation_result_review_required cannot transition to visual_qa_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "visual_qa_required"
        )

    def test_forbidden_retry_transition(self):
        """generation_result_review_required cannot transition to corrective_retry_plan_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "corrective_retry_plan_required"
        )

    def test_forbidden_retry_correction_transition(self):
        """generation_result_review_required cannot transition to retry_correction_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "retry_correction_required"
        )

    def test_forbidden_completed_transition(self):
        """generation_result_review_required cannot transition to completed."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "completed"
        )

    def test_forbidden_production_accepted_transition(self):
        """generation_result_review_required cannot transition to production_accepted."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "generation_result_review_required", "production_accepted"
        )

    def test_allowed_operator_visual_review_transition(self):
        """generation_result_review_required CAN transition to operator_visual_review_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.can_transition(
            "generation_result_review_required", "operator_visual_review_required"
        )

    def test_allowed_self_loop_transition(self):
        """generation_result_review_required can self-loop (stay in same state)."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.can_transition(
            "generation_result_review_required", "generation_result_review_required"
        )

    def test_allowed_blocked_manual_review_transition(self):
        """generation_result_review_required can transition to blocked_manual_review."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.can_transition(
            "generation_result_review_required", "blocked_manual_review"
        )

    def test_invalid_from_state(self):
        """An invalid from_state returns False from can_transition."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "nonexistent_state", "operator_visual_review_required"
        )

    def test_new_state_is_valid(self):
        """generation_result_review_required must be a valid state."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.is_valid_state("generation_result_review_required")


class TestForbiddenActionsInModule:
    """Tests that the module-level forbidden action constants are correct."""

    def test_forbidden_actions_not_in_function(self):
        """The run_generated_asset_visual_qa_package function must not set forbidden actions to True."""
        import inspect
        from app.qa import visual_qa_package

        source = inspect.getsource(visual_qa_package.run_generated_asset_visual_qa_package)

        # These patterns should NOT appear in the function (as True assignments)
        forbidden_patterns = [
            "new_generation_performed = True",
            "comfyui_submit_executed = True",
            "retry_attempted = True",
            "visual_acceptance_executed = True",
            "assembly_executed = True",
            "downstream_executed = True",
            "production_accepted = True",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Found forbidden pattern in function: {pattern}"
