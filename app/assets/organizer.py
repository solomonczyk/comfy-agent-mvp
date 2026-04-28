"""KT-5 Asset Pipeline: artifact organization into stable folders.

After a run or batch job completes, `organize_run_artifacts` copies the
produced image(s), metadata JSON, summary TXT, and trace JSONL into the
canonical run/job folder (`data/outputs/runs/{run_id}` or
`data/batches/{batch_id}/{job_id}`). Images are downloaded from the
ComfyUI `/view` endpoint so the agent does not need to know ComfyUI's
on-disk output directory.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import httpx

from app.config import settings


def _download_image(filename: str, subfolder: str, image_type: str, target: Path) -> bool:
    """Download a single image from ComfyUI /view into target path.

    Returns True on success, False otherwise.
    """
    url = f"{settings.comfy_base_url}/view"
    params = {
        "filename": filename,
        "subfolder": subfolder or "",
        "type": image_type or "output",
    }
    try:
        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
            return True
    except Exception:
        return False


def _safe_copy(src: str | None, dst: Path) -> str | None:
    """Copy src file to dst; return the dst path as str on success, else None."""
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
    return str(dst)


def organize_run_artifacts(
    target_dir: Path,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Organize a completed run's artifacts into target_dir.

    Layout inside target_dir:
        metadata.json      - copy of result.metadata_path
        summary.txt        - copy of result.summary_path
        trace.jsonl        - copy of result.trace_path
        result.json        - full result dict
        images/<filename>  - downloaded images from ComfyUI

    Args:
        target_dir: Canonical folder (run_dir or job_dir) for this artifact set.
        result: The result dict returned by run_agent.

    Returns:
        An asset_report dict summarizing what was copied.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "target_dir": str(target_dir),
        "metadata_path": None,
        "summary_path": None,
        "trace_path": None,
        "result_path": None,
        "image_paths": [],
        "images_failed": [],
    }

    # Copy metadata / summary / trace
    report["metadata_path"] = _safe_copy(result.get("metadata_path"), target_dir / "metadata.json")
    report["summary_path"] = _safe_copy(result.get("summary_path"), target_dir / "summary.txt")
    report["trace_path"] = _safe_copy(result.get("trace_path"), target_dir / "trace.jsonl")

    # Write full result JSON
    result_path = target_dir / "result.json"
    try:
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report["result_path"] = str(result_path)
    except Exception:
        report["result_path"] = None

    # Download images via ComfyUI /view
    images_dir = target_dir / "images"
    for image in result.get("images") or []:
        filename = image.get("filename")
        subfolder = image.get("subfolder") or ""
        image_type = image.get("type") or "output"
        if not filename:
            continue
        dst = images_dir / filename
        ok = _download_image(filename, subfolder, image_type, dst)
        if ok:
            report["image_paths"].append(str(dst))
        else:
            report["images_failed"].append(filename)

    return report
