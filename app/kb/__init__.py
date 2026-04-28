"""
Knowledge Bootstrap module for project knowledge base management.
"""

from app.kb.models import (
    ProjectManifest,
    SourceInventory,
    SeriesBible,
    CharacterRegistry,
    CharacterEntry,
    CharacterCanon,
    StyleBible,
    WorldBible,
    ProductionRules,
    ReferencePackManifest,
    ReferenceLockContract,
    KBReadinessReport,
    GateDecision,
    ProjectStatus,
    ContinuityPriority,
    ReferenceStatus,
)

from app.kb.bootstrap import KnowledgeBootstrapper
from app.kb.validator import KBValidator
from app.kb.gate import KnowledgeGate

__all__ = [
    # Models
    "ProjectManifest",
    "SourceInventory",
    "SeriesBible",
    "CharacterRegistry",
    "CharacterEntry",
    "CharacterCanon",
    "StyleBible",
    "WorldBible",
    "ProductionRules",
    "ReferencePackManifest",
    "ReferenceLockContract",
    "KBReadinessReport",
    "GateDecision",
    "ProjectStatus",
    "ContinuityPriority",
    "ReferenceStatus",
    # Classes
    "KnowledgeBootstrapper",
    "KBValidator",
    "KnowledgeGate",
]
