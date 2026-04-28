"""Tool trace collector.

A ToolTrace collects ToolResult records for a single agent run and persists
them as a JSONL file under `data/traces/<run_id>.jsonl`. The trace also
exposes an ordered `tool_chain` list and a one-line summary string.

Design rules:
- Append-only JSONL. One ToolResult per line.
- Synchronous I/O. No network, no async.
- If the trace directory is missing it is created lazily on first emit.
- `finalize()` is idempotent.
"""

import json
from pathlib import Path

from app.tools.tool_types import ToolResult


class ToolTrace:
    """Per-run, ordered collector of tool invocations."""

    def __init__(self, run_id: str, trace_dir: str | Path) -> None:
        """Initialize a trace for a given run.

        Args:
            run_id: Identifier that becomes the trace file stem.
            trace_dir: Directory under which `<run_id>.jsonl` is written.
        """
        self.run_id = run_id
        self.trace_dir = Path(trace_dir)
        self._results: list[ToolResult] = []
        self._path = self.trace_dir / f"{run_id}.jsonl"
        self._finalized = False

    @property
    def path(self) -> Path:
        """Absolute path to the trace JSONL file."""
        return self._path.resolve()

    @property
    def tool_chain(self) -> list[str]:
        """Ordered list of tool names as emitted."""
        return [r.name for r in self._results]

    @property
    def total_ms(self) -> int:
        """Sum of all emitted tool durations, in milliseconds."""
        return sum(r.duration_ms for r in self._results)

    @property
    def results(self) -> list[ToolResult]:
        """Read-only copy of the emitted ToolResult objects."""
        return list(self._results)

    def emit(self, result: ToolResult) -> None:
        """Append a ToolResult to the trace and write it as a JSONL line."""
        self._results.append(result)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def finalize(self) -> Path:
        """Mark the trace as finalized and return its absolute path.

        Idempotent. Safe to call even if no results were emitted.
        """
        self._finalized = True
        # Ensure the file exists even for zero-emit traces so downstream code
        # can reliably reference `trace_path`.
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()
        return self.path

    def summary_line(self) -> str:
        """Return the one-line terminal summary for this trace."""
        tools = ",".join(self.tool_chain)
        return (
            f"TOOL CHAIN | run_id={self.run_id} | tools={tools} | "
            f"total_ms={self.total_ms}"
        )
