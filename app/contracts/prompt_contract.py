"""Prompt composition contract."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class PromptCompositionContract:
    """Contract for prompt composition results."""
    positive_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    style_prompts: List[str] = field(default_factory=list)
    technical_prompts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
