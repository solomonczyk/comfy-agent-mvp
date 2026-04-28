"""
Director command history logging.

Director-lite writes its own read-only command history to director_history.jsonl.
This is separate from the pipeline ledger and is used for audit purposes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from app.director.models import DirectorHistoryRecord


class DirectorHistory:
    """Manages director command history."""
    
    def __init__(self, project_root: str):
        """Initialize history manager.
        
        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.history_path = self.project_root / "output" / "control" / "director_history.jsonl"
        self._ensure_history_dir()
    
    def _ensure_history_dir(self):
        """Ensure history directory exists."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_command(
        self,
        command: str,
        episode_id: str,
        shot_id: Optional[str],
        success: bool
    ) -> DirectorHistoryRecord:
        """Log a director command to history.
        
        Args:
            command: Command that was executed
            episode_id: Episode ID
            shot_id: Shot ID (optional)
            success: Whether command succeeded
            
        Returns:
            DirectorHistoryRecord that was logged
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        record = DirectorHistoryRecord(
            timestamp=timestamp,
            command=command,
            episode_id=episode_id,
            shot_id=shot_id,
            project_root=str(self.project_root),
            read_only=True,
            success=success
        )
        
        self._append_record(record)
        return record
    
    def _append_record(self, record: DirectorHistoryRecord):
        """Append a record to the history file.
        
        Args:
            record: Record to append
        """
        with open(self.history_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record.to_dict()) + '\n')
    
    def get_history(self, limit: Optional[int] = None) -> List[DirectorHistoryRecord]:
        """Read command history.
        
        Args:
            limit: Maximum number of records to return (None for all)
            
        Returns:
            List of history records
        """
        if not self.history_path.exists():
            return []
        
        records = []
        with open(self.history_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        records.append(DirectorHistoryRecord.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        # Reverse to show most recent first
        records = list(reversed(records))
        
        if limit is not None:
            records = records[:limit]
        
        return records
