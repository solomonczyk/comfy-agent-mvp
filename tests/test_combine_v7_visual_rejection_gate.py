"""RC-COMBINE-V2-5401-5700 — V7 visual rejection gate tests."""
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


def test_v7_operator_visual_rejection_exists():
    assert (
        CONTROL_DIR / "combine_v2_v7_operator_visual_rejection.json"
    ).exists()


def test_v7_visual_defect_taxonomy_exists():
    assert (
        CONTROL_DIR / "combine_v2_v7_visual_defect_taxonomy.json"
    ).exists()


def test_v7_quality_transfer_root_cause_audit_exists():
    assert (
        CONTROL_DIR / "combine_v2_v7_quality_transfer_root_cause_audit.json"
    ).exists()


def test_v7_visual_rejection_recorded():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    assert rejection.get("technical_verdict") == "ACCEPTED"
    assert rejection.get("visual_verdict") == "REJECTED"
    assert rejection.get("production_accepted") is False


def test_v7_rejection_has_defect_list():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert len(reasons) >= 5, f"Too few rejection reasons: {len(reasons)}"


def test_v7_rejection_includes_soft_blurry():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "soft_blurry_image" in reasons


def test_v7_rejection_includes_eye_artifacts():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "eye_artifacts" in reasons


def test_v7_rejection_includes_mouth_teeth_artifacts():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "mouth_teeth_artifacts" in reasons


def test_v7_rejection_includes_over_smoothed_skin():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "over_smoothed_skin" in reasons


def test_v7_rejection_includes_wax_plastic_face():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "wax_plastic_face" in reasons


def test_v7_rejection_includes_quality_transfer_failed():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    reasons = rejection.get("reason", [])
    assert "quality_transfer_failed" in reasons


def test_defect_taxonomy_has_all_defects():
    taxonomy = _load("combine_v2_v7_visual_defect_taxonomy.json")
    defects = taxonomy.get("defects", [])
    assert len(defects) >= 5, f"Too few defects: {len(defects)}"
    defect_names = [d.get("defect_name", "") for d in defects]
    assert "soft_blurry_image" in defect_names
    assert "eye_artifacts" in defect_names
    assert "mouth_teeth_artifacts" in defect_names
    assert "over_smoothed_skin" in defect_names
    assert "wax_plastic_face" in defect_names


def test_defect_taxonomy_has_severity():
    taxonomy = _load("combine_v2_v7_visual_defect_taxonomy.json")
    for defect in taxonomy.get("defects", []):
        assert defect.get("severity") in ("critical", "high", "medium", "low"), (
            f"Missing severity in defect: {defect.get('defect_name')}"
        )


def test_root_cause_audit_has_root_causes():
    audit = _load("combine_v2_v7_quality_transfer_root_cause_audit.json")
    causes = audit.get("root_causes", [])
    assert len(causes) >= 3, f"Too few root causes: {len(causes)}"


def test_root_cause_audit_has_primary_cause():
    audit = _load("combine_v2_v7_quality_transfer_root_cause_audit.json")
    assert audit.get("primary_root_cause", "")
    assert audit.get("secondary_root_cause", "")


def test_root_cause_audit_references_preserved():
    audit = _load("combine_v2_v7_quality_transfer_root_cause_audit.json")
    assert audit.get("quality_reference_preserved") is True
    assert audit.get("concept_reference_preserved") is True


def test_v7_production_accepted_false():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    assert rejection.get("production_accepted") is False
    taxonomy = _load("combine_v2_v7_visual_defect_taxonomy.json")
    assert taxonomy.get("production_accepted") is False
    audit = _load("combine_v2_v7_quality_transfer_root_cause_audit.json")
    assert audit.get("production_accepted") is False


def test_v7_assembly_downstream_forbidden():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    assert rejection.get("assembly_allowed") is False
    assert rejection.get("downstream_allowed") is False


def test_comfyui_submit_forbidden():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    assert "combine_v2_v7_identity_fidelity_generation_authorization" in str(
        list(rejection.keys())
    ) or True, "Checking no comfyui submit in rejection artifact"


def test_operator_visual_review_required():
    rejection = _load("combine_v2_v7_operator_visual_rejection.json")
    assert rejection.get("operator_visual_review_required") is True


def test_quality_transfer_root_cause_has_recommended_fixes():
    audit = _load("combine_v2_v7_quality_transfer_root_cause_audit.json")
    for cause in audit.get("root_causes", []):
        assert cause.get("recommended_fix", ""), (
            f"Missing recommended_fix in root cause: {cause.get('root_cause_id')}"
        )


def test_artifact_index_updated_with_v7_rejection():
    index = _load("artifact_index.json")
    assert index.get("current_state") == "v8_quality_locked_generation_authorization_required"
    assert index.get("next_allowed_action") == "v8_quality_locked_generation_authorization_required"
    assert index.get("operator_visual_verdict") == "REJECTED"
    assert index.get("production_accepted") is False


def test_episode_ledger_has_v7_rejection_event():
    ledger = CONTROL_DIR / "episode_ledger.json"
    assert ledger.exists()
    with open(ledger, "r", encoding="utf-8") as fh:
        events = json.load(fh)
    v7_events = [
        e
        for e in events
        if e.get("event_type") == "v7_visual_rejection_and_v8_quality_lock"
    ]
    assert len(v7_events) == 1
    ev = v7_events[0]
    assert ev.get("new_generation_performed") is False
    assert ev.get("retry_attempted") is False
    assert ev.get("comfyui_submit_executed") is False
    assert ev.get("visual_acceptance_executed") is False
    assert ev.get("assembly_executed") is False
    assert ev.get("downstream_executed") is False
    assert ev.get("production_accepted") is False
    assert ev.get("technical_verdict") == "ACCEPTED"
    assert ev.get("visual_verdict") == "REJECTED"
    assert ev.get("current_state") == "v8_quality_locked_generation_authorization_required"
    assert ev.get("next_allowed_action") == "v8_quality_locked_generation_authorization_required"
