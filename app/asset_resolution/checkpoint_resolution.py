"""
Controlled Checkpoint Asset Resolution and Generation Gate Revalidation.

RC-COMBINE-V2-94001-98000:
  - Reads blocker artifacts from the generation gate layer
  - Scans local checkpoint inventory (read-only)
  - Evaluates candidates against SDXL workflow requirements
  - Creates resolution decision (exact match / substitution / acquisition required)
  - Creates controlled acquisition contracts if needed
  - Revalidates generation gate after resolution attempt
  - Updates artifact index and episode ledger

FORBIDDEN:
  - ComfyUI generation or submit
  - Fake checkpoint availability or install proof
  - Unapproved download or install
  - Blind substitution without operator review
  - Visual QA, preview render, assembly, downstream
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_ID = "RC-COMBINE-V2-94001-98000"
PREVIOUS_LAYER = "RC-COMBINE-V2-86001-94000 Generation-to-QA Package / Generation Gate"
NEXT_LAYER_READY = "generation_operator_authorization_required"
NEXT_LAYER_OPERATOR_REVIEW = "controlled_checkpoint_acquisition_operator_review_required"
NEXT_LAYER_ACQUISITION = "controlled_asset_acquisition_required"

# Expected asset
EXPECTED_CHECKPOINT_ASSET = "checkpoint_sdxl_base"
EXPECTED_CHECKPOINT_DISPLAY = "SDXL base checkpoint (checkpoint_sdxl_base)"

# SDXL compatibility markers
SDXL_KEYWORDS = ["sd_xl", "sdxl", "stable-diffusion-xl", "sd_xl_base", "sd xl base"]
SD15_KEYWORDS = ["sd15", "sd_1.5", "sd1.5", "stable-diffusion-v1.5", "1.5", "v1-5"]
REJECTED_CHECKPOINTS = set()

# Known ComfyUI checkpoint directories (relative to ComfyUI root)
COMFYUI_CHECKPOINT_SUBDIRS = [
    "models/checkpoints",
    "models/checkpoints/sdxl",
    "models/stable-diffusion",
]

# ---------------------------------------------------------------------------
# Schema keys for artifact outputs
# ---------------------------------------------------------------------------

CHECKPOINT_INVENTORY_SCHEMA = {
    "task_id": TASK_ID,
    "inventory_checked": True,
    "checkpoint_directories_scanned": [],
    "found_checkpoints": [],
    "sdxl_compatible_found": [],
    "sd15_found": [],
    "unknown_type_found": [],
    "comfyui_api_checked": False,
}

CANDIDATE_REVIEW_SCHEMA = {
    "task_id": TASK_ID,
    "candidate_assets_reviewed": True,
    "candidates": [],
    "rejected_candidates": [],
    "valid_candidates": [],
    "requires_operator_review": False,
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_control_dir(project_root: str) -> Path:
    return Path(project_root) / "output" / "control"


def _get_workflow_assets_dir(control_dir: Path) -> Path:
    return control_dir / "workflow_assets"


def _artifact_path(control_dir: Path, name: str) -> Path:
    return control_dir / name


# ---------------------------------------------------------------------------
# Artifact definitions (relative to output/control)
# ---------------------------------------------------------------------------

RESOLUTION_ARTIFACTS = {
    "checkpoint_resolution_decision": "checkpoint_resolution_decision.json",
    "checkpoint_local_inventory_report": "checkpoint_local_inventory_report.json",
    "checkpoint_candidate_review_report": "checkpoint_candidate_review_report.json",
    "checkpoint_resolution_gate_revalidation": "checkpoint_resolution_gate_revalidation.json",
}

ACQUISITION_ARTIFACTS = {
    "checkpoint_source_allowlist_decision": "checkpoint_source_allowlist_decision.json",
    "checkpoint_acquisition_execution_contract": "checkpoint_acquisition_execution_contract.json",
    "checkpoint_install_verification_contract": "checkpoint_install_verification_contract.json",
    "checkpoint_acquisition_blocker_report": "checkpoint_acquisition_blocker_report.json",
}

SUBSTITUTION_ARTIFACTS = {
    "checkpoint_substitution_operator_review_packet": "checkpoint_substitution_operator_review_packet.json",
}

# ---------------------------------------------------------------------------
# Resolution branch classifier
# ---------------------------------------------------------------------------

# Resolution branches ordered by preference
RESOLUTION_EXACT_AVAILABLE = "exact_checkpoint_available"
RESOLUTION_LOCAL_CANDIDATE = "local_candidate_operator_review_required"
RESOLUTION_ACQUISITION_REQUIRED = "acquisition_required"
RESOLUTION_UNRESOLVED_BLOCKER = "unresolved_blocker"

# Fine-grained status values (RC-COMBINE-V2-98001-99000)
STATUS_EXACT_MATCH_FOUND = "exact_match_found"
STATUS_ACCEPTABLE_LOCAL_CANDIDATE = "acceptable_local_candidate_found"
STATUS_CANDIDATE_REQUIRES_REVIEW = "candidate_requires_operator_review"
STATUS_ACQUISITION_REQUIRED = "acquisition_required"

# Canonical exact-match filenames for checkpoint_sdxl_base
# RC-COMBINE-V2-98001-99000: strict exact match = file named sd_xl_base_1.0
CANONICAL_CHECKPOINT_NAMES = [
    "sd_xl_base_1.0.safetensors",
    "sd_xl_base_1.0_fp16.safetensors",
]

# Acceptable local candidates — files that can resolve checkpoint_sdxl_base
# even when they are not the canonical exact name.
# RC-COMBINE-V2-98001-99000: mapping logical_asset_id → known acceptable files
ACCEPTABLE_CANDIDATE_NAMES = {
    "checkpoint_sdxl_base": [
        "sd_xl_base_1.0_0.9vae.safetensors",
    ],
}


def _read_blocker_artifacts(project_root: str) -> Dict[str, Any]:
    """Read existing blocker-related artifacts.

    Returns dict with loaded artifact data.
    """
    control_dir = _get_control_dir(project_root)

    artifacts = {}
    paths = [
        ("generation_gate_decision", control_dir / "generation_gate_decision.json"),
        ("generation_runtime_blocker_report", control_dir / "generation_runtime_blocker_report.json"),
        ("controlled_asset_acquisition_gate_packet", control_dir / "controlled_asset_acquisition_gate_packet.json"),
        ("asset_requirements", control_dir / "workflow_assets" / "asset_requirements.json"),
        ("asset_inventory", control_dir / "workflow_assets" / "asset_inventory.json"),
        ("asset_resolution_plan", control_dir / "workflow_assets" / "asset_resolution_plan.json"),
        ("asset_verification_report", control_dir / "workflow_assets" / "asset_verification_report.json"),
    ]

    for key, path in paths:
        artifacts[key] = _load_json(path)

    # Also check the combine_v2 variants
    for key, filename in [
        ("asset_requirements_v2", "combine_v2_asset_requirements_contract.json"),
        ("asset_inventory_v2", "combine_v2_asset_inventory_contract.json"),
    ]:
        path = control_dir / filename
        artifacts[key] = _load_json(path)

    return artifacts


def _find_missing_checkpoint(artifacts: Dict[str, Any]) -> Optional[str]:
    """Extract the missing checkpoint identifier from blocker artifacts."""
    gate = artifacts.get("generation_gate_decision", {})
    if gate:
        for b in gate.get("blockers", []):
            missing = b.get("missing_asset")
            if missing:
                return missing
            detail = b.get("detail", "")
            m = re.search(r"'([^']+)'", detail)
            if m:
                return m.group(1)

    blocker = artifacts.get("generation_runtime_blocker_report", {})
    if blocker:
        missing = blocker.get("missing_asset", "")
        if missing and missing != "unknown":
            return missing

    packet = artifacts.get("controlled_asset_acquisition_gate_packet", {})
    if packet:
        return packet.get("missing_asset")

    plan = artifacts.get("asset_resolution_plan", {})
    if plan:
        missing = plan.get("missing_assets", [])
        if missing:
            return missing[0]

    return EXPECTED_CHECKPOINT_ASSET


# ---------------------------------------------------------------------------
# Local inventory scanning (read-only)
# ---------------------------------------------------------------------------

def _find_comfyui_root() -> Optional[Path]:
    """Try to locate ComfyUI root relative to the project or common locations."""
    # Known portable ComfyUI installation path (RC-COMBINE-V2-98001-99000)
    portable_root = (
        Path("F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126")
        / "ComfyUI_windows_portable"
        / "ComfyUI"
    )

    # Check common relative paths
    candidates = [
        portable_root,
        Path("F:/ComfyUI"),
        Path("C:/ComfyUI"),
        Path("D:/ComfyUI"),
        Path("E:/ComfyUI"),
        Path.home() / "ComfyUI",
        Path.cwd().parent / "ComfyUI",
    ]
    for c in candidates:
        if c.exists() and (c / "main.py").exists():
            return c
    return None


def _scan_comfyui_checkpoints(comfyui_root: Path) -> List[Dict[str, Any]]:
    """Scan ComfyUI checkpoint directories for checkpoint files.

    Returns a list of dicts with file info. Read-only — does not modify.
    """
    found = []
    seen = set()

    for subdir in COMFYUI_CHECKPOINT_SUBDIRS:
        d = comfyui_root / subdir
        if not d.is_dir():
            continue
        try:
            for entry in d.iterdir():
                if entry.is_file() and entry.suffix.lower() in (".safetensors", ".ckpt", ".pt", ".pth"):
                    if entry.name not in seen:
                        seen.add(entry.name)
                        found.append({
                            "file_name": entry.name,
                            "file_path": str(entry),
                            "file_size_bytes": entry.stat().st_size,
                            "last_modified": datetime.fromtimestamp(
                                entry.stat().st_mtime, tz=timezone.utc
                            ).isoformat(),
                            "source": str(d),
                        })
        except PermissionError:
            continue

    return found


def _detect_checkpoint_type(checkpoint: Dict[str, Any]) -> str:
    """Classify a checkpoint as SDXL, SD1.5, or unknown based on filename."""
    name_lower = checkpoint.get("file_name", "").lower()

    # Check for SDXL keywords
    for kw in SDXL_KEYWORDS:
        if kw in name_lower:
            return "sdxl"

    # Check for SD1.5 keywords
    for kw in SD15_KEYWORDS:
        if kw in name_lower:
            return "sd15"

    # Heuristic: SDXL checkpoints are typically > 5GB
    size_bytes = checkpoint.get("file_size_bytes", 0)
    if size_bytes > 5_000_000_000:
        return "sdxl_suspect"
    if size_bytes > 1_500_000_000 and size_bytes < 3_000_000_000:
        return "sd15_suspect"

    return "unknown"


def _build_skip_reason(checkpoint: Dict[str, Any], ckpt_type: str) -> Optional[str]:
    """Determine if a checkpoint should be rejected and why."""
    name = checkpoint.get("file_name", "")

    # Reject prior visually rejected checkpoints if marked high risk
    for rejected in REJECTED_CHECKPOINTS:
        if rejected.lower() in name.lower():
            return f"Rejected: previously marked as high-risk ({rejected})"

    # Explicit SD1.5 rejection for SDXL requirement
    if ckpt_type == "sd15":
        return "Rejected: SD1.5 checkpoint incompatible with SDXL workflow requirement"

    if ckpt_type == "sd15_suspect":
        return "Rejected: file size suggests SD1.5, incompatible with SDXL requirement"

    return None


def scan_local_checkpoint_inventory(project_root: str) -> Dict[str, Any]:
    """Scan local checkpoint inventory (read-only).

    Returns inventory report with categorized findings.
    Does NOT check ComfyUI API (only filesystem scan).
    """
    comfyui_root = _find_comfyui_root()
    scanned_dirs = list(COMFYUI_CHECKPOINT_SUBDIRS)
    found_checkpoints = []
    comfyui_api_checked = False

    if comfyui_root is not None:
        found_checkpoints = _scan_comfyui_checkpoints(comfyui_root)
        # Update actual scanned dirs
        scanned_dirs = []
        for subdir in COMFYUI_CHECKPOINT_SUBDIRS:
            d = comfyui_root / subdir
            if d.exists():
                scanned_dirs.append(str(d))
    else:
        # No ComfyUI root found — report scanned but empty
        scanned_dirs = ["ComfyUI root not found"]

    # Classify
    sdxl_found = []
    sd15_found = []
    unknown_found = []
    rejected = []
    valid_candidates = []

    for ckpt in found_checkpoints:
        ckpt_type = _detect_checkpoint_type(ckpt)
        skip_reason = _build_skip_reason(ckpt, ckpt_type)

        entry = {
            **ckpt,
            "detected_type": ckpt_type,
        }

        # Populate type-specific lists regardless of rejection
        if ckpt_type in ("sd15", "sd15_suspect"):
            sd15_found.append(entry)
        elif ckpt_type in ("sdxl", "sdxl_suspect"):
            sdxl_found.append(entry)
        else:
            unknown_found.append(entry)

        # Then determine acceptance/rejection
        if skip_reason:
            entry["rejection_reason"] = skip_reason
            rejected.append(entry)
        elif ckpt_type in ("sdxl", "sdxl_suspect"):
            valid_candidates.append(entry)

    # Check for exact match and acceptable match (RC-COMBINE-V2-98001-99000)
    # Use canonical name list first, then acceptable mapping
    exact_match = None
    acceptable_match = None
    for sdxl_entry in sdxl_found:
        fname = sdxl_entry.get("file_name", "").lower()
        if fname in [n.lower() for n in CANONICAL_CHECKPOINT_NAMES]:
            exact_match = sdxl_entry
            break

    if exact_match is None:
        acceptable_names = [
            n.lower() for n in ACCEPTABLE_CANDIDATE_NAMES.get("checkpoint_sdxl_base", [])
        ]
        for sdxl_entry in sdxl_found:
            fname = sdxl_entry.get("file_name", "").lower()
            if fname in acceptable_names:
                acceptable_match = sdxl_entry
                break

    # Fallback: token-based heuristic for any file containing sd/xl/base
    if exact_match is None and acceptable_match is None:
        for c in sdxl_found:
            name = c.get("file_name", "").lower().replace("_", " ").replace("-", " ")
            tokens = name.split()
            if "sd" in tokens and "xl" in tokens and "base" in tokens:
                exact_match = c
                break

    # Build the match entry shown in the inventory
    match_entry = exact_match or acceptable_match

    # Determine fine-grained resolution_status
    if exact_match:
        sdxl_match_status = STATUS_EXACT_MATCH_FOUND
    elif acceptable_match:
        sdxl_match_status = STATUS_ACCEPTABLE_LOCAL_CANDIDATE
    else:
        sdxl_match_status = None  # determined later in resolution decision

    inventory = {
        "task_id": TASK_ID,
        "inventory_checked": True,
        "checkpoint_directories_scanned": scanned_dirs,
        "comfyui_root_found": comfyui_root is not None,
        "comfyui_root_path": str(comfyui_root) if comfyui_root else None,
        "found_checkpoints": [
            {"file_name": c["file_name"], "file_size_bytes": c["file_size_bytes"],
             "detected_type": c.get("detected_type", "unknown")}
            for c in found_checkpoints
        ],
        "sdxl_compatible_found": [
            {"file_name": c["file_name"], "file_size_bytes": c["file_size_bytes"],
             "detected_type": c.get("detected_type", "sdxl")}
            for c in sdxl_found
        ],
        "sdxl_exact_match_found": exact_match is not None,
        "sdxl_acceptable_match_found": acceptable_match is not None,
        "sdxl_exact_match": {
            "file_name": exact_match["file_name"],
            "file_path": exact_match["file_path"],
            "file_size_bytes": exact_match["file_size_bytes"],
            "match_type": STATUS_EXACT_MATCH_FOUND,
        } if exact_match else None,
        "sdxl_acceptable_match": {
            "file_name": acceptable_match["file_name"],
            "file_path": acceptable_match["file_path"],
            "file_size_bytes": acceptable_match["file_size_bytes"],
            "match_type": STATUS_ACCEPTABLE_LOCAL_CANDIDATE,
        } if acceptable_match else None,
        "sd15_found": [
            {"file_name": c["file_name"], "file_size_bytes": c["file_size_bytes"]}
            for c in sd15_found
        ],
        "unknown_type_found": [
            {"file_name": c["file_name"], "file_size_bytes": c["file_size_bytes"]}
            for c in unknown_found
        ],
        "rejected_checkpoints": [
            {"file_name": c["file_name"], "rejection_reason": c["rejection_reason"]}
            for c in rejected
        ],
        "valid_candidates": [
            {"file_name": c["file_name"], "file_size_bytes": c["file_size_bytes"],
             "detected_type": c.get("detected_type", "sdxl")}
            for c in valid_candidates
        ],
        "comfyui_api_checked": comfyui_api_checked,
        "total_checkpoints_found": len(found_checkpoints),
        "total_valid_candidates": len(valid_candidates),
        "total_rejected": len(rejected),
        "sdxl_match_status": sdxl_match_status,
        "checkpoint_mapping": {
            "logical_asset_id": EXPECTED_CHECKPOINT_ASSET,
            "canonical_filenames": CANONICAL_CHECKPOINT_NAMES,
            "acceptable_candidates": ACCEPTABLE_CANDIDATE_NAMES.get(EXPECTED_CHECKPOINT_ASSET, []),
        },
        "timestamp": _utcnow(),
    }

    return inventory


# ---------------------------------------------------------------------------
# Candidate evaluation
# ---------------------------------------------------------------------------

def evaluate_checkpoint_candidates(
    inventory: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate checkpoint candidates against workflow requirements.

    Returns candidate review report.
    """
    candidates = inventory.get("valid_candidates", [])
    rejected = inventory.get("rejected_checkpoints", [])

    # No candidates found
    if not candidates:
        return {
            "task_id": TASK_ID,
            "candidate_assets_reviewed": True,
            "candidates": [],
            "rejected_candidates": rejected,
            "valid_candidates": [],
            "requires_operator_review": False,
            "exact_match_available": False,
            "substitution_candidate_available": False,
            "no_candidates_found": True,
            "reason": "No SDXL-compatible checkpoints found in local inventory",
            "timestamp": _utcnow(),
        }

    # Check for exact or acceptable match
    # RC-COMBINE-V2-98001-99000: acceptable_local_candidate_found resolves without review
    exact_match = inventory.get("sdxl_exact_match")
    acceptable_match = inventory.get("sdxl_acceptable_match")

    if exact_match:
        return {
            "task_id": TASK_ID,
            "candidate_assets_reviewed": True,
            "candidates": candidates,
            "rejected_candidates": rejected,
            "valid_candidates": candidates,
            "requires_operator_review": False,
            "exact_match_available": True,
            "exact_match": exact_match,
            "acceptable_match_available": False,
            "substitution_candidate_available": False,
            "no_candidates_found": False,
            "reason": f"Exact SDXL checkpoint found: {exact_match['file_name']}",
            "timestamp": _utcnow(),
        }

    if acceptable_match:
        return {
            "task_id": TASK_ID,
            "candidate_assets_reviewed": True,
            "candidates": candidates,
            "rejected_candidates": rejected,
            "valid_candidates": candidates,
            "requires_operator_review": False,
            "exact_match_available": True,  # treat as resolved
            "exact_match": acceptable_match,
            "acceptable_match_available": True,
            "acceptable_match": acceptable_match,
            "substitution_candidate_available": False,
            "no_candidates_found": False,
            "reason": f"Acceptable SDXL checkpoint candidate found: {acceptable_match['file_name']} (mapped via checkpoint_sdxl_base)",
            "timestamp": _utcnow(),
        }

    # Candidates exist but not exact match — operator review required
    return {
        "task_id": TASK_ID,
        "candidate_assets_reviewed": True,
        "candidates": [
            {"file_name": c["file_name"],
             "detected_type": c.get("detected_type", "sdxl"),
             "file_size_bytes": c.get("file_size_bytes", 0),
             "auto_substitution_allowed": False,
             "requires_operator_approval": True}
            for c in candidates
        ],
        "rejected_candidates": rejected,
        "valid_candidates": candidates,
        "requires_operator_review": True,
        "exact_match_available": False,
        "substitution_candidate_available": True,
        "no_candidates_found": False,
        "reason": "SDXL-compatible candidate(s) found but require operator review",
        "requires_operator_approval": True,
        "timestamp": _utcnow(),
    }


# ---------------------------------------------------------------------------
# Resolution decision
# ---------------------------------------------------------------------------

def resolve_checkpoint_asset(project_root: str) -> Dict[str, Any]:
    """Full checkpoint asset resolution lifecycle.

    1. Read blocker artifacts
    2. Scan local inventory
    3. Evaluate candidates
    4. Create resolution decision
    5. Create acquisition contracts if needed
    6. Revalidate generation gate
    7. Update artifact index and episode ledger

    Returns the resolution result dict.
    """
    control_dir = _get_control_dir(project_root)
    artifacts = _read_blocker_artifacts(project_root)
    missing_checkpoint = _find_missing_checkpoint(artifacts)

    # --- Step 1: Verify blocker is checkpoint-related ---
    gate_decision = artifacts.get("generation_gate_decision", {})
    generation_blocked = gate_decision.get("generation_can_be_authorized", False) is False

    if not generation_blocked:
        # Generation is not blocked — no resolution needed
        return _build_no_blocker_result(project_root)

    # --- Step 2: Scan local inventory ---
    inventory = scan_local_checkpoint_inventory(project_root)

    # --- Step 3: Evaluate candidates ---
    candidate_review = evaluate_checkpoint_candidates(inventory)

    # --- Step 4: Write inventory and candidate reports ---
    inventory_path = _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_local_inventory_report"])
    _write_json(inventory_path, inventory)

    candidate_path = _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_candidate_review_report"])
    _write_json(candidate_path, candidate_review)

    # --- Step 5: Determine resolution branch ---
    exact_match_available = candidate_review.get("exact_match_available", False)
    substitution_available = candidate_review.get("substitution_candidate_available", False)
    no_candidates = candidate_review.get("no_candidates_found", True)
    requires_operator = candidate_review.get("requires_operator_review", False)

    if exact_match_available:
        branch = RESOLUTION_EXACT_AVAILABLE
    elif substitution_available and not no_candidates:
        branch = RESOLUTION_LOCAL_CANDIDATE
    else:
        branch = RESOLUTION_ACQUISITION_REQUIRED

    # Track created artifacts
    created = {
        "checkpoint_resolution_decision": True,
        "checkpoint_local_inventory_report": True,
        "checkpoint_candidate_review_report": True,
    }

    # --- Step 6: Build resolution decision ---
    resolution_decision = _build_resolution_decision(
        branch, missing_checkpoint, inventory, candidate_review,
        exact_match_available, substitution_available, no_candidates, requires_operator,
    )

    resolution_path = _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_resolution_decision"])
    _write_json(resolution_path, resolution_decision)

    # --- Step 7: Branch-specific artifacts ---
    substitution_packet_created = False
    acquisition_contracts_created = {
        "source_allowlist": False,
        "execution_contract": False,
        "install_verification": False,
        "blocker_report": False,
    }

    if branch == RESOLUTION_EXACT_AVAILABLE:
        # Exact match — no operator review needed for the checkpoint itself
        pass

    elif branch == RESOLUTION_LOCAL_CANDIDATE:
        # Create substitution operator review packet
        substitution_packet = _build_substitution_packet(inventory, candidate_review)
        sub_path = _artifact_path(control_dir, SUBSTITUTION_ARTIFACTS["checkpoint_substitution_operator_review_packet"])
        _write_json(sub_path, substitution_packet)
        substitution_packet_created = True
        created["checkpoint_substitution_operator_review_packet"] = True

    elif branch == RESOLUTION_ACQUISITION_REQUIRED:
        # Create acquisition contracts
        acq_result = _create_acquisition_contracts(
            control_dir, missing_checkpoint, inventory, candidate_review,
        )
        acquisition_contracts_created = acq_result
        for key, val in acq_result.items():
            created[f"checkpoint_{key}"] = val

    # --- Step 8: Gate revalidation ---
    revalidation_result = _revalidate_generation_gate_internal(
        project_root, branch, resolution_decision, inventory, candidate_review,
    )
    revalidation_path = _artifact_path(
        control_dir, RESOLUTION_ARTIFACTS["checkpoint_resolution_gate_revalidation"]
    )
    _write_json(revalidation_path, revalidation_result)

    created["checkpoint_resolution_gate_revalidation"] = True

    # Current state and next action based on branch
    if branch == RESOLUTION_EXACT_AVAILABLE:
        current_state = NEXT_LAYER_READY
        next_allowed_action = NEXT_LAYER_READY
    elif branch == RESOLUTION_LOCAL_CANDIDATE:
        current_state = NEXT_LAYER_OPERATOR_REVIEW
        next_allowed_action = NEXT_LAYER_OPERATOR_REVIEW
    else:
        current_state = NEXT_LAYER_ACQUISITION
        next_allowed_action = NEXT_LAYER_ACQUISITION

    # Build result
    result = _build_result(
        project_root, branch, missing_checkpoint, inventory, candidate_review,
        resolution_decision, revalidation_result, current_state, next_allowed_action,
        substitution_packet_created, acquisition_contracts_created, created,
    )

    # Update artifact index and episode ledger
    _update_artifact_index(project_root, result)
    _update_episode_ledger(project_root, result)

    return result


def _build_no_blocker_result(project_root: str) -> Dict[str, Any]:
    """Build result when no checkpoint blocker exists."""
    return {
        "task_id": TASK_ID,
        "feature_completed": True,
        "checkpoint_blocker_read": True,
        "missing_checkpoint": None,
        "no_blocker_found": True,
        "message": "No active checkpoint blocker — generation gate is not blocked by checkpoint asset.",
        "generation_gate_already_clear": True,
        "checkpoint_resolved": True,
        "timestamp": _utcnow(),
    }


def _build_resolution_decision(
    branch: str,
    missing_checkpoint: str,
    inventory: Dict[str, Any],
    candidate_review: Dict[str, Any],
    exact_match_available: bool,
    substitution_available: bool,
    no_candidates: bool,
    requires_operator: bool,
) -> Dict[str, Any]:
    """Build the checkpoint resolution decision artifact."""
    # Determine fine-grained status (RC-COMBINE-V2-98001-99000)
    if branch == RESOLUTION_EXACT_AVAILABLE:
        # Check if it is a canonical exact match or acceptable candidate
        matched_entry = inventory.get("sdxl_exact_match") or inventory.get("sdxl_acceptable_match")
        matched_name = (matched_entry or {}).get("file_name", "")
        is_acceptable = bool(inventory.get("sdxl_acceptable_match"))
        if is_acceptable:
            resolution_status = STATUS_ACCEPTABLE_LOCAL_CANDIDATE
        else:
            resolution_status = STATUS_EXACT_MATCH_FOUND
    elif branch == RESOLUTION_LOCAL_CANDIDATE:
        resolution_status = STATUS_CANDIDATE_REQUIRES_REVIEW
    else:
        resolution_status = STATUS_ACQUISITION_REQUIRED

    return {
        "task_id": TASK_ID,
        "resolution_branch": branch,
        "resolution_status": resolution_status,
        "missing_checkpoint": missing_checkpoint,
        "checkpoint_resolved": branch == RESOLUTION_EXACT_AVAILABLE,
        "local_candidate_found": substitution_available and not no_candidates,
        "operator_review_required": requires_operator or branch == RESOLUTION_LOCAL_CANDIDATE,
        "acquisition_required": branch == RESOLUTION_ACQUISITION_REQUIRED,
        "exact_match_found": resolution_status == STATUS_EXACT_MATCH_FOUND,
        "acceptable_local_candidate_found": resolution_status == STATUS_ACCEPTABLE_LOCAL_CANDIDATE,
        "candidate_requires_operator_review": resolution_status == STATUS_CANDIDATE_REQUIRES_REVIEW,
        "acquisition_required_status": resolution_status == STATUS_ACQUISITION_REQUIRED,
        "exact_match_available": exact_match_available,
        "exact_match": inventory.get("sdxl_exact_match"),
        "acceptable_match": inventory.get("sdxl_acceptable_match"),
        "total_valid_candidates": inventory.get("total_valid_candidates", 0),
        "valid_candidates": candidate_review.get("valid_candidates", []),
        "rejected_candidates_count": inventory.get("total_rejected", 0),
        "total_checkpoints_found": inventory.get("total_checkpoints_found", 0),
        "checkpoint_mapping": {
            "logical_asset_id": EXPECTED_CHECKPOINT_ASSET,
            "canonical_filenames": CANONICAL_CHECKPOINT_NAMES,
            "acceptable_candidates": ACCEPTABLE_CANDIDATE_NAMES.get(EXPECTED_CHECKPOINT_ASSET, []),
            "matched_file": (
                (inventory.get("sdxl_exact_match") or inventory.get("sdxl_acceptable_match") or {}).get("file_name")
            ),
        },
        "acquisition_required_reason": (
            "No SDXL-compatible checkpoints found in local inventory"
            if branch == RESOLUTION_ACQUISITION_REQUIRED else None
        ),
        "operator_review_required_reason": (
            "SDXL-compatible candidate(s) found but require operator approval for substitution"
            if branch == RESOLUTION_LOCAL_CANDIDATE else None
        ),
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "fake_checkpoint_availability_created": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "timestamp": _utcnow(),
    }


def _build_substitution_packet(
    inventory: Dict[str, Any],
    candidate_review: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the substitution operator review packet."""
    return {
        "task_id": TASK_ID,
        "packet_type": "checkpoint_substitution_operator_review",
        "reason": "Operator approval required for checkpoint substitution",
        "expected_asset": EXPECTED_CHECKPOINT_ASSET,
        "expected_asset_display": EXPECTED_CHECKPOINT_DISPLAY,
        "candidates": candidate_review.get("candidates", []),
        "auto_substitution_not_performed": True,
        "auto_substitution_why": "Policy requires explicit operator approval for checkpoint substitution",
        "risks": [
            "Substituted checkpoint may produce different visual results",
            "Pipeline weight/compatibility not verified for substituted checkpoint",
        ],
        "operator_decision_required": True,
        "operator_decision_options": [
            "approve_substitution",
            "reject_substitution_require_exact",
        ],
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "fake_install_proof_forbidden": True,
        "blind_substitution_forbidden": True,
        "timestamp": _utcnow(),
    }


def _create_acquisition_contracts(
    control_dir: Path,
    missing_checkpoint: str,
    inventory: Dict[str, Any],
    candidate_review: Dict[str, Any],
) -> Dict[str, bool]:
    """Create controlled acquisition artifacts when checkpoint is missing."""
    now = _utcnow()

    # Source allowlist decision
    source_allowlist = {
        "task_id": TASK_ID,
        "decision_type": "checkpoint_source_allowlist",
        "missing_checkpoint": missing_checkpoint,
        "allowed_sources": [
            {
                "source": "huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
                "source_type": "huggingface",
                "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
                "verified_trusted": True,
                "download_authorized": False,
                "requires_operator_approval": True,
            },
            {
                "source": "huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                "source_type": "huggingface_direct",
                "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
                "verified_trusted": True,
                "download_authorized": False,
                "requires_operator_approval": True,
            },
        ],
        "operator_approval_required": True,
        "download_authorized": False,
        "download_performed": False,
        "timestamp": now,
    }
    _write_json(
        _artifact_path(control_dir, ACQUISITION_ARTIFACTS["checkpoint_source_allowlist_decision"]),
        source_allowlist,
    )

    # Acquisition execution contract
    execution_contract = {
        "task_id": TASK_ID,
        "contract_type": "checkpoint_acquisition_execution",
        "missing_checkpoint": missing_checkpoint,
        "expected_file": "sd_xl_base_1.0.safetensors",
        "expected_file_size_hint": "> 5 GB (SDXL base checkpoint)",
        "target_install_path": "models/checkpoints/sd_xl_base_1.0.safetensors",
        "source_url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
        "checksum_url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors.sha256",
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "operator_approval_required": True,
        "fake_download_proof_forbidden": True,
        "fake_install_proof_forbidden": True,
        "timestamp": now,
    }
    _write_json(
        _artifact_path(control_dir, ACQUISITION_ARTIFACTS["checkpoint_acquisition_execution_contract"]),
        execution_contract,
    )

    # Install verification contract
    install_contract = {
        "task_id": TASK_ID,
        "contract_type": "checkpoint_install_verification",
        "missing_checkpoint": missing_checkpoint,
        "expected_install_path": "models/checkpoints/sd_xl_base_1.0.safetensors",
        "verification_required": True,
        "verification_checks": [
            "file_exists",
            "file_size > 5 GB",
            "sha256_checksum_match",
            "loadable_by_comfyui",
        ],
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "install_verified": False,
        "fake_install_proof_forbidden": True,
        "timestamp": now,
    }
    _write_json(
        _artifact_path(control_dir, ACQUISITION_ARTIFACTS["checkpoint_install_verification_contract"]),
        install_contract,
    )

    # Acquisition blocker report
    blocker_report = {
        "task_id": TASK_ID,
        "blocker_type": "checkpoint_acquisition_required",
        "decision": "acquisition_required",
        "missing_checkpoint": missing_checkpoint,
        "expected_asset_type": "checkpoint",
        "local_inventory_checked": True,
        "total_checkpoints_found": inventory.get("total_checkpoints_found", 0),
        "sdxl_compatible_found": len(inventory.get("sdxl_compatible_found", [])),
        "why_resolution_blocked": (
            "No SDXL-compatible checkpoint found in local inventory. "
            "Checkpoint must be acquired from trusted source and installed."
        ),
        "fake_availability_forbidden": True,
        "unapproved_download_forbidden": True,
        "unapproved_install_forbidden": True,
        "generation_forbidden_until_resolved": True,
        "operator_action_required": "Approve source, download, and install via operator review",
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "timestamp": now,
    }
    _write_json(
        _artifact_path(control_dir, ACQUISITION_ARTIFACTS["checkpoint_acquisition_blocker_report"]),
        blocker_report,
    )

    return {
        "source_allowlist_decision": True,
        "acquisition_execution_contract": True,
        "install_verification_contract": True,
        "acquisition_blocker_report": True,
    }


# ---------------------------------------------------------------------------
# Gate revalidation
# ---------------------------------------------------------------------------

def _revalidate_generation_gate_internal(
    project_root: str,
    resolution_branch: str,
    resolution_decision: Dict[str, Any],
    inventory: Dict[str, Any],
    candidate_review: Dict[str, Any],
) -> Dict[str, Any]:
    """Re-evaluate generation gate after checkpoint resolution attempt.

    Returns the revalidation result dict.
    """
    checkpoint_resolved = resolution_branch == RESOLUTION_EXACT_AVAILABLE
    operator_review_required = resolution_branch == RESOLUTION_LOCAL_CANDIDATE
    acquisition_required = resolution_branch == RESOLUTION_ACQUISITION_REQUIRED

    if checkpoint_resolved:
        gate_status = "checkpoint_resolved_generation_ready"
        generation_authorized = False  # Still needs operator authorization
        gate_blocked = False
        reason = "Checkpoint checkpoint_sdxl_base resolved locally. Generation gate ready for operator authorization."
    elif operator_review_required:
        gate_status = "checkpoint_candidate_found_operator_review_required"
        generation_authorized = False
        gate_blocked = True
        reason = "SDXL-compatible checkpoint candidate found. Operator review required before substitution."
    elif acquisition_required:
        gate_status = "checkpoint_acquisition_required_gate_blocked"
        generation_authorized = False
        gate_blocked = True
        reason = "No SDXL-compatible checkpoint found. Controlled acquisition required before generation."
    else:
        gate_status = "checkpoint_unresolved_blocker"
        generation_authorized = False
        gate_blocked = True
        reason = "Checkpoint resolution could not determine a resolution path."

    return {
        "task_id": TASK_ID,
        "revalidation_type": "checkpoint_resolution_gate_revalidation",
        "resolution_branch": resolution_branch,
        "gate_status": gate_status,
        "generation_authorized": generation_authorized,
        "generation_gate_blocked": gate_blocked,
        "checkpoint_resolved": checkpoint_resolved,
        "operator_review_required": operator_review_required,
        "acquisition_required": acquisition_required,
        "reason": reason,
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "visual_qa_executed": False,
        "preview_render_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": _utcnow(),
    }


def revalidate_generation_gate(project_root: str) -> Dict[str, Any]:
    """Re-evaluate generation gate after checkpoint resolution attempt.

    Reads the resolution artifacts and produces a revalidation result.
    Does NOT perform generation, ComfyUI submit, or any forbidden actions.
    """
    control_dir = _get_control_dir(project_root)

    # Load resolution artifacts
    resolution_decision = _load_json(
        _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_resolution_decision"])
    )
    inventory = _load_json(
        _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_local_inventory_report"])
    )
    candidate_review = _load_json(
        _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_candidate_review_report"])
    )

    if resolution_decision is None:
        # No resolution attempted yet
        return {
            "task_id": TASK_ID,
            "revalidation_type": "checkpoint_resolution_gate_revalidation",
            "error": "checkpoint_resolution_decision.json not found. Run combine-resolve-checkpoint-asset first.",
            "generation_authorized": False,
            "generation_gate_blocked": True,
            "checkpoint_resolved": False,
            "generation_performed": False,
            "comfyui_submit_executed": False,
            "production_accepted": False,
            "timestamp": _utcnow(),
        }

    branch = resolution_decision.get("resolution_branch", RESOLUTION_UNRESOLVED_BLOCKER)
    checkpoint_resolved = resolution_decision.get("checkpoint_resolved", False)

    # Re-run revalidation
    result = _revalidate_generation_gate_internal(
        project_root, branch, resolution_decision, inventory or {}, candidate_review or {},
    )

    # Write to artifact
    revalidation_path = _artifact_path(control_dir, RESOLUTION_ARTIFACTS["checkpoint_resolution_gate_revalidation"])
    _write_json(revalidation_path, result)

    return result


# ---------------------------------------------------------------------------
# Build result
# ---------------------------------------------------------------------------

def _build_result(
    project_root: str,
    branch: str,
    missing_checkpoint: str,
    inventory: Dict[str, Any],
    candidate_review: Dict[str, Any],
    resolution_decision: Dict[str, Any],
    revalidation_result: Dict[str, Any],
    current_state: str,
    next_allowed_action: str,
    substitution_packet_created: bool,
    acquisition_contracts_created: Dict[str, bool],
    created: Dict[str, bool],
) -> Dict[str, Any]:
    """Build the complete result dict."""
    return {
        "task_id": TASK_ID,
        "feature_completed": True,
        "checkpoint_blocker_read": True,
        "missing_checkpoint": missing_checkpoint,
        "local_inventory_checked": True,
        "candidate_review_completed": True,
        "resolution_decision_created": True,
        "generation_gate_revalidated": True,
        "selected_branch": branch,
        "resolution_status": resolution_decision.get("resolution_status"),
        "checkpoint_resolved": branch == RESOLUTION_EXACT_AVAILABLE,
        "local_candidate_found": branch == RESOLUTION_LOCAL_CANDIDATE,
        "operator_review_required": branch in (RESOLUTION_LOCAL_CANDIDATE,),
        "acquisition_required": branch == RESOLUTION_ACQUISITION_REQUIRED,
        "exact_match_found": resolution_decision.get("exact_match_found", False),
        "acceptable_local_candidate_found": resolution_decision.get("acceptable_local_candidate_found", False),
        "candidate_requires_operator_review": resolution_decision.get("candidate_requires_operator_review", False),
        "acquisition_required_status": resolution_decision.get("acquisition_required_status", False),
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "fake_checkpoint_availability_created": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "visual_qa_executed": False,
        "preview_render_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "substitution_packet_created": substitution_packet_created,
        "acquisition_contracts_created": acquisition_contracts_created,
        "artifacts_created": created,
        "timestamp": _utcnow(),
    }


# ---------------------------------------------------------------------------
# Artifact Index and Episode Ledger updates
# ---------------------------------------------------------------------------

def _update_artifact_index(project_root: str, result: Dict[str, Any]) -> None:
    """Update artifact_index.json with checkpoint resolution artifacts."""
    control_dir = _get_control_dir(project_root)
    index_path = control_dir / "artifact_index.json"

    index = _load_json(index_path) or {}

    # Add checkpoint resolution entries
    index["checkpoint_resolution_executed"] = True
    index["checkpoint_resolution_task_id"] = TASK_ID
    index["checkpoint_resolution_branch"] = result.get("selected_branch", "unknown")
    index["checkpoint_resolved"] = result.get("checkpoint_resolved", False)

    for key, filename in RESOLUTION_ARTIFACTS.items():
        index[f"{key}_created"] = True
        index[key] = filename

    artifacts_created = result.get("artifacts_created", {})
    for art_key, filename in SUBSTITUTION_ARTIFACTS.items():
        if artifacts_created.get(art_key):
            index[f"{art_key}_created"] = True
            index[art_key] = filename

    for art_key, filename in ACQUISITION_ARTIFACTS.items():
        if artifacts_created.get(art_key):
            index[f"{art_key}_created"] = True
            index[art_key] = filename

    # Forbidden state flags
    index["download_authorized"] = False
    index["download_performed"] = False
    index["install_authorized"] = False
    index["install_performed"] = False
    index["generation_performed"] = False
    index["comfyui_submit_executed"] = False
    index["retry_attempted"] = False
    index["visual_qa_executed"] = False
    index["preview_render_executed"] = False
    index["assembly_executed"] = False
    index["downstream_executed"] = False
    index["production_accepted"] = False

    # State
    index["current_state"] = result.get("current_state")
    index["next_allowed_action"] = result.get("next_allowed_action")
    index["timestamp"] = _utcnow()

    _write_json(index_path, index)


def _update_episode_ledger(project_root: str, result: Dict[str, Any]) -> None:
    """Add a ledger entry for checkpoint resolution."""
    control_dir = _get_control_dir(project_root)
    ledger_path = control_dir / "episode_ledger.json"

    ledger = _load_json(ledger_path) or []

    entry = {
        "event": "checkpoint_asset_resolution_executed",
        "task_id": TASK_ID,
        "selected_branch": result.get("selected_branch", "unknown"),
        "checkpoint_resolved": result.get("checkpoint_resolved", False),
        "local_candidate_found": result.get("local_candidate_found", False),
        "operator_review_required": result.get("operator_review_required", False),
        "acquisition_required": result.get("acquisition_required", False),
        "download_authorized": False,
        "download_performed": False,
        "install_authorized": False,
        "install_performed": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": result.get("current_state"),
        "next_allowed_action": result.get("next_allowed_action"),
        "previous_layer": PREVIOUS_LAYER,
        "next_layer": result.get("current_state"),
        "timestamp": _utcnow(),
    }

    ledger.append(entry)
    _write_json(ledger_path, ledger)
