"""Route classification contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class RouteClassificationContract:
    """Contract for route classification results."""
    route_family: Optional[str] = None
    confidence: float = 0.0
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    policy: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
