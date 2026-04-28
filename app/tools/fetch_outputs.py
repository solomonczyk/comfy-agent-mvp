"""Tool: fetch_outputs — extract image metadata from a completed ComfyUI history item.

Thin wrapper around `ComfyClient.extract_images`. No network I/O; this just
reads from the history dict produced by `watch_progress`.
"""

import time
from typing import Any

from app.comfy.comfy_client import ComfyClient
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus


async def run(
    trace: ToolTrace | None,
    client: ComfyClient,
    history_item: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract image records from a ComfyUI history item.

    Raises:
        RuntimeError: If no images were produced (the caller decides whether
            this is a hard failure or not; we just report what we see).
    """
    start = time.perf_counter()
    inputs_summary = {
        "has_outputs": bool(history_item.get("outputs")) if isinstance(history_item, dict) else False,
    }
    try:
        images = client.extract_images(history_item)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="fetch_outputs",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "image_count": len(images),
                    "filenames": [img.get("filename") for img in images],
                },
                duration_ms=duration_ms,
            ))
        return images
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="fetch_outputs",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
