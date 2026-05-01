"""Brief intake contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class BriefIntakeContract:
    """Contract for brief intake results."""
    brief_id: Optional[str] = None
    brief_content: Optional[str] = None
    parsed_sections: Dict[str, Any] = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
