"""Test controlled generation single execution gate.

RC-COMBINE-V2-99001-102000

Validates:
- Exactly one generation executed
- No second generation
- No blind retry
- Workflow submitted exactly once
"""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"


def _read_json(name: str) -> dict:
    path = CONTROL_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestSingleExecution:
    def test_execution_report_exists(self):
        """generation_execution_report.json must exist."""
        report = _read_json("generation_execution_report.json")
        assert report, "generation_execution_report.json missing"

    def test_generation_count_equals_one(self):
        """Exactly one generation must have been attempted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("generation_count") == 1, "Must be exactly 1 generation"

    def test_max_generations_equals_one(self):
        """max_generations must equal 1."""
        report = _read_json("generation_execution_report.json")
        assert report.get("max_generations") == 1, "max_generations must be 1"

    def test_workflow_submitted(self):
        """Workflow must have been submitted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("workflow_submitted") is True

    def test_comfyui_execution(self):
        """ComfyUI execution must have occurred."""
        report = _read_json("generation_execution_report.json")
        assert report.get("comfyui_execution") is True

    def test_comfyui_submit_executed(self):
        """comfyui_submit_executed must be true."""
        report = _read_json("generation_execution_report.json")
        assert report.get("comfyui_submit_executed") is True

    def test_no_second_generation(self):
        """No second generation must have been attempted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("second_generation_attempted") is False

    def test_no_blind_retry(self):
        """No blind retry must have been attempted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("blind_retry_attempted") is False

    def test_prompt_id_present(self):
        """Real prompt_id must be present."""
        report = _read_json("generation_execution_report.json")
        pid = report.get("prompt_id", "")
        assert pid, "prompt_id must not be empty"
        assert pid != "fake_prompt_id", "prompt_id must not be fake"

    def test_generated_assets_count(self):
        """At least one generated asset must exist."""
        report = _read_json("generation_execution_report.json")
        assert report.get("generated_assets_count", 0) > 0

    def test_next_action_is_review_required(self):
        """Next allowed action must be generation_result_review_required."""
        report = _read_json("generation_execution_report.json")
        assert report.get("next_allowed_action") == "generation_result_review_required"

    def test_no_visual_qa(self):
        """Visual QA must not have been executed."""
        report = _read_json("generation_execution_report.json")
        assert report.get("visual_qa_executed") is False

    def test_no_assembly(self):
        """Assembly must not have been executed."""
        report = _read_json("generation_execution_report.json")
        assert report.get("assembly_executed") is False

    def test_no_downstream(self):
        """Downstream must not have been executed."""
        report = _read_json("generation_execution_report.json")
        assert report.get("downstream_executed") is False

    def test_no_production_acceptance(self):
        """Production acceptance must be false."""
        report = _read_json("generation_execution_report.json")
        assert report.get("production_accepted") is False


class TestPromptIdReport:
    def test_prompt_id_report_exists(self):
        """prompt_id_report.json must exist."""
        report = _read_json("prompt_id_report.json")
        assert report, "prompt_id_report.json missing"

    def test_prompt_id_created_true(self):
        """prompt_id_created must be true."""
        report = _read_json("prompt_id_report.json")
        assert report.get("prompt_id_created") is True

    def test_no_fake_prompt_id(self):
        """prompt_id must not be fake."""
        report = _read_json("prompt_id_report.json")
        assert report.get("prompt_id", "") != "fake_prompt_id"
        assert report.get("fake_prompt_id") is not True

    def test_prompt_id_not_empty(self):
        """prompt_id must be a non-empty string."""
        report = _read_json("prompt_id_report.json")
        assert isinstance(report.get("prompt_id"), str) and len(report["prompt_id"]) > 0
