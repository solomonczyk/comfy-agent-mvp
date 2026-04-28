"""Tool: validate_required_inputs — fail-fast guard on missing assets.

Mirrors the behavior of `fail_fast_guard` in `app/agent_run.py`: raises
`ValueError` when the routed task_type requires assets that are not present.
"""

import time
from typing import Any

from app.agent.task_selector import TaskSelectionResult
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus


async def run(
    trace: ToolTrace | None,
    task_selection: TaskSelectionResult,
    assets: dict[str, Any],
) -> None:
    """Validate that required assets are present for the routed task.

    Raises:
        ValueError: If any required input is missing.
    """
    start = time.perf_counter()
    missing = list(task_selection.missing_inputs or [])
    inputs_summary = {
        "task_type": task_selection.task_type.value,
        "required_inputs": list(task_selection.required_inputs or []),
        "missing_inputs": missing,
        "asset_keys": sorted(assets.keys()),
    }
    try:
        if missing:
            task_type_str = task_selection.task_type.value
            raise ValueError(
                f"FAIL-FAST: Missing required assets for {task_type_str}: "
                + ", ".join(missing)
            )

        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="validate_required_inputs",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={"missing_inputs": []},
                duration_ms=duration_ms,
            ))
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="validate_required_inputs",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
