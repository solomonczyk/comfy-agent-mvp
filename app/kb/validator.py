"""
Knowledge base validator for checking artifact completeness.
"""

import json
from pathlib import Path
from typing import List, Optional

from app.kb.models import (
    ProjectManifest,
    SourceInventory,
    SeriesBible,
    CharacterRegistry,
    CharacterCanon,
    StyleBible,
    WorldBible,
    ProductionRules,
    ReferencePackManifest,
    ReferenceLockContract,
    KBReadinessReport,
)


class KBValidator:
    """Validator for knowledge base artifacts."""
    
    REQUIRED_ARTIFACTS = [
        "project_manifest.json",
        "source_inventory.json",
        "series_bible.json",
        "character_registry.json",
        "character_canon.json",
        "style_bible.json",
        "world_bible.json",
        "production_rules.json",
        "reference_pack_manifest.json",
        "reference_lock_contract.json",
        "kb_readiness_report.json",
    ]
    
    def __init__(self, base_output_dir: str = "data"):
        """Initialize the validator with base output directory."""
        self.base_output_dir = Path(base_output_dir)
    
    def validate_project(self, project_id: str) -> KBReadinessReport:
        """
        Validate a project's knowledge base readiness.
        
        Args:
            project_id: Project identifier
            
        Returns:
            KBReadinessReport: Readiness report
        """
        project_dir = self.base_output_dir / project_id / "output" / "control"
        
        missing_artifacts = []
        blocking_reasons = []
        
        # Check for required artifacts
        for artifact in self.REQUIRED_ARTIFACTS:
            if not (project_dir / artifact).exists():
                missing_artifacts.append(artifact)
        
        if missing_artifacts:
            blocking_reasons.append(f"Missing required artifacts: {', '.join(missing_artifacts)}")
        
        # Check reference lock contract if it exists
        reference_lock = self._load_reference_lock(project_dir)
        if reference_lock:
            if not reference_lock.downstream_generation_allowed:
                blocking_reasons.append("Reference lock not approved")
        
        # Check readiness report if it exists
        existing_report = self._load_readiness_report(project_dir)
        
        ready_for_generation = (
            len(missing_artifacts) == 0
            and reference_lock is not None
            and reference_lock.downstream_generation_allowed
        )
        
        ready_for_reference_selection = (
            len(missing_artifacts) <= 2  # Allow missing canon during selection
            and (project_dir / "series_bible.json").exists()
        )
        
        kb_ready = ready_for_generation
        
        report = KBReadinessReport(
            kb_ready=kb_ready,
            blocking_reasons=blocking_reasons,
            missing_artifacts=missing_artifacts,
            ready_for_reference_selection=ready_for_reference_selection,
            ready_for_generation=ready_for_generation,
        )
        
        return report
    
    def _load_reference_lock(self, project_dir: Path) -> Optional[ReferenceLockContract]:
        """Load reference lock contract."""
        filepath = project_dir / "reference_lock_contract.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ReferenceLockContract.from_dict(data)
        except Exception:
            return None
    
    def _load_readiness_report(self, project_dir: Path) -> Optional[KBReadinessReport]:
        """Load existing readiness report."""
        filepath = project_dir / "kb_readiness_report.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return KBReadinessReport.from_dict(data)
        except Exception:
            return None
