"""
Knowledge Base models for project bootstrap and validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enum."""
    INITIALIZING = "initializing"
    BOOTSTRAPPING = "bootstrapping"
    READY_FOR_REFERENCE = "ready_for_reference"
    READY_FOR_GENERATION = "ready_for_generation"
    BLOCKED = "blocked"


class ContinuityPriority(str, Enum):
    """Continuity priority enum."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReferenceStatus(str, Enum):
    """Reference status enum."""
    MISSING = "missing"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ProjectManifest:
    """Project manifest with basic project information."""
    project_id: str
    project_title: str
    source_root: Optional[str] = None
    project_type: str = "video_series"
    expected_outputs: List[str] = field(default_factory=lambda: ["video"])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = ProjectStatus.INITIALIZING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_title": self.project_title,
            "source_root": self.source_root,
            "project_type": self.project_type,
            "expected_outputs": self.expected_outputs,
            "created_at": self.created_at,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectManifest":
        return cls(**data)


@dataclass
class SourceInventory:
    """Source inventory with file counts."""
    markdown_files: int = 0
    text_files: int = 0
    image_files: int = 0
    video_files: int = 0
    audio_files: int = 0
    script_files: int = 0
    reference_files: int = 0
    sample_paths: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "markdown_files": self.markdown_files,
            "text_files": self.text_files,
            "image_files": self.image_files,
            "video_files": self.video_files,
            "audio_files": self.audio_files,
            "script_files": self.script_files,
            "reference_files": self.reference_files,
            "sample_paths": self.sample_paths,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceInventory":
        return cls(**data)


@dataclass
class SeriesBible:
    """Series bible with story information."""
    title: str
    format: str = "short_form"
    target_duration: str = "45s"
    aspect_ratio: str = "16:9"
    genre: str = "drama"
    tone: str = "serious"
    story_summary: str = ""
    arcs: List[str] = field(default_factory=list)
    episode_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "format": self.format,
            "target_duration": self.target_duration,
            "aspect_ratio": self.aspect_ratio,
            "genre": self.genre,
            "tone": self.tone,
            "story_summary": self.story_summary,
            "arcs": self.arcs,
            "episode_count": self.episode_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeriesBible":
        return cls(**data)


@dataclass
class CharacterEntry:
    """Character entry in registry."""
    name: str
    role: str
    continuity_priority: str = ContinuityPriority.HIGH
    reference_required: bool = True
    reference_status: str = ReferenceStatus.MISSING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "continuity_priority": self.continuity_priority,
            "reference_required": self.reference_required,
            "reference_status": self.reference_status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterEntry":
        return cls(**data)


@dataclass
class CharacterRegistry:
    """Character registry with all detected characters."""
    characters: List[CharacterEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": [c.to_dict() for c in self.characters],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterRegistry":
        characters = [CharacterEntry.from_dict(c) for c in data.get("characters", [])]
        return cls(characters=characters)


@dataclass
class CharacterCanon:
    """Character canon with visual anchors and drift rules."""
    character_id: str
    name: str
    immutable_anchors: List[str] = field(default_factory=list)
    optional_variants: List[str] = field(default_factory=list)
    forbidden_drift: List[str] = field(default_factory=list)
    prompt_anchor_en: str = ""
    visual_reference_required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "immutable_anchors": self.immutable_anchors,
            "optional_variants": self.optional_variants,
            "forbidden_drift": self.forbidden_drift,
            "prompt_anchor_en": self.prompt_anchor_en,
            "visual_reference_required": self.visual_reference_required,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterCanon":
        return cls(**data)


@dataclass
class StyleBible:
    """Style bible with visual style rules."""
    visual_style: str = "cinematic"
    color_palette: List[str] = field(default_factory=list)
    lighting_rules: List[str] = field(default_factory=list)
    camera_language: str = "natural"
    texture: str = "realistic"
    forbidden_styles: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "visual_style": self.visual_style,
            "color_palette": self.color_palette,
            "lighting_rules": self.lighting_rules,
            "camera_language": self.camera_language,
            "texture": self.texture,
            "forbidden_styles": self.forbidden_styles,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleBible":
        return cls(**data)


@dataclass
class WorldBible:
    """World bible with environment rules."""
    locations: List[str] = field(default_factory=list)
    environment_rules: List[str] = field(default_factory=list)
    time_period: str = "contemporary"
    mood_rules: List[str] = field(default_factory=list)
    world_specific_visual_logic: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "locations": self.locations,
            "environment_rules": self.environment_rules,
            "time_period": self.time_period,
            "mood_rules": self.mood_rules,
            "world_specific_visual_logic": self.world_specific_visual_logic,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldBible":
        return cls(**data)


@dataclass
class ProductionRules:
    """Production rules with generation constraints."""
    aspect_ratio: str = "16:9"
    duration_range: str = "30-60s"
    subtitle_required: bool = False
    voiceover_required: bool = False
    hook_required: bool = True
    continuity_required: bool = True
    generation_blocked_until_reference_lock: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "aspect_ratio": self.aspect_ratio,
            "duration_range": self.duration_range,
            "subtitle_required": self.subtitle_required,
            "voiceover_required": self.voiceover_required,
            "hook_required": self.hook_required,
            "continuity_required": self.continuity_required,
            "generation_blocked_until_reference_lock": self.generation_blocked_until_reference_lock,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionRules":
        return cls(**data)


@dataclass
class ReferencePackManifest:
    """Reference pack manifest with reference information."""
    expected_reference_types: List[str] = field(default_factory=list)
    available_reference_files: List[str] = field(default_factory=list)
    missing_reference_files: List[str] = field(default_factory=list)
    selected_references: List[str] = field(default_factory=list)
    approval_required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_reference_types": self.expected_reference_types,
            "available_reference_files": self.available_reference_files,
            "missing_reference_files": self.missing_reference_files,
            "selected_references": self.selected_references,
            "approval_required": self.approval_required,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReferencePackManifest":
        return cls(**data)


@dataclass
class ReferenceLockContract:
    """Reference lock contract that blocks generation until approved."""
    downstream_generation_allowed: bool = False
    lock_reason: str = "knowledge base or references not approved"
    approved_references: List[str] = field(default_factory=list)
    approval_timestamp: Optional[str] = None
    approved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "downstream_generation_allowed": self.downstream_generation_allowed,
            "lock_reason": self.lock_reason,
            "approved_references": self.approved_references,
            "approval_timestamp": self.approval_timestamp,
            "approved_by": self.approved_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReferenceLockContract":
        return cls(**data)


@dataclass
class KBReadinessReport:
    """Knowledge base readiness report."""
    kb_ready: bool = False
    blocking_reasons: List[str] = field(default_factory=list)
    missing_artifacts: List[str] = field(default_factory=list)
    ready_for_reference_selection: bool = False
    ready_for_generation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "kb_ready": self.kb_ready,
            "blocking_reasons": self.blocking_reasons,
            "missing_artifacts": self.missing_artifacts,
            "ready_for_reference_selection": self.ready_for_reference_selection,
            "ready_for_generation": self.ready_for_generation,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KBReadinessReport":
        return cls(**data)


@dataclass
class GateDecision:
    """Gate decision for generation permission."""
    allowed: bool
    reason: str
    missing_artifacts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "missing_artifacts": self.missing_artifacts,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateDecision":
        return cls(**data)
