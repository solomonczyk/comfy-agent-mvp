"""Tests for combine-create-corrective-retry-v3-plan CLI command.

RC-COMBINE-V2-1161-1220 — Corrective Retry V3 Plan Creation
"""
import json
import argparse
from pathlib import Path

import pytest


def _build_args(project_root, shot_id="shot02", json_output=True):
    ns = argparse.Namespace()
    ns.project_root = str(project_root)
    ns.shot_id = shot_id
    ns.json = json_output
    return ns


def _seed_rejection_v2(control_dir, failure_categories=None):
    if failure_categories is None:
        failure_categories = ["blur_detected", "low_contrast"]
    control_dir.mkdir(parents=True, exist_ok=True)
    rejection = {
        "stage": "operator_visual_review",
        "shot_id": "shot02",
        "operator_visual_decision": "reject_visual_quality",
        "source_asset": "output/assets/combine_v2_corrective_retry_1777971208_00001_.png",
        "previous_qa_verdict": "qa_failed",
        "failure_categories": failure_categories,
        "operator_rejection_confirmed": True,
        "next_allowed_action": "corrective_retry_v3_plan_required",
    }
    (control_dir / "combine_v2_operator_visual_rejection_v2.json").write_text(json.dumps(rejection))


def _import_func():
    import importlib
    cli = importlib.import_module("app.cli")
    return cli.combine_create_corrective_retry_v3_plan


class TestCorrectiveRetryV3Plan:
    def test_requires_rejection_v2_artifact(self, tmp_path, capsys):
        fn = _import_func()
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["status"] == "error"

    def test_creates_all_five_artifacts(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        expected = [
            "combine_v2_corrective_retry_v3_failure_classification.json",
            "combine_v2_corrective_retry_v3_plan.json",
            "combine_v2_corrective_retry_v3_sampler_recipe_plan.json",
            "combine_v2_corrective_retry_v3_prompt_plan.json",
            "combine_v2_corrective_retry_v3_workflow_quality_plan.json",
        ]
        for fname in expected:
            assert (control_dir / fname).exists(), f"Missing: {fname}"

    def test_failure_classification_content(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        data = json.loads((control_dir / "combine_v2_corrective_retry_v3_failure_classification.json").read_text())
        assert data["blur_detected"] is True
        assert data["low_contrast"] is True
        assert data["blind_retry_allowed"] is False
        assert data["requires_corrective_retry_v3"] is True

    def test_v3_plan_content(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        data = json.loads((control_dir / "combine_v2_corrective_retry_v3_plan.json").read_text())
        assert data["plan_type"] == "controlled_corrective_retry_v3_plan"
        assert data["blind_retry_allowed"] is False
        assert data["retry_requires_operator_authorization"] is True
        assert data["generation_allowed"] is False
        assert data["next_allowed_action"] == "operator_retry_v3_plan_review_required"
        assert data["required_corrections"]["blur_reduction_required"] is True
        assert data["required_corrections"]["contrast_correction_required"] is True

    def test_json_output_fields(self, tmp_path, capsys):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["blind_retry_allowed"] is False
        assert output["generation_allowed"] is False
        assert output["retry_allowed"] is False
        assert output["comfyui_execution"] is False
        assert output["production_accepted"] is False
        assert output["next_allowed_action"] == "operator_retry_v3_plan_review_required"
        assert output["corrective_retry_v3_plan_created"] is True
        assert output["sampler_recipe_plan_created"] is True
        assert output["prompt_plan_created"] is True
        assert output["workflow_quality_plan_created"] is True

    def test_artifact_index_updated(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "corrective_retry_v3_plan_required"
        assert index["next_allowed_action"] == "operator_retry_v3_plan_review_required"
        assert index["blind_retry_allowed"] is False
        assert index["generation_allowed"] is False

    def test_episode_ledger_event(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("event_type") == "corrective_retry_v3_plan_created"]
        assert len(events) == 1
        assert events[0]["blind_retry_allowed"] is False

    def test_artifacts_list_in_output(self, tmp_path, capsys):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_rejection_v2(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        artifacts = output["artifacts"]
        assert any("corrective_retry_v3_plan.json" in a for a in artifacts)
        assert any("failure_classification" in a for a in artifacts)
        assert any("sampler_recipe" in a for a in artifacts)
        assert any("prompt_plan" in a for a in artifacts)
        assert any("workflow_quality" in a for a in artifacts)
