"""
Tests for RC-COMBINE-V2-CORRECTIVE-GENERATION-SCOPE-REPAIR-001.

Fix corrective generation scope after body-part crop failure and prepare
locked full-frame corrective retry package.
"""
import json
from pathlib import Path
import pytest

from app.visual.output_scope_validator import (
    OutputScopeValidator,
    validate_generation_package,
)


PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
REPAIR_DIR = CONTROL_DIR / "corrective_generation_scope_repair"


# ─── 6.1 Operator Rejection Artifact ───

def test_operator_rejection_records_body_part_crop_failure():
    """Operator rejection artifact must record body-part crop failure."""
    path = REPAIR_DIR / "operator_visual_rejection_corrective_v10.json"
    assert path.exists(), "Operator rejection artifact must exist"

    with open(path, "r", encoding="utf-8") as f:
        rejection = json.load(f)

    assert rejection["task_id"] == "RC-COMBINE-V2-CORRECTIVE-GENERATION-SCOPE-REPAIR-001"
    assert rejection["operator_verdict"] == "REJECTED"
    assert rejection["rejection_type"] == "composition_scope_failure"
    assert rejection["failure_class"] == "body_part_crop_instead_of_full_frame_candidate"
    assert rejection["technical_generation_completed"] is True
    assert rejection["technical_pass_not_visual_pass"] is True
    assert rejection["production_accepted"] is False
    assert rejection["assembly_allowed"] is False
    assert rejection["downstream_allowed"] is False


# ─── 6.2 Root Cause Report ───

def test_root_cause_report_identifies_quality_reference_leak():
    """Root cause report must identify quality reference leaking into composition target."""
    path = REPAIR_DIR / "body_part_crop_root_cause_report.json"
    assert path.exists(), "Root cause report must exist"

    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["primary_root_cause"] == "quality_reference_leaked_into_target_composition"
    assert "missing_full_frame_scene_constraint" in report["secondary_root_causes"]
    assert report["pipeline_failure"] == "Corrective constraints were interpreted as composition target instead of quality constraints."


# ─── 6.3 Full-Frame Contract ───

def test_full_frame_contract_forbids_eye_closeup_output():
    """Full-frame contract must explicitly forbid eye close-up and body-part crops."""
    path = REPAIR_DIR / "full_frame_corrective_generation_contract.json"
    assert path.exists(), "Full-frame contract must exist"

    with open(path, "r", encoding="utf-8") as f:
        contract = json.load(f)

    assert contract["target_output_type"] == "full_frame_production_visual_candidate"

    forbidden = contract["composition_target"]["forbidden_framing"]
    assert "eye_close_up" in forbidden
    assert "mouth_close_up" in forbidden
    assert "skin_macro_close_up" in forbidden
    assert "single_body_part_crop" in forbidden
    assert "isolated_face_fragment" in forbidden

    allowed = contract["composition_target"]["allowed_framing"]
    assert "full_body" in allowed or "medium_shot" in allowed or "cinematic_portrait_with_context" in allowed

    assert contract["camera_distance_policy"]["macro_closeup_forbidden"] is True
    assert contract["camera_distance_policy"]["body_part_crop_forbidden"] is True


# ─── 6.4 Reference Usage Policy ───

def test_quality_reference_cannot_be_used_as_composition_target():
    """Quality reference must not influence composition target."""
    path = REPAIR_DIR / "reference_usage_scope_policy.json"
    assert path.exists(), "Reference usage scope policy must exist"

    with open(path, "r", encoding="utf-8") as f:
        policy = json.load(f)

    quality_refs = policy["quality_references"]
    assert "target_composition" in quality_refs["must_not_influence"]
    assert "camera_distance" in quality_refs["must_not_influence"]
    assert "crop" in quality_refs["must_not_influence"]
    assert "shot_type" in quality_refs["must_not_influence"]

    body_rule = policy["body_part_reference_rule"]
    assert body_rule["body_part_reference_as_output_target"] is False
    assert body_rule["body_part_reference_as_composition_target"] is False
    assert body_rule["body_part_reference_scope"] == "quality_only"


# ─── 6.5 Prompt Recipe ───

def test_prompt_recipe_contains_full_frame_requirement():
    """Repaired prompt recipe must require full-frame scene composition."""
    path = REPAIR_DIR / "full_frame_corrective_prompt_recipe.json"
    assert path.exists(), "Prompt recipe must exist"

    with open(path, "r", encoding="utf-8") as f:
        recipe = json.load(f)

    positive_must = recipe["positive_prompt_requirements"]["must_include"]
    assert any("full-frame" in t or "full frame" in t for t in positive_must), "Must require full-frame"
    assert any("scene" in t for t in positive_must), "Must require scene context"

    negative_must = recipe["negative_prompt_requirements"]["must_include"]
    assert any("eye close-up" in t for t in negative_must), "Must block eye close-up"
    assert any("skin macro" in t for t in negative_must), "Must block skin macro"


def test_negative_prompt_blocks_body_part_crops():
    """Negative prompt must block body-part crop terms."""
    path = REPAIR_DIR / "full_frame_corrective_prompt_recipe.json"
    with open(path, "r", encoding="utf-8") as f:
        recipe = json.load(f)

    negative_must = recipe["negative_prompt_requirements"]["must_include"]
    required_blocks = [
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
    ]
    for term in required_blocks:
        assert any(term in t for t in negative_must), f"Negative prompt must block: {term}"


def test_prompt_weighting_policy_prioritizes_composition():
    """Prompt weighting must prioritize composition over detail."""
    path = REPAIR_DIR / "full_frame_corrective_prompt_recipe.json"
    with open(path, "r", encoding="utf-8") as f:
        recipe = json.load(f)

    weighting = recipe["prompt_weighting_policy"]
    assert weighting["composition_priority"] == "highest"
    assert weighting["body_part_detail_must_not_override_framing"] is True


# ─── 6.6 Output Scope Validator ───

def test_output_scope_validator_blocks_body_part_only_candidate():
    """Validator must block body-part-only candidates."""
    validator = OutputScopeValidator()

    # This is the previous failed prompt
    positive = "photorealistic close-up portrait, sharp focus, detailed skin texture"
    negative = "blur, haze, doll, anime, plastic"

    result = validator.validate_prompt_scope(positive, negative)
    assert result["valid"] is False
    assert any("close-up" in t for t in result["forbidden_terms_found"])


def test_output_scope_validator_passes_full_frame_prompt():
    """Validator must accept full-frame prompt."""
    validator = OutputScopeValidator()

    positive = "cinematic full-frame scene, main character visible, medium shot, environment visible"
    negative = "extreme close-up, eye close-up, skin macro, cropped face, isolated body part"

    result = validator.validate_prompt_scope(positive, negative)
    assert result["valid"] is True
    assert result["checks"]["no_forbidden_terms_in_positive"] is True
    assert result["checks"]["required_composition_terms_present"] is True
    assert result["checks"]["negative_prompt_blocks_crops"] is True


def test_validator_contract_target_check():
    """Validator must check contract target is full-frame."""
    validator = OutputScopeValidator()

    bad_contract = {"target_output_type": "quality_candidate_only", "composition_target": {}}
    result = validator.validate_contract_target(bad_contract)
    assert result["valid"] is False
    assert result["checks"]["target_is_full_frame"] is False

    good_contract = {
        "target_output_type": "full_frame_production_visual_candidate",
        "composition_target": {
            "allowed_framing": ["medium_shot"],
            "forbidden_framing": ["eye_close_up"],
        },
    }
    result = validator.validate_contract_target(good_contract)
    assert result["valid"] is True


def test_validator_reference_scope_check():
    """Validator must block body-part references used as composition targets."""
    validator = OutputScopeValidator()

    bad_policy = {"body_part_reference_rule": {"body_part_reference_as_output_target": True}}
    result = validator.validate_reference_scope(bad_policy)
    assert result["valid"] is False

    good_policy = {
        "body_part_reference_rule": {
            "body_part_reference_as_output_target": False,
            "body_part_reference_as_composition_target": False,
        }
    }
    result = validator.validate_reference_scope(good_policy)
    assert result["valid"] is True


def test_validate_generation_package_from_files():
    """Convenience function must load contract/policy from files and validate."""
    contract_path = REPAIR_DIR / "full_frame_corrective_generation_contract.json"
    policy_path = REPAIR_DIR / "reference_usage_scope_policy.json"

    positive = "cinematic full-frame scene, main character in fairytale winter environment, medium shot"
    negative = "extreme close-up, eye close-up, mouth close-up, skin macro, cropped face, isolated body part"

    result = validate_generation_package(
        positive_prompt=positive,
        negative_prompt=negative,
        contract_path=contract_path,
        reference_policy_path=policy_path,
    )
    assert result["valid"] is True
    assert result["production_candidate_allowed"] is True


# ─── 6.7 State Machine / Gate ───

def test_generation_gate_closed_after_scope_repair():
    """Generation gate must be closed after scope repair."""
    state_path = CONTROL_DIR / "state.json"
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["generation_gate_open"] is False
    assert state["current_state"] == "corrective_generation_scope_repaired_authorization_required"
    assert state["next_allowed_action"] == "operator_authorize_one_full_frame_corrective_generation"


def test_next_generation_requires_operator_authorization():
    """Next generation must require explicit operator authorization."""
    state_path = CONTROL_DIR / "state.json"
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["new_generation_requires_new_operator_authorization"] is True
    assert state["previous_corrective_generation_consumed"] is True


def test_production_accepted_remains_false():
    """Production accepted must remain false after repair."""
    state_path = CONTROL_DIR / "state.json"
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["production_accepted"] is False


def test_assembly_and_downstream_remain_blocked():
    """Assembly and downstream must remain blocked."""
    state_path = CONTROL_DIR / "state.json"
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["assembly_allowed"] is False
    assert state["downstream_allowed"] is False
    assert state["downstream_executed"] is False
    assert state["assembly_executed"] is False


# ─── 6.8 Authorization Packet ───

def test_authorization_packet_pending_operator():
    """Authorization packet must require pending operator authorization."""
    path = REPAIR_DIR / "full_frame_corrective_generation_authorization_packet.json"
    assert path.exists(), "Authorization packet must exist"

    with open(path, "r", encoding="utf-8") as f:
        packet = json.load(f)

    assert packet["authorization_status"] == "pending_operator_authorization"
    assert packet["generation_authorized_now"] is False
    assert packet["future_allowed_action_if_approved"] == "execute_one_full_frame_corrective_generation"
    assert packet["max_future_generations"] == 1
    assert packet["retry_authorized"] is False
    assert packet["blind_retry_allowed"] is False
    assert packet["stop_after_generation"] is True
    assert packet["operator_visual_review_required_after_generation"] is True
    assert packet["assembly_allowed"] is False
    assert packet["downstream_allowed"] is False
    assert packet["production_accepted"] is False


# ─── 7. Artifact Index & Ledger ───

def test_artifact_index_and_ledger_updated():
    """Artifact index and episode ledger must record scope repair."""
    index_path = CONTROL_DIR / "artifact_index.json"
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    assert index.get("corrective_generation_scope_repair_dir") == "corrective_generation_scope_repair/"
    assert index.get("corrective_generation_scope_repair_executed") is True
    assert index.get("full_frame_corrective_generation_contract") == "corrective_generation_scope_repair/full_frame_corrective_generation_contract.json"
    assert index.get("reference_usage_scope_policy") == "corrective_generation_scope_repair/reference_usage_scope_policy.json"
    assert index.get("full_frame_corrective_prompt_recipe") == "corrective_generation_scope_repair/full_frame_corrective_prompt_recipe.json"
    assert index.get("output_scope_validation_report") == "corrective_generation_scope_repair/output_scope_validation_report.json"
    assert index.get("full_frame_corrective_generation_authorization_packet") == "corrective_generation_scope_repair/full_frame_corrective_generation_authorization_packet.json"
    assert index.get("operator_visual_rejection_corrective_v10") == "corrective_generation_scope_repair/operator_visual_rejection_corrective_v10.json"
    assert index.get("body_part_crop_root_cause_report") == "corrective_generation_scope_repair/body_part_crop_root_cause_report.json"

    ledger_path = CONTROL_DIR / "episode_ledger.json"
    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    repair_events = [
        event for event in ledger
        if event.get("event_type") == "corrective_generation_scope_repair"
    ]
    assert len(repair_events) > 0, "Episode ledger must record scope repair event"

    event = repair_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-CORRECTIVE-GENERATION-SCOPE-REPAIR-001"
    assert event["generation_performed"] is False
    assert event["retry_attempted"] is False
    assert event["comfyui_submit_executed"] is False
    assert event["production_accepted"] is False


# ─── Proof ───

def test_proof_json_created():
    """Proof JSON must exist with all required fields."""
    path = REPAIR_DIR / "proof.json"
    assert path.exists(), "Proof JSON must exist"

    with open(path, "r", encoding="utf-8") as f:
        proof = json.load(f)

    assert proof["task_id"] == "RC-COMBINE-V2-CORRECTIVE-GENERATION-SCOPE-REPAIR-001"
    assert proof["feature_completed"] is True
    assert proof["operator_rejection_recorded"] is True
    assert proof["root_cause_report_created"] is True
    assert proof["full_frame_contract_created"] is True
    assert proof["reference_usage_scope_policy_created"] is True
    assert proof["corrective_prompt_recipe_repaired"] is True
    assert proof["body_part_crop_forbidden_as_production_candidate"] is True
    assert proof["quality_reference_not_allowed_as_composition_target"] is True
    assert proof["output_scope_validator_added_or_updated"] is True
    assert proof["output_scope_validation_report_created"] is True
    assert proof["previous_generation_count_consumed"] is True
    assert proof["new_generation_requires_new_operator_authorization"] is True
    assert proof["generation_performed"] is False
    assert proof["comfyui_submit_executed"] is False
    assert proof["retry_attempted"] is False
    assert proof["second_generation_attempted"] is False
    assert proof["generation_gate_open"] is False
    assert proof["authorization_packet_created"] is True
    assert proof["authorization_status"] == "pending_operator_authorization"
    assert proof["max_future_generations_if_authorized"] == 1
    assert proof["artifact_index_updated"] is True
    assert proof["episode_ledger_updated"] is True
    assert proof["state_updated"] is True
    assert proof["current_state"] == "corrective_generation_scope_repaired_authorization_required"
    assert proof["next_allowed_action"] == "operator_authorize_one_full_frame_corrective_generation"
    assert proof["production_accepted"] is False
    assert proof["tests_pass"] is True
    assert proof["py_compile_pass"] is True
    assert proof["git_status_clean"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
