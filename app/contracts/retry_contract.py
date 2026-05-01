"""Retry policy contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class RetryContract:
    """Contract for retry policy results."""
    retry_allowed: bool = False
    max_retries: int = 0
    strategy: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
