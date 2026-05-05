"""Tests for combine-build-retry-v3-plan-review-packet CLI command.

RC-COMBINE-V2-1161-1220 — Operator Retry V3 Plan Review Packet
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


def _seed_v3_plan(control_dir, failure_categories=None):
    if failure_categories is None:
        failure_categories = ["blur_detected", "low_contrast"]
    control_dir.mkdir(parents=True, exist_ok=True)
    source_asset = "output/assets/combine_v2_corrective_retry_1777971208_00001_.png"

    rejection_v2 = {
        "operator_visual_decision": "reject_visual_quality",
        "source_asset": source_asset,
        "previous_qa_verdict": "qa_failed",
        "failure_categories": failure_categories,
        "operator_rejection_confirmed": True,
    }
    (control_dir / "combine_v2_operator_visual_rejection_v2.json").write_text(json.dumps(rejection_v2))

    v3_plan = {
        "stage": "corrective_retry_v3_plan_required",
        "shot_id": "shot02",
        "plan_type": "controlled_corrective_retry_v3_plan",
        "source_asset": source_asset,
        "failure_basis": failure_categories,
        "blind_retry_allowed": False,
        "retry_requires_operator_authorization": True,
        "generation_allowed": False,
        "next_allowed_action": "operator_retry_v3_plan_review_required",
        "required_corrections": {
            "sampler_recipe_review_required": True,
            "contrast_correction_required": True,
            "blur_reduction_required": True,
        },
        "recommended_changes": {
            "increase_detail_clarity": True,
        },
    }
    (control_dir / "combine_v2_corrective_retry_v3_plan.json").write_text(json.dumps(v3_plan))

    for fname, key in [
        ("combine_v2_corrective_retry_v3_failure_classification.json", {}),
        ("combine_v2_corrective_retry_v3_sampler_recipe_plan.json",
         {"sampler_elements_to_review": ["sampler_name", "cfg"]}),
        ("combine_v2_corrective_retry_v3_prompt_plan.json",
         {"prompt_elements_to_review": ["positive_prompt"]}),
        ("combine_v2_corrective_retry_v3_workflow_quality_plan.json",
         {"workflow_elements_to_review": ["vae_decode_node"]}),
    ]:
        (control_dir / fname).write_text(json.dumps(key))


def _import_func():
    import importlib
    cli = importlib.import_module("app.cli")
    return cli.combine_build_retry_v3_plan_review_packet


class TestRetryV3PlanReviewPacket:
    def test_requires_v3_plan_artifact(self, tmp_path, capsys):
        fn = _import_func()
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["status"] == "error"

    def test_creates_review_packet(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        packet_path = control_dir / "combine_v2_retry_v3_operator_plan_review_packet.json"
        assert packet_path.exists()

    def test_packet_content(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        data = json.loads(
            (control_dir / "combine_v2_retry_v3_operator_plan_review_packet.json").read_text()
        )
        assert data["stage"] == "operator_retry_v3_plan_review_required"
        assert data["plan_type"] == "operator_retry_v3_plan_review_packet"
        assert data["operator_rejection_confirmed"] is True
        assert data["blind_retry_allowed"] is False
        assert data["generation_allowed"] is False
        assert data["next_allowed_action"] == "operator_retry_v3_plan_review_required"

    def test_forbidden_fields_all_false(self, tmp_path, capsys):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        for field in [
            "generation_allowed", "retry_allowed", "blind_retry_allowed",
            "workflow_submitted", "comfyui_execution", "visual_qa_rerun",
            "assembly_executed", "downstream_executed", "production_accepted"
        ]:
            assert output[field] is False, f"Expected {field}=False, got {output[field]}"

    def test_operator_actions_allowed_present(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        data = json.loads(
            (control_dir / "combine_v2_retry_v3_operator_plan_review_packet.json").read_text()
        )
        allowed = data["operator_actions_allowed"]
        assert "approve_retry_v3_plan" in allowed
        assert "manual_review" in allowed
        assert "abort_route" in allowed

    def test_plan_components_referenced(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        data = json.loads(
            (control_dir / "combine_v2_retry_v3_operator_plan_review_packet.json").read_text()
        )
        comps = data["plan_components"]
        assert "operator_visual_rejection_v2" in comps
        assert "corrective_retry_v3_plan" in comps
        assert "sampler_recipe_plan" in comps
        assert "prompt_plan" in comps
        assert "workflow_quality_plan" in comps

    def test_artifact_index_state(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "operator_retry_v3_plan_review_required"
        assert index["operator_retry_v3_plan_review_packet_created"] is True
        assert index["generation_allowed"] is False

    def test_episode_ledger_event(self, tmp_path):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("event_type") == "operator_retry_v3_plan_review_packet_created"]
        assert len(events) == 1
        assert events[0]["generation_allowed"] is False
        assert events[0]["next_allowed_action"] == "operator_retry_v3_plan_review_required"

    def test_stops_at_operator_retry_v3_plan_review_required(self, tmp_path, capsys):
        fn = _import_func()
        control_dir = tmp_path / "output" / "control"
        _seed_v3_plan(control_dir)
        args = _build_args(tmp_path)
        fn(args)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["next_allowed_action"] == "operator_retry_v3_plan_review_required"
        assert output["stage"] == "operator_retry_v3_plan_review_required"
