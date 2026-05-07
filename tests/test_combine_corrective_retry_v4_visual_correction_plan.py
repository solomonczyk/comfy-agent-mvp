"""Tests for RC-COMBINE-V2-2601-2660: Corrective Retry V4 Visual Correction Plan

This test module validates the combine-build-corrective-retry-v4-visual-correction-plan command
and its associated artifacts and state transitions.

Test coverage includes:
- Requires failed visual QA verdict
- Missing verdict blocked
- Passed verdict does not create retry plan
- Failed reasons mapped to corrections
- Subject scale requirements created
- Empty space requirements created
- Composition requirements created
- Shot intent requirements created
- Prompt patch recommendations created
- Operator review packet created
- No generation
- No ComfyUI submit
- No retry execution
- No assembly
- No downstream
- Production accepted false
- Next allowed action not none
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock

from app.orchestrator.state_machine import CombineStateMachine


class TestCorrectiveRetryV4VisualCorrectionPlan:
    """Test suite for V4 Visual Correction Plan"""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing"""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        control_dir = project_root / "output" / "control"
        assets_dir = project_root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)

        yield project_root

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def failed_verdict(self):
        """Create a failed Visual QA verdict fixture"""
        return {
            "task_id": "RC-COMBINE-V2-2541-2600",
            "stage": "corrective_retry_v4_visual_qa_required",
            "verdict_type": "corrective_retry_v4_visual_qa_verdict",
            "shot_id": "shot02",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "visual_qa_executed": True,
            "visual_qa_verdict": "failed",
            "production_accepted": False,
            "asset_path": "F:\\test\\output\\assets\\combine_v2_corrective_retry_v4_shot02_00001_.png",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
            "sha256_expected": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
            "sha256_match": True,
            "width": 1344,
            "height": 768,
            "file_size_bytes": 1054825,
            "checks": {
                "subject_scale_check": {"status": "failed", "message": "Subject too small - operator concern"},
                "empty_space_check": {"status": "failed", "message": "Excessive empty space - operator concern"},
                "composition_check": {"status": "failed", "message": "Weak composition - operator concern"},
                "shot_intent_alignment_check": {"status": "failed", "message": "Shot intent not satisfied - operator concern"},
                "prompt_scene_alignment_check": {"status": "failed", "message": "Prompt/scene alignment weak - operator concern"},
                "technical_readability_check": {"status": "passed", "message": "Asset readable"},
                "production_quality_check": {"status": "failed", "message": "Production quality issues detected: 5"}
            },
            "failed_reasons": [
                "subject_scale_check",
                "empty_space_check",
                "composition_check",
                "shot_intent_alignment_check",
                "prompt_scene_alignment_check",
                "production_quality_check",
                "subject_too_small",
                "excessive_empty_space",
                "weak_composition",
                "shot_intent_not_satisfied",
                "prompt_scene_alignment_weak"
            ],
            "operator_concerns_preserved": True,
            "known_visual_issues": [
                "subject_too_small",
                "excessive_empty_space",
                "weak_composition",
                "shot_intent_not_satisfied",
                "prompt_scene_alignment_weak"
            ],
            "operator_visual_concerns": {
                "subject_too_small": True,
                "excessive_empty_space": True,
                "weak_composition": True,
                "shot_intent_not_satisfied": True,
                "prompt_scene_alignment_weak": True
            },
            "recommended_next_action": "corrective_retry_v4_visual_correction_plan_required",
            "requires_operator_review": True,
            "generation_performed": False,
            "comfyui_execution": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False
        }

    @pytest.fixture
    def input_packet(self):
        """Create a Visual QA input packet fixture"""
        return {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
            "file_size_bytes": 1054825,
            "width": 1344,
            "height": 768,
            "source_manifest_path": "output/control/combine_v2_corrective_retry_v4_outputs_manifest.json",
            "source_result_review_path": "output/control/combine_v2_corrective_retry_v4_result_review.json",
            "technical_validation": {
                "asset_exists": True,
                "asset_readable": True,
                "asset_size_bytes": 1054825,
                "asset_size_bytes_gt_1024": True,
                "sha256_present": True,
                "sha256": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
                "width_present": True,
                "height_present": True,
                "dimensions_valid": True,
                "stub_asset_detected": False,
                "canonical_asset_used": True,
                "old_shot01_asset_used": False,
                "stale_stub_asset_used": False,
                "manifest_asset_matches_canonical_asset": True,
                "result_review_success_branch_used": True
            },
            "operator_visual_concerns": {
                "subject_too_small": True,
                "excessive_empty_space": True,
                "weak_composition": True,
                "shot_intent_not_satisfied": True,
                "prompt_scene_alignment_weak": True
            },
            "known_visual_issues": [
                "subject_too_small",
                "excessive_empty_space",
                "weak_composition",
                "shot_intent_not_satisfied",
                "prompt_scene_alignment_weak"
            ],
            "operator_visual_concerns_recorded": True,
            "full_visual_qa_verdict_executed": False,
            "operator_visual_review_executed": False,
            "generation_performed": False,
            "comfyui_execution": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False
        }

    def test_requires_failed_visual_qa_verdict(self, temp_project, failed_verdict, input_packet):
        """Test that command requires a failed Visual QA verdict"""
        control_dir = temp_project / "output" / "control"

        # Write required artifacts
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "corrective_retry_v4_visual_qa_required"}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        # Import and run the command
        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        result = combine_build_corrective_retry_v4_visual_correction_plan(args)

        assert result == 0, "Command should succeed with failed verdict"

        # Verify the plan was created
        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        assert plan_path.exists(), "Visual correction plan should be created"

        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["visual_qa_verdict"] == "failed"
        assert plan["visual_qa_verdict_used"] is True

    def test_missing_verdict_blocked(self, temp_project, input_packet):
        """Test that missing verdict blocks the command"""
        control_dir = temp_project / "output" / "control"

        # Write only input packet (no verdict)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        result = combine_build_corrective_retry_v4_visual_correction_plan(args)

        assert result == 1, "Command should fail with missing verdict"

        # Verify plan was NOT created
        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        assert not plan_path.exists(), "Plan should not be created when verdict missing"

    def test_passed_verdict_does_not_create_retry_plan(self, temp_project, failed_verdict, input_packet):
        """Test that passed verdict does not create retry plan"""
        control_dir = temp_project / "output" / "control"

        # Modify verdict to be "passed"
        passed_verdict = failed_verdict.copy()
        passed_verdict["visual_qa_verdict"] = "passed"
        passed_verdict["failed_reasons"] = []

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(passed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        result = combine_build_corrective_retry_v4_visual_correction_plan(args)

        assert result == 1, "Command should fail with passed verdict"

        # Verify plan was NOT created
        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        assert not plan_path.exists(), "Plan should not be created when verdict is passed"

    def test_failed_reasons_mapped_to_corrections(self, temp_project, failed_verdict, input_packet):
        """Test that failed reasons are properly mapped to corrections"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        correction_mapping = plan["correction_mapping"]

        assert "subject_too_small" in correction_mapping
        assert "excessive_empty_space" in correction_mapping
        assert "weak_composition" in correction_mapping
        assert "shot_intent_not_satisfied" in correction_mapping
        assert "prompt_scene_alignment_weak" in correction_mapping

    def test_subject_scale_requirements_created(self, temp_project, failed_verdict, input_packet):
        """Test that subject scale requirements are created correctly"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        subject_fix = plan["correction_mapping"]["subject_too_small"]
        assert subject_fix["target_subject_height_ratio"] == "0.40-0.60"
        assert subject_fix["minimum_subject_height_ratio"] == "0.30"
        assert "medium shot / medium-full shot" in subject_fix["recommended_shot_type"]

    def test_empty_space_requirements_created(self, temp_project, failed_verdict, input_packet):
        """Test that empty space requirements are created correctly"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        empty_space_fix = plan["correction_mapping"]["excessive_empty_space"]
        assert empty_space_fix["target_empty_space_ratio_max"] == "0.45"
        assert "tighter crop" in empty_space_fix["recommended_framing"].lower()

    def test_composition_requirements_created(self, temp_project, failed_verdict, input_packet):
        """Test that composition requirements are created correctly"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        composition_fix = plan["correction_mapping"]["weak_composition"]
        assert "rule-of-thirds" in composition_fix["techniques"]
        assert "cinematic subject-focused framing" in composition_fix["composition_target"]

    def test_shot_intent_requirements_created(self, temp_project, failed_verdict, input_packet):
        """Test that shot intent requirements are created correctly"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        intent_fix = plan["correction_mapping"]["shot_intent_not_satisfied"]
        assert "Character-focused" in intent_fix["shot_intent_restatement"]
        assert "generic landscape" in intent_fix["rejection_criteria"]

    def test_prompt_patch_recommendations_created(self, temp_project, failed_verdict, input_packet):
        """Test that prompt patch recommendations are created"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        retry_patch = plan["retry_prompt_patch"]
        assert len(retry_patch["positive_prompt_additions"]) > 0
        assert len(retry_patch["negative_prompt_additions"]) > 0
        assert "camera_framing_requirements" in retry_patch
        assert "subject_scale_requirements" in retry_patch
        assert "composition_requirements" in retry_patch
        assert "rejection_criteria" in retry_patch

    def test_operator_review_packet_created(self, temp_project, failed_verdict, input_packet):
        """Test that operator review packet is created"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        review_packet_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan_review_packet.json"
        assert review_packet_path.exists()

        with open(review_packet_path) as f:
            packet = json.load(f)

        assert packet["packet_type"] == "corrective_retry_v4_visual_correction_plan_review_packet"
        assert packet["operator_decision_required"] is True
        assert "approve_visual_correction_plan" in packet["allowed_decisions"]
        assert "request_visual_correction_plan_changes" in packet["allowed_decisions"]
        assert "reject_visual_correction_plan" in packet["allowed_decisions"]

    def test_no_generation(self, temp_project, failed_verdict, input_packet):
        """Test that no generation is performed"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["generation_performed"] is False
        assert plan["retry_attempted"] is False
        assert plan["workflow_mutated"] is False

    def test_no_comfyui_submit(self, temp_project, failed_verdict, input_packet):
        """Test that no ComfyUI submit is performed"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["comfyui_execution"] is False

    def test_no_assembly(self, temp_project, failed_verdict, input_packet):
        """Test that no assembly is executed"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["assembly_executed"] is False

    def test_no_downstream(self, temp_project, failed_verdict, input_packet):
        """Test that no downstream is executed"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["downstream_executed"] is False

    def test_production_accepted_false(self, temp_project, failed_verdict, input_packet):
        """Test that production_accepted is False"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["production_accepted"] is False

    def test_next_allowed_action_not_none(self, temp_project, failed_verdict, input_packet):
        """Test that next_allowed_action is not none"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(failed_verdict, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(input_packet, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(
            project_root=str(temp_project),
            shot_id="shot02",
            json=True
        )

        combine_build_corrective_retry_v4_visual_correction_plan(args)

        # Check plan artifact
        plan_path = control_dir / "combine_v2_corrective_retry_v4_visual_correction_plan.json"
        with open(plan_path) as f:
            plan = json.load(f)

        assert plan["next_allowed_action"] is not None
        assert plan["next_allowed_action"] != "none"
        assert "operator_retry_v4_visual_correction_plan_review" in plan["next_allowed_action"]

        # Check artifact_index
        index_path = control_dir / "artifact_index.json"
        with open(index_path) as f:
            index = json.load(f)

        assert index["next_allowed_action"] is not None
        assert index["next_allowed_action"] != "none"


class TestVisualQAGateStateMachine:
    """Test state machine transitions for Visual QA gate"""

    def test_state_exists_in_state_machine(self):
        """Test that corrective_retry_v4_visual_correction_plan_required exists"""
        assert CombineStateMachine.is_valid_state("corrective_retry_v4_visual_correction_plan_required")

    def test_operator_review_state_exists(self):
        """Test that operator_retry_v4_visual_correction_plan_review_required exists"""
        assert CombineStateMachine.is_valid_state("operator_retry_v4_visual_correction_plan_review_required")

    def test_transition_from_visual_qa_to_correction_plan_allowed(self):
        """Test transition from visual_qa_required to visual_correction_plan_required"""
        assert CombineStateMachine.can_transition(
            "corrective_retry_v4_visual_qa_required",
            "corrective_retry_v4_visual_correction_plan_required"
        )

    def test_transition_from_correction_plan_to_operator_review_allowed(self):
        """Test transition from correction_plan_required to operator_review_required"""
        assert CombineStateMachine.can_transition(
            "corrective_retry_v4_visual_correction_plan_required",
            "operator_retry_v4_visual_correction_plan_review_required"
        )

    def test_operator_review_self_loop_allowed(self):
        """Test that operator review state has self-loop"""
        assert CombineStateMachine.can_transition(
            "operator_retry_v4_visual_correction_plan_review_required",
            "operator_retry_v4_visual_correction_plan_review_required"
        )

    def test_operator_review_to_v4_plan_allowed(self):
        """Test transition from operator review to corrective_retry_v4_plan_required"""
        assert CombineStateMachine.can_transition(
            "operator_retry_v4_visual_correction_plan_review_required",
            "corrective_retry_v4_plan_required"
        )


class TestArtifactIndexUpdates:
    """Test that artifact_index.json is properly updated"""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure"""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir) / "test_project"
        control_dir = project_root / "output" / "control"
        assets_dir = project_root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)

        yield project_root

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def artifacts(self):
        """Create fixture artifacts"""
        verdict = {
            "task_id": "RC-COMBINE-V2-2541-2600",
            "stage": "corrective_retry_v4_visual_qa_required",
            "verdict_type": "corrective_retry_v4_visual_qa_verdict",
            "shot_id": "shot02",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "visual_qa_executed": True,
            "visual_qa_verdict": "failed",
            "production_accepted": False,
            "asset_path": "F:\\test\\output\\assets\\test.png",
            "canonical_asset_path": "output/assets/test.png",
            "sha256": "abc123",
            "failed_reasons": ["subject_too_small", "excessive_empty_space"],
            "known_visual_issues": ["subject_too_small", "excessive_empty_space"],
            "operator_visual_concerns": {"subject_too_small": True, "excessive_empty_space": True},
            "generation_performed": False,
            "comfyui_execution": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False
        }

        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/test.png",
            "sha256": "abc123",
            "operator_visual_concerns": {"subject_too_small": True, "excessive_empty_space": True},
            "known_visual_issues": ["subject_too_small", "excessive_empty_space"],
            "generation_performed": False,
            "comfyui_execution": False
        }

        return {"verdict": verdict, "input_packet": input_packet}

    def test_artifact_index_current_state_updated(self, temp_project, artifacts):
        """Test that artifact_index current_state is updated"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(artifacts["verdict"], f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(artifacts["input_packet"], f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "corrective_retry_v4_visual_qa_required"}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(project_root=str(temp_project), shot_id="shot02", json=True)
        combine_build_corrective_retry_v4_visual_correction_plan(args)

        with open(control_dir / "artifact_index.json") as f:
            index = json.load(f)

        assert index["current_state"] == "corrective_retry_v4_visual_correction_plan_required"

    def test_artifact_index_visual_correction_plan_created_flag(self, temp_project, artifacts):
        """Test that visual_correction_plan_created flag is set"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(artifacts["verdict"], f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(artifacts["input_packet"], f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(project_root=str(temp_project), shot_id="shot02", json=True)
        combine_build_corrective_retry_v4_visual_correction_plan(args)

        with open(control_dir / "artifact_index.json") as f:
            index = json.load(f)

        assert index["visual_correction_plan_created"] is True

    def test_artifact_index_downstream_blocked(self, temp_project, artifacts):
        """Test that downstream_blocked is True"""
        control_dir = temp_project / "output" / "control"

        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json", "w") as f:
            json.dump(artifacts["verdict"], f)
        with open(control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json", "w") as f:
            json.dump(artifacts["input_packet"], f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({}, f)
        with open(control_dir / "episode_ledger.json", "w") as f:
            json.dump([], f)

        from app.cli import combine_build_corrective_retry_v4_visual_correction_plan
        from argparse import Namespace

        args = Namespace(project_root=str(temp_project), shot_id="shot02", json=True)
        combine_build_corrective_retry_v4_visual_correction_plan(args)

        with open(control_dir / "artifact_index.json") as f:
            index = json.load(f)

        assert index["downstream_blocked"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
