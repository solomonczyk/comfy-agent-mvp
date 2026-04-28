"""Workflow type definitions for the agent system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowKind(str, Enum):
    """Kind of workflow generation method."""
    TXT2IMG = "txt2img"
    IMG2IMG = "img2img"
    INPAINT = "inpaint"
    UPSCALE = "upscale"
    CONTROLNET = "controlnet"


class TaskType(str, Enum):
    """Type of generation task."""
    PORTRAIT_TXT2IMG = "portrait_txt2img"
    CINEMATIC_TXT2IMG = "cinematic_txt2img"
    PRODUCT_TXT2IMG = "product_txt2img"
    FASHION_TXT2IMG = "fashion_txt2img"
    IMG2IMG = "img2img"
    INPAINT_FACE = "inpaint_face"
    UPSCALE = "upscale"
    UNKNOWN = "unknown"


@dataclass
class WorkflowSpec:
    """Specification for a workflow template."""
    workflow_id: str
    task_type: TaskType
    workflow_path: str
    preset_name: str
    kind: WorkflowKind
    description: str
    required_inputs: list[str] = field(default_factory=list)
    supports_retry: bool = True
    supports_judging: bool = True
    default_rewrite_mode: str = "fallback"
    implemented: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "task_type": self.task_type.value,
            "workflow_path": self.workflow_path,
            "preset_name": self.preset_name,
            "kind": self.kind.value,
            "description": self.description,
            "required_inputs": self.required_inputs,
            "supports_retry": self.supports_retry,
            "supports_judging": self.supports_judging,
            "default_rewrite_mode": self.default_rewrite_mode,
            "implemented": self.implemented,
            "metadata": self.metadata,
        }
