"""
Tests for RC-COMBINE-V2-FRESH-VISUAL-GENERATION-PREFLIGHT-CLEANUP-001
Covers: dirty-git blocker detection, file classification, root-proof relocation,
        unsafe-file blocking, forbidden actions, state repair, and ledger consistency.
"""
import json
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTROL_DIR = os.path.join(
    PROJECT_ROOT, "data", "rc2_multishot1_ep01", "output", "control"
)
PROOF_ARCHIVE_DIR = os.path.join(CONTROL_DIR, "proof_archive")


def _load(filename):
    path = os.path.join(CONTROL_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. Dirty git blocker detected and resolved
# ---------------------------------------------------------------------------

def test_dirty_git_blocker_detected():
    inv = _load("fresh_visual_generation_dirty_tree_inventory.json")
    assert inv["blocker_detected"] is False, "All files were explained; no remaining blocker"
    assert inv["all_files_explained"] is True


def test_dirty_git_blocker_resolved_in_state():
    state = _load("state.json")
    assert state["dirty_git_blocker_resolved"] is True
    assert state["preflight_cleanup_completed"] is True


# ---------------------------------------------------------------------------
# 2. Modified canonical control files classified correctly
# ---------------------------------------------------------------------------

def test_modified_canonical_files_classified():
    inv = _load("fresh_visual_generation_dirty_tree_inventory.json")
    canonical = inv["canonical_control_files"]
    assert len(canonical) == 3
    assert any("FRESH-VISUAL-STRATEGY-REFERENCE-INTEGRATION" in p for p in canonical)
    assert any("QUALITY-REFERENCE-REGISTRATION" in p for p in canonical)
    assert any("fresh_visual_strategy_manifest" in p for p in canonical)
    for m in inv["modified_files"]:
        assert m["classification"] == "canonical_control_file"
        assert m["safe_to_stage"] is True


# ---------------------------------------------------------------------------
# 3. Root-level proof JSON files classified and relocated
# ---------------------------------------------------------------------------

def test_root_proof_jsons_classified():
    inv = _load("fresh_visual_generation_dirty_tree_inventory.json")
    assert len(inv["root_level_proof_json_files"]) == 5
    for f in inv["untracked_files"]:
        assert f["classification"] == "root_level_proof_json"
        assert f["location"] == "repo_root"
        assert f["safe_to_relocate"] is True


def test_root_proof_jsons_relocated_to_archive():
    expected = [
        "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GATE-VERIFY-001_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001-FREEZE_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001_proof.json",
        "RC-COMBINE-V2-QA-REPAIRABILITY-GATE-NEXT-STAGE-PLANNING-001_proof.json",
    ]
    for fname in expected:
        dest = os.path.join(PROOF_ARCHIVE_DIR, fname)
        assert os.path.isfile(dest), f"Missing in proof_archive: {fname}"


def test_root_proof_jsons_not_in_repo_root():
    root = PROJECT_ROOT
    expected = [
        "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GATE-VERIFY-001_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-CORRECTIVE-GENERATE-ONE-001_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001-FREEZE_proof.json",
        "RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001_proof.json",
        "RC-COMBINE-V2-QA-REPAIRABILITY-GATE-NEXT-STAGE-PLANNING-001_proof.json",
    ]
    for fname in expected:
        assert not os.path.isfile(os.path.join(root, fname)), \
            f"Root-level proof JSON still in repo root: {fname}"


# ---------------------------------------------------------------------------
# 4. No unsafe / unknown files remain
# ---------------------------------------------------------------------------

def test_no_unsafe_unknown_files():
    inv = _load("fresh_visual_generation_dirty_tree_inventory.json")
    assert inv["unsafe_or_unknown_files"] == []

    result = _load("fresh_visual_generation_preflight_cleanup_result.json")
    assert result["unsafe_files_remaining"] is False


# ---------------------------------------------------------------------------
# 5. Destructive git commands not used
# ---------------------------------------------------------------------------

def test_no_destructive_git_used():
    inv = _load("fresh_visual_generation_dirty_tree_inventory.json")
    assert inv["destructive_git_used"] is False

    result = _load("fresh_visual_generation_preflight_cleanup_result.json")
    assert result["destructive_git_used"] is False

    report = _load("fresh_visual_generation_git_freeze_repair_report.json")
    assert report["resolution"]["destructive_commands_used"] is False
    assert report["resolution"]["git_reset_hard_used"] is False
    assert report["resolution"]["git_clean_fd_used"] is False
    assert report["resolution"]["files_silently_deleted"] is False


# ---------------------------------------------------------------------------
# 6. Generation not executed
# ---------------------------------------------------------------------------

def test_no_generation_executed():
    proof = _load("fresh_visual_generation_preflight_cleanup_proof.json")
    assert proof["generation_performed"] is False
    assert proof["comfyui_submit_executed"] is False
    assert proof["prompt_id_created"] is False
    assert proof["retry_attempted"] is False


def test_no_comfyui_submit_executed():
    result = _load("fresh_visual_generation_preflight_cleanup_result.json")
    assert result["comfyui_submit_executed"] is False


# ---------------------------------------------------------------------------
# 7. State returns to fresh_visual_generation_authorized
# ---------------------------------------------------------------------------

def test_state_is_fresh_visual_generation_authorized():
    state = _load("state.json")
    assert state["current_state"] == "fresh_visual_generation_authorized"


def test_next_action_is_execute_required():
    state = _load("state.json")
    assert state["next_allowed_action"] == "fresh_visual_generation_execute_required"


# ---------------------------------------------------------------------------
# 8. production_accepted remains false
# ---------------------------------------------------------------------------

def test_production_accepted_false():
    state = _load("state.json")
    assert state["production_accepted"] is False

    proof = _load("fresh_visual_generation_preflight_cleanup_proof.json")
    assert proof["production_accepted"] is False


# ---------------------------------------------------------------------------
# 9. artifact_index updated
# ---------------------------------------------------------------------------

def test_artifact_index_updated():
    idx = _load("artifact_index.json")
    assert idx.get("preflight_cleanup_task") == \
        "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-PREFLIGHT-CLEANUP-001"
    assert "proof_archive_dir" in idx
    assert len(idx.get("proof_archive_files", [])) == 5
    assert idx.get("preflight_cleanup_state") == "fresh_visual_generation_authorized"
    assert idx.get("preflight_cleanup_next_action") == "fresh_visual_generation_execute_required"


# ---------------------------------------------------------------------------
# 10. episode_ledger updated
# ---------------------------------------------------------------------------

def test_episode_ledger_updated():
    ledger = _load("episode_ledger.json")
    assert isinstance(ledger, list)
    cleanup_events = [
        e for e in ledger
        if e.get("task_id") == "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-PREFLIGHT-CLEANUP-001"
    ]
    assert len(cleanup_events) >= 1
    ev = cleanup_events[-1]
    assert ev["current_state"] == "fresh_visual_generation_authorized"
    assert ev["next_allowed_action"] == "fresh_visual_generation_execute_required"
    assert ev["generation_performed"] is False
    assert ev["production_accepted"] is False
    assert ev["artifact_index_updated"] is True
    assert ev["state_updated"] is True


# ---------------------------------------------------------------------------
# 11. Required cleanup artifacts exist on disk
# ---------------------------------------------------------------------------

def test_required_artifacts_exist():
    required = [
        "fresh_visual_generation_dirty_tree_inventory.json",
        "fresh_visual_generation_preflight_cleanup_plan.json",
        "fresh_visual_generation_preflight_cleanup_result.json",
        "fresh_visual_generation_git_freeze_repair_report.json",
        "fresh_visual_generation_preflight_cleanup_proof.json",
        "artifact_index.json",
        "episode_ledger.json",
    ]
    for fname in required:
        path = os.path.join(CONTROL_DIR, fname)
        assert os.path.isfile(path), f"Missing required artifact: {fname}"
