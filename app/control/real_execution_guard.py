"""MK-CTRL15 — Global real execution guard and audit.

Provides a global kill switch for real subprocess execution via environment variable.
Real execution requires triple lock:
1. service allow_real_execution=True
2. runner allow_subprocess_execution=True
3. COMFY_AGENT_REAL_EXECUTION_ENABLED is enabled
"""
from __future__ import annotations

import os


def is_real_execution_globally_enabled() -> bool:
    """Check if real execution is globally enabled via environment variable.
    
    Environment variable: COMFY_AGENT_REAL_EXECUTION_ENABLED
    Accepted values (case-insensitive): "1", "true", "yes"
    Everything else (including missing) means disabled.
    
    Returns:
        True if global guard is enabled, False otherwise.
    """
    value = os.getenv("COMFY_AGENT_REAL_EXECUTION_ENABLED", "").strip().lower()
    return value in {"1", "true", "yes"}


def real_execution_guard_status() -> dict:
    """Get current status of the global real execution guard.
    
    Returns:
        Dict with env_var name, enabled status, and current value.
    """
    return {
        "env_var": "COMFY_AGENT_REAL_EXECUTION_ENABLED",
        "enabled": is_real_execution_globally_enabled(),
        "value": os.getenv("COMFY_AGENT_REAL_EXECUTION_ENABLED"),
    }
