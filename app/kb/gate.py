"""
Knowledge gate for blocking generation until knowledge base is ready.
"""

import json
from pathlib import Path
from typing import List

from app.kb.models import GateDecision
from app.kb.validator import KBValidator


class KnowledgeGate:
    """
    Gate that checks if generation is allowed.
    
    Generation is denied if:
    - project_manifest.json missing
    - series_bible.json missing
    - character_registry.json missing
    - style_bible.json missing
    - reference_lock_contract.json missing
    - reference_lock_contract.downstream_generation_allowed != true
    - kb_readiness_report.ready_for_generation != true
    """
    
    REQUIRED_FOR_GENERATION = [
        "project_manifest.json",
        "series_bible.json",
        "character_registry.json",
        "style_bible.json",
        "reference_lock_contract.json",
        "kb_readiness_report.json",
    ]
    
    def __init__(self, base_output_dir: str = "data"):
        """Initialize the gate with base output directory."""
        self.base_output_dir = Path(base_output_dir)
        self.validator = KBValidator(base_output_dir)
    
    def can_generate(self, project_root: Path) -> GateDecision:
        """
        Check if generation is allowed for a project.
        
        Args:
            project_root: Path to project root directory
            
        Returns:
            GateDecision: Decision with allowed status and reason
        """
        # Extract project_id from path
        # Expected path: data/<project_id>/output/control/
        try:
            project_id = self._extract_project_id(project_root)
        except ValueError as e:
            return GateDecision(
                allowed=False,
                reason=str(e),
            )
        
        project_dir = self.base_output_dir / project_id / "output" / "control"
        
        # Check for required artifacts
        missing_artifacts = []
        for artifact in self.REQUIRED_FOR_GENERATION:
            if not (project_dir / artifact).exists():
                missing_artifacts.append(artifact)
        
        if missing_artifacts:
            return GateDecision(
                allowed=False,
                reason=f"Missing required artifacts: {', '.join(missing_artifacts)}",
                missing_artifacts=missing_artifacts,
            )
        
        # Check reference lock contract
        reference_lock = self._load_reference_lock(project_dir)
        if reference_lock is None:
            return GateDecision(
                allowed=False,
                reason="reference_lock_contract.json missing or invalid",
                missing_artifacts=["reference_lock_contract.json"],
            )
        
        if not reference_lock.downstream_generation_allowed:
            return GateDecision(
                allowed=False,
                reason=f"Reference lock not approved: {reference_lock.lock_reason}",
            )
        
        # Check readiness report
        readiness_report = self._load_readiness_report(project_dir)
        if readiness_report is None:
            return GateDecision(
                allowed=False,
                reason="kb_readiness_report.json missing or invalid",
                missing_artifacts=["kb_readiness_report.json"],
            )
        
        if not readiness_report.ready_for_generation:
            return GateDecision(
                allowed=False,
                reason=f"Knowledge base not ready: {', '.join(readiness_report.blocking_reasons)}",
            )
        
        # All checks passed
        return GateDecision(
            allowed=True,
            reason="All knowledge base artifacts present and reference lock approved",
        )
    
    def _extract_project_id(self, project_root: Path) -> str:
        """Extract project_id from project root path."""
        # Expected path: data/<project_id>/output/control/ or similar
        parts = project_root.parts
        
        # Try to find the project_id
        for i, part in enumerate(parts):
            if part == "data" and i + 1 < len(parts):
                return parts[i + 1]
        
        # If project_root is the control directory
        if "output" in parts and "control" in parts:
            idx = parts.index("output")
            if idx > 0:
                return parts[idx - 1]
        
        raise ValueError(f"Cannot extract project_id from path: {project_root}")
    
    def _load_reference_lock(self, project_dir: Path):
        """Load reference lock contract."""
        filepath = project_dir / "reference_lock_contract.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            from app.kb.models import ReferenceLockContract
            return ReferenceLockContract.from_dict(data)
        except Exception:
            return None
    
    def _load_readiness_report(self, project_dir: Path):
        """Load readiness report."""
        filepath = project_dir / "kb_readiness_report.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            from app.kb.models import KBReadinessReport
            return KBReadinessReport.from_dict(data)
        except Exception:
            return None
