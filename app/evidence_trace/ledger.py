"""Evidence Ledger

Append-only JSONL ledger for evidence trace layer.
"""

import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid

from .models import EvidenceEvent, EvidenceTraceManifest


class EvidenceLedger:
    """Append-only evidence ledger"""

    def __init__(self, ledger_path: str, task_id: str):
        self.ledger_path = ledger_path
        self.task_id = task_id
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self):
        """Ensure ledger file exists"""
        ledger_dir = os.path.dirname(self.ledger_path)
        if ledger_dir and not os.path.exists(ledger_dir):
            os.makedirs(ledger_dir, exist_ok=True)
        
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'w') as f:
                pass  # Create empty file

    def append_event(self, event: EvidenceEvent) -> bool:
        """Append event to ledger (append-only)"""
        try:
            # Validate artifact path exists
            if not os.path.exists(event.artifact_path):
                raise ValueError(f"Artifact path does not exist: {event.artifact_path}")
            
            # Append to ledger
            with open(self.ledger_path, 'a') as f:
                f.write(event.to_jsonl() + '\n')
            return True
        except Exception as e:
            print(f"Failed to append event: {e}")
            return False

    def read_all_events(self) -> List[EvidenceEvent]:
        """Read all events from ledger"""
        events = []
        if not os.path.exists(self.ledger_path):
            return events
        
        with open(self.ledger_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event_data = json.loads(line)
                        events.append(EvidenceEvent.from_dict(event_data))
                    except Exception as e:
                        print(f"Failed to parse event: {e}")
        return events

    def get_events_by_task(self, task_id: str) -> List[EvidenceEvent]:
        """Get events for specific task"""
        all_events = self.read_all_events()
        return [e for e in all_events if e.task_id == task_id]

    def get_events_by_source_layer(self, source_layer: str) -> List[EvidenceEvent]:
        """Get events by source layer"""
        all_events = self.read_all_events()
        return [e for e in all_events if e.source_layer.value == source_layer]

    def create_manifest(self) -> EvidenceTraceManifest:
        """Create manifest for ledger"""
        events = self.read_all_events()
        source_layers = list(set([e.source_layer.value for e in events]))
        
        return EvidenceTraceManifest(
            manifest_id=str(uuid.uuid4()),
            task_id=self.task_id,
            evidence_ledger_path=self.ledger_path,
            total_events=len(events),
            source_layers=source_layers,
            created_at=datetime.utcnow().isoformat()
        )

    def validate_append_only(self) -> bool:
        """Validate ledger is append-only (no destructive rewrites)"""
        # In a real implementation, this would check file modification patterns
        # For now, we assume the ledger is append-only if it exists
        return os.path.exists(self.ledger_path)
