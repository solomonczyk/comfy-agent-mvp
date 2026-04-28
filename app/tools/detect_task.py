"""Tool: detect_task — determine task type from prompt + mode + assets.

Wraps the mode-override / auto-routing logic that previously lived inline in
`app/agent_run.py`. The underlying behavior is unchanged; this tool exposes
the step as a named, traced event.
"""

import time
from typing import Any

from app.agent.task_selector import TaskSelectionResult, TaskSelector
from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus
from app.workflows.workflow_types import TaskType


_MODE_TO_TASK_TYPE: dict[str, tuple[TaskType, list[str]]] = {
    "portrait": (TaskType.PORTRAIT_TXT2IMG, []),
    "product": (TaskType.PRODUCT_TXT2IMG, []),
    "upscale": (TaskType.UPSCALE, ["input_image"]),
    "face-repair": (TaskType.INPAINT_FACE, ["input_image"]),
    "edit": (TaskType.IMG2IMG, ["input_image"]),
}


async def run(
    trace: ToolTrace | None,
    user_prompt: str,
    mode: str,
    assets: dict[str, Any],
    task_selector: TaskSelector | None,
) -> TaskSelectionResult:
    """Resolve a TaskSelectionResult for the run.

    Args:
        trace: Optional ToolTrace. If None, no event is emitted.
        user_prompt: Raw user prompt.
        mode: CLI mode (`auto`, `portrait`, `product`, `edit`, `upscale`, `face-repair`).
        assets: Already-resolved asset dictionary (may include `input_image`, `mask_image`).
        task_selector: TaskSelector instance used for `auto` mode routing.

    Returns:
        TaskSelectionResult describing the routed task.
    """
    start = time.perf_counter()
    inputs_summary = {
        "user_prompt": user_prompt[:120],
        "mode": mode,
        "asset_keys": sorted(assets.keys()),
    }
    try:
        if mode in _MODE_TO_TASK_TYPE:
            task_type, required_inputs = _MODE_TO_TASK_TYPE[mode]
            missing = [k for k in required_inputs if not assets.get(k)]
            result = TaskSelectionResult(
                task_type=task_type,
                confidence=1.0,
                reason=f"Mode override: {mode}",
                routing_source="cli",
                required_inputs=required_inputs,
                missing_inputs=missing,
            )
        elif mode == "auto":
            if task_selector is None:
                raise RuntimeError("task_selector is required for mode='auto'")
            result = task_selector.select(user_prompt, assets)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="detect_task",
                status=ToolStatus.OK,
                inputs_summary=inputs_summary,
                outputs_summary={
                    "task_type": result.task_type.value,
                    "confidence": result.confidence,
                    "routing_source": result.routing_source,
                    "missing_inputs": list(result.missing_inputs or []),
                },
                duration_ms=duration_ms,
            ))
        return result
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if trace is not None:
            trace.emit(ToolResult(
                name="detect_task",
                status=ToolStatus.FAILED,
                inputs_summary=inputs_summary,
                outputs_summary={},
                duration_ms=duration_ms,
                error=str(exc),
            ))
        raise
