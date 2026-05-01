"""Workflow technical direction contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class WorkflowTDContract:
    """Contract for workflow technical direction results."""
    workflow_type: Optional[str] = None
    node_count: Optional[int] = None
    complexity: Optional[str] = None
    technical_requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
