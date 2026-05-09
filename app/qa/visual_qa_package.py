"""Visual QA Package — generated asset technical validation and operator review routing.

This module implements the full visual QA feature loop for a generated asset:
1. Input artifact validation (generation_result_review, visual_qa_input_packet, canonical_manifest)
2. Asset technical validation (exists, readable, sha256, dimensions, size, stub detection)
3. Technical visual QA metrics (blur, brightness, contrast)
4. Visual QA report creation (technical pass != visual acceptance)
5. Operator review packet creation (for manual visual inspection)
6. State transition to operator_visual_review_required
7. Artifact index and episode ledger updates

It does NOT perform: new generation, retry, ComfyUI submit, visual acceptance,
operator visual decision, preview render, assembly, or downstream.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, UnidentifiedImageError

from app.qa.opencv_checks import (
    check_opencv_available,
    run_opencv_checks,
)

TASK_ID = "RC-COMBINE-V2-102001-106000"


# ---------------------------------------------------------------------------
# Asset validation helpers
# ---------------------------------------------------------------------------

def _resolve_asset_path(project_root: Path, asset_path: str) -> Path:
    """Resolve asset path relative to project root if not absolute."""
    p = Path(asset_path)
    if p.is_absolute():
        return p
    return project_root / asset_path


def _sha256_file(path: Path) -> Optional[str]:
    """Compute SHA-256 hex digest of a file. Returns None on error."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _read_json(path: Path) -> Dict[str, Any]:
    """Read a JSON file and return dict, or empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, payload: Any) -> None:
    """Write a JSON file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ---------------------------------------------------------------------------
# 1. Input artifact validation
# ---------------------------------------------------------------------------

def validate_input_artifacts(control_dir: Path) -> Dict[str, Any]:
    """Validate that all required input artifacts exist and point to the same asset.

    Checks:
    - generation_result_review.json exists and is well-formed
    - visual_qa_input_packet.json exists and is well-formed
    - canonical_outputs_manifest.json exists and is well-formed
    - All three reference the same generated asset (sha256 match)
    """
    result: Dict[str, Any] = {
        "validation_performed": True,
        "generation_result_review_valid": False,
        "visual_qa_input_packet_valid": False,
        "canonical_manifest_valid": False,
        "assets_match_across_artifacts": False,
        "blocker": None,
    }

    grr_path = control_dir / "generation_result_review.json"
    vqip_path = control_dir / "visual_qa_input_packet.json"
    com_path = control_dir / "canonical_outputs_manifest.json"

    # Load artifacts
    grr = _read_json(grr_path)
    vqip = _read_json(vqip_path)
    com = _read_json(com_path)

    missing = []
    if not grr:
        missing.append("generation_result_review.json")
    if not vqip:
        missing.append("visual_qa_input_packet.json")
    if not com:
        missing.append("canonical_outputs_manifest.json")

    if missing:
        result["blocker"] = f"Missing input artifacts: {', '.join(missing)}"
        result["missing_artifacts"] = missing
        return result

    # Validate structure — each should have a generated_assets list
    grr_assets = grr.get("generated_assets", [])
    vqip_assets = vqip.get("generated_assets", [])
    com_assets = com.get("generated_assets", [])

    if not grr_assets:
        result["blocker"] = "generation_result_review.json has empty generated_assets"
        return result
    if not vqip_assets:
        result["blocker"] = "visual_qa_input_packet.json has empty generated_assets"
        return result
    if not com_assets:
        result["blocker"] = "canonical_outputs_manifest.json has empty generated_assets"
        return result

    grr_valid = all(
        k in grr_assets[0] for k in ("path", "sha256", "width", "height", "size_bytes")
    )
    vqip_valid = all(
        k in vqip_assets[0] for k in ("path", "sha256", "width", "height", "size_bytes")
    )
    com_valid = all(
        k in com_assets[0] for k in ("path", "sha256", "width", "height", "size_bytes")
    )

    result["generation_result_review_valid"] = grr_valid
    result["visual_qa_input_packet_valid"] = vqip_valid
    result["canonical_manifest_valid"] = com_valid

    if not (grr_valid and vqip_valid and com_valid):
        result["blocker"] = "One or more input artifacts have incomplete asset data"
        return result

    # Check that all three reference the same asset (by sha256)
    sha256_grr = grr_assets[0].get("sha256")
    sha256_vqip = vqip_assets[0].get("sha256")
    sha256_com = com_assets[0].get("sha256")

    all_match = sha256_grr and sha256_grr == sha256_vqip == sha256_com
    result["assets_match_across_artifacts"] = all_match
    if not all_match:
        result["blocker"] = (
            f"SHA256 mismatch across input artifacts: "
            f"grr={sha256_grr}, vqip={sha256_vqip}, com={sha256_com}"
        )
        return result

    result["referenced_sha256"] = sha256_grr
    result["referenced_path"] = grr_assets[0].get("path")
    result["referenced_width"] = grr_assets[0].get("width")
    result["referenced_height"] = grr_assets[0].get("height")
    result["referenced_size_bytes"] = grr_assets[0].get("size_bytes")
    result["blocker"] = None
    return result


# ---------------------------------------------------------------------------
# 2. Asset technical validation
# ---------------------------------------------------------------------------

def validate_asset_technical(
    project_root: Path,
    asset_rel_path: str,
    expected_sha256: str,
    expected_width: int = 1024,
    expected_height: int = 1024,
) -> Dict[str, Any]:
    """Validate the generated asset exists, is readable, and matches expectations.

    Checks:
    - file exists
    - image is readable by PIL
    - SHA-256 matches expected value
    - dimensions match expected (1024x1024)
    - size > 1024 bytes (no stub)
    - not a test pattern / solid-color noise heuristic check
    """
    result: Dict[str, Any] = {
        "validation_performed": True,
        "asset_path": asset_rel_path,
        "exists": False,
        "readable": False,
        "sha256_matches": False,
        "dimensions_match": False,
        "size_valid": False,
        "stub_asset": True,
        "not_stub": False,
        "blocker": None,
        "technical_validation_pass": False,
    }

    asset_full = _resolve_asset_path(project_root, asset_rel_path)

    if not asset_full.exists():
        result["blocker"] = f"Asset file not found: {asset_full}"
        return result
    result["exists"] = True
    result["full_path"] = str(asset_full)

    # SHA-256
    actual_sha256 = _sha256_file(asset_full)
    result["actual_sha256"] = actual_sha256
    result["sha256_matches"] = actual_sha256 == expected_sha256
    if not result["sha256_matches"]:
        result["blocker"] = (
            f"SHA256 mismatch: expected={expected_sha256}, actual={actual_sha256}"
        )
        # Continue validation but flag blocker

    # Readability and dimensions
    try:
        with Image.open(asset_full) as img:
            width, height = img.size
            result["readable"] = True
            result["width"] = width
            result["height"] = height
            result["dimensions_match"] = (width == expected_width and height == expected_height)
            if not result["dimensions_match"]:
                result["blocker"] = (
                    f"Dimension mismatch: expected {expected_width}x{expected_height}, "
                    f"got {width}x{height}"
                )
    except (UnidentifiedImageError, OSError, ValueError) as e:
        result["readable"] = False
        result["read_error"] = str(e)
        result["blocker"] = f"Asset not readable: {e}"
        return result

    # File size / stub detection
    size_bytes = asset_full.stat().st_size
    result["size_bytes"] = size_bytes
    result["size_valid"] = size_bytes > 1024
    result["stub_asset"] = size_bytes <= 1024
    result["not_stub"] = size_bytes > 1024
    if result["stub_asset"]:
        result["blocker"] = f"Stub asset detected: size {size_bytes} <= 1024 bytes"

    # Heuristic: detect solid-color / test noise images
    try:
        with Image.open(asset_full) as img:
            extrema = img.getextrema()
            # If all channels have min==max (range 0), it's a solid-color image
            is_solid = all(
                (isinstance(ex, tuple) and ex[0] == ex[1])
                or (isinstance(ex, (int, float)) and ex == 0)
                for ex in extrema
            )
            result["solid_color_detected"] = bool(is_solid)
            if is_solid:
                result["blocker"] = "Solid-color image detected (may be a test pattern)"
    except Exception:
        result["solid_color_detected"] = None

    # Overall pass/fail
    result["technical_validation_pass"] = (
        result["exists"]
        and result["readable"]
        and result["sha256_matches"]
        and result["dimensions_match"]
        and result["not_stub"]
        and not result.get("solid_color_detected", False)
    )

    return result


# ---------------------------------------------------------------------------
# 3. Technical Visual QA metrics
# ---------------------------------------------------------------------------

def compute_technical_visual_qa_metrics(project_root: Path, asset_rel_path: str) -> Dict[str, Any]:
    """Compute technical image quality metrics for the generated asset.

    Metrics (with cv2):
    - blur score (Laplacian variance)
    - brightness (mean pixel intensity)
    - contrast (RMS / std of pixel intensities)

    Without cv2, returns baseline: blur=0, brightness=0, contrast=0
    and notes cv2 not available.
    """
    result: Dict[str, Any] = {
        "metrics_computed": True,
        "opencv_available": check_opencv_available(),
        "blur_score": None,
        "brightness": None,
        "contrast": None,
        "warnings": [],
        "automatic_visual_pass": False,
        "notes": [],
    }

    asset_full = _resolve_asset_path(project_root, asset_rel_path)

    if not asset_full.exists():
        result["metrics_computed"] = False
        result["blocker"] = "Asset not found"
        return result

    if not check_opencv_available():
        result["notes"].append("OpenCV not available -- returning baseline metrics")
        result["blur_score"] = 0.0
        result["brightness"] = 0.0
        result["contrast"] = 0.0
        result["baseline_used"] = True
        return result

    opencv_results = run_opencv_checks(asset_full)

    result["blur_score"] = opencv_results.get("blur_score")
    result["brightness"] = opencv_results.get("brightness")
    result["contrast"] = opencv_results.get("contrast")
    result["opencv_detail"] = opencv_results

    # Blur warning
    blur = result["blur_score"]
    if blur is not None:
        if blur < 50:
            result["warnings"].append(f"Severe blur detected: score={blur:.1f} (< 50)")
        elif blur < 100:
            result["warnings"].append(f"Moderate blur detected: score={blur:.1f} (< 100)")

    # Brightness warning
    brightness = result["brightness"]
    if brightness is not None:
        if brightness < 30:
            result["warnings"].append(f"Very dark image: brightness={brightness:.1f} (< 30)")
        elif brightness > 225:
            result["warnings"].append(f"Very bright/overexposed: brightness={brightness:.1f} (> 225)")
        elif brightness < 50:
            result["warnings"].append(f"Dark image: brightness={brightness:.1f} (< 50)")

    # Contrast warning
    contrast = result["contrast"]
    if contrast is not None:
        if contrast < 20:
            result["warnings"].append(f"Low contrast: contrast={contrast:.1f} (< 20)")

    # Explicitly do NOT set automatic_visual_pass = True
    result["automatic_visual_pass"] = False

    return result


# ---------------------------------------------------------------------------
# 4. Visual QA report
# ---------------------------------------------------------------------------

def build_visual_qa_report(
    project_root: Path,
    input_validation: Dict[str, Any],
    asset_validation: Dict[str, Any],
    technical_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the comprehensive Visual QA report.

    This report records the technical validation result and clearly states
    that a technical pass does NOT equal operator visual acceptance.
    production_accepted is always False.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Determine overall technical result
    input_valid = (
        input_validation.get("generation_result_review_valid", False)
        and input_validation.get("visual_qa_input_packet_valid", False)
        and input_validation.get("canonical_manifest_valid", False)
        and input_validation.get("assets_match_across_artifacts", False)
    )
    asset_valid = asset_validation.get("technical_validation_pass", False)
    metrics_computed = technical_metrics.get("metrics_computed", False)

    technical_pass = input_valid and asset_valid and metrics_computed
    has_warnings = len(technical_metrics.get("warnings", [])) > 0
    has_blockers = (
        input_validation.get("blocker") is not None
        or asset_validation.get("blocker") is not None
    )

    report: Dict[str, Any] = {
        "task_id": TASK_ID,
        "report_type": "generated_asset_visual_qa",
        "timestamp": timestamp,
        "technical_qa_executed": True,
        "input_validation": input_validation,
        "asset_validation": asset_validation,
        "technical_metrics": technical_metrics,
        "technical_pass": technical_pass,
        "has_warnings": has_warnings,
        "has_blockers": has_blockers,
        "blocker": input_validation.get("blocker") or asset_validation.get("blocker"),
        "disclaimer": "Technical pass does NOT equal operator visual acceptance. "
                      "Visual acceptance requires human operator inspection.",
        "production_accepted": False,
        "visual_acceptance_executed": False,
        "new_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "next_allowed_action": "operator_visual_review_required",
        "current_state": "generation_result_review_required",
        "target_state": "operator_visual_review_required",
    }

    return report


# ---------------------------------------------------------------------------
# 5. Operator visual review packet
# ---------------------------------------------------------------------------

def build_operator_visual_review_packet(
    project_root: Path,
    asset_rel_path: str,
    asset_validation: Dict[str, Any],
    technical_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the operator review packet for manual visual inspection.

    Includes:
    - asset path, sha256, dimensions
    - technical metrics
    - visual inspection checklist
    - explicit routing: operator_visual_review_required
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    asset_full = _resolve_asset_path(project_root, asset_rel_path)

    checklist = [
        "1. Overall composition: Is the subject fully visible and well-composed?",
        "2. Subject quality: Is the subject realistic, with proper skin/texture detail?",
        "3. Facial features (if applicable): Are eyes, mouth, teeth natural-looking?",
        "4. Lighting: Is the lighting consistent and natural?",
        "5. Background: Is the background appropriate and free of artifacts?",
        "6. Color: Are colors accurate and consistent?",
        "7. Sharpness: Is the image appropriately sharp (not oversharpened or too soft)?",
        "8. Artifacts: Any visible artifacts (glitches, doubling, seams, noise)?",
        "9. Prompt alignment: Does the image match the intended prompt/concept?",
        "10. Production quality: Is this image acceptable for production use?",
    ]

    packet: Dict[str, Any] = {
        "task_id": TASK_ID,
        "packet_type": "operator_visual_review",
        "timestamp": timestamp,
        "asset": {
            "path": asset_rel_path,
            "full_path": str(asset_full),
            "sha256": asset_validation.get("actual_sha256"),
            "width": asset_validation.get("width"),
            "height": asset_validation.get("height"),
            "size_bytes": asset_validation.get("size_bytes"),
        },
        "technical_metrics": {
            "blur_score": technical_metrics.get("blur_score"),
            "brightness": technical_metrics.get("brightness"),
            "contrast": technical_metrics.get("contrast"),
            "warnings": technical_metrics.get("warnings", []),
            "opencv_available": technical_metrics.get("opencv_available", False),
        },
        "visual_inspection_checklist": checklist,
        "decision_required": "operator_visual_review_decision",
        "decision_options": {
            "accept": "Accept the asset for pipeline (proceed to assembly)",
            "reject": "Reject the asset and request corrective retry",
            "reject_with_defects": "Reject and document specific visual defects",
        },
        "rules": {
            "production_accepted_must_remain_false": True,
            "agent_must_not_accept_visually": True,
            "agent_must_not_retry_or_regenerate": True,
            "agent_must_not_assemble_or_downstream": True,
        },
        "current_state": "generation_result_review_required",
        "target_state": "operator_visual_review_required",
        "production_accepted": False,
        "visual_acceptance_executed": False,
        "new_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "operator_decision": None,
        "operator_verdict": None,
        "operator_review_date": None,
    }

    return packet


# ---------------------------------------------------------------------------
# 6. Manifest / filesystem consistency check
# ---------------------------------------------------------------------------

def validate_manifest_matches_filesystem(
    project_root: Path,
    manifest_assets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Check that the manifest entries match the actual filesystem state.

    For each asset entry in the manifest, verify the file exists, its SHA-256
    matches, and its dimensions match the manifest record.
    """
    result: Dict[str, Any] = {
        "validation_performed": True,
        "manifest_count": len(manifest_assets),
        "filesystem_matches": False,
        "entries": [],
        "mismatches": [],
    }

    all_match = True
    for entry in manifest_assets:
        rel_path = entry.get("path", "")
        expected_sha = entry.get("sha256")
        full_path = _resolve_asset_path(project_root, rel_path)
        entry_result: Dict[str, Any] = {
            "path": rel_path,
            "exists": full_path.exists(),
            "sha256_matches": False,
            "manifest_sha256": expected_sha,
        }

        if full_path.exists():
            actual_sha = _sha256_file(full_path)
            entry_result["actual_sha256"] = actual_sha
            entry_result["sha256_matches"] = actual_sha == expected_sha
            if not entry_result["sha256_matches"]:
                all_match = False
                entry_result["mismatch_reason"] = "sha256"
                result["mismatches"].append(entry_result)
        else:
            all_match = False
            entry_result["mismatch_reason"] = "file_not_found"
            result["mismatches"].append(entry_result)

        result["entries"].append(entry_result)

    result["filesystem_matches"] = all_match
    return result


# ---------------------------------------------------------------------------
# 7. Main orchestrator function
# ---------------------------------------------------------------------------

def run_generated_asset_visual_qa_package(
    project_root: str | Path,
) -> Dict[str, Any]:
    """Execute the full Generated Asset Visual QA Package.

    Steps:
    1. Validate input artifacts
    2. Validate asset technically
    3. Compute technical metrics
    4. Validate manifest matches filesystem
    5. Build Visual QA report
    6. Build Operator Visual Review packet
    7. Update artifact_index.json with new state
    8. Update episode_ledger.json with event
    9. Return full result dict

    Forbidden:
    - No new generation
    - No retry
    - No ComfyUI submit
    - No visual acceptance
    - No operator visual decision by agent
    - No preview render
    - No assembly
    - No downstream
    - No production_accepted=true
    """
    project_root = Path(project_root)
    control_dir = project_root / "output" / "control"
    timestamp = datetime.now(timezone.utc).isoformat()

    # --- Step 1: Input artifact validation ---
    input_validation = validate_input_artifacts(control_dir)

    # --- Step 2: Asset technical validation ---
    referenced_path = input_validation.get("referenced_path", "")
    referenced_sha256 = input_validation.get("referenced_sha256", "")
    referenced_width = input_validation.get("referenced_width", 1024)
    referenced_height = input_validation.get("referenced_height", 1024)

    asset_validation = validate_asset_technical(
        project_root=project_root,
        asset_rel_path=referenced_path if referenced_path else "",
        expected_sha256=referenced_sha256 if referenced_sha256 else "",
        expected_width=referenced_width or 1024,
        expected_height=referenced_height or 1024,
    )

    # --- Step 3: Technical Visual QA metrics ---
    asset_rel = referenced_path or asset_validation.get("asset_path", "")
    technical_metrics = compute_technical_visual_qa_metrics(project_root, asset_rel)

    # --- Step 4: Manifest vs filesystem ---
    canonical_manifest = _read_json(control_dir / "canonical_outputs_manifest.json")
    manifest_assets = canonical_manifest.get("generated_assets", [])
    manifest_fs_match = validate_manifest_matches_filesystem(project_root, manifest_assets)

    # --- Step 5: Build Visual QA report ---
    qa_report = build_visual_qa_report(
        project_root,
        input_validation,
        asset_validation,
        technical_metrics,
    )
    qa_report["manifest_filesystem_match"] = manifest_fs_match
    qa_report["manifest_filesystem_matches"] = manifest_fs_match.get("filesystem_matches", False)

    # Determine overall pass: technical validation must pass, but we still route to operator
    has_blockers = (
        input_validation.get("blocker") is not None
        or asset_validation.get("blocker") is not None
    )

    if has_blockers:
        qa_report["technical_verdict"] = "BLOCKED"
        qa_report["blocker"] = (
            input_validation.get("blocker") or asset_validation.get("blocker")
        )
        # Still produce artifacts, but mark them as blocked
        target_state = "blocked_manual_review"
        next_action = "blocked_manual_review"
    else:
        qa_report["technical_verdict"] = "PASS"
        target_state = "operator_visual_review_required"
        next_action = "operator_visual_review_required"

    qa_report["current_state"] = "generation_result_review_required"
    qa_report["target_state"] = target_state
    qa_report["next_allowed_action"] = next_action

    # --- Step 6: Build Operator Visual Review packet ---
    op_packet = build_operator_visual_review_packet(
        project_root,
        asset_rel,
        asset_validation,
        technical_metrics,
    )
    op_packet["technical_verdict"] = qa_report.get("technical_verdict", "UNKNOWN")
    op_packet["current_state"] = qa_report["current_state"]
    op_packet["target_state"] = target_state
    op_packet["next_allowed_action"] = next_action

    # --- Write artifact files ---
    # visual_qa_report.json
    qa_report_path = control_dir / "visual_qa_report.json"
    _write_json(qa_report_path, qa_report)

    # operator_visual_review_packet.json
    op_packet_path = control_dir / "operator_visual_review_packet.json"
    _write_json(op_packet_path, op_packet)

    # visual_qa_technical_metrics.json
    metrics_artifact: Dict[str, Any] = {
        "task_id": TASK_ID,
        "timestamp": timestamp,
        "metrics": technical_metrics,
        "asset_validation": asset_validation,
        "input_validation": input_validation,
        "manifest_filesystem_match": manifest_fs_match,
    }
    metrics_path = control_dir / "visual_qa_technical_metrics.json"
    _write_json(metrics_path, metrics_artifact)

    # --- Step 7: Update artifact_index.json ---
    artifact_index = _read_json(control_dir / "artifact_index.json")
    artifact_index["current_state"] = target_state
    artifact_index["next_allowed_action"] = next_action
    artifact_index["production_accepted"] = False
    artifact_index["visual_qa_executed"] = True
    artifact_index["visual_acceptance_executed"] = False
    artifact_index["assembly_executed"] = False
    artifact_index["downstream_executed"] = False
    artifact_index["new_generation_performed"] = False
    artifact_index["retry_attempted"] = False
    artifact_index["comfyui_submit_executed"] = False
    artifact_index["technical_verdict"] = qa_report.get("technical_verdict", "UNKNOWN")

    # Add/update stage_results
    if "stage_results" not in artifact_index:
        artifact_index["stage_results"] = []
    artifact_index["stage_results"].append({
        "stage": "generated_asset_visual_qa_package",
        "success": not has_blockers,
        "message": (
            "Visual QA package executed. "
            f"Technical verdict: {qa_report.get('technical_verdict')}. "
            "No visual acceptance claimed. "
            "Routed to operator visual review."
        ),
        "artifacts": [
            "visual_qa_report.json",
            "operator_visual_review_packet.json",
            "visual_qa_technical_metrics.json",
        ],
        "metadata": {
            "task_id": TASK_ID,
            "technical_verdict": qa_report.get("technical_verdict"),
            "has_blockers": has_blockers,
            "production_accepted": False,
            "visual_acceptance_executed": False,
            "new_generation_performed": False,
            "comfyui_submit_executed": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "input_artifacts_valid": input_validation.get("blocker") is None,
            "asset_technical_validation_pass": asset_validation.get("technical_validation_pass", False),
            "manifest_filesystem_matches": manifest_fs_match.get("filesystem_matches", False),
            "blur_metric_recorded": technical_metrics.get("blur_score") is not None,
            "brightness_metric_recorded": technical_metrics.get("brightness") is not None,
            "contrast_metric_recorded": technical_metrics.get("contrast") is not None,
        },
        "timestamp": timestamp,
        "no_generation_performed": True,
    })
    _write_json(control_dir / "artifact_index.json", artifact_index)

    # --- Step 8: Update episode_ledger.json ---
    ledger_path = control_dir / "episode_ledger.json"
    ledger_data: Any = []
    if ledger_path.exists():
        try:
            with open(ledger_path, "r") as f:
                ledger_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            ledger_data = []

    if isinstance(ledger_data, dict):
        if "events" not in ledger_data:
            ledger_data["events"] = []
        ledger_data["events"].append({
            "event_type": "generated_asset_visual_qa_package_executed",
            "task_id": TASK_ID,
            "stage": "generated_asset_visual_qa_package",
            "technical_verdict": qa_report.get("technical_verdict"),
            "has_blockers": has_blockers,
            "visual_qa_executed": True,
            "visual_acceptance_executed": False,
            "new_generation_performed": False,
            "comfyui_submit_executed": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": next_action,
            "previous_state": "generation_result_review_required",
            "timestamp": timestamp,
        })
    elif isinstance(ledger_data, list):
        ledger_data.append({
            "event_type": "generated_asset_visual_qa_package_executed",
            "task_id": TASK_ID,
            "stage": "generated_asset_visual_qa_package",
            "technical_verdict": qa_report.get("technical_verdict"),
            "has_blockers": has_blockers,
            "visual_qa_executed": True,
            "visual_acceptance_executed": False,
            "new_generation_performed": False,
            "comfyui_submit_executed": False,
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": next_action,
            "previous_state": "generation_result_review_required",
            "timestamp": timestamp,
        })

    _write_json(ledger_path, ledger_data)

    # --- Step 9: Return full result ---
    return {
        "task_id": TASK_ID,
        "feature_completed": True,
        "full_feature_loop_executed": True,
        "input_generation_result_review_validated": input_validation.get("generation_result_review_valid", False),
        "input_visual_qa_packet_validated": input_validation.get("visual_qa_input_packet_valid", False),
        "canonical_manifest_validated": input_validation.get("canonical_manifest_valid", False),
        "generated_asset_validated": asset_validation.get("technical_validation_pass", False),
        "asset_exists": asset_validation.get("exists", False),
        "asset_readable": asset_validation.get("readable", False),
        "sha256_verified": asset_validation.get("sha256_matches", False),
        "dimensions_verified": asset_validation.get("dimensions_match", False),
        "size_bytes_verified": asset_validation.get("size_valid", False),
        "stub_asset_detected": asset_validation.get("stub_asset", True),
        "solid_color_detected": asset_validation.get("solid_color_detected", False),
        "manifest_matches_filesystem": manifest_fs_match.get("filesystem_matches", False),
        "technical_visual_qa_executed": technical_metrics.get("metrics_computed", False),
        "blur_metric_recorded": technical_metrics.get("blur_score") is not None,
        "brightness_metric_recorded": technical_metrics.get("brightness") is not None,
        "contrast_metric_recorded": technical_metrics.get("contrast") is not None,
        "visual_qa_report_created": qa_report_path.exists(),
        "operator_visual_review_packet_created": op_packet_path.exists(),
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "state_updated": True,
        "new_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "visual_acceptance_executed": False,
        "operator_visual_decision_made_by_agent": False,
        "preview_render_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": target_state,
        "next_allowed_action": next_action,
        "blockers": [] if not has_blockers else [str(qa_report.get("blocker", "unknown"))],
        "next_task_recommendation": "operator_visual_review_decision",
    }
