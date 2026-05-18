"""
Tests for RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GATE-VERIFY-001

Validates:
- corrective plan requires prior operator rejection
- corrective plan blocks blind retry
- gate requires operator corrective plan approval
- gate allows exactly one generation
- gate does not execute generation
- gate blocks visual acceptance, assembly, downstream
- production_accepted remains false throughout
- artifact_index and episode_ledger are updated
"""
import json
import os
import pytest

CONTROL_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "data", "rc2_multishot1_ep01", "output", "control"
)
CANDIDATE_DIR = os.path.join(CONTROL_DIR, "fresh_visual_candidate")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _rejection():
    return _load(os.path.join(CANDIDATE_DIR, "operator_visual_rejection.json"))


def _corrective_plan():
    return _load(os.path.join(CANDIDATE_DIR, "corrective_plan.json"))


def _plan_verification():
    return _load(os.path.join(CANDIDATE_DIR, "corrective_plan_verification.json"))


def _approval():
    return _load(os.path.join(CANDIDATE_DIR, "operator_corrective_plan_approval.json"))


def _gate():
    return _load(os.path.join(CANDIDATE_DIR, "corrective_generation_gate.json"))


def _artifact_index():
    return _load(os.path.join(CONTROL_DIR, "artifact_index.json"))


def _episode_ledger():
    return _load(os.path.join(CONTROL_DIR, "episode_ledger.json"))


# ---------------------------------------------------------------------------
# Test 1: corrective plan exists and is based on operator rejection
# ---------------------------------------------------------------------------
def test_corrective_plan_requires_operator_rejection():
    rejection = _rejection()
    plan = _corrective_plan()

    assert rejection["operator_verdict"] == "REJECTED", "Rejection verdict must be REJECTED"
    assert rejection["production_accepted"] is False
    assert rejection["retry_generation_authorized"] is False

    assert plan["based_on_rejection"] == "operator_visual_rejection.json", (
        "corrective_plan must reference the operator rejection document"
    )
    assert plan["production_accepted"] is False
    assert plan["retry_generation_authorized"] is False

    defect_ids_in_rejection = {d["defect_id"] for d in rejection["visual_defects"]}
    defect_ids_in_plan = {d["defect_id"] for d in plan["defects_to_address"]}
    assert defect_ids_in_rejection == defect_ids_in_plan, (
        "corrective plan must address exactly the defects listed in the rejection"
    )


# ---------------------------------------------------------------------------
# Test 2: corrective plan blocks blind retry
# ---------------------------------------------------------------------------
def test_corrective_plan_blocks_blind_retry():
    plan = _corrective_plan()
    verification = _plan_verification()

    assert plan["retry_generation_authorized"] is False
    assert plan["comfyui_submit_authorized"] is False
    assert verification["blind_retry_verdict"] is False, (
        "corrective_plan_verification must declare blind_retry_verdict=false"
    )
    assert len(plan.get("workflow_changes_required", [])) >= 3, (
        "corrective plan must list at least 3 distinct workflow changes (not a blind retry)"
    )
    assert len(verification.get("recipe_changes_from_original", [])) >= 3


# ---------------------------------------------------------------------------
# Test 3: gate requires operator corrective plan approval
# ---------------------------------------------------------------------------
def test_gate_requires_operator_corrective_plan_approval():
    approval = _approval()
    gate = _gate()

    assert approval["approved_document"].endswith("corrective_plan.json"), (
        "approval must reference the corrective_plan.json"
    )
    assert approval["approval_scope"] == "corrective_plan_only_and_gate_opening_only"
    assert approval["approval_meaning"]["visual_acceptance_approved"] is False
    assert approval["approval_meaning"]["production_accepted"] is False
    assert approval["approval_meaning"]["corrective_plan_approved"] is True
    assert approval["approval_meaning"]["gate_opening_approved"] is True

    assert gate["gate_opened_by"] == "operator_corrective_plan_approval"
    assert gate["approval_document"].endswith("operator_corrective_plan_approval.json")


# ---------------------------------------------------------------------------
# Test 4: gate allows exactly one generation
# ---------------------------------------------------------------------------
def test_gate_allows_exactly_one_generation():
    gate = _gate()
    assert gate["max_generations"] == 1, "max_generations must be exactly 1"
    assert gate["second_generation_allowed"] is False
    assert gate["blind_retry_allowed"] is False
    assert gate["stop_after_generation"] is True


# ---------------------------------------------------------------------------
# Test 5: gate does not execute generation
# ---------------------------------------------------------------------------
def test_gate_does_not_execute_generation():
    gate = _gate()
    assert gate["generation_performed"] is False, (
        "generation must NOT have been performed when the gate is created"
    )
    assert gate["comfyui_submit_executed"] is False
    assert gate["retry_attempted"] is False
    assert gate.get("generation_count_used", 0) == 0


# ---------------------------------------------------------------------------
# Test 6: gate blocks visual acceptance, assembly, downstream
# ---------------------------------------------------------------------------
def test_gate_blocks_visual_acceptance_assembly_downstream():
    gate = _gate()
    forbidden = gate.get("forbidden_actions", {})

    assert gate["visual_qa_allowed_before_separate_gate"] is False
    assert gate["assembly_allowed"] is False
    assert gate["downstream_allowed"] is False

    assert forbidden.get("visual_acceptance") is True
    assert forbidden.get("assembly") is True
    assert forbidden.get("downstream") is True
    assert forbidden.get("blind_retry") is True


# ---------------------------------------------------------------------------
# Test 7: production_accepted remains false in all gate artifacts
# ---------------------------------------------------------------------------
def test_production_accepted_remains_false():
    for loader, label in [
        (_rejection, "operator_visual_rejection"),
        (_corrective_plan, "corrective_plan"),
        (_plan_verification, "corrective_plan_verification"),
        (_approval, "operator_corrective_plan_approval"),
        (_gate, "corrective_generation_gate"),
    ]:
        doc = loader()
        assert doc.get("production_accepted") is False, (
            f"production_accepted must be False in {label}"
        )

    index = _artifact_index()
    assert index.get("production_accepted") is False, (
        "production_accepted must be False in artifact_index"
    )

    ledger = _episode_ledger()
    last_event = ledger[-1]
    assert last_event.get("production_accepted") is False, (
        "production_accepted must be False in last ledger event"
    )


# ---------------------------------------------------------------------------
# Test 8: artifact_index and episode_ledger are updated
# ---------------------------------------------------------------------------
def test_artifact_index_and_ledger_updated():
    index = _artifact_index()
    assert index.get("corrective_plan_verified") is True
    assert index.get("operator_corrective_plan_approval_recorded") is True
    assert index.get("corrective_generation_gate_opened") is True
    assert index.get("current_state") == "corrective_generation_gate_opened"
    assert index.get("next_allowed_action") == "corrective_generation_execute_one"
    assert index.get("corrective_generation_gate_max_generations") == 1
    assert index.get("blind_retry_allowed") is False

    ledger = _episode_ledger()
    gate_events = [
        e for e in ledger
        if e.get("event_type") == "corrective_gate_verification_and_opening"
    ]
    assert len(gate_events) >= 1, "episode_ledger must have corrective_gate_verification_and_opening event"
    last = gate_events[-1]
    assert last.get("current_state") == "corrective_generation_gate_opened"
    assert last.get("next_allowed_action") == "corrective_generation_execute_one"
    assert last.get("production_accepted") is False
    assert last.get("corrective_generation_gate_opened") is True
    assert last.get("max_generations") == 1
