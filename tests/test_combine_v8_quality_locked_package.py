"""RC-COMBINE-V2-5401-5700 — V8 quality-locked package tests."""
from __future__ import annotations

import json
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)


def _load(name: str) -> dict:
    p = CONTROL_DIR / name
    assert p.exists(), f"Missing control artifact: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_v8_quality_locked_refinement_package_exists():
    assert (
        CONTROL_DIR / "combine_v2_v8_quality_locked_refinement_package.json"
    ).exists()


def test_v8_quality_guardrails_exists():
    assert (
        CONTROL_DIR / "combine_v2_v8_quality_guardrails.json"
    ).exists()


def test_v8_generation_gate_exists():
    assert (
        CONTROL_DIR / "combine_v2_v8_quality_locked_generation_gate.json"
    ).exists()


def test_v8_generation_gate_closed():
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("generation_allowed_now") is False, (
        "V8 generation gate must be closed (generation_allowed_now=false)"
    )


def test_v8_gate_requires_operator_authorization():
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("requires_operator_authorization") is True, (
        "V8 generation gate must require operator authorization"
    )


def test_v8_gate_max_generations_is_one():
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("max_generations_after_authorization") == 1, (
        "V8 gate must limit to 1 generation after authorization"
    )


def test_concept_reference_preserved():
    package = _load("combine_v2_v8_quality_locked_refinement_package.json")
    refs = package.get("references", {})
    concept = refs.get("concept_reference", {})
    assert concept.get("role") == "concept_reference"
    assert "fantasy" in concept.get("name", "").lower()


def test_quality_reference_preserved():
    package = _load("combine_v2_v8_quality_locked_refinement_package.json")
    refs = package.get("references", {})
    quality = refs.get("quality_reference", {})
    assert quality.get("role") == "quality_reference"
    assert "elderly" in quality.get("name", "").lower() or "бабка" in quality.get("name", "").lower()


def test_failed_candidate_usage_is_negative_reference():
    package = _load("combine_v2_v8_quality_locked_refinement_package.json")
    refs = package.get("references", {})
    failed = refs.get("failed_candidate", {})
    assert failed.get("role") == "negative_reference"
    assert "negative audit" in failed.get("usage", "").lower()


def test_v8_quality_guardrails_created():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    rails = guardrails.get("guardrails", [])
    assert len(rails) >= 8, f"Expected >=8 guardrails, got {len(rails)}"


def test_anti_blur_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "anti_blur" in categories, "Anti-blur guardrail missing"


def test_realistic_eyes_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "realistic_eyes" in categories, "Realistic eyes guardrail missing"


def test_clean_eyelashes_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "clean_eyelashes" in categories, "Clean eyelashes guardrail missing"


def test_no_wax_plastic_skin_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "no_wax_plastic_skin" in categories, (
        "No wax/plastic skin guardrail missing"
    )


def test_hair_strand_detail_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "hair_strand_detail" in categories, (
        "Hair strand detail guardrail missing"
    )


def test_operator_visual_review_guardrail_exists():
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    categories = [g.get("category", "") for g in guardrails.get("guardrails", [])]
    assert "operator_visual_review" in categories, (
        "Operator visual review guardrail missing"
    )


def test_v8_state_transition_correct():
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("current_state") == "v8_quality_locked_generation_authorization_required"
    assert gate.get("next_allowed_action") == "v8_quality_locked_generation_authorization_required"


def test_v8_production_accepted_false():
    package = _load("combine_v2_v8_quality_locked_refinement_package.json")
    assert package.get("production_accepted") is False
    guardrails = _load("combine_v2_v8_quality_guardrails.json")
    assert guardrails.get("production_accepted") is False
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("production_accepted") is False


def test_v8_assembly_downstream_forbidden():
    package = _load("combine_v2_v8_quality_locked_refinement_package.json")
    assert package.get("assembly_allowed") is False
    assert package.get("downstream_allowed") is False
    gate = _load("combine_v2_v8_quality_locked_generation_gate.json")
    assert gate.get("assembly_allowed") is False
    assert gate.get("downstream_allowed") is False
