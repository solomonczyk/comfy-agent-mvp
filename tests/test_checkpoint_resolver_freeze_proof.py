"""Tests for the checkpoint resolver freeze proof artifact.

RC-COMBINE-V2-98001-99000-FREEZE:
  - freeze_proof_requires_commit_hash
  - freeze_proof_requires_pushed_status
  - freeze_proof_requires_clean_git
  - local_checkpoints_found
  - sd_xl_base_candidate_detected
  - checkpoint_sdxl_base_mapping_valid
  - previous_acquisition_required_corrected
  - generation_gate_revalidated_without_submit
  - generation_not_performed
  - comfyui_submit_not_executed
  - production_accepted_false
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CONTROL_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "rc2_multishot1_ep01"
    / "output"
    / "control"
)

FREEZE_PROOF_PATH = CONTROL_DIR / "checkpoint_resolver_freeze_proof.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_freeze_proof() -> dict:
    """Load the real freeze proof artifact."""
    assert FREEZE_PROOF_PATH.exists(), (
        f"Freeze proof artifact not found: {FREEZE_PROOF_PATH}"
    )
    with open(FREEZE_PROOF_PATH) as f:
        return json.load(f)


def _create_freeze_proof(overrides: dict | None = None) -> dict:
    """Create a minimal freeze proof dict for isolated testing."""
    data = {
        "task_id": "RC-COMBINE-V2-98001-99000-FREEZE",
        "previous_task_id": "RC-COMBINE-V2-98001-99000",
        "freeze_verified": True,
        "resolver_scan_paths_fixed": True,
        "local_checkpoints_found": True,
        "found_checkpoints": [
            "CyberRealisticXLPlay_V7.0_FP16.safetensors",
            "juggernautXL_version2.safetensors",
            "realvisxlV50_v50Bakedvae.safetensors",
            "sd_xl_base_1.0_0.9vae.safetensors",
        ],
        "checkpoint_sdxl_base_mapping_checked": True,
        "sd_xl_base_1.0_0.9vae_candidate_detected": True,
        "previous_acquisition_required_retracted_or_corrected": True,
        "generation_gate_revalidated": True,
        "download_performed": False,
        "install_performed": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "commit_hash": "f8fa1131096f1c4348cb093c989e300a6386dbfc",
        "push_status": "pushed_origin_main",
        "git_status_clean": True,
        "next_layer": "RC-COMBINE-V2-99001-102000 Controlled Generation Authorization and Single Execution Gate",
    }
    if overrides:
        data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Test: freeze proof artifact exists and is valid JSON
# ---------------------------------------------------------------------------

def test_freeze_proof_artifact_exists() -> None:
    """The freeze proof artifact must exist on disk."""
    assert FREEZE_PROOF_PATH.exists(), (
        f"Freeze proof artifact missing: {FREEZE_PROOF_PATH}"
    )


def test_freeze_proof_is_valid_json() -> None:
    """Freeze proof must be valid JSON."""
    proof = _load_freeze_proof()
    assert isinstance(proof, dict), "Freeze proof must be a JSON object"


# ---------------------------------------------------------------------------
# Test: freeze_proof_requires_commit_hash
# ---------------------------------------------------------------------------

def test_freeze_proof_contains_commit_hash() -> None:
    """Freeze proof must contain a non-empty commit_hash."""
    proof = _load_freeze_proof()
    commit_hash = proof.get("commit_hash", "")
    assert commit_hash, "commit_hash must be present and non-empty"
    assert isinstance(commit_hash, str), "commit_hash must be a string"
    assert len(commit_hash) >= 7, (
        f"commit_hash seems too short: {commit_hash}"
    )


# ---------------------------------------------------------------------------
# Test: freeze_proof_requires_pushed_status
# ---------------------------------------------------------------------------

def test_freeze_proof_contains_push_status() -> None:
    """Freeze proof must contain a push_status field."""
    proof = _load_freeze_proof()
    push_status = proof.get("push_status", "")
    assert push_status, "push_status must be present and non-empty"
    assert push_status in (
        "pushed_origin_main",
        "not_pushed",
        "push_failed",
    ), f"Unexpected push_status: {push_status}"


# ---------------------------------------------------------------------------
# Test: freeze_proof_requires_clean_git
# ---------------------------------------------------------------------------

def test_freeze_proof_requires_clean_git_field() -> None:
    """Freeze proof must contain a git_status_clean boolean field."""
    proof = _load_freeze_proof()
    assert "git_status_clean" in proof, (
        "Freeze proof missing git_status_clean field"
    )
    assert isinstance(proof["git_status_clean"], bool), (
        "git_status_clean must be boolean"
    )


# ---------------------------------------------------------------------------
# Test: local_checkpoints_found
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expected_name", [
    "CyberRealisticXLPlay_V7.0_FP16.safetensors",
    "juggernautXL_version2.safetensors",
    "realvisxlV50_v50Bakedvae.safetensors",
    "sd_xl_base_1.0_0.9vae.safetensors",
])
def test_freeze_proof_lists_all_expected_checkpoints(expected_name: str) -> None:
    """Freeze proof must list all 4 expected checkpoint files in found_checkpoints."""
    proof = _load_freeze_proof()
    found = proof.get("found_checkpoints", [])
    assert expected_name in found, (
        f"Expected checkpoint {expected_name} not in freeze proof found_checkpoints"
    )


# ---------------------------------------------------------------------------
# Test: sd_xl_base_candidate_detected
# ---------------------------------------------------------------------------

def test_freeze_proof_sdxl_base_candidate_detected() -> None:
    """Freeze proof must confirm sd_xl_base candidate was detected."""
    proof = _load_freeze_proof()
    assert proof.get("sd_xl_base_1.0_0.9vae_candidate_detected") is True, (
        "sd_xl_base_1.0_0.9vae_candidate_detected must be true"
    )
    assert "sd_xl_base_1.0_0.9vae.safetensors" in proof.get("found_checkpoints", []), (
        "sd_xl_base_1.0_0.9vae.safetensors must be in found_checkpoints"
    )


# ---------------------------------------------------------------------------
# Test: checkpoint_sdxl_base_mapping_valid
# ---------------------------------------------------------------------------

def test_freeze_proof_checkpoint_mapping_valid() -> None:
    """Freeze proof must confirm checkpoint_sdxl_base mapping was checked."""
    proof = _load_freeze_proof()
    assert proof.get("checkpoint_sdxl_base_mapping_checked") is True, (
        "checkpoint_sdxl_base_mapping_checked must be true"
    )


# ---------------------------------------------------------------------------
# Test: previous_acquisition_required_corrected
# ---------------------------------------------------------------------------

def test_freeze_proof_acquisition_required_corrected() -> None:
    """Freeze proof must confirm previous acquisition_required was retracted."""
    proof = _load_freeze_proof()
    assert proof.get("previous_acquisition_required_retracted_or_corrected") is True, (
        "previous_acquisition_required_retracted_or_corrected must be true"
    )


# ---------------------------------------------------------------------------
# Test: generation_gate_revalidated_without_submit
# ---------------------------------------------------------------------------

def test_freeze_proof_generation_gate_revalidated() -> None:
    """Freeze proof must confirm generation gate was revalidated."""
    proof = _load_freeze_proof()
    assert proof.get("generation_gate_revalidated") is True, (
        "generation_gate_revalidated must be true"
    )


# ---------------------------------------------------------------------------
# Test: generation_not_performed
# ---------------------------------------------------------------------------

def test_freeze_proof_generation_not_performed() -> None:
    """Freeze proof must show generation_performed is false."""
    proof = _load_freeze_proof()
    assert proof.get("generation_performed") is False, (
        "generation_performed must be false"
    )


# ---------------------------------------------------------------------------
# Test: comfyui_submit_not_executed
# ---------------------------------------------------------------------------

def test_freeze_proof_comfyui_submit_not_executed() -> None:
    """Freeze proof must show comfyui_submit_executed is false."""
    proof = _load_freeze_proof()
    assert proof.get("comfyui_submit_executed") is False, (
        "comfyui_submit_executed must be false"
    )


# ---------------------------------------------------------------------------
# Test: production_accepted_false
# ---------------------------------------------------------------------------

def test_freeze_proof_production_not_accepted() -> None:
    """Freeze proof must show production_accepted is false."""
    proof = _load_freeze_proof()
    assert proof.get("production_accepted") is False, (
        "production_accepted must be false"
    )


# ---------------------------------------------------------------------------
# Test: isolated proof with synthetic data
# ---------------------------------------------------------------------------

def test_freeze_proof_isolation_local_checkpoints() -> None:
    """Isolated freeze proof must validate found_checkpoints list."""
    proof = _create_freeze_proof()
    found = proof.get("found_checkpoints", [])
    assert len(found) == 4
    assert "sd_xl_base_1.0_0.9vae.safetensors" in found


def test_freeze_proof_isolation_forbidden_flags() -> None:
    """All forbidden flags must be false in isolated proof."""
    proof = _create_freeze_proof()
    assert proof["download_performed"] is False
    assert proof["install_performed"] is False
    assert proof["generation_performed"] is False
    assert proof["comfyui_submit_executed"] is False
    assert proof["visual_qa_executed"] is False
    assert proof["assembly_executed"] is False
    assert proof["downstream_executed"] is False
    assert proof["production_accepted"] is False


def test_freeze_proof_isolation_git_fields() -> None:
    """Isolated freeze proof must validate git-related fields."""
    proof = _create_freeze_proof()
    assert len(proof["commit_hash"]) >= 7
    assert proof["push_status"] == "pushed_origin_main"
    assert proof["git_status_clean"] is True


def test_freeze_proof_isolation_next_layer() -> None:
    """Freeze proof must specify the correct next layer."""
    proof = _create_freeze_proof()
    assert proof["next_layer"] == (
        "RC-COMBINE-V2-99001-102000 Controlled Generation Authorization and Single Execution Gate"
    )


def test_freeze_proof_isolation_task_id() -> None:
    """Freeze proof must have the correct task_id."""
    proof = _create_freeze_proof()
    assert proof["task_id"] == "RC-COMBINE-V2-98001-99000-FREEZE"
    assert proof["previous_task_id"] == "RC-COMBINE-V2-98001-99000"


def test_freeze_proof_isolation_scenario_dirty_git_fails() -> None:
    """A proof with git_status_clean=false must not pass acceptance."""
    proof = _create_freeze_proof({"git_status_clean": False})
    assert proof["git_status_clean"] is False
    # Acceptance criteria requires git_status_clean=true
    acceptance_criteria = (
        proof["commit_hash"] and
        proof["push_status"] == "pushed_origin_main" and
        proof["git_status_clean"] is True and
        proof["generation_performed"] is False and
        proof["comfyui_submit_executed"] is False and
        proof["production_accepted"] is False
    )
    assert not acceptance_criteria, (
        "Dirty git proof must not pass acceptance criteria"
    )


def test_freeze_proof_isolation_missing_hash_fails() -> None:
    """A proof without commit_hash must not pass acceptance."""
    proof = _create_freeze_proof({"commit_hash": ""})
    acceptance_criteria = (
        proof["commit_hash"] and
        proof["push_status"] == "pushed_origin_main" and
        proof["git_status_clean"] is True and
        proof["generation_performed"] is False and
        proof["comfyui_submit_executed"] is False and
        proof["production_accepted"] is False
    )
    assert not acceptance_criteria, (
        "Empty commit_hash proof must not pass acceptance criteria"
    )
