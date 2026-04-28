"""Tool: load_workflow — load a workflow template JSON from disk.

Thin wrapper around `WorkflowMutator.load_template`. Emits the template's
top-level node count as an output summary.
"""

import time
from pathlib import Path
from typing import Any

from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.workflow_mutator import WorkflowMutator


async def run(
    trace: ToolTrace | None,
    mutator: WorkflowMutator,
    workflow_path: str | Path,
) -> dict[str, Any]:
    """Load a workflow template and return the dict.

    Raises:
        FileNotFoundError / json.JSONDecodeError: as raised by the mutator.
    """
    start = time.perf_counter()
    inputs_summary = {"workflow_path": str(workflow_path)}
    try:
        template = mutator.load_template(workflow_path)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="load_workflow",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "node_count": len(template) if isinstance(template, dict) else 0,
                    "node_ids": sorted(template.keys()) if isinstance(template, dict) else [],
                },
                duration_ms=duration_ms,
            ))
        return template
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="load_workflow",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
