"""
Tests for app/visual_generation/executor.py
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def project_root(tmp_path):
    (tmp_path / "output" / "control" / "fresh_visual_candidate").mkdir(parents=True)
    (tmp_path / "output" / "assets" / "fresh_visual_candidates").mkdir(parents=True)
    return tmp_path


def _make_http_response(body: bytes, status: int = 200):
    m = MagicMock()
    m.read.return_value = body
    m.status = status
    m.__enter__ = lambda s: s
    m.__exit__ = MagicMock(return_value=False)
    return m


def test_execute_success(project_root):
    from app.visual_generation.executor import GenerationExecutor

    prompt_id = "test-prompt-abc"
    history_response = {
        prompt_id: {
            "outputs": {
                "9": {
                    "images": [{"filename": "test_out_001.png", "subfolder": ""}]
                }
            }
        }
    }

    submit_resp = _make_http_response(json.dumps({"prompt_id": prompt_id}).encode())
    history_resp = _make_http_response(json.dumps(history_response).encode())

    call_count = {"n": 0}

    def urlopen_side_effect(req, timeout=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return submit_resp
        return history_resp

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        executor = GenerationExecutor(project_root)
        result = executor.execute(
            workflow_payload={"key": "value"},
            comfyui_host="127.0.0.1",
            comfyui_port=8188,
        )

    assert result["generation_performed"] is True
    assert result["prompt_id"] == prompt_id
    assert result["generation_count"] == 1
    assert result["retry_attempted"] is False
    assert result["second_generation_attempted"] is False
    assert result["production_accepted"] is False
    assert result["failure"] is False
    assert "test_out_001.png" in result["output_images"]

    exec_report = (
        project_root / "output" / "control" / "fresh_visual_candidate" / "generation_execution_report.json"
    )
    assert exec_report.exists()


def test_execute_failure_on_submit_error(project_root):
    from app.visual_generation.executor import GenerationExecutor
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        executor = GenerationExecutor(project_root)
        result = executor.execute(
            workflow_payload={},
            comfyui_host="127.0.0.1",
            comfyui_port=8188,
        )

    assert result["failure"] is True
    assert result["retry_attempted"] is False
    assert result["second_generation_attempted"] is False
    assert result["generation_performed"] is False


def test_execute_no_second_generation(project_root):
    """Verifies executor never attempts more than one submission."""
    from app.visual_generation.executor import GenerationExecutor

    submit_count = {"n": 0}
    prompt_id = "once-only"
    history_response = {
        prompt_id: {"outputs": {"9": {"images": [{"filename": "out.png", "subfolder": ""}]}}}
    }

    def urlopen_side_effect(req, timeout=None):
        if hasattr(req, "full_url") and "/prompt" in req.full_url:
            submit_count["n"] += 1
        m = _make_http_response(
            json.dumps({"prompt_id": prompt_id}).encode()
            if submit_count["n"] <= 1 and hasattr(req, "data") and req.data
            else json.dumps(history_response).encode()
        )
        return m

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        executor = GenerationExecutor(project_root)
        executor.execute(workflow_payload={})

    assert submit_count["n"] <= 1


def test_execute_report_locks(project_root):
    from app.visual_generation.executor import GenerationExecutor
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
        executor = GenerationExecutor(project_root)
        result = executor.execute(workflow_payload={})

    assert result["assembly_executed"] is False
    assert result["downstream_executed"] is False
    assert result["operator_visual_acceptance_executed"] is False
    assert result["visual_qa_acceptance_executed"] is False
    assert result["production_accepted"] is False
