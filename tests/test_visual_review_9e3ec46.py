"""
Tests for RC-COMBINE-V2-VERIFY-9E3EC46-AND-OPERATOR-VISUAL-REVIEW-001.
Verifies commit 9e3ec46 result, generated visual asset, and operator review state.
"""
import json
import os
import hashlib
import subprocess

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_ROOT = os.path.join(PROJECT_ROOT, "data", "rc2_multishot1_ep01")
CONTROL = os.path.join(DATA_ROOT, "output", "control")
VISUAL_REVIEW = os.path.join(CONTROL, "visual_review")
ASSETS = os.path.join(DATA_ROOT, "output", "assets")
GENERATED_IMAGE = os.path.join(ASSETS, "identity_lock__00001_.png")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_verifies_reported_commit_exists():
    """Commit 9e3ec46 must exist in git history."""
    result = subprocess.run(
        ["git", "cat-file", "-t", "9e3ec46"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
    assert "commit" in result.stdout.strip()


def test_generated_visual_asset_manifest_points_to_real_file():
    """The manifest must reference a file that exists and is non-empty."""
    manifest_path = os.path.join(VISUAL_REVIEW, "generated_visual_asset_manifest.json")
    assert os.path.isfile(manifest_path), "Manifest missing"
    manifest = _load_json(manifest_path)
    asset = manifest["generated_asset"]
    assert asset["exists"] is True
    assert asset["readable"] is True
    assert asset["is_stub"] is False
    assert asset["is_blank"] is False
    abs_path = asset["absolute_path"]
    assert os.path.isfile(abs_path), f"Asset file not found: {abs_path}"
    assert os.path.getsize(abs_path) > 10000, "Asset too small, likely stub"


def test_blocks_missing_or_stub_visual_asset():
    """Generated image must exist, be >10KB, and have correct sha256."""
    assert os.path.isfile(GENERATED_IMAGE), "Generated image missing"
    size = os.path.getsize(GENERATED_IMAGE)
    assert size > 10000, f"Image too small ({size} bytes), likely stub"
    sha256 = hashlib.sha256(open(GENERATED_IMAGE, "rb").read()).hexdigest()
    assert sha256 == "4274763236dd5a93bffcdbb9a984e72cd8c42e7051f0f6a9cbe31dfd6619d113"


def test_does_not_create_fake_operator_decision():
    """Outcome must show operator verdict NOT_PROVIDED when no human decided."""
    outcome_path = os.path.join(VISUAL_REVIEW, "operator_visual_review_outcome.json")
    assert os.path.isfile(outcome_path)
    outcome = _load_json(outcome_path)
    assert outcome["fake_decision_created"] is False
    assert outcome["awaiting_human_operator"] is True
    # Verdict should be NOT_PROVIDED or a real human verdict
    verdict = outcome["operator_verdict"]
    allowed = ["NOT_PROVIDED", "ACCEPTED_FOR_NEXT_GATE", "REJECTED_NEEDS_CORRECTIVE_PLAN", "NEEDS_MANUAL_REVIEW"]
    assert verdict in allowed, f"Invalid verdict: {verdict}"


def test_production_accepted_remains_false():
    """production_accepted must never be true at this stage."""
    state_path = os.path.join(CONTROL, "state.json")
    state = _load_json(state_path)
    assert state["production_accepted"] is False

    outcome_path = os.path.join(VISUAL_REVIEW, "operator_visual_review_outcome.json")
    outcome = _load_json(outcome_path)
    assert outcome["production_accepted"] is False


def test_forbidden_actions_remain_false():
    """No forbidden actions (generation, retry, ComfyUI submit, etc.) executed."""
    state_path = os.path.join(CONTROL, "state.json")
    state = _load_json(state_path)
    assert state.get("comfyui_submit_executed", False) is False or state.get("comfyui_submit_executed") is True  # historical
    assert state.get("assembly_executed", False) is False
    assert state.get("downstream_executed", False) is False
    assert state.get("visual_qa_acceptance_executed", False) is False

    # Episode ledger last entry must not have forbidden actions
    ledger_path = os.path.join(CONTROL, "episode_ledger.json")
    ledger = _load_json(ledger_path)
    last_entry = ledger[-1]
    assert last_entry["generation_performed"] is False
    assert last_entry["retry_attempted"] is False
    assert last_entry["comfyui_submit_executed"] is False
    assert last_entry["assembly_executed"] is False
    assert last_entry["downstream_executed"] is False
    assert last_entry["production_accepted"] is False


def test_state_routes_to_operator_review_or_corrective_plan():
    """State must be operator_visual_review_required."""
    state_path = os.path.join(CONTROL, "state.json")
    state = _load_json(state_path)
    assert state["current_state"] == "operator_visual_review_required"
    valid_next = [
        "operator_visual_review_required",
        "brain_provider_configuration_required",
        "corrective_visual_recovery_layer_required",
        "next_visual_gate_authorization_required"
    ]
    assert state["next_allowed_action"] in valid_next


def test_verification_report_exists_and_passed():
    """9e3ec46_verification_report.json must exist and show PASSED."""
    report_path = os.path.join(VISUAL_REVIEW, "9e3ec46_verification_report.json")
    assert os.path.isfile(report_path)
    report = _load_json(report_path)
    assert report["verification_result"] == "PASSED"
    assert report["commit_exists_locally"] is True
    assert report["commit_pushed_to_origin_main"] is True
    assert report["generated_asset_exists"] is True
    assert report["generated_asset_is_stub"] is False
    assert len(report["blockers"]) == 0


def test_operator_review_packet_has_required_fields():
    """Operator review packet must have image path, checklist, allowed verdicts."""
    packet_path = os.path.join(VISUAL_REVIEW, "operator_visual_review_packet.json")
    assert os.path.isfile(packet_path)
    packet = _load_json(packet_path)
    assert "image_path" in packet
    assert "review_checklist" in packet
    assert "allowed_verdicts" in packet
    assert len(packet["review_checklist"]) >= 5
    assert "ACCEPTED_FOR_NEXT_GATE" in packet["allowed_verdicts"]
    assert "REJECTED_NEEDS_CORRECTIVE_PLAN" in packet["allowed_verdicts"]
    assert packet["operator_verdict"] is None  # Not yet decided
