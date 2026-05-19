"""Evidence Trace Layer - Project-Agnostic Audit Ledger

This module provides a universal evidence trace layer that records key decisions
across the project-agnostic pipeline.
"""

from .models import (
    SourceLayer,
    DecisionStatus,
    EvidenceEvent,
    EvidenceTraceManifest,
)
from .ledger import EvidenceLedger
from .consistency_checker import ConsistencyChecker

__all__ = [
    "SourceLayer",
    "DecisionStatus",
    "EvidenceEvent",
    "EvidenceTraceManifest",
    "EvidenceLedger",
    "ConsistencyChecker",
]
