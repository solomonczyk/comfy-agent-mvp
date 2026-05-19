"""Evidence Trace Models

Defines the data models for evidence trace and audit ledger.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import json


class SourceLayer(Enum):
    """Source layer for evidence events"""
    WORKFLOW_REGISTRY = "workflow_registry"
    REFERENCE_PACK = "reference_pack"
    REFERENCE_BINDING = "reference_binding"
    REFERENCE_SET = "reference_set"
    WORKFLOW_READINESS = "workflow_readiness"
    RUNTIME_GATE = "runtime_gate"
    TOOL_POLICY = "tool_policy"


class DecisionStatus(Enum):
    """Decision status for evidence events"""
    READY = "ready"
    PENDING = "pending"
    BLOCKED = "blocked"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    COMPLETE = "complete"


@dataclass
class EvidenceEvent:
    """Evidence event for project-agnostic trace layer"""
    event_id: str
    task_id: str
    source_layer: SourceLayer
    artifact_path: str
    artifact_sha256: str
    decision_status: DecisionStatus
    blocked_actions: List[str] = field(default_factory=list)
    allowed_next_action: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "source_layer": self.source_layer.value,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "decision_status": self.decision_status.value,
            "blocked_actions": self.blocked_actions,
            "allowed_next_action": self.allowed_next_action,
            "timestamp": self.timestamp,
            "created_by": self.created_by,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            task_id=data["task_id"],
            source_layer=SourceLayer(data["source_layer"]),
            artifact_path=data["artifact_path"],
            artifact_sha256=data["artifact_sha256"],
            decision_status=DecisionStatus(data["decision_status"]),
            blocked_actions=data.get("blocked_actions", []),
            allowed_next_action=data.get("allowed_next_action"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            created_by=data.get("created_by", "system"),
            metadata=data.get("metadata", {})
        )

    def to_jsonl(self) -> str:
        """Convert to JSONL string"""
        return json.dumps(self.to_dict())

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Compute SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


@dataclass
class EvidenceTraceManifest:
    """Manifest for evidence trace layer"""
    manifest_id: str
    task_id: str
    evidence_ledger_path: str
    total_events: int
    source_layers: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "manifest_id": self.manifest_id,
            "task_id": self.task_id,
            "evidence_ledger_path": self.evidence_ledger_path,
            "total_events": self.total_events,
            "source_layers": self.source_layers,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceTraceManifest":
        """Create from dictionary"""
        return cls(
            manifest_id=data["manifest_id"],
            task_id=data["task_id"],
            evidence_ledger_path=data["evidence_ledger_path"],
            total_events=data["total_events"],
            source_layers=data.get("source_layers", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {})
        )
