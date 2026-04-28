"""Typed domain types for branch execution.

This module provides strongly-typed domain objects for branch path,
replacing weak dict[str, Any] payloads with structured types.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkflowSpec:
    """Typed workflow specification for branch execution.
    
    Replaces dict[str, Any] with structured type.
    """
    workflow_id: str
    workflow_path: str
    api_name: str | None = None
    class_type: str | None = None
    version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "WorkflowSpec":
        """Create WorkflowSpec from dict for backward compatibility."""
        return cls(
            workflow_id=spec.get("workflow_id", ""),
            workflow_path=spec.get("workflow_path", ""),
            api_name=spec.get("api_name"),
            class_type=spec.get("class_type"),
            version=spec.get("version"),
            metadata=spec.get("metadata", {}),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_path": self.workflow_path,
            "api_name": self.api_name,
            "class_type": self.class_type,
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AssetBundle:
    """Typed asset container for branch execution.
    
    Replaces raw dict[str, Any] assets with structured type.
    """
    input_image: str | None = None
    mask_image: str | None = None
    reference_images: list[str] = field(default_factory=list)
    control_images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, assets: dict[str, Any] | None) -> "AssetBundle":
        """Create AssetBundle from dict for backward compatibility."""
        if not assets:
            return cls()
        
        return cls(
            input_image=assets.get("input_image"),
            mask_image=assets.get("mask_image"),
            reference_images=assets.get("reference_images", []),
            control_images=assets.get("control_images", []),
            metadata=assets.get("metadata", {}),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        result = {"metadata": self.metadata}
        if self.input_image:
            result["input_image"] = self.input_image
        if self.mask_image:
            result["mask_image"] = self.mask_image
        if self.reference_images:
            result["reference_images"] = self.reference_images
        if self.control_images:
            result["control_images"] = self.control_images
        return result
