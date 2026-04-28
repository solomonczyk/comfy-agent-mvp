"""MK-RECIPE1 — Data models for generation recipes and settings validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationRecipe:
    """A generation recipe defines approved settings for a specific task type."""
    recipe_id: str
    task_type: str
    model_family: str
    checkpoint_allowlist: list[str]
    sampler_allowlist: list[str]
    scheduler_allowlist: list[str]
    steps_min: int
    steps_max: int
    cfg_min: float
    cfg_max: float
    batch_size_max: int
    max_pixels: int
    allowed_aspect_ratios: dict[str, list[int]]
    denoise_min: float | None = None
    denoise_max: float | None = None
    required_negative_terms: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "recipe_id": self.recipe_id,
            "task_type": self.task_type,
            "model_family": self.model_family,
            "checkpoint_allowlist": self.checkpoint_allowlist,
            "sampler_allowlist": self.sampler_allowlist,
            "scheduler_allowlist": self.scheduler_allowlist,
            "steps_min": self.steps_min,
            "steps_max": self.steps_max,
            "cfg_min": self.cfg_min,
            "cfg_max": self.cfg_max,
            "batch_size_max": self.batch_size_max,
            "max_pixels": self.max_pixels,
            "allowed_aspect_ratios": self.allowed_aspect_ratios,
            "denoise_min": self.denoise_min,
            "denoise_max": self.denoise_max,
            "required_negative_terms": self.required_negative_terms,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationRecipe":
        """Create from dictionary."""
        return cls(
            recipe_id=data["recipe_id"],
            task_type=data["task_type"],
            model_family=data["model_family"],
            checkpoint_allowlist=data["checkpoint_allowlist"],
            sampler_allowlist=data["sampler_allowlist"],
            scheduler_allowlist=data["scheduler_allowlist"],
            steps_min=data["steps_min"],
            steps_max=data["steps_max"],
            cfg_min=data["cfg_min"],
            cfg_max=data["cfg_max"],
            batch_size_max=data["batch_size_max"],
            max_pixels=data["max_pixels"],
            allowed_aspect_ratios=data["allowed_aspect_ratios"],
            denoise_min=data.get("denoise_min"),
            denoise_max=data.get("denoise_max"),
            required_negative_terms=data.get("required_negative_terms", []),
            notes=data.get("notes", []),
        )


@dataclass
class HardwareProfile:
    """Hardware profile defining safe limits for generation settings."""
    profile_id: str
    gpu_name: str
    vram_gb: float
    max_pixels_sdxl: int
    max_batch_size_sdxl: int
    recommended_batch_size_sdxl: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "gpu_name": self.gpu_name,
            "vram_gb": self.vram_gb,
            "max_pixels_sdxl": self.max_pixels_sdxl,
            "max_batch_size_sdxl": self.max_batch_size_sdxl,
            "recommended_batch_size_sdxl": self.recommended_batch_size_sdxl,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HardwareProfile":
        """Create from dictionary."""
        return cls(
            profile_id=data["profile_id"],
            gpu_name=data["gpu_name"],
            vram_gb=data["vram_gb"],
            max_pixels_sdxl=data["max_pixels_sdxl"],
            max_batch_size_sdxl=data["max_batch_size_sdxl"],
            recommended_batch_size_sdxl=data["recommended_batch_size_sdxl"],
            notes=data.get("notes", []),
        )


@dataclass
class ObservedGenerationSettings:
    """Observed generation settings from ComfyUI nodes."""
    checkpoint: str | None = None
    sampler_name: str | None = None
    scheduler: str | None = None
    steps: int | None = None
    cfg: float | None = None
    width: int | None = None
    height: int | None = None
    batch_size: int | None = None
    denoise: float | None = None
    negative_prompt: str | None = None
    raw_nodes: dict = field(default_factory=dict)
    # MK-REF1 — Reference-locked mode fields
    generation_mode: str | None = None
    reference_image_path: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "checkpoint": self.checkpoint,
            "sampler_name": self.sampler_name,
            "scheduler": self.scheduler,
            "steps": self.steps,
            "cfg": self.cfg,
            "width": self.width,
            "height": self.height,
            "batch_size": self.batch_size,
            "denoise": self.denoise,
            "negative_prompt": self.negative_prompt,
            "raw_nodes": self.raw_nodes,
            "generation_mode": self.generation_mode,
            "reference_image_path": self.reference_image_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ObservedGenerationSettings":
        """Create from dictionary."""
        return cls(
            checkpoint=data.get("checkpoint"),
            sampler_name=data.get("sampler_name"),
            scheduler=data.get("scheduler"),
            steps=data.get("steps"),
            cfg=data.get("cfg"),
            width=data.get("width"),
            height=data.get("height"),
            batch_size=data.get("batch_size"),
            denoise=data.get("denoise"),
            negative_prompt=data.get("negative_prompt"),
            raw_nodes=data.get("raw_nodes", {}),
            generation_mode=data.get("generation_mode"),
            reference_image_path=data.get("reference_image_path"),
        )


@dataclass
class RecipeIssue:
    """A validation issue found during recipe validation."""
    severity: str  # "info" | "warning" | "error"
    code: str
    message: str
    expected: dict | str | int | float | None = None
    actual: dict | str | int | float | None = None
    recommendation: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "recommendation": self.recommendation,
        }


@dataclass
class RecipeValidationResult:
    """Result of validating generation settings against a recipe."""
    verdict: str  # "pass" | "warn" | "fail"
    recipe_id: str
    task_type: str
    hardware_profile_id: str
    score: float
    issues: list[RecipeIssue] = field(default_factory=list)
    observed_settings: dict = field(default_factory=dict)
    recommended_settings: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "verdict": self.verdict,
            "recipe_id": self.recipe_id,
            "task_type": self.task_type,
            "hardware_profile_id": self.hardware_profile_id,
            "score": self.score,
            "issues": [issue.to_dict() for issue in self.issues],
            "observed_settings": self.observed_settings,
            "recommended_settings": self.recommended_settings,
        }
