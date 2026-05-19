"""Output collector for ComfyUI generation with blank image detection.

RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001

- Searches native ComfyUI output by prompt_id / filename prefix / timestamp
- Reconciles manifest if real image exists elsewhere
- Diagnoses runtime failure if no real image exists
- Detects blank/near-uniform gray/black/white outputs
- Verifies file is not stub by size, dimensions, pixel variance, entropy
- Fixes SaveImage/output path collection
"""
from __future__ import annotations

import glob
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.visual_generation.blank_image_detector import (
    BlankImageDetector,
    record_operator_rejection,
    validate_output_collection,
)


class OutputCollector:
    """Collects ComfyUI output with validation and blank image detection."""

    TASK_ID = "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001"

    def __init__(
        self,
        project_root: Path,
        comfyui_output_dir: str | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.assets_dir = self.project_root / "output" / "assets" / "fresh_visual_candidates"

        # Default ComfyUI output directory
        if comfyui_output_dir is None:
            self.comfyui_output_dir = Path(
                "F:\\ComfyUI\\comfyUI_portable_inst\\ComfyUI_windows_portable_nvidia_cu126"
                "\\ComfyUI_windows_portable\\ComfyUI\\output"
            )
        else:
            self.comfyui_output_dir = Path(comfyui_output_dir)

        self.detector = BlankImageDetector()
        self.collected_assets: list[dict[str, Any]] = []

    def search_native_comfyui_output(
        self,
        prompt_id: str | None = None,
        filename_prefix: str | None = None,
        timestamp: int | None = None,
    ) -> list[Path]:
        """Search native ComfyUI output directory for images.

        Args:
            prompt_id: ComfyUI prompt_id to search for
            filename_prefix: Filename prefix from SaveImage node
            timestamp: Unix timestamp to search near

        Returns:
            List of paths to found images
        """
        found_images: list[Path] = []

        if not self.comfyui_output_dir.exists():
            return found_images

        # Search by filename prefix
        if filename_prefix:
            pattern = str(self.comfyui_output_dir / f"{filename_prefix}*.png")
            found = sorted(glob.glob(pattern))
            found_images.extend(Path(f) for f in found)

        # Search by prompt_id in filename (some ComfyUI versions include it)
        if prompt_id:
            pattern = str(self.comfyui_output_dir / f"*{prompt_id}*.png")
            found = sorted(glob.glob(pattern))
            found_images.extend(Path(f) for f in found)

        # Search by timestamp proximity (within 60 seconds)
        if timestamp:
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                for img_path in self.comfyui_output_dir.glob(ext):
                    try:
                        mtime = int(img_path.stat().st_mtime)
                        if abs(mtime - timestamp) < 60:
                            found_images.append(img_path)
                    except OSError:
                        continue

        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in found_images:
            if str(img) not in seen:
                seen.add(str(img))
                unique_images.append(img)

        return unique_images

    def reconcile_manifest_with_disk(
        self,
        manifest_images: list[str],
        prompt_id: str | None = None,
        filename_prefix: str | None = None,
    ) -> dict[str, Any]:
        """Reconcile manifest entries with actual files on disk.

        If files are missing from expected location but exist in ComfyUI output,
        update the manifest paths.

        Args:
            manifest_images: List of image filenames from manifest
            prompt_id: ComfyUI prompt_id
            filename_prefix: Filename prefix from workflow

        Returns:
            Reconciliation report
        """
        reconciliation = {
            "task_id": self.TASK_ID,
            "document_type": "output_manifest_reconciliation_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "manifest_entries": len(manifest_images),
            "found_in_expected_location": 0,
            "found_in_comfyui_output": 0,
            "missing_files": [],
            "reconciled_paths": [],
        }

        for filename in manifest_images:
            expected_path = self.assets_dir / filename

            if expected_path.exists():
                reconciliation["found_in_expected_location"] += 1
                reconciliation["reconciled_paths"].append(str(expected_path))
                continue

            # Search in ComfyUI output
            found = self.search_native_comfyui_output(
                prompt_id=prompt_id,
                filename_prefix=filename_prefix,
            )

            # Match by filename
            for img_path in found:
                if img_path.name == filename or filename in img_path.name:
                    # Copy to expected location
                    dst = self.assets_dir / filename
                    self.assets_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img_path, dst)
                    reconciliation["found_in_comfyui_output"] += 1
                    reconciliation["reconciled_paths"].append(str(dst))
                    break
            else:
                reconciliation["missing_files"].append(filename)

        reconciliation["all_found"] = len(reconciliation["missing_files"]) == 0

        return reconciliation

    def collect_and_validate(
        self,
        prompt_id: str,
        output_images: list[str],
        filename_prefix: str | None = None,
    ) -> dict[str, Any]:
        """Collect outputs and validate with blank image detection.

        Args:
            prompt_id: ComfyUI prompt_id
            output_images: List of output image filenames
            filename_prefix: Filename prefix from SaveImage node

        Returns:
            Collection and validation report
        """
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # First, reconcile manifest with disk
        reconciliation = self.reconcile_manifest_with_disk(
            output_images, prompt_id, filename_prefix
        )

        collected_assets = []
        validated_assets = []
        blank_assets = []

        for filename in output_images:
            # Check expected location
            expected_path = self.assets_dir / filename
            src_path = expected_path if expected_path.exists() else None

            # If not in expected location, try ComfyUI output
            if not src_path:
                found = self.search_native_comfyui_output(
                    prompt_id=prompt_id,
                    filename_prefix=filename_prefix,
                )
                for img_path in found:
                    if img_path.name == filename or filename in img_path.name:
                        src_path = img_path
                        break

            if not src_path or not src_path.exists():
                # Record missing file
                collected_assets.append({
                    "source_filename": filename,
                    "path": None,
                    "exists": False,
                    "readable": False,
                    "sha256": None,
                    "size_bytes": 0,
                    "width": 0,
                    "height": 0,
                    "error": "source file not found",
                    "is_blank": False,
                    "is_valid": False,
                })
                continue

            # Validate with blank image detector
            validation = self.detector.validate_and_classify(src_path)

            asset_entry = {
                "source_filename": filename,
                "path": str(src_path),
                "exists": True,
                "readable": validation["readable"],
                "sha256": validation["sha256"],
                "size_bytes": validation["size_bytes"],
                "width": validation["dimensions"]["width"],
                "height": validation["dimensions"]["height"],
                "pixel_analysis": validation["pixel_analysis"],
                "is_blank": validation["classification"]["is_blank"],
                "is_uniform_gray": validation["classification"]["is_uniform_gray"],
                "is_stub": validation["classification"]["is_stub"],
                "is_valid": validation["classification"]["is_valid"],
                "rejection_reason": validation["rejection_reason"],
            }

            collected_assets.append(asset_entry)

            if validation["classification"]["is_valid"]:
                validated_assets.append(asset_entry)
            else:
                blank_assets.append(asset_entry)

                # Record operator rejection for blank/stub
                record_operator_rejection(
                    asset_path=src_path,
                    rejection_reason=validation["rejection_reason"] or "unknown",
                    project_root=self.project_root,
                )

        # Determine state based on validation
        all_valid = len(blank_assets) == 0 and len(validated_assets) > 0
        any_blank = len(blank_assets) > 0

        current_state = (
            "operator_visual_review_required" if all_valid
            else "runtime_output_collection_blocked"
        )
        next_allowed_action = (
            "operator_visual_review_required" if all_valid
            else "runtime_output_collection_repair_required"
        )

        report = {
            "task_id": self.TASK_ID,
            "document_type": "output_collection_and_validation_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "filename_prefix": filename_prefix,
            "generation_performed": True,
            "generation_count": 1,
            "max_generations": 1,
            "reconciliation": reconciliation,
            "collected_assets": collected_assets,
            "validated_assets": validated_assets,
            "blank_or_invalid_assets": blank_assets,
            "total_assets": len(collected_assets),
            "valid_assets": len(validated_assets),
            "invalid_assets": len(blank_assets),
            "all_valid": all_valid,
            "blank_detected": any_blank,
            "invalid_blank_output_classified": any_blank,
            "operator_rejection_recorded": any_blank,
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "production_accepted": False,
            "retry_attempted": False,
            "second_generation_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
        }

        # Write report
        report_path = self.control_dir / "output_collection_validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def diagnose_runtime_failure(
        self,
        prompt_id: str | None,
        history: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Diagnose runtime failure when no output images are found.

        Args:
            prompt_id: ComfyUI prompt_id
            history: ComfyUI history dict if available

        Returns:
            Diagnosis report
        """
        diagnosis = {
            "task_id": self.TASK_ID,
            "document_type": "runtime_failure_diagnosis",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "comfyui_output_dir_exists": self.comfyui_output_dir.exists(),
            "comfyui_output_dir": str(self.comfyui_output_dir),
            "files_in_output_dir": [],
            "history_available": history is not None,
            "history_status": None,
            "failure_cause": None,
            "recommendation": None,
        }

        # List files in ComfyUI output
        if self.comfyui_output_dir.exists():
            recent_files = sorted(
                self.comfyui_output_dir.glob("*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:10]
            diagnosis["files_in_output_dir"] = [
                {"name": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime}
                for f in recent_files
            ]

        # Analyze history if available
        if history and prompt_id:
            status = history.get("status", {})
            diagnosis["history_status"] = status.get("status_str")
            diagnosis["execution_errors"] = status.get("messages", [])

            if status.get("status_str") != "success":
                diagnosis["failure_cause"] = f"comfyui_execution_failed: {status.get('status_str')}"
                diagnosis["recommendation"] = "check_comfyui_logs_and_retry"

        if not diagnosis["failure_cause"]:
            if not diagnosis["files_in_output_dir"]:
                diagnosis["failure_cause"] = "no_output_generated"
                diagnosis["recommendation"] = "check_saveimage_node_configuration"
            else:
                diagnosis["failure_cause"] = "output_not_collected"
                diagnosis["recommendation"] = "check_filename_prefix_and_paths"

        # Write diagnosis
        diagnosis_path = self.control_dir / "runtime_failure_diagnosis.json"
        with open(diagnosis_path, "w", encoding="utf-8") as f:
            json.dump(diagnosis, f, indent=2, ensure_ascii=False)

        return diagnosis


def search_and_validate_native_output(
    project_root: Path,
    prompt_id: str,
    comfyui_output_dir: str | None = None,
) -> dict[str, Any]:
    """Search native ComfyUI output and validate found images.

    Standalone function for searching by prompt_id and validating.

    Args:
        project_root: Project root directory
        prompt_id: ComfyUI prompt_id
        comfyui_output_dir: Optional custom ComfyUI output directory

    Returns:
        Search and validation report
    """
    collector = OutputCollector(project_root, comfyui_output_dir)

    # Search for images
    found_images = collector.search_native_comfyui_output(prompt_id=prompt_id)

    if not found_images:
        # Diagnose why no images found
        diagnosis = collector.diagnose_runtime_failure(prompt_id, None)
        return {
            "task_id": OutputCollector.TASK_ID,
            "document_type": "native_output_search_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "images_found": 0,
            "found_paths": [],
            "diagnosis": diagnosis,
            "current_state": "runtime_output_collection_blocked",
            "next_allowed_action": "runtime_output_collection_repair_required",
            "production_accepted": False,
        }

    # Validate found images
    validations = []
    valid_images = []
    invalid_images = []

    for img_path in found_images:
        validation = collector.detector.validate_and_classify(img_path)
        validations.append(validation)

        if validation["classification"]["is_valid"]:
            valid_images.append(img_path)
        else:
            invalid_images.append(img_path)
            # Record rejection
            record_operator_rejection(
                asset_path=img_path,
                rejection_reason=validation["rejection_reason"] or "invalid_output",
                project_root=project_root,
            )

    # Determine state
    has_valid = len(valid_images) > 0
    has_invalid = len(invalid_images) > 0

    if has_valid and not has_invalid:
        current_state = "operator_visual_review_required"
        next_allowed_action = "operator_visual_review_required"
    elif has_invalid:
        current_state = "runtime_output_collection_blocked"
        next_allowed_action = "runtime_output_collection_repair_required"
    else:
        current_state = "runtime_output_collection_blocked"
        next_allowed_action = "runtime_output_collection_repair_required"

    return {
        "task_id": OutputCollector.TASK_ID,
        "document_type": "native_output_search_and_validation_report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_id": prompt_id,
        "images_found": len(found_images),
        "valid_images": len(valid_images),
        "invalid_images": len(invalid_images),
        "found_paths": [str(p) for p in found_images],
        "valid_paths": [str(p) for p in valid_images],
        "invalid_paths": [str(p) for p in invalid_images],
        "validations": validations,
        "blank_detected": has_invalid,
        "invalid_blank_output_classified": has_invalid,
        "operator_rejection_recorded": has_invalid,
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
    }
