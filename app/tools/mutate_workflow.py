"""Tool: mutate_workflow — apply an ExecutionPlan to a workflow template.

Thin wrapper around `WorkflowMutator.apply_plan`. The canonical-recipe merge
happens inside `apply_plan` (via the optional `overrides` argument), so the
KT-2 tool chain does not need a separate `apply_canonical_recipe` step.
"""

import time
from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.workflow_mutator import WorkflowMutator


async def run(
    trace: ToolTrace | None,
    mutator: WorkflowMutator,
    template: dict[str, Any],
    execution_plan: ExecutionPlan,
    overrides: dict[str, Any] | None = None,
) -> Any:
    """Apply an ExecutionPlan (and optional overrides) to a template.

    Returns the MutationResult produced by the mutator. Re-raises any
    `MutationError`.
    """
    start = time.perf_counter()
    inputs_summary = {
        "workflow_id": execution_plan.workflow_id,
        "preset_name": execution_plan.preset_name,
        "has_canonical_recipe": execution_plan.canonical_recipe is not None,
        "override_keys": sorted((overrides or {}).keys()),
    }
    try:
        if overrides is not None:
            mutation_result = mutator.apply_plan(template, execution_plan, overrides=overrides)
        else:
            mutation_result = mutator.apply_plan(template, execution_plan)

        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="mutate_workflow",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "workflow_id": mutation_result.workflow_id,
                    "mutated_nodes": list(mutation_result.mutated_nodes),
                    "applied_change_keys": sorted(mutation_result.applied_changes.keys()),
                },
                duration_ms=duration_ms,
            ))
        return mutation_result
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="mutate_workflow",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
