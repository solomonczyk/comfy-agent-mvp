"""
Generation Gate

Internal execution gate that controls generation authorization.
"""

from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class GenerationGate:
    """
    Generation gate artifact.

    Must include authorization, max generations, LLM decision validation,
    conditioning contract, workflow patch, and state transition rules.
    """

    # Authorization
    generation_authorized_by_task: bool = False
    max_generations: int = 1

    # Prerequisites
    llm_decision_required: bool = True
    llm_decision_validated: bool = False
    conditioning_contract_required: bool = True
    workflow_patch_required: bool = True

    # Constraints
    forbid_second_generation: bool = True
    stop_after_generation: bool = True
    next_state_after_generation: str = "operator_visual_review_required"

    # Validation results
    provider_validated: bool = False
    model_available: bool = False
    pricing_policy_validated: bool = False

    # Artifact validation
    context_pack_exists: bool = False
    conditioning_diagnosis_exists: bool = False
    llm_decision_exists: bool = False
    role_aware_contract_exists: bool = False
    workflow_patch_exists: bool = False

    # Generation tracking
    generation_count: int = 0
    second_generation_attempted: bool = False
    blind_retry_attempted: bool = False

    # Blockers
    blockers: list = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert gate to dictionary."""
        return {
            "generation_authorized_by_task": self.generation_authorized_by_task,
            "max_generations": self.max_generations,
            "llm_decision_required": self.llm_decision_required,
            "llm_decision_validated": self.llm_decision_validated,
            "conditioning_contract_required": self.conditioning_contract_required,
            "workflow_patch_required": self.workflow_patch_required,
            "forbid_second_generation": self.forbid_second_generation,
            "stop_after_generation": self.stop_after_generation,
            "next_state_after_generation": self.next_state_after_generation,
            "provider_validated": self.provider_validated,
            "model_available": self.model_available,
            "pricing_policy_validated": self.pricing_policy_validated,
            "context_pack_exists": self.context_pack_exists,
            "conditioning_diagnosis_exists": self.conditioning_diagnosis_exists,
            "llm_decision_exists": self.llm_decision_exists,
            "role_aware_contract_exists": self.role_aware_contract_exists,
            "workflow_patch_exists": self.workflow_patch_exists,
            "generation_count": self.generation_count,
            "second_generation_attempted": self.second_generation_attempted,
            "blind_retry_attempted": self.blind_retry_attempted,
            "blockers": self.blockers,
            "created_at": self.created_at,
            "task_id": self.task_id,
        }

    def validate_prerequisites(
        self,
        provider_validated: bool,
        model_available: bool,
        pricing_policy_validated: bool,
        context_pack_exists: bool,
        conditioning_diagnosis_exists: bool,
        llm_decision_exists: bool,
        role_aware_contract_exists: bool,
        workflow_patch_exists: bool,
    ) -> bool:
        """
        Validate all prerequisites for generation.

        Args:
            provider_validated: Provider validation status
            model_available: Model availability status
            pricing_policy_validated: Pricing policy validation status
            context_pack_exists: Context pack artifact exists
            conditioning_diagnosis_exists: Conditioning diagnosis exists
            llm_decision_exists: LLM decision exists
            role_aware_contract_exists: Role-aware contract exists
            workflow_patch_exists: Workflow patch exists

        Returns:
            True if all prerequisites pass, False otherwise
        """
        self.provider_validated = provider_validated
        self.model_available = model_available
        self.pricing_policy_validated = pricing_policy_validated
        self.context_pack_exists = context_pack_exists
        self.conditioning_diagnosis_exists = conditioning_diagnosis_exists
        self.llm_decision_exists = llm_decision_exists
        self.role_aware_contract_exists = role_aware_contract_exists
        self.workflow_patch_exists = workflow_patch_exists

        # Check all prerequisites
        if self.llm_decision_required and not self.llm_decision_exists:
            self.blockers.append("LLM decision does not exist")
            return False

        if self.conditioning_contract_required and not self.role_aware_contract_exists:
            self.blockers.append("Role-aware conditioning contract does not exist")
            return False

        if self.workflow_patch_required and not self.workflow_patch_exists:
            self.blockers.append("Workflow patch does not exist")
            return False

        if not self.provider_validated:
            self.blockers.append("Provider not validated")
            return False

        if not self.model_available:
            self.blockers.append("Model not available")
            return False

        if not self.pricing_policy_validated:
            self.blockers.append("Pricing policy not validated")
            return False

        # All prerequisites pass
        self.llm_decision_validated = True
        return True

    def authorize_generation(self) -> bool:
        """
        Authorize generation for this task.

        Returns:
            True if generation authorized, False otherwise
        """
        if self.blockers:
            return False

        if self.generation_count >= self.max_generations:
            self.blockers.append(f"Generation count ({self.generation_count}) >= max ({self.max_generations})")
            return False

        self.generation_authorized_by_task = True
        return True

    def record_generation(self) -> None:
        """Record that a generation was performed."""
        self.generation_count += 1

        if self.generation_count >= self.max_generations:
            self.blockers.append("Max generations reached")

    def record_second_generation_attempt(self) -> None:
        """Record that a second generation was attempted (forbidden)."""
        self.second_generation_attempted = True
        self.blockers.append("Second generation attempted (forbidden)")

    def record_blind_retry_attempt(self) -> None:
        """Record that a blind retry was attempted (forbidden)."""
        self.blind_retry_attempted = True
        self.blockers.append("Blind retry attempted (forbidden)")

    def is_generation_allowed(self) -> bool:
        """Check if generation is allowed."""
        return (
            self.generation_authorized_by_task
            and len(self.blockers) == 0
            and self.generation_count < self.max_generations
            and not self.second_generation_attempted
            and not self.blind_retry_attempted
        )

    def save(self, path: str) -> None:
        """Save gate to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "GenerationGate":
        """Load gate from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
