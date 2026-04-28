"""Tool: submit_to_comfy — queue a mutated workflow to ComfyUI.

Thin wrapper around `ComfyClient.queue_prompt`. Emits the returned prompt_id.
"""

import time
from typing import Any

from app.comfy.comfy_client import ComfyClient
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus


async def run(
    trace: ToolTrace | None,
    client: ComfyClient,
    workflow: dict[str, Any],
) -> str:
    """Queue the workflow and return the ComfyUI prompt_id.

    Raises:
        RuntimeError: On ComfyUI API failure.
    """
    start = time.perf_counter()
    inputs_summary = {
        "node_count": len(workflow) if isinstance(workflow, dict) else 0,
    }
    try:
        prompt_id = await client.queue_prompt(workflow)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="submit_to_comfy",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={"prompt_id": prompt_id},
                duration_ms=duration_ms,
            ))
        return prompt_id
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="submit_to_comfy",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
