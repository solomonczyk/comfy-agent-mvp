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
        """Call LLM provider with prompt using REAL API."""
        if not self.config.provider_api_key:
            raise RuntimeError("DEEPSEEK_V4_FLASH_API_KEY not configured. Cannot make real LLM call.")

        # DeepSeek API endpoint (OpenAI-compatible)
        endpoint = self.config.provider_endpoint or "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.config.provider_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.primary_model_id,
            "messages": [
                {"role": "system", "content": "You are a Prompt/Conditioning Director Agent. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": self.config.max_tokens_per_request,
            "response_format": {"type": "json_object"},
        }

        try:
            response = self.client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Extract the decision from the response
            decision_content = result["choices"][0]["message"]["content"]
            return decision_content

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"DeepSeek API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to call DeepSeek API: {e}")

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
