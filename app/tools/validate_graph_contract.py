"""Tool: validate_graph_contract — check a mutated workflow against node contracts.

Walks the registered `NodeContract` set for the given workflow_id and
validates each required node in the mutated workflow. Raises `ValueError`
on the first contract failure (listing all failures in the message).
"""

import time
from typing import Any

from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.node_contracts import get_all_contracts


async def run(
    trace: ToolTrace | None,
    workflow: dict[str, Any],
    workflow_id: str,
) -> None:
    """Validate the mutated workflow against its node contracts.

    Raises:
        ValueError: If any node contract is violated.
    """
    start = time.perf_counter()
    inputs_summary = {
        "workflow_id": workflow_id,
        "node_count": len(workflow) if isinstance(workflow, dict) else 0,
    }
    try:
        contracts = get_all_contracts(workflow_id)
        failures: list[str] = []
        for node_id, contract in contracts.items():
            node_data = workflow.get(node_id)
            if node_data is None:
                failures.append(f"node {node_id}: missing from workflow")
                continue
            if not isinstance(node_data, dict):
                failures.append(f"node {node_id}: not a dict")
                continue
            is_valid, error_message = contract.validate_node(node_data)
            if not is_valid:
                failures.append(f"node {node_id}: {error_message}")

        if failures:
            raise ValueError(
                "Graph contract validation failed: " + "; ".join(failures)
            )

        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="validate_graph_contract",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "validated_node_ids": sorted(contracts.keys()),
                    "failures": [],
                },
                duration_ms=duration_ms,
            ))
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="validate_graph_contract",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
