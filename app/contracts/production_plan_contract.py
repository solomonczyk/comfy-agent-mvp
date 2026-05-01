"""Production plan contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ProductionPlanContract:
    """Contract for production plan results."""
    strategy: Optional[str] = None
    intent: Optional[str] = None
    shot_count: Optional[int] = None
    estimated_duration: Optional[float] = None
    resources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
