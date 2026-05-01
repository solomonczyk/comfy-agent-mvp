"""Visual QA contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class VisualQAContract:
    """Contract for visual QA results."""
    quality_score: Optional[float] = None
    verdict: Optional[str] = None
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
