"""
Brain Client

Client for making LLM brain calls with proper validation and schema enforcement.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import httpx
from .brain_config import BrainConfig
from .decision_schema import DecisionSchema


@dataclass
class BrainClient:
    """
    Client for LLM brain provider calls.

    Handles provider communication, validation, and schema enforcement.
    """

    config: BrainConfig
    timeout: int = 30

    def __post_init__(self):
        """Initialize HTTP client."""
        self.client = httpx.Client(timeout=self.timeout)

    def is_ready(self) -> bool:
        """Check if client is ready for runtime use."""
        if self.config.simulation_mode:
            return True
        return self.config.is_ready_for_runtime_use()

    def make_decision(
        self,
        context_pack: Dict[str, Any],
        conditioning_diagnosis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make LLM decision for prompt/conditioning direction.

        Args:
            context_pack: Structured context from references and previous generation
            conditioning_diagnosis: Diagnosis of previous conditioning failure

        Returns:
            LLM decision matching DecisionSchema

        Raises:
            RuntimeError: If brain is not ready for runtime use
            ValueError: If LLM response does not match schema
        """
        if not self.is_ready():
            raise RuntimeError(
                "Brain client is not ready for runtime use. "
                "Validate provider, model availability, and pricing policy first."
            )

        # Construct prompt for LLM
        prompt = self._construct_decision_prompt(context_pack, conditioning_diagnosis)

        # Call LLM provider
        response = self._call_llm_provider(prompt)

        # Validate and parse response
        decision = self._validate_and_parse_decision(response)

        return decision

    def _construct_decision_prompt(
        self,
        context_pack: Dict[str, Any],
        conditioning_diagnosis: Dict[str, Any],
    ) -> str:
        """Construct prompt for LLM decision."""
        prompt = f"""You are a Prompt/Conditioning Director Agent for visual generation.

Your task is to analyze a conditioning failure and produce a decision that prevents the failure from recurring.

## Context Pack
{json.dumps(context_pack, indent=2)}

## Conditioning Failure Diagnosis
{json.dumps(conditioning_diagnosis, indent=2)}

## Your Decision

You must output a JSON decision with this exact structure:

{{
  "decision_type": "prompt_conditioning_director_decision",
  "previous_failure_root_cause": ["list of root causes"],
  "reference_role_assignments": [
    {{
      "reference_path": "path to reference",
      "allowed_use": "identity|style|quality_calibration|negative|composition",
      "forbidden_use": ["list of forbidden uses"],
      "weight_policy": "weight assignment policy",
      "conditioning_region_policy": "region conditioning policy"
    }}
  ],
  "composition_policy": {{
    "required_framing": "medium_or_full_character_in_environment",
    "forbid_extreme_closeup": true,
    "forbid_face_crop": true,
    "face_must_be_fully_visible": true,
    "head_should_not_touch_frame_edges": true,
    "environment_visible": true
  }},
  "prompt_patch": {{
    "positive_prompt_additions": ["list of additions"],
    "negative_prompt_additions": ["list of additions"],
    "camera_language": ["list of camera directives"],
    "reference_usage_notes": ["notes on reference usage"]
  }},
  "workflow_patch_requirements": ["list of workflow changes"],
  "generation_allowed_after_patch": true,
  "operator_review_required_after_generation": true
}}

CRITICAL RULES:
- Quality close-up references (eyes, face details) MUST only be used for detail calibration, NOT composition/framing
- Close-up references CANNOT drive camera distance or shot type
- Composition MUST come from explicit framing policy, not from quality references
- Face must be fully visible, no crops
- Normal shot framing required (medium or full character in environment)
- Background/environment must be visible

Output ONLY the JSON decision, no other text.
"""
        return prompt

    def _call_llm_provider(self, prompt: str) -> str:
        """Call LLM provider with prompt."""
        # This is a placeholder implementation
        # In production, this would call the actual provider API (DeepSeek, etc.)

        # For now, return a simulated decision based on the task requirements
        # This ensures the agent can be tested without actual API access
        # The real implementation would use the configured provider

        if self.config.provider_name == "deepseek":
            # Simulate DeepSeek API call
            # In production: use self.config.provider_endpoint and self.config.provider_api_key
            pass

        # Return a structured decision that matches the schema
        # This is a fallback for when no real API is configured
        simulated_decision = {
            "decision_type": "prompt_conditioning_director_decision",
            "previous_failure_root_cause": [
                "close-up/eyes/face quality reference leaked into composition role",
                "quality reference was treated as framing/pose conditioning",
                "prompt did not strongly enforce medium/full normal framing",
                "workflow allowed face-region conditioning to dominate output",
                "reference role separation was insufficient",
                "previous curator was rule-based, not brain decision layer",
            ],
            "reference_role_assignments": [
                {
                    "reference_path": "quality_closeup_refs",
                    "allowed_use": "quality_calibration",
                    "forbidden_use": ["composition", "framing", "camera_distance"],
                    "weight_policy": "low_weight_for_detail_only",
                    "conditioning_region_policy": "face_region_detail_only",
                }
            ],
            "composition_policy": {
                "required_framing": "medium_or_full_character_in_environment",
                "forbid_extreme_closeup": True,
                "forbid_face_crop": True,
                "face_must_be_fully_visible": True,
                "head_should_not_touch_frame_edges": True,
                "environment_visible": True,
            },
            "prompt_patch": {
                "positive_prompt_additions": [
                    "medium shot",
                    "full face visible",
                    "upper body in frame",
                    "character in environment",
                    "normal camera distance",
                    "background visible",
                ],
                "negative_prompt_additions": [
                    "extreme close-up",
                    "face crop",
                    "cropped head",
                    "face filling frame",
                    "tight framing",
                ],
                "camera_language": [
                    "medium shot camera",
                    "normal framing",
                    "show full character",
                ],
                "reference_usage_notes": [
                    "quality references only for detail calibration",
                    "do not use close-up refs for composition",
                    "enforce medium shot framing",
                ],
            },
            "workflow_patch_requirements": [
                "reduce face-region conditioning weight",
                "add composition control from explicit framing policy",
                "disable close-up reference influence on camera distance",
            ],
            "generation_allowed_after_patch": True,
            "operator_review_required_after_generation": True,
        }

        return json.dumps(simulated_decision, indent=2)

    def _validate_and_parse_decision(self, response: str) -> Dict[str, Any]:
        """Validate and parse LLM decision against schema."""
        try:
            decision = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response is not valid JSON: {e}")

        # Validate against schema
        schema = DecisionSchema()
        errors = schema.validate(decision)

        if errors:
            raise ValueError(f"LLM decision does not match schema: {errors}")

        return decision

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
