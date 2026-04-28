"""KT-2: edit tool-chain order test.

Simulates an edit (img2img) run by invoking the tool chain in the same
order that `WorkflowAgentService.run` + `SDXLAgent.generate` produce at
runtime. All underlying services/clients are mocked so the test is fast.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

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
from app.workflows.workflow_types import TaskType, WorkflowKind, WorkflowSpec


EXPECTED_EDIT_CHAIN = [
    "detect_task",
    "select_workflow",
    "validate_required_inputs",
    "load_workflow",
    "mutate_workflow",
    "validate_graph_contract",
    "submit_to_comfy",
    "watch_progress",
    "fetch_outputs",
    "persist_run",
]


def _build_valid_img2img_workflow() -> dict:
    # Matches node_contracts.SDXL_IMG2IMG_CONTRACTS structure.
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 1,
                "steps": 25,
                "cfg": 6.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 0.6,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["8", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": "input.png"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "improve realism", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry", "clip": ["4", 1]}},
        "8": {"class_type": "VAEEncode", "inputs": {"pixels": ["5", 0], "vae": ["4", 2]}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "10": {"class_type": "SaveImage", "inputs": {"filename_prefix": "agent/img2img", "images": ["9", 0]}},
    }


def test_edit_chain_produces_expected_tool_order():
    tmp_dir = Path(tempfile.mkdtemp())
    trace = ToolTrace(run_id="edit_test", trace_dir=tmp_dir)

    workflow = _build_valid_img2img_workflow()

    registry = MagicMock()
    edit_spec = WorkflowSpec(
        workflow_id="img2img_v1",
        task_type=TaskType.IMG2IMG,
        workflow_path="data/workflows/img2img_simple_template.json",
        preset_name="portrait",
        kind=WorkflowKind.IMG2IMG,
        description="",
        required_inputs=["input_image"],
        supports_retry=True,
        supports_judging=True,
        default_rewrite_mode="raw",
        implemented=True,
    )
    registry.get_default_for_task = MagicMock(return_value=edit_spec)

    mutator = MagicMock()
    mutator.load_template = MagicMock(return_value=workflow)
    mr = MagicMock()
    mr.workflow_id = "img2img_v1"
    mr.mutated_nodes = ["3", "4", "5", "6", "7", "10"]
    mr.applied_changes = {"steps": 25}
    mr.mutated_workflow = workflow
    mutator.apply_plan = MagicMock(return_value=mr)

    client = MagicMock()
    client.queue_prompt = AsyncMock(return_value="edit-prompt-id")
    client.wait_for_history = AsyncMock(return_value={"status": {"status_str": "success"}, "outputs": {"10": {"images": [{"filename": "edit.png", "subfolder": "", "type": "output"}]}}})
    client.extract_images = MagicMock(return_value=[{"filename": "edit.png", "subfolder": "", "type": "output", "node_id": "10"}])

    plan = MagicMock(spec=ExecutionPlan)
    plan.workflow_id = "img2img_v1"
    plan.preset_name = "portrait"
    plan.canonical_recipe = None

    async def run_chain():
        ts = await detect_task.run(
            trace,
            user_prompt="improve realism and details",
            mode="edit",
            assets={"input_image": "test_input_image.png"},
            task_selector=None,
        )
        assert ts.task_type == TaskType.IMG2IMG
        # With input_image supplied, there should be no missing inputs.
        assert ts.missing_inputs == []

        spec = await select_workflow.run(trace, registry=registry, task_type=ts.task_type)
        assert spec.workflow_id == "img2img_v1"

        await validate_required_inputs.run(
            trace, task_selection=ts, assets={"input_image": "uploaded_input.png"},
        )

        template = await load_workflow.run(trace, mutator=mutator, workflow_path=spec.workflow_path)
        mutation_result = await mutate_workflow.run(
            trace, mutator=mutator, template=template, execution_plan=plan, overrides=None,
        )
        await validate_graph_contract.run(
            trace, workflow=mutation_result.mutated_workflow, workflow_id=spec.workflow_id,
        )
        prompt_id = await submit_to_comfy.run(trace, client=client, workflow=mutation_result.mutated_workflow)
        history = await watch_progress.run(trace, client=client, prompt_id=prompt_id)
        images = await fetch_outputs.run(trace, client=client, history_item=history)
        assert images and images[0]["filename"] == "edit.png"
        await persist_run.run(
            trace, metadata_path="/fake/meta.json", summary_path="/fake/summary.txt", status="completed",
        )

    asyncio.run(run_chain())

    assert trace.tool_chain == EXPECTED_EDIT_CHAIN, (
        f"Expected {EXPECTED_EDIT_CHAIN}, got {trace.tool_chain}"
    )
    for result in trace.results:
        assert result.status.value == "ok", f"{result.name}: expected ok, got {result.status}"

    # Validation tools must be present in the chain
    assert "validate_required_inputs" in trace.tool_chain
    assert "validate_graph_contract" in trace.tool_chain


def test_edit_chain_fails_fast_when_input_image_missing():
    """Regression: edit mode with no input_image must fail in validate_required_inputs."""
    tmp_dir = Path(tempfile.mkdtemp())
    trace = ToolTrace(run_id="edit_fail_test", trace_dir=tmp_dir)

    ts = asyncio.run(detect_task.run(
        trace,
        user_prompt="improve realism",
        mode="edit",
        assets={},
        task_selector=None,
    ))
    assert ts.task_type == TaskType.IMG2IMG
    assert ts.missing_inputs == ["input_image"]

    registry = MagicMock()
    edit_spec = WorkflowSpec(
        workflow_id="img2img_v1",
        task_type=TaskType.IMG2IMG,
        workflow_path="x.json",
        preset_name="portrait",
        kind=WorkflowKind.IMG2IMG,
        description="",
        required_inputs=["input_image"],
        supports_retry=True,
        supports_judging=True,
        default_rewrite_mode="raw",
        implemented=True,
    )
    registry.get_default_for_task = MagicMock(return_value=edit_spec)
    asyncio.run(select_workflow.run(trace, registry=registry, task_type=ts.task_type))

    import pytest
    with pytest.raises(ValueError):
        asyncio.run(validate_required_inputs.run(trace, task_selection=ts, assets={}))

    # Chain must stop at validate_required_inputs and that call must be FAILED
    assert trace.tool_chain == ["detect_task", "select_workflow", "validate_required_inputs"]
    assert trace.results[-1].status.value == "failed"
