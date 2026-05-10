"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Brain provider config layer for controlled external LLM calls.

Brain calls are advisory-only and require explicit operator runtime authorization.
No hidden API calls. No hardcoded model IDs in business logic.
"""

from app.agents.brain.brain_config import BrainProviderConfig
from app.agents.brain.brain_provider import (
    BrainProviderValidationResult,
    validate_brain_provider,
)
from app.agents.brain.brain_runtime_gate import (
    BrainRuntimeGate,
    BrainRuntimeGateResult,
)
from app.agents.brain.brain_call_contracts import (
    BrainCallContract,
    BrainCallContractBuilder,
)

__all__ = [
    "BrainProviderConfig",
    "BrainProviderValidationResult",
    "validate_brain_provider",
    "BrainRuntimeGate",
    "BrainRuntimeGateResult",
    "BrainCallContract",
    "BrainCallContractBuilder",
]
