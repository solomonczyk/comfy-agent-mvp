"""
Context Pack

Structured context pack from canonical references, Visual Reference Curator artifacts,
rejected outputs, previous prompts/workflows/manifests.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path


@dataclass
class ContextPack:
    """
    Structured context pack for LLM decision making.

    Aggregates:
    - canonical_references folder
    - Visual Reference Curator artifacts
    - previous rejected asset
    - previous prompt/workflow
    - operator rejection reason
    - accepted canonical reference set
    - negative references
    - quality references
    - framing requirements
    """

    # Previous generation info
    previous_prompt_id: Optional[str] = None
    previous_asset_path: Optional[str] = None
    previous_rejection_reason: Optional[str] = None
    previous_prompt_manifest: Optional[Dict[str, Any]] = None
    previous_workflow_manifest: Optional[Dict[str, Any]] = None

    # Reference information
    canonical_references: Dict[str, List[str]] = field(default_factory=dict)
    visual_reference_curator_artifacts: Optional[Dict[str, Any]] = None
    accepted_canonical_reference_set: List[str] = field(default_factory=list)
    negative_references: List[str] = field(default_factory=list)
    quality_references: List[str] = field(default_factory=list)

    # Framing requirements
    framing_requirements: Dict[str, Any] = field(default_factory=lambda: {
        "required_framing": "medium_or_full_character_in_environment",
        "forbid_extreme_closeup": True,
        "forbid_face_crop": True,
        "face_must_be_fully_visible": True,
        "environment_visible": True,
    })

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    project_root: Optional[str] = None
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context pack to dictionary."""
        return {
            "previous_prompt_id": self.previous_prompt_id,
            "previous_asset_path": self.previous_asset_path,
            "previous_rejection_reason": self.previous_rejection_reason,
            "previous_prompt_manifest": self.previous_prompt_manifest,
            "previous_workflow_manifest": self.previous_workflow_manifest,
            "canonical_references": self.canonical_references,
            "visual_reference_curator_artifacts": self.visual_reference_curator_artifacts,
            "accepted_canonical_reference_set": self.accepted_canonical_reference_set,
            "negative_references": self.negative_references,
            "quality_references": self.quality_references,
            "framing_requirements": self.framing_requirements,
            "created_at": self.created_at,
            "project_root": self.project_root,
            "task_id": self.task_id,
        }

    def load_from_project(
        self,
        project_root: str,
        previous_prompt_id: str,
        previous_asset_path: str,
        rejection_reason: str,
    ) -> None:
        """
        Load context pack from project directory structure.

        Args:
            project_root: Path to project root
            previous_prompt_id: ID of previous prompt
            previous_asset_path: Path to previous rejected asset
            rejection_reason: Operator rejection reason
        """
        self.project_root = project_root
        self.previous_prompt_id = previous_prompt_id
        self.previous_asset_path = previous_asset_path
        self.previous_rejection_reason = rejection_reason

        # Load canonical references
        self._load_canonical_references(project_root)

        # Load visual reference curator artifacts
        self._load_visual_reference_curator_artifacts(project_root)

        # Load previous prompt/workflow manifests
        self._load_previous_manifests(project_root, previous_prompt_id)

    def _load_canonical_references(self, project_root: str) -> None:
        """Load canonical references from directory."""
        canonical_refs_path = Path(project_root) / "input" / "canonical_references"

        if not canonical_refs_path.exists():
            return

        # Load reference manifest
        manifest_path = canonical_refs_path / "reference_manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                self.canonical_references = manifest.get("canonical_references", {})

        # Collect actual reference files
        for category in ["01_identity", "02_face_details", "03_costume_materials", "04_style_light", "05_environment", "06_quality_negative"]:
            category_path = canonical_refs_path / category
            if category_path.exists():
                refs = [str(f) for f in category_path.iterdir() if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg"]]
                self.canonical_references[category] = refs

                # Track quality references separately
                if category == "02_face_details":
                    self.quality_references.extend(refs)
                elif category == "06_quality_negative":
                    self.negative_references.extend(refs)

    def _load_visual_reference_curator_artifacts(self, project_root: str) -> None:
        """Load visual reference curator artifacts."""
        curator_path = (
            Path(project_root) / "output" / "control" / "visual_reference_curator_agent_contract.json"
        )

        if curator_path.exists():
            with open(curator_path, "r", encoding="utf-8") as f:
                self.visual_reference_curator_artifacts = json.load(f)

    def _load_previous_manifests(self, project_root: str, prompt_id: str) -> None:
        """Load previous prompt and workflow manifests."""
        # Look for prompt manifest
        prompt_manifest_path = (
            Path(project_root) / "output" / "control" / f"prompt_{prompt_id}.json"
        )

        if prompt_manifest_path.exists():
            with open(prompt_manifest_path, "r", encoding="utf-8") as f:
                self.previous_prompt_manifest = json.load(f)

        # Look for workflow manifest
        workflow_manifest_path = (
            Path(project_root) / "output" / "control" / "workflow_manifest.json"
        )

        if workflow_manifest_path.exists():
            with open(workflow_manifest_path, "r", encoding="utf-8") as f:
                self.previous_workflow_manifest = json.load(f)

    def save(self, path: str) -> None:
        """Save context pack to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ContextPack":
        """Load context pack from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
