"""Tests for combine-operator-visual-decision-v2 CLI command.

RC-COMBINE-V2-1161-1220 — Operator Visual Rejection V2
"""
import json
import sys
import types
import argparse
from pathlib import Path
from unittest.mock import patch
import tempfile
import os

import pytest


def _build_args(project_root, shot_id="shot02", decision="reject_visual_quality",
                asset="output/assets/combine_v2_corrective_retry_1777971208_00001_.png",
                reason="blur and low contrast", json_output=True):
    ns = argparse.Namespace()
    ns.project_root = str(project_root)
    ns.shot_id = shot_id
    ns.decision = decision
    ns.asset = asset
    ns.reason = reason
    ns.json = json_output
    return ns


def _import_func():
    import importlib
    cli = importlib.import_module("app.cli")
    return cli.combine_operator_visual_decision_v2


class TestOperatorVisualRejectionV2:
    def test_reject_visual_quality_creates_artifact(self, tmp_path):
        fn = _import_func()
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        artifact = tmp_path / "output" / "control" / "combine_v2_operator_visual_rejection_v2.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text())
        assert data["operator_visual_decision"] == "reject_visual_quality"
        assert data["operator_rejection_confirmed"] is True
        assert data["generation_allowed"] is False
        assert data["blind_retry_allowed"] is False
        assert data["next_allowed_action"] == "corrective_retry_v3_plan_required"

    def test_reject_visual_quality_json_output(self, tmp_path, capsys):
        fn = _import_func()
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["operator_visual_decision"] == "reject_visual_quality"
        assert output["next_allowed_action"] == "corrective_retry_v3_plan_required"
        assert output["generation_allowed"] is False
        assert output["blind_retry_allowed"] is False
        assert output["production_accepted"] is False

    def test_invalid_decision_rejected(self, tmp_path, capsys):
        fn = _import_func()
        args = _build_args(tmp_path, decision="accept")
        rc = fn(args)
        assert rc == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["status"] == "error"

    def test_failure_categories_populated(self, tmp_path):
        fn = _import_func()
        # Pre-create a QA report with specific categories
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        qa_report = {
            "qa_verdict": "qa_failed",
            "failure_categories": ["blur_detected", "low_contrast"]
        }
        (control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json").write_text(
            json.dumps(qa_report)
        )
        args = _build_args(tmp_path)
        rc = fn(args)
        assert rc == 0
        artifact = control_dir / "combine_v2_operator_visual_rejection_v2.json"
        data = json.loads(artifact.read_text())
        assert "blur_detected" in data["failure_categories"]
        assert "low_contrast" in data["failure_categories"]

    def test_artifact_index_updated(self, tmp_path):
        fn = _import_func()
        args = _build_args(tmp_path)
        fn(args)
        index_path = tmp_path / "output" / "control" / "artifact_index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())
        assert index["operator_visual_decision_v2"] == "reject_visual_quality"
        assert index["generation_allowed"] is False
        assert index["next_allowed_action"] == "corrective_retry_v3_plan_required"

    def test_episode_ledger_updated(self, tmp_path):
        fn = _import_func()
        args = _build_args(tmp_path)
        fn(args)
        ledger_path = tmp_path / "output" / "control" / "episode_ledger.json"
        assert ledger_path.exists()
        ledger = json.loads(ledger_path.read_text())
        assert isinstance(ledger, list)
        events = [e for e in ledger if e.get("event_type") == "operator_visual_rejection_v2"]
        assert len(events) == 1
        assert events[0]["generation_allowed"] is False

    def test_forbidden_fields_in_output(self, tmp_path, capsys):
        fn = _import_func()
        args = _build_args(tmp_path)
        fn(args)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # None of these should be True
        assert output["generation_allowed"] is False
        assert output["retry_allowed"] is False
        assert output["blind_retry_allowed"] is False
        assert output["workflow_submitted"] is False
        assert output["comfyui_execution"] is False
        assert output["downstream_executed"] is False
        assert output["production_accepted"] is False
