"""
Prompt/Conditioning Director Agent Contract

Defines the role, responsibility, and contract for the brain-enabled
prompt/conditioning director agent.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class PromptConditioningDirectorContract:
    """
    Contract for the Prompt/Conditioning Director Agent.

    Role: Brain-enabled agent that understands visual intent, classifies
    reference roles, prevents quality close-up refs from driving framing,
    produces prompt/conditioning decisions, and hands off safe generation
    requests to the execution layer.
    """

    agent_name: str = "prompt_conditioning_director"
    agent_role: str = "Prompt/Conditioning Director Agent"
    version: str = "1.0.0"

    # Responsibility definition
    responsibilities: Dict[str, Any] = field(default_factory=lambda: {
        "understand_visual_intent": True,
        "classify_reference_roles": True,
        "prevent_closeup_quality_refs_from_driving_framing": True,
        "produce_prompt_conditioning_decision": True,
        "hand_off_safe_generation_request": True,
    })

    # Brain configuration requirements
    brain_requirements: Dict[str, Any] = field(default_factory=lambda: {
        "primary_model_id": "deepseek-v4-flash",
        "provider_configurable": True,
        "exact_model_id_validation_required": True,
        "availability_validation_required": True,
        "pricing_limits_policy_required": True,
        "fallback_model_required": True,
        "runtime_llm_call_requires_gate": True,
        "hardcoded_business_logic_forbidden": True,
    })

    # Generation constraints
    generation_constraints: Dict[str, Any] = field(default_factory=lambda: {
        "max_generations": 1,
        "forbid_blind_retry": True,
        "forbid_second_generation": True,
        "stop_after_generation": True,
        "next_state_after_generation": "operator_visual_review_required",
    })

    # Reference role separation rules
    reference_role_rules: Dict[str, Any] = field(default_factory=lambda: {
        "quality_closeup_refs_may_calibrate_detail_only": True,
        "quality_refs_cannot_drive_camera_distance": True,
        "eyes_face_closeups_cannot_be_composition_refs": True,
        "negative_refs_must_only_suppress_defects": True,
        "composition_must_come_from_explicit_framing_policy": True,
    })

    # Composition policy
    composition_policy: Dict[str, Any] = field(default_factory=lambda: {
        "required_framing": "medium_or_full_character_in_environment",
        "forbid_extreme_closeup": True,
        "forbid_face_crop": True,
        "face_must_be_fully_visible": True,
        "head_should_not_touch_frame_edges": True,
        "environment_visible": True,
    })

    # Forbidden actions
    forbidden_actions: list = field(default_factory=lambda: [
        "blind_retry",
        "second_generation",
        "generation_before_llm_decision",
        "fake_llm_result",
        "fake_prompt_id",
        "fake_asset",
        "dry_run_as_generation",
        "visual_qa_acceptance",
        "operator_visual_acceptance_by_agent",
        "assembly",
        "preview_final_render",
        "voice_audio",
        "downstream",
        "production_accepted_true",
        "hidden_downloads_installs",
        "hardcoded_business_logic_replacing_llm_brain",
        "fallback_to_old_rule_only_curator",
    ])

    # Required artifacts
    required_artifacts: list = field(default_factory=lambda: [
        "prompt_conditioning_director_agent_contract.json",
        "brain_model_policy.json",
        "brain_provider_validation_report.json",
        "context_pack.json",
        "conditioning_failure_diagnosis.json",
        "llm_conditioning_director_decision.json",
        "role_aware_conditioning_contract.json",
        "workflow_patch_request.json",
        "patched_prompt_conditioning.json",
        "patched_workflow_manifest.json",
        "brain_conditioning_generation_gate.json",
        "corrected_generation_manifest.json",
        "corrected_generation_result_review.json",
        "operator_visual_review_packet.json",
        "proof.json",
    ])

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "version": self.version,
            "responsibilities": self.responsibilities,
            "brain_requirements": self.brain_requirements,
            "generation_constraints": self.generation_constraints,
            "reference_role_rules": self.reference_role_rules,
            "composition_policy": self.composition_policy,
            "forbidden_actions": self.forbidden_actions,
            "required_artifacts": self.required_artifacts,
            "created_at": self.created_at,
            "task_id": self.task_id,
        }

    def save(self, path: str) -> None:
        """Save contract to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "PromptConditioningDirectorContract":
        """Load contract from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
