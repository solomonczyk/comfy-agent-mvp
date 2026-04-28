"""KT-2 tool contract tests.

Verifies that every tool module exposes an async `run` function and that
its call emits a valid `ToolResult` onto the provided `ToolTrace`.

These tests avoid any network calls — they mock the underlying service/
client dependencies so the tests are fast and deterministic.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.execution_plan import ExecutionPlan
from app.agent.task_selector import TaskSelectionResult
from app.tools import (
    detect_task,
    fetch_outputs,
    load_workflow,
    mutate_workflow,
    persist_run,
    select_workflow,
    submit_to_comfy,
    validate_graph_contract,
    validate_required_inputs,
    watch_progress,
)
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.workflow_types import TaskType, WorkflowKind, WorkflowSpec


TOOL_MODULES = [
    ("detect_task", detect_task),
    ("select_workflow", select_workflow),
    ("validate_required_inputs", validate_required_inputs),
    ("validate_graph_contract", validate_graph_contract),
    ("load_workflow", load_workflow),
    ("mutate_workflow", mutate_workflow),
    ("submit_to_comfy", submit_to_comfy),
    ("watch_progress", watch_progress),
    ("fetch_outputs", fetch_outputs),
    ("persist_run", persist_run),
]


@pytest.mark.parametrize("name,module", TOOL_MODULES)
def test_tool_exposes_async_run(name, module):
    """Every tool module exposes an async `run` callable."""
    assert hasattr(module, "run"), f"{name}: missing `run` attribute"
    assert asyncio.iscoroutinefunction(module.run), f"{name}: `run` is not async"


def _make_trace() -> ToolTrace:
    tmp = Path(tempfile.mkdtemp())
    return ToolTrace(run_id="unit", trace_dir=tmp)


def test_detect_task_emits_ok_for_portrait():
    trace = _make_trace()
    result = asyncio.run(detect_task.run(
        trace,
        user_prompt="realistic female portrait",
        mode="portrait",
        assets={},
        task_selector=None,
    ))
    assert isinstance(result, TaskSelectionResult)
    assert result.task_type == TaskType.PORTRAIT_TXT2IMG
    assert trace.tool_chain == ["detect_task"]
    assert trace.results[0].status == ToolStatus.OK


def test_detect_task_emits_failed_for_unknown_mode():
    trace = _make_trace()
    with pytest.raises(ValueError):
        asyncio.run(detect_task.run(
            trace,
            user_prompt="x",
            mode="not-a-mode",
            assets={},
            task_selector=None,
        ))
    assert trace.results and trace.results[-1].status == ToolStatus.FAILED


def test_select_workflow_emits_ok():
    trace = _make_trace()
    spec = WorkflowSpec(
        workflow_id="portrait_sdxl_v1",
        task_type=TaskType.PORTRAIT_TXT2IMG,
        workflow_path="dummy.json",
        preset_name="portrait",
        kind=WorkflowKind.TXT2IMG,
        description="",
        required_inputs=["prompt"],
        supports_retry=True,
        supports_judging=True,
        default_rewrite_mode="fallback",
        implemented=True,
    )
    registry = MagicMock()
    registry.get_default_for_task = MagicMock(return_value=spec)

    result = asyncio.run(select_workflow.run(
        trace,
        registry=registry,
        task_type=TaskType.PORTRAIT_TXT2IMG,
    ))
    assert result is spec
    assert trace.tool_chain == ["select_workflow"]
    assert trace.results[0].outputs_summary["workflow_id"] == "portrait_sdxl_v1"


def test_select_workflow_raises_when_missing():
    trace = _make_trace()
    registry = MagicMock()
    registry.get_default_for_task = MagicMock(return_value=None)
    with pytest.raises(RuntimeError):
        asyncio.run(select_workflow.run(
            trace,
            registry=registry,
            task_type=TaskType.PORTRAIT_TXT2IMG,
        ))
    assert trace.results[-1].status == ToolStatus.FAILED


def test_validate_required_inputs_passes_when_none_missing():
    trace = _make_trace()
    ts = TaskSelectionResult(
        task_type=TaskType.PORTRAIT_TXT2IMG,
        confidence=1.0,
        reason="test",
        routing_source="cli",
        required_inputs=[],
        missing_inputs=[],
    )
    asyncio.run(validate_required_inputs.run(trace, task_selection=ts, assets={}))
    assert trace.tool_chain == ["validate_required_inputs"]
    assert trace.results[0].status == ToolStatus.OK


def test_validate_required_inputs_raises_when_missing():
    trace = _make_trace()
    ts = TaskSelectionResult(
        task_type=TaskType.IMG2IMG,
        confidence=1.0,
        reason="test",
        routing_source="cli",
        required_inputs=["input_image"],
        missing_inputs=["input_image"],
    )
    with pytest.raises(ValueError):
        asyncio.run(validate_required_inputs.run(trace, task_selection=ts, assets={}))
    assert trace.results[-1].status == ToolStatus.FAILED


def test_validate_graph_contract_ok_on_valid_workflow():
    trace = _make_trace()
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 1,
                "steps": 20,
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "hi", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "agent/x", "images": ["8", 0]}},
    }
    asyncio.run(validate_graph_contract.run(
        trace, workflow=workflow, workflow_id="portrait_sdxl_v1",
    ))
    assert trace.tool_chain == ["validate_graph_contract"]
    assert trace.results[0].status == ToolStatus.OK


def test_validate_graph_contract_raises_on_missing_node():
    trace = _make_trace()
    workflow = {"3": {"class_type": "KSampler", "inputs": {}}}
    with pytest.raises(ValueError):
        asyncio.run(validate_graph_contract.run(
            trace, workflow=workflow, workflow_id="portrait_sdxl_v1",
        ))
    assert trace.results[-1].status == ToolStatus.FAILED


def test_load_workflow_wraps_mutator():
    trace = _make_trace()
    mutator = MagicMock()
    mutator.load_template = MagicMock(return_value={"9": {"inputs": {}}})
    result = asyncio.run(load_workflow.run(
        trace, mutator=mutator, workflow_path="/fake/path.json",
    ))
    assert result == {"9": {"inputs": {}}}
    assert trace.tool_chain == ["load_workflow"]


def test_mutate_workflow_wraps_apply_plan():
    trace = _make_trace()
    mr = MagicMock()
    mr.workflow_id = "wf_v1"
    mr.mutated_nodes = ["6", "7"]
    mr.applied_changes = {"steps": 30}
    mr.mutated_workflow = {"9": {"inputs": {}}}
    mutator = MagicMock()
    mutator.apply_plan = MagicMock(return_value=mr)
    plan = MagicMock(spec=ExecutionPlan)
    plan.workflow_id = "wf_v1"
    plan.preset_name = "portrait"
    plan.canonical_recipe = None
    result = asyncio.run(mutate_workflow.run(
        trace, mutator=mutator, template={}, execution_plan=plan, overrides={"steps": 30},
    ))
    assert result is mr
    assert trace.tool_chain == ["mutate_workflow"]


def test_submit_to_comfy_wraps_queue_prompt():
    trace = _make_trace()
    client = MagicMock()
    client.queue_prompt = AsyncMock(return_value="abc-123")
    prompt_id = asyncio.run(submit_to_comfy.run(trace, client=client, workflow={"9": {}}))
    assert prompt_id == "abc-123"
    assert trace.tool_chain == ["submit_to_comfy"]
    assert trace.results[0].outputs_summary["prompt_id"] == "abc-123"


def test_watch_progress_wraps_wait_for_history():
    trace = _make_trace()
    client = MagicMock()
    client.wait_for_history = AsyncMock(return_value={"status": {"status_str": "success"}, "outputs": {}})
    history = asyncio.run(watch_progress.run(trace, client=client, prompt_id="p"))
    assert history["status"]["status_str"] == "success"
    assert trace.tool_chain == ["watch_progress"]


def test_fetch_outputs_wraps_extract_images():
    trace = _make_trace()
    client = MagicMock()
    client.extract_images = MagicMock(return_value=[{"filename": "x.png", "node_id": "9"}])
    imgs = asyncio.run(fetch_outputs.run(trace, client=client, history_item={"outputs": {}}))
    assert imgs[0]["filename"] == "x.png"
    assert trace.tool_chain == ["fetch_outputs"]


def test_persist_run_records_paths():
    trace = _make_trace()
    asyncio.run(persist_run.run(
        trace, metadata_path=None, summary_path=None, status="completed",
    ))
    assert trace.tool_chain == ["persist_run"]
    assert trace.results[0].outputs_summary["metadata_path"] is None


def test_tool_trace_finalize_creates_file_and_summary_line():
    trace = _make_trace()
    asyncio.run(detect_task.run(
        trace,
        user_prompt="portrait",
        mode="portrait",
        assets={},
        task_selector=None,
    ))
    path = trace.finalize()
    assert path.exists(), "finalize must materialize the trace file"
    summary = trace.summary_line()
    assert summary.startswith("TOOL CHAIN | run_id=unit")
    assert "detect_task" in summary
    # JSONL content should be parseable
    with path.open("r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 1
    assert lines[0]["name"] == "detect_task"
    assert lines[0]["status"] == "ok"
