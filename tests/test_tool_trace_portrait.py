"""KT-2: portrait tool-chain order test.

Simulates a portrait canonical run by invoking the tool chain in the same
order that `WorkflowAgentService.run` + `SDXLAgent.generate` produce at
runtime. All underlying services/clients are mocked so the test is fast and
does not touch ComfyUI.
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


EXPECTED_PORTRAIT_CHAIN = [
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


def _build_valid_portrait_workflow() -> dict:
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 123456789,
                "steps": 30,
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
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "realistic female portrait", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "portrait_comparison/test", "images": ["8", 0]}},
    }


def test_portrait_chain_produces_expected_tool_order():
    tmp_dir = Path(tempfile.mkdtemp())
    trace = ToolTrace(run_id="portrait_test", trace_dir=tmp_dir)

    workflow = _build_valid_portrait_workflow()

    # Mocks for underlying services/clients
    registry = MagicMock()
    portrait_spec = WorkflowSpec(
        workflow_id="portrait_sdxl_v1",
        task_type=TaskType.PORTRAIT_TXT2IMG,
        workflow_path="data/workflows/sdxl_txt2img_template.json",
        preset_name="portrait",
        kind=WorkflowKind.TXT2IMG,
        description="",
        required_inputs=["prompt"],
        supports_retry=True,
        supports_judging=True,
        default_rewrite_mode="fallback",
        implemented=True,
    )
    registry.get_default_for_task = MagicMock(return_value=portrait_spec)

    mutator = MagicMock()
    mutator.load_template = MagicMock(return_value=workflow)
    mr = MagicMock()
    mr.workflow_id = "portrait_sdxl_v1"
    mr.mutated_nodes = ["3", "4", "5", "6", "7", "9"]
    mr.applied_changes = {"steps": 30, "cfg": 6.0}
    mr.mutated_workflow = workflow
    mutator.apply_plan = MagicMock(return_value=mr)

    client = MagicMock()
    client.queue_prompt = AsyncMock(return_value="portrait-prompt-id")
    client.wait_for_history = AsyncMock(return_value={"status": {"status_str": "success"}, "outputs": {"9": {"images": [{"filename": "x.png", "subfolder": "", "type": "output"}]}}})
    client.extract_images = MagicMock(return_value=[{"filename": "x.png", "subfolder": "", "type": "output", "node_id": "9"}])

    plan = MagicMock(spec=ExecutionPlan)
    plan.workflow_id = "portrait_sdxl_v1"
    plan.preset_name = "portrait"
    plan.canonical_recipe = {"checkpoint": "realvisxlV50_v50Bakedvae.safetensors"}

    async def run_chain():
        # Step 1: detect_task
        ts = await detect_task.run(
            trace, user_prompt="realistic female portrait", mode="portrait", assets={}, task_selector=None,
        )
        assert ts.task_type == TaskType.PORTRAIT_TXT2IMG

        # Step 2: select_workflow
        spec = await select_workflow.run(trace, registry=registry, task_type=ts.task_type)
        assert spec.workflow_id == "portrait_sdxl_v1"

        # Step 3: validate_required_inputs (portrait has no asset requirements)
        await validate_required_inputs.run(trace, task_selection=ts, assets={})

        # Step 4: load_workflow
        template = await load_workflow.run(trace, mutator=mutator, workflow_path=spec.workflow_path)
        assert template is workflow

        # Step 5: mutate_workflow
        mutation_result = await mutate_workflow.run(
            trace, mutator=mutator, template=template, execution_plan=plan, overrides={"cfg": 6.0},
        )
        assert mutation_result.workflow_id == "portrait_sdxl_v1"

        # Step 6: validate_graph_contract (against the mutated workflow)
        await validate_graph_contract.run(
            trace, workflow=mutation_result.mutated_workflow, workflow_id=spec.workflow_id,
        )

        # Step 7: submit_to_comfy
        prompt_id = await submit_to_comfy.run(trace, client=client, workflow=mutation_result.mutated_workflow)
        assert prompt_id == "portrait-prompt-id"

        # Step 8: watch_progress
        history = await watch_progress.run(trace, client=client, prompt_id=prompt_id)

        # Step 9: fetch_outputs
        images = await fetch_outputs.run(trace, client=client, history_item=history)
        assert images and images[0]["filename"] == "x.png"

        # Step 10: persist_run
        await persist_run.run(
            trace, metadata_path="/fake/metadata.json", summary_path="/fake/summary.txt", status="completed",
        )

    asyncio.run(run_chain())

    # Assertions on the resulting chain
    assert trace.tool_chain == EXPECTED_PORTRAIT_CHAIN, (
        f"Expected {EXPECTED_PORTRAIT_CHAIN}, got {trace.tool_chain}"
    )
    for result in trace.results:
        assert result.status.value == "ok", f"{result.name}: expected ok, got {result.status}"

    # Validation tools must be present in the chain
    assert "validate_required_inputs" in trace.tool_chain
    assert "validate_graph_contract" in trace.tool_chain

    # Trace path should resolve to a real file after finalize
    path = trace.finalize()
    assert path.exists()
