"""
Controlled visual generation gate authorization.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class GateAuthorization:
    """Creates and validates the generation gate authorization artifact."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.gate_dir = self.control_dir / "controlled_visual_generation_gate"

    def create(
        self,
        authorized_by: str = "human_operator",
        max_generations: int = 1,
    ) -> Dict[str, Any]:
        """Create generation_gate_authorization.json."""
        self.gate_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "task_id": self.TASK_ID,
            "document_type": "generation_gate_authorization",
            "timestamp": self._now(),
            "generation_authorized": True,
            "authorized_by": authorized_by,
            "authorization_scope": "one_fresh_visual_candidate_only",
            "max_generations": max_generations,
            "retry_authorized": False,
            "second_generation_allowed": False,
            "stop_after_generation": True,
            "visual_qa_acceptance_allowed": False,
            "operator_visual_acceptance_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
        }

        self._write(self.gate_dir / "generation_gate_authorization.json", auth)
        return auth

    def load(self) -> Dict[str, Any]:
        path = self.gate_dir / "generation_gate_authorization.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_authorized(self) -> bool:
        auth = self.load()
        return bool(auth.get("generation_authorized", False))

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
