"""Tests for RC-COMBINE-V2-2721-2780 — combine-update-corrective-retry-v4-implementation-plan."""
import json
import sys
import types
import argparse
import importlib
import pytest
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(project_root: str, shot_id: str = "shot02", json_out: bool = True):
    ns = argparse.Namespace()
    ns.project_root = project_root
    ns.shot_id = shot_id
    ns.json = json_out
    return ns


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _import_handler():
    import importlib
    cli = importlib.import_module("app.cli")
    return cli.combine_update_corrective_retry_v4_implementation_plan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

APPROVED_REVIEW = {
    "task_id": "RC-COMBINE-V2-2661-2720",
    "operator_decision": "approve_visual_correction_plan",
    "visual_correction_plan_approved": True,
    "approved_failed_reasons": ["subject_too_small", "excessive_empty_space"],
    "shot_id": "shot02",
    "current_state": "operator_retry_v4_visual_correction_plan_review_required",
    "next_allowed_action": "corrective_retry_v4_retry_implementation_plan_update_required",
}

VISUAL_CORRECTION_PLAN = {
    "failed_reasons": ["subject_too_small", "excessive_empty_space", "weak_composition"],
    "correction_mapping": {
        "subject_too_small": {"target_subject_height_ratio": "0.40-0.60"},
        "excessive_empty_space": {"target_empty_space_ratio_max": 0.45},
    },
    "retry_prompt_patch": {
        "positive_prompt_additions": ["medium shot", "subject dominant"],
        "negative_prompt_additions": ["tiny person", "empty landscape"],
        "subject_scale_requirements": ["subject >= 40% of frame height"],
        "camera_framing_requirements": ["empty space <= 45%"],
        "composition_requirements": ["subject is focal point"],
        "rejection_criteria": ["subject < 30% → reject"],
    },
    "graph_recommendations": {"save_image_prefix": "combine_v2_corrective_retry_v4_shot02"},
    "production_accepted": False,
}

ARTIFACT_INDEX = {
    "current_state": "operator_retry_v4_visual_correction_plan_review_required",
    "next_allowed_action": "corrective_retry_v4_retry_implementation_plan_update_required",
    "production_accepted": False,
}


# ---------------------------------------------------------------------------
# Approval requirement tests
# ---------------------------------------------------------------------------

class TestApprovalRequirements:
    def test_blocks_when_operator_review_missing(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "VISUAL_CORRECTION_PLAN_REVIEW_MISSING"

    def test_blocks_when_visual_correction_plan_missing(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "VISUAL_CORRECTION_PLAN_MISSING"

    def test_blocks_when_operator_decision_not_approve(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        bad_review = {**APPROVED_REVIEW, "operator_decision": "request_visual_correction_plan_changes", "visual_correction_plan_approved": False}
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", bad_review)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "VISUAL_CORRECTION_PLAN_NOT_APPROVED"

    def test_blocks_when_visual_correction_plan_approved_false(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        bad_review = {**APPROVED_REVIEW, "visual_correction_plan_approved": False}
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", bad_review)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "VISUAL_CORRECTION_PLAN_NOT_APPROVED"

    def test_blocks_when_state_not_allowed(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        bad_index = {"current_state": "production_accepted", "next_allowed_action": "some_other_action", "production_accepted": False}
        _write(control / "artifact_index.json", bad_index)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "RETRY_IMPLEMENTATION_PLAN_UPDATE_NOT_ALLOWED"

    def test_blocks_when_production_accepted_true(self, tmp_path, capsys):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        bad_index = {**ARTIFACT_INDEX, "production_accepted": True}
        _write(control / "artifact_index.json", bad_index)

        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert out["blocker"] == "RETRY_IMPLEMENTATION_PLAN_UPDATE_NOT_ALLOWED"


# ---------------------------------------------------------------------------
# Artifact creation tests
# ---------------------------------------------------------------------------

class TestArtifactCreation:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_returns_zero_on_success(self, tmp_path, capsys):
        self._setup(tmp_path)
        handler = _import_handler()
        rc = handler(_make_args(str(tmp_path)))
        assert rc == 0

    def test_creates_updated_implementation_plan(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        handler = _import_handler()
        handler(_make_args(str(tmp_path)))
        plan_path = control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json"
        assert plan_path.exists()
        plan = _read(plan_path)
        assert plan["plan_type"] == "corrective_retry_v4_updated_implementation_plan"

    def test_creates_operator_review_packet(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        handler = _import_handler()
        handler(_make_args(str(tmp_path)))
        packet_path = control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json"
        assert packet_path.exists()
        packet = _read(packet_path)
        assert packet["packet_type"] == "corrective_retry_v4_updated_implementation_plan_review_packet"

    def test_result_json_fields(self, tmp_path, capsys):
        self._setup(tmp_path)
        handler = _import_handler()
        handler(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "ok"
        assert out["updated_retry_implementation_plan_created"] is True
        assert out["operator_review_packet_created"] is True


# ---------------------------------------------------------------------------
# Prompt patch tests
# ---------------------------------------------------------------------------

class TestPromptPatchRequirements:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_positive_prompt_additions_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["prompt_patch"]["positive_prompt_additions"]) > 0

    def test_negative_prompt_additions_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["prompt_patch"]["negative_prompt_additions"]) > 0

    def test_prompt_patch_has_source_field(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["prompt_patch"]["source"] == "approved_visual_correction_plan"

    def test_source_visual_qa_failed_reasons_populated(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["source_visual_qa_failed_reasons"] == VISUAL_CORRECTION_PLAN["failed_reasons"]


# ---------------------------------------------------------------------------
# Subject scale / empty space / composition tests
# ---------------------------------------------------------------------------

class TestSubjectScaleRequirements:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_camera_framing_target_ratio_min(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["camera_framing"]["target_subject_height_ratio_min"] == 0.40

    def test_camera_framing_target_ratio_max(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["camera_framing"]["target_subject_height_ratio_max"] == 0.60

    def test_camera_framing_hard_reject_below(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["camera_framing"]["hard_reject_subject_height_ratio_below"] == 0.30

    def test_camera_framing_empty_space_max(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["camera_framing"]["target_empty_space_ratio_max"] == 0.45

    def test_subject_scale_requirements_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["subject_scale_requirements"]) > 0

    def test_empty_space_requirements_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["empty_space_requirements"]) > 0

    def test_composition_requirements_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["composition_requirements"]) > 0

    def test_rejection_criteria_present(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert len(plan["rejection_criteria"]) > 0


# ---------------------------------------------------------------------------
# Pre/post submit contract tests
# ---------------------------------------------------------------------------

class TestValidationContracts:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_pre_submit_contract_max_generations_one(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["pre_submit_validation_contract"]["max_generations"] == 1

    def test_pre_submit_contract_dry_run_true(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["pre_submit_validation_contract"]["dry_run_for_preflight_only"] is True

    def test_pre_submit_contract_requires_separate_authorization(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["pre_submit_validation_contract"]["real_submit_requires_separate_operator_authorization"] is True

    def test_post_submit_contract_visual_qa_required(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["post_submit_validation_contract"]["visual_qa_required_after_generation"] is True

    def test_post_submit_contract_stub_asset_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["post_submit_validation_contract"]["stub_asset_detected"] is False

    def test_post_submit_contract_old_shot01_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["post_submit_validation_contract"]["old_shot01_asset_used"] is False

    def test_post_submit_contract_production_accepted_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["post_submit_validation_contract"]["production_accepted"] is False


# ---------------------------------------------------------------------------
# Operator review packet tests
# ---------------------------------------------------------------------------

class TestOperatorReviewPacket:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_operator_actions_include_approve(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        packet = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json")
        assert "approve_updated_retry_implementation_plan" in packet["operator_actions"]

    def test_operator_actions_include_request_changes(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        packet = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json")
        assert "request_updated_retry_implementation_plan_changes" in packet["operator_actions"]

    def test_operator_actions_include_reject(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        packet = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json")
        assert "reject_updated_retry_implementation_plan" in packet["operator_actions"]

    def test_review_packet_hard_boundary_generation_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        packet = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json")
        assert packet["hard_boundary"]["generation_allowed"] is False

    def test_review_packet_production_accepted_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        packet = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json")
        assert packet["production_accepted"] is False


# ---------------------------------------------------------------------------
# No generation / no execution tests
# ---------------------------------------------------------------------------

class TestNoGenerationNoExecution:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_result_no_generation(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["new_generation_performed"] is False

    def test_result_no_comfyui_submit(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["new_comfyui_submit_executed"] is False

    def test_result_no_retry_attempted(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["retry_attempted"] is False

    def test_result_no_workflow_submit(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["workflow_submitted"] is False

    def test_result_no_assembly(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["assembly_executed"] is False

    def test_result_no_downstream(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["downstream_executed"] is False

    def test_result_production_accepted_false(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["production_accepted"] is False

    def test_plan_generation_gate_closed(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["generation_gate"]["generation_allowed"] is False


# ---------------------------------------------------------------------------
# State transition tests
# ---------------------------------------------------------------------------

class TestStateTransition:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_artifact_index_current_state(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        idx = _read(control / "artifact_index.json")
        assert idx["current_state"] == "corrective_retry_v4_retry_implementation_plan_update_required"

    def test_artifact_index_next_allowed_action(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        idx = _read(control / "artifact_index.json")
        assert idx["next_allowed_action"] == "operator_retry_v4_updated_implementation_plan_review_required"

    def test_artifact_index_updated_plan_flag(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        idx = _read(control / "artifact_index.json")
        assert idx["updated_retry_implementation_plan_created"] is True

    def test_artifact_index_production_accepted_false(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        idx = _read(control / "artifact_index.json")
        assert idx["production_accepted"] is False

    def test_artifact_index_downstream_blocked(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        idx = _read(control / "artifact_index.json")
        assert idx["downstream_blocked"] is True

    def test_result_next_allowed_action(self, tmp_path, capsys):
        self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        out = json.loads(capsys.readouterr().out)
        assert out["next_allowed_action"] == "operator_retry_v4_updated_implementation_plan_review_required"

    def test_episode_ledger_event_appended(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        ledger = _read(control / "episode_ledger.json")
        event_types = [e.get("event_type") for e in ledger]
        assert "corrective_retry_v4_updated_implementation_plan_created" in event_types

    def test_episode_ledger_event_fields(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        ledger = _read(control / "episode_ledger.json")
        evt = next(e for e in ledger if e.get("event_type") == "corrective_retry_v4_updated_implementation_plan_created")
        assert evt["updated_retry_implementation_plan_created"] is True
        assert evt["new_generation_performed"] is False
        assert evt["production_accepted"] is False
        assert evt["next_allowed_action"] == "operator_retry_v4_updated_implementation_plan_review_required"


# ---------------------------------------------------------------------------
# Runtime prefix / collector invariant tests
# ---------------------------------------------------------------------------

class TestRuntimePrefixInvariants:
    def _setup(self, tmp_path):
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        _write(control / "combine_v2_operator_retry_v4_visual_correction_plan_review.json", APPROVED_REVIEW)
        _write(control / "combine_v2_corrective_retry_v4_visual_correction_plan.json", VISUAL_CORRECTION_PLAN)
        _write(control / "artifact_index.json", ARTIFACT_INDEX)
        _write(control / "episode_ledger.json", [])
        return control

    def test_runtime_saveimage_prefix(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["runtime_saveimage_prefix"] == "combine_v2_corrective_retry_v4_shot02"

    def test_collector_uses_runtime_prefix(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["collector_uses_runtime_saveimage_prefix"] is True

    def test_old_shot01_outputs_forbidden(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["old_shot01_outputs_forbidden"] is True

    def test_stub_outputs_forbidden(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        assert plan["stub_outputs_forbidden"] is True

    def test_prefix_invariants_in_plan(self, tmp_path, capsys):
        control = self._setup(tmp_path)
        _import_handler()(_make_args(str(tmp_path)))
        plan = _read(control / "combine_v2_corrective_retry_v4_updated_implementation_plan.json")
        inv = plan["runtime_prefix_invariants"]
        assert inv["saveimage_prefix"] == "combine_v2_corrective_retry_v4_shot02"
        assert inv["collector_must_use_prefix"] is True
        assert inv["cross_shot_prefix_reuse_forbidden"] is True
