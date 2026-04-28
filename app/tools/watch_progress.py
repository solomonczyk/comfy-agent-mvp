"""Tool: watch_progress — wait for a ComfyUI prompt to finish executing.

Thin wrapper around `ComfyClient.wait_for_history`. The duration recorded
by this tool reflects real generation time (seconds to minutes for SDXL).
"""

import time
from collections.abc import Callable
from typing import Any

from app.comfy.comfy_client import ComfyClient
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus


StatusCallback = Callable[[str, dict[str, Any] | None], None]


async def run(
    trace: ToolTrace | None,
    client: ComfyClient,
    prompt_id: str,
    status_callback: StatusCallback | None = None,
) -> dict[str, Any]:
    """Wait for ComfyUI to finish executing the given prompt_id.

    Returns the history item from ComfyUI.

    Raises:
        RuntimeError: If the run never reports success within the poll budget.
    """
    start = time.perf_counter()
    inputs_summary = {"prompt_id": prompt_id}
    try:
        history_item = await client.wait_for_history(
            prompt_id,
            status_callback=status_callback,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        status_obj = history_item.get("status", {}) if isinstance(history_item, dict) else {}
        if trace is not None:
            trace.emit(ToolResult(
                name="watch_progress",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "status_str": status_obj.get("status_str") if isinstance(status_obj, dict) else None,
                    "has_outputs": bool(history_item.get("outputs")) if isinstance(history_item, dict) else False,
                },
                duration_ms=duration_ms,
            ))
        return history_item
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="watch_progress",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
