"""LLM Brain Decision - uses real DeepSeek for identity lock decision.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import httpx


class LLMBrainDecision:
    """Uses real DeepSeek LLM for identity lock generation decision."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

        # Load DeepSeek API key from environment
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def make_identity_lock_decision(
        self, context_pack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make identity lock decision using real DeepSeek LLM."""
        # Construct the prompt for DeepSeek
        system_prompt = """You are an identity preservation specialist for AI image generation. Your task is to decide how to preserve canonical character identity while correcting framing.

Analyze the context and provide a decision that:
1. Uses canonical identity references as the ONLY identity source
2. Prevents quality references from affecting face identity
3. Prevents composition references from affecting face identity
4. Forbids extra human subjects
5. Enforces single-subject policy
6. Maintains corrected medium/upper-body framing
7. Requires full face visibility

Return your decision as JSON with this exact schema:
{
  "decision_type": "identity_lock_generation_decision",
  "canonical_identity_source": {
    "reference_path": "",
    "role": "identity_anchor",
    "exclusive_identity_source": true
  },
  "reference_role_assignments": [
    {
      "reference_path": "",
      "role": "identity|composition|quality|negative",
      "allowed_use": [],
      "forbidden_use": []
    }
  ],
  "identity_preservation_policy": {
    "preserve_face_shape": true,
    "preserve_eye_shape": true,
    "preserve_nose_mouth_relation": true,
    "preserve_age_impression": true,
    "preserve_skin_tone_family": true,
    "do_not_generate_new_person": true
  },
  "single_subject_policy": {
    "exactly_one_primary_human": true,
    "extra_foreground_person_forbidden": true,
    "background_people_forbidden": true
  },
  "composition_policy": {
    "medium_or_upper_body_shot": true,
    "full_face_visible": true,
    "head_not_touching_edges": true,
    "environment_visible": true,
    "extreme_closeup_forbidden": true
  },
  "workflow_patch_requirements": [],
  "positive_prompt_additions": [],
  "negative_prompt_additions": [],
  "generation_allowed_after_gates": true
}"""

        user_prompt = f"""Context: {json.dumps(context_pack, indent=2)}

Previous rejection reasons: {context_pack.get('previous_rejection_context', {}).get('operator_rejection_reason', [])}

Canonical identity sources available: {len(context_pack.get('canonical_identity_sources', {}).get('identity_references', []))}

Provide the identity lock decision as JSON."""

        # Call DeepSeek API
        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()
            decision_text = result["choices"][0]["message"]["content"]
            decision = json.loads(decision_text)

            # Add metadata
            decision["task_id"] = "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001"
            decision["timestamp"] = datetime.now(timezone.utc).isoformat()
            decision["llm_provider"] = "deepseek"
            decision["llm_model"] = "deepseek-chat"
            decision["simulation_mode_used"] = False

            return decision

        except Exception as e:
            # Fallback decision if API call fails
            return self._fallback_decision(context_pack, str(e))

    def _fallback_decision(
        self, context_pack: Dict[str, Any], error: str
    ) -> Dict[str, Any]:
        """Fallback decision if LLM call fails."""
        identity_refs = context_pack.get("canonical_identity_sources", {}).get(
            "identity_references", []
        )
        primary_identity = identity_refs[0] if identity_refs else {}

        fallback_decision = {
            "decision_type": "identity_lock_generation_decision",
            "task_id": "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_provider": "fallback",
            "llm_model": "rule_based",
            "simulation_mode_used": False,
            "llm_call_error": error,
            "canonical_identity_source": {
                "reference_path": primary_identity.get("relative_path", ""),
                "role": "identity_anchor",
                "exclusive_identity_source": True,
            },
            "reference_role_assignments": [
                {
                    "reference_path": ref.get("relative_path", ""),
                    "role": "identity" if "01_identity" in ref.get("relative_path", "") else "composition",
                    "allowed_use": ["identity_preservation"] if "01_identity" in ref.get("relative_path", "") else ["composition_reference"],
                    "forbidden_use": ["identity_source"] if "01_identity" not in ref.get("relative_path", "") else [],
                }
                for ref in identity_refs[:3]  # Limit to first 3 for fallback
            ],
            "identity_preservation_policy": {
                "preserve_face_shape": True,
                "preserve_eye_shape": True,
                "preserve_nose_mouth_relation": True,
                "preserve_age_impression": True,
                "preserve_skin_tone_family": True,
                "do_not_generate_new_person": True,
            },
            "single_subject_policy": {
                "exactly_one_primary_human": True,
                "extra_foreground_person_forbidden": True,
                "background_people_forbidden": True,
            },
            "composition_policy": {
                "medium_or_upper_body_shot": True,
                "full_face_visible": True,
                "head_not_touching_edges": True,
                "environment_visible": True,
                "extreme_closeup_forbidden": True,
            },
            "workflow_patch_requirements": [],
            "positive_prompt_additions": [
                "one woman only",
                "same person as canonical reference",
                "preserve facial identity",
            ],
            "negative_prompt_additions": [
                "second person",
                "man in foreground",
                "duplicate person",
                "different woman",
                "identity drift",
                "face swap",
                "close-up",
                "cropped face",
            ],
            "generation_allowed_after_gates": True,
        }

        return fallback_decision

    def save_decision(self, decision: Dict[str, Any]) -> None:
        """Save the LLM decision."""
        decision_path = self.identity_lock_dir / "llm_identity_lock_decision.json"
        with open(decision_path, "w", encoding="utf-8") as f:
            json.dump(decision, f, indent=2, ensure_ascii=False)
