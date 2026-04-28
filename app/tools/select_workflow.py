"""Tool: select_workflow — pick a WorkflowSpec for a given task type.

Thin wrapper around `WorkflowRegistry.get_default_for_task`. Emits which
workflow was chosen and whether it was the default.
"""

import time

from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType, WorkflowSpec


async def run(
    trace: ToolTrace | None,
    registry: WorkflowRegistry,
    task_type: TaskType,
) -> WorkflowSpec:
    """Look up the default workflow for a task type.

    Raises:
        RuntimeError: If no workflow is registered for the given task type.
    """
    start = time.perf_counter()
    inputs_summary = {"task_type": task_type.value}
    try:
        spec = registry.get_default_for_task(task_type)
        if spec is None:
            raise RuntimeError(f"No workflow registered for task type: {task_type.value}")

        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="select_workflow",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "workflow_id": spec.workflow_id,
                    "preset_name": spec.preset_name,
                    "kind": spec.kind.value if spec.kind else None,
                    "implemented": spec.implemented,
                },
                duration_ms=duration_ms,
            ))
        return spec
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="select_workflow",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
