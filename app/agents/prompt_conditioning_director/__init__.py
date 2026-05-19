"""
Prompt/Conditioning Director Agent

Brain-enabled agent that audits conditioning failures, separates reference roles,
prevents close-up quality references from controlling composition, and produces
safe generation requests.
"""

from .contract import PromptConditioningDirectorContract
from .runner import PromptConditioningDirectorRunner
from .brain_config import BrainConfig
from .brain_client import BrainClient
from .context_pack import ContextPack
from .conditioning_diagnosis import ConditioningDiagnosis
from .decision_schema import DecisionSchema
from .workflow_patch import WorkflowPatch
from .generation_gate import GenerationGate
from .artifacts import ArtifactManager

__all__ = [
    "PromptConditioningDirectorContract",
    "PromptConditioningDirectorRunner",
    "BrainConfig",
    "BrainClient",
    "ContextPack",
    "ConditioningDiagnosis",
    "DecisionSchema",
    "WorkflowPatch",
    "GenerationGate",
    "ArtifactManager",
]
