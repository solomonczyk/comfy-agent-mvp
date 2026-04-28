"""Internal tool layer (KT-2).

Thin, observable wrappers around existing services/clients. Each tool module
exposes a single async `run(trace, ...)` entry point. The tool layer is
additive — if `trace` is None, tools still perform the underlying work but
emit nothing. This preserves KT-1 parity for code paths that have not yet
been wired up to the trace.
"""

from app.tools.tool_types import ToolResult, ToolStatus
from app.tools.tool_trace import ToolTrace

__all__ = ["ToolResult", "ToolStatus", "ToolTrace"]
