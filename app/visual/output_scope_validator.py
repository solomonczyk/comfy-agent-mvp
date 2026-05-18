"""
RC-COMBINE-V2-CORRECTIVE-GENERATION-SCOPE-REPAIR-001
Output scope validator for visual generation.

Enforces contract-level validation that blocks body-part-only outputs
from being treated as valid production candidates.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OutputScopeValidator:
    """Validates that generation outputs meet full-frame production candidate requirements."""

    FORBIDDEN_FRAMING_TERMS: list[str] = [
        "close-up portrait",
        "extreme close-up",
        "eye close-up",
        "mouth close-up",
        "skin macro",
        "cropped face",
        "isolated body part",
        "only one eye",
        "only lips",
        "beauty macro photo",
        "medical close-up",
        "partial face crop",
        "no scene context",
        "macro close-up",
        "macro detail",
        "isolated face",
        "disembodied face",
        "floating head",
    ]

    REQUIRED_COMPOSITION_TERMS: list[str] = [
        "full-frame",
        "full frame",
        "cinematic scene",
        "scene context",
        "environment",
        "background",
        "medium shot",
        "three-quarter",
        "waist up",
        "complete composition",
    ]

    def __init__(self, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path(".")
        self.image_semantic_detection_available = False

    def validate_prompt_scope(
        self,
        positive_prompt: str,
        negative_prompt: str,
        target_output_type: str | None = None,
    ) -> dict[str, Any]:
        """Check prompt for forbidden framing terms and required composition terms."""
        positive_lower = positive_prompt.lower()
        negative_lower = negative_prompt.lower()

        forbidden_found = [
            term for term in self.FORBIDDEN_FRAMING_TERMS
            if term in positive_lower
        ]

        required_found = [
            term for term in self.REQUIRED_COMPOSITION_TERMS
            if term in positive_lower
        ]

        negative_blocks = [
            term for term in self.FORBIDDEN_FRAMING_TERMS
            if term in negative_lower
        ]

        passed = (
            len(forbidden_found) == 0
            and len(required_found) > 0
            and len(negative_blocks) > 0
        )

        return {
            "valid": passed,
            "forbidden_terms_found": forbidden_found,
            "required_terms_found": required_found,
            "negative_blocking_terms": negative_blocks,
            "target_output_type": target_output_type,
            "checks": {
                "no_forbidden_terms_in_positive": len(forbidden_found) == 0,
                "required_composition_terms_present": len(required_found) > 0,
                "negative_prompt_blocks_crops": len(negative_blocks) > 0,
            },
        }

    def validate_contract_target(self, contract: dict[str, Any]) -> dict[str, Any]:
        """Check generation contract specifies full-frame production candidate."""
        target = contract.get("target_output_type", "")
        forbidden = contract.get("composition_target", {}).get("forbidden_framing", [])
        allowed = contract.get("composition_target", {}).get("allowed_framing", [])

        passed = (
            target == "full_frame_production_visual_candidate"
            and len(forbidden) > 0
            and len(allowed) > 0
        )

        return {
            "valid": passed,
            "target_output_type": target,
            "forbidden_framing_count": len(forbidden),
            "allowed_framing_count": len(allowed),
            "checks": {
                "target_is_full_frame": target == "full_frame_production_visual_candidate",
                "forbidden_framing_defined": len(forbidden) > 0,
                "allowed_framing_defined": len(allowed) > 0,
            },
        }

    def validate_reference_scope(self, reference_policy: dict[str, Any]) -> dict[str, Any]:
        """Check that quality references are not used as composition targets."""
        body_part_rule = reference_policy.get("body_part_reference_rule", {})
        as_output_target = body_part_rule.get("body_part_reference_as_output_target", True)
        as_composition_target = body_part_rule.get("body_part_reference_as_composition_target", True)

        passed = not as_output_target and not as_composition_target

        return {
            "valid": passed,
            "body_part_reference_as_output_target": as_output_target,
            "body_part_reference_as_composition_target": as_composition_target,
            "checks": {
                "body_part_not_output_target": not as_output_target,
                "body_part_not_composition_target": not as_composition_target,
            },
        }

    def validate_output_candidate(
        self,
        positive_prompt: str,
        negative_prompt: str,
        contract: dict[str, Any] | None = None,
        reference_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run all validation checks for a generation candidate."""
        prompt_result = self.validate_prompt_scope(
            positive_prompt, negative_prompt,
            target_output_type=contract.get("target_output_type") if contract else None,
        )

        contract_result = self.validate_contract_target(contract) if contract else {"valid": False, "checks": {}}
        reference_result = self.validate_reference_scope(reference_policy) if reference_policy else {"valid": False, "checks": {}}

        all_passed = (
            prompt_result["valid"]
            and contract_result["valid"]
            and reference_result["valid"]
        )

        return {
            "valid": all_passed,
            "prompt_scope_check": prompt_result,
            "contract_target_check": contract_result,
            "reference_scope_check": reference_result,
            "image_semantic_detection_available": self.image_semantic_detection_available,
            "fallback_validation_used": not self.image_semantic_detection_available,
            "manual_visual_review_required": True,
            "blocks_body_part_crop_as_production_candidate": True,
            "production_candidate_allowed": all_passed,
        }

    def body_part_crop_blocked(self, validation_result: dict[str, Any]) -> bool:
        """Return True if body-part crop is blocked."""
        return not validation_result.get("production_candidate_allowed", True)


def validate_generation_package(
    positive_prompt: str,
    negative_prompt: str,
    contract_path: Path | str | None = None,
    reference_policy_path: Path | str | None = None,
) -> dict[str, Any]:
    """Convenience function to validate a full generation package from file paths."""
    validator = OutputScopeValidator()

    contract: dict[str, Any] | None = None
    if contract_path and Path(contract_path).exists():
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

    reference_policy: dict[str, Any] | None = None
    if reference_policy_path and Path(reference_policy_path).exists():
        with open(reference_policy_path, "r", encoding="utf-8") as f:
            reference_policy = json.load(f)

    return validator.validate_output_candidate(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        contract=contract,
        reference_policy=reference_policy,
    )
