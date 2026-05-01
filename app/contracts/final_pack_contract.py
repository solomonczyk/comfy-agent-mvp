"""Final pack contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class FinalPackContract:
    """Contract for final acceptance pack."""
    acceptance_status: Optional[str] = None
    final_artifacts: List[str] = field(default_factory=list)
    quality_summary: Optional[str] = None
    sign_off: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
