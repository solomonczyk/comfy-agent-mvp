"""Tool: persist_run — observational record of metadata+summary persistence.

Metadata is actually written to disk by `RunMetadataService.persist_terminal_report`
inside the generation service. This tool is a post-hoc observation emitted
after the generation service returns, recording where the files landed.

Designed to be side-effect-free: it just records paths that already exist.
"""

import time
from pathlib import Path

from app.tools.tool_trace import ToolTrace
from app.tools.tool_types import ToolResult, ToolStatus


async def run(
    trace: ToolTrace | None,
    metadata_path: str | None,
    summary_path: str | None,
    status: str,
) -> None:
    """Record a persist_run event.

    Args:
        trace: Optional ToolTrace.
        metadata_path: Path to the run metadata JSON (may be None for failed runs).
        summary_path: Path to the run summary txt (may be None for failed runs).
        status: Final run status string (`completed` / `failed`).
    """
    start = time.perf_counter()
    inputs_summary = {"status": status}
    notes: list[str] = []

    metadata_exists = False
    summary_exists = False
    if metadata_path:
        try:
            metadata_exists = Path(metadata_path).exists()
        except OSError:
            metadata_exists = False
    if summary_path:
        try:
            summary_exists = Path(summary_path).exists()
        except OSError:
            summary_exists = False

    if metadata_path and not metadata_exists:
        notes.append("metadata_path reported but file does not exist on disk")
    if summary_path and not summary_exists:
        notes.append("summary_path reported but file does not exist on disk")

    duration_ms = int((time.perf_counter() - start) * 1000)
    if trace is not None:
        trace.emit(ToolResult(
            name="persist_run",
            status=ToolStatus.OK,
            inputs_summary=inputs_summary,
            outputs_summary={
                "metadata_path": metadata_path,
                "summary_path": summary_path,
                "metadata_exists": metadata_exists,
                "summary_exists": summary_exists,
            },
            duration_ms=duration_ms,
            notes=notes,
        ))
