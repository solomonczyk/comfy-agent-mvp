"""
Knowledge bootstrapper for creating project knowledge bases.
"""

import json
from pathlib import Path
from typing import Optional, List

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
    ContinuityPriority,
    ReferenceStatus,
    ProjectStatus,
)


class KnowledgeBootstrapper:
    """
    Bootstrapper for creating project knowledge bases.
    
    This class does NOT call ComfyUI or generate images.
    It only creates metadata artifacts.
    """
    
    def __init__(self, base_output_dir: str = "data"):
        """Initialize the bootstrapper with base output directory."""
        self.base_output_dir = Path(base_output_dir)
    
    def bootstrap_from_source_root(
        self, 
        project_id: str, 
        source_root: str
    ) -> KBReadinessReport:
        """
        Bootstrap knowledge base from a source root directory.
        
        Args:
            project_id: Project identifier
            source_root: Path to source root directory
            
        Returns:
            KBReadinessReport: Readiness report
            
        Behavior:
        - Scan files
        - Build source_inventory
        - Infer candidate project title
        - Create preliminary series_bible if scripts are found
        - Create character_registry if character names are detected
        - Create missing references list
        - Do not approve references automatically
        """
        project_dir = self.base_output_dir / project_id / "output" / "control"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan source root
        source_inventory = self._scan_source_root(source_root)
        
        # Infer project title from source root
        project_title = self._infer_project_title(source_root)
        
        # Create project manifest
        project_manifest = ProjectManifest(
            project_id=project_id,
            project_title=project_title,
            source_root=source_root,
            status=ProjectStatus.BOOTSTRAPPING,
        )
        
        # Create preliminary series bible if scripts found
        series_bible = self._create_preliminary_series_bible(
            source_inventory, project_title
        )
        
        # Create character registry if character names detected
        character_registry = self._detect_characters(source_inventory)
        
        # Create reference pack manifest with missing references
        reference_pack = self._create_reference_pack_manifest(character_registry)
        
        # Create empty character canon (will be filled after reference selection)
        character_canon = CharacterCanon(
            character_id=project_id,
            name="placeholder",
            immutable_anchors=[],
            prompt_anchor_en="",
        )
        
        # Create style bible
        style_bible = StyleBible()
        
        # Create world bible
        world_bible = WorldBible()
        
        # Create production rules
        production_rules = ProductionRules()
        
        # Create reference lock contract (blocks generation)
        reference_lock = ReferenceLockContract(
            downstream_generation_allowed=False,
            lock_reason="knowledge base or references not approved",
        )
        
        # Save all artifacts
        self._save_artifact(project_dir, "project_manifest.json", project_manifest)
        self._save_artifact(project_dir, "source_inventory.json", source_inventory)
        self._save_artifact(project_dir, "series_bible.json", series_bible)
        self._save_artifact(project_dir, "character_registry.json", character_registry)
        self._save_artifact(project_dir, "character_canon.json", character_canon)
        self._save_artifact(project_dir, "style_bible.json", style_bible)
        self._save_artifact(project_dir, "world_bible.json", world_bible)
        self._save_artifact(project_dir, "production_rules.json", production_rules)
        self._save_artifact(project_dir, "reference_pack_manifest.json", reference_pack)
        self._save_artifact(project_dir, "reference_lock_contract.json", reference_lock)
        
        # Create readiness report
        readiness_report = KBReadinessReport(
            kb_ready=False,
            blocking_reasons=["references not approved"],
            missing_artifacts=["approved character references"],
            ready_for_reference_selection=True,
            ready_for_generation=False,
        )
        
        self._save_artifact(project_dir, "kb_readiness_report.json", readiness_report)
        
        return readiness_report
    
    def bootstrap_from_raw_brief(
        self, 
        project_id: str, 
        raw_brief: str
    ) -> KBReadinessReport:
        """
        Bootstrap knowledge base from a raw brief text.
        
        Args:
            project_id: Project identifier
            raw_brief: Raw project brief text
            
        Returns:
            KBReadinessReport: Readiness report
            
        Behavior:
        - Create minimal project_manifest
        - Create preliminary series_bible
        - Create preliminary character_registry
        - Create style_bible from user description
        - Mark reference_pack as missing
        - Block generation
        """
        project_dir = self.base_output_dir / project_id / "output" / "control"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse brief for project title
        project_title = self._extract_title_from_brief(raw_brief)
        
        # Create project manifest
        project_manifest = ProjectManifest(
            project_id=project_id,
            project_title=project_title,
            status=ProjectStatus.BOOTSTRAPPING,
        )
        
        # Create preliminary series bible from brief
        series_bible = self._create_series_bible_from_brief(raw_brief, project_title)
        
        # Create preliminary character registry
        character_registry = self._create_character_registry_from_brief(raw_brief)
        
        # Create style bible from brief
        style_bible = self._create_style_bible_from_brief(raw_brief)
        
        # Create empty inventory
        source_inventory = SourceInventory()
        
        # Create reference pack manifest as missing
        reference_pack = ReferencePackManifest(
            missing_reference_files=["all"],
            approval_required=True,
        )
        
        # Create empty character canon
        character_canon = CharacterCanon(
            character_id=project_id,
            name="placeholder",
            immutable_anchors=[],
            prompt_anchor_en="",
        )
        
        # Create world bible
        world_bible = WorldBible()
        
        # Create production rules
        production_rules = ProductionRules()
        
        # Create reference lock contract (blocks generation)
        reference_lock = ReferenceLockContract(
            downstream_generation_allowed=False,
            lock_reason="knowledge base or references not approved",
        )
        
        # Save all artifacts
        self._save_artifact(project_dir, "project_manifest.json", project_manifest)
        self._save_artifact(project_dir, "source_inventory.json", source_inventory)
        self._save_artifact(project_dir, "series_bible.json", series_bible)
        self._save_artifact(project_dir, "character_registry.json", character_registry)
        self._save_artifact(project_dir, "character_canon.json", character_canon)
        self._save_artifact(project_dir, "style_bible.json", style_bible)
        self._save_artifact(project_dir, "world_bible.json", world_bible)
        self._save_artifact(project_dir, "production_rules.json", production_rules)
        self._save_artifact(project_dir, "reference_pack_manifest.json", reference_pack)
        self._save_artifact(project_dir, "reference_lock_contract.json", reference_lock)
        
        # Create readiness report
        readiness_report = KBReadinessReport(
            kb_ready=False,
            blocking_reasons=["source root missing", "references missing"],
            missing_artifacts=["source_root", "character references"],
            ready_for_reference_selection=False,
            ready_for_generation=False,
        )
        
        self._save_artifact(project_dir, "kb_readiness_report.json", readiness_report)
        
        return readiness_report
    
    def bootstrap_empty_project(self, project_id: str) -> KBReadinessReport:
        """
        Bootstrap an empty project with minimal artifacts.
        
        Args:
            project_id: Project identifier
            
        Returns:
            KBReadinessReport: Readiness report
            
        Behavior:
        - Create kb_readiness_report with kb_ready=false
        - Ask for required production brief fields
        - Do not create fake canon
        """
        project_dir = self.base_output_dir / project_id / "output" / "control"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create readiness report only
        readiness_report = KBReadinessReport(
            kb_ready=False,
            blocking_reasons=["project brief required", "source root or brief required"],
            missing_artifacts=["project_brief", "source_root"],
            ready_for_reference_selection=False,
            ready_for_generation=False,
        )
        
        self._save_artifact(project_dir, "kb_readiness_report.json", readiness_report)
        
        return readiness_report
    
    def _scan_source_root(self, source_root: str) -> SourceInventory:
        """Scan source root and create inventory."""
        root_path = Path(source_root)
        
        inventory = SourceInventory()
        
        if not root_path.exists():
            return inventory
        
        # Count files by type
        for ext in ["*.md", "*.txt"]:
            for f in root_path.rglob(ext):
                if ext == "*.md":
                    inventory.markdown_files += 1
                elif ext == "*.txt":
                    inventory.text_files += 1
        
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif"]:
            for f in root_path.rglob(ext):
                inventory.image_files += 1
        
        for ext in ["*.mp4", "*.mov", "*.avi"]:
            for f in root_path.rglob(ext):
                inventory.video_files += 1
        
        for ext in ["*.mp3", "*.wav"]:
            for f in root_path.rglob(ext):
                inventory.audio_files += 1
        
        # Collect sample paths
        sample_paths = {}
        
        md_files = list(root_path.rglob("*.md"))
        if md_files:
            sample_paths["markdown"] = [str(f.relative_to(root_path)) for f in md_files[:3]]
        
        img_files = list(root_path.rglob("*.png"))
        if img_files:
            sample_paths["images"] = [str(f.relative_to(root_path)) for f in img_files[:3]]
        
        inventory.sample_paths = sample_paths
        
        return inventory
    
    def _infer_project_title(self, source_root: str) -> str:
        """Infer project title from source root path."""
        root_path = Path(source_root)
        return root_path.name
    
    def _create_preliminary_series_bible(
        self, 
        inventory: SourceInventory, 
        project_title: str
    ) -> SeriesBible:
        """Create preliminary series bible from inventory."""
        return SeriesBible(
            title=project_title,
            format="short_form",
            story_summary="Preliminary bible from source scan",
        )
    
    def _detect_characters(self, inventory: SourceInventory) -> CharacterRegistry:
        """Detect characters from source inventory."""
        # In a real implementation, this would parse scripts to find character names
        # For now, return empty registry
        return CharacterRegistry()
    
    def _create_reference_pack_manifest(
        self, 
        character_registry: CharacterRegistry
    ) -> ReferencePackManifest:
        """Create reference pack manifest."""
        missing_refs = []
        for char in character_registry.characters:
            if char.reference_required and char.reference_status == ReferenceStatus.MISSING:
                missing_refs.append(f"{char.name}_reference")
        
        return ReferencePackManifest(
            expected_reference_types=["identity", "outfit", "mood"],
            missing_reference_files=missing_refs,
            approval_required=True,
        )
    
    def _extract_title_from_brief(self, brief: str) -> str:
        """Extract title from brief text."""
        lines = brief.strip().split('\n')
        return lines[0] if lines else "Untitled Project"
    
    def _create_series_bible_from_brief(
        self, 
        brief: str, 
        project_title: str
    ) -> SeriesBible:
        """Create series bible from brief."""
        return SeriesBible(
            title=project_title,
            story_summary=brief[:500] if len(brief) > 500 else brief,
        )
    
    def _create_character_registry_from_brief(self, brief: str) -> CharacterRegistry:
        """Create character registry from brief."""
        # In a real implementation, this would parse the brief for character names
        return CharacterRegistry()
    
    def _create_style_bible_from_brief(self, brief: str) -> StyleBible:
        """Create style bible from brief."""
        return StyleBible(
            visual_style="cinematic",
        )
    
    def _save_artifact(self, project_dir: Path, filename: str, artifact):
        """Save artifact to JSON file."""
        filepath = project_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(artifact.to_dict(), f, indent=2, ensure_ascii=False)
